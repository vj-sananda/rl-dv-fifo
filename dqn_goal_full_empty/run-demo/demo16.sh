#!/bin/sh

echo "+++++++  Random FIFO Test 1 +++++++"
echo "Press any key to start ..."

cp ../src/fifo_demo16.sv ../src/fifo_demo.sv

read dummy

make clean
make MODULE=random_fifo EXTRA_ARGS=--trace

echo "Check Waves ..."
echo ""

echo "+++++++  Deep Q Network FIFO Agent +++++++"
echo "Press any key to start ..."
read dummy

make clean
make MODULE=dqn_train_fifo PLUSARGS="+NUM_EPISODES=15000 +TARGET_SCORE=1000"

echo ""
echo "Training complete, Run test with Policy learned"
read dummy

echo "Press any key to start ..."

read dummy

make clean
make MODULE=policy_fifo EXTRA_ARGS=--trace

echo "Check Waves ..."
read dummy

echo "Demo Done"
