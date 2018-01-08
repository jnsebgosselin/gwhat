![Logo](https://github.com/jnsebgosselin/WHAT/blob/master/Images/WHAT_banner_lowres(150).png)
====
Copyright 2014-2018 © GWHAT Project Contributors.<br>
Licensed under the terms of the GNU-GPLv3

# Project details and build status

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](./LICENSE)
[![Documentation Status](https://readthedocs.org/projects/gwhat/badge/?version=latest)](http://gwhat.readthedocs.io)
[![Travis status](https://travis-ci.org/jnsebgosselin/gwhat.svg?branch=master)](https://travis-ci.org/jnsebgosselin/gwhat)
[![Coverage Status](https://coveralls.io/repos/github/jnsebgosselin/gwhat/badge.svg?branch=master&service=github#3)](https://coveralls.io/github/jnsebgosselin/gwhat?branch=master)
[![Build status](https://ci.appveyor.com/api/projects/status/7f2sr3ccd807ydjc/branch/master?svg=true)](https://ci.appveyor.com/project/jnsebgosselin/gwhat/branch/master)
[![codecov](https://codecov.io/gh/jnsebgosselin/gwhat/branch/master/graph/badge.svg)](https://codecov.io/gh/jnsebgosselin/gwhat)


You can read the GWHAT documentation [here](https://gwhat.readthedocs.io).<br>
You can download the latest version of GWHAT [here](https://github.com/jnsebgosselin/gwhat/releases/latest).<br>
Instructions for installing GWHAT are available [here](https://gwhat.readthedocs.io/en/latest/getting_started.html).<br>
The roadmap of the project can be consulted [here](https://github.com/jnsebgosselin/gwhat/milestones).

# About GWHAT

GWHAT (GroundWater Hydrograph Analysis Toolbox) is a free, open source, and cross-platform interactive computer program whose main focus is the interpretation of observation well hydrographs, including:
* the preparation of a gapless daily weather time-series (precipitation and air temperature) representative of the well location. For this purpose, an interface to the online [Canadian Daily Climate Database](http://climate.weather.gc.ca/) (CDCD) is provided that allows to query stations interactively by location coordinates, download the available data, and automatically rearranged the data in a format compatible with WHAT. Furthermore, missing data for a given station can be quickly filled with data from selected neighboring weather stations using a multiple linear regression model
* the generation of various publication-quality figures from the weather and water level data;

* the exploration, manipulation, and validation of the data within a user-friendly dynamic graphical environment;

* the calculation of the master recession curve (MRC) of the well hydrograph (experimental);

* the estimation of groundwater recharge at the local scale in unconfined conditions with a method combining the daily meteorological data and the water level time series (will be available in a future release).

* the calculation of the barometric response function of the well that can be used to assess the level of confinement of the aquifer at the well location (will be available in a future release).

GWHAT is written in the Python 3 programming language and is currently maintained and developed by [Jean-Sébastien Gosselin](http://www.liamg.ca/en/about-us/jean-sebastien-gosselin/) at [INRS-ETE](http://ete.inrs.ca/).

If you encounter any problems or errors during program execution, have any questions, or have specific suggestions on how to improve GWHAT, please contact Jean-Sébastien Gosselin at [jean-sebastien.gosselin@ete.inrs.ca](mailto:jean-sebastien.gosselin@ete.inrs.ca) or open an issue in our issues tracker [here](https://github.com/jnsebgosselin/gwhat/issues).

# Screenshots

<table>
  <tr>
    <td align="center" bgcolor=white><img width="300" src="https://github.com/jnsebgosselin/WHAT/blob/master/Images/WHAT_Screenshot000.png"></td>
    <td align="center"><img width="300" src="https://github.com/jnsebgosselin/WHAT/blob/master/Images/WHAT_Screenshot001.png"></td>
  </tr>
  <tr>
    <td align="center"><b>Conveniently download and format daily weather data of canadian stations</b></td>
    <td align="center"><b>Quickly estimate and fill missing weather data for all the stations in your study area</b></td>
  </tr>
    <td align="center"><br><br><img width="300" src="https://github.com/jnsebgosselin/WHAT/blob/master/Images/WHAT_Screenshot002.png"></td>
    <td align="center"><br><br><img width="300" src="https://github.com/jnsebgosselin/WHAT/blob/master/Images/WHAT_Screenshot003.png"></td>
  </tr>
  <tr>
    <td align="center"><b>Easily prepare publication-quality figures with your data</b></td>
    <td align="center"><b>Explore and analyse your data within a user-friendly dynamic graphical environment</b></td>
  </tr>
  <tr>
</table>

# Output Samples

![Weather yearly and monthly averages](https://github.com/jnsebgosselin/WHAT/blob/master/Images/weather_normals_sample.png)

![Well hydrograph and weekly weather data](https://github.com/jnsebgosselin/WHAT/blob/master/Images/hydrograph_PO07.png)

Last edited: 08/01/2018
