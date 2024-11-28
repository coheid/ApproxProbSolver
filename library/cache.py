import os

from library.condition import Condition
from library.exterior  import Config
from library.external  import StrategyLct
from library.functions import mkdir, readJson, writeJson
from library.ic        import Triangle, ThreefoldWay, StrategyIc
from library.internal  import StrategyInt



## Collection
## ========================================================================
class Collection:
	""" helper class for collections of elements stored in the cache """

	## __init__
	## --------------------------------------------------------------------
	def __init__(self, aps, name):
		""" constructor """
		self.aps  = aps
		self.name = name
		self.data = {}

	## __iter__
	## --------------------------------------------------------------------
	def __iter__(self):
		""" iterator """
		for k,v in self.data.items():
			yield v

	## __len__
	## --------------------------------------------------------------------
	def __len__(self):
		""" length """
		return len(self.data.keys())

	## get
	## --------------------------------------------------------------------
	def get(self, key):
		""" retrieves an element from the collection """
		if not self.has(key): return None
		return self.data[key]

	## has
	## --------------------------------------------------------------------
	def has(self, key):
		""" checks if an element exists in the collection """
		return key in self.data.keys()

	## load
	## --------------------------------------------------------------------
	def load(self, jin, comp, toLink):
		""" parses the input json and fills the collection """
		link = self.aps.task if toLink=="task" else getattr(self.aps, toLink) if toLink in self.aps.components else self.aps
		for entry in jin:
			for k,v in entry.items():
				self.data[k] = comp(link, fromDict=v)

	## save
	## --------------------------------------------------------------------
	def save(self):
		""" exports the collection into json format """
		jout = []
		for k,v in self.data.items():
			jout.append({k: self.data[k].write()})
		return jout

	## set
	## --------------------------------------------------------------------
	def set(self, key, comp):
		""" adds a new element to the collection """
		self.data[key] = comp




## Cache
## ========================================================================
class Cache:
	""" long-term memory """

	## __init__
	## --------------------------------------------------------------------
	def __init__(self, aps):
		""" constructor """
		self.aps    = aps
		self.task   = aps.task
		self.comps  = {"lct": (self.aps.lct, "allMoves"), "int": (self.aps.int, "allMoves"), "tri": (self.aps, "allTriangles"), "icm": (self.aps.icm, "allMoves"), "scm": (self.aps.scm, "allMoves"), "cnd": (self.aps , "allConditions"), "cfg": (self.aps, "allConfigs")}
		self.strct  = {"lct": (StrategyLct , "aps"     ), "int": (StrategyInt , "aps"     ), "tri": (Triangle, "task"        ), "icm": (ThreefoldWay, "icm"     ), "scm": (StrategyIc  , "scm"     ), "cnd": (Condition, "cnd"          ), "cfg": (Config  , "task"      )}
		self.order  = ["cfg", "tri", "lct", "int", "icm", "scm", "cnd"]
		self.data   = {name: Collection(self.aps, name) for name in self.order}

	## permanentize
	## --------------------------------------------------------------------
	def permanentize(self, **kwargs):
		""" adds a strategy to long-term memory in case its info is complete """
		for k,v in kwargs.items():
			if k not in self.data.keys(): continue
			self.data[k].set(v.name, v)

	## read
	## --------------------------------------------------------------------
	def read(self):
		""" loads the cache (and thus strategies) of the task at hand from disk """
		if self.aps.j["simulation"]["reset"]==1: return
		mkdir("%s/cache"%self.aps.base)
		path = "%s/cache/%s"%(self.aps.base, self.aps.name)
		mkdir(path)
		if not os.path.exists(path): return
		for n in self.order: self.readJson(path, n)

	## readJson
	## --------------------------------------------------------------------
	def readJson(self, path, name):
		""" loads an individual json file into the cache """
		if os.path.exists("%s/%s.json"%(path, name)):
			self.data[name].load(readJson("%s/%s.json"%(path, name)), self.strct[name][0], self.strct[name][1])
		setattr(self.comps[name][0], self.comps[name][1], self.data[name]) ## link to the component

	## reestablish
	## --------------------------------------------------------------------
	def reestablish(self, what):
		""" reestablishes a set of strategies from long-term memory """
		if what not in self.data.keys(): return None
		return self.data[what]

	## write
	## --------------------------------------------------------------------
	def write(self):
		""" write cache to disk """
		for k,v in self.data.items():
			if len(v)==0: continue
			writeJson("%s/cache/%s/%s.json"%(self.aps.base, self.aps.name, k), v.save())


