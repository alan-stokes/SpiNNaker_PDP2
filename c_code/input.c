// SpiNNaker API
#include "spin1_api.h"

// graph-front-end
#include "common-typedefs.h"
#include <data_specification.h>
#include <simulation.h>

// mlp
#include "mlp_params.h"
#include "mlp_types.h"
#include "mlp_macros.h"
#include "mlp_externs.h"  // allows compiler to check extern types!

#include "init_i.h"
#include "comms_i.h"
#include "process_i.h"

// main methods for the input core

// ------------------------------------------------------------------------
// global "constants"
// ------------------------------------------------------------------------
// list of procedures for the FORWARD phase in the input pipeline. The order is
// relevant, as the index is defined in mlp_params.h
in_proc_t const
  i_in_procs[SPINN_NUM_IN_PROCS] =
  {
    in_integr, in_soft_clamp
  };

// list of procedures for the BACKPROP phase. Order is relevant, as the index
// needs to be the same as in the FORWARD phase. In case a routine is not
// available, then a NULL should replace the call
in_proc_back_t const
  i_in_back_procs[SPINN_NUM_IN_PROCS] =
  {
    in_integr_back, NULL
  };

// list of procedures for the initialization of the input pipeline. Order
// is relevant, as the index needs to be the same as in the FORWARD phase. In
// case one routine is not intended to be available because no initialization
// is required, then a NULL should replace the call
in_proc_init_t const
  i_init_in_procs[SPINN_NUM_IN_PROCS] =
  {
      init_in_integr, NULL
  };
// ------------------------------------------------------------------------

// ------------------------------------------------------------------------
// global variables
// ------------------------------------------------------------------------
uint chipID;               // 16-bit (x, y) chip ID
uint coreID;               // 5-bit virtual core ID

uint fwdKey;               // 32-bit packet ID for FORWARD phase
uint bkpKey;               // 32-bit packet ID for BACKPROP phase

uint         epoch;        // current training iteration
uint         example;      // current example in epoch
uint         evt;          // current event in example
uint         num_events;   // number of events in current example
uint         event_idx;    // index into current event
proc_phase_t phase;        // FORWARD or BACKPROP
uint         num_ticks;    // number of ticks in current event
uint         max_ticks;    // maximum number of ticks in current event
uint         min_ticks;    // minimum number of ticks in current event
uint         tick;         // current tick in phase
uchar        tick_stop;    // current tick stop decision

uint         to_epoch   = 0;
uint         to_example = 0;
uint         to_tick    = 0;

// ------------------------------------------------------------------------
// data structures in regions of SDRAM
// ------------------------------------------------------------------------
mlp_example_t    *ex; // example data
mlp_event_t      *ev; // event data
activation_t     *it; // example inputs
uint             *rt; // multicast routing keys data

// ------------------------------------------------------------------------
// network and core configurations (DTCM)
// ------------------------------------------------------------------------
network_conf_t ncfg;           // network-wide configuration parameters
i_conf_t       icfg;           // input core configuration parameters
// ------------------------------------------------------------------------

// ------------------------------------------------------------------------
// input core variables
// ------------------------------------------------------------------------
// input cores process the input values through a sequence of functions.
// ------------------------------------------------------------------------
long_net_t     * i_nets;            // unit nets computed in current tick
long_delta_t   * i_deltas;          // deltas computed in current tick
long_delta_t   * i_init_delta;      // deltas computed in initial tick
pkt_queue_t      i_pkt_queue;       // queue to hold received nets/deltas
uchar            i_active;          // processing b-d-ps from queue?

long_net_t     * i_last_integr_net; //last integrator output value
long_delta_t   * i_last_integr_delta; //last integrator delta value

uint             i_it_idx;          // index into current inputs/targets

// FORWARD phase specific
// (net processing)
scoreboard_t     if_done;           // current tick net computation done
uint             if_thrds_pend;     // sync. semaphore: proc & stop

// BACKPROP phase specific
// (delta processing)
long_delta_t   * ib_init_delta;     // initial delta value for every tick
scoreboard_t     ib_done;           // current tick delta computation done

// history arrays
long_net_t     * i_net_history;   //sdram pointer where to store input history
// ------------------------------------------------------------------------

#ifdef DEBUG
// ------------------------------------------------------------------------
// DEBUG variables
// ------------------------------------------------------------------------
uint pkt_sent = 0;  // total packets sent
uint sent_fwd = 0;  // packets sent in FORWARD phase
uint sent_bkp = 0;  // packets sent in BACKPROP phase
uint pkt_recv = 0;  // total packets received
uint recv_fwd = 0;  // packets received in FORWARD phase
uint recv_bkp = 0;  // packets received in BACKPROP phase
uint spk_sent = 0;  // sync packets sent
uint spk_recv = 0;  // sync packets received
uint stp_sent = 0;  // stop packets sent
uint stp_recv = 0;  // stop packets received
uint stn_recv = 0;  // network_stop packets received
uint wrng_phs = 0;  // packets received in wrong phase
uint wrng_tck = 0;  // FORWARD packets received in wrong tick
uint wrng_btk = 0;  // BACKPROP packets received in wrong tick
uint wght_ups = 0;  // number of weight updates done
uint tot_tick = 0;  // total number of ticks executed
// ------------------------------------------------------------------------
#endif


// ------------------------------------------------------------------------
// load configuration from SDRAM and initialise variables
// ------------------------------------------------------------------------
uint init ()
{
  io_printf (IO_BUF, "input\n");

  // read the data specification header
  data_specification_metadata_t * data =
          data_specification_get_data_address();
  if (!data_specification_read_header (data))
  {
	  return (SPINN_CFG_UNAVAIL);
  }

  // set up the simulation interface (system region)
  //NOTE: these variables are not used!
  uint32_t n_steps, run_forever, step;
  if (!simulation_steps_initialise(
      data_specification_get_region(SYSTEM, data),
      APPLICATION_NAME_HASH, &n_steps, &run_forever, &step, 0, 0))
  {
    return (SPINN_CFG_UNAVAIL);
  }

  // network configuration address
  address_t nt = data_specification_get_region (NETWORK, data);

  // initialise network configuration from SDRAM
  spin1_memcpy (&ncfg, nt, sizeof (network_conf_t));

  // core configuration address
  address_t dt = data_specification_get_region (CORE, data);

  // initialise core-specific configuration from SDRAM
  spin1_memcpy (&icfg, dt, sizeof (i_conf_t));

  // inputs iff this core receives inputs from examples file
  if (icfg.input_grp)
  {
	  it = (activation_t *) data_specification_get_region
		  (INPUTS, data);
  }

  // examples
  ex = (mlp_example_t *) data_specification_get_region
		  (EXAMPLES, data);

  // events
  ev = (mlp_event_t *) data_specification_get_region
		  (EVENTS, data);

  // routing keys
  rt = (uint *) data_specification_get_region
		  (ROUTING, data);

#ifdef DEBUG_CFG0
  io_printf (IO_BUF, "og: %d\n", icfg.output_grp);
  io_printf (IO_BUF, "ig: %d\n", icfg.input_grp);
  io_printf (IO_BUF, "nu: %d\n", icfg.num_units);
  io_printf (IO_BUF, "np: %d\n", icfg.num_in_procs);
  io_printf (IO_BUF, "p0: %d\n", icfg.procs_list[0]);
  io_printf (IO_BUF, "p1: %d\n", icfg.procs_list[1]);
  io_printf (IO_BUF, "ie: %d\n", icfg.in_integr_en);
  io_printf (IO_BUF, "dt: %f\n", icfg.in_integr_dt);
  io_printf (IO_BUF, "sc: %f\n", icfg.soft_clamp_strength);
  io_printf (IO_BUF, "in: %d\n", icfg.initNets);
  io_printf (IO_BUF, "io: %f\n", SPINN_LCONV_TO_PRINT(
  		icfg.initOutput, SPINN_ACTIV_SHIFT));
  io_printf (IO_BUF, "fk: 0x%08x\n", rt[FWD]);
  io_printf (IO_BUF, "bk: 0x%08x\n", rt[BKP]);
#endif

  // initialise epoch, example and event counters
  //TODO: alternative algorithms for choosing example order!
  epoch   = 0;
  example = 0;
  evt     = 0;

  // initialise phase
  phase = SPINN_FORWARD;

  // initialise number of events and event index
  num_events = ex[example].num_events;
  event_idx  = ex[example].ev_idx;

  // allocate memory and initialise variables
  uint rcode = i_init ();

  return (rcode);
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// timer callback: check that there has been progress in execution.
// If no progress has been made terminate with SPINN_TIMEOUT_EXIT exit code.
// ------------------------------------------------------------------------
void timeout (uint ticks, uint null)
{
  (void) ticks;
  (void) null;

  // check if progress has been made
  if ((to_epoch == epoch) && (to_example == example) && (to_tick == tick))
  {
    // report timeout error
    done(SPINN_TIMEOUT_EXIT);
  }
  else
  {
    // update checked variables
    to_epoch   = epoch;
    to_example = example;
    to_tick    = tick;
  }
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// start callback: get started by sending outputs to host and w cores.
// ------------------------------------------------------------------------
void get_started (void)
{
  // start log,
  io_printf (IO_BUF, "-----------------------\n");
  io_printf (IO_BUF, "starting simulation\n");

  // and enable deadlock check
  tc[T1_INT_CLR] = 1;
  tc[T1_LOAD] = sv->cpu_clk * SPINN_TIMER_TICK_PERIOD;
  vic[VIC_ENABLE] = (1 << TIMER1_INT);
  tc[T1_CONTROL] = 0xe2;
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// main: register callbacks and initialise basic system variables
// ------------------------------------------------------------------------
void c_main ()
{
  // say hello,
  io_printf (IO_BUF, ">> mlp\n");

  // get this core's IDs,
  chipID = spin1_get_chip_id();
  coreID = spin1_get_core_id();

  // initialise application,
  uint exit_code = init ();

  // check if init completed successfully,
  if (exit_code != SPINN_NO_ERROR)
  {
    // if init failed report results and abort simulation
    done(exit_code);
    rt_error(RTE_SWERR);
  }

#ifdef PROFILE
  // configure timer 2 for profiling
  // enabled, 32 bit, free running, 16x pre-scaler
  tc[T2_CONTROL] = SPINN_TIMER2_CONF;
  tc[T2_LOAD] = SPINN_TIMER2_LOAD;
#endif

  // timer1 callback (used for background deadlock check)
  spin1_callback_on (TIMER_TICK, timeout, SPINN_TIMER_P);

  // packet received callbacks
  spin1_callback_on (MC_PACKET_RECEIVED, i_receivePacket, SPINN_PACKET_P);
  spin1_callback_on (MCPL_PACKET_RECEIVED, i_receivePacket, SPINN_PACKET_P);

#ifdef PROFILE
  uint start_time = tc[T2_COUNT];
  io_printf (IO_BUF, "start count: %u\n", start_time);
#endif

  // setup simulation,
  simulation_set_start_function(get_started);
  simulation_set_uses_timer(FALSE);

  // start execution,
  simulation_run();

#ifdef PROFILE
  uint final_time = tc[T2_COUNT];
  io_printf (IO_BUF, "final count: %u\n", final_time);
  io_printf (IO_BUF, "execution time: %u us\n",
      (start_time - final_time) / SPINN_TIMER2_DIV);
#endif

  // and say goodbye
  io_printf (IO_BUF, "<< mlp\n");
}
// ------------------------------------------------------------------------
