# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

# ---- Standard Libraries Imports
import os.path as osp

# ---- Third Party Libraries Imports
import numpy as np
import pytest
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication, QFileDialog


# ---- Local Libraries Imports
from gwhat.meteo.weather_reader import WXDataFrame
from gwhat.projet.reader_waterlvl import WLDataset
from gwhat.HydroCalc2 import WLCalc
from gwhat.projet.manager_data import DataManager
from gwhat.projet.reader_projet import ProjetReader


# =============================================================================
# ---- Pytest Fixtures
# =============================================================================
DATADIR = osp.join(osp.dirname(osp.realpath(__file__)), 'data')
WXFILENAME = osp.join(DATADIR, "MARIEVILLE (7024627)_2000-2015.out")
WLFILENAME = osp.join(DATADIR, 'sample_water_level_datafile.csv')


# ---- Pytest Fixtures
@pytest.fixture
def project(tmp_path):
    # Create a project and add add the wldset to it.
    project = ProjetReader(osp.join(tmp_path, "project_test_hydrocalc.gwt"))

    # Add the weather dataset to the project.
    wxdset = WXDataFrame(WXFILENAME)
    project.add_wxdset(wxdset.metadata['Station Name'], wxdset)

    # Add the water level dataset to the project.
    wldset = WLDataset(WLFILENAME)
    project.add_wldset(wldset['Well'], wldset)
    return project


@pytest.fixture
def datamanager(project):
    datamanager = DataManager()
    datamanager.set_projet(project)
    return datamanager


@pytest.fixture
def hydrocalc(datamanager, qtbot):
    hydrocalc = WLCalc(datamanager)
    hydrocalc.show()
    qtbot.addWidget(hydrocalc)
    return hydrocalc


# =============================================================================
# ---- Tests
# =============================================================================
def test_hydrocalc_init(hydrocalc):
    assert hydrocalc


def test_copy_to_clipboard(hydrocalc, qtbot):
    """
    Test that puting a copy of the hydrograph figure on the clipboard is
    working as expected.
    """
    QApplication.clipboard().clear()
    assert QApplication.clipboard().text() == ''
    assert QApplication.clipboard().image().isNull()

    qtbot.mouseClick(hydrocalc.btn_copy_to_clipboard, Qt.LeftButton)
    assert not QApplication.clipboard().image().isNull()


def test_calc_mrc(hydrocalc, tmp_path, qtbot, mocker):
    """
    Test that the tool to calculate the MRC is working as expected.
    """
    assert hydrocalc.dformat == 1  # Matplotlib date format
    hydrocalc.switch_date_format()
    assert hydrocalc.dformat == 0  # Excel date format

    # Select recession periods on the hydrograph.
    coordinates = [
        (41384.260416666664, 41414.114583333336),
        (41310.385416666664, 41340.604166666664),
        (41294.708333333336, 41302.916666666664),
        (41274.5625, 41284.635416666664),
        (41457.395833333336, 41486.875),
        (41440.604166666664, 41447.697916666664),
        (41543.958333333336, 41552.541666666664)]
    for coord in coordinates:
        hydrocalc.tools['mrc'].add_mrcperiod(coord)

    # Calcul the MRC.
    mrc_data = hydrocalc.wldset.get_mrc()
    assert np.isnan(mrc_data['params']).all()
    assert len(mrc_data['peak_indx']) == 0
    assert len(mrc_data['recess']) == 0
    assert len(mrc_data['time']) == 0

    hydrocalc.tools['mrc'].calculate_mrc()

    mrc_data = hydrocalc.wldset.get_mrc()
    assert abs(mrc_data['params'][0] - 0.07004324034418882) < 10**-5
    assert abs(mrc_data['params'][1] - 0.25679183844863535) < 10**-5
    assert len(mrc_data['peak_indx']) == 7
    assert len(mrc_data['recess']) == 343
    assert len(mrc_data['time']) == 343
    assert np.sum(~np.isnan(mrc_data['recess'])) == 123

    # Save MRC results to file.
    outfile = osp.join(tmp_path, 'test_mrc_export')
    ffilter = "Text CSV (*.csv)"
    qfdialog_patcher = mocker.patch.object(
        QFileDialog,
        'getSaveFileName',
        return_value=(outfile, ffilter))

    assert not osp.exists(outfile + '.csv')
    hydrocalc.tools['mrc'].save_mrc_tofile()
    assert osp.exists(outfile + '.csv')
    assert qfdialog_patcher.call_count == 1


if __name__ == "__main__":
    pytest.main(['-x', __file__, '-v', '-rw'])
