# Automate EPANET simulations
This project helps you generate large amounts of EPANET data.

## A note on OS
This has only been tested on mac. If you use windows I wish you the best of luck with all your EPANET-related ventures but I can't help you. If you use linux you don't need my help.

## What you need to run this
Before doing any of the below you need to make sure you have a C compiler like llvm/clang or gcc, cmake, swig and scikit-build.
These can all be installed via tools like brew or pip.

Get the OWA-EPANET module by pasting the below into your terminal
```
$ git clone https://github.com/OpenWaterAnalytics/epanet-python.git
$ cd epanet-python
$ git submodule update --init
```

Then build according to the instructions in the OWA-EPANET readme: https://github.com/OpenWaterAnalytics/epanet-python/tree/dev/owa-epanet#readme

## Running simulations

You can run this code via one of two scripts. `length_transect_modellers.py` lets you run simulations along the transect of a pipe for a series of sizes. `multiple_leaks_modeller.py` lets you run simulations for a set number of leaks  instead. For either of these scripts you can use a number of input arguments:

| name            | data type | default value | description                                 | used in script               |
|-----------------|-----------|---------------|---------------------------------------------|------------------------------|
| input_filename  | string    | net1.inp      | An EPANET input file describing the system. | both                         |
| report_filename | string    |               | Report log file from the simulation run.    | both                         |
| binary_filename | string    |               | Hydraulic analysis results file (binary).   | both                         |
| --hstep         | int       | 3600          | Hydraulic time step (3600s=1h).             | both                         |
| --pipe          | int       | 2             | Index of pipe to look at.                   | both                         |
| --iter          | int       | 1             | Number of leak size iterations.             | length_transect_modellers.py |
| --lstep         | int       | 1             | Distance between leaks.                     | multiple_leaks_modeller.py   |
| --nleaks        | int       | 2             | Number of leaks.                            | multiple_leaks_modeller.py   |

Both scripts can be run without input arguments, or with all arguments. A run could look something like the following:

```
python3 length_transect_modeller.py examplenet.inp report.txt binary.bin --hstep 7200 --pipe 3 --iter 5
```
```
python3 multiple_leaks_modeller.py otherexamplenet.inp report.txt binary.bin --hstep 1800 --pipe 1 --lstep 5 --nleaks 3
```

or just:

```
python3 length_transect_modeller.py
```

Good luck!


