#!/bin/sh

echo "+++++++  Random Test  +++++++"
echo "Press any key to start ..."

read dummy

make clean
make MODULE=tb EXTRA_ARGS="--trace -Wno-lint"

echo "Check Waves ..."
echo ""

read dummy
echo "+++++++  SARSA-max (Q-Learning) FIFO Agent +++++++"
echo "Press any key to start ..."
read dummy

make clean
make MODULE=train PLUSARGS="+NUM_EPISODES=1500" EXTRA_ARGS="-Wno-lint"

echo ""
echo "Training complete, Run test with Policy learned"
read dummy

echo "Press any key to start ..."

read dummy

make clean
make MODULE=policy EXTRA_ARGS="--trace -Wno-lint"

echo "Check Waves ..."
read dummy

echo "Demo Done"
