#!/usr/bin/env python
 
from distutils.core import setup, Extension


pylibroot = "/usr/local/lib/python2.7/dist-packages"

sim = Extension("sim",
                 language="c++",
                 include_dirs=[pylibroot + "/numpy/core/include",],
                 sources=["similarity.cpp",],
                 extra_compile_args=["-std=c++11",])

setup(name="Similarity",
      version="1.0",
      description="Collaborative Filtering",
      author="wxn",
      ext_modules=[sim,])

