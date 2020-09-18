# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# Standard library imports
import os
import os.path as osp

# Third party imports
import numpy as np
import pytest

# Local imports
from gwhat.brf_mod.kgs_brf import read_brf_output
from gwhat.brf_mod import __install_dir__

BRFOUT_FNAME = osp.join(
    __install_dir__, 'tests', 'data', 'sample_BRFOutput.txt')


# =============================================================================
# ---- Tests BRFManager
# =============================================================================
def test_read_brf_output():
    """Test reading output data textfile from the KGS_BRF software."""
    dataf = read_brf_output(BRFOUT_FNAME)
    assert dataf.index.name == 'LagNo'
    assert list(dataf.columns) == ['Lag', 'A', 'sdA', 'SumA', 'sdSumA',
                                   'B', 'sdB', 'SumB', 'sdSumB']

    expected_results = np.array([
        [0, 0.521478346963427, 7.648827722801245e-3, 0.521478346963427,
         7.648827722801245e-3, 5.086604999498747e-3, 6.321138112964522e-3,
         5.086604999498747e-3, 9.952390015808350e-3],
        [1.041700000000000e-2, -6.947421040956547e-2, 7.771006243462716e-3,
         0.452004136553862, 9.510764156784108e-3, -5.479303873243220e-3,
         1.756708843397315e-2, -3.926988737444730e-4, 1.391296084688980e-2],
        [2.083400000000000e-2, 1.601502292575797e-2, 7.769715676833136e-3,
         0.468019159479620, 1.060394691961404e-2, -1.315681173763455e-2,
         1.806455491159068e-2, -1.354951061137902e-2, 1.342368409664440e-2],
        [3.125100000000000e-2, -1.042758981793621e-2, 7.767527692940659e-3,
         0.457591569661684, 1.115794799418575e-2, 1.549560118178247e-2,
         1.958206178346853e-2, 1.946090570403451e-3, 1.352319895121824e-2],
        [4.166800000000000e-2, -1.484155138618283e-2, 7.641345168801899e-3,
         0.442750018275501, 1.067620747867187e-2, 1.268481475971202e-2,
         1.806924845972978e-2, 1.463090533011547e-2, 1.405227605999844e-2],
        [5.208499999999999e-2, np.nan, np.nan, np.nan, np.nan,
         -2.221169698161619e-2, 1.756958272953278e-2, -7.580791651500721e-3,
         9.805609222919637e-3],
        [6.250200000000000e-2, np.nan, np.nan, np.nan, np.nan,
         7.582742242187344e-3, 6.320880028003846e-3, 1.950590686622573e-6,
         7.641489273970253e-3]
        ])

    assert len(dataf) == len(expected_results)
    for a, b in zip(expected_results.flatten(), dataf.values.flatten()):
        if np.isnan(a):
            assert np.isnan(b)
        else:
            assert a == b


if __name__ == "__main__":
    pytest.main(['-x', __file__, '-v', '-rw'])
