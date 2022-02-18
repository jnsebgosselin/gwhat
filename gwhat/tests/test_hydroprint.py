# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

# ---- Standard Libraries Imports
import os
import os.path as osp

# ---- Third Party Libraries Imports
import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication


# ---- Local Libraries Imports
from gwhat.meteo.weather_reader import WXDataFrame
from gwhat.projet.reader_waterlvl import WLDataFrame
from gwhat.HydroPrint2 import (HydroprintGUI, PageSetupWin, QFileDialog,
                               QMessageBox)
from gwhat.projet.manager_data import DataManager
from gwhat.projet.reader_projet import ProjetReader

DATADIR = osp.join(osp.dirname(osp.realpath(__file__)), 'data')
WXFILENAMES = (
    osp.join(DATADIR, "IBERVILLE (7023270)_2000-2015.out"),
    osp.join(DATADIR, "L'ACADIE (702LED4)_2000-2015.out"),
    osp.join(DATADIR, "MARIEVILLE (7024627)_2000-2015.out")
    )
WLFILENAME = osp.join(DATADIR, 'sample_water_level_datafile.csv')


# ---- Pytest Fixtures
@pytest.fixture(scope="module")
def projectpath(tmp_path_factory):
    return tmp_path_factory.mktemp("project_test_hydroprint")


@pytest.fixture(scope="module")
def project(projectpath):
    # Create a project and add add the wldset to it.
    project = ProjetReader(
        osp.join(projectpath, "project_test_hydroprint.gwt"))

    # Add the weather datasets to the project.
    for wxfilename in WXFILENAMES:
        wxdset = WXDataFrame(wxfilename)
        project.add_wxdset(wxdset.metadata['Station Name'], wxdset)

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
def hydroprint(datamanager, qtbot):
    hydroprint = HydroprintGUI(datamanager)
    qtbot.addWidget(hydroprint)
    qtbot.addWidget(hydroprint.page_setup_win)
    hydroprint.wldset_changed()
    hydroprint.show()
    return hydroprint


@pytest.fixture
def pagesetup(qtbot):
    pagesetup = PageSetupWin()
    qtbot.addWidget(pagesetup)
    pagesetup.show()
    return pagesetup


# ---- Test HydroprintGUI
def test_hydroprint_page_setup(hydroprint, mocker, qtbot, projectpath):
    """Test the Page Setup Window is shown correctly."""
    qtbot.mouseClick(hydroprint.btn_page_setup, Qt.LeftButton)
    qtbot.waitForWindowShown(hydroprint.page_setup_win)


def test_autoplot_hydroprint(hydroprint):
    """Test the default values set when autoplotting the data."""
    assert (hydroprint.dmngr.wldsets_cbox.currentText() ==
            "PO01 - Calixa-Lavallée")
    assert hydroprint.dmngr.wxdsets_cbox.currentText() == "MARIEVILLE"
    assert hydroprint.waterlvl_scale.value() == 0.25
    assert hydroprint.waterlvl_max.value() == 3.75
    assert hydroprint.NZGridWL_spinBox.value() == 8
    assert hydroprint.datum_widget.currentText() == 'Ground Surface'
    data_start = hydroprint.date_start_widget.date()
    assert data_start.day() == 1
    assert data_start.month() == 11
    assert data_start.year() == 2012
    data_end = hydroprint.date_end_widget.date()
    assert data_end.day() == 1
    assert data_end.month() == 12
    assert data_end.year() == 2013
    assert hydroprint.time_scale_label.currentText() == "Month"


def test_zoomin_zoomout(hydroprint):
    """Test zooming in and out the graph."""
    # Test zoom in.
    expected_values = [100, 120, 144, 173, 173]
    for expected_value in expected_values:
        assert hydroprint.zoom_disp.value() == expected_value
        hydroprint.zoom_in()

    # Test zoom out.
    expected_values = [173, 144, 120, 100, 83, 69, 58, 58]
    for expected_value in expected_values:
        assert hydroprint.zoom_disp.value() == expected_value
        hydroprint.zoom_out()


@pytest.mark.parametrize('fext', ['.png', '.pdf', '.svg'])
def test_save_hydrograph_fig(hydroprint, mocker, qtbot, fext, tmp_path):
    """
    Test that saving the hydrograph figure to disk is working as
    expected.
    """
    fname = osp.join(tmp_path, "test_hydrograph" + fext)
    mocker.patch.object(
        QFileDialog,
        'getSaveFileName',
        return_value=(fname, '*{}'.format(fext)))
    qtbot.mouseClick(hydroprint.btn_save, Qt.LeftButton)
    qtbot.waitUntil(lambda: osp.exists(fname))


def test_copy_to_clipboard(hydroprint, qtbot):
    """
    Test that puting a copy of the hydrograph figure on the clipboard is
    working as expected.
    """
    QApplication.clipboard().clear()
    assert QApplication.clipboard().text() == ''
    assert QApplication.clipboard().image().isNull()
    qtbot.mouseClick(hydroprint.btn_copy_to_clipboard, Qt.LeftButton)
    assert not QApplication.clipboard().image().isNull()


def test_graph_layout(hydroprint, mocker, qtbot):
    """Test saving and loading hydrograph layout to and from the project."""
    # Save the graph layout.
    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes)
    qtbot.mouseClick(hydroprint.btn_save_layout, Qt.LeftButton)

    layout = hydroprint.wldset.get_layout()
    assert type(layout) == dict
    assert layout['legend_on'] is True
    assert layout['title_on'] is True
    assert layout['trend_line'] is False
    assert layout['wxdset'] == "MARIEVILLE"
    assert layout['WLmin'] == 3.75
    assert layout['WLscale'] == 0.25
    assert layout['RAINscale'] == 20
    assert layout['fwidth'] == 11
    assert layout['fheight'] == 7
    assert layout['va_ratio'] == 0.2
    assert layout['NZGrid'] == 8
    assert layout['bwidth_indx'] == 1
    assert layout['date_labels_pattern'] == 2
    assert layout['datemode'] == 'Month'
    assert layout['language'] == 'english'

    # Change some parameters values.
    hydroprint.dmngr.wxdsets_cbox.setCurrentIndex(0)
    assert hydroprint.dmngr.wxdsets_cbox.currentText() == "IBERVILLE"
    hydroprint.waterlvl_scale.setValue(0.2)
    hydroprint.waterlvl_max.setValue(3.5)
    hydroprint.NZGridWL_spinBox.setValue(10)
    hydroprint.datum_widget.setCurrentIndex(1)
    assert hydroprint.datum_widget.currentText() == 'Sea Level'
    hydroprint.btn_language.set_language('french')
    assert hydroprint.btn_language.language == 'french'

    # Click to save the layout, but cancel the operation.
    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.No)
    qtbot.mouseClick(hydroprint.btn_save_layout, Qt.LeftButton)

    # Load the graph layout.
    qtbot.mouseClick(hydroprint.btn_load_layout, Qt.LeftButton)
    layout = hydroprint.wldset.get_layout()
    assert type(layout) == dict
    assert layout['legend_on'] is True
    assert layout['title_on'] is True
    assert layout['trend_line'] is False
    assert layout['wxdset'] == "MARIEVILLE"
    assert hydroprint.dmngr.wxdsets_cbox.currentText() == "MARIEVILLE"
    assert layout['WLmin'] == 3.75
    assert hydroprint.waterlvl_max.value() == 3.75
    assert layout['WLscale'] == 0.25
    assert hydroprint.waterlvl_scale.value() == 0.25
    assert layout['RAINscale'] == 20
    assert layout['fwidth'] == 11
    assert layout['fheight'] == 7
    assert layout['va_ratio'] == 0.2
    assert layout['NZGrid'] == 8
    assert hydroprint.NZGridWL_spinBox.value() == 8
    assert layout['bwidth_indx'] == 1
    assert layout['date_labels_pattern'] == 2
    assert layout['datemode'] == 'Month'
    assert layout['language'] == 'english'
    assert hydroprint.btn_language.language == 'english'
    assert hydroprint.datum_widget.currentText() == 'Ground Surface'


def test_clear_hydrograph(hydroprint, mocker, tmp_path):
    """
    Test that the hydrograph is cleared correctly when the water level or
    weather dataset become None at some point.
    """
    assert hydroprint.hydrograph.isHydrographExists is True
    empty_project = ProjetReader(osp.join(tmp_path, "empty_project.gwt"))
    hydroprint.dmngr.set_projet(empty_project)
    assert hydroprint.hydrograph.isHydrographExists is False


# ---- Test PageSetupWin
def test_pagesetup_defaults(pagesetup):
    """Assert that the default values are as expected."""
    assert pagesetup.fwidth.value() == 11
    assert pagesetup.pageSize[0] == 11

    assert pagesetup.fheight.value() == 7
    assert pagesetup.pageSize[1] == 7

    assert pagesetup.va_ratio_spinBox.value() == 0.2
    assert pagesetup.va_ratio == 0.2

    assert pagesetup.legend_on.value() is True
    assert pagesetup.isLegend is True
    assert pagesetup.wltrend_on.value() is False
    assert pagesetup.isTrendLine is False
    assert pagesetup.title_on.value() is True
    assert pagesetup.isGraphTitle is True
    assert pagesetup.meteo_on.value() is True
    assert pagesetup.is_meteo_on is True


def test_pagesetup_cancel(pagesetup, qtbot):
    """Test that the Cancel button is working as expected."""
    # Change the default values.
    pagesetup.fwidth.setValue(12.5)
    pagesetup.fheight.setValue(8.5)
    pagesetup.va_ratio_spinBox.setValue(0.7)

    pagesetup.legend_on.set_value(False)
    pagesetup.wltrend_on.set_value(True)
    pagesetup.title_on.set_value(False)
    pagesetup.meteo_on.set_value(False)

    # Assert that previous values are kept when clicking on the button Cancel.
    qtbot.mouseClick(pagesetup.btn_cancel, Qt.LeftButton)
    assert pagesetup.fwidth.value() == 11
    assert pagesetup.pageSize[0] == 11

    assert pagesetup.fheight.value() == 7
    assert pagesetup.pageSize[1] == 7

    assert pagesetup.va_ratio_spinBox.value() == 0.2
    assert pagesetup.va_ratio == 0.2

    assert pagesetup.legend_on.value() is True
    assert pagesetup.isLegend is True
    assert pagesetup.wltrend_on.value() is False
    assert pagesetup.isTrendLine is False
    assert pagesetup.title_on.value() is True
    assert pagesetup.isGraphTitle is True
    assert pagesetup.meteo_on.value() is True
    assert pagesetup.is_meteo_on is True

    assert not pagesetup.isVisible()


def test_pagesetup_ok(pagesetup, qtbot):
    """Test that the OK button is working as expected."""
    # Change the default values.
    pagesetup.show()
    pagesetup.fwidth.setValue(12.5)
    pagesetup.fheight.setValue(8.5)
    pagesetup.va_ratio_spinBox.setValue(0.7)

    pagesetup.legend_on.set_value(False)
    pagesetup.wltrend_on.set_value(True)
    pagesetup.title_on.set_value(False)
    pagesetup.meteo_on.set_value(False)

    # Assert that the values are updated correctly when clicking the button OK.
    qtbot.mouseClick(pagesetup.btn_OK, Qt.LeftButton)
    assert pagesetup.fwidth.value() == 12.5
    assert pagesetup.pageSize[0] == 12.5

    assert pagesetup.fheight.value() == 8.5
    assert pagesetup.pageSize[1] == 8.5

    assert pagesetup.va_ratio_spinBox.value() == 0.7
    assert pagesetup.va_ratio == 0.7

    assert pagesetup.legend_on.value() is False
    assert pagesetup.isLegend is False
    assert pagesetup.wltrend_on.value() is True
    assert pagesetup.isTrendLine is True
    assert pagesetup.title_on.value() is False
    assert pagesetup.isGraphTitle is False
    assert pagesetup.meteo_on.value() is False
    assert pagesetup.is_meteo_on is False

    assert not pagesetup.isVisible()


if __name__ == "__main__":
    pytest.main(['-x', __file__, '-v', '-rw'])
