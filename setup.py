# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

import csv
import setuptools
import numpy
from numpy.distutils.core import setup, Extension
from Cython.Build import cythonize

from gwhat import __version__, __project_url__

with open('requirements.txt', 'r') as csvfile:
    INSTALL_REQUIRES = list(csv.reader(csvfile))
INSTALL_REQUIRES = [item for sublist in INSTALL_REQUIRES for item in sublist]

with open('requirements-dev.txt', 'r') as csvfile:
    DEV_INSTALL_REQUIRES = list(csv.reader(csvfile))
DEV_INSTALL_REQUIRES = [
    item for sublist in DEV_INSTALL_REQUIRES for item in sublist]

EXTRAS_REQUIRE = {'dev': DEV_INSTALL_REQUIRES}

PACKAGE_DATA = {
    'gwhat': ['ressources/icons_png/*.png',
              'ressources/icons_scalable/*.svg',
              'ressources/WHAT_banner_750px.png',
              'ressources/splash.png',
              'gwrecharge/*.pyd']
    }

RECHGEXT = Extension(
    name='gwhat.gwrecharge.gwrecharge_calculs',
    sources=['gwhat/gwrecharge/gwrecharge_calculs.pyx'],
    include_dirs=[numpy.get_include()]
    )

setup(name='gwhat',
      version=__version__,
      license='GPLv3',
      author='GWHAT Project Contributors',
      author_email='jean-sebastien.gosselin@outlook.com',
      url=__project_url__,
      ext_modules=cythonize(RECHGEXT),
      packages=setuptools.find_packages(),
      package_data=PACKAGE_DATA,
      include_package_data=True,
      install_requires=INSTALL_REQUIRES,
      extras_require=EXTRAS_REQUIRE,
      )
