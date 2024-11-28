# Approximate Problem Solver

This is the readme of the approximate problem solver (APS; github.com/coheid/ApproxProbSolver) algorithm that simulates productive processing in external and internal branches.



## Introduction

The point of this algorithm is to simulate productive processing in the external and internal branches, including low-level response-oriented processing by the LCT and high-level tasking by IC at the internal branch. 
Thus, it simulates the processing activity of an imaginary individual interacting with an imaginary problem setup in an imaginary laboratory.



### Princinpal Logic

The algorithm contains four components: the LCT, the internal interface, the ICM, and the SCM. 
These four components operate autonomously at each iteration of the stimulation, though they do exchange information with one another, such that emphasis can move from one component to the next.
Of course, these components are organized hierarchically, with the LCT lowest in the chain, the internal interface operating on top of it, the ICM being located on top of the internal interface, and the SCM connecting to the ICM. 
Generally, each iteration corresponds to an LCT-level move. 
The processing activity in the three higher-level components, then, spans multiple iterations. 

The principal logic of the algorithm is such that APS always interacts with a finite set of user-defined _objects_ through a finite set of user-defined general _moves_ (called _handles_), moving these objects from one user-defined _slot_ to another. 
The way these entities are defined by the user is discussed in below (see [Running the Simulation](#running-the-simulation)). 

The moves are defined _in principle_, meaning, the user defines what "can" be done (e.g. "grab", "move", or "place"), while the _specific_ move still needs to be constructed (e.g. "grab disk 1 from slot 1").
Objects are always bound to slots.
Slots can be any of three types: 
* _channels_ if they "belong" to the imaginary individual that is simulated here (a typical channel might be the hand of the imaginary individual), 
* _pins_ if they are part of the imaginary experimental setup the imaginary individual is confronted with, or 
* _pos_ if they label distinct, pre-defined positions throughout the imaginary experimental setup.

Besides objects, also channels can be moved from one slot to another.
While objects are moved from a pin-slot to a channel-slot or from a channel-slot to a pin-slot, channels can be moved from a pos-slot to another pos-slot. 
Pin-slots cannot be moved. 

The use of slots is a simplification that allows the discretization necessary for conducting an iteration-based simulation.
At every iteration, at most one move can be carried out, thus, either an object can be moved from one slot to another, or a channel can be moved from one slot to another.
The use of `pos`-type slots allows the pre-definition of all possible paths along which the channels can move, and this path is discretized via these slots, avoiding having to deal with irrelevant allocation-related mechanisms.

Overall, the definition of the moves and slots in this abstract way, enables the removal of low-level processing that would otherwise take place at the outer branch and its interfaces to the LCT. 
While this processing is relevant in reality, it is also extremely complex, and it is irrelevant when simulating productive processing at the internal branch. 



### Simulation Procedure

Throughout the program (code, input, and output), the four components are abbreviated with the following keys:
* `lct` denotes the local contextual trinity (LCT)
* `int` denotes the internal interface (abbreviated as INT in this readme)
* `icm` denotes the interactive contextual model (ICM) at the first contextual stage
* `scm` denotes the situative contextual model (SCM) at the second contextual stage
In addition, the exterior is integrated into the simulation via the key `ext`, and a dedicated control module is used with key (`ctl`) to oversee the simulation and truncate or restart it in case the corresponding conditions have been observed.

The strategies developed at each component are permanentized and reestablished in upcoming instances of the simulation. 
In this way they APS learns how to solve problems.

If APS cannot fall back on prior knowledge, it has to generate it from scratch.
This is done at each of the four central components separately.
They conduct their own processing at every step of the iteration, taking into account the processing conditions of the neighboring components. 
In so doing, every component suits a specific purpose.

While the LCT constructs and probes _any_ move against the exterior, the INT assembles _paths_ of consecutive LCT moves for single objects.
Here, _consecutive_ implies that an LCT move in the path must be logically related to the previous moves in that path. 
For example, the first move might be "grab disk 1 into hand at position 1" and a valid consecutive move would be "place disk 1 onto pin 1 at position 1" or "move hand from position 1 to position 2" but not "place disk 1 onto pin 2 at position 2".
The number of LCT moves incorporated into a single INT path can be limited via the `maxMovesInt` parameter (see [Running the Simulation](#running-the-simulation)).

While INT generates consecutive moves, these moves may not be very meaningful insofar that they do advance the current state towards the final state (e.g. grabbing disk 1 and then placing it back immediately). 
Instead, the ICM takes an INT move and checks whether or not it has advanced the current state, and if not, it discards it. 
In this way, it builds sequences of moves, each of which advancing the current state.
These moves do not need to be consecutive, so they can concern different objects at different slots.
Notably, the ICM does not require the paths to advance the current state towards the final state, but the current state could also be "moved away" from the final state. 

For every problem, there is a minimum number of LCT moves necessary to solve it, organized in a specific sequence of INT paths.
For example, consider the 27 LCT moves organized in 7 INT paths for the Tower of Hanoi problem (see [Examples](#examples)).
Any other sequence of INT paths potentially found by APS for a given ICM will
* either result in a dead end
* or contain additional INT paths that are futile.
Here, the ICM prevents paths from annihilating each other, meaning, one path undoes what another path has done before, or paths do not change the configuration (e.g. pick up a disk and place it back to the same pin). 
Still, ICM can do futile moves (e.g. move two disks to two pins and move one of them back), and it is the SCM that ensures an overall meaningful progress. 

In case the sequence contains futile INT paths, one can find two paths that are additive, meaning, they can be replaced by a single path.
For example, the first move (`move disk1 from pin1 to pin3`) might have been done by two paths (`move disk1 from pin1 to pin2` and `move disk1 from pin2 to pin3`). 
These moves are recombined in a posterior optimization step once a valid solution path has been found.
This optimization step is where _cognitive precision_ comes into play, potentially recombining futile moves that are a number `precision` moves apart from one another.
The larger this parameter is defined by the user, the further apart futile moves may be, the higher the cognitive precision is simulated. 

Generally, at each component, known strategies are preferred over the constitution of new strategies. 
However, randomness is inserted via a user-defined parameter (`probRedo`) at every component, dictating the probability for either trying an existing strategy or for attempting to generate a new strategy irrespective of the existing ones.
This is necessary as otherwise APS would merely repeat the first solution path that it finds, continue to run into the same dead ends, or never optimize its strategies. 
In this sense, one can view _inserted randomness_ as the curiosity and creativity of an individual that leads them to choose an alternative approach when repeating the same problem solving exercise.

For every configuration (i.e. object positions on slots), a metric can be computed, by assigning a score for every slot and multiplying that with the number of objects that it holds. 
Slots closer to the final state should be awarded higher scores, and no 0 score should be awarded at all (otherwise the _gradient_ between two different configurations may be zero). 
The more objects are in their final-state position (including ordered layers on pins), the higher the metric score of that configuration. 
If the difference between two configurations is zero, they are considered identical. 
This is used to determine whether or not the final-state configuration of the problem has been reached.



### Simplifications Compared to Full Theory

The architecture of the algorithm requires a number of simplifications of the mechanisms when compared to theory. 
These simplifications are either conceptual ones, where certain mechanisms or processes have been omitted or designed in a different way as is otherwise not feasible in this algorithm, or computational ones, arising from procedural limitations and being necessary for ensuring computational stability.

The conceptual simplifications are:
* the principal architecture with objects, handles, and slots is a simplification to real-world scenarios, which is necessary to construct any algorithm in the first place;
* proximity-flavor information is omitted completely, and all interactions with the exterior are conducted via distance-flavor information only; the generic case would involve triples $(s,d,p)$ for NC and $(t,c,s)$ for IC with arbitrary values;
* NC and IC do not confine processing activity, but they operate on downstream moves directly;
* the available moves and objects are defined explicitly (in abstract terms) through user input and do not need to be first discovered by the individual; in other words, external-branch processing is abstracted from completely, as this is not relevant to the questions under study; abstract objects and handles may allow to simulate logical reasoning; 
* accordingly, processing is not driven by quality, but the runtime of the algorithm itself drives processing;
* there is only a single procedural instance (no triangular exchange); accordingly, problems need to be well-defined by the user, and no too complex a problem can be processed requiring contextual scaling; this involves that the problem representation and definition of constraints and moves must be clear by the user;
* at all levels, randomness is inserted by a user parameter, potentially bypassing simple application of known strategies and allowing the optimization of strategies; in reality, this would be a goal-driven process, involving higher-level components beyond a single procedural instance;
* long-term memory is perfect, there are no retrieval effects and no loss;
* feedback through the exterior is modelled in a perfect way: either the move works or it does not, there is no intermediary response.

The computationally-motivated simplifications are:
* emphasis is always inserted anew at every iteration of the simulation, and it is inserted into the second contextual stage, such that it always flows top-down;
* repeated patterns of moves at the INT level are searched for and handled explicitly (in reality, these would be learned as part of the strategies themselves);
* configurations (i.e. object positions on slots) may not be re-encountered, meaning, every configuration is only allowed to be encountered once (to avoid circular behavior); 
* also the explicit truncation of path building in case the path has touched all available objects, or objects are in final configuration already would be learned strategically in reality;
* the handling of ownership and responsibility is simplified, e.g. the tensoral predicate of an ICM strategy contains the triangle directly rather than the modulation of the triangle; 
* NMs are merely copies of configurations of the associated tasks rather than networks of nonlinear context (in other words, they describe a purely static arrangement of objects and slots);
* virtual executions operate on the task itself rather than the NC, since this may require triangular exchange;
* the exchange of information between the different components is simplified.



## Installation

APS is installed by cloning this GitHub repository:
```
git clone git@github.com:coheid/ApproxProbSolver.git
``` 

The algorithm uses a number of Python libraries, most of which are standard to any Python installation.
However, potentially some of them need to be pre-installed, e.g. using `pip`:
```
pip install <library>
```
The full set of libraries required by APS is as follows:
* argparse
* collections
* copy
* json
* math
* matplotlib
* more_itertools
* numpy
* os
* random
* regex
* sys



## Execution

There are two modes of running APS: either executing an instance of the simulation and, thus, solving a specific problem, or analyzing the output of this and other simulation instances and generating plots.
For understanding the program architecture, please consult section [Program Architecture](#program-architecture). 



### Running the Simulation

The simulation is executed by running the main `aps.py` script, giving an input JSON file (see [Examples](#examples)) that defines the problem space and all operators.
The following line will run one instance of the simulation using the Tower of Hanoi example:
```
python aps.py examples/towerofhanoi.json
``` 
The simulation output, then, can be studied manually by considering the output JSON file that is to be found in the `output/` directory.


### Analyzing the Simulation Output

It can also be studied by repeating the simulation a `n` times, and the plotting contours for various parameters observed during repeated executions.
This is done automatically by a ddedicated plotting code, which is also run via the same input JSON and the number of repetitions via the `-n` parameter.
For example,
```
python plots.py examples/towerofhanoi.json -n 100
``` 
will repeat the simulation 100 times, transfer the output JSON file to a newly created `plotter/` directory, and then generate a number of diagrams related to different parameter, which are stored in the same directory.

Diagrams showing the performance of different problem examples can be generated via the `combPlot.py` script located in the `scripts/` sub-folder.


### Additional Scripts

Additional and more complex plots may be generated via scripts found in the `scripts/` sub-folder of the repository.

This also contains a script `genLct.py` which generates the cache JSON file for all possible LCT moves. 
This may be relevant for testing the behavior of the simulation at higher levels, bypassing the potentially cumbersome process of acquiring these strategies through the simulation.



## Program Architecture

APS consists of three scripts and a module library in which the objects utilized in the simulation are defined. 

The central executive is the `aps.py` script, which is run from comand line (see [Running the Simulation](#running-the-simulation)). 
Every execution runs the simulation one time until either the maximum number of iterations (`maxIts` parameter) is hit or the solution to the problem is found.

The executive constructs an instance of the `Aps` class defined in the `library/kernel.py` module, which serves as the main class of the simulation.

Each of the four central components is implemented as a dedicated object, and it contains its own strategies that 
Strategies are buffered, permanentized, and reestablished through the `Cache` class. 
Permanentization involves an export to a JSON file stored on disk in the `cache/` subfolder in the working directory of the algorithm.

A `Task` object is instantiated for one of two purposes: it either resolves the exterior as is ("real task"), or it is used as a playground for testing moves ("virtual task").
Notably, every component can potentially have its own copy of a task, since these components operate in the scope of different triangles. 
Furthermore, it may have additional task instances (e.g. in the `.before` member) to keep track of previous states of the problem.

`Config` objects allow the exchange and comparisons of object-slot configurations, meaning, the set of all slots in a given task and the objects held by these slots per layer.
`Triangle` objects implement external, extended, or real triangles, which are effectively labeled lists of slots irrespective of the objects that they hold.

The algorithm learns the application of strategies through `Condition` objects, which take a configuration, the previous move and the current/attempted move, and store a boolean (`isPos`, short for "is positive condition") for whether or not this move should be applied or avoided.
Conditions are collected in the cache together with all strategies and triangles that are permanentized, and conditions are probed upon re-establishment and generation of strategies.

At every iteration, the `do` function is called for every component.
In fact, the program proceeds by always calling the `do` method of the `Control` class, which merely oversees the execution and either continues it (if the method returns `True`) or truncates it (if the method returns `False`). 
The main loop is done in the `do` function of the `Aps` class in the kernel module.

For the `do` methods at every component, a return value of `True` implies progression to the next step, while `False` requires truncation as will be taken care of by the higher-level component. 
Notably, the return value of a lower-level component can be `True` when the higher-level component steers execution top-down, i.e., via a list of prior strategies for which it seeks implementation.
Likewise, it can be `False` if the lower-level component has encountered a failure (e.g. the desired strategy did not work) or if the implementation has been completed. 
In this sense, via the return value of the `do` method, the algorithm simulates the propagation of emphasis from one iteration to the next: it can either remain on that component (`True`) or be propagated upstream (`False`).
The downstream propagation is done within the higher-level `do` method always. 

The actual moves are always conducted at the lowest-level component, namely, the LCT.
Hence, it's `do` method needs to be called at every iteration.
In so doing, the LCT tries to apply a particular move to a given task at hand.
This is done via the `apply` method in the `Task` class, which knows about all slots and objects accessible in the task.
This method, thus, implements the lowest-level logic of actually moving objects and channels (collectively referred to as "movables") from one eligible slot to another. 

Auxiliary functions are provided in the `functions` module of the algorithm's library.

The output generated by the simulation is a JSON file documenting the strategies, input and outputs at each of the processing components in every iteration.
This documentation is generated by the `Logger` class during runtime. 

This file is written to disk in the `output/` subfolder in the working directory of the software. 
It is what is analyzed in the second step via the script `plot.py` (see [Analyzing the Simulation Output](#analyzing-the-simulation-output)).



## Examples

The folder `examples/` contains a number of input JSON files by which one can run APS for different standard problem solving exercises. 


### Arguments of the Input JSON File

The program parses a given input JSON file, which, in the case of a variant of the Tower of Hanoi problem, contains the following lines:
```
{
	"simulation": {
		"maxIts"      : 500,
		"maxMovesInt" : 4,
		"maxMovesIcm" : 100,
		"maxMovesScm" : 100,
		"maxRecsLct"  : 100,
		"maxRecsInt"  : 100,
		"maxRecsIcm"  : 50,
		"maxRecsScm"  : 50,
		"maxTruncsInt": 20,
		"maxTruncsIcm": 5,
		"probRedoLct" : 0.5,
		"probRedoInt" : 0.0,
		"probRedoIcm" : 0.0,
		"precision"   : 1,
		"reset"       : 0,
		"sizePattern" : 2
	},
	"objectTypes": [
		{"name": "disk", "actions": [], "properties": ["diameter"]}
	],
	"slotTypes": [
		{"name": "channel", "numberOfLayers": 3, "ordered": 0, "gradientAsc": [], "gradientDesc": [], "noNegSum": [], "noPosSum": []},
		{"name": "pin"    , "numberOfLayers": 3, "ordered": 1, "gradientAsc": [], "gradientDesc": [], "noNegSum": [], "noPosSum": []},
		{"name": "pos"    , "numberOfLayers": 1, "ordered": 0, "gradientAsc": [], "gradientDesc": [], "noNegSum": [], "noPosSum": []}
	],
	"actions": [
	],
	"handles": [
		{"name": "grab" , "type": "distance", "modulate": "object", "initial": "pin" , "final": "hand"},
		{"name": "move" , "type": "distance", "modulate": "hand"  , "initial": "pos" , "final": "pos" },
		{"name": "place", "type": "distance", "modulate": "object", "initial": "hand", "final": "pin" }
	],
	"task": {
		"name"    : "Tower of Hanoi (3 disks, 3 pins)", 
		"objects" : [
			{"name": "disk1", "type": "disk", "diameter": 0},
			{"name": "disk2", "type": "disk", "diameter": 1},
			{"name": "disk3", "type": "disk", "diameter": 2}
		],
		"slots"   : [
			{"name": "hand", "type": "channel", "holds": [], "score": -1  , "pos": "pos1", "bound": ["pos1", "pos2", "pos3"]}, 
			{"name": "pin1", "type": "pin"    , "holds": [], "score":  0.3, "pos": "pos1", "bound": ["pos1"]                }, 
			{"name": "pin2", "type": "pin"    , "holds": [], "score":  0.6, "pos": "pos2", "bound": ["pos2"]                }, 
			{"name": "pin3", "type": "pin"    , "holds": [], "score":  1  , "pos": "pos3", "bound": ["pos3"]                }, 
			{"name": "pos1", "type": "pos"    , "holds": [], "score": -1  , "pos": null  , "bound": []                      }, 
			{"name": "pos2", "type": "pos"    , "holds": [], "score": -1  , "pos": null  , "bound": []                      }, 
			{"name": "pos3", "type": "pos"    , "holds": [], "score": -1  , "pos": null  , "bound": []                      }
		],
		"initial": [
			{"name": "pin1", "holds": ["disk3", "disk2", "disk1"]}
		],
		"final": [
			{"name": "pin3", "holds": ["disk3", "disk2", "disk1"]}
		],
		"constraints": [
			{"name": "gradient"   , "pin1": {"gradientDesc": ["diameter"]}, "pin2": {"gradientDesc": ["diameter"]}, "pin3": {"gradientDesc": ["diameter"]}},
			{"name": "moveOneDisk", "hand": {"numberOfLayers": 1}}

		]
	}
}
```
This JSON contains six first-level keys. 

The key `simulation` contains all parameters affecting the entire simulation, including technical parameters. These parameters are as follows:
* `maxIts` (int) defines the maximum number of iteration steps per execution of the simulation;
* a move at a given component, will point to a sequence of moves at the downstream component directly related to it (e.g. an INT strategy is a path of a number of LCT moves); the maximum number of the downstream-level moves involved in a strategy of a given component can be regulated via the parameters `maxMovesInt`, `maxMovesIcm`, and `maxMovesScm` (all ints); notably, 4 is the minimum value applicable to `maxMovesInt`;
* at the beginning of every iteration and for each of the four components, an appropriate strategy (or move) must be chosen, this is either done by taking a random existing strategy or generating a new one (the choice of whether or not to test an existing strategy or develop a new one is defined by `probRedo` (float)); this is an iterative process relying on an recursive architecture of the relevant methods; in order to prevent any endless loops, the number of recursions are counted during the process, and the strategy-finding is truncated if this number exceeds a value specified by the user via the parameters `maxRecsLct`, `maxRecsInt`, `maxRecsIcm`, and `maxRecsScm` (all ints); in case a given component does not find a move, this information is propagated to the next component, which may be able to pick a move through its own mechanics; if no move is found at all for a given iteration of the simulation, this iteration is sacrificed (nothing is done), and the simulation proceeds to the next iteration step, where it will restart anew trying to find an applicable move;
* strategy finding may result in dead ends; this is because strategies are picked at random, and previous configurations (i.e. object positions on slots) may not be re-encountered at the ICM-level (this is to avoid going in circles); if INT is unable to generate a path that translates the current configuration into a new configuration that has not been encountered before for a number of iteration steps, the condition is considered a dead end by ICM, and processing starts anew; this threshold value can be tuned via `maxTruncsInt` (int).
* `precision` (int) gives the maximum distance between INT moves for which the merging is probed in the optimization of a solution path; here, a value of 2 means that the two INT moves must be consecutive, a value of 3 allows another INT move in between them; values lower than 2 effectively switch off the optimization of the solution path; via this method, the `precision` parameter effectively is a measure of cognitive precision; 
* `reset` (int, either 0 or 1) specifies, whether or not permanentized strategies should be re-established from the cache (1) or the cache should be cleared and the simulation should re-learn all strategies (0); 
* `sizePattern` (int) is the required number of elements a pattern of strategies at INT must have to be probed for repetition. For example, if the internal interface has executed the strategies
```
[int_001, int_005, int_002, int_008, int_005, int_007, int_002, int_008]
```
and this parameter was set to 2, the pattern `[int_002, int_008]` would be found as having been repeated. Note that also `int_005` is repeated in this list, but only patterns of exactly two strategies are probed in this example. The point of this check is to avoid circular behavior. 

The remaining five keys define the components of the simulation, including the object types (`objectTypes`), the slot types (`slotTypes`), the LCT-level moves available in principle (`handles`), the interactions among task objects at each iteration (`actions`), and specific task-related properties (`task`):
* _object types_ are specified by name and a list of "properties", referring to hypothetical properties an object of this type may possess;
* _slot types_ have a name, a list of object types a slot of this type can hold, a number of layers (int; essentially, this is the number of objects a slot of this type can hold simultaneously), a parameter that specifies whether the objects need to be ordered (1) or not (0) when placed on the slot of this type (if ordered, only the top-most of these objects is accessible), and two parameters (`gradientAsc` and `gradientDesc`) that determine any rule in how the objects need to be ordered (see below);
* _actions_ are intended as object-to-object iteractions to be carried out when an object is placed on a pin where another object is already located (not implemented in this version); 
* _handles_ are essentially the types of moves that can be executed at each iteration; here, they are defined in a general way, including name, type ("distance" or "proximity"; only the former is implemented currently), a parameter (`modulate`) that specifies whether a move of this type is focused on moving an object ("object") or moving a channel-type slot (e.g. "hand") from one slot to another (notably, in the latter case, the name of the specific channel is given, while in the former case, the term "object" is given), and two parameters (`initial` and `final`) that determine the type of the input and output slots (again, if an input or output slot is a channel, the name of that channel is given explicitly, otherwise the type of the slot is given);

Specific task-related properties are defined under the key `task`. This includes:
* the name of the task (`name`);
* all objects involved in the task (`objects`): for each of them, the name of the object, its object type, and values of any potential additional parameters specified with `properties` for that object type are given;
* all slots involved in the task (`slots`): for each of them, the name of the slot, its slot type, the list of objects it may hold by default, a score parameter by which the metric is computed (see above), any link to any `pos` slots this slot is located at by default, and a `bound` parameter that dictates to which `pos` slots this slot is constrained to (if only one, the slot cannot be moved; if two or more, the slot (i.e. a channel) can be moved along these positions; notably, the channel can move from any position to any position);
* the initial-state configuration (`initial`): for every pin, the objects that it holds in the initial state of the problem can be specified; if a pin does not hold any objects, it does not need to be given here;
* the final-state configuration (`final`): for every pin, the objects that it holds in the final state of the problem can be specified; if a pin does not hold any objects, it does not need to be given here;
* additional constraints can be given separately (`constraints`): these may overwrite any property defined in the lines above; the `name` parameter defines the name of the constraint, and then one gives the name of the slot affected by the constraint as key and one adds the parameter of that slot and its new value to this key; for example, the constraint "moveOneDisk" overwrites the parameter `numberOfLayers` of channel `hand`, which has been set to 3 before, to 1, such that the hand can only hold one object at a time.

The input JSON defines a variant of the Tower of Hanoi problem. Here, three disks serve as objects, and there are three pins from which the hand has to move one disk at a time. 
Note: It is convenient to only use exactly three types of slots: channels (by which the imaginary user interacts with the imaginary objects, e.g. the hand), pins (permanent pegs of the problem setup), and pos (imaginary positions on a potential imaginary trajectory of one's hand).

*Important: All names used in the input JSON file must be unique! For example, there may not be an object type and a slot type with the same name. Proper execution of the code depends on the uniqueness of item names specified in the input JSON!* 


### Simulation and Output

At minimum, the following 27 LCT-level moves are required to solve the Tower of Hanoi problem:
```
  - grab(disk1)-move(pin3)-place(disk1)            = move disk1 from pin1 to pin3
  - move(pin1)-grab(disk2)-move(pin2)-place(disk2) = move disk2 from pin1 to pin2
  - move(pin3)-grab(disk1)-move(pin2)-place(disk1) = move disk1 from pin3 to pin2
  - move(pin1)-grab(disk3)-move(pin3)-place(disk3) = move disk3 from pin1 to pin3
  - move(pin2)-grab(disk1)-move(pin1)-place(disk1) = move disk1 from pin2 to pin1
  - move(pin2)-grab(disk2)-move(pin3)-place(disk2) = move disk2 from pin2 to pin3
  - move(pin1)-grab(disk1)-move(pin3)-place(disk1) = move disk1 from pin1 to pin3
```
Organized in this way, this can be structured in 7 consecutive paths constructed at the INT.
