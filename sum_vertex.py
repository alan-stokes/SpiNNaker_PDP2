import struct
import numpy as np
import os

from data_specification.enums.data_type import DataType

from pacman.executor.injection_decorator import inject_items

from pacman.model.graphs.machine.machine_vertex import MachineVertex
from pacman.model.decorators.overrides import overrides
from pacman.model.resources.resource_container import ResourceContainer
from pacman.model.resources.sdram_resource import SDRAMResource

from spinn_front_end_common.utilities.utility_objs.executable_start_type \
    import ExecutableStartType
from spinn_front_end_common.abstract_models.abstract_has_associated_binary \
    import AbstractHasAssociatedBinary
from spinn_front_end_common.abstract_models\
    .abstract_generates_data_specification \
    import AbstractGeneratesDataSpecification
from spinn_front_end_common.abstract_models\
    .abstract_provides_n_keys_for_partition \
    import AbstractProvidesNKeysForPartition

from mlp_types import MLPRegions, MLPConstants


class SumVertex(
        MachineVertex,
        AbstractHasAssociatedBinary,
        AbstractProvidesNKeysForPartition,
        AbstractGeneratesDataSpecification):
    """ A vertex to implement an MLP input core
    """

    def __init__(self,
                 network,
                 group
                 ):
        """
        """
        MachineVertex.__init__(self, label =\
                               "s{} core".format (group.id))

        # application-level data
        self._network    = network
        self._group      = group

        # forward and backprop link partition names
        self._fwd_link = "fwd_s{}".format (self.group.id)
        self._bkp_link = "bkp_s{}".format (self.group.id)

        # sum core-specific parameters
        # NOTE: if all-zero w cores are optimised out this need reviewing
        self._fwd_expect = len (network.groups)
        self._bkp_expect = len (network.groups)

        # reserve a 16-bit key space in every link
        self._n_keys = MLPConstants.KEY_SPACE_SIZE

        # binary, configuration and data files
        self._aplx_file     = "binaries/sum.aplx"
        self._examples_file = "data/examples.dat"

        # find out the size of an integer!
        _data_int=DataType.INT32
        int_size = _data_int.size

        # size in bytes of the data in the regions
        self._N_NETWORK_CONFIGURATION_BYTES = \
            len (self._network.config)

        self._N_CORE_CONFIGURATION_BYTES = \
            len (self.config)

        self._N_EXAMPLES_BYTES = \
            os.path.getsize (self._examples_file) \
            if os.path.isfile (self._examples_file) \
            else 0

        # keys are integers
        self._N_KEYS_BYTES = MLPConstants.NUM_KEYS_REQ * int_size

        self._sdram_usage = (
            self._N_NETWORK_CONFIGURATION_BYTES + \
            self._N_CORE_CONFIGURATION_BYTES + \
            self._N_EXAMPLES_BYTES + \
            self._N_KEYS_BYTES
        )

    @property
    def group (self):
        return self._group

    @property
    def fwd_link (self):
        return self._fwd_link

    @property
    def bkp_link (self):
        return self._bkp_link

    @property
    def config (self):
        """ returns a packed string that corresponds to
            (C struct) s_conf in mlp_types.h:

            typedef struct s_conf
            {
              uint         num_units;
              scoreboard_t fwd_expect;
              scoreboard_t bkp_expect;
            } s_conf_t;

            pack: standard sizes, little-endian byte order,
            explicit padding
        """
        return struct.pack ("<3I",
                            self.group.units,
                            self._fwd_expect,
                            self._bkp_expect
                            )
    @property
    @overrides (MachineVertex.resources_required)
    def resources_required (self):

        resources = ResourceContainer (
            sdram = SDRAMResource (self._sdram_usage),
            )
        return resources

    @overrides (AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name (self):
        return self._aplx_file

    @overrides (AbstractHasAssociatedBinary.get_binary_start_type)
    def get_binary_start_type (self):
        return ExecutableStartType.SYNC

    @overrides (AbstractProvidesNKeysForPartition.get_n_keys_for_partition)
    def get_n_keys_for_partition (self, partition, graph_mapper):
        return self._n_keys

    @inject_items ({
        "routing_info": "MemoryRoutingInfos"})
    @overrides (
        AbstractGeneratesDataSpecification.generate_data_specification,
        additional_arguments=["routing_info"])
    def generate_data_specification (
            self, spec, placement, routing_info):

        # Reserve and write the network configuration region
        spec.reserve_memory_region (
            MLPRegions.NETWORK.value,
            self._N_NETWORK_CONFIGURATION_BYTES)

        spec.switch_write_focus (MLPRegions.NETWORK.value)

        # write the network configuration into spec
        for c in self._network.config:
            spec.write_value (ord (c), data_type=DataType.UINT8)

        # Reserve and write the core configuration region
        spec.reserve_memory_region (
            MLPRegions.CORE.value, self._N_CORE_CONFIGURATION_BYTES)

        spec.switch_write_focus (MLPRegions.CORE.value)

        # write the core configuration into spec
        for c in self.config:
            spec.write_value (ord (c), data_type=DataType.UINT8)

        # Reserve and write the examples region
        if os.path.isfile (self._examples_file):
            spec.reserve_memory_region (
                MLPRegions.EXAMPLES.value,
                self._N_EXAMPLES_BYTES)

#             print "sv-{}: reading {}".format (self.group.id,
#                                               self._examples_file
#                                               )

            spec.switch_write_focus (MLPRegions.EXAMPLES.value)

            # open the examples file
            _ef = open (self._examples_file, "rb")

            # read the data into a numpy array and put in spec
            _ex = np.fromfile (_ef, np.uint8)
            _ef.close ()
            for byte in _ex:
                spec.write_value (byte, data_type=DataType.UINT8)

        # Reserve and write the routing region
        spec.reserve_memory_region (
            MLPRegions.ROUTING.value, self._N_KEYS_BYTES)

        spec.switch_write_focus (MLPRegions.ROUTING.value)

        # write link keys (fwd, bkp)
        spec.write_value (routing_info.get_first_key_from_pre_vertex (
            self, self.fwd_link), data_type = DataType.UINT32)
        spec.write_value (routing_info.get_first_key_from_pre_vertex (
            self, self.bkp_link), data_type = DataType.UINT32)
        spec.write_value (0, data_type = DataType.UINT32)
        spec.write_value (0, data_type = DataType.UINT32)

        # End the specification
        spec.end_specification ()
