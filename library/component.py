

## Component
## ========================================================================
class Component(object):
	""" base class for all branches and components """

	## __init__
	## --------------------------------------------------------------------
	def __init__(self, aps, name):
		""" constructor """
		self.aps      = aps       ## link to kernel
		self.task     = aps.task  ## link to the main task (default)
		self.name     = name      ## short name of the branch
		self.allMoves = None      ## collection of all available moves (working memory)
		self.recent   = None      ## the move done most recently
		self.move     = None      ## the current move

	## findMove
	## --------------------------------------------------------------------
	def findMove(self, other):
		""" find this version of an existing move """
		for move in self.allMoves:
			if move == other: return move
		return None

	## getMove
	## --------------------------------------------------------------------
	def getMove(self, name):
		""" finds a move known by the branch via its name """
		for move in self.allMoves:
			if move.name==name: return move
		return None

	## log
	## --------------------------------------------------------------------
	def log(self, step, key, value):
		""" wrapper around the logger::record function for easier recording of data """
		self.aps.log.record(self.name, step, key, value)

	## logStrategies
	## --------------------------------------------------------------------
	def logStrategies(self):
		""" adds strategies of this component to the logger """
		moves = {}
		for move in self.allMoves:
			moves[move.name] = move.write()	
		self.aps.log.add("strategies", self.name, moves)


