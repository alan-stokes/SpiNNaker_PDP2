import struct

from data_specification.enums.data_type import DataType

from pacman.model.graphs.machine.machine_vertex import MachineVertex
from pacman.model.resources.resource_container \
    import ResourceContainer, ConstantSDRAM

from spinn_utilities.overrides import overrides

from spinn_front_end_common.abstract_models.abstract_provides_n_keys_for_partition \
    import AbstractProvidesNKeysForPartition
from spinn_front_end_common.abstract_models import \
    AbstractRewritesDataSpecification
from spinn_front_end_common.abstract_models.impl \
    import MachineDataSpecableVertex
from spinn_front_end_common.utilities.constants \
    import SYSTEM_BYTES_REQUIREMENT

from spinnaker_graph_front_end.utilities import SimulatorVertex
from spinnaker_graph_front_end.utilities.data_utils \
    import generate_steps_system_data_region

from spinn_pdp2.mlp_types import MLPRegions, MLPConstants


class SumVertex(
        SimulatorVertex,
        MachineDataSpecableVertex,
        AbstractProvidesNKeysForPartition,
        AbstractRewritesDataSpecification
        ):

    """ A vertex to implement an PDP2 sum core
        that aggregates partial weight/input products
    """

    def __init__(self,
                 network,
                 group,
                 subgroup
                 ):

        self._network  = network
        self._group    = group
        self._subgroup = subgroup

        super(SumVertex, self).__init__(
            label = f"s_core{self.group.id}/{self.subgroup}",
            binary_name = "sum.aplx",
            constraints = None)

        self._stage = 0

        # application-level data
        self._set_cfg = self.network.ex_set.set_config
        self._ex_cfg  = self.network.ex_set.example_config

        # forward, backprop, link delta summation and sync link names
        self._fwd_link = f"fwd_s{self.group.id}/{self.subgroup}"
        self._bkp_link = f"bkp_s{self.group.id}/{self.subgroup}"
        self._lds_link = f"lds_s{self.group.id}/{self.subgroup}"
        self._fds_link = f"fds_s{self.group.id}/{self.subgroup}"

        # sum core-specific parameters
        # NOTE: if all-zero w cores are optimised out these need reviewing
        self._units = self.group.subunits[self.subgroup]

        # configuration and data sizes
        # network configuration structure
        self._NETWORK_CONFIGURATION_BYTES = len (self.network.network_config)

        # core configuration structure
        self._CORE_CONFIGURATION_BYTES = len (self.config)

        # set configuration structure
        self._EXAMPLE_SET_BYTES = len (self._set_cfg)

        # list of example configurations
        self._EXAMPLES_BYTES = len (self._ex_cfg) * len (self._ex_cfg[0])

        # list of routing keys
        self._KEYS_BYTES = MLPConstants.NUM_KEYS_REQ * (DataType.INT32).size

        # stage configuration structure
        self._STAGE_CONFIGURATION_BYTES = len (self.network.stage_config)

        self._sdram_usage = (
            self._NETWORK_CONFIGURATION_BYTES +
            self._CORE_CONFIGURATION_BYTES +
            self._EXAMPLE_SET_BYTES +
            self._EXAMPLES_BYTES +
            self._KEYS_BYTES +
            self._STAGE_CONFIGURATION_BYTES
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
    def lds_link (self):
        return self._lds_link

    @property
    def fds_link (self):
        return self._fds_link

    @property
    def config (self):
        """ returns a packed string that corresponds to
            (C struct) s_conf in mlp_types.h:

            typedef struct s_conf
            {
              uint         num_units;
              scoreboard_t fwd_expect;
              scoreboard_t bkp_expect;
              scoreboard_t ldsa_expect;
              uchar        is_first_group;
            } s_conf_t;

            pack: standard sizes, little-endian byte order,
            explicit padding
        """
        # check if first group in the network
        if self.group == self.network.groups[0]:
            is_first_group = 1
        else:
            is_first_group = 0

        fwd_expect  = self.network.subgroups
        bkp_expect  = self.network.subgroups

        # every s core expects partial lds from every w core in subgroup
        ldsa_expect = self.network.subgroups * self._units

        # first subgroup expects a partial lds from every other subgroup
        if self.subgroup == 0:
            ldsa_expect += self.group.subgroups - 1

            # first group expects a partial lds from every other group
            if is_first_group:
                ldsa_expect += len (self.network.groups) - 1

        return struct.pack ("<4IB3x",
                            self._units,
                            fwd_expect,
                            bkp_expect,
                            ldsa_expect,
                            is_first_group
                            )

    @property
    @overrides (MachineVertex.resources_required)
    def resources_required (self):
        resources = ResourceContainer (
            sdram = ConstantSDRAM(SYSTEM_BYTES_REQUIREMENT + self._sdram_usage)
            )
        return resources


    @overrides (AbstractProvidesNKeysForPartition.get_n_keys_for_partition)
    def get_n_keys_for_partition (self, partition, graph_mapper):
        return MLPConstants.KEY_SPACE_SIZE


    @overrides(MachineDataSpecableVertex.generate_machine_data_specification)
    def generate_machine_data_specification(
            self, spec, placement, machine_graph, routing_info, iptags,
            reverse_iptags, machine_time_step, time_scale_factor):

        # Generate the system data region for simulation.c requirements
        generate_steps_system_data_region(spec, MLPRegions.SYSTEM.value, self)

        # Reserve and write the network configuration region
        spec.reserve_memory_region (MLPRegions.NETWORK.value,
                                    self._NETWORK_CONFIGURATION_BYTES)

        spec.switch_write_focus (MLPRegions.NETWORK.value)

        # write the network configuration into spec
        for c in self.network.network_config:
            spec.write_value (c, data_type = DataType.UINT8)

        # Reserve and write the core configuration region
        spec.reserve_memory_region (MLPRegions.CORE.value,
                                    self._CORE_CONFIGURATION_BYTES)

        spec.switch_write_focus (MLPRegions.CORE.value)

        # write the core configuration into spec
        for c in self.config:
            spec.write_value (c, data_type = DataType.UINT8)

        # Reserve and write the example set region
        spec.reserve_memory_region (MLPRegions.EXAMPLE_SET.value,
                                    self._EXAMPLE_SET_BYTES)

        spec.switch_write_focus (MLPRegions.EXAMPLE_SET.value)

        # write the example set configuration into spec
        for c in self._set_cfg:
            spec.write_value (c, data_type = DataType.UINT8)

        # Reserve and write the examples region
        spec.reserve_memory_region (MLPRegions.EXAMPLES.value,
                                    self._EXAMPLES_BYTES)

        spec.switch_write_focus (MLPRegions.EXAMPLES.value)

        # write the example configurations into spec
        for ex in self._ex_cfg:
            for c in ex:
                spec.write_value (c, data_type = DataType.UINT8)

        # Reserve and write the routing region
        spec.reserve_memory_region (MLPRegions.ROUTING.value,
                                    self._KEYS_BYTES)

        spec.switch_write_focus (MLPRegions.ROUTING.value)

        # write link keys: fwd
        spec.write_value (routing_info.get_first_key_from_pre_vertex (
            self, self.fwd_link), data_type = DataType.UINT32)

        # write link keys: bkp
        spec.write_value (routing_info.get_first_key_from_pre_vertex (
            self, self.bkp_link), data_type = DataType.UINT32)

        # write link keys: fds
        spec.write_value (routing_info.get_first_key_from_pre_vertex (
            self, self.fds_link), data_type = DataType.UINT32)

        # write link keys: stp (padding)
        spec.write_value (0, data_type = DataType.UINT32)

        # write link keys: lds
        spec.write_value (routing_info.get_first_key_from_pre_vertex (
            self, self.lds_link), data_type = DataType.UINT32)

        # Reserve and write the stage configuration region
        spec.reserve_memory_region (MLPRegions.STAGE.value,
                                    self._STAGE_CONFIGURATION_BYTES)

        spec.switch_write_focus (MLPRegions.STAGE.value)

        # write the stage configuration into spec
        for c in self.network.stage_config:
            spec.write_value (c, data_type = DataType.UINT8)

        spec.end_specification ()


    @overrides(AbstractRewritesDataSpecification.regenerate_data_specification)
    def regenerate_data_specification(self, spec, placement):
        # Reserve and write the stage configuration region
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
