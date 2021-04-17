# Reinforcement Learning (RL) in Digital Simulation

## Demo Instructions

1. Install [Docker](https://www.docker.com/products/docker-desktop) 
2. (Optional): To view waves: Install [GTKWave](http://gtkwave.sourceforge.net) or any viewer for .vcd files
3. Clone this repo: git clone https://github.com/vj-sananda/rl-dv-fifo
4. cd to locally-cloned-directory
5. Start docker container: docker run -it -v $PWD:/work siliconbootcamp/verilator-cocotb:latest

### To run SARSA-Max (Q-Learning) FIFO Example
1. cd td_goal_full_empty/run-demo
2. ./demo16.sh
3. Waves will be dumped in directory from Step 1 above. 

### To run DQN (Deep Q Network) FIFO Example
1. cd dqn_goal_full_empty/run-demo
2. ./demo16.sh
3. Waves will be dumped in directory from Step 1 above. 

### For DQN (Deep Q Network) Lunar Lander demo:
#### This runs locally on your machine
#### Make sure following python packages are installed
#### In addition to numpy, matplotlib
* pip install gym
* pip install torch torchvision
* pip install BOX2D

