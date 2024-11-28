import os
import re
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")))
from library.functions import readJson
from library.plotter   import plots

def getData(path, num):
	## linear line in y
	if "linear:" in path: 
		val = int(re.findall(r"(?<=y=)\d+", path)[0])
		return [(x,val) for x in range(1,num+1)]
	## proper data from JSON files
	nIts = []
	for i in range(1,num+1):
		p = "%s/output_%03d.json"%(path, i)
		if not os.path.exists(p): continue
		j = readJson(p)
		nIts.append((i, len(j)))
	return nIts


contours = [
            ("linear: y=27"                             , "Tower of Hanoi (3d, 3p, min)"   , {"linestyle": "dotted", "linewidth": 1, "color": "lightcoral"}),
            ("linear: y=36"                             , "Hobbits and Orcs (3p, min)"     , {"linestyle": "dotted", "linewidth": 1, "color": "lightsteelblue"}),

            ("plotter/towerofhanoi_3d3p/prec1"          , "Tower of Hanoi (3d, 3p, prec=1)", {"linestyle": "solid" , "linewidth": 1, "color": "firebrick"}),
            ("plotter/towerofhanoi_3d3p/prec2"          , "Tower of Hanoi (3d, 3p, prec=2)", {"linestyle": "dashed", "linewidth": 1, "color": "indianred"}),

            ("plotter/hobbitsandorcs_3p_unordered/prec1", "Hobbits and Orcs (3p, prec=1)"  , {"linestyle": "solid" , "linewidth": 1, "color": "darkblue"}),
            ("plotter/hobbitsandorcs_3p_unordered/prec2", "Hobbits and Orcs (3p, prec=2)"  , {"linestyle": "dashed", "linewidth": 1, "color": "royalblue"}),
            ("plotter/hobbitsandorcs_3p_unordered/prec4", "Hobbits and Orcs (3p, prec=4)"  , {"linestyle": "dashed", "linewidth": 1, "color": "cornflowerblue"}),

           ]

num   = 10 ## number of repetitions
datas = []

for path,title,style in contours:
	data = getData(path, num)
	datas.append((data, title, style))

plots("combPlot.pdf", datas, "repetition", "number of moves")

