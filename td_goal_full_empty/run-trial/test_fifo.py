
# set environment variable:
# export COCOTB_REDUCED_LOG_FMT=true to prettify output so that it fits on the screen width

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
from cocotb.triggers import RisingEdge
from cocotb.triggers import Join

@cocotb.test()
async def test_fifo_simple(dut):
    """ Test that pushes and pops from fifo """

    num = 1000
    run_time = 10000
    gap_push = 3
    gap_pop  = 3

    async def tick(n = 1):
        for _ in range(n):
            await RisingEdge(dut.clk)

    async def reset():
        dut._log.info("Start reset")
        dut.rst <= 1 #Assert rst
        await tick(5)
        dut.rst <= 0 #deassert rst
        await tick(5)
        dut._log.info("End reset")
        return dut.rst.value.integer

    async def push_data(n,gap):
        data_value = 0
        for _ in range(n): #like repeat(n)
            while dut.full == 1:
                await tick()
            data_value += 1
            dut.datain <= data_value
            dut.push <= 1
            await tick()
            dut.push <= 0

            await tick( random.randint(0,gap) )

    async def pop_data(n,gap):
        for _ in range(n):
            while dut.empty == 1:
                await tick()
            dut.pop <= 1
            await tick()
            dut.pop <= 0

            await tick( random.randint(0,gap) )

    async def goal_function(run_time):
        reward = 0
        select = "full"
        for _ in range(run_time):
            await tick()
            if dut.full == 1 and select == "full":
                reward += 1
                select = "empty"
            elif dut.empty == 1 and select == "empty":
                reward += 1
                select = "full"
        return reward

    async def state_monitor():
        select = 'full'
        while True:
            reward = -1
            count = dut.count.value
            full = dut.full.value
            empty = dut.empty.value
            if dut.full == 1 and select == "full":
                reward = 5
                select = "empty"
            elif dut.empty == 1 and select == "empty":
                reward = 5
                select = "full"
            #dut._log.info("c:{},f:{},e:{},R:{}".format(count.integer,full,empty,reward))
            await tick()

    """
    Create a 2ps period clock on port clk
    This will be fastest clock possible with the Verilator default time resolution
    of 1 ps. Will result in the fastest runtime.
    Sample runtimes (with 1000 transactions, over 10000 cycles)
    2 ps clock :  2.61 sec
    2 ns clock : 17.14 sec
    """
    clock = Clock(dut.clk, 2, units="ps")
    cocotb.fork(clock.start())  # Start the clock

    reset_value = await reset()
    dut._log.info("Reset signal at the end of reset : {}".format(reset_value))

    push_thread = cocotb.fork( push_data(num,gap_push) )
    pop_thread = cocotb.fork( pop_data(num,gap_pop) )
    run_thread = cocotb.fork( goal_function(run_time) )
    monitor_thread = cocotb.fork( state_monitor() )

    reward = await Join(run_thread)
    dut._log.info("+++ Final reward = %d " % reward)

    push_thread.kill()
    pop_thread.kill()
