# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Imports: standard libraries

import os
import os.path as osp
import datetime
from itertools import product
import time

# ---- Imports: third parties

import numpy as np
from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal as QSignal

# ---- Imports: local

from gwhat.gwrecharge.glue import GLUEDataFrame
from gwhat.gwrecharge.gwrecharge_calculs import (calcul_surf_water_budget,
                                                 calc_hydrograph_forward)


class RechgEvalWorker(QObject):

    sig_glue_progress = QSignal(float)
    sig_glue_finished = QSignal(object)

    def __init__(self):
        super(RechgEvalWorker, self).__init__()
        self.wxdset = None
        self.ETP, self.PTOT, self.TAVG = [], [], []

        self.wldset = None
        self.A, self.B = None, None
        self.twlvl = []
        self.wlobs = []
        self.wl_date = []

        self.TMELT = 0
        self.CM = 4
        self.deltat = 0

        self.Sy = (0, 1)
        self.Cro = (0, 1)
        self.RASmax = (0, 150)

        self.glue_pardist_res = 'fine'

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
        # Setup weather data.

        self.wxdset = wxdset
        self.ETP = self.wxdset['PET']
        self.PTOT = self.wxdset['Ptot']
        self.TAVG = self.wxdset['Tavg']
        self.tweatr = self.wxdset['Time'] + self.deltat
        # We introduce a time lag here to take into account the travel time
        # through the unsaturated zone.

        # Setup water level data.

        self.wldset = wldset
        self.A, self.B = wldset['mrc/params']
        self.twlvl, self.wlobs = self.make_data_daily(wldset['Time'],
                                                      wldset['WL'])

        if not self.A and not self.B:
            error = ("Groundwater recharge cannot be computed because a"
                     " master recession curve (MRC) must be defined first.")
            return error

        # Check that the wldset and wxdset are not mutually exclusive.
        time = np.unique(np.hstack([self.tweatr, self.twlvl]))
        if len(time) == (len(self.tweatr) + len(self.twlvl)):
            error = ("Groundwater recharge cannot be computed because the"
                     " water level and weather datasets are mutually"
                     " exclusive in time.")
            return error

        # Clip the observed water level time series to the weather data.
        if self.twlvl[0] < self.tweatr[0]:
            idx = np.where(self.twlvl == self.tweatr[0])[0][0]
            self.twlvl = self.twlvl[idx:]
            self.wlobs = self.wlobs[idx:]
        if self.twlvl[-1] > self.tweatr[-1]:
            idx = np.where(self.twlvl == self.tweatr[-1])[0][0]
            self.twlvl = self.twlvl[:idx+1]
            self.wlobs = self.wlobs[:idx+1]

        # Compute time in a datetime format readable by matplotlib.
        ts = np.where(self.twlvl[0] == self.tweatr)[0][0]
        te = np.where(self.twlvl[-1] == self.tweatr)[0][0]

        years = self.wxdset['Year'][ts:te+1]
        months = self.wxdset['Month'][ts:te+1]
        days = self.wxdset['Day'][ts:te+1]
        self.wl_date = convert_date_to_datetime(years, months, days)

        return None

    def make_data_daily(self, t, h):
        """
        Convert a given time series to a daily basis. Only the last water level
        measurements made on a given day is kept in the daily time series.
        If there is no measurement at all for a given day, the default nan
        value is kept instead in the daily time series.
        """
        argsort = np.argsort(t)
        t = np.floor(t[argsort])
        h = h[argsort]

        td = np.arange(np.min(t), np.max(t)+1, 1).astype(int)
        hd = np.ones(len(td)) * np.nan
        for i in range(len(td)):
            indx = np.where(t == td[i])[0]
            if len(indx) > 0:
                hd[i] = h[indx[-1]]

        return td, hd

    def produce_params_combinations(self):
        """
        Produce a set of parameter combinations (RASmax + Cro) from the ranges
        provided by the user using a flat distribution.
        """
        if self.glue_pardist_res == 'rough':
            U_RAS = np.arange(self.RASmax[0], self.RASmax[1]+1, 5)
        elif self.glue_pardist_res == 'fine':
            U_RAS = np.arange(self.RASmax[0], self.RASmax[1]+1, 1)
        U_Cro = np.arange(self.Cro[0], self.Cro[1]+0.01, 0.01)

        return U_RAS, U_Cro

    def eval_recharge(self):
        """
        Produce a set of behavioural models that all represent the observed
        data equiprobably and evaluate the water budget with GLUE for diffrent
        GLUE uncertainty limits.
        """

        U_RAS, U_Cro = self.produce_params_combinations()

        # Find the indexes to align the water level with the weather data
        # daily time series.

        ts = np.where(self.twlvl[0] == self.tweatr)[0][0]
        te = np.where(self.twlvl[-1] == self.tweatr)[0][0]

        # ---- Produce realizations

        set_RMSE = []

        set_Sy = []
        set_RASmax = []
        set_Cru = []

        sets_waterlevels = []
        set_recharge = []
        set_runoff = []
        set_evapo = []

        Sy0 = np.mean(self.Sy)
        time_start = time.clock()
        N = sum(1 for p in product(U_Cro, U_RAS))
        self.sig_glue_progress.emit(0)
        for it, (cro, rasmax) in enumerate(product(U_Cro, U_RAS)):
            rechg, ru, etr, ras, pacc = self.surf_water_budget(cro, rasmax)
            SyOpt, RMSE, wlvlest = self.optimize_specific_yield(
                    Sy0, self.wlobs*1000, rechg[ts:te])
            Sy0 = SyOpt

            if SyOpt >= min(self.Sy) and SyOpt <= max(self.Sy):
                set_RMSE.append(RMSE)
                set_recharge.append(rechg)
                sets_waterlevels.append(wlvlest)
                set_Sy.append(SyOpt)
                set_RASmax.append(rasmax)
                set_Cru.append(cro)
                set_evapo.append(etr)
                set_runoff.append(ru)

            self.sig_glue_progress.emit((it+1)/N*100)
            print(('Cru = %0.3f ; RASmax = %0.0f mm ; Sy = %0.4f ; ' +
                   'RMSE = %0.1f') % (cro, rasmax, SyOpt, RMSE))

        print("GLUE computed in : %0.1 s" % (time.clock()-time_start))
        self._print_model_params_summary(set_Sy, set_Cru, set_RASmax)

        # ---- Format results

        glue_rawdata = {}
        glue_rawdata['models'] = {}
        glue_rawdata['models']['count'] = len(set_RMSE)
        glue_rawdata['models']['RMSE'] = set_RMSE
        glue_rawdata['models']['params'] = {'RMSE': set_RMSE,
                                            'Sy': set_Sy,
                                            'RASmax': set_RASmax,
                                            'Cru': set_Cru}
        glue_rawdata['models']['input ranges'] = {'Sy': self.Sy,
                                                  'Cro': self.Cro,
                                                  'RASmax': self.RASmax,
                                                  'tmelt': self.TMELT,
                                                  'CM': self.CM,
                                                  'deltat': self.deltat}

        glue_rawdata['water levels'] = {}
        glue_rawdata['water levels']['time'] = self.twlvl
        glue_rawdata['water levels']['date'] = self.wl_date
        glue_rawdata['water levels']['observed'] = self.wlobs
        glue_rawdata['water levels']['simulated'] = sets_waterlevels

        glue_rawdata['mrc'] = {}
        glue_rawdata['mrc']['params'] = self.wldset['mrc/params']
        glue_rawdata['mrc']['time'] = self.wldset['mrc/time']
        glue_rawdata['mrc']['levels'] = self.wldset['mrc/recess']

        glue_rawdata['recharge'] = set_recharge
        glue_rawdata['etr'] = set_evapo
        glue_rawdata['ru'] = set_runoff
        glue_rawdata['Time'] = self.wxdset['Time']
        glue_rawdata['Year'] = self.wxdset['Year']
        glue_rawdata['Month'] = self.wxdset['Month']
        glue_rawdata['Day'] = self.wxdset['Day']
        glue_rawdata['Weather'] = {'Tmax': self.wxdset['Tmax'],
                                   'Tmin': self.wxdset['Tmin'],
                                   'Tavg': self.wxdset['Tavg'],
                                   'Ptot': self.wxdset['Ptot'],
                                   'Rain': self.wxdset['Rain'],
                                   'PET': self.wxdset['PET']}

        # Save infos about the piezometric station.

        keys = ['Well', 'Well ID', 'Province', 'Latitude', 'Longitude',
                'Elevation', 'Municipality']
        glue_rawdata['wlinfo'] = {k: self.wldset[k] for k in keys}

        # Save infos about the weather station.

        keys = ['Station Name', 'Climate Identifier', 'Province', 'Latitude',
                'Longitude', 'Elevation']
        glue_rawdata['wxinfo'] = {k: self.wxdset[k] for k in keys}

        self.save_glue_to_npy('glue_rawdata.npy', glue_rawdata)


        if len(set_RECHG) == 0:
            glue_dataf = GLUEDataFrame(results)
        else:
            glue_dataf = None
        self.sig_glue_finished.emit(glue_dataf)

        return glue_dataf

    def _print_model_params_summary(self, set_Sy, set_Cru, set_RASmax):
        """
        Print a summary of the range of parameter values that were used to
        produce the set of behavioural models.
        """
        print('-'*78)
        if len(set_Sy) > 0:
            print('-'*78)
            range_sy = (np.min(set_Sy), np.max(set_Sy))
            print('range Sy = %0.3f to %0.3f' % range_sy)
            range_rasmax = (np.min(set_RASmax), np.max(set_RASmax))
            print('range RASmax = %d to %d' % range_rasmax)
            range_cru = (np.min(set_Cru), np.max(set_Cru))
            print('range Cru = %0.3f to %0.3f' % range_cru)
            print('-'*78)
        else:
            print("The number of behavioural model produced is 0.")

    def save_glue_to_npy(self, filename, glue_rawdata):
        """Save the last computed glue results in a numpy npy file."""
        root, ext = os.path.splitext(filename)
        filename = filename if ext == '.npy' else filename+'.ext'
        np.save(filename, glue_rawdata)

    def optimize_specific_yield(self, Sy0, wlobs, rechg):
        """
        Find the optimal value of Sy that minimizes the RMSE between the
        observed and predicted ground-water hydrographs. The observed water
        level (wlobs) and simulated recharge (rechg) time series must be
        in mm and be properly align in time.
        """
        nonan_indx = np.where(~np.isnan(wlobs))

        # ---- Gauss-Newton

        tolmax = 0.001
        Sy = Sy0
        dSy = 0.01

        wlpre = self.calc_hydrograph(rechg, Sy)
        RMSE = calcul_rmse(wlobs[nonan_indx], wlpre[nonan_indx])

        it = 0
        while 1:
            it += 1
            if it > 100:
                print('Not converging.')
                break

            # Calculating Jacobian (X) Numerically.
            wlvl = self.calc_hydrograph(rechg, Sy * (1+dSy))
            X = Xt = (wlvl[nonan_indx] - wlpre[nonan_indx])/(Sy*dSy)

            # Solving Linear System.
            dh = wlobs[nonan_indx] - wlpre[nonan_indx]
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
                wlpre = self.calc_hydrograph(rechg, Sy)
                RMSE = calcul_rmse(wlobs[nonan_indx], wlpre[nonan_indx])

                # Checking overshoot.
                if (RMSE - RMSEold) > 0.1:
                    dr = dr * 0.5
                else:
                    break

            # Checking tolerance.
            tol = np.abs(Sy - Syold)
            if tol < tolmax:
                return Sy, RMSE, wlpre

    def surf_water_budget(self, CRU, RASmax):
        """
        Compute recharge with a daily soil surface moisture balance model.

        CRU = Surface runoff coefficient
        RASmax = Maximum readily available storage in mm
        ETP = Dailty potential evapotranspiration in mm
        PTOT = Daily total precipitation in mm
        TAVG = Daily average air temperature in deg. C.
        CM = Daily melt coefficient
        TMELT = Temperature treshold for snowmelt

        rechg = Daily groundwater recharge in mm
        etr = Daily real evapotranspiration in mm
        ru = Daily surface runoff in mm
        ras = Daily readily available storage in mm
        pacc = Daily accumulated precipitation on the ground surface in mm
        """
        rechg, ru, etr, ras, pacc = calcul_surf_water_budget(
                self.ETP, self.PTOT, self.TAVG, self.TMELT,
                self.CM,  CRU, RASmax)

        return rechg, ru, etr, ras, pacc

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
        wlobs = self.wlobs*1000
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


def convert_date_to_datetime(years, months, days):
    """
    Produce datetime series from years, months, and days series.
    """
    dates = [0] * len(years)
    for t in range(len(years)):
        dates[t] = datetime.datetime(
                int(years[t]), int(months[t]), int(days[t]), 0)
    return dates


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


def load_glue_from_npy(filename):
    """Load previously computed results from a numpy npy file."""
    glue_results = np.load(filename).item()
    return glue_results
