# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0
VERILOG_SOURCES = ../src/fifo.sv
SIM=verilator
COCOTB_REDUCED_LOG_FMT=1

#Does not seem to work
#Verilator timescale default is 1 ps, so generate events
#in this case the clk changing every 1 ps.
#so clock period will be 2 ps.
#COCOTB_HDL_TIMEPRECISION = 1us

EXTRA_ARGS += --trace --trace-structs --assert

MODULE = random_fifo
TOPLEVEL = fifo

include $(shell cocotb-config --makefiles)/Makefile.sim
