# Reinforcement Learning (RL) in Digital Simulation

## Instructions to run Examples

1. Install [Docker](https://www.docker.com/products/docker-desktop) 
2. (Optional): To view waves: Install [GTKWave](http://gtkwave.sourceforge.net) or any viewer for .vcd files
3. Clone this repo: git clone https://github.com/vj-sananda/rl-dv-fifo
4. cd to locally-cloned-directory
5. Start docker container: 
   * docker run -it -v $PWD:/work siliconbootcamp/verilator-cocotb:latest
   * The locally-cloned-directory will be mounted under /work in the docker container

### To run SARSA-Max (Q-Learning) FIFO Example
1. Within the docker container: cd td_goal_full_empty
2. ./run.sh 8   (Argument specifies FIFO depth)
3. Waves will be dumped in directory from Step 1 above.
4. You can use GTKWave running locally on your machine to load the vcd file.

### To run DQN (Deep Q Network) FIFO Example
1. Within the docker container: cd dqn_goal_full_empty
2. ./run.sh 8   (Argument specifies FIFO depth)
3. Waves will be dumped in directory from Step 1 above. 
4. You can use GTKWave running locally on your machine to load the vcd file.

### For DQN (Deep Q Network) Lunar Lander demo:
#### This runs locally on your machine
#### Make sure following python packages are installed
#### In addition to numpy, matplotlib
* pip install gym
* pip install torch torchvision
* pip install BOX2D

#### mc_goal_full_empty : Some prelim work using Monte Carlo
#### pgr_goal_full_empty: Work in progress. Policy Gradient method (REINFORCE)