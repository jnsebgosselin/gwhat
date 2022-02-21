# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

import datetime
import numpy as np
from scipy.stats import linregress


def calcul_rmse(Xobs, Xpre):
    """Compute the root-mean square error."""
    return (np.nanmean((Xobs - Xpre)**2))**0.5


def calc_goodness_of_fit(xobs, xpre):
    """
    Calculate the goodness-of-fit between observed and predicted values.

    https://blog.minitab.com/en/adventures-in-statistics-2/regression-analysis-how-to-interpret-s-the-standard-error-of-the-regression
    https://statisticsbyjim.com/glossary/standard-error-regression/

    Parameters
    ----------
    xobs : np.ndarray
        A numpy array containing the observations.
    xpre : np.ndarray
        A numpy array containing the predictions.

    Returns
    -------
    std_err : float
        The standard error of the water levels predicted with the MRC.
    r_squared : float,
        The coefficient of determination of the water levels predicted
        with the MRC.
    rmse : float
        The root mean square error (RMSE) of the water levels predicted
        with the MRC.

    """
    mask = ~np.isnan(xobs) * ~np.isnan(xpre)
    slope, intercept, r_value, p_value, std_err = linregress(
        xobs[mask], xpre[mask])
    rmse = calcul_rmse(xobs, xpre)
    return std_err, r_value**2, rmse


def clip_time_series(tclip, tp, xp):
    """
    Clip tp and xp on tclip. tclip and tp must be arrays of numerical
    Excel times. Return two empty arrays if tclip and tp are
    mutually exclusive.
    """
    # Check that tp and tclip are not mutually exclusive.
    if len(np.unique(np.hstack([tclip, tp]))) == (len(tclip) + len(tp)):
        return [], []

    # Clip xp and tp on tclip.
    if tp[0] < tclip[0]:
        idx = np.where(tp >= tclip[0])[0][0]
        tp = tp[idx:]
        xp = xp[idx:]
    if tp[-1] > tclip[-1]:
        idx = np.where(tp <= tclip[-1])[0][-1]
        tp = tp[:idx+1]
        xp = xp[:idx+1]
    return tp, xp


def convert_date_to_datetime(years, months, days):
    """
    Produce datetime series from years, months, and days series.
    """
    dates = [0] * len(years)
    for t in range(len(years)):
        dates[t] = datetime.datetime(
                int(years[t]), int(months[t]), int(days[t]), 0)
    return dates


def nan_as_text_tolist(arr):
    """
    Convert the float nan to text while converting a numpy 2d array to a
    list, so that it is possible to save to an Excel file.
    """
    if np.isnan(arr).any():
        m, n = np.shape(arr)
        list_ = []
        for i in range(m):
            list_.append(['nan' if np.isnan(x) else x for x in arr[i, :]])
    else:
        list_ = arr.tolist()
    return list_
