
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
from collections import deque
import dill
import sys
from pprint import pprint as pp

def epsilon_greedy(Q, state, nA, eps):
    """Selects epsilon-greedy action for supplied state.

    Params
    ======
        Q (dictionary): action-value function
        state (int): current state
        nA (int): number actions in the environment
        eps (float): epsilon
    """
    if random.random() > eps: # select greedy action with probability epsilon
        return np.argmax(Q[state])
    else:                     # otherwise, select an action randomly
        return random.choice(np.arange(nA))

def update_Q_sarsamax(alpha, gamma, Q, state, action, reward, next_state=None):
    """Returns updated Q-value for the most recent experience."""
    current = Q[state][action]  # estimate in Q-table (for current state, action pair)

    Qsa_next = np.max(Q[next_state]) if next_state is not None else 0  # value of next state

    target = reward + (gamma * Qsa_next)               # construct TD target

    new_value = current + (alpha * (target - current)) # get updated value

    return new_value

@cocotb.test()
async def train_fifo(dut):
    """ Test to collect MC samples for RL training"""

    #Length of an episode in timesteps
    EPISODE_LENGTH = 200

    #Number of episodes over which to train
    NUM_EPISODES = 200

    ALPHA = 0.005

    GAMMA = 1.0

    EPS_START = 1.0

    EPS_DECAY = 0.999

    EPS_MIN = 0.05

    #Size of Action space = 4 : {pop, push}
    nA = 4

    if 'EPISODE_LENGTH' in cocotb.plusargs:
        EPISODE_LENGTH = int(cocotb.plusargs['EPISODE_LENGTH'])

    if 'NUM_EPISODES' in cocotb.plusargs:
        NUM_EPISODES = int(cocotb.plusargs['NUM_EPISODES'])

    if 'ALPHA' in cocotb.plusargs:
        ALPHA = float(cocotb.plusargs['ALPHA'])

    if 'EPS_DECAY' in cocotb.plusargs:
        EPS_DECAY = float(cocotb.plusargs['EPS_DECAY'])

    if 'EPS_MIN' in cocotb.plusargs:
        EPS_MIN = float(cocotb.plusargs['EPS_MIN'])

    if 'EPS_START' in cocotb.plusargs:
        EPS_START = float(cocotb.plusargs['EPS_START'])

    if 'GAMMA' in cocotb.plusargs:
        GAMMA = float(cocotb.plusargs['GAMMA'])

    for k,v in cocotb.plusargs.items():
        print("{} = {}".format(k,v))

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


    def compute_reward(filled):
        reward = -1
        next_filled = filled
        if dut.full == 1 and filled == 0:
            reward = 100
            next_filled = 1
        elif dut.empty == 1 and filled == 1:
            reward = 100
            next_filled = 0
        return reward,next_filled


    """
    def compute_reward(select):
        reward = -1
        next_select = select
        if dut.full_posedge == 1:
            reward = 100
        return reward,next_select
    """

    """
    def compute_reward(select):
        reward = -1
        next_select = select
        if dut.empty_posedge == 1:
            reward = 100
        return reward,next_select
    """

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

    async def q_learning(num_episodes, alpha, gamma=1.0, plot_every=100):
        """Q-Learning - TD Control

        Params
        ======
            num_episodes (int): number of episodes to run the algorithm
            alpha (float): learning rate
            gamma (float): discount factor
            plot_every (int): number of episodes to use when calculating average score
        """
        Q = defaultdict(lambda: np.zeros(nA))  # initialize empty dictionary of arrays

        for i_episode in range(1, NUM_EPISODES+1):

            await reset()            # start episode with a reset
            state, reward, next_select = get_state_reward(select)

            eps = 1.0 / i_episode    # set value of epsilon

            for _ in range(EPISODE_LENGTH):

                action = epsilon_greedy(Q, state, nA, eps) # epsilon-greedy action selection

                s=Switcher()
                s.do_action(action)

                await tick()
                next_state,reward,next_select = get_state_reward(select)

                Q[state][action] = update_Q_sarsamax(alpha, gamma, Q, \
                                                     state, action, reward, next_state)
                state = next_state
                select = next_select

                #.... Stopping condition when cumulative reward is high enough
        return Q

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

    Q  = await q_learning(NUM_EPISODES, ALPHA)

    print("Final Policy")
    policy_print = dict((k,ACTION_NAME_MAP[np.argmax(v)]) for k, v in Q.items())
    pp(policy_print)

    # determine the policy corresponding to the final action-value function estimate
    policy = dict((k,np.argmax(v)) for k, v in Q.items())
    #print(policy)
    #print(Q)

    with open("mc_control.dump","wb") as f:
        dill.dump( (policy,Q) , f)

    dut._log.info("End of Training::Finished dumping")

    # End of Test
