# -*- coding: utf-8 -*-
"""
Copyright 2015 Jean-Sebastien Gosselin

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

#===============================================================================
def decdeg2dms(dd):
    '''
    Convert decimal degree lat/lon coordinate to decimal, minute, second format.
    '''    
#===============================================================================
    
    mnt,sec = divmod(dd*3600, 60)
    deg,mnt = divmod(mnt, 60)
    
    return deg, mnt, sec

#===============================================================================   
def dms2decdeg(deg, mnt, sec):
    '''
    Convert decimal, minute, second format lat/lon coordinate to decimal degree.
    '''
#===============================================================================
    
    dd = deg + mnt/60. + sec/3600.    
    
    return dd

#===============================================================================
def search4meteo(LAT, LON, RADIUS):
    """
    Search on the Government of Canada website for weather stations with daily 
    meteo data around a decimal degree Lat, Lon coordinate with a radius 
    given in km.
    
    The results are returned in a list formatted ready to be read by WHAT UI.
    
    If no results are found, or there is an error with the search, only the list
    header is return with an empty list of station.
    """
#===============================================================================
    
    Nmax = 100
    
    StationID = ['stationId']
    Prov = ['Province']
    StartYear = ['StartYear']
    EndYear = ['EndYear']
    staName = ['staName']    
    
    #----------------------------------------------------------------- url -----
    
    url =  'http://climate.weather.gc.ca/advanceSearch/'
    url += 'searchHistoricDataStations_e.html?'
    url += 'searchType=stnProx&timeframe=1&txtRadius=%d' % RADIUS
    url += '&selCity=&selPark=&optProxType=custom'
       
    deg, mnt, sec = decdeg2dms(np.abs(LAT))
    url += '&txtCentralLatDeg=%d' % deg
    url += '&txtCentralLatMin=%d' % mnt
    url += '&txtCentralLatSec=%d' % sec
                                                                     
    deg, mnt, sec = decdeg2dms(np.abs(LON))
    url += '&txtCentralLongDeg=%d' % deg
    url += '&txtCentralLongMin=%d' % mnt
    url += '&txtCentralLongSec=%d' % sec

    url += '&optLimit=yearRange&StartYear=1840'
    url += '&EndYear=2014&Year=2013&Month=6&Day=4'
    url += '&selRowPerPage=%d&cmdProxSubmit=Search' % (Nmax)
    
    #-------------------------------------------------------------- Querry -----
    
    try:
        f = urlopen(url)
    
    #    # write downlwaded content to local file
    #    with open("url.txt", "wb") as local_file:
    #        local_file.write(f.read())
    #
    #    f = urlopen(url)
    
        #---------------------------------------------- Results Extraction -----
        
        stnresults = f.read()
        
        #----- Number of Stations Found -----
    
        txt2find = ' locations match your customized search.'
        indx_e =stnresults.find(txt2find, 0)
        if indx_e == -1:
            N = 0
            print 'No weather stations found.'
            
            cmt = '<font color=red>No weather stations found.</font>'
            
        else:        
            indx_0 = stnresults.find('<p>', indx_e-10)
            N = int(stnresults[indx_0+3:indx_e])
            print '%d weather stations found.' % N
            
            cmt = '<font color=red>%d weather stations found.</font>' % N
       
        for i in range(N):
        
            #----- StartDate and EndDate -----
            
            txt2find = '<input type="hidden" name="dlyRange" value="'
            n = len(txt2find)
            indx_0 = stnresults.find(txt2find, indx_e)
            indx_e = stnresults.find('|', indx_0)
            try:        
                StartYear.append(stnresults[indx_0+n:indx_0+n+4])
                EndYear.append(stnresults[indx_e+1:indx_e+1+4])
                
                #----- StationID -----
            
                txt2find = '<input type="hidden" name="StationID" value="'
                n = len(txt2find)
                indx_0 = stnresults.find(txt2find, indx_e)
                indx_e = stnresults.find('" />', indx_0)
                
                StationID.append(stnresults[indx_0+n:indx_e])
                
                #----- Province -----
            
                txt2find = '<input type="hidden" name="Prov" value="'
                n = len(txt2find)
                indx_0 = stnresults.find(txt2find, indx_e)
                indx_e = stnresults.find('" />', indx_0)
                
                Prov.append(stnresults[indx_0+n:indx_e])
                
                #----- Name -----
            
                txt2find = ('<div class="span-2 row-end row-start margin' +
                            '-bottom-none station wordWrap stnWidth">')
                n = len(txt2find)
                indx_0 = stnresults.find(txt2find, indx_e)
                indx_e = stnresults.find('\t', indx_0)
                
                staName.append(stnresults[indx_0+n:indx_e])
                               
            except:       
                pass
            
    except URLError as e:
        
        if hasattr(e, 'reason'):
            print('Failed to reach a server.')
            print('Reason: ', e.reason)
            print
            
            cmt = '<font color=red>Failed to reach a server.</font>'
            
        elif hasattr(e, 'code'):
            print('The server couldn\'t fulfill the request.')
            print('Error code: ', e.code)
            print
            
            cmt = '''<font color=red>
                       The server couldn\'t fulfill the request.
                     </font>'''

    #----------------------------------------------------- Arrange Results -----
    
    staList = [staName, StationID, StartYear, EndYear, Prov]
    staList = np.transpose(staList)
    
    return staList, cmt

if __name__ == '__main__':

    LAT = 45.4
    LON = -73.13
    RADIUS = 50
    
    staList, cmt = search4meteo(LAT, LON, RADIUS)
    
    print staList
    print cmt
    
    fname = 'weather_stations.lst'    
    with open(fname, 'wb') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(staList)
        
# ----- EXAMPLE url output (reformated from original) -----

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








