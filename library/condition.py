

## Condition
## ========================================================================
class Condition:
	""" class for condition objects, by which the application (or not application) of a strategy is learned """

	## __init__
	## --------------------------------------------------------------------
	def __init__(self, aps, name=None, config=None, prev=None, strategy=None, isPos=None, fromDict=None):
		""" constructor """
		self.aps      = aps
		self.task     = aps.task
		self.name     = name
		self.config   = config 
		self.prev     = prev
		self.strategy = strategy
		self.isPos    = isPos
		if fromDict: self.read(fromDict)

	## __eq__
	## --------------------------------------------------------------------
	def __eq__(self, other):
		""" tests if this Condition object is the same as another Condition object """
		if type(other.prev    )!=type(self.prev    ): return False
		if type(other.strategy)!=type(self.strategy): return False
		return self.isPos==other.isPos and self.config==other.config and self.prev==other.prev and self.strategy==other.strategy

	## __neq__
	## --------------------------------------------------------------------
	def __neq__(self, other):
		""" tests if this Condition object is not the same as another Condition object """
		return not self==other

	## applies
	## --------------------------------------------------------------------
	def applies(self, config, prev, strategy):
		""" probes a given config and returns true if the strategy shall be applied """
		if type(prev    )!=type(self.prev    ): return False
		if type(strategy)!=type(self.strategy): return False
		return self.config==config and self.prev==prev and self.strategy==strategy

	## dump
	## --------------------------------------------------------------------
	def dump(self):
		""" dumps the content of this object to screen (for debugging) """
		return "Condition (%s, %s, %s, %s, %s)"%(self.name, self.config.name, self.prev.name if self.prev else None, self.strategy.name, "pos" if self.isPos else "neg")

	## read
	## --------------------------------------------------------------------
	def read(self, d):
		""" decode a dict from long-term memory to retrieve the content of this object """
		configs       = self.aps.cache.reestablish("cfg")
		self.name     = d["name"]
		self.config   = configs.get(d["config"])
		self.prev     = self.aps.findStrategy(d["prev"    ])
		self.strategy = self.aps.findStrategy(d["strategy"])
		self.isPos    = True if d["isPos"]==1 else False

	## write
	## --------------------------------------------------------------------
	def write(self):
		""" encode the content of this object into a dict stored in long-term memory """
		return {"name": self.name, "config": self.config.name, "prev": self.prev.name if self.prev else None, "strategy": self.strategy.name, "isPos": 1 if self.isPos else 0}


