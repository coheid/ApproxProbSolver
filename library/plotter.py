import os
import matplotlib.pyplot as plt
import matplotlib.ticker as tck

from library.functions import mkdir, readJson
from library.kernel    import Aps


## decorations
## ------------------------------------------------------------------------
def decorations(ax, xlabel, ylabel):
	""" adds style to the plot """
	plt.margins(0,0)
	plt.subplots_adjust(left=0.12, right=0.98, top=0.98, bottom=0.12)
	plt.xlabel(xlabel, labelpad=6, fontsize=12)
	plt.ylabel(ylabel, labelpad=8, fontsize=12)
	ax.tick_params(axis='both', which='major', labelsize=12)
	ax.tick_params(axis='both', which='minor', labelsize=10)
	plt.title("")

## plot
## ------------------------------------------------------------------------
def plot(path, data, xlabel, ylabel, xIntTicks=True):
	""" simple plotting function for a single contour """
	x = [z[0] for z in data]
	y = [z[1] for z in data]
	plt.clf()
	fig, ax = plt.subplots()
	plt.plot(x, y)
	plt.xticks(x)
	if max(y)>0: ax.set_ylim([0, max(y)*1.2])
	decorations(ax, xlabel, ylabel)
	plt.savefig(path)

## plots
## ------------------------------------------------------------------------
def plots(path, datas, xlabel, ylabel):
	""" simple plotting function for a multiple contours """
	if type(datas)!=list: return
	plt.clf()
	fig, ax = plt.subplots()
	xt = []
	ym = 0
	for data,label,style in datas:
		x = [z[0] for z in data]
		y = [z[1] for z in data]
		for i in x: 
			if i in xt: continue
			xt.append(i)
		if ym<max(y): ym = max(y)
		plt.plot(x, y, **style, label=label)
	plt.xticks(xt)
	#if ym>0: ax.set_ylim([0, ym*1.2])
	if ym>0: 
		ax.set_ylim([10, ym*1.5])
		ax.set_yscale("log")
	plt.legend(loc="upper right", fontsize=12, fancybox=True, framealpha=1.0)
	decorations(ax, xlabel, ylabel)
	plt.savefig(path)



## Plotter
## ========================================================================
class Plotter:
	""" plotter class """

	## __init__
	## --------------------------------------------------------------------
	def __init__(self, name, bpath, num):
		""" constructor """
		self.name    = name  ## name of the plotter
		self.base    = bpath ## base path
		self.outpath = None  ## output path
		self.num     = num   ## number of executions
		self.jpath   = ""    ## path to the input JSON

	## close
	## --------------------------------------------------------------------
	def close(self):
		""" do any post-processing here and finish the plotter """
		pass

	## do
	## --------------------------------------------------------------------
	def do(self):
		""" main procedure to run the plotter """
		self.doAps()
		self.doPlots()

	## doAps
	## --------------------------------------------------------------------
	def doAps(self):
		""" runs APS to do the actual simulation and merely transfers the output to the relevant directory """ 
		for i in range(self.num):
			## run the simulation
			aps   = Aps("aps", self.base)
			aps.load (self.jpath)
			aps.do   ()
			aps.close()
			## transfer output
			mv("%s/%s.json"%(aps.outpath, aps.name), "%s/output_%03d.json"%(self.outpath, i))

	## doPlots
	## --------------------------------------------------------------------
	def doPlots(self):
		""" do the analysis, collecting data from the raw outputs and creating plots """
		## collect data
		nIts  = [] ## number of iterations
		nLcts = [] ## number of LCT strategies built
		nInts = [] ## number of INT strategies built
		nIcms = [] ## number of ICM strategies built
		nScms = [] ## number of SCM strategies built
		nTris = [] ## number of triangles built
		nCnds = [] ## number of conditions built
		for i in range(1,self.num+1):
			j = readJson("%s/output_%03d.json"%(self.outpath, i))
			nIts .append((i, len(j)))
			nLcts.append((i, len(j[-1]["strategies"]["lct"])))
			nInts.append((i, len(j[-1]["strategies"]["int"])))
			nIcms.append((i, len(j[-1]["strategies"]["icm"])))
			nScms.append((i, len(j[-1]["strategies"]["scm"])))
			nTris.append((i, len(j[-1]["strategies"]["tri"])))
			nCnds.append((i, len(j[-1]["strategies"]["cnd"])))
		## plot data
		plot("%s/nits_vs_exec" %self.opath, nIts , "repetition", "number of iterations"    )
		plot("%s/nlcts_vs_exec"%self.opath, nLcts, "repetition", "number of LCT strategies")
		plot("%s/nints_vs_exec"%self.opath, nInts, "repetition", "number of INT strategies")
		plot("%s/nicms_vs_exec"%self.opath, nIcms, "repetition", "number of ICM strategies")
		plot("%s/nscms_vs_exec"%self.opath, nScms, "repetition", "number of SCM strategies")
		plot("%s/ntris_vs_exec"%self.opath, nTris, "repetition", "number of triangles"     )
		plot("%s/ncnds_vs_exec"%self.opath, nCnds, "repetition", "number of conditions"    )
		plots("%s/strats_vs_exec"%self.opath, [(nLcts, "LCT", {"linestyle": "solid", "color": "red"  }),\
		                                       (nInts, "INT", {"linestyle": "solid", "color": "blue" }),\
		                                       (nIcms, "ICM", {"linestyle": "solid", "color": "green"}),\
		                                       (nScms, "SCM", {"linestyle": "solid", "color": "cyan" })], "repetition", "number of strategies")

	## load
	## --------------------------------------------------------------------
	def load(self, jpath):
		""" build the processing structure and initialize components """
		self.jpath = jpath
		## extract job name and create output directory
		oname        = os.path.basename(jpath)[0:-5] ## cut off .json
		self.outpath = "%s/plotter/%s"%(self.base, oname)
		mkdir(self.outpath)


