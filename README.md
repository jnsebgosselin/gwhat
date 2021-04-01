![Logo](https://github.com/jnsebgosselin/WHAT/blob/master/Images/WHAT_banner_lowres(150).png)
====
Copyright 2014-2021 © GWHAT Project Contributors.<br>
Licensed under the terms of the GNU-GPLv3

# Project details and build status

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](./LICENSE)
[![Latest release](https://img.shields.io/github/release/jnsebgosselin/gwhat.svg)](https://github.com/jnsebgosselin/gwhat/releases)
[![Build status](https://ci.appveyor.com/api/projects/status/7f2sr3ccd807ydjc/branch/master?svg=true)](https://ci.appveyor.com/project/jnsebgosselin/gwhat/branch/master)
[![codecov](https://codecov.io/gh/jnsebgosselin/gwhat/branch/master/graph/badge.svg)](https://codecov.io/gh/jnsebgosselin/gwhat)

# About GWHAT

GWHAT (Ground-Water Hydrograph Analysis Toolbox) is a free and open source
application whose main objective is to support the interpretation of
water levels measured in observation wells (hydrographs) to estimate
groundwater recharge with a method combining a daily soil moisture balance
and an aquifer water budget applicable to unconfined aquifers.
The method is described in detail in the PhD thesis of Jean-Sébastien Gosselin
available [here](http://espace.inrs.ca/id/eprint/5122/). Application of the
recharge assessment method requires a well hydrograph and weather data
measured daily. A long-duration hydrograph (more than 5 years) provides
more constraints on recharge assessment. Recharge is assessed for the
period for which weather data are available and it is not limited to
the period of available water levels. Results are produced in tabular
and graphical formats.

Furthermore, GWHAT includes a tool to easily calculate the barometric
response function (BRF) of wells, provided that barometric and
earth tide data are available along with the water level data.
BRF calculations are performed with the
[KGS Barometric Response Function Software (KGS_BRF)](http://www.kgs.ku.edu/HighPlains/OHP/index_program/brf.html),
which implements the method described by
[Butler et al. (2010)](https://ngwa.onlinelibrary.wiley.com/doi/10.1111/j.1745-6584.2010.00768.x).
The calculated BRF can be used to determine the type of aquifer
(unconfined, semi-confined, or confined) in which wells are installed
([Rasmussen and Crawford, 1997](https://ngwa.onlinelibrary.wiley.com/doi/10.1111/j.1745-6584.1997.tb00111.x),
[Spane, 2002](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2001wr000701))
and thus provides a reliable way to identify wells that are under unconfined
conditions and which can be used to assess groundwater recharge with the
method implemented in GWHAT.

GWHAT is written in the Python 3 programming language and is currently
maintained and developed by Jean-Sébastien Gosselin at
[INRS-ETE](http://ete.inrs.ca/). If you encounter any problems or
errors during program execution, have any questions, or have specific
suggestions on how to improve GWHAT, please open an issue in our
[issues tracker](https://github.com/jnsebgosselin/gwhat/issues).

Last edited: 01/04/2021
