
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
from rl_fifo_utils import get_state_reward, tick, reset, get_state_reward, Switcher, ACTION_NAME_MAP

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
    """ RL stimulus Agent training using DQN """

    #Length of an episode in timesteps
    EPISODE_LENGTH = 200

    #Number of episodes over which to train
    NUM_EPISODES = 20000

    ALPHA = 0.005

    GAMMA = 1.0

    EPS_START = 1.0

    EPS_DECAY = 0.999

    EPS_MIN = 0.05

    TARGET_SCORE = 10000

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

    if 'TARGET_SCORE' in cocotb.plusargs:
        TARGET_SCORE = float(cocotb.plusargs['TARGET_SCORE'])

    for k,v in cocotb.plusargs.items():
        print("{} = {}".format(k,v))

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
        avg_high_score = -np.inf

        scores = []                        # list containing scores from each episode
        scores_window = deque(maxlen=100)  # last 100 scores

        for i_episode in range(1, NUM_EPISODES+1):

            score = 0                                              # initialize score

            #state = env.reset()                                    # start episode
            await reset(dut)

            total_episode_reward = 0
            state, reward = get_state_reward(dut)
            #dut._log.info("Reset state = {}".format(state))

            eps = 1.0 / i_episode                                  # set value of epsilon

            for _ in range(EPISODE_LENGTH):

                action = agent.act(np.array(state,dtype=np.float32), eps)

                s=Switcher(dut)
                s.do_action(action)
                #print("state:{} + action:{} ->".format(state,action),end="")

                await tick(dut)

                next_state,reward = get_state_reward(dut)
                #print("next_state:{}".format(next_state))

                done = False
                agent.step(np.array(state,dtype=np.float32),action,reward,np.array(next_state,dtype=np.float32), done)

                score += reward                                    # add reward to agent's score
                state = next_state

            scores_window.append(score)       # save most recent score
            scores.append(score)              # save most recent score
            eps = max(eps_end, eps_decay*eps) # decrease epsilon
            print('\rEpisode {}\tAverage Score: {:.2f}'.format(i_episode, np.mean(scores_window)), end="")
            if i_episode % 100 == 0:
                #print('\rEpisode {}\tAverage Score: {:.2f}'.format(i_episode, np.mean(scores_window)))
                if np.mean(scores_window) > avg_high_score:
                    avg_high_score = np.mean(scores_window)
                    torch.save(agent.qnetwork_local.state_dict(), 'checkpoint.pth')
                    print(" ->Saved checkpoint")
                else:
                    print("")
            if np.mean(scores_window)>=TARGET_SCORE:
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
