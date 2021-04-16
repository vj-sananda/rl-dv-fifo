#!/bin/sh

make clean
make MODULE=train_fifo PLUSARGS="+NUM_EPISODES=150"

echo ""
echo "Training complete, Run test with Policy learned"
