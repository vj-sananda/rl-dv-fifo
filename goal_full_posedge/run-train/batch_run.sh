make PLUSARGS="+NUM_EPISODES=6000 +EPS_DECAY=0.9999 +ALPHA=0.01" > run1.log

make PLUSARGS="+NUM_EPISODES=6000 +EPS_DECAY=0.9999 +ALPHA=0.005" > run2.log

make PLUSARGS="+NUM_EPISODES=6000 +EPS_DECAY=0.9999 +ALPHA=0.05" > run3.log

make PLUSARGS="+NUM_EPISODES=6000 +EPS_DECAY=0.999 +ALPHA=0.05" > run4.log

make PLUSARGS="+NUM_EPISODES=10000 +EPS_DECAY=0.99999 +ALPHA=0.01" > run5.log

make PLUSARGS="+NUM_EPISODES=10000 +EPS_DECAY=0.99999 +ALPHA=0.005" > run6.log

make PLUSARGS="+NUM_EPISODES=10000 +EPS_DECAY=0.99999 +ALPHA=0.05" > run7.log

make PLUSARGS="+NUM_EPISODES=10000 +EPS_DECAY=0.9999 +ALPHA=0.05" > run8.log