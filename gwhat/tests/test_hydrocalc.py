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
from qtpy.QtWidgets import QApplication, QFileDialog, QMessageBox


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


def test_calc_mrc_if_empty(hydrocalc, tmp_path, qtbot, mocker):
    """
    Test that the tool to calculate the MRC is working as expected when
    no recession period is selected.

    Regression test for gwhat/issues#415
    """
    mrc_tool = hydrocalc.tools['mrc']
    assert len(mrc_tool._mrc_period_xdata) == 0

    qmsgbox_patcher = mocker.patch.object(
        QMessageBox, 'warning', return_value=QMessageBox.Ok)

    # Try to compute the MRC when no recession period is selected.
    qtbot.mouseClick(mrc_tool.btn_calc_mrc, Qt.LeftButton)
    assert qmsgbox_patcher.call_count == 1

    # Select one recession period on the hydrograph and compute the MRC.
    hydrocalc.tools['mrc'].add_mrcperiod(
        (41384.260416666664, 41414.114583333336))

    qtbot.mouseClick(mrc_tool.btn_calc_mrc, Qt.LeftButton)
    assert qmsgbox_patcher.call_count == 1

    # Clear all recession period and try computing the MRC again.
    qtbot.mouseClick(mrc_tool.btn_clear_periods, Qt.LeftButton)

    qtbot.mouseClick(mrc_tool.btn_calc_mrc, Qt.LeftButton)
    assert qmsgbox_patcher.call_count == 2


def test_calc_mrc(hydrocalc, tmp_path, qtbot, mocker):
    """
    Test that the tool to calculate the MRC is working as expected.
    """
    mrc_tool = hydrocalc.tools['mrc']

    assert hydrocalc.dformat == 1  # Matplotlib date format

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
        mrc_tool.add_mrcperiod(coord)

    mrc_data = hydrocalc.wldset.get_mrc()
    assert np.isnan(mrc_data['params']).all()
    assert len(mrc_data['peak_indx']) == 0
    assert len(mrc_data['recess']) == 0
    assert len(mrc_data['time']) == 0

    # Compute the MRC using the Exponential type.
    assert mrc_tool.cbox_mrc_type.currentText() == 'Exponential'
    qtbot.mouseClick(mrc_tool.btn_calc_mrc, Qt.LeftButton)

    mrc_data = hydrocalc.wldset.get_mrc()
    assert abs(mrc_data['params'][0] == 0.07004324034418882) < 10**-5
    assert abs(mrc_data['params'][1] == 0.25679183844863535) < 10**-5
    assert len(mrc_data['peak_indx']) == 7
    assert len(mrc_data['recess']) == 343
    assert len(mrc_data['time']) == 343
    assert np.sum(~np.isnan(mrc_data['recess'])) == 123

    # Compute the MRC using the Linear type.
    mrc_tool.cbox_mrc_type.setCurrentIndex(0)
    assert mrc_tool.cbox_mrc_type.currentText() == 'Linear'
    qtbot.mouseClick(mrc_tool.btn_calc_mrc, Qt.LeftButton)

    mrc_data = hydrocalc.wldset.get_mrc()
    assert mrc_data['params'][0] == 0
    assert abs(mrc_data['params'][1] - 0.019866789904866653) < 10**-5
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


def test_pan_axes(hydrocalc, tmp_path, qtbot, mocker):
    """
    Test that the tool to pan the axes with keyboard shortcuts is working
    as expected.
    """
    fig = hydrocalc.canvas.figure

    expected_xmin = 15655.9
    expected_xmax = 16032.1

    expected_ymin = 3.8955
    expected_ymax = 2.7344

    xoffset = (16032.1 - 15655.9) * 0.1
    yoffset = (3.90 - 2.73) * 0.025

    xmin, xmax = fig.axes[0].get_xlim()
    assert round(xmin, 1) == expected_xmin
    assert round(xmax, 1) == expected_xmax

    ymin, ymax = fig.axes[0].get_ylim()
    assert round(ymin, 4) == expected_ymin
    assert round(ymax, 4) == expected_ymax

    # Pan xaxis to the left.
    qtbot.keyPress(hydrocalc, Qt.Key_Left, modifier=Qt.ControlModifier)

    xmin, xmax = fig.axes[0].get_xlim()
    assert round(xmin, 1) == round(expected_xmin + xoffset, 1)
    assert round(xmax, 1) == round(expected_xmax + xoffset, 1)

    ymin, ymax = fig.axes[0].get_ylim()
    assert round(ymin, 4) == expected_ymin
    assert round(ymax, 4) == expected_ymax

    # Pan xaxis to the right (x2).
    qtbot.keyPress(hydrocalc, Qt.Key_Right, modifier=Qt.ControlModifier)
    qtbot.keyPress(hydrocalc, Qt.Key_Right, modifier=Qt.ControlModifier)

    xmin, xmax = fig.axes[0].get_xlim()
    assert round(xmin, 1) == round(expected_xmin - xoffset, 1)
    assert round(xmax, 1) == round(expected_xmax - xoffset, 1)

    ymin, ymax = fig.axes[0].get_ylim()
    assert round(ymin, 4) == expected_ymin
    assert round(ymax, 4) == expected_ymax

    # Pan yaxis up.
    qtbot.keyPress(hydrocalc, Qt.Key_Up, modifier=Qt.ControlModifier)

    xmin, xmax = fig.axes[0].get_xlim()
    assert round(xmin, 1) == round(expected_xmin - xoffset, 1)
    assert round(xmax, 1) == round(expected_xmax - xoffset, 1)

    ymin, ymax = fig.axes[0].get_ylim()
    assert round(ymin, 2) == round(expected_ymin + yoffset, 2)
    assert round(ymax, 2) == round(expected_ymax + yoffset, 2)

    # Pan yaxis down.
    qtbot.keyPress(hydrocalc, Qt.Key_Down, modifier=Qt.ControlModifier)
    qtbot.keyPress(hydrocalc, Qt.Key_Down, modifier=Qt.ControlModifier)

    xmin, xmax = fig.axes[0].get_xlim()
    assert round(xmin, 1) == round(expected_xmin - xoffset, 1)
    assert round(xmax, 1) == round(expected_xmax - xoffset, 1)

    ymin, ymax = fig.axes[0].get_ylim()
    assert round(ymin, 2) == round(expected_ymin - yoffset, 2)
    assert round(ymax, 2) == round(expected_ymax - yoffset, 2)


def test_zoom_in_axes(hydrocalc, tmp_path, qtbot, mocker):
    """
    Test that the tool to zoom the axes in with keyboard shortcuts is
    working as expected.
    """
    fig = hydrocalc.canvas.figure

    expected_xmin = 15655.9
    expected_xmax = 16032.1

    expected_ymin = 3.8955
    expected_ymax = 2.7344

    xoffset = (16032.1 - 15655.9) * 0.1
    yoffset = (3.90 - 2.73) * 0.025

    xmin, xmax = fig.axes[0].get_xlim()
    assert round(xmin, 1) == expected_xmin
    assert round(xmax, 1) == expected_xmax

    ymin, ymax = fig.axes[0].get_ylim()
    assert round(ymin, 4) == expected_ymin
    assert round(ymax, 4) == expected_ymax

    # Zoom xaxis in.
    qtbot.keyPress(hydrocalc, Qt.Key_Right,
                   modifier=Qt.ControlModifier | Qt.ShiftModifier)

    xmin, xmax = fig.axes[0].get_xlim()
    assert round(xmin, 1) == round(expected_xmin + xoffset, 1)
    assert round(xmax, 1) == round(expected_xmax - xoffset, 1)

    ymin, ymax = fig.axes[0].get_ylim()
    assert round(ymin, 4) == expected_ymin
    assert round(ymax, 4) == expected_ymax

    # Zoom yaxis in.
    qtbot.keyPress(hydrocalc, Qt.Key_Up,
                   modifier=Qt.ControlModifier | Qt.ShiftModifier)

    xmin, xmax = fig.axes[0].get_xlim()
    assert round(xmin, 1) == round(expected_xmin + xoffset, 1)
    assert round(xmax, 1) == round(expected_xmax - xoffset, 1)

    ymin, ymax = fig.axes[0].get_ylim()
    assert round(ymin, 2) == round(expected_ymin - yoffset, 2)
    assert round(ymax, 2) == round(expected_ymax + yoffset, 2)


def test_zoom_out_axes(hydrocalc, tmp_path, qtbot, mocker):
    """
    Test that the tool to zoom the axes out with keyboard shortcuts is
    working as expected.
    """
    fig = hydrocalc.canvas.figure

    expected_xmin = 15655.9
    expected_xmax = 16032.1

    expected_ymin = 3.8955
    expected_ymax = 2.7344

    xoffset = (16032.1 - 15655.9) * 0.1
    yoffset = (3.90 - 2.73) * 0.025

    xmin, xmax = fig.axes[0].get_xlim()
    assert round(xmin, 1) == expected_xmin
    assert round(xmax, 1) == expected_xmax

    ymin, ymax = fig.axes[0].get_ylim()
    assert round(ymin, 4) == expected_ymin
    assert round(ymax, 4) == expected_ymax

    # Zoom xaxis out.
    qtbot.keyPress(hydrocalc, Qt.Key_Left,
                   modifier=Qt.ControlModifier | Qt.ShiftModifier)

    xmin, xmax = fig.axes[0].get_xlim()
    assert round(xmin, 1) == round(expected_xmin - xoffset, 1)
    assert round(xmax, 1) == round(expected_xmax + xoffset, 1)

    ymin, ymax = fig.axes[0].get_ylim()
    assert round(ymin, 4) == expected_ymin
    assert round(ymax, 4) == expected_ymax

    # Zoom yaxis in.
    qtbot.keyPress(hydrocalc, Qt.Key_Down,
                   modifier=Qt.ControlModifier | Qt.ShiftModifier)

    xmin, xmax = fig.axes[0].get_xlim()
    assert round(xmin, 1) == round(expected_xmin - xoffset, 1)
    assert round(xmax, 1) == round(expected_xmax + xoffset, 1)

    ymin, ymax = fig.axes[0].get_ylim()
    assert round(ymin, 2) == round(expected_ymin + yoffset, 2)
    assert round(ymax, 2) == round(expected_ymax - yoffset, 2)


if __name__ == "__main__":
    pytest.main(['-x', __file__, '-v', '-rw'])
