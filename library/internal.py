import collections
import math
import more_itertools
import random
from numpy.random import choice as npchoice

from library.component import Component
from library.exterior  import Task, createTask, copyTaskData
from library.external  import StrategyLct
from library.ic        import buildTriangleFromTask


## areConsecutiveMoves
## ------------------------------------------------------------------------
def areConsecutiveMoves(prevMove, thisMove):
	""" checks if two LCT moves are consecutive or not """
	## if there is no previous move, return True
	if not prevMove: return True
	## properties
	prevOBM = prevMove.handle.modulate == "object"
	thisOBM = thisMove.handle.modulate == "object"
	## previous was an object-based move, this one is a slot-based move
	if prevOBM and not thisOBM:
		return thisMove.slotin.type.name=="pos" and thisMove.slotin in prevMove.slotout.bound
	## previous was not an object-based move, but this one is
	if not prevOBM and thisOBM:
		return prevMove.slotout.type.name=="pos" and prevMove.slotout in thisMove.slotin.bound
	## both moves are object-based moves
	return prevMove.slotout == thisMove.slotin and prevMove.movable == thisMove.movable

## findMovePattern
## ------------------------------------------------------------------------
def findMovePattern(moves, minLen=2):
	""" finds a repeating pattern of moves """
	maxLen = math.ceil(float(len(moves))/2)
	for size in range(minLen,maxLen+1):
		windows = [
			tuple(window)
			for window in more_itertools.windowed(moves, size)
		]
		counter = collections.Counter(windows)
		for window, count in counter.items():
			if count==1: continue
			return window
	return None

## reduceLctMoves
## ------------------------------------------------------------------------
def reduceLctMoves(lct, moves):
	""" reduces a path of LCT moves in case a pattern of four moves are consecutive and futile """
	## need to have at least four moves in the path
	if len(moves)<4: return moves
	## build windows of size 4
	windows = [
		tuple(window)
		for window in more_itertools.windowed(moves, 4)
	]
	## loop through windows, checking whether or not to combine moves
	for i,window in enumerate(windows):
		first  = window[0]
		second = window[1]
		third  = window[2]
		fourth = window[3]
		## check if moves can be merged, if not, continue to next window
		if first.handle.modulate=="object" or first.movable != fourth.movable or first.handle != fourth.handle or second.slotout != third.slotin: 
			continue
		## merge last into first and remove from list
		name     = "lct_%03d"%(len(lct.allMoves)+1)
		strategy = StrategyLct(lct.aps, name, first.handle, first.slotin, first.movable, fourth.slotout)
		exmove   = lct.findMove(strategy)
		if not exmove: lct.aps.cache.permanentize(lct=strategy)
		move     = exmove if exmove else strategy
		## restart with merged set of moves
		newmoves = moves[0:i] + [move] + moves[i+4:]
		return reduceLctMoves(lct, newmoves)
	## the loop finishes only when no moves could be combined anymore, so return the list of moves
	return moves




## StrategyInt
## ========================================================================
class StrategyInt:
	""" a move executed by the internal interface """

	## __init__
	## --------------------------------------------------------------------
	def __init__(self, aps, name=None, slotin=None, moves=None, slotout=None, fromDict=None):
		""" constructor """
		self.aps       = aps
		self.task      = aps.task
		self.int       = aps.int
		self.name      = name
		self.slotin    = slotin
		self.moves     = moves
		self.slotout   = slotout
		self.score     = len(moves) if moves else 0
		if fromDict: self.read(fromDict)

	## __eq__
	## --------------------------------------------------------------------
	def __eq__(self, other):
		""" tests if this StrategyInt object is the same as another StrategyInt object """
		if len(self.moves)!=len(other.moves): return False
		for i,move in enumerate(self.moves):
			if move != other.moves[i]: return False
		return self.slotin.name==other.slotin.name and self.slotout.name==other.slotout.name

	## __neq__
	## --------------------------------------------------------------------
	def __neq__(self, other):
		""" tests if this StrategyInt object is not the same as another StrategyInt object """
		return not self==other

	## dump
	## --------------------------------------------------------------------
	def dump(self):
		""" dumps the content of this object to screen (for debugging) """
		return "StrategyInt (%s, %s, %s, %s)"%(self.name, self.slotin.name, ",".join([x.name for x in self.moves]), self.slotout.name)

	## merge
	## --------------------------------------------------------------------
	def merge(self, other):
		""" creates a new StrategyInt object from the merge of this move with another """
		moves    = reduceLctMoves(self.aps.lct, self.moves[:]+other.moves[:])
		name     = "int_%03d"%(len(self.int.allMoves)+1)
		strategy = StrategyInt(self.aps, name, moves[0].slotin, moves, moves[-1].slotout)
		exmove   = self.int.findMove(strategy)
		if not exmove: self.aps.cache.permanentize(int=strategy)
		return exmove if exmove else strategy

	## read
	## --------------------------------------------------------------------
	def read(self, d):
		""" decode a dict from long-term memory to retrieve the content of this object """
		self.name      = d["name"]
		self.slotin    = self.task.getSlot(d["slotin" ])
		self.moves     = [self.int.lct.getMove(x) for x in d["moves"]]
		self.slotout   = self.task.getSlot(d["slotout"])
		self.score     = len(self.moves)

	## write
	## --------------------------------------------------------------------
	def write(self):
		""" encode the content of this object into a dict stored in long-term memory """
		return {"name": self.name, "slotin": self.slotin.name, "moves": [x.name for x in self.moves], "slotout": self.slotout.name}




## InternalInterface
## ========================================================================
class InternalInterface(Component):
	""" the internal interface operating between the LCT and the first contextual stage (ICM) """

	## __init__
	## --------------------------------------------------------------------
	def __init__(self, aps):
		""" constructor """
		super(InternalInterface, self).__init__(aps, "int")
		self.lct          = None     ## link to LCT
		self.icm          = None     ## link to first stage
		self.fnmc         = None     ## link to Config of current state FNM
		self.fnmf         = None     ## link to Config of desired final state FNM
		self.virt         = None     ## link to virtual task
		self.gradient     = 0        ## metric distance of last change of last move
		self.recentMoves  = []       ## history of the last moves
		self.priors       = []       ## planned LCT moves
		self.posteriors   = []       ## done    LCT moves
		self.before       = None     ## copy of the task before all moves
		self.history      = []       ## history of last "before" tasks
		self.blockedMoves = []       ## list of INT moves blocked top-down
		self.genMoves     = []       ## list of all moves generated (only for buildRandomPath, no full INT moves yet)
		self.numTruncs    = 0        ## number of truncations
		self.deadEnd      = False    ## true if the interface has encountered a dead end
		self.isFinal      = False    ## true if the final state has been reached
		self.foundGoodOne = False

	## load
	## --------------------------------------------------------------------
	def load(self, task=None, triangle=None):
		""" load the instance, build components and define the triangle """
		## load the task and virtual task
		self.task = createTask(self.aps, "external")
		self.virt = createTask(self.aps, "external_virt")
		self.reload(task, triangle)
		## store a copy of the real task
		self.before = self.task.copy("external_before")
		## reset containers
		self.recentMoves  = []
		self.history      = []
		self.blockedMoves = []

	## reload
	## --------------------------------------------------------------------
	def reload(self, task=None, triangle=None):
		""" load the instance, build components and define the triangle """
		## take the full task as default
		task = task if task else self.aps.task
		## the triangle of the internal interface (external triangle) is a subset or full set of extended triangle
		self.triangle = triangle if triangle else buildTriangleFromTask(task)
		## the real task of the internal interface is a copy and subset of the current upstream task
		self.task.reload(task, triangle)
		## extract the initial and final state FNMs
		self.fnmc = self.task.config()
		self.fnmf = self.task.config("final")
		## the virtual task is a copy of that task
		self.virt.reload(task, triangle)

	## buildRandomPath
	## --------------------------------------------------------------------
	def buildRandomPath(self, moves, allMoves, it, jt):
		""" builds a random path of consecutive LCT moves """
		## if total maximum iterations reached, abort
		if jt==self.aps.j["simulation"]["maxRecsInt"]: 
			return []
		## if reached maximum path size, but path does not close, start over
		if it==self.aps.j["simulation"]["maxMovesInt"]: 
			self.virt.reset(self.fnmc)
			return self.buildRandomPath([], allMoves, 0, jt+1)
		## inserted randomness: not necessarily proceed with a known LCT move, but try to create a new one
		choice = random.choice([0,1])
		if choice==0: 
			return self.buildRandomPathTryMove(moves, allMoves, it, jt, None)
		## build LCT move bottom-up
		if len(allMoves)==0:
			return self.buildRandomPathTryMove(moves, allMoves, it, jt, None)
		## pick a random LCT move
		availMoves = [x for x in allMoves if x not in self.lct.blockedMoves]
		## no moves available -> start over or go in bottom-up if no moves available from start
		if len(availMoves)==0:
			if len(moves)==0: return []
			return self.buildRandomPath([], allMoves, 0, jt+1)
		## pick random LCT move
		lctMove = random.choice(availMoves)
		## if we have "move" handles consecutively, try again
		if len(moves)>0 and not lctMove.handle.modulate=="object" and not moves[-1].handle.modulate=="object":
			return self.buildRandomPath(moves, allMoves, it, jt+1)
		## get strategy details
		prev    = moves[-1] if len(moves)>0 else None
		thisin  = lctMove.movable.slot
		## check if move is consecutive (output slot of previous move is equal to input slot of this move); if not, try again
		if not areConsecutiveMoves(prev, lctMove):
			return self.buildRandomPath(moves, allMoves, it, jt+1)
		## try the move or find an alternative one
		return self.buildRandomPathTryMove(moves, allMoves, it, jt, lctMove)

	## buildRandomPathTryMove
	## --------------------------------------------------------------------
	def buildRandomPathTryMove(self, moves, allMoves, it, jt, lctMove):
		""" trying a move when building a random path of consecutive LCT moves """
		## make a hard copy of the virtual task since slots are updated
		before  = self.virt.copy("externalvirt_before")
		## try the move (or find an alternative one)
		res     = self.lct.do(lctMove, self.virt, True if lctMove else False)
		## move did not work, try again
		if not res: 
			self.virt.reset(before.config())
			return self.buildRandomPath(moves, allMoves, it, jt+1)
		## retrieve LCT move carried out, append to path
		## N.B. this if clause is necessary because in probe mode (if lctMove is given), LCT does not update its recent move
		lctMove = self.lct.recent if not lctMove else lctMove
		moves.append(lctMove)
		if lctMove in allMoves: 
			allMoves.remove(lctMove) ## remove move from container to avoid going in cricles
		## if path has not yet reached the end, continue
		if lctMove.slotout.type.name!="pin":
			return self.buildRandomPath(moves, allMoves, it+1, jt+1)
		## if path reached the end, but has been generated before, start over
		## N.B. this is NOT recentMoves, cause genMoves applies only for a single call of selectStrategy
		if moves in self.genMoves: 
			return self.buildRandomPath([], allMoves, 0, jt+1)
		## path is good, return
		self.genMoves.append(moves)
		return moves

	## createStrategy
	## --------------------------------------------------------------------
	def createStrategy(self):
		""" creates a strategy from the downstream moves that have been executed """
		moves    = self.optimizeStrategy(self.posteriors)
		name     = "int_%03d"%(len(self.allMoves)+1)
		strategy = StrategyInt(self.aps, name, moves[0].slotin, moves, moves[-1].slotout)
		exmove   = self.findMove(strategy)
		return exmove if exmove else strategy

	## do
	## --------------------------------------------------------------------
	def do(self, topDownStrat=None):
		""" run an individual processing step of the internal interface (NC contribution) per iteration """
		## reset state
		self.deadEnd = False
		## record top-down data
		if topDownStrat: 
			self.log("top-down", "strategy", topDownStrat.name)
		## select strategy to apply
		self.selectStrategy(topDownStrat)
		## record job data
		self.log("before", "task"                    , self.task.log()                  ) 
		self.log("before", "prior LCT strategies"    , [x.name for x in self.priors    ])
		self.log("before", "posterior LCT strategies", [x.name for x in self.posteriors])
		## try the next move, capture feedback by LCT
		strategy = self.priors[0] if len(self.priors)>0 else None
		self.log("planned", "strategy"    , self.move.name if self.move else None)
		self.log("planned", "LCT strategy", strategy .name if strategy  else None)
		success  = self.lct.do(strategy, self.task)
		## update the NC bottom-up
		self.updateNC()
		## record job
		self.log("used" , "success", success        )
		self.log("after", "task"   , self.task.log()) 
		## if success, it means the LCT worked, but not necessarily with the top-down strategy, merely it could do SOMETHING
		if success:
			## get LCT strategy that has been executed
			stratUsed = self.lct.recent
			## record LCT strategy that has been executed
			self.log("used", "LCT strategy", stratUsed.name)
			## anti-circular condition, block last LCT move and try again
			if stratUsed in self.posteriors:
				self.lct.blockedMoves.append(stratUsed)
				self.task.revert()
				return True
			## append to posterior moves
			self.posteriors.append(stratUsed)
			## top-down strategy worked, proceed to next prior move in the path
			if len(self.priors)>1 and stratUsed == self.priors[0]:
				self.priors = self.priors[1:]
				return True
			## top-down did not work, lower-level component did its own thing, need to change the path and retry downstream or propagate upstream
			return self.evaluate()
		## top-down strategy did not work, need to change the path and retry downstream or propagate upstream
		return self.evaluate()

	## evaluate
	## --------------------------------------------------------------------
	def evaluate(self):
		""" evaluates a configuration and determines whether to propagate emphasis upstream or downstream """
		## check distance to final state, if any (top-down "strategy application" mode)
		if self.fnmf: 
			dist = self.fnmf.distance(self.task.config()) ## needs to be the current task here, not fnmc (which is updated later)!
			## if final state has been reached -> truncate and store strategy and propagate upstream
			if dist == 0: 
				self.isFinal = True
				self.storeStrategy()
				return False
		## if a loop is present -> truncate and continue
		## N.B. this is done regardless of the ICM strategies; we book-keep recentMoves potentially accross multiple ICM strategies
		idxMove = self.startsLoop(self.aps.j["simulation"]["sizePattern"])
		if idxMove>-1: 
			self.truncateStrategy(idxMove)
			return True
		## if the move is closed -> truncate and store strategy and propagate upstream
		## (notably, we store ANY closing path, not only those that have gradient!=0, meaning, where something useful is done)
		if len(self.posteriors)>0 and self.posteriors[-1].handle.modulate=="object" and self.posteriors[-1].slotout.type.name=="pin":
			self.storeStrategy()
			return False
		## check length of moves and truncate if necessary -> start over
		if len(self.posteriors) >= self.aps.j["simulation"]["maxMovesInt"]:
			self.truncateStrategy()
			return True
		## all checks passed, so processing can continue downstream, but LCT diverged from top-down, so restart the INT move in the next iteration (reassess strategy)
		self.truncateStrategy()
		## dead end (INT and LCT could not find meaningful strategies in maxTruncsInt attempts) -> propagate upstream
		if self.numTruncs >= self.aps.j["simulation"]["maxTruncsInt"]:
			self.deadEnd   = True
			self.numTruncs = 0
			return False
		## restart the INT move in the next iteration (reassess strategy) 
		return True

	## finishMove
	## --------------------------------------------------------------------
	def finishMove(self):
		""" finish the move by resetting buffers and keeping track of the evolving task """
		## keep track of the previous state before that move
		self.history.append(self.before.copy("external_history_%03d"%(len(self.history)+1)))
		## keep track of the move
		self.recentMoves.append(self.move)
		## update internal state
		copyTaskData(self.task, self.before)
		self.recent           = self.move
		self.move             = None
		self.priors           = []
		self.posteriors       = []
		self.lct.blockedMoves = []
		self.foundGoodOne     = True

	## optimizeStrategy
	## --------------------------------------------------------------------
	def optimizeStrategy(self, path):
		""" optimizes the path to be stored by removing irrelevant LCT moves """
		## FIXME: not implemented in this version
		return path

	## probe
	## --------------------------------------------------------------------
	def probe(self, topDownStrat):
		""" tests a given top-down strategy downstream completely; self.virt needs to have been set properly """
		if topDownStrat in self.blockedMoves: return False
		for move in topDownStrat.moves:
			res = self.lct.do(move, self.virt, True)
			if not res: return False
		return True

	## saveStrategy
	## --------------------------------------------------------------------
	def saveStrategy(self):
		""" saves the current strategy into long-term memory and working memory """
		## check if strategy has been loaded from cache (do not create a new move for an existing move)
		if self.move in self.allMoves: return
		## store new strategy in long-term memory
		self.aps.cache.permanentize(int = self.move)

	## selectStrategy
	## --------------------------------------------------------------------
	def selectStrategy(self, topDownStrat=None, it=0):
		""" selects a path and triangle (= IC streak), i.e. does NC action """
		## strategy forced top-down
		if topDownStrat: 
			self.storeStrategy()
			self.move       = topDownStrat
			self.priors     = self.move.moves[:]
			self.posteriors = []
			return
		## if total maximum iterations reached, abort, sacrificing an iteration
		if it==self.aps.j["simulation"]["maxRecsInt"]: 
			self.move   = None
			self.priors = []
			return
		## we already have a strategy
		if len(self.priors)>0: 
			return 
		## if LCT does not know any moves, run LCT in bottom-up
		if len(self.lct.allMoves)==0:
			self.move   = None
			self.priors = []
			return
		## inserted randomness: not necessarily proceed with a known LCT move, but try to create a new one
		choice = npchoice([0,1], 1, p=[self.aps.j["simulation"]["probRedoInt"], 1-self.aps.j["simulation"]["probRedoInt"]])
		if choice==0: 
			return self.selectStrategyNewMove(it)
		## analyze the current configuration, find ANY slot that is filled
		slotin = self.task.findFilledSlot()
		if not slotin: return
		## first, try to find an applicable strategy from long-term memory, try it out in the virtual task instance
		for move in sorted(self.allMoves, key=lambda x: x.score):
			if not self.aps.applies(self.task.config(), self.recent, move): continue ## ignore inapplicable moves
			if move in self.blockedMoves                                  : continue ## ignore moves blocked top-down
			res = True
			if slotin != move.moves[0].slotin: continue
			self.virt.reset(self.fnmc)
			for lctMove in move.moves:
				res = self.lct.do(lctMove, self.virt, True)
				if not res: break
			if not res: continue
			self.move   = move
			self.priors = move.moves[:]
			return
		## second, generate a new random path of LCT strategies
		return self.selectStrategyNewMove(it)

	## selectStrategyNewMove
	## --------------------------------------------------------------------
	def selectStrategyNewMove(self, it):
		""" generates a new strategy randomly """
		## generate a new random path of LCT strategies
		self.virt.reset(self.fnmc)
		self.genMoves = []
		moves = self.buildRandomPath([], list(self.lct.allMoves)[:], 0, 0)
		## if not found a proper path (probably not enough LCT strategies) -> run LCT in bottom-up mode
		if len(moves)==0: 
			self.move   = None
			self.priors = []
			return
		## if found a proper path -> run LCT in top-down mode
		slotin      = moves[ 0].slotin
		slotout     = moves[-1].slotout
		name        = "int_%03d"%(len(self.allMoves)+1) #"-".join([x.name for x in moves])
		move        = StrategyInt(self.aps, name, slotin, moves, slotout)
		exmove      = self.findMove(move)
		move        = exmove if exmove else move ## if path already exists, take the existing one
		## if this sequence of moves is not applicable, try again
		if not self.aps.applies(self.task.config(), self.recent, move) or move in self.blockedMoves: 
			return self.selectStrategy(it=it+1)
		## set the path and priors
		self.move   = move 
		self.priors = self.move.moves[:]

	## startsLoop
	## --------------------------------------------------------------------
	def startsLoop(self, minLen=2):
		""" returns the move, that started a loop, if any """
		## find a repeating pattern of moves (as a tuple of move names)
		moves   = [x.name for x in self.recentMoves]
		pattern = findMovePattern(moves, minLen)
		if not pattern: return -1
		## find the first occurence of that pattern and return the index of the first move
		lmd = lambda data, pos, size: data[pos: pos + size] 
		for i in range(len(moves)+len(pattern)+1):
			p = lmd(moves, i, len(pattern))
			if all(p[j]==pattern[j] for j in range(len(p))): return i
		return -1

	## storeStrategy
	## --------------------------------------------------------------------
	def storeStrategy(self):
		""" finalizes the path of LCT moves from self.posterior and generates the StrategyInt instance and saves it """
		## check if there is something to be done
		if len(self.posteriors)==0:
			return
		## assemble the strategy from the LCT moves actually executed
		self.move = self.createStrategy()
		## save the strategy in long-term memory and working memory
		self.saveStrategy()
		## reset everything
		self.finishMove()

	## truncateStrategy
	## --------------------------------------------------------------------
	def truncateStrategy(self, idxToRevertTo=-1):
		""" truncates the current strategy and resets the buffers, also blocks the first LCT move, as it led into this mess """
		## only truncate if something has actually been done
		if len(self.posteriors)==0: return
		## if move to revert to is given, do so
		if idxToRevertTo>-1: 
			return self.truncateStrategyToMove(idxToRevertTo)
		## else simply revert the last INT move, remember the first LCT move of that last attempted path and block it (= try something else in next attempt)
		copyTaskData(self.before, self.task)
		self.lct.blockedMoves.append(self.posteriors[0])
		## reset recent moves to before that move
		self.recentMoves = self.recentMoves[:-1]
		self.recent      = self.recentMoves[-1] if len(self.recentMoves)>0 else None
		## reset moves
		self.move        = None
		self.priors      = []
		self.posteriors  = []
		self.numTruncs  += 1

	## truncateStrategyToMove
	## --------------------------------------------------------------------
	def truncateStrategyToMove(self, idxToRevertTo):
		""" reverts all moves until BEFORE a given move """
		## learn that that INT move does not apply for that condition
		self.aps.learn(self.task.config(), self.recentMoves[idxToRevertTo-1] if idxToRevertTo>0 else None, self.recentMoves[idxToRevertTo], False)
		## reset task to previous instance
		copyTaskData(self.history[idxToRevertTo], self.task  )
		copyTaskData(self.history[idxToRevertTo], self.before)
		## reset containers to before that move
		self.history     = self.history    [:idxToRevertTo]
		self.recentMoves = self.recentMoves[:idxToRevertTo]
		self.recent      = self.recentMoves[-1] if len(self.recentMoves)>0 else None
		## reset moves
		self.move        = None
		self.priors      = []
		self.posteriors  = []
		self.numTruncs  += 1

	## updateNC
	## --------------------------------------------------------------------
	def updateNC(self):
		""" propagate the configuration bottom-up into the current FNM """
		## compute the metric distance to the last move
		self.gradient = self.task.config().distance(self.fnmc)
		## INT is the last module (viewed from top-down) that has a task instance, so the configuration is propagated automatically into self.task


