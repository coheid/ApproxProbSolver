import math
import more_itertools
import random
from numpy.random import choice as npchoice

from library.cache     import Condition
from library.component import Component
from library.exterior  import Config, Task, createTask, copyTaskData
from library.functions import areEqualLists


## buildIntPath
## ------------------------------------------------------------------------
def buildIntPath(posteriors):
	""" builds a path of INT moves from a list of posterior ThreefoldWay objects """
	path = []
	for tfw in posteriors:
		path.extend(tfw.conceptual)
	return path

## checkIntMoves
## ------------------------------------------------------------------------
def checkIntMoves(first, last, inbetween):
	""" checks if two INT moves (first and last) can be combined to a single move """
	## first and last move need to deal with the same object
	fobjs = list(set([x.movable.name for x in first.moves if x.movable.type.name!="channel"]))
	lobjs = list(set([x.movable.name for x in last .moves if x.movable.type.name!="channel"]))
	if len(fobjs)!=1 or len(lobjs)!=1 or fobjs[0]!=lobjs[0]: return False
	## moves in between may not have dealt with the same object
	bobjs = []
	for y in inbetween:
		bobjs.extend([x.movable.name for x in y.moves if x.movable.type.name!="channel"])
	if fobjs[0] in bobjs: return False
	## the output slot of the first move must be the same as the input slot of the last move
	if first.slotout != last.slotin: return False
	## the moves can be combined
	return True

## reduceIntMoves
## ------------------------------------------------------------------------
def reduceIntMoves(moves, size):
	""" reduces a path of INT moves by checking windows of a given size """
	windows = [
		tuple(window)
		for window in more_itertools.windowed(moves, size)
	]
	for i,window in enumerate(windows):
		first = window[0]
		last  = window[-1]
		inb   = [x for x in window[1:-1]] ## needs to be list not tuple
		## check if moves can be merged, if not, continue to next window
		if not checkIntMoves(first, last, inb): continue
		## merge last into first and remove from list
		newmoves = moves[0:i] + [first.merge(last)] + inb + moves[i+size:]
		return reduceIntMoves(newmoves, size)
	## the loop finishes only when no moves could be combined anymore, so return the list of moves
	return moves

## reduceIntPath
## ------------------------------------------------------------------------
def reduceIntPath(moves, prec=2):
	""" reduces a path of INT moves, thus, optimizes it """
	if prec<=1: return moves
	for size in range(2, prec+1):
		moves = reduceIntMoves(moves, size)
	return moves

## buildTriangleFromMoves
## ------------------------------------------------------------------------
def buildTriangleFromMoves(task, intMoves):
	""" builds the list of all slots actually used in given INT moves """
	## flatten the list
	slots  = []
	for intMove in intMoves:
		for lctMove in intMove.moves:
			slots.append(task.getSlot(lctMove.slotin .name))
			slots.append(task.getSlot(lctMove.slotout.name))
	## add pin slots to pos slots
	allPins = task.getSlots(type="pin")
	for slot in slots:
		if slot.type.name!="pos": continue
		for pin in allPins:
			if slot not in pin.bound: continue
			slots.append(pin)
	## add pos slots to pin slots
	allPos = task.getSlots(type="pos")
	for slot in slots:
		if slot.type.name!="pin": continue
		for pos in allPos:
			if pos not in slot.bound: continue
			slots.append(pos)
	## remove double counts
	snames = list(set([x.name for x in slots]))
	slots  = [task.getSlot(x) for x in snames]
	## build triangle
	name  = "tri_%03d"%(len(task.aps.allTriangles)+1)
	tri   = task.aps.createTriangle(task, name, slots)
	return tri

## buildTriangleFromTask
## ------------------------------------------------------------------------
def buildTriangleFromTask(task):
	""" builds a triangle from all slots present in a given task """
	## build triangle
	slots = task.current[:]
	name  = "tri_%03d"%(len(task.aps.allTriangles)+1)
	tri   = task.aps.createTriangle(task, name, slots)
	return tri

## isFinal
## ------------------------------------------------------------------------
def isFinal(cm):
	""" checks if a contextual model is in final configuration """
	if not cm.nmf.slots: return False
	dist = cm.nmf.distance(cm.task.config()) ## needs to be the current task here, not nmc (which is updated later)!
	cm.log("after", "distance", dist) 
	return dist == 0

## getListOfFinalObjects
## ------------------------------------------------------------------------
def getListOfFinalObjects(task, nmf):
	""" collects a list of all objects in the final state already """
	arefinal = []
	for fslot in nmf.slots:
		if len(fslot.holds)==0: continue
		cslot = task.getSlot(fslot.name)
		for cpos,cobj in enumerate(cslot.holds):
			if len(fslot.holds)<=cpos: continue
			if cobj != fslot.holds[cpos]: continue
			arefinal.append(cobj)
	return arefinal

## getListOfObjects
## ------------------------------------------------------------------------
def getListOfObjects(intMoves):
	""" collects a list of all objects involved in given INT moves """
	touched = []
	for intMove in intMoves:
		touched.extend([x.movable for x in intMoves.moves])
	return list(set(touched))




## Triangle
## ========================================================================
class Triangle:
	""" a triangle, i.e. subset of slots in the problem space """

	## __init__
	## --------------------------------------------------------------------
	def __init__(self, task, name=None, slots=None, fromDict=None):
		self.aps   = task.aps
		self.task  = task
		self.name  = name
		self.slots = slots
		if fromDict: self.read(fromDict)

	## __eq__
	## --------------------------------------------------------------------
	def __eq__(self, other):
		""" tests if this Triangle object is the same as another Triangle object """
		## compare number of slots
		if len(self.slots)!=len(other.slots): 
			return False
		## compare slots
		onames = sorted([x.name for x in other.slots])
		snames = sorted([x.name for x in self .slots])
		return snames == onames

	## __neq__
	## --------------------------------------------------------------------
	def __neq__(self, other):
		""" tests if this Triangle object is not the same as another Triangle object """
		return not self==other

	## __str__
	## --------------------------------------------------------------------
	def __str__(self):
		""" dumps the content of this object to screen (for debugging) """
		return self.dump()

	## config
	## --------------------------------------------------------------------
	def config(self):
		""" returns a Config object that corresponds to this triangle """
		return Config(self.task, fromTriangle=self)

	## dump
	## --------------------------------------------------------------------
	def dump(self):
		""" dumps the content of this object to screen (for debugging) """
		return "Triangle (%s)"%", ".join([x.name for x in self.slots])

	## fromTask
	## --------------------------------------------------------------------
	def fromTask(self, task):
		""" retrieve the slots (configuration) from a given task """
		self.slots = [self.task.getSlot(x.name) for x in task.current]

	## read
	## --------------------------------------------------------------------
	def read(self, d):
		""" decode a string from long-term memory to retrieve the content of this object """
		self.name  = d["name"]
		self.slots = [self.task.getSlot(x) for x in d["slots"]]

	## write
	## --------------------------------------------------------------------
	def write(self):
		""" encode the content of this object into a string stored in long-term memory """
		return {"name": self.name, "slots": [x.name for x in self.slots]}




## ThreefoldWay
## ========================================================================
class ThreefoldWay:
	""" a set of tensoral, conceptual, and symbolic moves; a move of interactive context executed by the first contextual stage """

	## __init__
	## --------------------------------------------------------------------
	def __init__(self, comp, name=None, tensoral=None, conceptual=None, symbolic=None, fromDict=None):
		self.aps        = comp.aps
		self.task       = comp.task
		self.comp       = comp
		self.name       = name
		self.tensoral   = tensoral
		self.conceptual = conceptual
		self.symbolic   = symbolic
		self.score      = sum(x.score for x in conceptual) if conceptual else 0
		if fromDict: self.read(fromDict)

	## __eq__
	## --------------------------------------------------------------------
	def __eq__(self, other):
		""" tests if this ThreefoldWay object is the same as another ThreefoldWay object """
		## compare tensoral
		if self.tensoral != other.tensoral: return False
		## compare moves
		if len(self.conceptual)!=len(other.conceptual): 
			return False
		for i,move in enumerate(self.conceptual):
			if move != other.conceptual[i]: return False
		## compare symbolic
		pass	
		## return true
		return True

	## __neq__
	## --------------------------------------------------------------------
	def __neq__(self, other):
		""" tests if this ThreefoldWay object is not the same as another ThreefoldWay object """
		return not self==other

	## __str__
	## --------------------------------------------------------------------
	def __str__(self):
		""" dumps the content of this object to screen (for debugging) """
		return self.dump()

	## dump
	## --------------------------------------------------------------------
	def dump(self):
		""" dumps the content of this object to screen (for debugging) """
		return "ThreefoldWay (%s; %s; %s; %s)"%(self.name, self.tensoral.name, ",".join(x.name for x in self.conceptual), "")

	## read
	## --------------------------------------------------------------------
	def read(self, d):
		""" decode a dict from long-term memory to retrieve the content of this object """
		self.name       = d["name"]
		self.tensoral   = self.aps.cache.reestablish("tri").get(d["tensoral"])
		self.conceptual = [self.comp.dn.getMove(x) for x in d["conceptual"]]
		self.symbolic   = d["symbolic"]
		self.score      = sum(x.score for x in self.conceptual)

	## write
	## --------------------------------------------------------------------
	def write(self):
		""" encode the content of this object into a dict stored in long-term memory """
		return {"name": self.name, "tensoral": self.tensoral.name, "conceptual": [x.name for x in self.conceptual], "symbolic": self.symbolic}




## StrategyIc
## ========================================================================
class StrategyIc:
	""" a move of interactive context executed by the second contextual stage """

	## __init__
	## --------------------------------------------------------------------
	def __init__(self, comp, name=None, confin=None, moves=None, confout=None, fromDict=None):
		""" constructor """
		self.aps       = comp.aps
		self.task      = comp.task
		self.comp      = comp
		self.name      = name
		self.confin    = confin
		self.moves     = moves
		self.confout   = confout
		self.score     = sum(x.score for x in moves) if moves else 0
		if fromDict: self.read(fromDict)

	## __eq__
	## --------------------------------------------------------------------
	def __eq__(self, other):
		""" tests if this StrategyIc object is the same as another StrategyIc object """
		## compare moves
		if len(self.moves)!=len(other.moves): 
			return False
		for i,move in enumerate(self.moves):
			if move != other.moves[i]: return False
		## compare confin
		if self.confin != other.confin: return False
		## compare confout
		if self.confout != other.confout: return False
		## return true
		return True

	## __neq__
	## --------------------------------------------------------------------
	def __neq__(self, other):
		""" tests if this StrategyIc object is not the same as another StrategyIc object """
		return not self==other

	## dump
	## --------------------------------------------------------------------
	def dump(self):
		""" dumps the content of this object to screen (for debugging) """
		return "StrategyIc (%s, %s, %s, %s)"%(self.name, self.confin.name, ",".join([x.name for x in self.moves]), self.confout.name)

	## read
	## --------------------------------------------------------------------
	def read(self, d):
		""" decode a dict from long-term memory to retrieve the content of this object """
		configs        = self.aps.cache.reestablish("cfg")
		threefoldways  = self.aps.cache.reestablish("icm")
		self.name      = d["name"]
		self.confin    = configs.get(d["confin" ])
		self.moves     = [threefoldways.get(x) for x in d["moves"]]
		self.confout   = configs.get(d["confout"])
		self.score     = sum(x.score for x in self.moves)

	## write
	## --------------------------------------------------------------------
	def write(self):
		""" encode the content of this object into a dict stored in long-term memory """
		return {"name": self.name, "confin": self.confin.name, "moves": [x.name for x in self.moves], "confout": self.confout.name}




## ContextualModel
## ========================================================================
class ContextualModel(Component):
	""" the internal branch, prototype of a contextual model (CM) or interactive context (IC) """

	## __init__
	## --------------------------------------------------------------------
	def __init__(self, aps, name):
		""" constructor """
		super(ContextualModel, self).__init__(aps, name)
		self.task       = None  ## reset the task for this CM
		self.virt       = None  ## virtual task for this CM
		self.dn         = None  ## link to downstream CM
		self.up         = None  ## link to upstream  CM
		self.nmc        = None  ## link to Config of current NC model (initial state)
		self.nmf        = None  ## link to Config of desired NC model (final   state)
		self.triangle   = None  ## triangle for this CM
		self.gradient   = 0     ## metric distance of last change of last move
		self.history    = []    ## history of last metric distances of done moves
		self.move       = None  ## the move (e.g. ThreefoldWay objec) used currently downstream
		self.priors     = []    ## planned downstream moves (e.g. ThreefoldWay object)
		self.posteriors = []    ## used    downstream moves (e.g. ThreefoldWay object)
		self.prev       = False ## downstream return value kept for later
		self.before     = None  ## copy of the task before all moves
		self.seen       = []    ## tasks and thus configs (NC states) seen before
		self.numTruncs  = 0     ## number of truncations
		self.deadEnd    = False ## true if the model has encountered a dead end
		self.hardReload = False ## true if downstream component shall be reloaded hard (all tasks rebuild)
		self.isFinal    = False ## true if the final state for that model has been reached
		self.foundGoodOne = False

	## load
	## --------------------------------------------------------------------
	def load(self, task=None, triangle=None):
		""" load the instance, build components and define the triangle """
		name = "extended" if self.name=="icm" else "real"
		## load the task and virtual task
		self.task = createTask(self.aps, name)
		self.virt = createTask(self.aps, "%s_virt"%name)
		self.reload(task, triangle)
		## store a copy of the real task
		self.before = self.task.copy("%s_before"%name)
		c           = self.task.config()
		c.name      = "%s_seen_%02d"%(name, len(self.seen)+1)
		self.seen.append(c)

	## do
	## --------------------------------------------------------------------
	def do(self, topDownStrat=None):
		""" run an individual processing step of the first (ICM) or second (SCM) contextual stage per iteration """
		## reset state
		self.deadEnd = False
		## record top-down data
		if topDownStrat: 
			self.log("top-down", "strategy", topDownStrat.name)
		## update internal values by selecting a new strategy
		self.selectStrategy(topDownStrat)
		## assign proper triangle and final state to the downstream component
		## FIXME: not very clever or efficient to reload the task/virt of the downstream component for every iteration (still needed in this version of the algo)
		callable = self.dn.load if self.hardReload else self.dn.reload
		callable(self.task, self.move.tensoral if self.name=="icm" and self.move else self.triangle)
		self.hardReload = False
		## record job data
		self.log("before", "task"                    , self.task.log()                  ) 
		self.log("before", "prior INT strategies"    , [x.name for x in self.priors    ])
		self.log("before", "posterior INT strategies", [x.name for x in self.posteriors])
		## proceed with ordinary iterations; i.e. try the next move, capture feedback by the downstream component
		## careful: if self.prev==True, strategy must be set to None, because downstream shall continue running as is
		strategy = self.priors[0] if not self.prev and len(self.priors)>0 else None 
		self.log("planned", "strategy"    , self.move.name if self.move else None)
		self.log("planned", "INT strategy", strategy .name if strategy  else None)
		success = self.dn.do(strategy)
		## store for next iteration (relevant for selectStrategy)
		self.prev = success
		## update the NC bottom-up
		self.updateNC()
		## record job
		self.log("used" , "success", success        )
		self.log("after", "task"   , self.task.log()) 
		## careful about timescale! downstream has multiple moves for each move executed here
		## the downstream layers returns True if it wants to continue to the next iteration -- this layer needs to follow suit
		if success:
			return True

		## then, once the downstream move has been completed or truncated, this layer must take action

		## if processing in the downstream layer has been completed successfully, the success must be propagated upstream to this layer
		if self.dn.recent:
			## get downstream strategy that has been executed
			stratUsed = self.dn.recent
			## record strategy that has been executed
			self.log("used", "INT strategy", stratUsed.name)
			## anti-circular condition, truncate the entire ICM strategy and propagate upstream
			## (at ICM: other than at INT, ICM has selected a top-down INT path, which apparently failed; redoing the same ICM strategy will result in the same failing path)
			if self.name=="icm" and len(self.priors)==0 and stratUsed in self.posteriors:
				self.truncateStrategy()
				return False
			## append to posterior moves
			self.posteriors.append(stratUsed)
			## top-down strategy worked, proceed to next move in the path
			if len(self.priors)>1 and stratUsed == self.priors[0]:
				self.priors = self.priors[1:]
				return True
			## top-down did not work, lower-level component did its own thing, need to change the path and retry downstream or propagate upstream
			return self.evaluate()	
		## top-down strategy did not work, need to change the path and retry downstream or propagate upstream
		return self.evaluate()

	## finishMove
	## --------------------------------------------------------------------
	def finishMove(self):
		""" finish the move by resetting buffers and keeping track of the evolving task """
		## update buffer
		copyTaskData(self.task, self.before)
		## build and store the configuration
		name   = "extended" if self.name=="icm" else "real"
		c      = self.task.config()
		c.name = "%s_seen_%02d"%(name, len(self.seen)+1)
		self.seen.append(c)
		## update moves
		self.recent          = self.move
		self.move            = None
		self.priors          = []
		self.posteriors      = []
		self.foundGoodOne = True

	## saveStrategy
	## --------------------------------------------------------------------
	def saveStrategy(self, move=None):
		""" saves the current strategy into long-term memory and working memory """
		## take the good move
		move = move if move else self.move
 		## check if strategy has been loaded from cache (do not create a new move for an existing move)
		if move and move in self.allMoves: return
		## store new strategy in long-term memory
		kwargs = {self.name: move}
		self.aps.cache.permanentize(**kwargs)

	## seenConfig
	## --------------------------------------------------------------------
	def seenConfig(self, nm):
		""" checks if a given config (or NC model) has been seen before """
		## if nothing has been seen before, false
		if len(self.seen)==0: return False
		## check if config has been seen before
		for seen in self.seen:
			if not seen.equalCustom(nm): continue
			return True
		return False

	## selectRandomSlots
	## --------------------------------------------------------------------
	def selectRandomSlots(self, size=0):
		""" selects a random subset of slots in the task to generate the triangle """
		## select a random subset of all "pin" slots
		slots  = self.task.current[:]
		sample = random.sample(slots, size if size else len(slots))
		## check if at least one of them holds an object, if not, try again
		if all([len(x.holds)==0 for x in sample]): return self.selectRandomSlots(size)
		return sample

	## truncateStrategy
	## --------------------------------------------------------------------
	def truncateStrategy(self, hardReload=False):
		""" truncates the current strategy and resets the buffers """
		## only truncate if something has actually been done
		if len(self.posteriors)==0: return
		## reset task to previous instance
		copyTaskData(self.before, self.task) 
		self.hardReload = hardReload ## force hard reload of downstream component (rebuild all tasks, including "before" task)
		## reset moves
		self.gradient   = 0
		self.recent     = None
		self.move       = None
		self.priors     = []
		self.posteriors = []

	## updateNC
	## --------------------------------------------------------------------
	def updateNC(self):
		""" propagate the configuration bottom-up into the current NM """
		## compute the metric distance to the last move on this layer
		self.gradient = self.dn.task.config().distance(self.before.config())
		## update the current NM
		self.task.update(self.dn.task)
		self.nmc = self.task.config()




## ICM
## ========================================================================
class ICM(ContextualModel):
	""" the internal branch, first contextual stage (ICM) """

	## __init__
	## --------------------------------------------------------------------
	def __init__(self, aps):
		""" constructor """
		super(ICM, self).__init__(aps, "icm")

	## reload
	## --------------------------------------------------------------------
	def reload(self, task=None, triangle=None):
		""" load the instance, build components and define the triangle """
		## take the full task as default
		task = task if task else self.aps.task
		## the triangle of the ICM (extended triangle) is a subset or full set of real triangle
		self.triangle = triangle if triangle else buildTriangleFromTask(task)
		## the real task of the ICM is a copy and subset of the current upstream task
		self.task.reload(task, triangle)
		## extract the initial and final state INMs
		self.nmc = self.task.config()
		self.nmf = self.task.config("final")
		## the virtual task is a copy of that task
		self.virt.reload(task, triangle)

	## buildRandomPath
	## --------------------------------------------------------------------
	def buildRandomPath(self, triangle, moves, allMoves, it, jt):
		""" builds a random path of INT moves in parallel """

		## basic checks

		## if total maximum iterations reached, abort
		if jt==self.aps.j["simulation"]["maxRecsIcm"]: 
			return []
		## if reached maximum path size, but path does not close, start over
		if it==self.aps.j["simulation"]["maxMovesIcm"]: 
			self.dn.virt.reload(self.task, triangle)
			return self.buildRandomPath(triangle, [], allMoves, 0, jt+1)
		## build moves bottom-up
		if len(allMoves)==0:
			return []

		## checks on all moves done so far in this path
 
		## generate the list of all objects in the triangle
		allObjs = []
		for slot in triangle.slots:
			allObjs.extend(slot.holds)
		## generate the list of all objects in the triangle that have been touched in previous moves
		touched = getListOfObjects(moves)
		## if all objects have been touched, the path has reached the end
		if areEqualLists(allObjs, touched): 
			return moves
		## generate the list of all objects in the final configuration already (slot and layer!)
		arefinal = getListOfFinalObjects(self.task, self.nmf)
		## if all objects are in final position already, the path has reached the end
		if areEqualLists(allObjs, arefinal):
			return moves

		## try adding a new move to the path

		## pick a random downstream move (or create one) and a random slot that holds an object
		slotin     = random.choice([x for x in triangle.slots if len(x.holds)>0])
		availMoves = [x for x in allMoves if x.slotin == slotin and self.aps.applies(self.dn.virt.config(), moves[-1] if len(moves)>0 else None, x)]
		intMove    = random.choice(availMoves) if len(availMoves)>0 else self.buildRandomPathMakeMove(0) ## try existing moves first 
		slotout    = intMove.slotout
		objs       = list(set(x.movable for x in dnMove.moves))
		## if the move touches an object that has already been touched, try again (anti-circular condition)
		touched = getListOfObjects(moves)
		if len([x for x in objs if x in touched])>0: 
			return self.buildRandomPath(triangle, moves, allMoves, it, jt+1)
		## if the move touches an object in the final state configuration, try again
		if len([x for x in objs if x in arefinal])>0: 
			return self.buildRandomPath(triangle, moves, allMoves, it, jt+1)
		## make a hard copy of the virtual task since slots are updated
		before  = self.dn.virt.copy("%s_before"%self.dn.virt.name)
		## try the move
		res     = self.dn.probe(intMove)
		## move did not work, try again
		if not res: 
			self.dn.virt.reset(before.config())
			return self.buildRandomPath(triangle, moves, allMoves, it, jt+1)
		## move did work, append to path
		moves.append(intMove)
		if intMoves in allMoves: allMoves.remove(intMove)
		## continue to next move
		return self.buildRandomPath(triangle, moves, allMoves, it+1, jt+1)

	## buildRandomPathMakeMove
	## --------------------------------------------------------------------
	def buildRandomPathMakeMove(self, kt):
		""" trying a move when building a random path of INT moves """
		## if total maximum iterations reached, abort
		if kt==self.aps.j["simulation"]["maxRecsIcm"]: 
			return None
		## generate a new INT strategy by running INT's selectStrategy method
		self.dn.selectStrategy()
		## if no move has been generated, try again
		if not self.dn.move: return self.buildRandomPathMakeMove(kt+1)
		## capture move that has been created
		intMove = self.dn.move
		self.dn.move   = None
		self.dn.priors = []
		return intMove

	## createStrategy
	## --------------------------------------------------------------------
	def createStrategy(self, moves):
		""" creates a strategy from the downstream moves that have been executed """
		moves    = self.optimizeStrategy(moves)
		name     = "icm_%03d"%(len(self.allMoves)+1)
		triangle = buildTriangleFromTask(self.task)
		strategy = ThreefoldWay(self, name, triangle, moves, [])
		exmove   = self.findMove(strategy)
		return exmove if exmove else strategy

	## evaluate
	## --------------------------------------------------------------------
	def evaluate(self):
		""" evaluates the configuration of the ICM and determines whether to propagate emphasis upstream or downstream """
		## if final state has been reached downstream -> store strategy and continue
		## if this also means that the final state of this CM has been reached -> propagate upstream
		if self.dn.isFinal:
			self.storeStrategy()
			if isFinal(self): self.isFinal = True; return False
			return True
		## we have at least one INT move, the gradient is not zero (objects on pins are different), and the new configuration 
		## has not been seen before (includes the hand) -> close the ICM and propagate upstream
		## N.B.: it is NOT gradient>0, so we do NOT force the CM to proceed linearly towards the final state!
		if len(self.posteriors)>0 and self.gradient!=0 and not self.seenConfig(self.nmc):
			self.storeStrategy()
			return False
		## check length of moves and truncate if necessary
		if len(self.posteriors) >= self.aps.j["simulation"]["maxMovesIcm"]:
			self.truncateStrategy()
			return True
		## dead end (INT and LCT could not find meaningful strategies in maxTruncsInt attempts) -> propagate upstream
		if self.dn.deadEnd:
			self.truncateStrategy(True)
			self.deadEnd   = True
			self.numTruncs = 0
			self.seen      = []
			return False
		## all checks passed, so processing can continue downstream, but INT diverged from top-down, so reassess the strategy (beginning of next iteration)
		## dead end (INT and LCT could not find meaningful strategies in maxTruncsInt attempts) -> propagate upstream
		if self.numTruncs+1 >= self.aps.j["simulation"]["maxTruncsIcm"]:
			self.truncateStrategy(True)
			self.deadEnd   = True
			self.numTruncs = 0
			self.seen      = []
			return False
		## restart the ICM move in the next iteration (reassess strategy) 
		self.truncateStrategy()
		return True

	## finishMove
	## --------------------------------------------------------------------
	def finishMove(self):
		""" finish the move by resetting buffers and keeping track of the evolving task """
		super(ICM, self).finishMove()
		self.dn.blockedMoves = []
		self.numTruncs       = 0

	## optimizeStrategy
	## --------------------------------------------------------------------
	def optimizeStrategy(self, path):
		""" optimizes the path to be stored by removing irrelevant downstream moves """
		## FIXME: not implemented in this version
		return path

	## probe
	## --------------------------------------------------------------------
	def probe(self, topDownStrat):
		""" tests a given top-down strategy downstream completely; self.virt needs to have been set properly """
		## probe a given strategy of downstream moves
		for move in topDownStrat.moves:
			self.dn.virt.reload(self.virt, move.tensoral)
			for intMove in move.conceptual:
				res = self.dn.probe(intMove)
				if not res: return False
		return True

	## selectStrategy
	## --------------------------------------------------------------------
	def selectStrategy(self, topDownStrat=None, it=0):
		""" updates the internal condition of the ICM by selecting a strategy and a triangle, i.e. does ICM action """
		## strategy forced top-down
		if topDownStrat: 
			self.storeStrategy()
			self.move       = topDownStrat
			self.priors     = self.move.conceptual[:]
			self.posteriors = []
			return
		## if previous iteration has worked: continue on that path (i.e. no update)
		## (note: no prior is needed to continue on a given path, the prior is only given at the very first iteration)
		if self.prev: 
			return
		## if we're still having priors to work off, do that
		if len(self.priors)>0:
			return
		## if total maximum iterations reached, abort, sacrificing an iteration
		if it==self.aps.j["simulation"]["maxRecsIcm"]: 
			self.move   = None
			self.priors = []
			return
		## if previous iteration has not worked, strategy has been closed already by the internal interface,
		## and now we create and try a new strategy, i.e., a new ThreefoldWay object
		## inserted randomness: not necessarily proceed with a known ICM move, but try to create a new one
		choice = npchoice([0,1], 1, p=[self.aps.j["simulation"]["probRedoIcm"], 1-self.aps.j["simulation"]["probRedoIcm"]])
		if choice==0: 
			return self.selectStrategyNewMove(it)
		## first, try to find an applicable strategy from long-term memory, try it out in the virtual task instance
		for move in sorted(self.allMoves, key=lambda x: x.score):
			if not self.aps.applies(self.task.config(), self.recent, move): continue ## ignore inapplicable moves
			res = True
			if len([x for x in move.tensoral.slots if x in self.triangle.slots])!=len(move.tensoral.slots): continue
			self.dn.virt.reload(self.task, move.tensoral)
			for i,intMove in enumerate(move.conceptual):
				res = self.dn.probe(intMove)
				if not res: break
			if not res: continue
			self.move   = move
			self.priors = move.conceptual[:]
			return
		## second, generate a new random strategy
		return self.selectStrategyNewMove(it)

	## selectStrategyNewMove
	## --------------------------------------------------------------------
	def selectStrategyNewMove(self, it):
		""" generates a new strategy randomly """
		## generate a new random strategy
		randomSlots = self.selectRandomSlots() 
		name        = "tri_%03d"%(len(self.aps.allTriangles)+1)
		triangle    = self.aps.createTriangle(self.task, name, randomSlots)
		self.dn.virt.reload(self.task, triangle)		
		moves       = self.buildRandomPath(triangle, [], list(self.dn.allMoves), 0, 0)
		## if not found a proper path (probably not enough downstream strategies) -> run downstream in bottom-up mode
		if len(moves)==0: 
			self.move   = None
			self.priors = []
			return
		## if found a proper path -> run downstream in top-down mode
		name        = "icm_%03d"%(len(self.allMoves)+1)
		move        = ThreefoldWay(self, name, triangle, moves, [])
		exmove      = self.findMove(move)
		move        = exmove if exmove else move ## if path already exists, take the existing one
		## if this sequence of moves is not applicable, try again
		if not self.aps.applies(self.task.config(), self.recent, move): 
			return self.selectStrategy(it+1)
		## use this new move
		self.move   = move
		self.priors = moves[:]

	## storeStrategy
	## --------------------------------------------------------------------
	def storeStrategy(self):
		""" finalizes the path of downstream moves from self.posterior and generates the ThreefoldWay instance and saves it """
		## check if there is something to be done
		if len(self.posteriors)==0: 
			return
		## assemble the strategy from the downstream moves actually executed
		self.move = self.createStrategy(self.posteriors)
		## save the strategy in long-term memory and working memory
		self.saveStrategy()
		## reset everything
		self.finishMove()

	## truncateStrategy
	## --------------------------------------------------------------------
	def truncateStrategy(self, hardReload=False):
		""" truncates the current strategy and resets the buffers, also blocks the move, as it led into this mess """
		self.numTruncs += 1
		## if NOT hardReset, we block the first INT move in the ICM path
		## this is because this condition is not generalize-able, we should not learn it, merely try something else
		if not hardReload and len(self.posteriors)>0:
			self.dn.blockedMoves.append(self.posteriors[0])
		## truncate strategy
		super(ICM, self).truncateStrategy(hardReload)
		## revert last move at INT (task and before are taken care of by top-down call of reload)
		self.dn.recentMoves = self.dn.recentMoves[:-1]
		self.dn.recent      = self.dn.recentMoves[-1] if len(self.dn.recentMoves)>0 else None
		self.dn.move        = None




## SCM
## ========================================================================
class SCM(ContextualModel):
	""" the internal branch, second contextual stage (SCM) """

	## __init__
	## --------------------------------------------------------------------
	def __init__(self, aps):
		""" constructor """
		super(SCM, self).__init__(aps, "scm")

	## reload
	## --------------------------------------------------------------------
	def reload(self, task=None, triangle=None):
		""" load the instance, build components and define the triangle """
		## the real task of the SCM is the main task
		self.task = self.aps.task 
		self.task.name = "real" ## main task corresponds to the real triangle
		## the triangle of the SCM (real triangle) is the full set of slots
		self.triangle = buildTriangleFromTask(self.task)
		## extract the initial and final state SNMs
		self.nmc = self.task.config()
		self.nmf = self.task.config("final")
		## the virtual task is a copy of the main task
		self.virt = createTask(self.aps, "virtual")
		self.virt.load()

	## createStrategy
	## --------------------------------------------------------------------
	def createStrategy(self, moves):
		""" creates a strategy from the downstream moves that have been executed """
		name      = "scm_%03d"%(len(self.allMoves)+1)
		confin    = self.aps.createConfig(config=self.before.config(), itName=True)
		confout   = self.aps.createConfig(config=self.task  .config(), itName=True)
		strategy  = StrategyIc(self, name, confin, moves, confout)
		exmove    = self.findMove(strategy)
		return exmove if exmove else strategy

	## evaluate
	## --------------------------------------------------------------------
	def evaluate(self):
		""" evaluates the configuration of the SCM and determines whether to continue processing or to truncate the simulation """
		## if final state has been reached downstream -> store strategy and continue
		## if this also means that the final state of this CM has been reached -> propagate upstream
		if self.dn.isFinal:
			self.storeStrategy()
			if isFinal(self): self.isFinal = True; return False
			return True
		## check length of moves and truncate if necessary -> start over
		if len(self.posteriors) >= self.aps.j["simulation"]["maxMovesScm"]:
			self.truncateStrategy(True)
			return False
		## ICM has moved into a dead end -> try again
		## (though the result is the same as in "all checks passed" below, this case is checked explicitly, logic might be changed)
		if self.dn.deadEnd:
			self.truncateStrategy(True)
			return True
		## all checks passed, so processing can continue downstream, but ICM diverged from top-down, so reassess the strategy (beginning of next iteration)
		return True

	## optimizeStrategy
	## --------------------------------------------------------------------
	def optimizeStrategy(self, posteriors):
		""" optimizes the path to be stored by removing irrelevant downstream moves """
		## reduce the path of INT moves
		path = buildIntPath(posteriors)
		path = reduceIntPath(path, self.aps.j["simulation"]["precision"])
		## build ThreefoldWay object
		move = self.dn.createStrategy(path)
		if move not in self.dn.allMoves: self.aps.cache.permanentize(icm=move)
		## return the object
		return [move]

	## probe
	## --------------------------------------------------------------------
	def probe(self, topDownStrat):
		""" tests a given top-down strategy downstream completely; self.virt needs to have been set properly """
		## FIXME: triangular exchange is not implemented in this version of the algo
		return False

	## selectStrategy
	## --------------------------------------------------------------------
	def selectStrategy(self, topDownStrat=None):
		""" updates the internal condition of the SCM by selecting a path, i.e. does SCM action """
		## strategy forced top-down (triangular exchange)
		if topDownStrat: 
			self.storeStrategy()
			self.move       = topDownStrat
			self.priors     = self.move.moves[:]
			self.posteriors = []
			return
		## if previous iteration has worked: continue on that path (i.e. no update)
		## (note: no prior is needed to continue on a given path, the prior is only given at the very first iteration)
		if self.prev: 
			return
		## if previous iteration has not worked, we try either a top-down pick of known strategies
		## or a bottom-up construction of a new StrategyIc object
		## first, try to find an applicable strategy from long-term memory, try it out in the virtual task instance
		for move in sorted(self.allMoves, key=lambda x: x.score):
			if not self.aps.applies(self.task.config(), self.recent, move): continue ## ignore inapplicable moves
			res = True
			if move.confin != self.task.config(): continue
			self.dn.virt.reload(self.task, move.confin)
			if not self.dn.probe(move): continue
			self.move   = move
			self.priors = move.moves[:]
			return
		## second, generate a new random strategy
		## this is done EXCLUSIVELY bottom-up via the ICM, the SCM does not plan any moves here top-down
		self.move   = None
		self.priors = []
		return

	## storeStrategy
	## --------------------------------------------------------------------
	def storeStrategy(self):
		""" finalizes the path of downstream moves from self.posterior and generates the StrategyIc instance and saves it """
		## check if there is something to be done
		if len(self.posteriors)==0: 
			return
		## try to assemble an optimized version of this strategy, if possible, and save in memory
		move = self.createStrategy(self.optimizeStrategy(self.posteriors))
		self.saveStrategy(move)
		## check if strategy has been loaded from cache (do not create a new move for an existing move)
		if self.move and self.move in self.allMoves:
			self.finishMove()
			return
		## assemble the strategy from the downstream moves actually executed, and save in memory
		self.move = self.createStrategy(self.posteriors)
		self.saveStrategy()
		## reset everything
		self.finishMove()

	## truncateStrategy
	## --------------------------------------------------------------------
	def truncateStrategy(self, hardReload=False):
		""" truncates the current strategy and resets the buffers, also blocks the move, as it led into this mess """
		## truncate strategy
		super(SCM, self).truncateStrategy(hardReload)
		## learn that this strategy has put us into this mess (only in case we had a hard reload, otherwise we cannot really learn anything)
		if not hardReload or len(self.posteriors)==0: return
		move = self.createStrategy()
		self.aps.learn(self.before.config(), None, move, False)


