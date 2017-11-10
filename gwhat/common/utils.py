# -*- coding: utf-8 -*-

# Copyright © 2014-2017 Jean-Sebastien Gosselin
# email: jean-sebastien.gosselin@ete.inrs.ca
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Imports: third party

import numpy as np


def latlon_to_dist(lat1, lon1, lat2, lon2):
    """
    Computes the horizontal distance in km between 2 points from geographic
    coordinates given in decimal degrees.

    source:
    www.stackoverflow.com/questions/19412462 (last accessed on 17/01/2014)
    """
    from math import sin, cos, sqrt, atan2, radians

    r = 6373  # r is the Earth radius in km.

    # Convert decimal degrees to radians.
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    # Compute the horizontal distance between the two points in km.
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = (sin(dlat/2))**2 + cos(lat1) * cos(lat2) * (sin(dlon/2))**2
    c = 2 * atan2(np.sqrt(a), sqrt(1-a))

    dist = r * c

    return dist
