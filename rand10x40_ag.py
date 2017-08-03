from mlp_network import MLPNetwork
from mlp_types   import MLPNetworkTypes, MLPGroupTypes
from mlp_types   import MLPInputProcs

#-----------------------------------------------------------
# rand10x40
#
# gfe implementation of Lens' example rand10x40.
#
#-----------------------------------------------------------

# instantiate the MLP network
rand10x40 = MLPNetwork (net_type = MLPNetworkTypes.CONTINUOUS,
                        intervals = 4,
                        ticks_per_interval = 5
                        )

# instantiate network groups (layers)
Input  = rand10x40.group (units = 10,
                          group_type = MLPGroupTypes.INPUT,
                          label = "Input"
                          )
Hidden = rand10x40.group (units = 50,
                          input_funcs = [MLPInputProcs.IN_INTEGR],
                          label = "Hidden"
                          )
Output = rand10x40.group (units = 10,
                          group_type = MLPGroupTypes.OUTPUT,
                          label = "Output"
                          )

# instantiate network links
rand10x40.link (Input,  Hidden)
rand10x40.link (Hidden, Output)

# read initial weights from Lens-generated file
rand10x40.read_Lens_weights_file (
    "rand10x40_train_no_recurrent_conn_weights.txt")

# read Lens-style examples file
set1 = rand10x40.read_Lens_examples_file ("rand10x40.ex")

# set network parameters
rand10x40.set (num_updates = 10,
               train_group_crit = 0.2
               )

# train the network
rand10x40.train (num_examples = 40)

# close the application
rand10x40.end ()
