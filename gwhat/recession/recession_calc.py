# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

from __future__ import annotations

# ---- Third party imports
import numpy as np
from scipy.optimize import curve_fit
from functools import partial


def predict_recession(t: np.ndarray, B: float, A: float,
                      h: np.ndarray,
                      breaks: np.ndarray) -> np.ndarray:
    """
    Compute synthetic hydrograph with a time-forward implicit numerical scheme
    during periods where the water level recedes identified by the "ipeak"
    pointers.

    This is documented in logbook#10 p.79-80, 106.
    """
    hp = np.ones(len(h)) * np.nan
    for i in range(len(t)):
        if i in breaks:
            hp[i] = h[i]
        else:
            dt = t[i] - t[i - 1]
            LUMP1 = (1 - A * dt / 2)
            LUMP2 = B * dt
            LUMP3 = (1 + A * dt / 2)**-1

            hp[i] = (LUMP1 * hp[i - 1] + LUMP2) * LUMP3
    return hp


def calculate_mrc(t, h, periods: list(tuple), mrctype: int = 1):
    """
    Calculate the equation parameters of the Master Recession Curve (MRC) of
    the aquifer from the water level time series using a modified Gauss-Newton
    optimization method.

    Parameters
    ----------
    h : water level time series in mbgs
    t : time in days
    periods: sequence of tuples containing the boundaries, in XLS numerical
             date format, of the periods selected by the user to evaluate
             the MRC.

    mrctype: MRC equation type
             MODE = 0 -> linear (dh/dt = b)
             MODE = 1 -> exponential (dh/dt = -a*h + b)
    """
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

    indexes = []
    for i in range(len(periods)):
        indexes.extend(range(istart[i], iend[i] + 1))
    indexes = np.sort(indexes)

    breaks = []
    for i in range(len(indexes)):
        if indexes[i] in istart:
            breaks.append(i)

    A0 = 0
    B0 = np.mean((h[istart] - h[iend]) / (t[istart] - t[iend]))

    if mrctype == 1:  # exponential (dh/dt = -a*h + b)
        coeffs, coeffs_cov = curve_fit(
            f=partial(predict_recession, h=h[indexes], breaks=breaks),
            xdata=t[indexes], ydata=h[indexes],
            p0=[A0, B0],
            bounds=([-np.inf, 0], [np.inf, np.inf])
            )
        B, A = coeffs
    elif mrctype == 0:  # linear (dh/dt = b)
        func = partial(predict_recession, A=0, h=h[indexes], breaks=breaks)
        coeffs, coeffs_cov = curve_fit(
            func, xdata=t[indexes], ydata=h[indexes], p0=[B0])
        B = coeffs[0]
        A = 0

    hp = np.zeros(len(t)) * np.nan
    hp[indexes] = predict_recession(
        t=t[indexes], A=A, B=B, h=h[indexes], breaks=breaks)

    RMSE = (np.mean((h[indexes] - hp[indexes])**2))**0.5

    print(coeffs_cov)

    return A, B, hp, RMSE


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

    A, B, hp, RMSE = calculate_mrc(t, h, periods, mrctype=1)
    print(A, B)

    fig, ax = plt.subplots()
    ax.plot(t, h)
    ax.plot(t, hp)
    ax.invert_yaxis()
