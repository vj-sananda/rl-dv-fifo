
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

def get_probs(Q_s, epsilon, nA):
    """ obtains the action probabilities corresponding to epsilon-greedy policy """
    policy_s = np.ones(nA) * epsilon / nA
    best_a = np.argmax(Q_s)
    policy_s[best_a] = 1 - epsilon + (epsilon / nA)
    return policy_s

def update_Q(episode, Q, alpha, gamma):
    """ updates the action-value function estimate using the most recent episode """
    states, actions, rewards = zip(*episode)

    # prepare for discounting
    discounts = np.array([gamma**i for i in range(len(rewards)+1)])
    for i, state in enumerate(states):
        old_Q = Q[state][actions[i]]
        Q[state][actions[i]] = old_Q + alpha*(sum(rewards[i:]*discounts[:-(1+i)]) - old_Q)
    return Q

@cocotb.test()
async def train_fifo(dut):
    """ Test to collect MC samples for RL training"""

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
        if dut.full == 1 and select == 0:
            reward = 10
            next_select = 1
        elif dut.empty == 1 and select == 1:
            reward = 10
            next_select = 0
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

    async def generate_episode_from_Q(Q, epsilon, nA):
        """ generates an episode from following the epsilon-greedy policy """
        episode = []

        await reset()

        total_episode_reward = 0
        select = 0
        dut.select = select
        state, reward, next_select = get_state_reward(select)
        #dut._log.info("Reset state = {}".format(state))
        select = next_select
        dut.reward = reward

        for _ in range(EPISODE_LENGTH):
            #Generates actions 0 through 3, using epsilon greedy
            #get_probs is the epsilon greedy probability function
            action = np.random.choice(np.arange(nA), p=get_probs(Q[state], epsilon, nA)) \
                                       if state in Q else np.random.choice(np.arange(nA))

            s=Switcher()
            s.do_action(action)
            #print("state:{} + action:{} ->".format(state,action),end="")

            await tick()

            next_state,reward,next_select = get_state_reward(select)
            #print("next_state:{}".format(next_state))

            dut.select <= select
            dut.reward <= reward
            episode.append((state, action, reward))

            state = next_state
            select = next_select

            total_episode_reward += reward

        return episode,total_episode_reward

    ACTION_NAME_MAP = { 0: 'NONE', 1:'PUSH' , 2 : 'POP', 3:'BOTH'}
    async def mc_control(num_episodes, alpha, gamma=1.0, eps_start=1.0, eps_decay=.999, eps_min=0.005):
        # initialize empty dictionary of arrays
        Q = defaultdict(lambda: np.zeros(nA))
        policy_best_print = dict((k,ACTION_NAME_MAP[np.argmax(v)]) for k, v in Q.items())
        policy_best = dict((k,np.argmax(v)) for k, v in Q.items())

        epsilon = eps_start
        episode_reward_min = 100000
        episode_reward_max = -10000
        # loop over episodes
        for i_episode in range(1, num_episodes+1):


            # monitor progress
            if i_episode % 10 == 0:
                print("Episode {}/{}, Episode Reward (min={},max={})".format(i_episode, num_episodes,episode_reward_min,episode_reward_max))
                print("epsilon = {}".format(epsilon))
                print("Best Policy")
                pp(policy_best_print)

            # set the value of epsilon
            epsilon = max(epsilon*eps_decay, eps_min)
            # generate an episode by following epsilon-greedy policy
            episode,total_episode_reward = await generate_episode_from_Q(Q, epsilon, nA)

            # update the action-value function estimate using the episode
            Q = update_Q(episode, Q, alpha, gamma)
            #pp(Q)
            if total_episode_reward > episode_reward_max:
                episode_reward_max = total_episode_reward
                policy_best_print = dict((k,ACTION_NAME_MAP[np.argmax(v)]) for k, v in Q.items())
                policy_best = dict((k,np.argmax(v)) for k, v in Q.items())
                with open("mc_control.dump","wb") as f:
                    dill.dump( (policy_best,Q) , f)
            if total_episode_reward < episode_reward_min:
                episode_reward_min = total_episode_reward


        # determine the policy corresponding to the final action-value function estimate
        return policy_best, Q

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

    policy, Q  = await mc_control(NUM_EPISODES,0.05)

    print(policy)
    print(Q)

    with open("mc_control.dump","wb") as f:
        dill.dump( (policy,Q) , f)

    dut._log.info("End of Training::Finished dumping")

    # End of Test
