pyUTK
=====

pyUTK is a python interface around the [UTK library](https://utk-team.github.io/utk/). It exposes basic samplers and discrepancies that are available through executables once UTK is built. 

This mini-library is not a real binding as it only uses executables files generated when compiling UTK. This project makes heavy use of IO operation that slows down samplers. 

Building 
--------

The library must be built by the user with one of the two commands : 

```python
# 1st option
python setup.py install
# 2cd option
python setup.py install --utk path_to_utk/build/src
```

The first version is a basic installation of the library. Each time the library is used the 
path to UTK must be set via `pyutk.set_dir(path_to_utk)`.
The second will bind the library to the path provided and it won't be necessary
to provide the path each time. 

The path must point to the directory enclosing the binaries. If the step described [here](https://utk-team.github.io/utk/) have been followed with no addition, the path should end with "build/src". 

Usage
-----

Here are two scripts that shows most common usage of the library : 

```python
import pyutk

# If built with option 1
# pyutk.set_dir("path_to_utk")

print(pyutk.get_samplers()) # List available samplers, maps name to dimensions

s = pyutk.Sampler("Whitenoise", d=2) # 2-D Whitenoise sampler
d = pyutk.Discrepancy("StarDiscrepancy", d=2)
samples = s.sample(n=123) # Ask for 123 points
print(d.compute(samples)) # Compute star discrepancy
```

```python
import pyutk
import numpy as np
# Reader and writer does not requires utk path to be set
samples = np.random.uniform(0, 1, (123, 2)) # 2-d Whitenoise

# Context manager is supported (only for now) for writting
# Writting can also be done by calling at first .open(path)
# then .write(points) and by closing the file (.close())
with pyutk.PointWriter("out.dat") as writer:
    writer.write(samples)

reader = pyutk.PointReader(samples.shape[0], samples.shape[1]) # Specify number of coordinates to read
print(np.all(samples == reader.read("out.dat")))
```

