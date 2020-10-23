
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

#Length of an episode in timesteps
EPISODE_LENGTH = 200

#Number of episodes over which to train
NUM_EPISODES = 1000

#Size of Action space = 4 : {pop, push}
nA = 4

@cocotb.test()
async def random_fifo(dut):
    """ Test to that runs policy found by training """

    async def tick(n = 1):
        for _ in range(n):
            await RisingEdge(dut.clk)

    async def reset():
        #dut._log.info("Start reset")
        dut.rst <= 1 #Assert rst
        dut.push <= 0
        dut.pop <= 0
        await tick(5)
        dut.rst <= 0 #deassert rst
        await tick(5)
        #dut._log.info("End reset")

    def compute_reward(select):
        reward = -1
        next_select = select
        if dut.full_posedge == 1:
            reward = 10
        return reward,next_select

    def get_state_reward(select):
        reward,next_select = compute_reward(select)
        next_state = (next_select, dut.count.value.integer, dut.empty.value.integer, dut.full.value.integer)
        return next_state,reward,next_select

    #Case like statement to translate action to {pop,push}
    class Switcher(object):
        def do_action(self,i):
            method_name='action_'+str(i)
            method=getattr(self,method_name,lambda :'Invalid')
            return method()

        def action_0(self):
            dut.push <= 0
            dut.pop <= 0

        def action_1(self):
            if dut.full == 0:
                dut.push <= 1
            else:
                dut.push <= 0
            dut.pop <= 0

        def action_2(self):
            if dut.empty == 0:
                dut.pop <= 1
            else:
                dut.pop <= 0
            dut.push <= 0

        def action_3(self):
            if dut.full == 0:
                dut.push <= 1
            else:
                dut.push <= 0
            if dut.empty == 0:
                dut.pop <= 1
            else:
                dut.pop <= 0

    ACTION_NAME_MAP = { 0: 'NONE', 1:'PUSH' , 2 : 'POP', 3:'BOTH'}

    async def run_random(nA):
        """ run simulation based on policy """

        total_reward = 0
        await reset()

        select = 0
        state, reward, next_select = get_state_reward(select)
        select = next_select

        for _ in range(EPISODE_LENGTH):

            #Choose action at random
            action = np.random.choice(np.arange(nA))

            s=Switcher()
            s.do_action(action)

            await tick()

            next_state,reward,next_select = get_state_reward(select)

            select = next_select
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

    total_reward = await run_random(nA)

    dut._log.info('Total reward = {}'.format(total_reward))
