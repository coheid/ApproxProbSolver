import argparse
import os 
import sys

from library.plotter import Plotter

base   = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser(description='Approximate Problem Solver, plotting script.')
parser.add_argument('path', metavar='path', type=str,
                    help='path to a valid json input file')
parser.add_argument('-b'  , metavar='base', type=str, default=base,
                    help='path to the base directory')
parser.add_argument('-n'  , metavar='num', type=int, default=10,
                    help='number of executions of the code to be carried out')
args = parser.parse_args()

if not os.path.exists("%s/%s"%(args.b, args.path)): 
	print("ERROR: Give a valid input JSON file!")
	sys.exit()

x = Plotter("plotter", args.b, args.n)
x.load (args.path)
x.do   ()
x.close()

