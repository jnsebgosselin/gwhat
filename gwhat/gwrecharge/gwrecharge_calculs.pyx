# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Third party imports

from numpy cimport ndarray
import numpy as np
cimport numpy as np
cimport cython
ctypedef np.float64_t DTYPE_t
DTYPE = np.float64

def calcul_surf_water_budget(ndarray[np.float64_t, ndim=1] ETP, 
                             ndarray[np.float64_t, ndim=1] PTOT, 
                             ndarray[np.float64_t, ndim=1] TAVG,
                             double TMELT, double CM, double CRU, 
                             double RASmax):
    
    cdef int N = len(ETP)
    cdef ndarray[np.float64_t, ndim=1] PAVL = np.zeros(N, dtype=DTYPE)   # Available  Precipitation
    cdef ndarray[np.float64_t, ndim=1] PACC = np.zeros(N, dtype=DTYPE)   # Accumulated Precipitation
    cdef ndarray[np.float64_t, ndim=1] RU = np.zeros(N, dtype=DTYPE)     # Runoff
    cdef ndarray[np.float64_t, ndim=1] I = np.zeros(N, dtype=DTYPE)      # Infiltration
    cdef ndarray[np.float64_t, ndim=1] ETR = np.zeros(N, dtype=DTYPE)    # Evapotranspiration Real
    cdef ndarray[np.float64_t, ndim=1] dRAS = np.zeros(N, dtype=DTYPE)   # Variation of RAW
    cdef ndarray[np.float64_t, ndim=1] RAS = np.zeros(N, dtype=DTYPE)    # Readily Available Storage
    cdef ndarray[np.float64_t, ndim=1] RECHG = np.zeros(N, dtype=DTYPE)  # Recharge (mm)
    cdef double MP = 0.0
    
    PACC[0] = 0
    RAS[0] = RASmax
    
    cdef Py_ssize_t i
    for i in range(N-1):
        MP = max(CM * (TAVG[i] - TMELT), 0)  # Snow Melt Potential

        # ----- Precipitation, Accumulation, and Melt -----

        if TAVG[i] > TMELT:
            # Precipitation is falling as rain.
            if MP >= PACC[i]:
                # Rain is falling on bareground (all snow is melted).
                PAVL[i] = PACC[i] + PTOT[i]
                PACC[i+1] = 0
            else:
                # Rain is falling on the snowpack.
                PAVL[i] = MP
                PACC[i+1] = PACC[i] - MP + PTOT[i]
        else:
            # Precipitation is falling as Snow.
            PAVL[i] = 0
            PACC[i+1] = PACC[i] + PTOT[i]

        # ----- Infiltration and Runoff -----

        # runoff coefficient
        RU[i] = CRU*PAVL[i]

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
    return RECHG, RU, ETR, RAS, PACC


def calc_hydrograph_forward(ndarray[np.float64_t, ndim=1] rechg, 
                            ndarray[np.float64_t, ndim=1] wlobs,
                            double Sy, double A, double B):
    
    cdef int N = len(wlobs)
    cdef ndarray[np.float64_t, ndim=1] wlpre = np.zeros(N, dtype=DTYPE)
    
    wlpre[0] = wlobs[0]
    cdef Py_ssize_t i
    for i in range(N-1):
        recess = max((B - A*wlpre[i]/1000) * 1000, 0)
        wlpre[i+1] = wlpre[i] - (rechg[i]/Sy) + recess
    return wlpre
