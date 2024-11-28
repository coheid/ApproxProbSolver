from library.functions import writeJson


## Iteration
## ========================================================================
class Iteration:
	""" a container to log the output data fog a given iteration """

	## __init__
	## --------------------------------------------------------------------
	def __init__(self, logger, idx):
		""" constructor """
		self.logger = logger
		self.aps    = logger.aps
		self.idx    = idx
		self.steps  = ["before", "after", "top-down", "bottom-up", "used", "planned"]
		self.data   = {}

	## add
	## --------------------------------------------------------------------
	def add(self, cname, key, value):
		""" records data outside the components in the iteration """
		if cname not in self.data.keys(): self.data[cname] = {}
		self.data[cname][key] = value

	## load
	## --------------------------------------------------------------------
	def load(self):
		""" loads the default values for the iteration """
		self.data = {"iteration": {}}
		for comp in self.aps.components: 
			self.data[comp] = {}
			for step in self.steps:
				self.data[comp][step] = {}
		self.add("iteration", "i", self.idx)

	## record
	## --------------------------------------------------------------------
	def record(self, cname, step, key, value):
		""" records data for a given component in the iteration """
		if cname not in self.data       .keys(): self.data[cname]       = {}
		if step  not in self.data[cname].keys(): self.data[cname][step] = {}
		self.data[cname][step][key] = value

	## write
	## --------------------------------------------------------------------
	def write(self):
		""" writes the data into json format to save it to disk """
		return self.data


	
## Logger
## ========================================================================
class Logger:
	""" a logging system to record data per iteration step of the simulation and output it to a json """

	## __init__
	## --------------------------------------------------------------------
	def __init__(self, aps):
		""" constructor """
		self.aps     = aps
		self.idx     = 0
		self.data    = []
		self.current = None

	## add
	## --------------------------------------------------------------------
	def add(self, cname, key, value):
		""" records data for the current iteration outside the components """
		self.current.add(cname, key, value)

	## logStrategies
	## --------------------------------------------------------------------
	def logStrategies(self):
		""" adds strategies to the logger """
		self.aps    .logStrategies()
		self.aps.lct.logStrategies()
		self.aps.int.logStrategies()
		self.aps.icm.logStrategies()
		self.aps.scm.logStrategies()

	## newIteration
	## --------------------------------------------------------------------
	def newIteration(self, idx=None):
		""" opens a new iteration and sets the pointer to it """
		it = Iteration(self, idx if idx else self.idx)
		it.load()
		self.data.append(it)
		self.current = it
		self.idx    += 1

	## record
	## --------------------------------------------------------------------
	def record(self, cname, step, key, value):
		""" records data for a given component in the iteration """
		self.current.record(cname, step, key, value)

	## write
	## --------------------------------------------------------------------
	def write(self):
		""" writes the output to disk """
		if len(self.data)==0: return
		jraw = []
		for iteration in self.data:
			jraw.append(iteration.write())
		writeJson("%s/%s.json"%(self.aps.outpath, self.aps.name), jraw)


