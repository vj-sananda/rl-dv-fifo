from cocotb.triggers import RisingEdge
import numpy as np

LOAD  = 0
CLEAR = 1
INC   = 2
DEC   = 3
READ  = 4
B2B_FLAG = True
ID_LOW = 1
ID_HIGH = 2

# Reward Function
# We want hazard_p1 to toggle as many times as possible
def compute_reward(dut):
    reward = -1
    if dut.hazard_state == 0 and dut.hazard_p1 == 1:
        reward = 100
    elif dut.hazard_state == 1 and dut.hazard_p1 == 0:
        reward = 100
    return reward

# Next state and reward
def get_state_reward(dut):
    reward = compute_reward(dut)
    next_state = (dut.cmd_state_p0.value.integer,dut.cmd_state_p1.value.integer,dut.cmd_state_p2.value.integer)
    return next_state,reward

##---------------- DO NOT MODIFY BELOW THIS LINE --------------------

ACTION_NAME_MAP = { 0: 'LOAD', 1:'CLEAR' , 2 : 'INC', 3:'DEC', 4:'READ', 5:'NOP' }

class op_transaction:
    def __init__(self):
        self.id = 0 
        self.data = 0
        self.op = 0

async def tick(dut,n = 1):
    for _ in range(n):
        await RisingEdge(dut.clk)

async def initialize_inputs(dut):
    dut.rst <= 0
    dut.valid <= 0
    dut.data <= 0
    dut.id <= 0
    dut.cmd <= 0

async def reset(dut):
    #dut._log.info("Start reset")
    dut.rst <= 1 #Assert rst
    await tick(dut,5)
    dut.rst <= 0 #deassert rst
    await tick(dut,5)
    #dut._log.info("End reset")

async def init_counter(dut,id,data=-1,b2b=B2B_FLAG):

   xact = op_transaction()

   await tick(dut)

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
       await tick(dut)
       dut.valid <= 0

async def initialize_counters(dut):
    for i in range(10):
        await init_counter(dut,i,-1)

def op_counter(dut,cmd,id,b2b=B2B_FLAG):

   xact = op_transaction()

   xact.id = id
   xact.op = cmd

   dut.valid <= 1
   dut.id <= xact.id
   dut.cmd <= xact.op  


#Case like statement to translate action to {pop,push}
class Switcher(object):
    def __init__(self,dut):
        self.dut = dut

    def do_action(self,i):
        method_name='action_'+str(i)
        method=getattr(self,method_name,lambda :'Invalid')
        return method()

    def action_0(self):
        op_counter(self.dut,0,np.random.randint(ID_LOW,ID_HIGH))

    def action_1(self):
        op_counter(self.dut,1,np.random.randint(ID_LOW,ID_HIGH))

    def action_2(self):
        op_counter(self.dut,2,np.random.randint(ID_LOW,ID_HIGH))

    def action_3(self):
        op_counter(self.dut,3,np.random.randint(ID_LOW,ID_HIGH))

    def action_4(self):
        op_counter(self.dut,4,np.random.randint(ID_LOW,ID_HIGH))

    def action_5(self):
        self.dut.valid <= 0
