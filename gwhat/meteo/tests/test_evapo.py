# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

# ---- Standard library imports
import os

# ---- Third party imports
import pandas as pd
import pytest
import numpy as np

# ---- Local library imports
from gwhat.meteo.evapotranspiration import calcul_daylength


# =============================================================================
# ---- Tests
# =============================================================================
def test_calcul_daylength():
    """
    Test that the photoperiod calculations are correct.
    """
    dtimes = pd.DatetimeIndex([
        '2019-01-01', '2019-02-01', '2019-03-01', '2019-04-01',
        '2019-05-01', '2019-06-01', '2019-07-01', '2019-08-01',
        '2019-09-01', '2019-10-01', '2019-11-01', '2019-12-01'])
    daylength = calcul_daylength(dtimes, 46.82)

    # The expected day lenghts were calculated for the city of Quebec
    # (latitude=46.82 ddec) with a tool available on the Government of
    # Canada website at:
    # https://www.nrc-cnrc.gc.ca/eng/services/sunrise/index.html

    expected_daylength = np.array([8.62, 9.64, 11.09, 12.82, 14.41, 15.61,
                                   15.80, 14.88, 13.35, 11.70, 10.04, 8.83])

    assert np.max(np.abs(daylength - expected_daylength)) < 0.1


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
