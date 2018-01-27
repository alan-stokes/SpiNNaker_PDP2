#ifndef __MLP_EXTERNS_H__
#define __MLP_EXTERNS_H__

// ------------------------------------------------------------------------
// global variables
// ------------------------------------------------------------------------
extern uint coreID;               // 5-bit virtual core ID

extern uint fwdKey;               // 32-bit packet ID for FORWARD phase
extern uint bkpKey;               // 32-bit packet ID for BACKPROP phase

extern uint         epoch;        // current training iteration
extern uint         example;      // current example in epoch
extern uint         evt;          // current event in example
extern uint         num_events;   // number of events in current example
extern uint         event_idx;    // index into current event
extern uint         num_ticks;    // number of ticks in current event
extern uint         max_ticks;    // maximum number of ticks in current event
extern uint         min_ticks;    // minimum number of ticks in current event
extern uint         tick;         // current tick in phase
extern uchar        tick_stop;    // current tick stop decision
extern uint         ev_tick;      // current tick in event
extern proc_phase_t phase;        // FORWARD or BACKPROP

extern uint                 *rt; // multicast routing keys data
extern weight_t             *wt; // initial connection weights
extern struct mlp_set       *es; // example set data
extern struct mlp_example   *ex; // example data
extern struct mlp_event     *ev; // event data
extern activation_t         *it; // example inputs
extern activation_t         *tt; // example targets

// ------------------------------------------------------------------------
// network and core configurations
// ------------------------------------------------------------------------
extern network_conf_t ncfg;       // network-wide configuration parameters
extern w_conf_t       wcfg;       // weight core configuration parameters
extern s_conf_t       scfg;       // sum core configuration parameters
extern i_conf_t       icfg;       // input core configuration parameters
extern t_conf_t       tcfg;       // threshold core configuration parameters
// ------------------------------------------------------------------------

// ------------------------------------------------------------------------
// weight core variables
// ------------------------------------------------------------------------
extern weight_t       * * w_weights;     // connection weights block
extern long_wchange_t * * w_wchanges;    // accumulated weight changes
extern activation_t     * w_outputs[2]; // unit outputs for b-d-p
extern long_delta_t   * * w_link_deltas; // computed link deltas
extern error_t          * w_errors;      // computed errors next tick
extern pkt_queue_t        w_delta_pkt_q; // queue to hold received deltas
extern fpreal             w_delta_dt;    // scaling factor for link deltas
extern uint               wf_procs;      // pointer to processing unit outputs
extern uint               wf_comms;      // pointer to receiving unit outputs
extern scoreboard_t       wf_arrived;    // keeps track of received unit outputs
extern uint               wf_thrds_done; // sync. semaphore: comms, proc & stop
extern uint               wf_sync_key;   // FORWARD processing can start
extern uchar              wb_active;     // processing deltas from queue?
extern scoreboard_t       wb_arrived;    // keeps track of received deltas
extern uint               wb_sync_key;   // BACKPROP processing can start

// history arrays
extern activation_t     * w_output_history;
// ------------------------------------------------------------------------

// ------------------------------------------------------------------------
// sum core variables
// ------------------------------------------------------------------------
extern long_net_t     * s_nets[2];     // unit nets computed in current tick
extern long_error_t   * s_errors[2];   // errors computed in current tick
extern pkt_queue_t      s_pkt_queue;   // queue to hold received b-d-ps
extern uchar            s_active;      // processing b-d-ps from queue?
extern scoreboard_t   * sf_arrived[2]; // keep track of expected net b-d-p
extern scoreboard_t     sf_done;       // current tick net computation done
extern uint             sf_thrds_done; // sync. semaphore: proc & stop
extern scoreboard_t   * sb_arrived[2]; // keep track of expected error b-d-p
extern scoreboard_t     sb_done;       // current tick error computation done
// ------------------------------------------------------------------------

// ------------------------------------------------------------------------
// input core variables
// ------------------------------------------------------------------------
// global "constants"
//list of input pipeline procedures
extern in_proc_t      const i_in_procs[SPINN_NUM_IN_PROCS];
extern in_proc_back_t const i_in_back_procs[SPINN_NUM_IN_PROCS];
//list of initialization procedures for input pipeline
extern in_proc_init_t const i_init_in_procs[SPINN_NUM_IN_PROCS];

extern long_net_t     * i_nets;        // unit nets computed in current tick
extern long_delta_t   * i_deltas;      // deltas computed in current tick
extern long_delta_t   * i_init_delta;  // deltas computed in first tick
extern pkt_queue_t      i_pkt_queue;   // queue to hold received nets/deltas
extern uchar            i_active;      // processing b-d-ps from queue?
extern uint             i_it_idx;      // index into current inputs/targets
extern scoreboard_t     if_done;       // current tick net computation done
extern uint             if_thrds_done; // sync. semaphore: proc & stop
extern long_delta_t   * ib_init_delta; // initial delta value for every tick
extern scoreboard_t     ib_done;       // current tick delta computation done
extern long_net_t     * i_last_integr_net;   //last integrator output value
extern long_delta_t   * i_last_integr_delta; //last integrator delta value

// history arrays
extern long_net_t      * i_net_history; //sdram pointer where to store input history
// ------------------------------------------------------------------------

// ------------------------------------------------------------------------
// threshold core variables
// ------------------------------------------------------------------------
// global "constants"
// list of output pipeline procedures
extern out_proc_t      const t_out_procs[SPINN_NUM_OUT_PROCS];
extern out_proc_back_t const t_out_back_procs[SPINN_NUM_OUT_PROCS];
// list of stop eval procedures
extern stop_crit_t     const t_stop_procs[SPINN_NUM_STOP_PROCS];
// list of initialization procedures for output pipeline
extern out_proc_init_t const t_init_out_procs[SPINN_NUM_OUT_PROCS];
extern out_error_t     const t_out_error[SPINN_NUM_ERROR_PROCS];

extern activation_t   * t_outputs;     // current tick unit outputs
extern net_t          * t_nets;        // nets received from sum cores
extern error_t        * t_errors[2];   // error banks: current and next tick
extern activation_t   * t_last_integr_output;   //last integrator output value
extern long_deriv_t   * t_last_integr_output_deriv; //last integr output deriv
extern activation_t   * t_instant_outputs; // output stored BACKPROP
extern uchar            t_hard_clamp_en;   // hard clamp output enabled
extern uint             t_it_idx;      // index into current inputs/targets
extern uint             t_tot_ticks;   // total ticks on current example
extern pkt_queue_t      t_net_pkt_q;   // queue to hold received nets
extern uchar            t_active;      // processing nets/errors from queue?
extern scoreboard_t     t_sync_arrived; // keep track of expected sync packets
extern uchar            t_sync_done;   // have expected sync packets arrived?
extern sdp_msg_t        t_sdp_msg;     // SDP message buffer for host comms.
extern scoreboard_t     tf_arrived;    // keep track of expected nets
extern uint             tf_thrds_done; // sync. semaphore: proc & stop
extern uchar            tf_chain_prev; // previous daisy chain (DC) value
extern uchar            tf_chain_init; // previous DC received init
extern uchar            tf_chain_rdy;  // local DC value can be forwarded
extern uchar            tf_stop_crit;  // stop criterion met?
extern stop_crit_t      tf_stop_func;  // stop evaluation function
extern uint             tf_stop_key;   // stop criterion packet key
extern uint             tb_procs;      // pointer to processing errors
extern uint             tb_comms;      // pointer to receiving errors
extern scoreboard_t     tb_arrived;    // keep track of expected errors
extern uint             tb_thrds_done; // sync. semaphore: proc & stop
extern int              t_max_output_unit; // unit with highest output
extern int              t_max_target_unit; // unit with highest target
extern activation_t     t_max_output;      // highest output value
extern activation_t     t_max_target;      // highest target value
extern long_deriv_t   * t_output_deriv;
extern delta_t        * t_deltas;

// history arrays
extern net_t          * t_net_history;
extern activation_t   * t_output_history;
extern activation_t   * t_target_history;
extern long_deriv_t   * t_output_deriv_history;
// ------------------------------------------------------------------------

// ------------------------------------------------------------------------
// DEBUG variables
// ------------------------------------------------------------------------
#ifdef DEBUG
  extern uint pkt_sent;  // total packets sent
  extern uint sent_fwd;  // packets sent in FORWARD phase
  extern uint sent_bkp;  // packets sent in BACKPROP phase
  extern uint pkt_recv;  // total packets received
  extern uint recv_fwd;  // packets received in FORWARD phase
  extern uint recv_bkp;  // packets received in BACKPROP phase
  extern uint spk_sent;  // sync packets sent
  extern uint spk_recv;  // sync packets received
  extern uint stp_sent;  // stop packets sent
  extern uint stp_recv;  // stop packets received
  extern uint tot_tick;  // total number of ticks executed
  extern uint wght_ups;  // number of weight updates done
  extern uint wrng_phs;  // packets received in wrong phase
  extern uint wrng_tck;  // FORWARD packets received in wrong tick
  extern uint wrng_btk;  // BACKPROP packets received in wrong tick
#endif
// ------------------------------------------------------------------------

#endif
