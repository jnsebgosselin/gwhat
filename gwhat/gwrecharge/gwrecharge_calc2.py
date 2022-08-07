# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

# ---- Stantard imports
import os
import os.path as osp
import datetime
from itertools import product
from time import perf_counter

# ---- Third party imports
import numpy as np
import pandas as pd
from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal as QSignal

# ---- Local imports
from gwhat.utils.math import clip_time_series, calcul_rmse
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

        self.TMELT = 0
        self.CM = 4
        self.deltat = 0

        # Models parameters space.
        self.Sy = (0, 1)
        self.Cro = (0, 1)
        self.RASmax = (0, 150)
        self.glue_pardist_res = 'fine'

        self.rmse_cutoff = 0
        self.rmse_cutoff_enabled = 0

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
        self.ETP = self.wxdset.data['PET'].values
        self.PTOT = self.wxdset.data['Ptot'].values
        self.TAVG = self.wxdset.data['Tavg'].values
        self.tweatr = self.wxdset.get_xldates() + self.deltat
        # We introduce a time lag here to take into account the travel time
        # through the unsaturated zone.

        # Setup water level data.

        self.wldset = wldset
        self.A, self.B = wldset.get_mrc()['params']
        self.twlvl, self.wlobs = self.make_data_daily(
            wldset.xldates, wldset['WL'])

        if pd.isnull(self.A) and pd.isnull(self.B):
            error = ("Groundwater recharge cannot be computed because a"
                     " master recession curve (MRC) must be defined first.")
            return error

        # Clip the observed water level time series to the weather data.
        self.twlvl, self.wlobs = clip_time_series(
            self.tweatr, self.twlvl, self.wlobs)

        # We need to remove nan values at the start and the end of the series
        # to avoid problems when computing synthetic hydrographs.
        for istart in range(len(self.wlobs)):
            if not np.isnan(self.wlobs[istart]):
                break
        for iend in reversed(range(len(self.wlobs))):
            if not np.isnan(self.wlobs[iend]):
                break
        self.twlvl = self.twlvl[istart:iend]
        self.wlobs = self.wlobs[istart:iend]

        if len(self.twlvl) == 0:
            # The wldset and wxdset are mutually exclusive.
            error = ("Groundwater recharge cannot be computed because the"
                     " water level and weather datasets are mutually"
                     " exclusive in time.")
            return error
        else:
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
        time_start = perf_counter()
        N = sum(1 for p in product(U_Cro, U_RAS))
        self.sig_glue_progress.emit(0)
        for it, (cro, rasmax) in enumerate(product(U_Cro, U_RAS)):
            rechg, ru, etr, ras, pacc = self.surf_water_budget(cro, rasmax)
            SyOpt, RMSE, wlvlest = self.optimize_specific_yield(
                Sy0, self.wlobs*1000, rechg[ts:te])
            if SyOpt is not None:
                Sy0 = SyOpt

                # Check if the model respected the cutoff criteria if any.
                rmse_cutoff_value = (
                    self.rmse_cutoff if self.rmse_cutoff_enabled else RMSE)
                if (SyOpt >= self.Sy[0] and
                        SyOpt <= self.Sy[1] and
                        RMSE <= rmse_cutoff_value):
                    set_RMSE.append(RMSE)
                    set_recharge.append(rechg)
                    sets_waterlevels.append(wlvlest)
                    set_Sy.append(SyOpt)
                    set_RASmax.append(rasmax)
                    set_Cru.append(cro)
                    set_evapo.append(etr)
                    set_runoff.append(ru)

            self.sig_glue_progress.emit((it+1)/N*100)
        print("GLUE computed in {:0.1f} sec".format(perf_counter()-time_start))
        self._print_model_params_summary(set_Sy, set_Cru, set_RASmax, set_RMSE)

        # ---- Format results
        glue_rawdata = {}
        glue_rawdata['count'] = len(set_RMSE)
        glue_rawdata['RMSE'] = np.array(set_RMSE)
        glue_rawdata['params'] = {'Sy': np.array(set_Sy),
                                  'RASmax': np.array(set_RASmax),
                                  'Cru': np.array(set_Cru),
                                  'tmelt': self.TMELT,
                                  'CM': self.CM,
                                  'deltat': self.deltat}
        glue_rawdata['ranges'] = {'Sy': self.Sy,
                                  'Cro': self.Cro,
                                  'RASmax': self.RASmax}
        glue_rawdata['cutoff'] = {
            'rmse_cutoff': self.rmse_cutoff,
            'rmse_cutoff_enabled': self.rmse_cutoff_enabled}

        glue_rawdata['water levels'] = {}
        glue_rawdata['water levels']['time'] = self.twlvl
        glue_rawdata['water levels']['observed'] = self.wlobs

        glue_rawdata['Weather'] = {'Tmax': self.wxdset.data['Tmax'].values,
                                   'Tmin': self.wxdset.data['Tmin'].values,
                                   'Tavg': self.wxdset.data['Tavg'].values,
                                   'Ptot': self.wxdset.data['Ptot'].values,
                                   'Rain': self.wxdset.data['Rain'].values,
                                   'PET': self.wxdset.data['PET'].values}

        # Save the water levels simulated with the mrc, as well as and values
        # of the parameters that characterized this mrc.
        glue_rawdata['mrc'] = self.wldset.get_mrc()

        # Store the models output that will need to be processed with GLUE.
        glue_rawdata['hydrograph'] = sets_waterlevels
        glue_rawdata['recharge'] = set_recharge
        glue_rawdata['etr'] = set_evapo
        glue_rawdata['ru'] = set_runoff
        glue_rawdata['Time'] = self.wxdset.get_xldates()
        glue_rawdata['Year'] = self.wxdset.data.index.year.values
        glue_rawdata['Month'] = self.wxdset.data.index.month.values
        glue_rawdata['Day'] = self.wxdset.data.index.day.values

        # Save infos about the piezometric station.

        keys = ['Well', 'Well ID', 'Province', 'Latitude', 'Longitude',
                'Elevation', 'Municipality']
        glue_rawdata['wlinfo'] = {k: self.wldset[k] for k in keys}

        # Save infos about the weather station.

        keys = ['Station Name', 'Station ID', 'Location', 'Latitude',
                'Longitude', 'Elevation']
        glue_rawdata['wxinfo'] = {k: self.wxdset.metadata[k] for k in keys}

        # Calcul GLUE from the set of behavioural model and send the results
        # with a signal so that it can be handled on the UI side.

        if glue_rawdata['count'] > 0:
            glue_dataf = GLUEDataFrame(glue_rawdata)
            # self._save_glue_to_npy(glue_rawdata)
        else:
            glue_dataf = None
        self.sig_glue_finished.emit(glue_dataf)

        return glue_dataf

    def _print_model_params_summary(self, set_Sy, set_Cru, set_RASmax,
                                    set_rmse):
        """
        Print a summary of the range of parameter values that were used to
        produce the set of behavioural models.
        """
        if len(set_Sy) > 0:
            print('%d behavioural models were produced' % len(set_Sy))
            print('-'*78)
            range_sy = (np.min(set_Sy), np.max(set_Sy))
            print('range Sy = %0.3f to %0.3f' % range_sy)
            range_rasmax = (np.min(set_RASmax), np.max(set_RASmax))
            print('range RASmax = %d to %d' % range_rasmax)
            range_cru = (np.min(set_Cru), np.max(set_Cru))
            print('range Cru = %0.3f to %0.3f' % range_cru)
            range_rmse = (np.min(set_rmse), np.max(set_rmse))
            print('range RMSE = %0.1f to %0.1f' % range_rmse)
            print('mean RMSE = %0.1f' % np.mean(set_rmse))
            print('-'*78)
        else:
            print("The number of behavioural model produced is 0.")

    def _save_glue_to_npy(self, glue_rawdata):
        """Save the last computed glue results in a numpy npy file."""
        if not osp.exists(osp.dirname(__file__)):
            os.makedirs(osp.dirname(__file__))
        filename = osp.join(osp.dirname(__file__), 'glue_rawdata.npy')
        np.save(filename, glue_rawdata)

    def optimize_specific_yield(self, Sy0, wlobs, rechg):
        """
        Find the optimal value of Sy that minimizes the RMSE between the
        observed and predicted ground-water hydrographs. The observed water
        level (wlobs) and simulated recharge (rechg) time series must be
        in mm and be properly align in time.
        """
        nonan_indx = np.where(~np.isnan(wlobs))

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
                return None, None, None

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
        wlobs = self.wlobs.copy() * 1000
        if np.isnan(wlobs[0]) or np.isnan(wlobs[-1]):
            raise ValueError('The observed water level time series either '
                             'starts or ends with a nan value.')
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


def convert_date_to_strdate(years, months, days):
    """Produce a list of dates in bytes using the '%Y-%m-%d' format."""
    strdates = ['%d-%02d-%02d' % (yy, mm, dd) for
                yy, mm, dd in zip(years, months, days)]
    # We need to encode the strings because it cannot be saved in hdf5
    # otherwise. See https://github.com/h5py/h5py/issues/289.
    strdates = [s.encode('utf8') for s in strdates]
    return strdates


def strdate_to_datetime(strdates):
    """Return a list of datetime objects created from a list of bytes."""
    return [datetime.datetime.strptime(s.decode('utf8'), '%Y-%m-%d')
            for s in strdates]


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
