

## Control
## ========================================================================
class Control:
	""" control instance, overseeing all processing """

	## __init__
	## --------------------------------------------------------------------
	def __init__(self, aps):
		""" constructor """
		self.aps    = aps
		self.name   = "ctl"
		self.dn     = None
		self.before = None
		self.it     = 0

	## load
	## --------------------------------------------------------------------
	def load(self):
		""" load control """
		self.before = self.dn.task.copy("control_before")

	## do
	## --------------------------------------------------------------------
	def do(self):
		""" run an individual processing step per iteration """

		## proceed with ordinary iterations; i.e. try the next move, capture feedback by the downstream component
		success = self.dn.do()

		## careful about timescale! downstream has multiple moves for each move executed here
		## the downstream layers returns True if it wants to continue to the next iteration -- this layer needs to follow suit
		if success:
			return True

		## then, once the downstream move has been completed or truncated, this layer must take action

		## if processing in the downstream layer has been completed successfully, truncate the loop
		if self.dn.isFinal:
			print("Arrived at the final state!")
			return False

		## if processing in the downstream layer has NOT been completed successfully, start all over again in the next iteration
		return True


