#!/bin/sh

if [ -z $1 ] 
then
    echo "Specify FIFO depth"
    exit
fi

echo "------ FIFO depth of $1 ---------"

echo "+++++++  Deep Q Network FIFO Agent +++++++"
echo "Press any key to start ..."
read dummy

make clean
make MODULE=pgr_train_fifo PLUSARGS="+NUM_EPISODES=15000" EXTRA_ARGS="-Gdepth=$1 -Wno-lint"

echo ""
echo "Training complete, Run test with Policy learned"
read dummy

echo "Press any key to start ..."

read dummy

make clean
make MODULE=policy_fifo EXTRA_ARGS="--trace -Gdepth=$1 -Wno-lint"

echo "Check Waves ..."
read dummy

echo "Done"
