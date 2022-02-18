# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

from __future__ import annotations

# ---- Standard library imports
from functools import partial
from collections import namedtuple

# ---- Third party imports
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import linregress


def predict_recession(tdeltas: np.ndarray, B: float, A: float,
                      h: np.ndarray) -> np.ndarray:
    """
    Parameters
    ----------
    tdeltas : np.ndarray
        Time in days after the start of the recession segment. Values of
        0 indicate the start of a new recession segment.
    B : float
        Coefficient of the master recession curve equation, where
        ∂h/∂t = -A * h + B.
    A : float
        Coefficient of the master recession curve equation, where
        ∂h/∂t = -A * h + B.
    h : np.ndarray
        Water levels in meters below the ground surface.

    Returns
    -------
    hp : np.ndarray
        Predicted water levels in meters below the ground surface.

    """
    hp = np.ones(len(h)) * np.nan
    for i in range(len(tdeltas)):
        if tdeltas[i] == 0:
            hp[i] = h[i]
        else:
            dt = tdeltas[i] - tdeltas[i - 1]
            LUMP1 = (1 - A * dt / 2)
            LUMP2 = B * dt
            LUMP3 = (1 + A * dt / 2)**-1

            hp[i] = (LUMP1 * hp[i - 1] + LUMP2) * LUMP3

    return hp


def calculate_mrc(t, h, periods: list(tuple), mrctype: int = 1):
    """
    Calculate the master recession curve (MRC).
    Parameters
    ----------
    t : np.ndarray
        Time in days.
    h : np.ndarray
        Water levels in meters below the ground surface.
    periods : list(tuple)
        List of tuples containing the boundaries of the segments of
        the hydrograph that need to be used to evaluate the MRC.
    mrctype : int, optional
        Equation type of the MRC. The default is 1.
            mrctype = 0 -> linear (dh/dt = b)
            mrctype = 1 -> exponential (dh/dt = -a*h + b)

    Returns
    -------
    coeffs : namedtuple
        The optimal coefficients of the MRC.
    hp : np.ndarray
        The water levels predicted using the calculated MRC.
    std_err : float
        The standard error of the water levels predicted with the MRC.
    r_squared : float,
        The coefficient of determination of the water levels predicted
        with the MRC.
    rmse : float
        The root mean square error (RMSE) of the water levels predicted
        with the MRC.
    """
    # Define the indices corresponding to the beginning and end of each
    # recession segment.
    iend = []
    istart = []
    for period in periods:
        indx0 = np.argmin(np.abs(t - period[0]))
        indx1 = np.argmin(np.abs(t - period[1]))
        if np.abs(indx1 - indx0) < 2:
            # Periods that are smaller than two time steps are ignored.
            continue
        istart.append(min(indx0, indx1))
        iend.append(max(indx0, indx1))

    # Define the indexes corresponding to the recession segments.
    seg_indexes = []
    seg_tstart = []
    for i, j in zip(istart, iend):
        seg_tstart.extend([t[i]] * (j - i + 1))
        seg_indexes.extend(range(i, j + 1))

    # Sort periods indexes and time start so that both series are
    # monotically increasing.
    argsort_idx = np.argsort(seg_indexes)
    seg_indexes = np.array(seg_indexes)[argsort_idx]
    seg_tstart = np.array(seg_tstart)[argsort_idx]

    t_seg = t[seg_indexes]
    h_seg = h[seg_indexes]
    tdeltas = (t_seg - seg_tstart)

    # Define initial guess for the parameters .
    A0 = 0
    B0 = np.mean((h[istart] - h[iend]) / (t[istart] - t[iend]))

    if mrctype == 1:  # exponential (dh/dt = -a*h + b)
        coeffs, coeffs_cov = curve_fit(
            f=partial(predict_recession, h=h_seg),
            xdata=tdeltas, ydata=h_seg,
            p0=[B0, A0],
            bounds=([-np.inf, 0], [np.inf, np.inf]))
        coeffs = namedtuple('Coeffs', ['B', 'A'])(*coeffs)
    elif mrctype == 0:  # linear (dh/dt = b)
        coeffs, coeffs_cov = curve_fit(
            f=partial(predict_recession, A=0, h=h_seg),
            xdata=tdeltas, ydata=h_seg, p0=[B0])

        # In order to return a consistent signature regardless of the type
        # of the MRC equation, we return a value of 0 for the coefficient A.
        coeffs = namedtuple('Coeffs', ['B', 'A'])('B', 'A')(coeffs[0], 0)

    hp = np.zeros(len(t)) * np.nan
    hp[seg_indexes] = predict_recession(
        tdeltas, A=coeffs[1], B=coeffs[0], h=h_seg)

    # Calculate metrics of the fit.
    # https://blog.minitab.com/en/adventures-in-statistics-2/regression-analysis-how-to-interpret-s-the-standard-error-of-the-regression
    # https://statisticsbyjim.com/glossary/standard-error-regression/
    slope, intercept, r_value, p_value, std_err = linregress(
        h[seg_indexes], hp[seg_indexes])
    r_squared = r_value**2
    rmse = (np.nanmean((h - hp)**2))**0.5

    return coeffs, hp, std_err, r_squared, rmse


if __name__ == '__main__':
    from gwhat.projet.reader_waterlvl import WLDataFrame
    import matplotlib.pyplot as plt

    wldset = WLDataFrame(
        "C:/Users/User/gwhat/gwhat/tests/data/sample_water_level_datafile.csv")
    periods = [
        (41384.260416666664, 41414.114583333336),
        (41310.385416666664, 41340.604166666664),
        (41294.708333333336, 41302.916666666664),
        (41274.5625, 41284.635416666664),
        (41457.395833333336, 41486.875),
        (41440.604166666664, 41447.697916666664),
        (41543.958333333336, 41552.541666666664)]

    t = wldset.xldates
    h = wldset.waterlevels

    coeffs, hp, std_err, r_squared, rmse = calculate_mrc(
        t, h, periods, mrctype=1)
    print(coeffs)
    print(std_err, r_squared, rmse)

    fig, ax = plt.subplots()
    ax.plot(t, h)
    ax.plot(t, hp)
    ax.plot(t, hp + std_err)
    ax.plot(t, hp - std_err)
    ax.invert_yaxis()

    fig2, ax2 = plt.subplots()
    ax2.plot(h, hp, 'o')

    # %%
    coeffs_stack = []
    hp_stack = []
    for period in periods:
        coeffs, hp, std_err, r_squared, rmse = calculate_mrc(
            t, h, [period], mrctype=1)
        coeffs_stack.append(coeffs)
        hp_stack.append(hp)

    fig3, ax3 = plt.subplots()
    ax3.plot(t, h)

    iend = []
    istart = []
    for period in periods:
        indx0 = np.argmin(np.abs(t - period[0]))
        indx1 = np.argmin(np.abs(t - period[1]))
        if np.abs(indx1 - indx0) < 2:
            # Periods that are smaller than two time steps are ignored.
            continue
        istart.append(min(indx0, indx1))
        iend.append(max(indx0, indx1))

    # Define the indexes corresponding to the recession segments.
    seg_indexes = []
    seg_tstart = []
    for i, j in zip(istart, iend):
        seg_tstart.extend([t[i]] * (j - i + 1))
        seg_indexes.extend(range(i, j + 1))

    # Sort periods indexes and time start so that both series are
    # monotically increasing.
    argsort_idx = np.argsort(seg_indexes)
    seg_indexes = np.array(seg_indexes)[argsort_idx]
    seg_tstart = np.array(seg_tstart)[argsort_idx]

    t_seg = t[seg_indexes]
    h_seg = h[seg_indexes]
    tdeltas = (t_seg - seg_tstart)

    for coeffs in coeffs_stack:
        hp = np.ones(len(h)) * np.nan
        hp[seg_indexes] = predict_recession(tdeltas, coeffs.B, coeffs.A, h_seg)
        ax3.plot(t, hp)

    ax3.invert_yaxis()
