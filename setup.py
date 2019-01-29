# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

import numpy
from numpy.distutils.core import setup, Extension
from Cython.Build import cythonize


setup(ext_modules=cythonize("gwhat/gwrecharge/gwrecharge_calculs.pyx"),
      include_dirs=[numpy.get_include()])
