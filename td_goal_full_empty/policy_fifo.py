
# set environment variable:
# export COCOTB_REDUCED_LOG_FMT=true to prettify output so that it fits on the screen width

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
from cocotb.triggers import RisingEdge
from cocotb.triggers import Join
import numpy as np
from collections import defaultdict
import dill
import sys
from pprint import pprint as pp

from rl_fifo_utils import get_state_reward, tick, reset, get_state_reward, Switcher, ACTION_NAME_MAP

#Length of an episode in timesteps
EPISODE_LENGTH = 200

#Number of episodes over which to train
NUM_EPISODES = 1000

#Size of Action space = 4 : {pop, push}
nA = 4

@cocotb.test()
async def policy_fifo(dut):
    """ Test that runs policy found by training """


    async def run_policy(policy,nA):
        """ run simulation based on policy """

        total_reward = 0
        await reset(dut)

        state, reward = get_state_reward(dut)

        for _ in range(EPISODE_LENGTH):

            if state in policy:
                action = policy[state]
                dut._log.info("For state:{} => {}".format(state,ACTION_NAME_MAP[action]))
            else:
                dut._log.error("No action found in policy for state {}".format(state))
                action = np.random.choice(np.arange(nA))

            s=Switcher(dut)
            s.do_action(action)
            #print("state:{} + action:{} ->".format(state,action),end="")

            await tick(dut)

            next_state,reward = get_state_reward(dut)
            #print("\t next_state:{}".format(next_state))
            dut._log.info("reward = {}".format(reward))

            state = next_state
            total_reward += reward

        return total_reward

    """
    Create a 2ps period clock on port clk
    This will be fastest clock possible with the Verilator default time resolution
    of 1 ps. Will result in the fastest runtime.
    Sample runtimes (with 1000 transactions, over 10000 cycles)
    2 ps clock :  2.61 sec
    2 ns clock : 17.14 sec
    """
    clock = Clock(dut.clk, 2, units="ns")
    cocotb.fork(clock.start())  # Start the clock

    with open("policy.dump","rb") as f:
        (policy,Q) = dill.load(f)

    pp(policy)
    pp(Q)

    total_reward = await run_policy(policy,nA)

    dut._log.info('Total reward = {}'.format(total_reward))
