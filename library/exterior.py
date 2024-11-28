import copy
import math


## copyTaskData
## ------------------------------------------------------------------------
def copyTaskData(fr, to):
	""" copies the data from one task (from) to another (to) """
	attributes = ("slotTypes", "objectTypes", "objects", "actions", "handles", "initial", "current", "final")
	for attrib in attributes:
		items = [x.copy() for x in getattr(fr, attrib)]
		for item in items: item.task = to
		setattr(to, attrib, items)

## createTask
## ------------------------------------------------------------------------
def createTask(aps, name):
	""" creates a task instance including its before component """
	task        = Task(aps, name            )
	task.before = Task(aps, "%s_before"%name)
	return task

## getItem
## ------------------------------------------------------------------------
def getItem(container, name):
	""" finds an item by name in a container """
	for item in container:
		if item.name==name: return item
	return None

## metric
## ------------------------------------------------------------------------
def metric(config):
	""" computes the metric (score) of a configuration as the squared sum of all scores """
	score = 0
	for slot in config:
		score += math.pow(slot.score * len(slot.holds), 2)
	return math.sqrt(score)

## storeVals
## ------------------------------------------------------------------------
def storeVals(item, entry, keys=[]):
	""" stores the values of certain keys as presented in the entry list in an item """
	if len(keys)==0: keys = list(entry.keys())
	for key in keys:
		if key not in entry: continue
		setattr(item, key, entry[key])




## Item
## ========================================================================
class Item:
	""" item to hold info from json file """

	## __init__
	## --------------------------------------------------------------------
	def __init__(self, task, stype, name):
		""" constructor """
		self.task      = task
		self.stype     = stype
		self.name      = name
		self.isMovable = False

	## __eq__
	## --------------------------------------------------------------------
	def __eq__(self, other):
		""" test if two items are identical """
		return self.stype==other.stype and self.name==other.name

	## __neq__
	## --------------------------------------------------------------------
	def __neq__(self, other):
		""" test if two items are not identical """
		return not self==other

	## copy
	## --------------------------------------------------------------------
	def copy(self):
		""" creates a copy of this item """
		item = Item(self.task, self.stype, self.name)
		for k,v in vars(self).items():
			setattr(item, k, copy.copy(v)) #v[:] if type(v)==list else v)
		return item




## Config
## ========================================================================
class Config:
	""" a configuration of slots and what they are holding """

	## __init__
	## --------------------------------------------------------------------
	def __init__(self, task, name=None, slots=None, fromDict=None, fromTask=None, fromTriangle=None):
		""" constructor """
		self.aps   = task.aps
		self.task  = task
		self.name  = name
		self.slots = slots
		if fromDict    : self.read        (fromDict)
		if fromTask    : self.fromTask    (fromTask)
		if fromTriangle: self.fromTriangle(fromTriangle)

	## __eq__
	## --------------------------------------------------------------------
	def __eq__(self, other):
		""" tests if this Config object is the same as another Config object """
		return self.show() == other.show()

	## __neq__
	## --------------------------------------------------------------------
	def __neq__(self, other):
		""" tests if this Config object is not the same as another Config object """
		return not self==other

	## distance
	## --------------------------------------------------------------------
	def distance(self, other):
		""" computes the metric distance between two Config objects, accounting for different slots in these configs """
		onames = [x.name for x in other.slots]
		snames = [x.name for x in self .slots if x.name in onames]
		sub1   = [x for x in self .slots if x.name in snames]
		sub2   = [x for x in other.slots if x.name in snames]
		return metric(sub1) - metric(sub2)

	## dump
	## --------------------------------------------------------------------
	def dump(self):
		""" dumps the content of this object to screen (for debugging) """
		slots = self.show()
		dump= ["[%s, %s, [%s]]"%(x, y if y else "None", ",".join(i for i in z)) for x,y,z in slots]
		return "Config (%s, %s)"%(self.name, ", ".join(dump))

	## equalCustom
	## --------------------------------------------------------------------
	def equalCustom(self, other, stypes=["pin",]):
		""" same as __eq__ but customizable slot types, no channel slots """
		return self.showCustom(stypes) == other.showCustom(stypes)

	## fromTask
	## --------------------------------------------------------------------
	def fromTask(self, collection="current"):
		""" fill the Config object from an existing task (do hard copy!) """
		if collection not in ("initial", "current", "final"): return
		self.name  = "%s_%s"%(self.task.name, collection)
		self.slots = []
		for slot in getattr(self.task, collection):
			self.slots.append(slot.copy())

	## fromTriangle
	## --------------------------------------------------------------------
	def fromTriangle(self, triangle):
		""" fill the Config object from an existing triangle (this is NOT a hard copy!) """
		self.name  = "%s_%s"%(triangle.name, "config")
		self.slots = triangle.slots[:]

	## read
	## --------------------------------------------------------------------
	def read(self, d):
		""" decode a dict from long-term memory to retrieve the content of this object """
		## name
		self.name  = d["name"]
		## slots
		self.slots = []
		for sraw in d["slots"]:
			## find slot
			s = self.task.getSlot(sraw[0])
			if not s: 
				self.slots = []
				## FIXME: better to throw a runtime error here!
				return
			slot = s.copy()
			slot.holds = []
			self.slots.append(slot)
			## add slot for channels
			if slot.type.name=="channel": 
				slot.slot = None
				s = self.task.getSlot(sraw[1])
				if s: slot.slot = s.copy()
				## FIXME: also here!
			## add objects
			for oname in sraw[2]:
				o = self.task.getObject(oname)
				## FIXME: and here!
				if not o: continue
				slot.holds.append(o.copy())

	## show
	## --------------------------------------------------------------------
	def show(self):
		""" collect and display the contents of this configuration """
		slots = []
		for slot in sorted(self.slots, key=lambda x: x.name):
			holds = [o.name for o in slot.holds]
			slots.extend([[slot.name, slot.slot.name if hasattr(slot, "slot") else None, holds if slot.type.ordered==1 else sorted(holds)]])
		return slots

	## showCustom
	## --------------------------------------------------------------------
	def showCustom(self, stypes=["pin",]):
		""" collect and display the contents of this configuration, customizable slot types, no channel slots """
		slots = []
		for slot in sorted(self.slots, key=lambda x: x.name):
			if len(stypes)>0 and slot.type.name not in stypes: continue
			holds = [o.name for o in slot.holds]
			slots.extend([[slot.name, holds if slot.type.ordered==1 else sorted(holds)]])
		return slots

	## write
	## --------------------------------------------------------------------
	def write(self):
		""" encode the content of this object into a dict stored in long-term memory """
		return {"name": self.name, "slots": self.show()}




## Task
## ========================================================================
class Task:
	""" the problem space """

	## __init__
	## --------------------------------------------------------------------
	def __init__(self, aps, name):
		""" constructor """
		self.aps          = aps
		self.name         = name
		self.slotTypes    = []
		self.objectTypes  = []
		self.objects      = []
		self.actions      = []
		self.handles      = []
		self.initial      = []
		self.current      = []
		self.final        = []
		self.before       = None



	## == access methods ==================================================

	## getAction
	## --------------------------------------------------------------------
	def getAction(self, name):
		""" returns an action item by name """
		return getItem(self.actions, name)

	## getChannels
	## --------------------------------------------------------------------
	def getChannels(self):
		""" returns all channels of the task """
		return [x for x in self.current if x.type.name=="channel"]

	## getHandle
	## --------------------------------------------------------------------
	def getHandle(self, name):
		""" returns a handle item by name """
		return getItem(self.handles, name)

	## getItem
	## --------------------------------------------------------------------
	def getItem(self, name):
		""" returns any item by name """
		i = self.getSlot  (name)
		if i: return i
		i = self.getAction(name)
		if i: return i
		i = self.getHandle(name)
		if i: return i
		return self.getObject(name)

	## getMovable
	## --------------------------------------------------------------------
	def getMovable(self, name):
		""" returns all movable items (objects and slots) by name """
		i = self.getSlot(name)
		if i: return i
		return self.getObject(name)

	## getMovables
	## --------------------------------------------------------------------
	def getMovables(self, itemType=None):
		""" returns all movable items (objects and slots) by type """
		if itemType in [x.name for x in self.current    ]: 
			if self.getItem(itemType).isMovable: return [self.getSlot(itemType)]
			return []
		if itemType in [x.name for x in self.objectTypes]: 
			return [x for x in self.objects if x.stype==itemType]
		return self.objects + [x for x in self.current if x.isMovable]

	## getObject
	## --------------------------------------------------------------------
	def getObject(self, name):
		""" returns an object item by name """
		return getItem(self.objects    , name)

	## getObjectType
	## --------------------------------------------------------------------
	def getObjectType(self, name):
		""" returns and object type item by name """
		return getItem(self.objectTypes, name)

	## getSlot
	## --------------------------------------------------------------------
	def getSlot(self, name, collection="current"):
		""" returns a slot item by name """
		return getItem(getattr(self, collection), name)

	## getSlots
	## --------------------------------------------------------------------
	def getSlots(self, collection="current", type=None):
		""" returns a slot item by name """
		slots = []
		for slot in getattr(self, collection):
			if type and slot.type.name!=type: continue
			slots.append(slot)
		return slots

	## getSlotType
	## --------------------------------------------------------------------
	def getSlotType(self, name):
		""" returns a slot type item by name """
		return getItem(self.slotTypes  , name)



	## == function methods ================================================

	## apply
	## --------------------------------------------------------------------
	def apply(self, handle, slotin, movable, slotout):
		""" applies a handle to the current problem space """
		## sanity check
		if not handle or not slotin or not movable or not slotout: return False
		## book-keep in case of revert
		copyTaskData(self, self.before)
		## carry out the action
		if handle.modulate=="object"                        : return self.applyObject(handle, slotin, movable, slotout)
		if handle.modulate in [x.name for x in self.current]: return self.applySlot  (handle, slotin, movable, slotout)
		## nothing done
		return False

	## applyObject
	## --------------------------------------------------------------------
	def applyObject(self, handle, slotin, obj, slotout):
		""" applies a handle to the current problem space """
		## check if output slot is of proper type
		if slotout.type.name == "pos": return False
		## check if the output slot can take another object or is full already
		if slotout.numberOfLayers <= len(slotout.holds): return False
		## check if handle can couple to that output slot
		if handle.final.stype=="slot":
			if handle.final != slotout     : return False
		else:
			if handle.final != slotout.type: return False
		## check if output slot has constraints
		if len(slotout.gradientAsc )>0 and len(slotout.holds)>0:
			for prop in slotout.gradientAsc:
				if getattr(slotout.holds[-1], prop) >= getattr(obj, prop): return False
		if len(slotout.gradientDesc)>0 and len(slotout.holds)>0:
			for prop in slotout.gradientDesc:
				if getattr(slotout.holds[-1], prop) <= getattr(obj, prop): return False
		if slotout.noNegSum and len(slotout.holds)>0:
			for prop in slotout.noNegSum:
				if sum(getattr(x, prop) for x in slotout.holds) + getattr(obj, prop) < 0: return False
		if slotout.noPosSum and len(slotout.holds)>0:
			for prop in slotout.noPosSum:
				if sum(getattr(x, prop) for x in slotout.holds) + getattr(obj, prop) > 0: return False
		## find the current place of the object
		myslot = self.findSlot(obj)
		if not myslot: return False
		## check if the slot of the object is the same as the input slot
		if slotin != myslot: return False
		## check if handle can couple to that input slot
		if handle.initial.stype=="slot":
			if handle.initial != myslot     : return False
		else: 
			if handle.initial != myslot.type: return False
		## check if input slot has constraints (gradient constraints already checked through slotout)
		if slotin.noNegSum and len(slotin.holds)>0:
			for prop in slotin.noNegSum:
				if sum(getattr(x, prop) for x in slotin.holds if x!=obj) < 0: return False
		if slotin.noPosSum and len(slotin.holds)>0:
			for prop in slotin.noPosSum:
				if sum(getattr(x, prop) for x in slotin.holds if x!=obj) > 0: return False
		## check if object is on the the top-most layer of the slot
		if myslot.type.ordered==1 and myslot.holds.index(obj)+1 != len(myslot.holds): return False
		## check position of the output slot in case it is the hand
		if slotout.type.name=="channel" and slotout.slot != slotin .pos: return False
		if slotin .type.name=="channel" and slotin .slot != slotout.pos: return False
		## execute the handle (= place the object on the new slot and update the state)
		slotout.holds.append(obj)
		slotin .holds.remove(obj)
		obj.slot = slotout
		return True

	## applySlot
	## --------------------------------------------------------------------
	def applySlot(self, handle, slotin, movable, slotout):
		""" applies a handle to the current problem space """
		## check if handle can couple to slots
		if handle.initial.name!="pos": return False
		if handle.final  .name!="pos": return False
		## check if output slot is of proper type
		if slotout.type.name != "pos": return False
		## check if movable can move to that output slot
		if slotout not in movable.bound: return False
		## find the current slot of the movable
		myslot = movable.slot
		if not myslot: return False
		## check if movable is on a good input slot
		if myslot.type.name != "pos": return False
		## check if movable is on the required input slot
		if myslot.name != slotin.name: return False
		## execute the handle (= place the movable on the new slot and update the state)
		movable.slot = slotout
		return True

	## applyTriangle
	## --------------------------------------------------------------------
	def applyTriangle(self, triangle):
		""" applies a triangle to the current problem space """
		## check if triangle is empty
		if not triangle or len(triangle.slots)==0: return
		## clear everything outside the given triangle
		for v in ["initial", "final", "current"]:
			for i,slot in enumerate(getattr(self, v)):
				if slot in triangle.slots: continue
				getattr(self, v).remove(slot)
				del(slot)

	## config
	## --------------------------------------------------------------------
	def config(self, collection="current"):
		""" returns a Config object that corresponds to this task """
		return Config(self, fromTask=collection)

	## copy
	## --------------------------------------------------------------------
	def copy(self, name):
		""" builds a copy of this task under a new name """
		task = createTask(self.aps, name)
		copyTaskData(self, task)
		return task

	## dump
	## --------------------------------------------------------------------
	def dump(self):
		""" dumps the current configuration of the task """
		return "%s: %s"%(self.name, self.config().dump())

	## findSlot
	## --------------------------------------------------------------------
	def findSlot(self, movable):
		""" finds the current slot (loation) of a given object or slot (movable) """
		for slot in self.current:
			if movable.name not in [x.name for x in slot.holds]: continue
			return slot
		return None

	## findFilledSlot
	## --------------------------------------------------------------------
	def findFilledSlot(self):
		""" finds the first slot of this task that is filled """
		for slot in self.current:
			if len(slot.holds)==0: continue
			return slot
		return None

	## load
	## --------------------------------------------------------------------
	def load(self, triangle=None):
		""" builds the problem space of the task at hand """

		## general properties

		## load object types
		for entry in self.aps.j["objectTypes"]:
			item            = Item(self, "objectType", entry["name"])
			item.properties = entry["properties"]
			self.objectTypes.append(item)
		## load slot types
		for entry in self.aps.j["slotTypes"]:
			item       = Item(self, "slotType", entry["name"])
			storeVals(item, entry, ["numberOfLayers", "ordered", "gradientAsc", "gradientDesc", "noNegSum", "noPosSum"])
			self.slotTypes.append(item)
		## load actions
		## FIXME: not implemented in this version
		pass
		## load handles
		for entry in self.aps.j["handles"]:
			item         = Item(self, "handle", entry["name"])
			storeVals(item, entry, ["type", "modulate"])
			self.handles.append(item)
## FIXME: uncomment once actions are implemented
#		## link actions back to the object types
#		for entry in self.aps.j["objectTypes"]:
#			item         = self.getObjectType(entry["name"])
#			item.actions = [self.getAction(x) for x in entry["actions"]]

		## task-related properties

		## load objects
		for entry in self.aps.j["task"]["objects"]:
			item            = Item(self, "object", entry["name"])
			item.type       = self.getObjectType(entry["type"])
			item.isMovable  = True
			item.slot       = None
			for prop in item.type.properties:
				setattr(item, prop, entry[prop])
			self.objects.append(item)
		## load slots
		inherit = ["numberOfLayers", "gradientAsc", "gradientDesc", "noNegSum", "noPosSum"]
		for entry in self.aps.j["task"]["slots"]:
			objs           = [self.getObject(x) for x in entry["holds"]]
			item           = Item(self, "slot", entry["name"])
			item.type      = self.getSlotType(entry["type"])
			item.holds     = objs
			item.score     = entry["score"]
			for atr in inherit: setattr(item, atr, getattr(item.type, atr))
			for obj in objs   : obj.slot = item
			self.current.append(item)
		## link slots to one another
		for entry in self.aps.j["task"]["slots"]:
			item           = self.getSlot(entry["name"])
			item.pos       = self.getSlot(entry["pos"]) if "pos" in entry.keys() else None
			item.bound     = [self.getSlot(x) for x in entry["bound"]]
			item.isMovable = len(item.bound)>1
			if item.isMovable: item.slot = item.bound[0] ## first one by default
		## link slots to handles
		for entry in self.aps.j["handles"]:
			item         = self.getHandle(entry["name"])
			item.initial = self.getSlot(entry["initial"]) if self.getSlot(entry["initial"]) else self.getSlotType(entry["initial"])
			item.final   = self.getSlot(entry["final"  ]) if self.getSlot(entry["final"  ]) else self.getSlotType(entry["final"  ])
		## copy default for final states
		self.final = [x.copy() for x in self.current]
		## set initial and current state
		for entry in self.aps.j["task"]["initial"]:
			item       = self.getSlot(entry["name"])
			item.holds = [self.getObject(x) for x in entry["holds"]]
			for x in entry["holds"]: self.getObject(x).slot = item
		self.initial = [x.copy() for x in self.current]
		## set final state
		for entry in self.aps.j["task"]["final"]:
			item       = self.getSlot(entry["name"], "final")
			item.holds = [self.getObject(x) for x in entry["holds"]]

		## task-related constraints

		## apply triangle, i.e., clear everything outside of it
		self.applyTriangle(triangle)

		## load constraints (= overwrite certain parameters)
		for entry in self.aps.j["task"]["constraints"]:
			for key,entry in entry.items():
				if key=="name": continue
				item = self.getItem(key)
				storeVals(item, entry, list(entry.keys()))

		## book-keep the task for revert
		self.before = Task(self.aps, "%s_before"%self.name)

	## log
	## --------------------------------------------------------------------
	def log(self):
		""" dumps the current configuration of the task in dict form for logging """
		holds = {"name": self.name}
		for slot in self.current:
			holds[slot.name] = [x.name for x in slot.holds]
		return holds

	## reload
	## --------------------------------------------------------------------
	def reload(self, task, triangle):
		""" take a subset of another task for a given triangle """
		## copy data from other task
		copyTaskData(task, self)
		## apply the triangle
		self.applyTriangle(triangle)

	## reset
	## --------------------------------------------------------------------
	def reset(self, config):
		""" resets the task to a given state; assumes that the triangles are equal """
		for slot in config.slots:
			mySlot = self.getSlot(slot.name)
			myObjs = [self.getObject(x.name) for x in slot.holds]
			mySlot.holds = myObjs
			for obj in myObjs: obj.slot = mySlot
			if slot.type.name=="channel": mySlot.slot = self.getSlot(slot.slot.name)

	## revert
	## --------------------------------------------------------------------
	def revert(self):
		""" reverts/undoes the last move invoked with the apply method """
		copyTaskData(self.before, self)

	## update
	## --------------------------------------------------------------------
	def update(self, smaller):
		""" inserts the positions of a smaller task into this task, updating the condition of the slots involved """
		## move the objects of this task according to location in the other task
		for slot in smaller.current:
			mySlot = self.getSlot(slot.name)
			mySlot.holds = []
			for obj in slot.holds:
				myObj      = self.getObject(obj.name)
				myObj.slot = mySlot
				mySlot.holds.append(myObj)
		## move all channels of this task	
		for movable in smaller.getMovables():
			if     movable.stype=="object": continue
			if not movable.isMovable      : continue
			myMovable      = self.getSlot(movable.name)
			myMovable.slot = self.getSlot(smaller.getSlot(movable.name).slot.name)




## Exterior
## ========================================================================
class Exterior:

	## __init__
	## --------------------------------------------------------------------
	def __init__(self, aps):
		""" constructor """
		self.aps  = aps
		self.lct  = None

	## do
	## --------------------------------------------------------------------
	def do(self, task, strategy):
		""" apply an LCT strategy to the Exterior, generate response (True if it worked, False if not) """
		## try to execute it (note that items are re-picked from the task according to name)
		return task.apply(task.getHandle(strategy.handle.name), task.getSlot(strategy.slotin.name), task.getMovable(strategy.movable.name), task.getSlot(strategy.slotout.name))


