# -*- coding: utf-8 -*-
"""
Copyright 2014-2017 Jean-Sebastien Gosselin
email: jean-sebastien.gosselin@ete.inrs.ca

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

from __future__ import division, unicode_literals

# Standard library imports :

# from datetime import date
import csv
import datetime

# Third party imports :

import numpy as np
# from xlrd import xldate_as_tuple
from xlrd.xldate import xldate_from_date_tuple
import matplotlib.pyplot as plt

# Local imports :

import meteo.weather_reader as wxrd
from waterlvldata import WaterlvlData
from gwrecharge_post import plot_water_budget_yearly


# =============================================================================


class SynthHydrograph(object):

    def __init__(self):

        self.wxdset = None
        self.ETP, self.PTOT, self.TAVG = [], [], []

        self.wldset = None
        self.A, self.B = None, None

        self.twlvl = []
        self.WLVLobs = []
        self.NaNindx = []

        self.YEAR = []
        self.MONTH = []
        self.TIME = []
        self.PRECIP = []

        self.DATE = []

        self.TMELT = 0
        self.CM = 4
        self.deltat = 0

        self.language = 'French'

    # =========================================================================

    @property
    def language(self):
        return self.__language

    @language.setter
    def language(self, x):
        if x.lower() in ['french', 'english']:
            self.__language = x
        else:
            raise NameError('Language must be either French or English.')

    @property
    def CM(self):
        return self.__CM

    @CM.setter
    def CM(self, x):
        if x > 0:
            self.__CM = x
        else:
            raise ValueError('CM must be greater than 0.')

    @property
    def TMELT(self):
        return self.__TMELT

    @TMELT.setter
    def TMELT(self, x):
        self.__TMELT = x

    # =========================================================================

    def load_data(self, wxdset, wldset):

        # ---- Load Data ----

        print('--------')

        self.wxdset = wxdset

        # Includes the estimation of ETP if not already present in file.

        self.ETP = self.wxdset['PET']
        self.PTOT = self.wxdset['Ptot']
        self.TAVG = self.wxdset['Tavg']

        print('--------')

        self.wldset = wldset

        self.A, self.B = wldset['mrc/params']
        self.twlvl, self.WLVLobs = self.make_data_daily(wldset['Time'],
                                                        wldset['WL'])
        self.NaNindx = np.where(~np.isnan(self.WLVLobs))

        print('--------')

        # ---- Prepare DATE time series ----

        # Converting time in a date format readable by matplotlib and also make
        # the weather and water level time series synchroneous.

        tweatr = self.wxdset['Time']

        ts = self.ts = np.where(self.twlvl[0] == tweatr)[0][0]
        te = self.te = np.where(self.twlvl[-1] == tweatr)[0][0]

        self.YEAR = self.wxdset['Year'][ts:te+1]
        self.MONTH = self.wxdset['Month'][ts:te+1]
        DAY = self.wxdset['Day'][ts:te+1]
        self.TIME = self.wxdset['Time'][ts:te+1]
        self.DATE = self.convert_time_to_date(self.YEAR, self.MONTH, DAY)
        self.PRECIP = self.wxdset['Ptot'][ts:te+1]

    # =========================================================================

    def make_data_daily(self, t, h):
        argsort = np.argsort(t)
        t = np.floor(t[argsort])
        h = h[argsort]

        tmin = np.min(t)
        tmax = np.max(t)
        t1d = np.arange(tmin, tmax+1, 1)
        h1d = np.ones(len(t1d))*np.nan

        # Only the last water level measurements made on that day will be
        # kept in the h1d time series.
        # If there is no measurement at all, the default nan value is
        # kept instead in the h1d time series.

        for i in range(len(t1d)):
            indx = np.where(t == t1d[i])[0]
            if len(indx) > 0:
                h1d[i] = h[indx[-1]]

        return t1d, h1d

    @staticmethod
    def convert_time_to_date(YEAR, MONTH, DAY):

        DATE = [0] * len(YEAR)
        for t in range(len(YEAR)):
            DATE[t] = datetime.datetime(int(YEAR[t]), int(MONTH[t]),
                                        int(DAY[t]), 0)

        return DATE

    # =========================================================================

    def initPlot(self):

        # ---- Prepare Figure and Plot Obs. ----

        fwidth, fheight = 12.5, 6
        self.fig = plt.figure(figsize=(fwidth, fheight))

        lmarg = 0.85/fwidth
        rmarg = 0.25/fwidth
        tmarg = 0.5/fheight
        bmarg = 0.65/fheight

        axwidth = 1 - (lmarg + rmarg)
        axheight = 1 - (bmarg + tmarg)

        ax = self.fig.add_axes([lmarg, bmarg, axwidth, axheight])

        # ---- Figure setup ----
        label = 'Water Level (mbgs)'
        if self.language == 'French':
            label = "Niveau d'eau (m sous la surface)"

        ax.set_ylabel(label, fontsize=16)
        ax.grid(axis='x', color=[0.65, 0.65, 0.65], ls=':', lw=1)
        ax.set_axisbelow(True)

        ax.invert_yaxis()

        # ----------------------------------------------- Plot Observation ----

        wlvl, = ax.plot(self.DATE, self.WLVLobs, color='b', ls='None',
                        marker='.', ms=3, zorder=100)

        self.fig.canvas.draw()

        # ----------------------------------------------- YTICKS FORMATING ----

        ax.yaxis.set_ticks_position('left')
        ax.tick_params(axis='y', direction='out', gridOn=True, labelsize=12)

        # ----------------------------------------------- XTICKS FORMATING ----

        ax.xaxis.set_ticks_position('bottom')
        ax.tick_params(axis='x', direction='out')
        self.fig.autofmt_xdate()

        # ---- Legend ----

        dum1 = plt.Rectangle((0, 0), 1, 1, fc='0.5', ec='0.5')
        dum2, = plt.plot([], [], color='b', ls='None', marker='.', ms=10)

        lg_handles = [dum2, dum1]
        lg_labels = ['Observations', 'GLUE 5/95']

        ax.legend(lg_handles, lg_labels, ncol=2, fontsize=12, frameon=False,
                  numpoints=1)

    def plot_prediction(self):

        data = np.load('GLUE.npy').item()
        hydrograph = np.array(data['hydrograph'])
        RMSE = np.array(data['RMSE'])
        RMSE = RMSE / np.sum(RMSE)

        hGLUE = []
        for i in range(len(hydrograph[0, :])):
            isort = np.argsort(hydrograph[:, i])
            CDF = np.cumsum(RMSE[isort])
            hGLUE.append(
                np.interp([0.05, 0.5, 0.95], CDF, hydrograph[isort, i]))

        hGLUE = np.array(hGLUE)
        min_wlvl = hGLUE[:, 0] / 1000.
        max_wlvl = hGLUE[:, 2] / 1000.

        self.fig.axes[0].fill_between(
                self.DATE, max_wlvl, min_wlvl, color='0.5', lw=1.5,
                alpha=0.65, zorder=10)

        # ---- Calculate Containement Ratio ----

        obs_wlvl = self.WLVLobs
        CR = 0
        for i in range(len(obs_wlvl)):
            if obs_wlvl[i] >= min_wlvl[i] and obs_wlvl[i] <= max_wlvl[i]:
                CR += 1.

        print('Containement Ratio = %0.1f' % CR)

    # =========================================================================

    @staticmethod
    def nash_sutcliffe(Xobs, Xpre):
        # Source: Wikipedia
        # https://en.wikipedia.org/wiki/
        # Nash%E2%80%93Sutcliffe_model_efficiency_coefficient
        return 1 - np.sum((Xobs - Xpre)**2) / np.sum((Xobs - np.mean(Xobs))**2)

    @staticmethod
    def calc_RMSE(Xobs, Xpre):
        return (np.mean((Xobs - Xpre)**2))**0.5

    def calc_recharge(self):
        data = np.load('GLUE.npy').item()
        rechg = np.array(data['recharge'])
        RMSE = np.array(data['RMSE'])

        CPDF = np.cumsum(RMSE / np.sum(RMSE))
        TIME = self.wxdset['Time']
        Rbound = []
        for i in range(len(TIME)):
            isort = np.argsort(rechg[:, i])
            Rbound.append(
                np.interp([0.05, 0.5, 0.95], CPDF[isort], rechg[isort, i]))
        Rbound = np.array(Rbound)

        max_rechg = np.sum(Rbound[:, 2]) / len(Rbound[:, 0]) * 365.25
        min_rechg = np.sum(Rbound[:, 0]) / len(Rbound[:, 0]) * 365.25
        prob_rechg = np.sum(Rbound[:, 1]) / len(Rbound[:, 0]) * 365.25

        print('Max Recharge = %0.1f mm/y' % max_rechg)
        print('Min Recharge = %0.1f mm/y' % min_rechg)
        print('Most Probable Recharge = %0.1f mm/y' % prob_rechg)

    # =============================================================== GLUE ====

    def GLUE(self, Sy, RASmax, Cro, res='rough'):
        if res == 'rough':
            U_RAS = np.arange(RASmax[0], RASmax[1]+1, 5)
            U_Cro = np.arange(Cro[0], Cro[1]+0.01, 0.05)
        elif res == 'fine':
            U_RAS = np.arange(RASmax[0], RASmax[1]+1, 1)
            U_Cro = np.arange(Cro[0], Cro[1]+0.01, 0.01)

        # ---- Produce realization ----

        set_RMSE = []
        set_RECHG = []
        set_WLVL = []
        set_Sy = []
        set_RASmax = []
        set_Cru = []

        set_ru = []
        set_etr = []

        Sy0 = np.mean(Sy)
        for i, cro in enumerate(U_Cro):
            for j, rasmax in enumerate(U_RAS):
                rechg, ru, etr, ras, pacc = self.surf_water_budget(cro, rasmax)
                SyOpt, RMSE, wlvlest = self.opt_Sy(Sy0, rechg)
                Sy0 = SyOpt

                if SyOpt >= Sy[0] and SyOpt <= Sy[1]:
                    set_RMSE.append(RMSE)
                    set_RECHG.append(rechg)
                    set_WLVL.append(wlvlest)
                    set_Sy.append(SyOpt)
                    set_RASmax.append(rasmax)
                    set_Cru.append(cro)
                    set_etr.append(etr)
                    set_ru.append(ru)

                print(('Cru = %0.3f ; RASmax = %0.0f mm ; Sy = %0.4f ; ' +
                       'RMSE = %0.1f') % (cro, rasmax, SyOpt, RMSE))

        dataset = {}
        dataset['RMSE'] = set_RMSE
        dataset['recharge'] = set_RECHG
        dataset['etr'] = set_etr
        dataset['ru'] = set_ru

        dataset['twlvl'] = self.twlvl
        dataset['hydrograph'] = set_WLVL

        dataset['Sy'] = set_Sy
        dataset['RASmax'] = set_RASmax
        dataset['Cru'] = set_Cru
        dataset['deltat'] = self.deltat

        dataset['Time'] = self.wxdset['Time']
        dataset['Year'] = self.wxdset['Year']
        dataset['Month'] = self.wxdset['Month']
        dataset['Weather'] = {'Tmax': self.wxdset['Tmax'],
                              'Tmin': self.wxdset['Tmin'],
                              'Tavg': self.wxdset['Tavg'],
                              'Ptot': self.wxdset['Ptot'],
                              'Rain': self.wxdset['Rain'],
                              'PET': self.wxdset['PET']
                              }

        np.save('GLUE.npy', dataset)

    # =========================================================================

    def opt_Sy(self, Sy0, rechg):
        tweatr = self.wxdset['Time']     # Here we introduce the time lag
        twlvl = self.twlvl               # time water level
        WLVLobs = self.WLVLobs * 1000    # water level observations

        ts = np.where(twlvl[0] == tweatr+self.deltat)[0][0]
        te = np.where(twlvl[-1] == tweatr+self.deltat)[0][0]

        # ---- Gauss-Newton ----

        tolmax = 0.001
        Sy = Sy0
        dSy = 0.01

        WLVLpre = self.calc_hydrograph(rechg[ts:te], Sy)
        RMSE = self.calc_RMSE(WLVLobs[self.NaNindx], WLVLpre[self.NaNindx])

        it = 0
        while 1:
            it += 1
            if it > 100:
                print('Not converging.')
                break

            # Calculating Jacobian (X) Numerically :

            wlvl = self.calc_hydrograph(rechg[ts:te], Sy * (1+dSy))
            X = Xt = (wlvl[self.NaNindx] - WLVLpre[self.NaNindx])/(Sy*dSy)

            # Solving Linear System :

            dh = WLVLobs[self.NaNindx] - WLVLpre[self.NaNindx]
            XtX = np.dot(Xt, X)
            Xtdh = np.dot(Xt, dh)

            dr = np.linalg.tensorsolve(XtX, Xtdh, axes=None)

            # Storing old parameter values :

            Syold = np.copy(Sy)
            RMSEold = np.copy(RMSE)

            while 1:  # Loop for Damping (to prevent overshoot)

                # Calculating new paramter values :

                Sy = Syold + dr

                # Solving for new parameter values :

                WLVLpre = self.calc_hydrograph(rechg[ts:te], Sy)
                RMSE = self.calc_RMSE(WLVLobs[self.NaNindx],
                                      WLVLpre[self.NaNindx])

                # Checking overshoot :

                if (RMSE - RMSEold) > 0.1:
                    dr = dr * 0.5
                else:
                    break

            # Checking tolerance :

            tol = np.abs(Sy - Syold)

            if tol < tolmax:
                return Sy, RMSE, WLVLpre

    def surf_water_budget(self, CRU, RASmax):
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
        ETP = self.ETP
        PTOT = self.PTOT
        TAVG = self.TAVG

        TMELT = self.TMELT
        CM = self.CM

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

        for i in range(N-1):

            # ----- Precipitation, Accumulation, and Melt -----

            if TAVG[i] > TMELT:  # Rain
                if MP[i] >= PACC[i]:  # Rain on Bareground (All snow is melted)
                    PAVL[i] = PACC[i] + PTOT[i]
                    PACC[i+1] = 0
                elif MP[i] < PACC[i]:  # Rain on Snow
                    PAVL[i] = MP[i]
                    PACC[i+1] = PACC[i] - MP[i] + PTOT[i]
            elif TAVG[i] <= TMELT:  # Snow
                PAVL[i] = 0
                PACC[i+1] = PACC[i] + PTOT[i]

#            if TAVG[i] > TMELT:  # Rain
#
#                if MP[i] >= PACC[i]: # Rain on Bareground
#                    PAVL[i+1] = PACC[i] + PTOT[i]
#                    PACC[i+1] = 0
#
#                elif MP[i] < PACC[i]: #Rain on Snow
#                    PAVL[i+1] = MP[i]
#                    PACC[i+1] = PACC[i] - MP[i] + PTOT[i]
#
#            elif TAVG[i] <= TMELT: #Snow
#                PAVL[i+1] = 0
#                PACC[i+1] = PACC[i] + PTOT[i]

            # ----- Infiltration and Runoff -----

            # runoff coefficient
            RU[i] = CRU * PAVL[i]

            # curve number
            # CN = CRU
            # num = (PAVL[i] - 0.2*(1000/CN-10))**2
            # den = PAVL[i] + 0.8*(1000/CN-10)
            # RU[i] = max(num/den, 0)

            I[i] = PAVL[i] - RU[i]

            # ----- ETR, Recharge and Storage change -----

            # Intermediate Step
            dRAS[i] = min(I[i], RASmax - RAS[i])
            RAS[i+1] = RAS[i] + dRAS[i]

            # Final Step
            RECHG[i] = I[i] - dRAS[i]
            ETR[i] = min(ETP[i], RAS[i])
            RAS[i+1] = RAS[i+1] - ETR[i]

            # Evaportransporation is calculated after recharge. It is assumed
            # that recharge occurs on a time scale that is faster than
            # evapotranspiration in permeable soil.

#        print np.sum(PTOT - ETR - RECHG - RU) - (RAS[-1] - RAS[0])

        return RECHG, RU, ETR, RAS, PACC

    def calc_hydrograph(self, RECHG, Sy, nscheme='forward'):
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
        WLobs: Observed Water Level (mm)

        A, B: MRC Parameters, where: Recess(m/d) = -A * h + B
        nscheme: Option are "forward" or "downdward" depending if the
                 hydrograph is being built forward in time or backward.
                 Default is "forward".
        """

        # It should also be possible to do a Crank-Nicholson on this. I should
        # check this out.

        A, B = self.A, self.B
        WLobs = self.WLVLobs * 1000

        WLpre = np.zeros(len(RECHG)+1) * np.nan

        if nscheme == 'backward':
            WLpre[0] = WLobs[-1]
            for i in reversed(range(len(RECHG))):
                RECESS = (B - A * WLpre[i] / 1000.) * 1000
                RECESS = max(RECESS, 0)

                WLpre[i] = WLpre[i+1] + (RECHG[i] / Sy) - RECESS

        elif nscheme == 'forward':
            WLpre[0] = WLobs[0]
            for i in range(len(RECHG)):
                # if i%365 == 0:
                #     WLpre[i+1] = WLobs[i]
                # else:
                RECESS = (B - A*WLpre[i]/1000) * 1000
                RECESS = max(RECESS, 0)

                WLpre[i+1] = WLpre[i] - (RECHG[i] / Sy) + RECESS
        else:
            WLpre = []

        return WLpre

    @staticmethod
    def mrc2rechg(t, hobs, A, B, z, Sy):

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

        # ---- Check Data Integrity ----

        if np.min(hobs) < 0:
            print('Water level rise above ground surface.' +
                  ' Please check your data.')
            return

        dz = np.diff(z)  # Tickness of soil layer

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

            # RECHG[i] will be positive in most cases. In theory, it should
            # always be positive, but error in the MRC and noise in the data
            # can cause hp to be above ho in some cases.

            RECHG[i] *= np.sign(hp - hobs[i+1])

        return RECHG

if __name__ == '__main__':

    plt.close('all')
    import os
    from gwrecharge_post import plot_rechg_GLUE

    sh = SynthHydrograph()

    # ---- Pont-Rouge ----

#    dirname = '../Projects/Pont-Rouge/'
#    fmeteo = dirname + 'Meteo/Output/STE CHRISTINE (7017000)_1960-2015.out'
#    fwaterlvl = dirname + 'Water Levels/5080001.xls'

    # ---- Valcartier ----

#    dirname = '../Projects/Valcartier'
#    fmeteo = os.path.join(dirname, 'Meteo', 'Output', 'Valcartier (9999999)',
#                          'Valcartier (9999999)_1994-2015.out')
#    fwaterlvl = os.path.join(dirname, 'Water Levels', 'valcartier2.xls')
#
#    Sy = [0.2, 0.3]
#    RASmax = [40, 100]
#    Cru = [0.22, 0.39]
#    sh.TMELT = 0
#    sh.CM = 4

    # ---- IDM ----

#    dirname = '../Projects/IDM/'
#    fmeteo = os.path.join(dirname, 'Meteo', 'Output', 'IDM (JSG2017)',
#                          'IDM (JSG2017)_1960-2016.out')

#    fwaterlvl = os.path.join(dirname, 'Water Levels', 'Boisville.xls')
#    Sy = [0.05, 0.15]
#    RASmax = [10, 100]
#    Cru = [0.1, 0.3]
#    sh.TMELT = -2

#    fwaterlvl = os.path.join(dirname, 'Water Levels', 'Cap-aux-Meules.xls')
#    Sy = [0.2, 0.3]
#    RASmax = [100, 200]
#    Cru = [0.2, 0.4]
#    sh.TMELT = -2

#    fwaterlvl = os.path.join(dirname, 'Water Levels', 'Fatima.xls')
#    Sy = [0.05, 0.15]
#    RASmax = [10, 100]
#    Cru = [0.1, 0.3]
#    sh.TMELT = -5

    # ---- NB ----

    dirname = '../Projects/Sussex'
    fmeteo = os.path.join(dirname, 'Meteo', 'Output',
                          'SUSSEX (8105200_8105210)',
                          'SUSSEX (8105200_8105210)_1980-2017.out')
    fwaterlvl = os.path.join(dirname, 'Water Levels', 'PO-03.xlsx')

    Sy = [0.001, 0.05]
    # RASmax = [40, 110]
    # Cru = [0.35, 0.45]
    RASmax = [40, 110]
    Cru = [0.35, 0.45]
#    Cru = [60, 70]
    sh.TMELT = -2
    sh.CM = 4

    # ---- Suffield ----

#    dirname = 'C:\\Users\\jnsebgosselin\\OneDrive\\Research\\Collaborations\\'
#    dirname += 'R. Martel - Suffield\\Suffield (WHAT)'
#    fmeteo = os.path.join(dirname, 'Meteo', 'Output',
#                          'MEDICINE HAT RCS (3034485)',
#                          'MEDICINE HAT RCS (3034485)_2000-2016.out')

#    fmeteo = os.path.join(dirname, 'Meteo', 'Output',
#                          'SUFFIELD A (3036240)',
#                          'SUFFIELD A (3036240)_1990-2016.out')
##
#    fmeteo = os.path.join(dirname, 'Meteo', 'Output',
#                          'ROLLING HILLS AGCM (3035530)',
#                          'ROLLING HILLS AGCM (3035530)_2007-2016.out')

#    fmeteo = os.path.join(dirname, 'Meteo', 'Output',
#                          'ATLEE AGCM (3020405)',
#                          'ATLEE AGCM (3020405)_2009-2016.out')

#    fmeteo = os.path.join(dirname, 'Meteo', 'Output',
#                          'SCHULER AGDM (3025768)',
#                          'SCHULER AGDM (3025768)_2002-2016.out')

#    fwaterlvl = os.path.join(dirname, 'Water Levels', 'GWSU16.xlsx')
#
#    Sy = [0.1, 0.32]
#    RASmax = [15, 35]
#    Cru = [0, 0.05]
#    sh.TMELT = -2.5
#    sh.CM = 4
#    sh.deltat = 80

    # ---- Pont-Rouge ----

#    dirname = '../Projects/Pont-Rouge/'
#    fmeteo = dirname + 'Meteo/Output/STE CHRISTINE (7017000)_1960-2015.out'
#    fwaterlvl = dirname + 'Water Levels/5080001.xls'

    # ---- Wainwright ----

#    dirname = '../Projects/Wainwright/'
#    fmeteo = (dirname + 'Meteo/Output/WAINWRIGHT CFB AIRFIELD 21 (301S001)' +
#              '/WAINWRIGHT CFB AIRFIELD 21 (301S001)_2000-2016.out')
#
#    fwaterlvl = dirname + 'Water Levels/area3-GW-07.xlsx'
#
#    Sy = [0.2*0.9, 0.2*1.1]
#    RASmax = [15, 55]
#    Cru = [0, 0.15]
#    sh.TMELT = 0
#    sh.CM = 4
#    sh.deltat = delta = 25

    # ---- Example ----

#    fmeteo = ('C:/Users/jnsebgosselin/Desktop/Example/Meteo/Output/'
#              'STE CHRISTINE (7017000)/'
#              'STE CHRISTINE (7017000)_1990-2015.out')
#    fwaterlvl = ('C:/Users/jnsebgosselin/Desktop/Example/'
#                 'Water Levels/5080001.xls')
#
#    Sy = [0.2, 0.3]
#    RASmax = [40, 120]
#    Cru = [0.2, 0.4]
#    sh.TMELT = 0
#    sh.CM = 2.75

    # ---- Calculations ----

    sh.load_data(fmeteo, fwaterlvl)
    sh.GLUE(Sy, RASmax, Cru, res='rough')

    # sh.calc_recharge()
    sh.initPlot()
    sh.plot_prediction()
    plot_rechg_GLUE('English', Ymin0=-20, yrs_range=[2000, 2016])

    plt.show()
