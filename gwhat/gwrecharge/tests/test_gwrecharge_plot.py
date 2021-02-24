# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

# ---- Standard library imports
import os.path as osp

# ---- Third party imports
import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

# ---- Local library imports
from gwhat import __rootdir__
from gwhat.projet.reader_projet import ProjetReader
from gwhat.meteo.weather_viewer import WeatherViewer, QFileDialog
from gwhat.gwrecharge.gwrecharge_plot_results import FigureStackManager


# =============================================================================
# ---- Pytest Fixtures
# =============================================================================
@pytest.fixture
def project():
    projectfile = osp.join(
        __rootdir__, 'gwrecharge', 'tests', 'test_gwrecharge_project.gwt')
    project = ProjetReader(projectfile)
    return project


@pytest.fixture()
def figstackmanager(qtbot):
    figstackmanager = FigureStackManager()
    # qtbot.addWidget(figstackmanager)
    figstackmanager.show()
    qtbot.waitForWindowShown(figstackmanager)
    return figstackmanager


# =============================================================================
# ---- Tests
# =============================================================================
def test_figstackmanager(figstackmanager, project):
    """
    Test that the figure stack manager is working as expected.
    """
    # Make sure all figure manager are showing correctly when gluedf is None.
    for index in range(figstackmanager.stack.count()):
        figstackmanager.stack.setCurrentIndex(index)

    # Set a valid gluedf in the figure stack manager and make sure everything
    # is plotted as expected.
    wldset = project.get_wldset('3040002_15min')
    figstackmanager.set_gluedf(wldset.get_glue_at(-1))
    for index in range(figstackmanager.stack.count()):
        figstackmanager.stack.setCurrentIndex(index)


if __name__ == "__main__":
    pytest.main(['-x', __file__, '-v', '-rw', '-s'])
