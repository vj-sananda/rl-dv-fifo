
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

LOAD  = 0
CLEAR = 1
INC   = 2
DEC   = 3
READ  = 4
B2B_FLAG = True
ID_LOW = 1
ID_HIGH = 2

@cocotb.test()
async def tb(dut):
    mem = {}

    class op_transaction:
        def __init__(self):
            self.id = 0 
            self.data = 0
            self.op = 0

    async def tick(n = 1):
        for _ in range(n):
            await RisingEdge(dut.clk)

    async def initialize_inputs():
        dut.rst <= 0
        dut.valid <= 0
        dut.data <= 0
        dut.id <= 0
        dut.cmd <= 0

    async def reset():
        #dut._log.info("Start reset")
        dut.rst <= 1 #Assert rst
        await tick(5)
        dut.rst <= 0 #deassert rst
        await tick(5)
        #dut._log.info("End reset")

    async def monitor_input():
        while True:
            await tick()

    async def monitor_output():
        EXPECTED_READ_DATA = {}
        while True:
            await tick()
            if dut.valid.value == 1:
                id = dut.id.value.integer
                if dut.cmd.value.integer == LOAD:
                    load_data = dut.data.value.integer
                    mem[id] = load_data
                    dut._log.info(f"MONITOR::LOAD for ID:{id} <= {load_data}")
                if dut.cmd.value.integer == CLEAR:
                    mem[id] = 0
                    dut._log.info(f"MONITOR::CLEAR for ID:{id} <= 0")
                if dut.cmd.value.integer == INC:
                    mem[id] += 1
                    if mem[id] > 255:
                        mem[id] = 0
                    dut._log.info(f"MONITOR::INC for ID:{id} <= {mem[id]}")
                if dut.cmd.value.integer == DEC:
                    mem[id] -= 1
                    if mem[id] < 0:
                        mem[id] = 255
                    dut._log.info(f"MONITOR::DEC for ID:{id} <= {mem[id]}")
                if dut.cmd.value.integer == READ:
                    EXPECTED_READ_DATA[id] = mem[id]
                    dut._log.info(f"MONITOR::READ for ID:{id} <= {EXPECTED_READ_DATA[id]}")        
            if dut.output_valid.value == 1:
                read_data = dut.output_data.value.integer
                id = dut.output_id.value.integer
                if read_data == EXPECTED_READ_DATA[id]:
                    dut._log.info(f"CHECK::PASS::Read data match for ID:{id} = {read_data}")
                assert read_data == EXPECTED_READ_DATA[id], f"CHECK::FAIL::Read data Mismatch for ID:{id}: Actual = {read_data}, Expected = {EXPECTED_READ_DATA[id]}"

    async def init_counter(id,data=-1,b2b=B2B_FLAG):

        xact = op_transaction()

        await tick()

        xact.id = id
        xact.op = LOAD

        if data == -1:
           xact.data = id + 16
        else:
           xact.data = data

        dut.valid <= 1
        dut.id <= xact.id
        dut.cmd <= xact.op  
        dut.data <= xact.data

        if not b2b:
            await tick()
            dut.valid <= 0

    async def op_counter(cmd,id,b2b=B2B_FLAG):

        xact = op_transaction()

        await tick()

        xact.id = id
        xact.op = cmd

        dut.valid <= 1
        dut.id <= xact.id
        dut.cmd <= xact.op  

        if not b2b:
            await tick()
            dut.valid <= 0

    """
    Create a 2ps period clock on port clk
    This will be fastest clock possible with the Verilator default time resolution
    of 1 ps. Will result in the fastest runtime.
    Sample runtimes (with 1000 transactions, over 10000 cycles)
    2 ps clock :  2.61 sec
    2 ns clock : 17.14 sec
    """
    clock = Clock(dut.clk,10,units="ns")
    cocotb.fork(clock.start())  # Start the clock
    cocotb.fork(monitor_input())
    cocotb.fork(monitor_output())

    await initialize_inputs()
    await reset()

    
    for i in range(10):
        await init_counter(i,-1)

    """
    for i in range(10):
        await op_counter(INC,i)

    for i in range(10):
        await op_counter(READ,i)

    for i in range(10):
        await op_counter(DEC,i)

    for i in range(10):
        await op_counter(READ,i)

    for i in range(10):
        await init_counter(i,-1)

    for i in range(10):
        await op_counter(INC,np.random.randint(ID_LOW,ID_HIGH))

    for i in range(10):
        await op_counter(READ,np.random.randint(ID_LOW,ID_HIGH))

    for i in range(10):
        await op_counter(DEC,np.random.randint(ID_LOW,ID_HIGH))

    for i in range(10):
        await op_counter(READ,np.random.randint(ID_LOW,ID_HIGH))

    for i in range(100):
        await op_counter(np.random.randint(1,5),np.random.randint(ID_LOW,ID_HIGH))
    """

    for i in range(100):
        await op_counter(np.random.randint(0,5),LOAD,np.random.randint(ID_LOW,ID_HIGH))

    await tick()

    await initialize_inputs()

    await tick(10)

    dut._log.info(f"Test done")
