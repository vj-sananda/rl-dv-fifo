
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
import torch
from dqn_agent import Agent

agent = Agent(state_size=4, action_size=4, seed=0)

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

@cocotb.test()
async def train_fifo(dut):
    """ Test to collect MC samples for RL training"""

    #Length of an episode in timesteps
    EPISODE_LENGTH = 200

    #Number of episodes over which to train
    NUM_EPISODES = 20000

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

    async def dqn(eps_start=1.0, eps_end=0.01, eps_decay=0.995):
        """Q-Learning - TD Control

        Params
        ======
            num_episodes (int): number of episodes to run the algorithm
            alpha (float): learning rate
            gamma (float): discount factor
        """
        Q = defaultdict(lambda: np.zeros(nA))  # initialize empty dictionary of arrays
        new_policy = {}
        old_policy = {}
        policy_stable_count = 0

        scores = []                        # list containing scores from each episode
        scores_window = deque(maxlen=100)  # last 100 scores

        for i_episode in range(1, NUM_EPISODES+1):

            score = 0                                              # initialize score

            #state = env.reset()                                    # start episode
            await reset()

            total_episode_reward = 0
            select = 0
            dut.select = select
            state, reward, next_select = get_state_reward(select)
            #dut._log.info("Reset state = {}".format(state))
            select = next_select
            dut.reward = reward

            eps = 1.0 / i_episode                                  # set value of epsilon

            for _ in range(EPISODE_LENGTH):

                action = agent.act(np.array(state,dtype=np.float32), eps)

                s=Switcher()
                s.do_action(action)
                #print("state:{} + action:{} ->".format(state,action),end="")

                await tick()

                next_state,reward,next_select = get_state_reward(select)
                #print("next_state:{}".format(next_state))
                dut.select <= select
                dut.reward <= reward


                done = False
                agent.step(np.array(state,dtype=np.float32),action,reward,np.array(next_state,dtype=np.float32), done)

                score += reward                                    # add reward to agent's score
                state = next_state
                select = next_select

            scores_window.append(score)       # save most recent score
            scores.append(score)              # save most recent score
            eps = max(eps_end, eps_decay*eps) # decrease epsilon
            print('\rEpisode {}\tAverage Score: {:.2f}'.format(i_episode, np.mean(scores_window)), end="")
            if i_episode % 100 == 0:
                print('\rEpisode {}\tAverage Score: {:.2f}'.format(i_episode, np.mean(scores_window)))
            if np.mean(scores_window)>=2300.0:
                print('\nEnvironment solved in {:d} episodes!\tAverage Score: {:.2f}'.format(i_episode-100, np.mean(scores_window)))
                torch.save(agent.qnetwork_local.state_dict(), 'checkpoint.pth')
                break

        return scores

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

    scores  = await dqn()

    dut._log.info("End of Training::Finished dumping")
    # End of Test
