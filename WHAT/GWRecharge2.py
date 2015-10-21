# -*- coding: utf-8 -*-
"""
Copyright 2014-2015 Jean-Sebastien Gosselin
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
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

#----- STANDARD LIBRARY IMPORTS -----
      
#from datetime import date
#import csv

#----- THIRD PARTY IMPORTS -----

import numpy as np
#from xlrd import xldate_as_tuple
#from xlrd.xldate import xldate_from_date_tuple
import matplotlib.pyplot as plt

#----- PERSONAL LIBRARY IMPORTS -----

from meteo import MeteoObj
from waterlvldata import WaterlvlData

#==============================================================================

class SynthHydrograph(object):                              # SynthHydrograph #
    
#==============================================================================
    
    def __init__(self, fmeteo, fwaterlvl, CRU, Sy=0.25):
    
        #---- Load Data ----
    
        print('--------')
        self.meteoObj = MeteoObj()
        self.meteoObj.load_and_format(fmeteo) # Includes the estimation of ETP
                                              # if not already present in file.
        print('--------')
        self.waterlvlObj = WaterlvlData()
        self.waterlvlObj.load(fwaterlvl)
        print('--------')
        
        #---- Make the water level time series continuous ----
        
        ts, te = self.waterlvlObj.time[0], self.waterlvlObj.time[-1]
        self.twlvl = np.arange(ts, te+1)
        self.WLVLobs = np.interp(self.twlvl, self.waterlvlObj.time,
                                 self.waterlvlObj.lvl)
        

        #---- Plotting the Results ----
        
        import datetime
        
        tweatr = self.meteoObj.TIME
        
        ts = np.where(self.twlvl[0] == tweatr)[0][0]
        te = np.where(self.twlvl[-1] == tweatr)[0][0] 
        
        YEAR = self.meteoObj.DATA[ts:te+1,0]
        MONTH = self.meteoObj.DATA[ts:te+1,1]
        DAY = self.meteoObj.DATA[ts:te+1,2]
        
        DATE = [0] * len(self.twlvl)
        for t in range(len(self.twlvl)):
            DATE[t] = datetime.datetime(int(YEAR[t]), int(MONTH[t]),
                                        int(DAY[t]), 0)
        
        #---- prepare figure and plot obs. ----
        
        fig = plt.figure(figsize=(11, 6))
        ax = fig.add_axes([0.08, 0.1, 0.75, 0.8])
        fig.suptitle('Synthetic hydrographs with Sy = %0.2f' % Sy, fontsize=20)
        
        ax.plot(DATE, self.WLVLobs, '0.65', lw=1.5)
        
        #---- Multiple Fit ----
        
        CRU = np.array([0.2, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55])
        RASMAX = [0] * len(CRU)
        WLVLPRE = [0] * len(CRU)
        RECHG = [0] * len(CRU)
        for i in range(len(CRU)):
            RASMAX[i], WLVLPRE[i], RECHG[i] = self.opt_RASmax(Sy, CRU[i])
        
        for i in range(len(CRU)):
            RMSE = np.mean((WLVLPRE[i] - self.WLVLobs*1000)**2)**0.5
            NSE = self.nash_sutcliffe(self.WLVLobs*1000, WLVLPRE[i])
            rechg = np.mean(RECHG[i]) * 365
            
            label = ('Cru = %0.2f\nRASmax = %0.0f\n' + 
                     'RMSE = % 0.0f mm\nNSE = %0.2f\n' +
                     'Rechg = %0.0f mm/y'
                     ) % (CRU[i], RASMAX[i], RMSE, NSE, rechg)
            ax.plot(DATE, WLVLPRE[i]/1000., alpha=0.65, lw=1.5, label=label)
        
        #---- Best Fit ----
        
#        Cru, RASmax, WLVLPRE, RECHG = self.opt_CruRASmax(Sy)
#        
#        RMSE = np.mean((WLVLPRE - self.WLVLobs*1000)**2)**0.5
#        NSE = self.nash_sutcliffe(self.WLVLobs*1000, WLVLPRE)
#        rechg = np.mean(RECHG) * 365
#        
#        label = ('Cru = %0.2f\nRASmax = %0.0f\n' + 
#                 'RMSE = % 0.0f mm\nNSE = %0.2f\n' +
#                 'Rechg = %0.0f mm/y'
#                 ) % (Cru, RASmax, RMSE, NSE, rechg)
#                 
#        ax.plot(DATE, WLVLPRE/1000., alpha=0.65, lw=1.5, label=label)
        
        #--------           
        
        ax.set_ylabel('Water Level (mbgs)', fontsize=16) 
        ax.grid(axis='x', color=[0.65, 0.65, 0.65], ls=':', lw=1)
        ax.set_axisbelow(True)
        
        ax.legend(loc=[1.01, 0], ncol=1, fontsize=8)
        ax.invert_yaxis()
        
#        fname = '%0.2f.pdf' % Sy
#        fig.savefig(fname)
        
#    def plot_synth_hydrograph(0):
#        pass
    
    @staticmethod
    def nash_sutcliffe(Xobs, Xpre):
        # Source: Wikipedia
        # https://en.wikipedia.org/wiki/
        # Nash%E2%80%93Sutcliffe_model_efficiency_coefficient
        
        NSE = 1 - np.sum((Xobs - Xpre)**2) / np.sum((Xobs - np.mean(Xobs))**2)
        return NSE        
        
    def opt_CruRASmax(self, Sy): #========================== Optimize RASmax ==
        
        Cru = 0.
        RMSEnew = 10**6 # force divergence
        dCru = 0.1
        while abs(dCru) >= 0.01:
            while 1:
                RMSEold = np.copy(RMSEnew)
                
                Cru += dCru
                RASMAX, WLVLpre, RECHG = self.opt_RASmax(Sy, Cru)
                
                RMSEnew = (np.mean((self.WLVLobs * 1000 - WLVLpre)**2))**0.5
                
                if RMSEnew > RMSEold:
                    dCru /= -10.
                    break
                
        return Cru, RASMAX, WLVLpre, RECHG
                
    def opt_RASmax(self, Sy, CRU): #======================== Optimize RASmax ==
        
        #---- weather observations ----
        
        ETP = self.meteoObj.DATA[:, 7]
        PTOT = self.meteoObj.DATA[:, 6]
        TAVG = self.meteoObj.DATA[:, 5]
        tweatr = self.meteoObj.TIME + 10
        
        #---- water lvl observations ----
        
        twlvl = self.twlvl
        WLVLobs = self.WLVLobs * 1000
        
        ts = np.where(twlvl[0] == tweatr)[0][0]
        te = np.where(twlvl[-1] == tweatr)[0][0]        
        
        #---- MRC ----
        
        A, B = self.waterlvlObj.A, self.waterlvlObj.B

        #---- Gauss-Newton ----
        
        tolmax = 0.1       
        RASMAX = 100.
        
        RECHGpre = self.surf_water_budget(CRU, RASMAX, ETP, PTOT, TAVG)
        WLVLpre = self.calc_hydrograph(RECHGpre[ts:te], A, B, WLVLobs[0],
                                       Sy, nscheme='forward')
        RMSE = (np.mean((WLVLobs - WLVLpre)**2))**0.5
#        print('RASmax = %0.1f mm ; RMSE = %0.2f mm' % (RASMAX, RMSE))
        
        it = 0
        while 1:
            
            it += 1
            if it > 50:
                print('Not converging.')
                break                
            
            #---- Calculating Jacobian (X) Numerically ---- 
            
            rechg = self.surf_water_budget(CRU, RASMAX + tolmax, ETP,
                                           PTOT, TAVG) 
                                           
            wlvl = self.calc_hydrograph(rechg[ts:te], A, B, WLVLobs[0],
                                        Sy, nscheme='forward')
            X = Xt = (wlvl - WLVLpre) / tolmax            

            if np.sum(X) == 0:
                rechg_yearly = np.mean(RECHGpre) * 365
                RASMAX = np.inf
#                print('!Uppermost limit of RASmax!') 
                print('Cru = %0.2f ; RASmax = %0.0f mm ; ' +
                      'RMSE = %0.1f mm ; Rechg = %0.0f mm' 
                      ) % (CRU, RASMAX, RMSE, rechg_yearly)              
                return RASMAX, WLVLpre, RECHGpre
            
            #---- Solving Linear System ----
            
            dh = WLVLobs - WLVLpre
            XtX = np.dot(Xt, X)                
            Xtdh = np.dot(Xt, dh)
            
            dr = np.linalg.tensorsolve(XtX, Xtdh, axes=None)
            
            #---- Storing old parameter values ----
            
            RASMAXold = np.copy(RASMAX)
            RMSEold = np.copy(RMSE)

            while 1: # Loop for Damping (to prevent overshoot)
                
                #---- Calculating new paramter values ----

                RASMAX = RASMAXold + dr
                    
                #---- Applying parameter bound-constraints ----
                
                if RASMAX < 0:
                    RASMAX = 0
                    rechg_yearly = np.mean(RECHGpre) * 365
#                    print('!Lowermost limit of RASmax!')
                    print('Cru = %0.2f ; RASmax = %0.0f mm ; ' +
                          'RMSE = %0.1f mm ; Rechg = %0.0f mm' 
                          ) % (CRU, RASMAX, RMSE, rechg_yearly)
                          
                    return RASMAX, WLVLpre, RECHGpre
                    
                #---- Solving for new parameter values ----
                
                RECHGpre = self.surf_water_budget(CRU, RASMAX, ETP, PTOT, TAVG)
                WLVLpre = self.calc_hydrograph(RECHGpre[ts:te], A, B,
                                               WLVLobs[0], Sy,
                                               nscheme='forward')
                RMSE = (np.mean((WLVLobs - WLVLpre)**2))**0.5
                
                #---- Checking overshoot ----
                
                if (RMSE - RMSEold) > 0.001:
                    dr = dr * 0.5
                else:
                    break
    
            #---- Checking tolerance ----
        
            tol = np.abs(RASMAX - RASMAXold)            
            
            if tol < tolmax:
#                out = np.correlate(WLVLobs, WLVLpre[:-100])
#                plt.plot(out)
                rechg_yearly = np.mean(RECHGpre) * 365
                print('Cru = %0.2f ; RASmax = %0.0f mm ; ' +
                      'RMSE = %0.1f mm ; Rechg = %0.0f mm' 
                      ) % (CRU, RASMAX, RMSE, rechg_yearly)
                return RASMAX, WLVLpre, RECHGpre
                            
        
    @staticmethod
    def surf_water_budget(CRU, RASmax, ETP, PTOT,   #===== Surf Water Budget ==
                          TAVG, TMELT=1.5, CM=4 ):
                          
    
        """    
        Input
        -----
        {float} CRU = Runoff coefficient
        {float} RASmax = Readily Available Storage Max in mm
        {1D array} ETP = Dailty evapotranspiration in mm
        {1D array} PTOT = Daily total precipitation in mm
        {1D array} TAVG = Daily average air temperature in deg. C.
        
        CM: Daily melt coefficient
        TMELT: Temperature treshold for snowmelt
        
        Output
        ------
        {1D array} RECHG = Daily groundwater recharge in mm    
        """
        
        N = len(ETP)    
        PAVL = np.zeros(N)   # Available Precipitation
        PACC = np.zeros(N)   # Accumulated Precipitation
        RU = np.zeros(N)     # Runoff
        I = np.zeros(N)      # Infiltration
        ETR = np.zeros(N)    # Evapotranspiration Real
        dRAS = np.zeros(N)   # Variation of RAW
        RAS = np.zeros(N)    # Readily Available Storage
        RECHG = np.zeros(N)  # Recharge (mm)
                
        MP = CM * (TAVG - TMELT)  # Snow Melt Potential
        MP[MP < 0] = 0
        
        PACC[0] = 0
        RAS[0] = RASmax
        
        for i in range(0, N - 1):
    
            #----- Precipitation -----          
    
            if TAVG[i] > TMELT:  # Rain
            
                if MP[i] >= PACC[i]: # Rain on Bareground
                    PAVL[i+1] = PACC[i] + PTOT[i]
                    PACC[i+1] = 0
                    
                elif MP[i] < PACC[i]: #Rain on Snow
                    PAVL[i+1] = MP[i]
                    PACC[i+1] = PACC[i] - MP[i] + PTOT[i]                
                    
            elif TAVG[i] <= TMELT: #Snow
                PAVL[i+1] = 0
                PACC[i+1] = PACC[i] + PTOT[i]
                
            #----- Infiltration and Runoff -----
            
            RU[i] = CRU * PAVL[i]
            I[i] = PAVL[i] - RU[i]
            
            #----- ETR, Recharge and Storage change -----
            
            dRAS[i] = min(I[i], RASmax - RAS[i])
            RAS[i+1] = RAS[i] + dRAS[i] #intermediate step
            RECHG[i] = I[i] - dRAS[i]
            
            ETR[i] = min(ETP[i], RAS[i])
            
            RAS[i+1] = RAS[i+1] - ETR[i]
        
        return RECHG
    
    
    @staticmethod
    def calc_hydrograph(RECHG, A, B, WL0, Sy, nscheme='forward'): #============        
        """
        This is a forward numerical explicit scheme for generating the
        synthetic well hydrograph.
        
        This is a backward explicit scheme to produce a synthetic well
        hydrograph. The water level starts at the last days in the observed
        water level time series and generate the hydrograph by going backward
        in time. This is very usefull when one which to produce water level
        for the period of time before water level measurements are
        available.
        
        Parameters
        ----------
        Wlpre: Predicted Water Level (mm)
        Sy: Specific Yield
        RECHG: Groundwater Recharge (mm)
        
        A, B: MRC Parameters, where: Recess(m/d) = -A * h + B
        nscheme: Option are "forward" or "downdward" depending if the 
                 hydrograph is being built forward in time or backward. 
                 Default is "forward".
        """
        
        # It should also be possible to do a Crank-Nicholson on this. I should
        # check this out.
        
        WLpre = np.zeros(len(RECHG)+1) * np.nan
        WLpre[0] = WL0
        
        if nscheme == 'backward':
            for i in reversed(range(len(RECHG))):
                RECESS = (B - A * WLpre[i] / 1000.) * 1000
                RECESS = max(RECESS, 0)
                
                WLpre[i] = WLpre[i+1] + (RECHG[i] / Sy) - RECESS
            
        elif nscheme == 'forward':
            for i in range(len(RECHG)):
                RECESS = (B - A * WLpre[i] / 1000.) * 1000
                RECESS = max(RECESS, 0)
                            
                WLpre[i+1] = WLpre[i] - (RECHG[i] / Sy) + RECESS
        else:
            WLpre = []
            
        return WLpre
        
    
    @staticmethod
    def mrc2rechg(t, hobs, A, B, z, Sy): #=====================================
 
        """
        Calculate groundwater recharge from the Master Recession Curve (MRC)
        equation defined by the parameters A and B, the water level time series
        in mbgs (t and ho) and the soil column description (z and Sy), using
        the water-level fluctuation principle.
           
        INPUTS
        ------
        {1D array} t : Time in days 
        {1D array} hobs = Observed water level in mbgs
        {float}    A = Model parameter of the MRC
        {float}    B = Model parameter of the MRC
        {1D array} z = Depth of the soil layer limits
        {1D array} Sy = Specific yield for each soil layer
        {1D array} indx = Time index defining the periods over which recharge
                          is to be computed. Odd index numbers are for the
                          beginning of periods while even index numbers are for
                          the end of periods.
                             
        OUTPUTS
        -------       
        {1D array} RECHG = Groundwater recharge time series in m
    
        Note: This is documented in logbook #11, p.23.
        """
        
        #---- Check Data Integrity ----
        
        if np.min(hobs) < 0:
            print('Water level rise above ground surface. Please check your data.')
            return
    
        dz = np.diff(z) # Tickness of soil layer
        
        dt = np.diff(t)
        RECHG = np.zeros(len(dt))
        
        # !Do not forget it is mbgs. Everything is upside down!

        for i in range(len(dt)):
            
            # Calculate projected water level at i+1
            
            LUMP1 = 1 - A * dt[i] / 2
            LUMP2 = B * dt[i]
            LUMP3 = (1 + A * dt[i] / 2) ** -1
            
            hp = (LUMP1 * hobs[i] + LUMP2) * LUMP3
            
            # Calculate resulting recharge over dt (See logbook #11, p.23)
                    
            hup = min(hp, hobs[i+1])
            hlo = max(hp, hobs[i+1])
                    
            iup = np.where(hup >= z)[0][-1]
            ilo = np.where(hlo >= z)[0][-1]
            
            RECHG[i] = np.sum(dz[iup:ilo+1] * Sy[iup:ilo+1])        
            RECHG[i] -= (z[ilo+1] - hlo) * Sy[ilo]
            RECHG[i] -= (hup - z[iup]) * Sy[iup]
            
            # RECHG[i] will be positive in most cases. In theory, it should always
            # be positive, but error in the MRC and noise in the data can cause hp
            # to be above ho in some cases.
            
            RECHG[i] *= np.sign(hp - hobs[i+1])
               
        return RECHG 

if __name__ == '__main__':
   
    plt.close('all')
    
    dirname = '../Projects/Pont-Rouge/'
    fmeteo = dirname + 'Meteo/Output/STE CHRISTINE (7017000)_1960-2015.out'
    fwaterlvl = dirname + 'Water Levels/5080001.xls'
    
    CRU = np.array([0.2, 0.3, 0.4, 0.5])
    
#    CRU = [0.3]
    synth_hydrograph = SynthHydrograph(fmeteo, fwaterlvl, CRU, Sy=0.28)
    
#    synth_hydrograph = SynthHydrograph(fmeteo, fwaterlvl, CRU, Sy=0.3)
    
#    synth_hydrograph = SynthHydrograph(fmeteo, fwaterlvl, CRU, Sy=0.25)
    
#    synth_hydrograph = SynthHydrograph(fmeteo, fwaterlvl, CRU, Sy=0.2)
    
    plt.show()
    
    
    
    
#    Sy = 0.25
#    synth_hydrograph = SynthHydrograph(fmeteo, fwaterlvl, Sy, CRU)
#    Sy = 0.25
#    CRU = [0.45]
#    synth_hydrograph = SynthHydrograph(fmeteo, fwaterlvl, Sy, CRU)
    
#    plt.show()
#    for Sy in [0.2, 0.25, 0.3, 0.35]:
#        synth_hydrograph = SynthHydrograph(fmeteo, fwaterlvl, Sy, CRU)
    
    
    #        self.compare_rechg(twlvl, RECHGobs, tmeteo, RECHGpre)
    
#    @ staticmethod
#    def compare_rechg(tobs, Robs, tpre, Rpre):
#        
#        CORRCOEF = []
        
#        bwidth = 7.
#        nbin = np.floor(len(Robs) / bwidth)
#
#        Robs_week = Robs[:nbin*bwidth].reshape(nbin, bwidth)
#        Robs_week = np.sum(Robs_week, axis=1)
        
#        for i in range(100):
#            
#            tindx_start = np.where(tobs[0] == (tpre + i))[0][0]
#            tindx_end = np.where(tobs[-1] == (tpre + i))[0][0]
#        
#            Rpre2 = Rpre[tindx_start:tindx_end]
#            
#            Rpre2_week = Rpre2[:nbin*bwidth].reshape(nbin, bwidth)
#            Rpre2_week = np.sum(Rpre2_week, axis=1)
#
#            CORRCOEF.append(np.corrcoef(Rpre2_week, Robs_week)[0, 1])
                

#        print(np.sum(Robs)/len(Robs) * 365)
#        Robs[Robs<1] = 0
#
#        fig, ax = plt.subplots(2,1)
#        ax[0].plot(tobs[:-1], Robs)
#        ax[1].plot(tpre, Rpre)
#        plt.show(block=False)
        
        
#        print indx_start, indx_end
#        print(len(RECHGpre))
#        print(len(RECHGobs))
        
#        print len(RECHGpre[indx_start:indx_end+1])
#        print len(RECHGobs)
        
#        out = np.correlate(RECHGobs, RECHGpre[indx_start:indx_end+1])
       

        
#        Wsy = self.calc_hydrograph_down(RECHG, A, B, WLVLobs[-1], Sy * 1.05)
#        ss_sy = (Wsy-WLVLpre) / 0.05
#
#        Rcru = self.surf_water_budget(CRU * 1.05, RASmax, ETP, PTOT, TAVG)
#        Wcru = self.calc_hydrograph_down(Rcru, A, B, WLVLobs[-1], Sy)
#        ss_cru = (Wcru-WLVLpre) / 0.05
#        
#        Rras = self.surf_water_budget(CRU, RASmax * 1.05, ETP, PTOT, TAVG)
#        Wras = self.calc_hydrograph_down(Rras, A, B, WLVLobs[-1], Sy)
#        ss_ras = (Wras-WLVLpre) / 0.05
#        
#        ss_mat = np.vstack((ss_sy, ss_cru, ss_ras))
#        
#        VCo_mat = np.dot(ss_mat, ss_mat.T)
#        
#        pcc = np.zeros((3,3)) + np.diag([1,1,1])
#        #qz and porosity=
#        pcc[0,1] = VCo_mat[0,1]/(VCo_mat[0,0]**0.5*VCo_mat[1,1]**0.5)
#        pcc[1,0] = pcc[0,1]
#        #qz and soil moisture
#        pcc[0,2] = VCo_mat[0,2]/(VCo_mat[0,0]**0.5*VCo_mat[2,2]**0.5)
#        pcc[2,0] = pcc[0,2]
#        #porosity and soil moisture
#        pcc[2,1] = VCo_mat[2,1]/(VCo_mat[2,2]**0.5*VCo_mat[1,1]**0.5)
#        pcc[1,2] = pcc[2,1]
#        
#        print pcc