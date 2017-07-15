import logging

from pacman.model.constraints.placer_constraints\
    .placer_chip_and_core_constraint import PlacerChipAndCoreConstraint

import spinnaker_graph_front_end as g

from pacman.model.graphs.machine import MachineEdge

from input_vertex     import InputVertex
from sum_vertex       import SumVertex
from threshold_vertex import ThresholdVertex
from weight_vertex    import WeightVertex

logger = logging.getLogger (__name__)

#-----------------------------------------------------------
# rand10x40
#
# hard-coded implementation of the machine graph
# for Lens' example rand10x40.
#
#-----------------------------------------------------------

# Set up the simulation
g.setup ()

#------v- bias layer (group 2) -v------
# instantiate group 2 cores and place them appropriately
wv2_2 = WeightVertex    (group=2, frm_grp = 2, chip_x=0, chip_y=0, core=1)
wv2_3 = WeightVertex    (group=2, frm_grp = 3, chip_x=0, chip_y=0, core=2)
wv2_4 = WeightVertex    (group=2, frm_grp = 4, chip_x=0, chip_y=0, core=3)
wv2_5 = WeightVertex    (group=2, frm_grp = 5, chip_x=0, chip_y=0, core=4)
sv2   = SumVertex       (group=2, chip_x=0, chip_y=0, core=5)
iv2   = InputVertex     (group=2, chip_x=0, chip_y=0, core=6)
tv2   = ThresholdVertex (group=2, chip_x=0, chip_y=0, core=7)

# add group 2 vertices to graph
g.add_machine_vertex_instance (wv2_2)
g.add_machine_vertex_instance (wv2_3)
g.add_machine_vertex_instance (wv2_4)
g.add_machine_vertex_instance (wv2_5)
g.add_machine_vertex_instance (sv2)
g.add_machine_vertex_instance (iv2)
g.add_machine_vertex_instance (tv2)

# place group 2 vertices to match pacman48 (temporary constraint)
wv2_2.add_constraint (PlacerChipAndCoreConstraint (0, 0, 1))
wv2_3.add_constraint (PlacerChipAndCoreConstraint (0, 0, 2))
wv2_4.add_constraint (PlacerChipAndCoreConstraint (0, 0, 3))
wv2_5.add_constraint (PlacerChipAndCoreConstraint (0, 0, 4))
sv2.add_constraint   (PlacerChipAndCoreConstraint (0, 0, 5))
iv2.add_constraint   (PlacerChipAndCoreConstraint (0, 0, 6))
tv2.add_constraint   (PlacerChipAndCoreConstraint (0, 0, 7))
#------^- bias layer (group 2) -^------


#------v- input layer (group 3) -v------
# instantiate group 3 cores and place them appropriately
wv3_2 = WeightVertex    (group=3, frm_grp = 2, chip_x=0, chip_y=0, core=8)
wv3_3 = WeightVertex    (group=3, frm_grp = 3, chip_x=0, chip_y=0, core=9)
wv3_4 = WeightVertex    (group=3, frm_grp = 4, chip_x=0, chip_y=0, core=10)
wv3_5 = WeightVertex    (group=3, frm_grp = 5, chip_x=0, chip_y=0, core=11)
sv3   = SumVertex       (group=3, chip_x=0, chip_y=0, core=12)
iv3   = InputVertex     (group=3, chip_x=0, chip_y=0, core=13)
tv3   = ThresholdVertex (group=3, chip_x=0, chip_y=0, core=14)

# add group 3 vertices to graph
g.add_machine_vertex_instance (wv3_2)
g.add_machine_vertex_instance (wv3_3)
g.add_machine_vertex_instance (wv3_4)
g.add_machine_vertex_instance (wv3_5)
g.add_machine_vertex_instance (sv3)
g.add_machine_vertex_instance (iv3)
g.add_machine_vertex_instance (tv3)

# place group 3 vertices to match pacman48 (temporary constraint)
wv3_2.add_constraint (PlacerChipAndCoreConstraint (0, 0, 8))
wv3_3.add_constraint (PlacerChipAndCoreConstraint (0, 0, 9))
wv3_4.add_constraint (PlacerChipAndCoreConstraint (0, 0, 10))
wv3_5.add_constraint (PlacerChipAndCoreConstraint (0, 0, 11))
sv3.add_constraint   (PlacerChipAndCoreConstraint (0, 0, 12))
iv3.add_constraint   (PlacerChipAndCoreConstraint (0, 0, 13))
tv3.add_constraint   (PlacerChipAndCoreConstraint (0, 0, 14))
#------^- input layer (group 3) -^------


#------v- hidden layer (group 4) -v------
# instantiate group 4 cores and place them appropriately
wv4_2 = WeightVertex    (group=4, frm_grp = 2, chip_x=0, chip_y=0, core=15)
wv4_3 = WeightVertex    (group=4, frm_grp = 3, chip_x=0, chip_y=0, core=16)
wv4_4 = WeightVertex    (group=4, frm_grp = 4, chip_x=0, chip_y=1, core=1)
wv4_5 = WeightVertex    (group=4, frm_grp = 5, chip_x=0, chip_y=1, core=2)
sv4   = SumVertex       (group=4, chip_x=0, chip_y=1, core=3)
iv4   = InputVertex     (group=4, chip_x=0, chip_y=1, core=4)
tv4   = ThresholdVertex (group=4, chip_x=0, chip_y=1, core=5)

# add group 4 vertices to graph
g.add_machine_vertex_instance (wv4_2)
g.add_machine_vertex_instance (wv4_3)
g.add_machine_vertex_instance (wv4_4)
g.add_machine_vertex_instance (wv4_5)
g.add_machine_vertex_instance (sv4)
g.add_machine_vertex_instance (iv4)
g.add_machine_vertex_instance (tv4)

# place group 4 vertices to match pacman48 (temporary constraint)
wv4_2.add_constraint (PlacerChipAndCoreConstraint (0, 0, 15))
#wv4_3.add_constraint (PlacerChipAndCoreConstraint (0, 0, 16))
wv4_4.add_constraint (PlacerChipAndCoreConstraint (0, 1, 1))
wv4_5.add_constraint (PlacerChipAndCoreConstraint (0, 1, 2))
sv4.add_constraint   (PlacerChipAndCoreConstraint (0, 1, 3))
iv4.add_constraint   (PlacerChipAndCoreConstraint (0, 1, 4))
tv4.add_constraint   (PlacerChipAndCoreConstraint (0, 1, 5))
#------^- hidden layer (group 4) -^------


#------v- output layer (group 5) -v------
# instantiate group 5 cores and place them appropriately
wv5_2 = WeightVertex    (group=5, frm_grp = 2, chip_x=0, chip_y=1, core=6)
wv5_3 = WeightVertex    (group=5, frm_grp = 3, chip_x=0, chip_y=1, core=7)
wv5_4 = WeightVertex    (group=5, frm_grp = 4, chip_x=0, chip_y=1, core=8)
wv5_5 = WeightVertex    (group=5, frm_grp = 5, chip_x=0, chip_y=1, core=9)
sv5   = SumVertex       (group=5, chip_x=0, chip_y=1, core=10)
iv5   = InputVertex     (group=5, chip_x=0, chip_y=1, core=11)
tv5   = ThresholdVertex (group=5, chip_x=0, chip_y=1, core=12)

# add group 5 vertices to graph
g.add_machine_vertex_instance (wv5_2)
g.add_machine_vertex_instance (wv5_3)
g.add_machine_vertex_instance (wv5_4)
g.add_machine_vertex_instance (wv5_5)
g.add_machine_vertex_instance (sv5)
g.add_machine_vertex_instance (iv5)
g.add_machine_vertex_instance (tv5)

# place group 5 vertices to match pacman48 (temporary constraint)
wv5_2.add_constraint (PlacerChipAndCoreConstraint (0, 1, 6))
wv5_3.add_constraint (PlacerChipAndCoreConstraint (0, 1, 7))
wv5_4.add_constraint (PlacerChipAndCoreConstraint (0, 1, 8))
wv5_5.add_constraint (PlacerChipAndCoreConstraint (0, 1, 9))
sv5.add_constraint   (PlacerChipAndCoreConstraint (0, 1, 10))
iv5.add_constraint   (PlacerChipAndCoreConstraint (0, 1, 11))
tv5.add_constraint   (PlacerChipAndCoreConstraint (0, 1, 12))
#-------^- output layer (group 5) -^------


#-------v- group 2 network links -v------
# add group 2 forward links
g.add_machine_edge_instance (MachineEdge (wv2_2, sv2), wv2_2.fwd_link)
g.add_machine_edge_instance (MachineEdge (wv2_3, sv2), wv2_3.fwd_link)
g.add_machine_edge_instance (MachineEdge (wv2_4, sv2), wv2_4.fwd_link)
g.add_machine_edge_instance (MachineEdge (wv2_5, sv2), wv2_5.fwd_link)
g.add_machine_edge_instance (MachineEdge (sv2, iv2), sv2.fwd_link)
g.add_machine_edge_instance (MachineEdge (iv2, tv2), iv2.fwd_link)
g.add_machine_edge_instance (MachineEdge (tv2, wv2_2), tv2.fwd_link)
g.add_machine_edge_instance (MachineEdge (tv2, wv3_2), tv2.fwd_link)
g.add_machine_edge_instance (MachineEdge (tv2, wv4_2), tv2.fwd_link)
g.add_machine_edge_instance (MachineEdge (tv2, wv5_2), tv2.fwd_link)

# add group 2 backprop links
g.add_machine_edge_instance (MachineEdge (wv2_2, sv2), wv2_2.bkp_link)
g.add_machine_edge_instance (MachineEdge (wv2_3, sv3), wv2_3.bkp_link)
g.add_machine_edge_instance (MachineEdge (wv2_4, sv4), wv2_4.bkp_link)
g.add_machine_edge_instance (MachineEdge (wv2_5, sv5), wv2_5.bkp_link)
g.add_machine_edge_instance (MachineEdge (sv2, tv2), sv2.bkp_link)
g.add_machine_edge_instance (MachineEdge (tv2, iv2), tv2.bkp_link)
g.add_machine_edge_instance (MachineEdge (iv2, wv2_2), iv2.bkp_link)
g.add_machine_edge_instance (MachineEdge (iv2, wv2_3), iv2.bkp_link)
g.add_machine_edge_instance (MachineEdge (iv2, wv2_4), iv2.bkp_link)
g.add_machine_edge_instance (MachineEdge (iv2, wv2_5), iv2.bkp_link)

# add group 2 fwd sync links
g.add_machine_edge_instance (MachineEdge (wv2_2, tv2), wv2_2.fds_link)
g.add_machine_edge_instance (MachineEdge (wv2_3, tv3), wv2_3.fds_link)
g.add_machine_edge_instance (MachineEdge (wv2_4, tv4), wv2_4.fds_link)
g.add_machine_edge_instance (MachineEdge (wv2_5, tv5), wv2_5.fds_link)

# add group 2 stop links
g.add_machine_edge_instance (MachineEdge (tv2, tv3), tv2.stp_link)
#-------^- group 2 network links -^------

#-------v- group 3 network links -v------
# add group 3 forward links
g.add_machine_edge_instance (MachineEdge (wv3_2, sv3), wv3_2.fwd_link)
g.add_machine_edge_instance (MachineEdge (wv3_3, sv3), wv3_3.fwd_link)
g.add_machine_edge_instance (MachineEdge (wv3_4, sv3), wv3_4.fwd_link)
g.add_machine_edge_instance (MachineEdge (wv3_5, sv3), wv3_5.fwd_link)
g.add_machine_edge_instance (MachineEdge (sv3, iv3), sv3.fwd_link)
g.add_machine_edge_instance (MachineEdge (iv3, tv3), iv3.fwd_link)
g.add_machine_edge_instance (MachineEdge (tv3, wv2_3), tv3.fwd_link)
g.add_machine_edge_instance (MachineEdge (tv3, wv3_3), tv3.fwd_link)
g.add_machine_edge_instance (MachineEdge (tv3, wv4_3), tv3.fwd_link)
g.add_machine_edge_instance (MachineEdge (tv3, wv5_3), tv3.fwd_link)

# add group 3 backprop links
g.add_machine_edge_instance (MachineEdge (wv3_2, sv2), wv3_2.bkp_link)
g.add_machine_edge_instance (MachineEdge (wv3_3, sv3), wv3_3.bkp_link)
g.add_machine_edge_instance (MachineEdge (wv3_4, sv4), wv3_4.bkp_link)
g.add_machine_edge_instance (MachineEdge (wv3_5, sv5), wv3_5.bkp_link)
g.add_machine_edge_instance (MachineEdge (sv3, tv3), sv3.bkp_link)
g.add_machine_edge_instance (MachineEdge (tv3, iv3), tv3.bkp_link)
g.add_machine_edge_instance (MachineEdge (iv3, wv3_2), iv3.bkp_link)
g.add_machine_edge_instance (MachineEdge (iv3, wv3_3), iv3.bkp_link)
g.add_machine_edge_instance (MachineEdge (iv3, wv3_4), iv3.bkp_link)
g.add_machine_edge_instance (MachineEdge (iv3, wv3_5), iv3.bkp_link)

# add group 3 fwd sync links
g.add_machine_edge_instance (MachineEdge (wv3_2, tv2), wv3_2.fds_link)
g.add_machine_edge_instance (MachineEdge (wv3_3, tv3), wv3_3.fds_link)
g.add_machine_edge_instance (MachineEdge (wv3_4, tv4), wv3_4.fds_link)
g.add_machine_edge_instance (MachineEdge (wv3_5, tv5), wv3_5.fds_link)

# add group 3 stop links
g.add_machine_edge_instance (MachineEdge (tv3, tv4), tv3.stp_link)
#-------^- group 3 network links -^------

#-------v- group 4 network links -v------
# add group 4 forward links
g.add_machine_edge_instance (MachineEdge (wv4_2, sv4), wv4_2.fwd_link)
g.add_machine_edge_instance (MachineEdge (wv4_3, sv4), wv4_3.fwd_link)
g.add_machine_edge_instance (MachineEdge (wv4_4, sv4), wv4_4.fwd_link)
g.add_machine_edge_instance (MachineEdge (wv4_5, sv4), wv4_5.fwd_link)
g.add_machine_edge_instance (MachineEdge (sv4, iv4), sv4.fwd_link)
g.add_machine_edge_instance (MachineEdge (iv4, tv4), iv4.fwd_link)
g.add_machine_edge_instance (MachineEdge (tv4, wv2_4), tv4.fwd_link)
g.add_machine_edge_instance (MachineEdge (tv4, wv3_4), tv4.fwd_link)
g.add_machine_edge_instance (MachineEdge (tv4, wv4_4), tv4.fwd_link)
g.add_machine_edge_instance (MachineEdge (tv4, wv5_4), tv4.fwd_link)

# add group 4 backprop links
g.add_machine_edge_instance (MachineEdge (wv4_2, sv2), wv4_2.bkp_link)
g.add_machine_edge_instance (MachineEdge (wv4_3, sv3), wv4_3.bkp_link)
g.add_machine_edge_instance (MachineEdge (wv4_4, sv4), wv4_4.bkp_link)
g.add_machine_edge_instance (MachineEdge (wv4_5, sv5), wv4_5.bkp_link)
g.add_machine_edge_instance (MachineEdge (sv4, tv4), sv4.bkp_link)
g.add_machine_edge_instance (MachineEdge (tv4, iv4), tv4.bkp_link)
g.add_machine_edge_instance (MachineEdge (iv4, wv4_2), iv4.bkp_link)
g.add_machine_edge_instance (MachineEdge (iv4, wv4_3), iv4.bkp_link)
g.add_machine_edge_instance (MachineEdge (iv4, wv4_4), iv4.bkp_link)
g.add_machine_edge_instance (MachineEdge (iv4, wv4_5), iv4.bkp_link)

# add group 4 fwd sync links
g.add_machine_edge_instance (MachineEdge (wv4_2, tv2), wv4_2.fds_link)
g.add_machine_edge_instance (MachineEdge (wv4_3, tv3), wv4_3.fds_link)
g.add_machine_edge_instance (MachineEdge (wv4_4, tv4), wv4_4.fds_link)
g.add_machine_edge_instance (MachineEdge (wv4_5, tv5), wv4_5.fds_link)

# add group 4 stop links
g.add_machine_edge_instance (MachineEdge (tv4, tv5), tv4.stp_link)
#-------^- group 4 network links -^------

#-------v- group 5 network links -v------
# add group 5 forward links
g.add_machine_edge_instance (MachineEdge (wv5_2, sv5), wv5_2.fwd_link)
g.add_machine_edge_instance (MachineEdge (wv5_3, sv5), wv5_3.fwd_link)
g.add_machine_edge_instance (MachineEdge (wv5_4, sv5), wv5_4.fwd_link)
g.add_machine_edge_instance (MachineEdge (wv5_5, sv5), wv5_5.fwd_link)
g.add_machine_edge_instance (MachineEdge (sv5, iv5), sv5.fwd_link)
g.add_machine_edge_instance (MachineEdge (iv5, tv5), iv5.fwd_link)
g.add_machine_edge_instance (MachineEdge (tv5, wv2_5), tv5.fwd_link)
g.add_machine_edge_instance (MachineEdge (tv5, wv3_5), tv5.fwd_link)
g.add_machine_edge_instance (MachineEdge (tv5, wv4_5), tv5.fwd_link)
g.add_machine_edge_instance (MachineEdge (tv5, wv5_5), tv5.fwd_link)

# add group 5 backprop links
g.add_machine_edge_instance (MachineEdge (wv5_2, sv2), wv5_2.bkp_link)
g.add_machine_edge_instance (MachineEdge (wv5_3, sv3), wv5_3.bkp_link)
g.add_machine_edge_instance (MachineEdge (wv5_4, sv4), wv5_4.bkp_link)
g.add_machine_edge_instance (MachineEdge (wv5_5, sv5), wv5_5.bkp_link)
g.add_machine_edge_instance (MachineEdge (sv5, tv5), sv5.bkp_link)
g.add_machine_edge_instance (MachineEdge (tv5, iv5), tv5.bkp_link)
g.add_machine_edge_instance (MachineEdge (iv5, wv5_2), iv5.bkp_link)
g.add_machine_edge_instance (MachineEdge (iv5, wv5_3), iv5.bkp_link)
g.add_machine_edge_instance (MachineEdge (iv5, wv5_4), iv5.bkp_link)
g.add_machine_edge_instance (MachineEdge (iv5, wv5_5), iv5.bkp_link)

# add group 5 fwd sync links
g.add_machine_edge_instance (MachineEdge (wv5_2, tv2), wv5_2.fds_link)
g.add_machine_edge_instance (MachineEdge (wv5_3, tv3), wv5_3.fds_link)
g.add_machine_edge_instance (MachineEdge (wv5_4, tv4), wv5_4.fds_link)
g.add_machine_edge_instance (MachineEdge (wv5_5, tv5), wv5_5.fds_link)

# add group 5 stop links
g.add_machine_edge_instance (MachineEdge (tv5, wv2_2), tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, wv2_3), tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, wv2_4), tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, wv2_5), tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, sv2),   tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, iv2),   tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, tv2),   tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, wv3_2), tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, wv3_3), tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, wv3_4), tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, wv3_5), tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, sv3),   tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, iv3),   tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, tv3),   tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, wv4_2), tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, wv4_3), tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, wv4_4), tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, wv4_5), tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, sv4),   tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, iv4),   tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, tv4),   tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, wv5_2), tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, wv5_3), tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, wv5_4), tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, wv5_5), tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, sv5),   tv5.stp_link)
g.add_machine_edge_instance (MachineEdge (tv5, iv5),   tv5.stp_link)
#-------^- group 5 network links -^------

# Run the simulation
g.run (None)

# close the machine
# g.stop ()
