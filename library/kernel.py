import json
import os

from library.cache     import Cache
from library.condition import Condition
from library.control   import Control
from library.functions import mkdir, readJson
from library.exterior  import Config, Task, Exterior
from library.external  import StrategyLct, LCT
from library.ic        import Triangle, ThreefoldWay, StrategyIc, ICM, SCM, buildTriangleFromTask
from library.internal  import StrategyInt, InternalInterface
from library.logger    import Logger



## Aps
## ========================================================================
class Aps:
	""" the main class of the simulation """

	## __init__
	## --------------------------------------------------------------------
	def __init__(self, name, bpath):
		""" constructor """
		self.name          = name
		self.base          = bpath
		self.outpath       = None
		self.j             = None
		self.log           = None
		self.cache         = None
		self.task          = None
		self.ext           = None
		self.lct           = None
		self.int           = None
		self.icm           = None
		self.scm           = None
		self.ctl           = None
		self.allConfigs    = None ## collection of all configs    used in the system
		self.allTriangles  = None ## collection of all triangles  used in the system
		self.allConditions = None ## collection of all conditions used in the system
		self.components    = ["lct", "int", "icm", "scm"] ## hard-coded list of those components always included in output log

	## applies
	## --------------------------------------------------------------------
	def applies(self, config, prev, strategy):
		""" tests if a given strategy is applicable in a given task, as learned """
		## find the condition, if it exists
		cnd = self.findCondition(config, prev, strategy)
		## if no condition recorded, return true
		if not cnd: return True
		## if a condition exists, return isPos 
		## (if isPos==True, the config has to be as given, hence True; if isPos==False, the config may not be as given, hence False)
		return cnd.isPos

	## close
	## --------------------------------------------------------------------
	def close(self):
		""" do any post-processing here and finish the simuation """
		self.log  .logStrategies()
		self.log  .write()
		self.cache.write()

	## createConfig
	## --------------------------------------------------------------------
	def createConfig(self, task=None, name=None, slots=None, config=None, itName=False):
		""" create a config in a safe way """ 
		## create the config
		config = Config(task, name, slots) if not config else config
		## check if it already exists; if so, return existing
		excfg  = self.findConfig(config)
		if excfg: return excfg
		## iterate the name if requested, store it in long-term memory
		if itName: config.name = "cfg_%03d"%(len(self.allConfigs)+1)
		self.cache.permanentize(cfg = config)
		return config

	## createTriangle
	## --------------------------------------------------------------------
	def createTriangle(self, task=None, name=None, slots=None, triangle=None):
		""" create a triangle in a safe way """ 
		triangle = Triangle(task, name, slots) if not triangle else triangle
		extri    = self.findTriangle(triangle)
		if extri: return extri
		self.cache.permanentize(tri = triangle)
		return triangle

	## do
	## --------------------------------------------------------------------
	def do(self):
		""" main procedure to run the simulation """
		for iStep in range(self.j["simulation"]["maxIts"]):
			print("Processing iteration",iStep)
			self.log.newIteration()	
			self.ctl.it = iStep
			ret = self.ctl.do()
			if not ret: return

	## findCnd
	## --------------------------------------------------------------------
	def findCnd(self, other):
		""" find this version of an existing condition """
		for cnd in self.allConditions:
			if cnd == other: return cnd
		return None

	## findCondition
	## --------------------------------------------------------------------
	def findCondition(self, config, prev, strategy):
		""" finds the condition that applies to the current configuration of a given config and a specific strategy """
		for cnd in self.allConditions:
			if not cnd.applies(config, prev, strategy): continue
			return cnd
		return None

	## findConfig
	## --------------------------------------------------------------------
	def findConfig(self, other):
		""" find this version of an existing config """
		for cfg in self.allConfigs:
			if cfg == other: return cfg
		return None

	## findStrategy
	## ------------------------------------------------------------------------
	def findStrategy(self, name):
		""" finds a strategy by name in the cache """
		if not name: return None
		lcts = self.cache.reestablish("lct")
		ints = self.cache.reestablish("int")
		icms = self.cache.reestablish("icm")
		scms = self.cache.reestablish("scm")
		if lcts.has(name): return lcts.get(name)
		if ints.has(name): return ints.get(name)
		if icms.has(name): return icms.get(name)
		if scms.has(name): return scms.get(name)
		return None

	## findTriangle
	## --------------------------------------------------------------------
	def findTriangle(self, other):
		""" find this version of an existing triangle """
		for tri in self.allTriangles:
			if tri == other: return tri
		return None

	## learn
	## --------------------------------------------------------------------
	def learn(self, config, prev, move, isPos):
		""" learn a new condition (positive or negative) """
		## nothing to learn if there is no move
		if not move: return
		## make sure, the config is stored
		cfg  = self.createConfig(config=config, itName=True)
		## construct the condition		
		name = "cnd_%03d"%(len(self.allConditions)+1)
		c    = Condition(self, name, cfg, prev, move, isPos)
		## do not acquire it if it already exists
		if self.findCnd(c): return
		## learn it
		self.cache.permanentize(cnd=c)

	## load
	## --------------------------------------------------------------------
	def load(self, jpath):
		""" build the processing structure and initialize components """
		## create output directory
		self.outpath = "%s/output"%self.base
		mkdir(self.outpath)
		## load logger and record
		self.log  = Logger(self)
		## load json
		self.j    = readJson("%s/%s"%(self.base, jpath))
		## build problem space
		self.task = Task(self, "main")
		self.task.load()
		## initialize components
		self.ext = Exterior         (self)
		self.lct = LCT              (self)
		self.int = InternalInterface(self)
		self.icm = ICM              (self)
		self.scm = SCM              (self)
		self.ctl = Control          (self)
		## link components to each other
		self.ext.lct = self.lct
		self.lct.ext = self.ext
		self.lct.int = self.int
		self.int.lct = self.lct
		self.int.icm = self.icm
		self.icm.dn  = self.int
		self.icm.up  = self.scm
		self.scm.dn  = self.icm
		self.scm.up  = self.ctl
		self.ctl.dn  = self.scm
		## load cache (must come after component init and links)
		self.cache = Cache(self)
		self.cache.read()
		## load components (must come after cache)
		self.int.load()
		self.icm.load()
		self.scm.load()
		self.ctl.load()

	## logStrategies
	## --------------------------------------------------------------------
	def logStrategies(self):
		""" adds strategies of this component to the logger """
		## configs
		configs = {}
		for cfg in self.allConfigs:
			configs[cfg.name] = cfg.write()	
		self.log.add("strategies", "cfg", configs)
		## triangles
		triangles = {}
		for tri in self.allTriangles:
			triangles[tri.name] = tri.write()	
		self.log.add("strategies", "tri", triangles)
		## conditions
		conditions = {}
		for cnd in self.allConditions:
			conditions[cnd.name] = cnd.write()	
		self.log.add("strategies", "cnd", conditions)


