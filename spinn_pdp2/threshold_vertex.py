import struct

from data_specification.enums.data_type import DataType

from pacman.model.constraints.placer_constraints import ChipAndCoreConstraint
from pacman.model.graphs.machine.machine_vertex import MachineVertex
from pacman.model.resources import ResourceContainer, VariableSDRAM, ConstantSDRAM
from pacman.executor.injection_decorator import inject_items

from spinn_utilities.overrides import overrides

from spinn_front_end_common.abstract_models.abstract_provides_n_keys_for_partition \
    import AbstractProvidesNKeysForPartition
from spinn_front_end_common.abstract_models import \
    AbstractRewritesDataSpecification
from spinn_front_end_common.abstract_models.impl \
    import MachineDataSpecableVertex
from spinn_front_end_common.utilities.constants \
    import SYSTEM_BYTES_REQUIREMENT, BYTES_PER_WORD
from spinn_front_end_common.interface.buffer_management.buffer_models import (
    AbstractReceiveBuffersToHost)
from spinn_front_end_common.interface.buffer_management import (
    recording_utilities)
from spinn_front_end_common.utilities.helpful_functions import (
    locate_memory_region_for_placement)

from spinnaker_graph_front_end.utilities import SimulatorVertex
from spinnaker_graph_front_end.utilities.data_utils \
    import generate_steps_system_data_region

from spinn_pdp2.mlp_types import MLPConstants, MLPRegions, \
    MLPVarSizeRecordings, MLPConstSizeRecordings, MLPExtraRecordings



class ThresholdVertex(
        SimulatorVertex,
        MachineDataSpecableVertex,
        AbstractProvidesNKeysForPartition,
        AbstractRewritesDataSpecification,
        AbstractReceiveBuffersToHost
        ):

    """ A vertex to implement a PDP2 threshold core
        that applies unit output and activation functions
    """

    def __init__(self,
                 network,
                 group,
                 subgroup
                 ):

        self._network  = network
        self._group    = group
        self._subgroup = subgroup

        # place OUTPUT groups "close" to the host
        if self.group.output_grp:
            self._constraints = [ChipAndCoreConstraint (x = 0, y = 0)]
        else:
            self._constraints = None

        super(ThresholdVertex, self).__init__(
            label = f"t_core{self.group.id}/{self.subgroup}",
            binary_name = "threshold.aplx",
            constraints = self._constraints)

        self._stage = 0

        # application-level data
        self._set_cfg = self.network.ex_set.set_config
        self._ex_cfg  = self.network.ex_set.example_config
        self._ev_cfg  = self.network.ex_set.event_config

        # application parameters
        self._out_integr_dt = 1.0 / self.network.ticks_per_int

        if self.group.test_group_crit is not None:
            self._tst_group_criterion = self.group.test_group_crit
        elif self.network.test_group_crit is not None:
            self._tst_group_criterion = self.network.test_group_crit
        else:
            self._tst_group_criterion = MLPConstants.DEF_GRP_CRIT

        if self.group.train_group_crit is not None:
            self._trn_group_criterion = self.group.train_group_crit
        elif self.network.train_group_crit is not None:
            self._trn_group_criterion = self.network.train_group_crit
        else:
            self._trn_group_criterion = MLPConstants.DEF_GRP_CRIT

        # forward, backprop and stop link names
        self._fwd_link = f"fwd_t{self.group.id}/{self.subgroup}"
        self._bkp_link = f"bkp_t{self.group.id}/{self.subgroup}"
        self._stp_link = f"stp_t{self.group.id}/{self.subgroup}"

        # threshold core-specific parameters
        self._units = self.group.subunits[self.subgroup]

        # first output subgroup has special functions
        self._is_first_out = self.group.is_first_out and (self.subgroup == 0)

        # last output subgroup has special functions
        self._is_last_out = ((self.group == self.network.output_chain[-1]) and
                             (self.subgroup == (self.group.subgroups - 1)))

        # configuration and data sizes
        # network configuration structure
        self._NETWORK_CONFIGURATION_BYTES = len (self.network.network_config)

        # core configuration structure
        self._CORE_CONFIGURATION_BYTES = len (self.config)

        # set configuration structure
        self._EXAMPLE_SET_BYTES = len (self._set_cfg)

        # list of example configurations
        self._EXAMPLES_BYTES = len (self._ex_cfg) * len (self._ex_cfg[0])

        # list of event configurations
        self._EVENTS_BYTES = len (self._ev_cfg) * len (self._ev_cfg[0])

        # list of subgroup inputs (empty if not an INPUT group)
        if self.group.input_grp:
            self._INPUTS_BYTES = ((len (self.group.inputs) // self.group.units) *
                                  self._units * DataType.INT32.size)
        else:
            self._INPUTS_BYTES = 0

        # list of subgroup targets (empty if not an OUTPUT group)
        if self.group.output_grp:
            self._TARGETS_BYTES = ((len (self.group.targets) // self.group.units) *
                                  self._units * DataType.INT32.size)
        else:
            self._TARGETS_BYTES = 0

        # list of routing keys
        self._KEYS_BYTES = MLPConstants.NUM_KEYS_REQ * DataType.INT32.size

        # stage configuration structure
        self._STAGE_CONFIGURATION_BYTES = len (self.network.stage_config)

        # reserve SDRAM space used to store historic data
        #NOTE: MLPConstants sizes are in bits
        self._TARGET_HISTORY_BYTES = ((MLPConstants.ACTIV_SIZE // 8) *
            self._units * self.network.global_max_ticks)

        self._OUT_DERIV_HISTORY_BYTES = ((MLPConstants.LONG_DERIV_SIZE // 8) *
            self._units * self.network.global_max_ticks)

        self._NET_HISTORY_BYTES = ((MLPConstants.NET_SIZE // 8) *
            self._units * self.network.global_max_ticks)

        self._OUTPUT_HISTORY_BYTES = ((MLPConstants.ACTIV_SIZE // 8) *
            self._units * self.network.global_max_ticks)

        # recording info region size
        if self.group.output_grp:
            # number of recording channels
            NUM_REC_CHANNS = (len(MLPVarSizeRecordings) +
                              len(MLPConstSizeRecordings))

            # first output group/subgroup has extra recording channels
            if self._is_first_out:
                # number of extra recording channels
                NUM_REC_CHANNS += len(MLPExtraRecordings)

            self._REC_INFO_BYTES = (
                recording_utilities.get_recording_header_size(NUM_REC_CHANNS))
        else:
            self._REC_INFO_BYTES = 0

        # recording channel sizes
        if self.group.output_grp:
            # list of variable-size recording channel sizes
            self.VAR_CHANNEL_SIZES = [
                self._units * (BYTES_PER_WORD // 2)  # OUTPUTS
                ]

            # list of constant-size recording channel sizes
            self.CONST_CHANNEL_SIZES = [
                4 * BYTES_PER_WORD  # TEST_RESULTS
                ]

            # list of extra recording channel sizes
            if self._is_first_out:
                # list of extra recording channel sizes
                self.EXTRA_CHANNEL_SIZES = [
                    4 * BYTES_PER_WORD  # TICK_DATA
                    ]
            else:
                self.EXTRA_CHANNEL_SIZES = [0]

            self._VAR_CHANNEL_BYTES = sum(self.VAR_CHANNEL_SIZES) + \
                sum(self.EXTRA_CHANNEL_SIZES)

            self._CONST_CHANNEL_BYTES = sum(self.CONST_CHANNEL_SIZES)
        else:
            self._VAR_CHANNEL_BYTES = 0
            self._CONST_CHANNEL_BYTES = 0

        # configuration data plus application core SDRAM usage
        self._sdram_fixed = (
            SYSTEM_BYTES_REQUIREMENT +
            self._NETWORK_CONFIGURATION_BYTES +
            self._CORE_CONFIGURATION_BYTES +
            self._EXAMPLE_SET_BYTES +
            self._EXAMPLES_BYTES +
            self._EVENTS_BYTES +
            self._INPUTS_BYTES +
            self._TARGETS_BYTES +
            self._KEYS_BYTES +
            self._STAGE_CONFIGURATION_BYTES +
            self._TARGET_HISTORY_BYTES +
            self._OUT_DERIV_HISTORY_BYTES +
            self._NET_HISTORY_BYTES +
            self._OUTPUT_HISTORY_BYTES +
            self._REC_INFO_BYTES +
            self._CONST_CHANNEL_BYTES
        )

        # recording channels SDRAM usage
        self._sdram_variable = (
            self._VAR_CHANNEL_BYTES
        )

    @property
    def network (self):
        return self._network

    @property
    def group (self):
        return self._group

    @property
    def subgroup (self):
        return self._subgroup

    @property
    def fwd_link (self):
        return self._fwd_link

    @property
    def bkp_link (self):
        return self._bkp_link

    @property
    def stp_link (self):
        return self._stp_link

    @property
    def config (self):
        """ returns a packed string that corresponds to
            (C struct) t_conf in mlp_types.h:

            typedef struct t_conf
            {
              uchar         output_grp;
              uchar         input_grp;
              uint          num_units;
              uchar         write_results;
              uchar         write_out;
              uchar         last_tick_only;
              uchar         hard_clamp_en;
              uchar         out_integr_en;
              fpreal        out_integr_dt;
              uint          num_out_procs;
              uint          procs_list[SPINN_NUM_OUT_PROCS];
              fpreal        weak_clamp_strength;
              activation_t  initOutput;
              error_t       tst_group_criterion;
              error_t       trn_group_criterion;
              uchar         criterion_function;
              uchar         is_first_output;
              uchar         is_last_output;
              uchar         error_function;
            } t_conf_t;

            pack: standard sizes, little-endian byte order,
            explicit padding
        """
        # recording options
        #TODO: Cannot get no recording to work - for now minimise recorded data!
        if self.network.rec_outputs:
            write_out = self.group.write_out
            last_tick_only = self.network.rec_example_last_tick_only
        else:
            write_out = self.group.write_out
            last_tick_only = True

        # integration dt is an MLP fixed-point fpreal
        out_integr_dt = int (self._out_integr_dt *
                              (1 << MLPConstants.FPREAL_SHIFT))

        # weak_clamp_strength is an MLP fixed-point fpreal
        weak_clamp_strength = int (self.group.weak_clamp_strength *
                           (1 << MLPConstants.FPREAL_SHIFT))

        # init output is an MLP fixed-point activation_t
        init_output = int (self.group.init_output *
                           (1 << MLPConstants.ACTIV_SHIFT))

        # group criteria are MLP fixed-point error_t
        tst_group_criterion = int (self._tst_group_criterion *
                                (1 << MLPConstants.ERROR_SHIFT))
        trn_group_criterion = int (self._trn_group_criterion *
                                (1 << MLPConstants.ERROR_SHIFT))

        return struct.pack ("<2B2xI5B3xi6I4i4B",
                            self.group.output_grp,
                            self.group.input_grp,
                            self._units,
                            self.network.rec_test_results,
                            write_out,
                            last_tick_only,
                            self.group.hard_clamp_en,
                            self.group.out_integr_en,
                            out_integr_dt,
                            self.group.num_out_procs,
                            self.group.out_procs_list[0].value,
                            self.group.out_procs_list[1].value,
                            self.group.out_procs_list[2].value,
                            self.group.out_procs_list[3].value,
                            self.group.out_procs_list[4].value,
                            weak_clamp_strength,
                            init_output,
                            tst_group_criterion,
                            trn_group_criterion,
                            self.group.criterion_function.value,
                            self._is_first_out,
                            self._is_last_out,
                            self.group.error_function.value
                            )

    @property
    @overrides (MachineVertex.resources_required)
    def resources_required (self):
        if self.group.output_grp:
            resources = ResourceContainer (
                sdram = VariableSDRAM(self._sdram_fixed, self._sdram_variable)
                )
        else:
            resources = ResourceContainer (
                sdram = ConstantSDRAM(self._sdram_fixed)
                )
        return resources


    @overrides (AbstractProvidesNKeysForPartition.get_n_keys_for_partition)
    def get_n_keys_for_partition (self, partition, graph_mapper):
        return MLPConstants.KEY_SPACE_SIZE


    def read(self, placement, buffer_manager, channel):
        """ get recorded data from SDRAM

        :param placement: the location of this vertex
        :param buffer_manager: the buffer manager
        :param channel: recording channel to be read
        :return: recorded data as packed bytes
        """
        raw_data, missing_data = buffer_manager.get_data_by_placement(
            placement, channel
            )
        if missing_data:
            raise Exception("missing data!")

        # return data as "packed" bytes
        return raw_data


    @inject_items({
        "data_n_steps": "DataNSteps"
    })
    @overrides(MachineDataSpecableVertex.generate_machine_data_specification,
               additional_arguments=["data_n_steps"])
    def generate_machine_data_specification(
            self, spec, placement, machine_graph, routing_info, iptags,
            reverse_iptags, machine_time_step, time_scale_factor, data_n_steps):

        # Generate the system data region for simulation.c requirements
        generate_steps_system_data_region(spec, MLPRegions.SYSTEM.value, self)

        # reserve and write the network configuration region
        spec.reserve_memory_region (MLPRegions.NETWORK.value,
                                    self._NETWORK_CONFIGURATION_BYTES)

        spec.switch_write_focus (MLPRegions.NETWORK.value)

        # write the network configuration into spec
        for c in self.network.network_config:
            spec.write_value (c, data_type = DataType.UINT8)

        # reserve and write the core configuration region
        spec.reserve_memory_region (MLPRegions.CORE.value,
                                    self._CORE_CONFIGURATION_BYTES)

        spec.switch_write_focus (MLPRegions.CORE.value)

        # write the core configuration into spec
        for c in self.config:
            spec.write_value (c, data_type = DataType.UINT8)

        # reserve and write the example set region
        spec.reserve_memory_region (MLPRegions.EXAMPLE_SET.value,
                                    self._EXAMPLE_SET_BYTES)

        spec.switch_write_focus (MLPRegions.EXAMPLE_SET.value)

        # write the example set configuration into spec
        for c in self._set_cfg:
            spec.write_value (c, data_type = DataType.UINT8)

        # reserve and write the examples region
        spec.reserve_memory_region (MLPRegions.EXAMPLES.value,
                                    self._EXAMPLES_BYTES)

        spec.switch_write_focus (MLPRegions.EXAMPLES.value)

        # write the example configurations into spec
        for ex in self._ex_cfg:
            for c in ex:
                spec.write_value (c, data_type = DataType.UINT8)

        # reserve and write the events region
        spec.reserve_memory_region (MLPRegions.EVENTS.value,
                                    self._EVENTS_BYTES)

        spec.switch_write_focus (MLPRegions.EVENTS.value)

        # write the event configurations into spec
        for ev in self._ev_cfg:
            for c in ev:
                spec.write_value (c, data_type = DataType.UINT8)

        # reserve and write the input data region (if INPUT group)
        if self.group.input_grp:
            spec.reserve_memory_region (MLPRegions.INPUTS.value,
                                        self._INPUTS_BYTES)

            spec.switch_write_focus (MLPRegions.INPUTS.value)

            # write inputs to spec
            us = self.subgroup * MLPConstants.MAX_BLK_UNITS
            for _ in range (len (self.group.inputs) // self.group.units):
                for i in self.group.inputs[us : us + self._units]:
                    # inputs are fixed-point activation_t
                    #NOTE: check for absent or NaN
                    if (i is None) or (i != i):
                        inp = MLPConstants.ACTIV_NaN
                    else:
                        inp = int (i * (1 << MLPConstants.ACTIV_SHIFT))
                    spec.write_value (inp, data_type = DataType.UINT32)
                us += self.group.units

        # reserve and write the target data region
        if self.group.output_grp:
            spec.reserve_memory_region (MLPRegions.TARGETS.value,
                                        self._TARGETS_BYTES)

            spec.switch_write_focus (MLPRegions.TARGETS.value)

            # write targets to spec
            us = self.subgroup * MLPConstants.MAX_BLK_UNITS
            for _ in range (len (self.group.targets) // self.group.units):
                for t in self.group.targets[us : us + self._units]:
                    # inputs are fixed-point activation_t
                    #NOTE: check for absent or NaN
                    if (t is None) or (t != t):
                        tgt = MLPConstants.ACTIV_NaN
                    else:
                        tgt = int (t * (1 << MLPConstants.ACTIV_SHIFT))
                    spec.write_value (tgt, data_type = DataType.UINT32)
                us += self.group.units

        # reserve and write the routing region
        spec.reserve_memory_region (MLPRegions.ROUTING.value,
                                    self._KEYS_BYTES)

        spec.switch_write_focus (MLPRegions.ROUTING.value)

        # write link keys: fwd
        spec.write_value (routing_info.get_first_key_from_pre_vertex (
            self, self.fwd_link), data_type = DataType.UINT32)

        # write link keys: bkp
        spec.write_value (routing_info.get_first_key_from_pre_vertex (
            self, self.bkp_link), data_type = DataType.UINT32)

        # write link keys: fds (padding)
        spec.write_value (0, data_type = DataType.UINT32)

        # write link keys: stp (OUTPUT groups only)
        if self.group.output_grp:
            spec.write_value (routing_info.get_first_key_from_pre_vertex (
                self, self.stp_link), data_type = DataType.UINT32)
        else:
            spec.write_value (0, data_type = DataType.UINT32)

        # write link keys: lds (padding)
        spec.write_value (0, data_type = DataType.UINT32)

        # reserve and write the stage configuration region
        spec.reserve_memory_region (MLPRegions.STAGE.value,
                                    self._STAGE_CONFIGURATION_BYTES)

        spec.switch_write_focus (MLPRegions.STAGE.value)

        # write the stage configuration into spec
        for c in self.network.stage_config:
            spec.write_value (c, data_type = DataType.UINT8)

        # reserve and write the recording info region
        if self.group.output_grp:
            spec.reserve_memory_region(
                region = MLPRegions.REC_INFO.value,
                size = self._REC_INFO_BYTES
                )

            # write the actual recording channel sizes for a stage
            _sizes = [data_n_steps * sz for sz in self.VAR_CHANNEL_SIZES]
            _sizes.extend([sz for sz in self.CONST_CHANNEL_SIZES])
            if self._is_first_out:
                _sizes.extend(
                    [data_n_steps * sz for sz in self.EXTRA_CHANNEL_SIZES]
                    )

            spec.switch_write_focus(MLPRegions.REC_INFO.value)
            spec.write_array(
                recording_utilities.get_recording_header_array(_sizes)
            )

        spec.end_specification ()


    @overrides(AbstractRewritesDataSpecification.regenerate_data_specification)
    def regenerate_data_specification(self, spec, placement):
        # reserve and write the stage configuration region
        spec.reserve_memory_region (MLPRegions.STAGE.value,
                                    self._STAGE_CONFIGURATION_BYTES)

        spec.switch_write_focus (MLPRegions.STAGE.value)

        # write the stage configuration into spec
        for c in self.network.stage_config:
            spec.write_value (c, data_type = DataType.UINT8)

        spec.end_specification()


    @overrides(AbstractRewritesDataSpecification.requires_memory_regions_to_be_reloaded)
    def requires_memory_regions_to_be_reloaded(self):
        return True


    @overrides(AbstractRewritesDataSpecification.mark_regions_reloaded)
    def mark_regions_reloaded(self):
        """
            TODO: not really sure what this method is used for!
        """
        # prepare for next stage
        self._stage += 1


    @overrides(AbstractReceiveBuffersToHost.get_recorded_region_ids)
    def get_recorded_region_ids(self):
        if self.group.output_grp:
            ids = [ch.value for ch in MLPVarSizeRecordings]
            ids.extend([ch.value for ch in MLPConstSizeRecordings])

            # first output group has additional recording channels
            if self._is_first_out:
                ids.extend([ch.value for ch in MLPExtraRecordings])

            return ids
        else:
            return []


    @overrides(AbstractReceiveBuffersToHost.get_recording_region_base_address)
    def get_recording_region_base_address(self, txrx, placement):
        return locate_memory_region_for_placement(
            placement, MLPRegions.REC_INFO.value, txrx)
