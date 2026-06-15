<p align="center">
  <img src="assets/logo.png" alt="NumStore Logo" width="200"/>
</p>

# Numstore Workbench

A Place for performance analysis and other sand boxed use cases

1.0 Quick Start
===============

Build the Code 
--------------

```
git submodule update --init --recursive
mkdir build 
cd build 
cmake ..
cmake --build .
```

Inner Inserts
-------------

Generate the csv file with all the data generated. 
```
python3 performance/inner_insert/scripts/run_trials.py
```

Generate plots from the data
```
python3 performance/inner_insert/scripts/visualize.py
```

Generate Flame Graphs 
```
./performance/inner_insert/scripts/gen_flamegraph.sh
```
