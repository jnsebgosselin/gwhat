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
import numpy as np
import pytest
from PyQt5.QtGui import QImage
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
    qtbot.addWidget(figstackmanager)
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


def test_hydrological_budget_calculs(figstackmanager, project):
    """
    Test that the yearly values of the hydrological budget are calculated
    as expected
    """
    wldset = project.get_wldset('3040002_15min')
    glue_df = wldset.get_glue_at(-1)
    figstackmanager.set_gluedf(glue_df)

    # Assert the average yearly recharge values are calculated as expected in
    # FigYearlyRechgGLUE.
    figstackmanager.stack.setCurrentIndex(0)
    figcanvas = figstackmanager.figmanagers[0].figcanvas
    assert '(GLUE 5) 363 mm/y' in figcanvas.txt_yearly_avg.get_text()
    assert '(GLUE 25) 415 mm/y' in figcanvas.txt_yearly_avg.get_text()
    assert '(GLUE 50) 484 mm/y' in figcanvas.txt_yearly_avg.get_text()
    assert '(GLUE 75) 578 mm/y' in figcanvas.txt_yearly_avg.get_text()
    assert '(GLUE 95) 709 mm/y' in figcanvas.txt_yearly_avg.get_text()

    # Assert the values are calculated as expected of the average
    # yearly water budget in FigAvgYearlyBudget.
    figstackmanager.stack.setCurrentIndex(2)
    figcanvas = figstackmanager.figmanagers[2].figcanvas

    assert figcanvas.notes[0].get_text() == '421'
    assert figcanvas.notes[1].get_text() == '226'
    assert figcanvas.notes[2].get_text() == '484'
    assert figcanvas.notes[3].get_text() == '1131'


def test_copy_to_clipboard(qtbot, figstackmanager, project):
    """
    Test that copying figures to the clipboard works as expected.
    """
    wldset = project.get_wldset('3040002_15min')
    figstackmanager.set_gluedf(wldset.get_glue_at(-1))

    for index in range(figstackmanager.stack.count()):
        figstackmanager.stack.setCurrentIndex(index)
        qtbot.wait(300)

        QApplication.clipboard().clear()
        assert QApplication.clipboard().text() == ''
        assert QApplication.clipboard().image().isNull()

        qtbot.mouseClick(
            figstackmanager.figmanagers[index].btn_copy_to_clipboard,
            Qt.LeftButton)

        assert not QApplication.clipboard().image().isNull()


if __name__ == "__main__":
    pytest.main(['-x', __file__, '-v', '-rw'])
