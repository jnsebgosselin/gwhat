# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Standard Libraries Imports
import os
import os.path as osp

# ---- Third Party Libraries Imports
import pytest
from PyQt5.QtCore import Qt

# ---- Local Libraries Imports
from gwhat.meteo.weather_reader import WXDataFrame
from gwhat.projet.reader_waterlvl import WLDataFrame
from gwhat.HydroCalc2 import WLCalc
from gwhat.projet.manager_data import DataManager
from gwhat.projet.reader_projet import ProjetReader


# ---- Pytest Fixtures
DATADIR = osp.join(osp.dirname(osp.realpath(__file__)), 'data')
WXFILENAME = osp.join(DATADIR, "MARIEVILLE (7024627)_2000-2015.out")
WLFILENAME = osp.join(DATADIR, 'sample_water_level_datafile.csv')


# ---- Pytest Fixtures
@pytest.fixture(scope="module")
def projectpath(tmp_path_factory):
    return tmp_path_factory.mktemp("project_test_hydrocalc")


@pytest.fixture(scope="module")
def project(projectpath):
    # Create a project and add add the wldset to it.
    project = ProjetReader(osp.join(projectpath, "project_test_hydrocalc.gwt"))

    # Add the weather dataset to the project.
    wxdset = WXDataFrame(WXFILENAME)
    project.add_wxdset(wxdset['Station Name'], wxdset)

    # Add the water level dataset to the project.
    wldset = WLDataFrame(WLFILENAME)
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
    qtbot.addWidget(hydrocalc)
    hydrocalc.show()
    return hydrocalc


# ---- Test WLCalc
@pytest.mark.run(order=9)
def test_hydrocalc_init(hydrocalc, mocker):
    assert hydrocalc


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
    # pytest.main()
