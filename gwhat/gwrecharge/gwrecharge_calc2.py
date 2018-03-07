# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Imports: standard libraries

import os
import datetime
from itertools import product
import time

# ---- Imports: third parties

import numpy as np
from xlrd import xldate_as_tuple
from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal as QSignal

# ---- Imports: local

from gwhat.gwrecharge.gwrecharge_calculs import (calcul_surf_water_budget,
                                                 calc_hydrograph_forward)


class RechgEvalWorker(QObject):

    sig_glue_progress = QSignal(float)
    sig_glue_finished = QSignal(int)

    def __init__(self):
        super(RechgEvalWorker, self).__init__()

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

        self.Sy = (0, 1)
        self.Cro = (0, 1)
        self.RASmax = (0, 150)

        self.language = 'French'
        self.glue_results = None
        self.fig = None
        self.glue_pardist_res = 'fine'

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

    def calc_recharge(self, data=None):
        data = self.glue_results
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

    def calcul_GLUE(self):
        if self.glue_pardist_res == 'rough':
            U_RAS = np.arange(self.RASmax[0], self.RASmax[1]+1, 5)
        elif self.glue_pardist_res == 'fine':
            U_RAS = np.arange(self.RASmax[0], self.RASmax[1]+1, 1)
        U_Cro = np.arange(self.Cro[0], self.Cro[1]+0.01, 0.01)

        # ---- Produce realization ----

        set_RMSE = []
        set_RECHG = []
        set_WLVL = []
        set_Sy = []
        set_RASmax = []
        set_Cru = []

        set_ru = []
        set_etr = []

        Sy0 = np.mean(self.Sy)
        tstart = time.clock()
        N = sum(1 for p in product(U_Cro, U_RAS))
        self.sig_glue_progress.emit(0)
        for it, (cro, rasmax) in enumerate(product(U_Cro, U_RAS)):
            rechg, ru, etr, ras, pacc = self.surf_water_budget(cro, rasmax)
            SyOpt, RMSE, wlvlest = self.optimize_Sy(Sy0, rechg)
            Sy0 = SyOpt

            if SyOpt >= self.Sy[0] and SyOpt <= self.Sy[1]:
                set_RMSE.append(RMSE)
                set_RECHG.append(rechg)
                set_WLVL.append(wlvlest)
                set_Sy.append(SyOpt)
                set_RASmax.append(rasmax)
                set_Cru.append(cro)
                set_etr.append(etr)
                set_ru.append(ru)

            self.sig_glue_progress.emit((it+1)/N*100)
            print(('Cru = %0.3f ; RASmax = %0.0f mm ; Sy = %0.4f ; ' +
                   'RMSE = %0.1f') % (cro, rasmax, SyOpt, RMSE))

        tend = time.clock()
        print("GLUE computed in : ", tend-tstart)

        if len(set_RMSE) > 0:
            print('-'*78)
            range_sy = (np.min(set_Sy), np.max(set_Sy))
            print('range Sy = %0.3f to %0.3f' % range_sy)
            range_rasmax = (np.min(set_RASmax), np.max(set_RASmax))
            print('range RASmax = %d to %d' % range_rasmax)
            range_cru = (np.min(set_Cru), np.max(set_Cru))
            print('range Cru = %0.3f to %0.3f' % range_cru)
            print('-'*78)

        self.glue_results = {}
        self.glue_results['RMSE'] = set_RMSE
        self.glue_results['recharge'] = set_RECHG
        self.glue_results['etr'] = set_etr
        self.glue_results['ru'] = set_ru

        self.glue_results['wl_time'] = self.twlvl
        self.glue_results['wl_obs'] = self.WLVLobs
        self.glue_results['wl_date'] = self.DATE
        self.glue_results['hydrograph'] = set_WLVL

        self.glue_results['Sy'] = set_Sy
        self.glue_results['RASmax'] = set_RASmax
        self.glue_results['Cru'] = set_Cru
        self.glue_results['deltat'] = self.deltat

        self.glue_results['Time'] = self.wxdset['Time']
        self.glue_results['Year'] = self.wxdset['Year']
        self.glue_results['Month'] = self.wxdset['Month']
        self.glue_results['Weather'] = {'Tmax': self.wxdset['Tmax'],
                                        'Tmin': self.wxdset['Tmin'],
                                        'Tavg': self.wxdset['Tavg'],
                                        'Ptot': self.wxdset['Ptot'],
                                        'Rain': self.wxdset['Rain'],
                                        'PET': self.wxdset['PET']
                                        }
        self.sig_glue_finished.emit(len(set_RECHG))
        return self.glue_results

    def load_glue_from_npy(self, filename):
        """Load previously computed results from a numpy npy file."""
        self.glue_results = np.load(filename).item()
        return self.glue_results

    def save_glue_to_npy(self, filename):
        """Save the last computed glue results in a numpy npy file."""
        if self.glue_results is None:
            print("There is no results to save.")
            return

        root, ext = os.path.splitext(filename)
        filename = filename if ext == '.npy' else filename+'.ext'
        np.save(filename, self.glue_results)

    def optimize_Sy(self, Sy0, rechg):
        """
        Finds the optimal value of Sy that minimizes the RMSE between the
        observed and predicted ground-water hydrographs.
        """
        tweatr = self.wxdset['Time']     # time weather data
        twlvl = self.twlvl               # time water level
        WLVLobs = self.WLVLobs * 1000    # water level observations

        # We introduce the time lag here.
        ts = np.where(twlvl[0] == tweatr+self.deltat)[0][0]
        te = np.where(twlvl[-1] == tweatr+self.deltat)[0][0]

        # ---- Gauss-Newton

        tolmax = 0.001
        Sy = Sy0
        dSy = 0.01

        WLVLpre = self.calc_hydrograph(rechg[ts:te], Sy)
        RMSE = calcul_rmse(WLVLobs[self.NaNindx], WLVLpre[self.NaNindx])

        it = 0
        while 1:
            it += 1
            if it > 100:
                print('Not converging.')
                break

            # Calculating Jacobian (X) Numerically.
            wlvl = self.calc_hydrograph(rechg[ts:te], Sy * (1+dSy))
            X = Xt = (wlvl[self.NaNindx] - WLVLpre[self.NaNindx])/(Sy*dSy)

            # Solving Linear System.
            dh = WLVLobs[self.NaNindx] - WLVLpre[self.NaNindx]
            XtX = np.dot(Xt, X)
            Xtdh = np.dot(Xt, dh)

            dr = np.linalg.tensorsolve(XtX, Xtdh, axes=None)

            # Storing old parameter values.
            Syold = np.copy(Sy)
            RMSEold = np.copy(RMSE)

            # Loop for Damping (to prevent overshoot)
            while 1:
                # Calculating new paramter values.
                Sy = Syold + dr

                # Solving for new parameter values.
                WLVLpre = self.calc_hydrograph(rechg[ts:te], Sy)
                RMSE = calcul_rmse(WLVLobs[self.NaNindx],
                                   WLVLpre[self.NaNindx])

                # Checking overshoot.
                if (RMSE - RMSEold) > 0.1:
                    dr = dr * 0.5
                else:
                    break

            # Checking tolerance.
            tol = np.abs(Sy - Syold)
            if tol < tolmax:
                return Sy, RMSE, WLVLpre

    def surf_water_budget(self, CRU, RASmax):
        """
        Compute recharge with a daily soil surface moisture balance model.

        RU = Runoff coefficient
        RASmax = Readily Available Storage Max in mm
        ETP = Dailty evapotranspiration in mm
        PTOT = Daily total precipitation in mm
        TAVG = Daily average air temperature in deg. C.
        CM = Daily melt coefficient
        TMELT = Temperature treshold for snowmelt
        RECHG = Daily groundwater recharge in mm
        """
        RECHG, RU, ETR, RAS, PACC = calcul_surf_water_budget(
                self.ETP, self.PTOT, self.TAVG, self.TMELT,
                self.CM,  CRU, RASmax)

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

        # TODO: It should also be possible to do a Crank-Nicholson on this.
        # I should check this out.

        A, B = self.A, self.B
        wlobs = self.WLVLobs*1000
        if nscheme == 'backward':
            wlpre = np.zeros(len(RECHG)+1) * np.nan
            wlpre[0] = wlobs[-1]
            for i in reversed(range(len(RECHG))):
                RECESS = (B - A * wlpre[i] / 1000.) * 1000
                RECESS = max(RECESS, 0)

                wlpre[i] = wlpre[i+1] + (RECHG[i] / Sy) - RECESS
        elif nscheme == 'forward':
            wlpre = calc_hydrograph_forward(RECHG, wlobs, Sy, self.A, self.B)
        else:
            wlpre = []

        return wlpre

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


def calcul_rmse(Xobs, Xpre):
    """Compute the root-mean square error."""
    return (np.mean((Xobs - Xpre)**2))**0.5


def calcul_nash_sutcliffe(Xobs, Xpre):
    """
    Compute the Nash–Sutcliffe model efficiency coefficient.
    https://en.wikipedia.org/wiki/Nash–Sutcliffe_model_efficiency_coefficient
    """
    return 1 - np.sum((Xobs - Xpre)**2) / np.sum((Xobs - np.mean(Xobs))**2)


def calcul_containement_ratio(obs_wlvl, min_wlvl, max_wlvl):
    """Calcul the containement ratio of the GLUE5/95 predicted water levels."""
    CR = 0
    for i in range(len(obs_wlvl)):
        if obs_wlvl[i] >= min_wlvl[i] and obs_wlvl[i] <= max_wlvl[i]:
            CR += 1
    CR = CR/len(obs_wlvl)
    print('Containement Ratio = %0.1f' % CR)
    return CR


def calcul_glue(data, p, varname='recharge'):
    """
    Calcul recharge for GLUE p confidence intervals from a set of
    behavioural models.
    """
    if varname not in ['recharge', 'etr', 'ru', 'hydrograph']:
        raise ValueError("varname value must be",
                         ['recharge', 'etr', 'ru', 'hydrograph'])
    x = np.array(data[varname])
    m, n = np.shape(x)

    rmse = np.array(data['RMSE'])
    rmse = rmse/np.sum(rmse)  # Rescaling

    glue_dly = np.zeros((n, len(p)))
    for i in range(n):
        # Sort predicted values.
        isort = np.argsort(x[:, i])
        # Compute the Cumulative Density Function.
        CDF = np.cumsum(rmse[isort])
        # Get GLUE values for the p confidence intervals.
        glue_dly[i, :] = np.interp(p, CDF, x[isort, i])

    return glue_dly


def calcul_glue_yearly_rechg(data, p, yrs_range=None):
    glue_rechg_dly = calcul_glue(data, p, varname='recharge')

    years = np.array(data['Year']).astype(int)
    months = np.array(data['Month']).astype(int)
    deltat = data['deltat']
    if deltat > 0:
        Time = np.array(data['Time'])
        for i, t in enumerate(Time):
            date = xldate_as_tuple(t+deltat, 0)
            years[i], months[i] = date[0], date[1]

    # Convert daily to hydrological year. An hydrological year is defined from
    # October 1 to September 30 of the next year.

    if yrs_range:
        yrs2plot = np.arange(yrs_range[0], yrs_range[1]).astype('int')
    else:
        yrs2plot = np.arange(np.min(years), np.max(years)).astype('int')

    glue_rechg_yr = np.zeros((len(yrs2plot), len(p)))
    year_labels = []
    for i in range(len(yrs2plot)):
        yr0 = yrs2plot[i]
        yr1 = yr0 + 1
        year_labels.append("'%s-'%s" % (str(yr0)[-2:], str(yr1)[-2:]))

        indexes = np.where((years == yr0) & (months == 10))[0]
        indx0 = 0 if len(indexes) == 0 else indexes[0]

        indexes = np.where((years == yr1) & (months == 9))[0]
        indx1 = len(years-1) if len(indexes) == 0 else indexes[-1]

        glue_rechg_yr[i, :] = np.sum(glue_rechg_dly[indx0:indx1+1, :], axis=0)

    return year_labels, glue_rechg_yr


# ---- if __name__ == '__main__'

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    plt.close('all')
    import os
    from gwrecharge_post import plot_rechg_GLUE

    sh = RechgEvalWorker()

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
    sh.calcul_GLUE(Sy, RASmax, Cru, res='rough')

    # sh.calc_recharge()
    sh.initPlot()
    sh.plot_prediction()
    plot_rechg_GLUE('English', Ymin0=-20, yrs_range=[2000, 2016])
