![Logo](https://github.com/jnsebgosselin/WHAT/blob/master/Images/WHAT_banner_lowres(150).png)
====
Copyright 2014-2020 © GWHAT Project Contributors.<br>
Licensed under the terms of the GNU-GPLv3

# Project details and build status

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](./LICENSE)
[![Latest release](https://img.shields.io/github/release/jnsebgosselin/gwhat.svg)](https://github.com/jnsebgosselin/gwhat/releases)
[![Build status](https://ci.appveyor.com/api/projects/status/7f2sr3ccd807ydjc/branch/master?svg=true)](https://ci.appveyor.com/project/jnsebgosselin/gwhat/branch/master)
[![codecov](https://codecov.io/gh/jnsebgosselin/gwhat/branch/master/graph/badge.svg)](https://codecov.io/gh/jnsebgosselin/gwhat)

# About GWHAT

GWHAT (Ground-Water Hydrograph Analysis Toolbox) is a free and open source
interactive computer program whose main objective is the interpretation of
observation well hydrographs to assess groundwater recharge with
a method combining a daily soil moisture balance and an aquifer
water budget applicable to unconfined aquifers.
The method is described in detail in the PhD thesis of Jean-Sébastien Gosselin
available [here](http://espace.inrs.ca/id/eprint/5122/).

In addition, GWHAT includes a tool to easily and quickly calculate the
barometric response function (BRF) of wells, provided that barometric and
earth tide data is available along with the water level data.
BRF calculations are performed with the
[KGS Barometric Response Function Software (KGS_BRF)](http://www.kgs.ku.edu/HighPlains/OHP/index_program/brf.html)
which implements the method described by
[Butler et al., 2010](https://ngwa.onlinelibrary.wiley.com/doi/10.1111/j.1745-6584.2010.00768.x).
The calculated BRFs can be used to determine the type of aquifer
(unconfined, semi-confined, or confined) in which the wells are installed
([Rasmussen and Crawford, 1997](https://ngwa.onlinelibrary.wiley.com/doi/10.1111/j.1745-6584.1997.tb00111.x),
[Spane, 2002](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2001wr000701))
and thus provide a reliable means to identify the wells under unconfined
conditions that can be used to assess groundwater recharge with the method
implemented in GWHAT.

GWHAT is written in the Python 3 programming language and is currently
maintained and developed by Jean-Sébastien Gosselin
at [INRS-ETE](http://ete.inrs.ca/). If you encounter any problems or errors
during program execution, have any questions, or have specific suggestions
on how to improve GWHAT, please open an issue
in our  [issues tracker](https://github.com/jnsebgosselin/gwhat/issues).

Last edited: 18/19/2020
