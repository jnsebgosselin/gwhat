# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# Standard library imports
import sys
import os

# Third party imports
import pytest
from PyQt5.QtCore import Qt

# Local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from gwhat.HydroPrint2 import (HydroprintGUI, PageSetupWin, QFileDialog,
                               QMessageBox)
from gwhat.projet.manager_data import DataManager
from gwhat.projet.reader_projet import ProjetReader


# Qt Test Fixtures
# --------------------------------


working_dir = os.path.join(os.getcwd(), "@ new-prô'jèt!")
output_dir = os.path.join(working_dir, "Water Levels")


@pytest.fixture
def hydroprint_bot(qtbot):
    pf = os.path.join(working_dir, "@ new-prô'jèt!.gwt")
    pr = ProjetReader(pf)

    dm = DataManager()
    dm.set_projet(pr)

    hydroprint = HydroprintGUI(dm)
    qtbot.addWidget(hydroprint)
    qtbot.addWidget(hydroprint.page_setup_win)

    return hydroprint, qtbot


@pytest.fixture
def pagesetup_bot(qtbot):
    pagesetup_win = PageSetupWin()
    qtbot.addWidget(pagesetup_win)

    return pagesetup_win, qtbot


# Test HydroprintGUI
# -------------------------------


@pytest.mark.run(order=8)
def test_hydroprint_init(hydroprint_bot, mocker):
    hydroprint, qtbot = hydroprint_bot
    hydroprint.show()
    assert hydroprint

    # Assert that the water_level_measurement file was initialize correctly.
    filename = os.path.join(output_dir, "waterlvl_manual_measurements.csv")
    assert os.path.exists(filename)

    # Assert that the Page Setup Window is shown correctly.
    qtbot.mouseClick(hydroprint.btn_page_setup, Qt.LeftButton)
    qtbot.waitForWindowShown(hydroprint.page_setup_win)


@pytest.mark.run(order=8)
def test_autoplot_hydroprint(hydroprint_bot):
    hydroprint, qtbot = hydroprint_bot
    hydroprint.show()

    assert hydroprint.dmngr.wldsets_cbox.currentText() == "PO01 - Calixa-Lavallée"
    assert hydroprint.dmngr.wxdsets_cbox.currentText() == "IBERVILLE"

    # Forces a refresh of the graph and check that the automatic values
    # set for the axis is correct.

    hydroprint.wldset_changed()
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


@pytest.mark.run(order=8)
def test_zoomin_zoomout(hydroprint_bot):
    hydroprint, qtbot = hydroprint_bot
    hydroprint.show()
    hydroprint.wldset_changed()

    expected_values = [100, 120, 144, 172, 172]
    for expected_value in expected_values:
        assert hydroprint.zoom_disp.value() == expected_value
        hydroprint.zoom_in()
    expected_values = [172, 144, 120, 100, 83, 69, 57, 57]
    for expected_value in expected_values:
        assert hydroprint.zoom_disp.value() == expected_value
        hydroprint.zoom_out()


@pytest.mark.run(order=8)
def test_save_figure(hydroprint_bot, mocker):
    hydroprint, qtbot = hydroprint_bot
    hydroprint.show()
    hydroprint.wldset_changed()

    # Assert that the hydrograph is saved correctly.
    fname = os.path.join(os.getcwd(), "@ new-prô'jèt!", "test_hydrograph.pdf")
    mocker.patch.object(QFileDialog, 'getSaveFileName',
                        return_value=(fname, '*.pdf'))
    qtbot.mouseClick(hydroprint.btn_save, Qt.LeftButton)
    qtbot.waitUntil(lambda: os.path.exists(fname))

    fname = os.path.join(os.getcwd(), "@ new-prô'jèt!", "test_hydrograph.svg")
    mocker.patch.object(QFileDialog, 'getSaveFileName',
                        return_value=(fname, '*.svg'))
    qtbot.mouseClick(hydroprint.btn_save, Qt.LeftButton)
    qtbot.waitUntil(lambda: os.path.exists(fname))


@pytest.mark.run(order=8)
def test_graph_layout(hydroprint_bot, mocker):
    hydroprint, qtbot = hydroprint_bot
    hydroprint.show()
    hydroprint.wldset_changed()

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

    # Change some parameters values.
    hydroprint.dmngr.wxdsets_cbox.setCurrentIndex(0)
    assert hydroprint.dmngr.wxdsets_cbox.currentText() == "IBERVILLE"
    hydroprint.waterlvl_scale.setValue(0.2)
    hydroprint.waterlvl_max.setValue(3.5)
    hydroprint.NZGridWL_spinBox.setValue(10)
    hydroprint.datum_widget.setCurrentIndex(1)
    assert hydroprint.datum_widget.currentText() == 'Sea Level'

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
    assert layout['wxdset'] == hydroprint.dmngr.wxdsets_cbox.currentText() == "MARIEVILLE"
    assert layout['WLmin'] == hydroprint.waterlvl_max.value() == 3.75
    assert layout['WLscale'] == hydroprint.waterlvl_scale.value() == 0.25
    assert layout['RAINscale'] == 20
    assert layout['fwidth'] == 11
    assert layout['fheight'] == 7
    assert layout['va_ratio'] == 0.2
    assert layout['NZGrid'] == hydroprint.NZGridWL_spinBox.value() == 8
    assert layout['bwidth_indx'] == 1
    assert layout['date_labels_pattern'] == 2
    assert layout['datemode'] == 'Month'
    assert hydroprint.datum_widget.currentText() == 'Ground Surface'


@pytest.mark.run(order=8)
def test_clear_hydrograph(hydroprint_bot, mocker):
    """
    Test that the hydrograph is cleared correctly when the water level or
    weather dataset become None at some point.
    """
    hydroprint, qtbot = hydroprint_bot
    hydroprint.show()
    assert hydroprint.hydrograph.isHydrographExists is False

    hydroprint.wldset_changed()
    assert hydroprint.hydrograph.isHydrographExists is True

    empty_project = ProjetReader('empty_project.gwt')
    hydroprint.dmngr.set_projet(empty_project)

    assert hydroprint.hydrograph.isHydrographExists is False


# Test PageSetupWin
# -------------------------------

@pytest.mark.run(order=8)
def test_pagesetup(pagesetup_bot):  
    pagesetup_win, qtbot = pagesetup_bot
    pagesetup_win.show()

    # Assert the default values.
    assert pagesetup_win.fwidth.value() == pagesetup_win.pageSize[0] == 11
    assert pagesetup_win.fheight.value() == pagesetup_win.pageSize[1] == 7
    assert pagesetup_win.va_ratio_spinBox.value() == pagesetup_win.va_ratio == 0.2
    assert pagesetup_win.legend_on.isChecked() == pagesetup_win.isLegend == True
    assert pagesetup_win.trend_on.isChecked() == pagesetup_win.isTrendLine == False
    assert pagesetup_win.title_on.isChecked() == pagesetup_win.isGraphTitle == True

    # Test that previous values are kept when clicking on the button Cancel.
    pagesetup_win.fwidth.setValue(12.5)
    pagesetup_win.fheight.setValue(8.5)
    pagesetup_win.va_ratio_spinBox.setValue(0.7)
    pagesetup_win.legend_off.toggle()
    pagesetup_win.trend_on.toggle()
    pagesetup_win.title_off.toggle()

    qtbot.mouseClick(pagesetup_win.btn_cancel, Qt.LeftButton)
    assert pagesetup_win.fwidth.value() == pagesetup_win.pageSize[0] == 11
    assert pagesetup_win.fheight.value() == pagesetup_win.pageSize[1] == 7
    assert pagesetup_win.va_ratio_spinBox.value() == pagesetup_win.va_ratio == 0.2
    assert pagesetup_win.legend_on.isChecked() == pagesetup_win.isLegend == True
    assert pagesetup_win.trend_on.isChecked() == pagesetup_win.isTrendLine == False
    assert pagesetup_win.title_on.isChecked() == pagesetup_win.isGraphTitle == True
    assert not pagesetup_win.isVisible()
    
    # Test that the values are updated correctly when clicking the button OK.
    pagesetup_win.show()
    pagesetup_win.fwidth.setValue(12.5)
    pagesetup_win.fheight.setValue(8.5)
    pagesetup_win.va_ratio_spinBox.setValue(0.7)
    pagesetup_win.legend_off.toggle()
    pagesetup_win.trend_on.toggle()
    pagesetup_win.title_off.toggle()

    qtbot.mouseClick(pagesetup_win.btn_OK, Qt.LeftButton)
    assert pagesetup_win.fwidth.value() == pagesetup_win.pageSize[0] == 12.5
    assert pagesetup_win.fheight.value() == pagesetup_win.pageSize[1] == 8.5
    assert pagesetup_win.va_ratio_spinBox.value() == pagesetup_win.va_ratio == 0.7
    assert pagesetup_win.legend_on.isChecked() == pagesetup_win.isLegend == False
    assert pagesetup_win.trend_on.isChecked() == pagesetup_win.isTrendLine == True
    assert pagesetup_win.title_on.isChecked() == pagesetup_win.isGraphTitle == False
    assert not pagesetup_win.isVisible()

if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
#     pytest.main()
