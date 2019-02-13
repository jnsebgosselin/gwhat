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
import pytest
from PyQt5.QtCore import Qt

# Local imports
from gwhat.brf_mod.kgs_gui import (BRFManager, KGSBRFInstaller, QMessageBox,
                                   QFileDialog)
from gwhat.projet.reader_projet import ProjetReader
from gwhat.projet.reader_waterlvl import WLDataFrame


# ---- Pytest Fixtures

@pytest.fixture(scope="module")
def project(tmp_path_factory):
    # Create a project and add add the wldset to it.
    basetemp = tmp_path_factory.getbasetemp()
    return ProjetReader(osp.join(basetemp, "brf_test.gwt"))


@pytest.fixture(scope="module")
def wldataset(project):
    """Return a water level dataset object that is saved in a GWHAT project."""
    # Create a wldset object from a file.
    rootpath = osp.dirname(osp.realpath(__file__))
    filepath = osp.join(rootpath, 'data', 'sample_water_level_datafile.csv')
    wldset = WLDataFrame(filepath)

    # Add the wldset to the project.
    project.add_wldset('test_brf_wldset', wldset)

    return project.get_wldset(project.wldsets[0])


@pytest.fixture
def brfmanager(qtbot):
    brfmanager = BRFManager(None)
    qtbot.addWidget(brfmanager)
    qtbot.addWidget(brfmanager.viewer)
    return brfmanager


# ---- Tests BRFManager
@pytest.mark.skipif(os.environ.get('CI', None) is None,
                    reason="We do not want to run this locally")
def test_install_kgs_brf(brfmanager, mocker, qtbot):
    """Test the installation of the kgs_brf software."""
    brfmanager.show()
    assert brfmanager
    assert brfmanager.kgs_brf_installer

    # In Linux, a warning message will popup telling the user that this
    # feature is not supported for their system.
    mocker.patch.object(QMessageBox, 'warning', return_value=QMessageBox.Ok)

    # Install the KGS_BRF software and assert that it was correctly
    # installed and that the kgs_brf installer was uninstalled correctly.
    qtbot.mouseClick(brfmanager.kgs_brf_installer.install_btn, Qt.LeftButton)

    if os.name == 'nt':
        qtbot.waitUntil(lambda: brfmanager.kgs_brf_installer is None)
        assert KGSBRFInstaller().kgsbrf_is_installed()
    else:
        assert not KGSBRFInstaller().kgsbrf_is_installed()


@pytest.mark.skipif(os.name == 'posix',
                    reason="This feature is not supported on Linux")
def test_kgs_brf_defaults(brfmanager, wldataset, qtbot):
    """
    Assert that the default values are set as expected when setting
    the water level dataset.
    """
    assert wldataset.get_brfperiod() == [None, None]
    brfmanager.set_wldset(wldataset)
    assert wldataset.get_brfperiod() == [41334.0, 41425.0]

    assert brfmanager.nlag_baro == 100
    assert brfmanager.nlag_earthtides == 100
    assert brfmanager.detrend_waterlevels is True
    assert brfmanager.correct_waterlevels is True
    assert brfmanager.get_brfperiod() == [41334.0, 41425.0]


@pytest.mark.skipif(os.name == 'posix',
                    reason="This feature is not supported on Linux")
def test_set_brfperiod(brfmanager, wldataset, qtbot):
    """
    Test that setting the period in the manager correctly set the values
    in the GUI and save them in the dataset HDF5 file.
    """
    brfmanager.set_wldset(wldataset)

    # Set the period of which the BRF will be evaluated.
    expected_brfperiod = [41384.0, 41416.0]
    brfmanager.set_brfperiod(expected_brfperiod)
    assert brfmanager.get_brfperiod() == expected_brfperiod
    assert wldataset.get_brfperiod() == expected_brfperiod


@pytest.mark.skipif(os.name == 'posix',
                    reason="This feature is not supported on Linux")
def test_calcul_brf(brfmanager, wldataset, qtbot):
    """Calcul the brf and assert the the results are plotted as expected."""
    brfmanager.show()
    brfmanager.set_wldset(wldataset)
    assert brfmanager.get_brfperiod() == [41384.0, 41416.0]

    assert brfmanager.viewer.tbar.isEnabled() is False
    assert brfmanager.viewer.current_brf.value() == 0
    brfmanager.calc_brf()
    assert brfmanager.viewer.current_brf.value() == 1
    assert brfmanager.viewer.tbar.isEnabled()


# ---- Tests BRFViewer

@pytest.mark.skipif(os.name == 'posix',
                    reason="This feature is not supported on Linux")
def test_save_brf_figure(brfmanager, wldataset, mocker, qtbot,
                         tmp_path_factory):
    """Test that the BRF figures are saved correctly from the GUI."""
    brfmanager.show()
    brfmanager.set_wldset(wldataset)

    qtbot.mouseClick(brfmanager.btn_show, Qt.LeftButton)
    qtbot.waitExposed(brfmanager.viewer)

    # Save the figure in the file system.
    filename = osp.join(tmp_path_factory.getbasetemp(), "brf_fig1.pdf")
    mocker.patch.object(
        QFileDialog, 'getSaveFileName', return_value=(filename, "*.pdf"))

    qtbot.mouseClick(brfmanager.viewer.btn_save, Qt.LeftButton)
    qtbot.waitUntil(lambda: osp.exists(filename))
    os.remove(filename)


@pytest.mark.skipif(os.name == 'posix',
                    reason="This feature is not supported on Linux")
def test_graph_panel(brfmanager, wldataset, mocker, qtbot):
    brfmanager.show()
    brfmanager.set_wldset(wldataset)

    graph_opt_panel = brfmanager.viewer.graph_opt_panel

    qtbot.mouseClick(brfmanager.btn_show, Qt.LeftButton)
    qtbot.waitExposed(brfmanager.viewer)

    # Toggle on the panel and assert it is shown correctly.
    assert(graph_opt_panel.isVisible() is False)
    qtbot.mouseClick(brfmanager.viewer.btn_setp, Qt.LeftButton)
    assert(graph_opt_panel.isVisible())

    # Assert the default values for the y-axis.
    assert(graph_opt_panel.ymin is None)
    assert(graph_opt_panel.ymax is None)
    assert(graph_opt_panel.yscale is None)

    graph_opt_panel._ylim['auto'].setChecked(False)
    assert(graph_opt_panel.ymin == 0)
    assert(graph_opt_panel.ymax == 1)

    # Assert the default values for the x-axis.
    assert(graph_opt_panel.xmin is None)
    assert(graph_opt_panel.xmax is None)
    assert(graph_opt_panel.xscale is None)
    assert(graph_opt_panel.time_units is 'auto')

    graph_opt_panel._xlim['auto'].setChecked(False)
    assert(graph_opt_panel.xmin == 0)
    assert(graph_opt_panel._xlim['min'].value() == 0)
    assert(graph_opt_panel.xmax == 1)
    assert(graph_opt_panel._xlim['max'].value() == 1)
    assert(graph_opt_panel.xscale == 1)
    assert(graph_opt_panel._xlim['scale'].value() == 1)
    assert(graph_opt_panel.time_units == 'days')

    # Assert when the value of time_units change.
    graph_opt_panel._xlim['units'].setCurrentIndex(0)
    assert(graph_opt_panel.time_units == 'hours')
    assert(graph_opt_panel.xmin == 0)
    assert(graph_opt_panel._xlim['min'].value() == 0)
    assert(graph_opt_panel.xmax == 1)
    assert(graph_opt_panel._xlim['max'].value() == 24)
    assert(graph_opt_panel.xscale == 1)
    assert(graph_opt_panel._xlim['scale'].value() == 24)

    # Assert the default values for the artists.
    assert graph_opt_panel.show_ebar is True
    assert graph_opt_panel.draw_line is False
    assert graph_opt_panel.markersize == 5

    # Toggle off the panel and assert it is hidden correctly.
    qtbot.mouseClick(brfmanager.viewer.btn_setp, Qt.LeftButton)
    assert(brfmanager.viewer.graph_opt_panel.isVisible() is False)


@pytest.mark.skipif(os.name == 'posix',
                    reason="This feature is not supported on Linux")
def test_del_brf_result(brfmanager, wldataset, mocker, qtbot):
    """Test that the BRF results are deleted correctly."""
    brfmanager.show()
    brfmanager.set_wldset(wldataset)

    # Delete the brf and assert the GUI is updated as expected.
    assert brfmanager.viewer.current_brf.value() == 1
    qtbot.mouseClick(brfmanager.viewer.btn_del, Qt.LeftButton)
    assert brfmanager.viewer.current_brf.value() == 0
    assert brfmanager.viewer.tbar.isEnabled() is False


@pytest.mark.skipif(os.name == 'posix',
                    reason="This feature is not supported on Linux")
def test_del_all_brf_result(brfmanager, wldataset, mocker, qtbot):
    """Test that the BRF results are deleted correctly."""
    brfmanager.show()
    brfmanager.set_wldset(wldataset)

    # Create BRF results X2.
    assert brfmanager.viewer.current_brf.value() == 0
    brfmanager.calc_brf()
    brfmanager.calc_brf()
    assert brfmanager.viewer.current_brf.value() == 2

    # Click to delete all BRF results, but answer No.
    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.No)
    qtbot.mouseClick(brfmanager.viewer.btn_del_all, Qt.LeftButton)
    assert brfmanager.viewer.current_brf.value() == 2

    # Click to delete all BRF results and answer Yes.
    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes)
    qtbot.mouseClick(brfmanager.viewer.btn_del_all, Qt.LeftButton)
    assert brfmanager.viewer.current_brf.value() == 0
    assert brfmanager.viewer.tbar.isEnabled() is False


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
    # pytest.main()
