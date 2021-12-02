
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

from rl_fifo_utils import get_state_reward, tick, reset, get_state_reward, Switcher, ACTION_NAME_MAP

import torch
import torch.optim as optim
from policy_network import Policy

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

policy = Policy().to(device)
optimizer = optim.Adam(policy.parameters(), lr=1e-3)

@cocotb.test()
async def train_fifo(dut):
    """ RL stimulus Agent training using Policy Gradient (REINFORCE Algorithm) """

    #Length of an episode in timesteps
    EPISODE_LENGTH = 200

    #Number of episodes over which to train
    NUM_EPISODES = 20000

    ALPHA = 0.005

    GAMMA = 1.0

    TARGET_SCORE = 10000

    #Size of Action space = 4 : {pop, push}
    nA = 4

    if 'EPISODE_LENGTH' in cocotb.plusargs:
        EPISODE_LENGTH = int(cocotb.plusargs['EPISODE_LENGTH'])

    if 'NUM_EPISODES' in cocotb.plusargs:
        NUM_EPISODES = int(cocotb.plusargs['NUM_EPISODES'])

    if 'ALPHA' in cocotb.plusargs:
        ALPHA = float(cocotb.plusargs['ALPHA'])

    if 'GAMMA' in cocotb.plusargs:
        GAMMA = float(cocotb.plusargs['GAMMA'])

    if 'TARGET_SCORE' in cocotb.plusargs:
        TARGET_SCORE = float(cocotb.plusargs['TARGET_SCORE'])

    for k,v in cocotb.plusargs.items():
        print("{} = {}".format(k,v))

    async def reinforce(gamma=0.999, print_every=100):
        """
        Params
        ======
            num_episodes (int): number of episodes to run the algorithm
            alpha (float): learning rate
            gamma (float): discount factor
        """
        
        scores_deque = deque(maxlen=100)
    
        new_policy = {}
        old_policy = {}
        policy_stable_count = 0
        avg_high_score = -np.inf

        scores = []                        # list containing scores from each episode
        scores_window = deque(maxlen=100)  # last 100 scores

        for i_episode in range(1, NUM_EPISODES+1):
            saved_log_probs = []
            rewards = []
            score = 0                                              # initialize score

            #state = env.reset()                                    # start episode
            await reset(dut)

            total_episode_reward = 0
            state, reward = get_state_reward(dut)
            #dut._log.info("Reset state = {}".format(state))
            dut.reward = reward

            for _ in range(EPISODE_LENGTH):

                action, log_prob = policy.act(np.array(state,dtype=np.float32))
                saved_log_probs.append(log_prob)

                s=Switcher(dut)
                s.do_action(action)
                #print("state:{} + action:{} ->".format(state,action),end="")

                await tick(dut)

                next_state,reward = get_state_reward(dut)
                #print("next_state:{}".format(next_state))
                dut.reward <= reward

                done = False

                rewards.append(reward)

                state = next_state

            scores_deque.append(sum(rewards))
            scores.append(sum(rewards))
            
            discounts = [gamma**i for i in range(len(rewards)+1)]
            R = sum([a*b for a,b in zip(discounts, rewards)])
            
            policy_loss = []
            for log_prob in saved_log_probs:
                policy_loss.append(-log_prob * R)
            policy_loss = torch.cat(policy_loss).sum()
            
            optimizer.zero_grad()
            policy_loss.backward()
            optimizer.step()
            
            if i_episode % print_every == 0:
                print('Episode {}\tAverage Score: {:.2f}'.format(i_episode, np.mean(scores_deque)))

            if np.mean(scores_deque) > avg_high_score:
                    print('Episode {}\tAverage Score: {:.2f}'.format(i_episode, np.mean(scores_deque)),end="")
                    avg_high_score = np.mean(scores_deque)
                    torch.save(policy.state_dict(), 'checkpoint.pth')
                    print(" ->Saved checkpoint")

            if np.mean(scores_deque)>=2300:
                print('Environment solved in {:d} episodes!\tAverage Score: {:.2f}'.format(i_episode-100, np.mean(scores_deque)))
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

    scores  = await reinforce()

    dut._log.info("End of Training::Finished dumping")
    # End of Test
