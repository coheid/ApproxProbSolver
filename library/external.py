import random
from numpy.random import choice as npchoice

from library.component import Component


## StrategyLct
## ========================================================================
class StrategyLct:
	""" a move executed by the LCT """

	## __init__
	## --------------------------------------------------------------------
	def __init__(self, aps, name=None, handle=None, slotin=None, movable=None, slotout=None, fromDict=None):
		""" constructor """
		self.aps       = aps
		self.task      = aps.task
		self.lct       = aps.lct
		self.name      = name
		self.handle    = handle
		self.slotin    = slotin
		self.movable   = movable
		self.slotout   = slotout
		if fromDict: self.read(fromDict)

	## __eq__
	## --------------------------------------------------------------------
	def __eq__(self, other):
		""" tests if this StrategyLct object is the same as another StrategyLct object """
		return self.handle.name==other.handle.name and self.slotin.name==other.slotin.name and self.movable.name==other.movable.name and self.slotout.name==other.slotout.name

	## __neq__
	## --------------------------------------------------------------------
	def __neq__(self, other):
		""" tests if this StrategyLct object is not the same as another StrategyLct object """
		return not self==other

	## dump
	## --------------------------------------------------------------------
	def dump(self):
		""" dumps the content of this object to screen (for debugging) """
		return "StrategyLct (%s, %s, %s, %s, %s)"%(self.name, self.handle.name, self.slotin.name, self.movable.name, self.slotout.name)

	## read
	## --------------------------------------------------------------------
	def read(self, d):
		""" decode a dict from long-term memory to retrieve the content of this object """		
		self.name      = d["name"]
		self.handle    = self.task.getHandle (d["handle" ])
		self.slotin    = self.task.getSlot   (d["slotin" ])
		self.movable   = self.task.getMovable(d["movable"])
		self.slotout   = self.task.getSlot   (d["slotout"])

	## write
	## --------------------------------------------------------------------
	def write(self):
		""" encode the content of this object into a dict stored in long-term memory """
		return {"name": self.name, "handle": self.handle.name, "slotin": self.slotin.name, "movable": self.movable.name, "slotout": self.slotout.name}




## LCT
## ========================================================================
class LCT(Component):
	""" the local contextual trinity, i.e. external-branch processing """

	## __init__
	## --------------------------------------------------------------------
	def __init__(self, aps):
		""" constructor """
		super(LCT, self).__init__(aps, "lct")
		self.ext          = None ## link to the exterior
		self.int          = None ## link to the first stage of the internal branch
		self.recentMoves  = []   ## moves carried out recently
		self.blockedMoves = []   ## moves blocked top-down from INT

	## do
	## --------------------------------------------------------------------
	def do(self, topDownStrat=None, taskInst=None, probe=False):
		""" run an individual processing step of the LCT """
		## record top-down data
		if topDownStrat: 
			self.log("top-down", "strategy", topDownStrat.name)
			self.log("top-down", "taskInst", taskInst    .name)
		## select task instance to use
		task     = taskInst if taskInst else self.task
		## select strategy to apply
		strategy = self.selectStrategy(task, topDownStrat)
		## if no strategy has been found, proceed to next iteration
		if not strategy: return False
		## record job data
		self.log("before" , "task"    , task.log()   )
		self.log("planned", "strategy", strategy.name)
		## apply strategy to exterior, capture feedback
		success  = self.ext.do(task, strategy)
		## virtual mode, only the top-down strategy should be tested
		if probe: 
			return success
		## if false, retry next time 
		## (i.e. LCT does potentially multiple sub-iterations per iteration of the simulation in order to find a move that works) 
		if not success:
			## real mode: here we can try to find a new strategy
			return self.do(taskInst=taskInst)
		## record job
		self.log("used" , "success" , success      ) ## this will always be true, because LCT always makes sure that it succeeds
		self.log("used" , "strategy", strategy.name)
		self.log("used" , "taskInst", task    .name)
		self.log("after", "task"    , task.log()   ) 
		## if true, complete the strategy and store it in long-term memory and working memory
		self.saveStrategy(strategy)
		## reset containers
		self.recent = strategy
		self.recentMoves.append(strategy)
		## return true, thus, end this iteration
		return True

	## saveStrategy
	## --------------------------------------------------------------------
	def saveStrategy(self, strategy):
		""" saves the current strategy into long-term memory and working memory """
		self.aps.cache.permanentize(lct = strategy)

	## selectMovable
	## --------------------------------------------------------------------
	def selectMovable(self, task, handle):
		""" selects a random movable payload (object or slot) for a given handle """
		if handle.modulate=="object": 
			slotin = self.selectSlot(task, handle.initial)
			if len(slotin.holds)==0: return None
			return random.choice(slotin.holds)
		channels = task.getMovables(handle.modulate)
		if len(channels)<1: return None
		return channels[0]

	## selectSlot
	## --------------------------------------------------------------------
	def selectSlot(self, task, theSlot, other=None):
		""" selects a random slot for a given handle """
		if theSlot in task.getChannels():
			return task.getSlot(theSlot.name)
		slots = []
		for slot in task.current:
			if other and slot == other       : continue
			if slot.type.name != theSlot.name: continue
			slots.append(slot)
		return random.choice(slots)

	## selectStrategy
	## --------------------------------------------------------------------
	def selectStrategy(self, task, topDownStrat=None):
		""" select the next strategy (i.e. combination of handle and payload) to be applied """
		## strategy forced top-down
		if topDownStrat: 
			self.recentMoves = [] ## we only reset the list of good moves once a new top-down strategy comes
			return topDownStrat
		## inserted randomness: not necessarily proceed with a known LCT move, but try to create a new one
		choice = npchoice([0,1], 1, p=[self.aps.j["simulation"]["probRedoLct"], 1-self.aps.j["simulation"]["probRedoLct"]])
		if choice==0: 
			return self.selectStrategyNewMove(task, 0)
		## find an applicable strategy from long-term memory based on condition
		for move in self.allMoves:
			if move in self.recentMoves : continue ## avoid going in circles
			if move in self.blockedMoves: continue ## avoid moves blocked top-down
			self.recentMoves.append(move) ## also add this one to recent moves, to avoid re-generating the same move
			return move
		## generate random strategy
		return self.selectStrategyNewMove(task, 0)

	## selectStrategyNewMove
	## --------------------------------------------------------------------
	def selectStrategyNewMove(self, task, it):
		""" generates a new strategy randomly """
		## if total maximum iterations reached, abort, sacrificing an iteration
		if it==self.aps.j["simulation"]["maxRecsLct"]: 
			return None
		## generate random strategy
		handle   = random.choice(task.handles)
		movable  = self.selectMovable(task, handle)
		## cannot find movable or its slot in the triangle
		if not movable or not movable.slot: 
			return self.selectStrategyNewMove(task, it+1)
		## search for output slot
		slotout  = self.selectSlot   (task, handle.final, movable.slot)
		if not slotout: return self.selectStrategyNewMove(task, it+1)
		## assemble the strategy
		name     = "lct_%03d"%(len(self.allMoves)+1)
		strategy =  StrategyLct(self.aps, name, handle, movable.slot, movable, slotout)
		## if a strategy like that exists already, retry
		if strategy in list(self.allMoves): 
			return self.selectStrategyNewMove(task, it+1)
		## if the strategy is forbidden, retry
		if strategy in self.recentMoves or strategy in self.blockedMoves: 
			return self.selectStrategyNewMove(task, it+1)
		## return strategy
		self.recentMoves.append(strategy) ## also add this one to recent moves, to avoid re-generating the same move
		return strategy


