from cocotb.triggers import RisingEdge

# Reward Function
def compute_reward(dut):
    reward = -1
    if dut.full == 1 and dut.filled == 0:
        reward = 100
    elif dut.empty == 1 and dut.filled == 1:
        reward = 100
    return reward

"""
def compute_reward(dut):
    reward = -1
    if dut.full_posedge == 1:
        reward = 100
    return reward
"""
"""
def compute_reward(dut):
    reward = -1
    if dut.empty_posedge == 1:
        reward = 100
    return reward
"""

# Next state and reward
def get_state_reward(dut):
    reward = compute_reward(dut)
    next_state = (dut.filled.value.integer, dut.count.value.integer, dut.empty.value.integer, dut.full.value.integer)
    #next_state = (dut.filled.value.integer, dut.count.value.integer)
    return next_state,reward


##---------------- DO NOT MODIFY BELOW THIS LINE --------------------

ACTION_NAME_MAP = { 0: 'NONE', 1:'PUSH' , 2 : 'POP', 3:'BOTH'}

async def tick(dut,n = 1):
    for _ in range(n):
        await RisingEdge(dut.clk)

async def reset(dut):
    #dut._log.info("Start reset")
    dut.rst <= 1 #Assert rst
    dut.push <= 0
    dut.pop <= 0
    await tick(dut,5)
    dut.rst <= 0 #deassert rst
    await tick(dut,5)
    #dut._log.info("End reset")

#Case like statement to translate action to {pop,push}
class Switcher(object):
    def __init__(self,dut):
        self.dut = dut

    def do_action(self,i):
        method_name='action_'+str(i)
        method=getattr(self,method_name,lambda :'Invalid')
        return method()

    def action_0(self):
        self.dut.push <= 0
        self.dut.pop <= 0

    def action_1(self):
        if self.dut.full == 0:
            self.dut.push <= 1
        else:
            self.dut.push <= 0
        self.dut.pop <= 0

    def action_2(self):
        if self.dut.empty == 0:
            self.dut.pop <= 1
        else:
            self.dut.pop <= 0
        self.dut.push <= 0

    def action_3(self):
        if self.dut.full == 0:
            self.dut.push <= 1
        else:
            self.dut.push <= 0
        if self.dut.empty == 0:
            self.dut.pop <= 1
        else:
            self.dut.pop <= 0