# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

import numpy
from numpy.distutils.core import setup, Extension
from Cython.Build import cythonize
from gwhat import __version__, __project_url__


RECHGEXT = Extension(
    name='gwhat.gwrecharge.gwrecharge_calculs',
    sources=['gwhat/gwrecharge/gwrecharge_calculs.pyx'],
    include_dirs=[numpy.get_include()],
    extra_link_args=["-static", "-static-libgcc"]
    )

setup(name='GWHAT',
      version=__version__,
      license='GPLv3',
      author='GWHAT Project Contributors',
      author_email='jean-sebastien.gosselin@ete.inrs.ca',
      url=__project_url__,
      ext_modules=cythonize(RECHGEXT),
      )
