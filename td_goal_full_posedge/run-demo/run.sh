#!/bin/bash

echo "+++++++++++++ Run Random +++++++++++++"
echo ".."
read dummy

make clean
make MODULE=random_fifo EXTRA_ARGS=--trace


echo "Press any key to continue.."
read dummy

make clean
make MODULE=train_fifo


echo "Press any key to continue.."
read dummy


make clean
make MODULE=policy_fifo EXTRA_ARGS=--trace
