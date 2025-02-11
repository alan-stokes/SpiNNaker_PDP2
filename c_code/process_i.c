/*
 * Copyright (c) 2015 The University of Manchester
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

// SpiNNaker API
#include "spin1_api.h"

// mlp
#include "mlp_params.h"
#include "mlp_types.h"
#include "mlp_macros.h"
#include "mlp_externs.h"

#include "init_i.h"
#include "process_i.h"
#include "activation.h"


// ------------------------------------------------------------------------
// input core computation routines
// ------------------------------------------------------------------------
// ------------------------------------------------------------------------
// process FORWARD phase: apply input pipeline elements
// ------------------------------------------------------------------------
void if_process (uint key, uint payload)
{
#ifdef DEBUG
  recv_fwd++;
  if (phase != SPINN_FORWARD)
    wrng_fph++;
#endif

#ifdef PROFILE
  // start profiler,
  tc[T2_LOAD] = SPINN_PROFILER_START;
#endif

  // get net index: mask out block and phase data,
  uint inx = key & SPINN_NET_MASK;

  // store received net to be processed,
  i_nets[inx] = (long_net_t) ((net_t) payload);

  net_t net_tmp;

  // compute unit input,
  //TODO: need to make sure this is the same as Lens
  compute_in (inx);

  // saturate and cast the long nets before sending,
  if (i_nets[inx] >= (long_net_t) SPINN_NET_MAX)
  {
    net_tmp = (net_t) SPINN_NET_MAX;
  }
  else if (i_nets[inx] <= (long_net_t) SPINN_NET_MIN)
  {
    net_tmp = (net_t) SPINN_NET_MIN;
  }
  else
  {
    net_tmp = (net_t) i_nets[inx];
  }

  // and incorporate net index to the packet key and send
  while (!spin1_send_mc_packet ((fwdKey | inx), net_tmp, WITH_PAYLOAD));

#ifdef DEBUG
  sent_fwd++;
#endif

#ifdef PROFILE
  // update profiler values,
  uint cnt = SPINN_PROFILER_START - tc[T2_COUNT];
  if (cnt < prf_fwd_min) prf_fwd_min = cnt;
  if (cnt > prf_fwd_max) prf_fwd_max = cnt;
#endif
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// process BACKPROP phase: apply BACKPROP input pipeline elements
// ------------------------------------------------------------------------
void ib_process (uint key, uint payload)
{
#ifdef DEBUG
  recv_bkp++;
  if (phase != SPINN_BACKPROP)
    wrng_bph++;
#endif

#ifdef PROFILE
  // start profiler,
  tc[T2_LOAD] = SPINN_PROFILER_START;
#endif

  // get delta index: mask out block and phase data,
  uint inx = key & SPINN_DELTA_MASK;

  // store received delta to be processed,
  i_deltas[inx] = ((long_delta_t) ((delta_t) payload))
    << (SPINN_LONG_DELTA_SHIFT - SPINN_DELTA_SHIFT);

  compute_in_back (inx);

  // saturate and cast the long deltas before sending
  long_delta_t delta_tmp = i_deltas[inx]
                         >> (SPINN_LONG_DELTA_SHIFT - SPINN_DELTA_SHIFT);
  delta_t delta;

  if (delta_tmp >= (long_delta_t) SPINN_DELTA_MAX)
  {
    delta = (delta_t) SPINN_DELTA_MAX;
  }
  else if (delta_tmp <= (long_delta_t) SPINN_DELTA_MIN)
  {
    delta = (delta_t) SPINN_DELTA_MIN;
  }
  else
  {
    delta = (delta_t) delta_tmp;
  }

  // incorporate delta index to the packet key and send,
  while (!spin1_send_mc_packet ((bkpKey | inx), delta, WITH_PAYLOAD));

#ifdef DEBUG
  sent_bkp++;
#endif

#ifdef PROFILE
  // update profiler values,
  uint cnt = SPINN_PROFILER_START - tc[T2_COUNT];
  if (cnt < prf_bkp_min) prf_bkp_min = cnt;
  if (cnt > prf_bkp_max) prf_bkp_max = cnt;
#endif
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// FORWARD phase: the tick has been completed, move to the next tick
// updating the indices to the events/examples as required
// ------------------------------------------------------------------------
void if_advance_tick (uint unused0, uint unused1)
{
  (void) unused0;
  (void) unused1;

#ifdef TRACE
  io_printf (IO_BUF, "if_advance_tick\n");
#endif

  // prepare to start tick,
  tick_init (!SPINN_RESTART, 0);

  // and check if end of event
  if (tick_stop)
  {
    if_advance_event ();
  }
  else
  {
    // if not done increment tick
    tick++;
  }
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// BACKPROP phase: the tick has been completed, move to the next tick
// updating the indices to the events/examples as required
// ------------------------------------------------------------------------
void ib_advance_tick (uint unused0, uint unused1)
{
  (void) unused0;
  (void) unused1;

#ifdef TRACE
  io_printf (IO_BUF, "ib_advance_tick\n");
#endif

  // prepare to start tick,
  tick_init (!SPINN_RESTART, 0);

  // and check if end of BACKPROP phase
  if (tick == SPINN_IB_END_TICK)
  {
    // initialise the tick count
    tick = SPINN_I_INIT_TICK;

    // switch to FORWARD phase,
    phase = SPINN_FORWARD;

    // and move to next example
    i_advance_example ();
  }
  else
  {
    // if not done decrement tick,
    tick--;

    // and restore nets
    restore_nets (tick);
  }
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// FORWARD phase: update the event at the end of a simulation tick
// ------------------------------------------------------------------------
void if_advance_event (void)
{
#ifdef TRACE
  io_printf (IO_BUF, "if_advance_event\n");
#endif

  // check if done with example's FORWARD phase
  if ((++evt >= num_events) || (tick == ncfg.global_max_ticks - 1))
  {
    // and check if in training mode
    if (xcfg.training)
    {
       // move on to BACKPROP phase
      phase = SPINN_BACKPROP;
    }
    else
    {
      // if not training, initialise ticks for the next example
      tick = SPINN_I_INIT_TICK;

      // then move to next example
      i_advance_example ();
    }
  }
  else
  {
    // if input or output group update input/target index
    //TODO: check if the target value is required in I cores
    // for the BACKPROP phase, otherwise remove the condition for the
    // output group
    if (icfg.input_grp || icfg.output_grp)
    {
      i_it_idx += icfg.num_units;
    }

    // and increment tick
    tick++;
  }
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// update example at the end of a (FORWARD or BACKPROP) tick
// ------------------------------------------------------------------------
void i_advance_example (void)
{
#ifdef TRACE
  io_printf (IO_BUF, "i_advance_example\n");
#endif

  // point to next example in the set - wrap around if at the end,
  if (++example_inx >= es->num_examples)
  {
    example_inx = 0;
  }

  // check if done with examples,
  if (++example_cnt >= xcfg.num_examples)
  {
    // prepare for next epoch,
    epoch++;

    // record the last example presented
    if (xcfg.training)
    {
      train_cnt = example_inx;
    }
    else
    {
      test_cnt = example_inx;
    }

    // access network stop flag with interrupts disabled,
    uint cpsr = spin1_int_disable ();

    // check if network stop decision ready,
    if (net_stop_rdy)
    {
      // clear flag,
      net_stop_rdy = FALSE;

      // restore interrupts after flag access,
      spin1_mode_restore (cpsr);

      // and decide what to do
      if (net_stop)
      {
        // finish stage and report no error
        //TODO: check if need to schedule or can simply call
        spin1_schedule_callback (stage_done, SPINN_NO_ERROR, 0, SPINN_DONE_P);
      }
    }
    else
    {
      // flag ready for net_stop decision,
      net_stop_rdy = TRUE;

      // and restore interrupts after flag access
      spin1_mode_restore (cpsr);
    }

    // and reset example count for next epoch
    example_cnt = 0;
  }

  // start from first event for next example,
  evt = 0;
  num_events = ex[example_inx].num_events;
  event_idx = ex[example_inx].ev_idx;

  // and initialise event input and target indices - if input or output group
  //TODO: check if the target value is required in I cores
  // for the BACKPROP phase, otherwise remove condition for output group
  if (icfg.input_grp || icfg.output_grp)
  {
    i_it_idx = ev[event_idx].it_idx * icfg.num_units;
  }

  // if the input INTEGRATOR is used reset the array of last values
  if (icfg.in_integr_en)
    for (uint i = 0; i < icfg.num_units; i++)
    {
      i_last_integr_net[i] = (long_net_t) icfg.initNets;
      i_last_integr_delta[i] = 0;
    }
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// FORWARD phase:
// call the elements in the input pipeline
// ------------------------------------------------------------------------
void compute_in (uint inx)
{
#ifdef TRACE
  io_printf (IO_BUF, "compute_in\n");
#endif

  for (uint i = 0; i < icfg.num_in_procs; i++)
  {
    i_in_procs[icfg.procs_list[i]] (inx);
  }

  // check if in training mode, and if so, store nets
  //TODO: for non-continuous networks, this needs to check the requirement
  // to have these histories saved, which needs to come as a configuration
  // parameter. For continuous networks, these histories are always required.
  if (xcfg.training)
  {
    store_net(inx);
  }
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// input INTEGRATOR element
// ------------------------------------------------------------------------
void in_integr (uint inx)
{
#ifdef TRACE
  io_printf (IO_BUF, "in_integr\n");
#endif

  // use stored value if in deadlock recovery
  long_net_t last_net = i_last_integr_net[inx];
  if (dlrv)
  {
    last_net = i_last_integr_net_dlrv[inx];
  }
  else
  {
    // remember last value in case of deadlock recovery
    i_last_integr_net_dlrv[inx] = i_last_integr_net[inx];

    last_net = i_last_integr_net[inx];
  }

  long_net_t  desired_net = i_nets[inx];
  long_fpreal dt = icfg.in_integr_dt;

  // compute the new value of the net as indicated by lens
  // all the variables are expanded to long types to avoid overflows and wrap-around
  long_net_t net = last_net + (dt * (desired_net - last_net) >> SPINN_LONG_FPREAL_SHIFT);

  // saturate the value computed and assign it to the nets variable
  // to be used in the next stage of computation
  if (net > (long_net_t) SPINN_NET_MAX)
    i_nets[inx] = (long_net_t) SPINN_NET_MAX;
  else if (net < (long_net_t) SPINN_NET_MIN)
    i_nets[inx] = (long_net_t) SPINN_NET_MIN;
  else
    i_nets[inx] = (long_net_t) net;

  // store the outcome of the computation for the next tick
  i_last_integr_net[inx] = i_nets[inx];
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
//soft clamp element
// ------------------------------------------------------------------------
void in_soft_clamp (uint inx)
{
#ifdef TRACE
  io_printf (IO_BUF, "in_soft_clamp\n");
#endif

  // compute only if input is not NaN
  if (it[i_it_idx + inx] != SPINN_ACTIV_NaN)
  {
    long_activ_t external_input = it[i_it_idx + inx];

    long_fpreal soft_clamp_strength = icfg.soft_clamp_strength;

    long_activ_t init_output = icfg.initOutput;

    // computation of the soft clamp operator following Lens code
    long_activ_t output = init_output
                             + ((soft_clamp_strength
                                 * (external_input - init_output))
                                   >> SPINN_FPREAL_SHIFT
                               );

    i_nets[inx] += inv_sigmoid((short_activ_t) (output << (SPINN_ACTIV_SHIFT - SPINN_SHORT_ACTIV_SHIFT)));
  }
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// routine which computes the BACKPROP phase of the computation of the
// input elements pipeline
// ------------------------------------------------------------------------
void compute_in_back (uint inx)
{
#ifdef TRACE
  io_printf (IO_BUF, "compute_in_back\n");
#endif

  // the set of procedures needs to be executed in the reverse order, starting
  // from the last input pipeline element, and executing the routine only if the
  // element in the list is not NULL
  if (icfg.num_in_procs >= 1)
  {
    for (int i = icfg.num_in_procs - 1; i >= 0; i--)
    {
      if (i_in_back_procs[icfg.procs_list[i]] != NULL)
        i_in_back_procs[icfg.procs_list[i]] (inx);
    }
  }
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// compute the input integration operation for the BACKPROP phase
// ------------------------------------------------------------------------
void in_integr_back (uint inx)
{
#ifdef TRACE
  io_printf (IO_BUF, "in_integr_back\n");
#endif

  // use stored value if in deadlock recovery
  long_delta_t last_delta;
  if (dlrv)
  {
    last_delta = i_last_integr_delta_dlrv[inx];
  }
  else
  {
    // remember last value in case of deadlock recovery
    i_last_integr_delta_dlrv[inx] = i_last_integr_delta[inx];

    last_delta = i_last_integr_delta[inx];
  }

  long_fpreal dt = icfg.in_integr_dt;

  long_delta_t d = (dt * last_delta) >> SPINN_FPREAL_SHIFT;

  last_delta += i_deltas[inx] - d;

  i_deltas[inx] = d;

  // store the INTEGRATOR state for the next iteration
  i_last_integr_delta[inx] = last_delta;
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
/* There is no softClampInputBack in Lens*/
/*
void in_soft_clamp_back (uint inx)
{
#ifdef TRACE
  io_printf (IO_BUF, "in_soft_clamp_back\n");
#endif
}
*/
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// stores unit net received for the current tick
// ------------------------------------------------------------------------
void store_net (uint inx)
{
#ifdef TRACE
  io_printf (IO_BUF, "store_nets\n");
#endif

  i_net_history[(tick * icfg.num_units) + inx] = i_nets[inx];
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// restores unit net for the requested tick
// ------------------------------------------------------------------------
void restore_net (uint inx, uint tick)
{
#ifdef TRACE
  io_printf (IO_BUF, "restore_net\n");
#endif

  i_nets[inx] = i_net_history[(tick * icfg.num_units) + inx];
}
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// restores all unit nets for the requested tick
// ------------------------------------------------------------------------
void restore_nets (uint tick)
{
#ifdef TRACE
  io_printf (IO_BUF, "restore_nets\n");
#endif

  for (uint inx = 0; inx < icfg.num_units; inx++)
  {
    i_nets[inx] = i_net_history[(tick * icfg.num_units) + inx];
  }
}
// ------------------------------------------------------------------------
