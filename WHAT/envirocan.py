# -*- coding: utf-8 -*-
"""
Copyright 2014 Jean-Sebastien Gosselin

email: jnsebgosselin@gmail.com

This file is part of WHAT (Well Hydrograph Analysis Toolbox).

WHAT is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""

#----- STANDARD LIBRARY IMPORTS -----

import csv
from urllib2 import urlopen, URLError

#----- THIRD PARTY IMPORTS -----

import numpy as np

LAT = 45.4
LON = -73.13
Nmax = 25

def decdeg2dms(dd):
    mnt,sec = divmod(dd*3600, 60)
    deg,mnt = divmod(mnt, 60)
    
    return deg,mnt,sec
    
def dms2decdeg(deg, mnt, sec):
    dd = deg + mnt/60. + sec/3600.    
    
    return dd

url = ('http://climate.weather.gc.ca/advanceSearch/'+
       'searchHistoricDataStations_e.html?' +
       'searchType=stnProx&timeframe=1&txtRadius=25&selCity=&' +
       'selPark=&optProxType=custom&txt')
       
deg, mnt, sec = decdeg2dms(np.abs(LAT))
url += 'CentralLatDeg=%d' % deg
url += '&txtCentralLatMin=%d' % mnt
url += '&txtCentralLatSec=%d' % sec
                                                                     
deg, mnt, sec = decdeg2dms(np.abs(LON))
url += '&txtCentralLongDeg=%d' % deg
url += '&txtCentralLongMin=%d' % mnt
url += '&txtCentralLongSec=%d' % sec

url += '&optLimit=yearRange&StartYear=1840&EndYear=2014&Year=2013&Month=6&Day=4'
url += '&selRowPerPage=%d&cmdProxSubmit=Search' % (Nmax)

try:
    f = urlopen(url)

    # write downlwaded content to local file
#    with open("url.txt", "wb") as local_file:
#        local_file.write(f.read())
        
except URLError as e:
    
    if hasattr(e, 'reason'):
        print('Failed to reach a server.')
        print('Reason: ', e.reason)
        
    elif hasattr(e, 'code'):
        print('The server couldn\'t fulfill the request.')
        print('Error code: ', e.code)
        
stnresults = f.read()

txt2find = ' locations match your customized search.'
indx_e =stnresults.find(txt2find, 0)
indx_0 = stnresults.find('<p>', indx_e-10)

N = int(stnresults[indx_0+3:indx_e])
print N, 'weather stations found'

StationID = np.zeros(N)
Prov = np.zeros(N).astype(str)
StartYear = np.zeros(N)
EndYear = np.zeros(N)
staName = np.zeros(N).astype(str)

indx_e = 0
for i in range(N):
    
    #----- StartDate -----
    
    txt2find = '<input type="hidden" name="dlyRange" value="'
    n = len(txt2find)
    indx_0 = stnresults.find(txt2find, indx_e)
    indx_e = stnresults.find('|', indx_0)
    try:        
        StartYear[i] = stnresults[indx_0+n:indx_0+n+4]
        EndYear[i] = stnresults[indx_e+1:indx_e+1+4]
    except:       
        StartYear[i] = np.nan
        EndYear[i] = np.nan
        
#    indx_0 = stnresults.find(txt2find, indx_e)
#    indx_e = stnresults.find('|', indx_0)
    
#    EndDate[i] =
    
    #----- StationID -----
    
    txt2find = '<input type="hidden" name="StationID" value="'
    n = len(txt2find)
    indx_0 = stnresults.find(txt2find, indx_e)
    indx_e = stnresults.find('" />', indx_0)
    
    StationID[i] = stnresults[indx_0+n:indx_e]
    
    #----- Province -----
    
    txt2find = '<input type="hidden" name="Prov" value="'
    n = len(txt2find)
    indx_0 = stnresults.find(txt2find, indx_e)
    indx_e = stnresults.find('" />', indx_0)
    
    Prov[i] = stnresults[indx_0+n:indx_e]
   
    #----- Name -----
    
    txt2find = ('<div class="span-2 row-end row-start margin-bottom' +
                '-none station wordWrap stnWidth">')
    n = len(txt2find)
    indx_0 = stnresults.find(txt2find, indx_e)
    indx_e = stnresults.find('\t', indx_0)
    
    staName[i] = stnresults[indx_0+n:indx_e]

fcontent = [['staName', 'stationId', 'StartYear', 'EndYear', 'Province']]

indx = np.where(~np.isnan(StartYear))[0]
for i in indx:
    fcontent.append([staName[i], StationID[i], StartYear[i], EndYear[i],
                     Prov[i]])
                                          
fname = 'weather_stations.lst'    
with open(fname, 'wb') as f:
    writer = csv.writer(f, delimiter='\t')
    writer.writerows(fcontent)
                       
# ----- EXAMPLE -----

#</div></div><div class="clear"> </div><p>17 locations match your customized search.
#<div class="span-2 row-end row-start margin-bottom-none station stnWidth">Station</div>
#<div class="span-1 row-end row-start margin-bottom-none day_mth_yr">Province</div>
#<div class="span-1 row-end row-start margin-bottom-none day_mth_yr">Proximity (km)</div>
#<div class="span-1 row-end row-start margin-bottom-none intWidth">Data Interval</div>
#<div class="span-1 row-end row-start margin-bottom-none day_mth_yr">Year	</div>
#<div class="span-1 row-end row-start margin-bottom-none day_mth_yr">Month</div>
#<div class="span-1 row-end row-start margin-bottom-none day_mth_yr">Day</div>
#
#<input type="hidden" name="dlyRange" value="1960-06-01|2014-10-31" />
#<input type="hidden" name="mlyRange" value="1960-01-01|2014-10-01" />
#<input type="hidden" name="StationID" value="5406" />
#<input type="hidden" name="Prov" value="QC" />
#<input type="hidden" name="urlExtension" value="_e.html" />
#<input type="hidden" name="searchType" value="stnProx" />
#<input type="hidden" name="txtRadius" value="25" />
#<input type="hidden" name="optProxType" value="custom" />
#<input type="hidden" name="selCity" value="" />
#<input type="hidden" name="selPark" value="" />
#<input type="hidden" name="txtCentralLatDeg" value="45" />
#<input type="hidden" name="txtCentralLatMin" value="24" />
#<input type="hidden" name="txtCentralLatSec" value="0" />
#<input type="hidden" name="txtCentralLongDeg" value="73" />
#<input type="hidden" name="txtCentralLongMin" value="8" />
#<input type="hidden" name="txtCentralLongSec" value="0" />
#<input type="hidden" name="optLimit" value="yearRange" />
#<input type="hidden" name="StartYear" value="1840" />
#<input type="hidden" name="EndYear" value="2014" />
#<input type="hidden" name="selRowPerPage" value="25" />
#<input type="hidden" name="searchType" value="stnProx" />
#<input type="hidden" name="cmdProvSubmit" value="" />
#<input type="hidden" name="Line" value="0" />
#<div>		<div class="divTableRowOdd">
#
#<div class="span-2 row-end row-start margin-bottom-none station wordWrap stnWidth">MARIEVILLE</div>
#<div class="span-1 row-end row-start margin-bottom-none wordWrap day_mth_yr">QC</div>
#<div class="span-1 row-end row-start margin-bottom-none day_mth_yr wordWrap">0</div>
#<div class="span-1 row-end row-start margin-bottom-none wordWrap intWidth"><select name="timeframe" size="1"><option value="2" selected="selected">








