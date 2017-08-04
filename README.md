![Logo](https://github.com/jnsebgosselin/WHAT/blob/master/Images/WHAT_banner_lowres(150).png)
====
Copyright 2014-2017 © Jean-Sébastien Gosselin

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](./LICENSE)
[![Travis status](https://travis-ci.org/jnsebgosselin/WHAT.svg?branch=master)](https://travis-ci.org/jnsebgosselin/WHAT)
[![Coverage Status](https://coveralls.io/repos/github/jnsebgosselin/WHAT/badge.svg?branch=master)](https://coveralls.io/github/jnsebgosselin/WHAT?branch=master)

News (2015-07-27): A <b>user guide</b> is available for download [here](https://github.com/jnsebgosselin/WHAT/raw/master/User_Manual/WHATMANUAL.pdf). The guide only covers, for the time being, the creation of gapless daily weather datasets, including the downloading and formatting of weather data from the online Canadian Daily Climatic Database (CDCD).

# Table of Contents
- [What is WHAT](#what-is-what)
- [Installation](#installation)
- [Screenshots](#screenshots)
- [Output Samples](#output-samples)
- [License](#license)

# What is WHAT

WHAT (Well Hydrograph Analysis Toolbox) is a free, open source, and cross-platform interactive computer program whose main focus is the interpretation of observation well hydrographs, including:
* the preparation of a gapless daily weather time-series (precipitation and air temperature) representative of the well location. For this purpose, an interface to the online [Canadian Daily Climate Database](http://climate.weather.gc.ca/) (CDCD) is provided that allows to query stations interactively by location coordinates, download the available data, and automatically rearranged the data in a format compatible with WHAT. Furthermore, missing data for a given station can be quickly filled with data from selected neighboring weather stations using a multiple linear regression model
* the generation of various publication-quality figures from the weather and water level data;

* the exploration, manipulation, and validation of the data within a user-friendly dynamic graphical environment;

* the calculation of the master recession curve (MRC) of the well hydrograph (experimental);

* the estimation of groundwater recharge at the local scale in unconfined conditions with a method combining the daily meteorological data and the water level time series (will be available in a future release).

* the calculation of the barometric response function of the well that can be used to assess the level of confinement of the aquifer at the well location (will be available in a future release).

WHAT is written in the Python 3.4 programming language and is currently maintained and developed by [Jean-Sébastien Gosselin](http://www.liamg.ca/en/about-us/jean-sebastien-gosselin/) at [INRS-ETE](http://ete.inrs.ca/) under the direction and co-direction of [Richard Martel](http://www.inrs.ca/richard-martel) and [Christine Rivard](http://science.gc.ca/default.asp?lang=En&n=E3024D2D-1&xsl=sdmtprofile&xml=E3024D2D-1AB4-4F74-AF13-755D0DCF3E13&formid=B03536B8-8F8E-4BC1-A5BF-D62B13F57A8B&showfromadmin=1&readonly=true).

A user manual and the technical documentation of the software are currently being prepared and should be available shortly. To download a stand-alone executable of WHAT for Windows click on the button "releases" on top of this page or follow this [Link](https://github.com/jnsebgosselin/WHAT/releases). WHAT is currently under heavy development and is unfortunately not yet complete or free of bugs. If you encounter any problems or errors during program execution, have any questions, or have specific suggestions on how to improve WHAT, please contact Jean-Sébastien Gosselin at this email address: jnsebgosselin@gmail.com.

# Installation

The stand-alone executable for Windows 7 is distributed in a Zip archive that can be downloaded freely on GitHub [here](https://github.com/jnsebgosselin/WHAT/releases). This archive contains:

* the GNU General Public License;

* a folder named WHAT that contains all the necessary system files for the program to run, including the file WHAT.exe from which the software can be started;

* a folder named Projects where all input and output files used or created by WHAT are stored by default. In this folder are included samples of input and output files that provide a quick and convenient way to test and learn the various features of the program.

Once the content of the Zip archive has been extracted, the program can be started directly from the WHAT.exe executable file that is contained withing the folder named WHAT. The software can conveniently run from any location on the computer or from any storage device without the need to install the program beforehand.

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

# LICENSE

Copyright 2014-2017 Jean-Sébastien Gosselin. All Rights Reserved.

email: jean-sebastien.gosselin@ete.inrs.ca

WHAT is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
[GNU General Public License](http://www.gnu.org/licenses/) for more details.


Last edited: 04/02/2015
