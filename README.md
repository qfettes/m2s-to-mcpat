# Convert Multi2Sim results into McPAT configuration
## The problem
Multi2Sim (sometimes referred as m2s) has been adapted to provide some of the statistics that McPAT requires in its input file. The correspondence between the multi2sim statistics and mcpat input parameters is given in Appendix II of the Multi2Sim (v4.2) manual. However, Multi2Sim does not provide any tool to generate the McPAT input file automatically, which means that for every simulation we ought to manually copy the values from the m2s result file to the mcpat input configuration file; **this process should be automatized**.

## The solution
### Step 1
When we run a simulation on m2s we can indicate to save the output results into different files, i.e. processor, memory and network. Each of these contains different sections (usually one per component simulated, plus some global statistics), and every section contains multiple pairs of parameters/values. Example (from a processor output):

    [ Global ]
    Cycles = 251285895
    Time = 18604.76
    CyclesPerSecond = 13507
    MemoryUsed = 45395968
    ...
    Dispatch.Total = 5572371475
    ...

    [ Config.BranchPredictor ]
    Kind = TwoLevel
    BTB.Sets = 256
    BTB.Assoc = 4
    ...

    [ ... ]
    ...

In our script, the first thing we do is parse all the m2s results files provided, and separate them into sections. Additionally, every section is also separated into the multiple pairs of parameters/values. This structure is saved using a dictionary inside another dictionary, and the process is defined in the function `parser()` of the code.

### Step 2
mcpat requires an XML configuration file to run a simulation, which looks like this:

    <component id="system.core0" name="core0">
    	<param name="clock_rate" value="1000"/>
    	...
    	<stat name="total_instructions" value="400000"/>
    	<stat name="int_instructions" value="200000"/>
    	...
    <component id="system.core0.icache" name="icache">
    	...
    	<stat name="read_accesses" value="200000"/>
    	<stat name="read_misses" value="100000"/>
    	...
    <component id="system.core0.dcache" name="dcache">
    	...
    	<stat name="read_accesses" value="200000"/>
    	<stat name="read_misses" value="1000000"/>
    	...

As we explained before, the problem is that changing the value of every `stat` in the file at every execution of m2s is arduous.
So, in our second step, and now that all the values that we are trying to export from m2s into mcpat are saved and organized into memory, we have to fill the mcpat configuration template with them.
To do that, we check every line of the mcpat template file, and if it contains a `stat` we look for its correspondence parameter name into a translation table called `corresp_mcpat_to_m2s` (previously defined by the user in the code). If there is a match, we search the translated parameter name in the dictionary created during the parsing process (Step 1), we save the value into a temporal variable, and we use it to write the line into the output mcpat configuration file, using the same format as in the template; which is:

    <stat name="corresponding name from m2s" value="value from m2s"/>
The rest of the lines from the template (the ones not containing a `stat`), are copied verbatim from the template to the output file.

### Usage
(if argument files are in different folder than current working directory, make sure to specify the path to each of them)

	shell> python m2s-to-mcpat.py <mcpatTemplateFile.xml> ...
			<mcpatOutputFile.xml> <m2sInputFile1> [<m2sInputFile2> ...
			<m2sInputFileN>]

The script `m2s-to-mcpat.py` takes at least 3 arguments when executed:

 - `mcpatTemplateFile.xml` is the actual configuration template that we are planning to use as input to mcpat. This file must contain all the components, parameters and stats that we plan to simulate on mcpat. *This file will not be modified by this script.*
 - `mcpatOutputFile.xml` will be the resulting configuration file after the template is filled with all the values from the multi2sim results file. ***This is the file that we can later use to run mcpat.***
 - `m2sInputFileN` contains the different sections and parameter values that multi2sim provides at the end of each simulation. *If multiple files are provided, they will all be treated as a single file, so **make sure that there are no duplicated sections between them.***

### Example
(assuming all argument files are within the same folder, which is the current working directory)

	shell> python m2s-to-mcpat.py mcpat_xeon_template.xml ...
			mcpat_xeon_raytrace.xml m2s_raytrace_results_proc.txt ...
			m2s_raytrace_results_mem.txt
This example shows a possible case where we might have run the Raytrace benchmark on multi2sim, and saved the results of the processor and memory components into `m2s_raytrace_results_proc.txt` and `m2s_raytrace_results_mem.txt`; which could look something like this,

`m2s_raytrace_results_proc.txt`:

    [ Global ] <--- Information relative to all cores
    Cycles = 251285895 <--- we want this parameter
    Time = 18604.76
    CyclesPerSecond = 13507
    ...

    [ c0 ] <--- Information relative to the first core
    ...
    Dispatch.Total = 5572371475 <--- we want this parameter
    ...

    [ ... ]
    ...

`m2s_raytrace_results_mem.txt`:

    [ il1-0 ] <--- L1 instruction cache
    Sets = 256
	Assoc = 2
	...
	Reads = 3016215 <--- we want this parameter
	...

	[ l1-0 ] <--- L1 data cache
    Sets = 256
	Assoc = 2
	...
	Reads = 3897354 <--- we want this parameter
	...
Notice that in each file, some of the sections contain the parameters that we want to convert to mcpat. Specifically, in this case we want the parameter `Cycles` from the `Global` section, the `Dispatch.Total` from `c0`, and the L1 instruction and data `Reads` from `il1-0` and `l1-0` respectively.
The value of these parameters will fill their corresponding `stat`, on a mcpat template that might look like this,

`mcpat_xeon_template.xml`:

    <component id="system" name="system">
    	<param name="number_of_cores" value="4"/>
    	<param name="temperature" value="380"/>
    	...
    	<stat name="total_cycles" value=""/> <--- we want to fill this stat
    	...
    <component id="system.core0" name="core0">
    	...
    	<stat name="total_instructions" value=""/> <--- we want to fill this stat
    	...
    <component id="system.core0.icache" name="icache">
    	...
    	<stat name="read_accesses" value=""/> <--- we want to fill this stat
    	...
    <component id="system.core0.dcache" name="dcache">
    	...
    	<stat name="read_accesses" value=""/> <--- we want to fill this stat
    	...

### Implementation details
talk about the dictionary inside a dictionary, the global variables, etc.


> Written with [StackEdit](https://stackedit.io/).
