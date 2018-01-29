# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# Standard library imports
import sys
import os
import os.path as osp
from shutil import copy2

# Third party imports
import pytest
from PyQt5.QtCore import Qt

# Local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from gwhat.brf_mod.kgs_gui import (BRFManager, KGSBRFInstaller, QMessageBox,
                                   QFileDialog)
from gwhat.projet.reader_projet import ProjetReader


# ---- Qt Test Fixtures

@pytest.fixture
def brf_manager_bot(qtbot):
    brf_manager = BRFManager(None)

    qtbot.addWidget(brf_manager)
    qtbot.addWidget(brf_manager.viewer)

    return brf_manager, qtbot


# ---- Test BRFManager

@pytest.mark.run(order=9)
@pytest.mark.skipif(os.environ.get('CI', None) is None,
                    reason="We do not want to run this locally")
def test_install_kgs_brf(brf_manager_bot, mocker):
    brf_manager, qtbot = brf_manager_bot
    brf_manager.show()
    assert brf_manager
    assert brf_manager.kgs_brf_installer

    # In Linux, a warning message will popup telling the user that this
    # feature is not supported for their system.
    mocker.patch.object(QMessageBox, 'warning', return_value=QMessageBox.Ok)

    # Install the KGS_BRF software and assert that it was correctly
    # installed and that the kgs_brf installer was uninstalled correctly.
    qtbot.mouseClick(brf_manager.kgs_brf_installer.install_btn, Qt.LeftButton)

    if os.name == 'nt':
        qtbot.waitUntil(lambda: brf_manager.kgs_brf_installer is None)
        assert KGSBRFInstaller().kgsbrf_is_installed()
    else:
        assert not KGSBRFInstaller().kgsbrf_is_installed()


@pytest.mark.run(order=9)
@pytest.mark.skipif(os.name == 'posix',
                    reason="This feature is not supported on Linux")
def test_run_kgs_brf(brf_manager_bot):
    brf_manager, qtbot = brf_manager_bot
    brf_manager.show()

    # Set the water level dataset and assert the expected values are displayed
    # correctly in the GUI.
    ppath = osp.join(os.getcwd(), "@ new-prô'jèt!", "@ new-prô'jèt!.gwt")
    projet = ProjetReader(ppath)
    wldset = projet.get_wldset(projet.wldsets[0])
    brf_manager.set_wldset(wldset)

    assert brf_manager.lagBP == 300
    assert brf_manager.lagET == 300
    assert brf_manager.detrend == 'Yes'
    assert brf_manager.correct_WL == 'No'
    assert brf_manager.brfperiod == (41241.0, 41584.0)

    brf_manager.set_datarange((41300.0, 41400.0))
    assert brf_manager.brfperiod == (41300.0, 41400.0)

    # Calcul the brf and assert the the results are plotted as expected.
    assert brf_manager.viewer.tbar.isEnabled() is False
    assert brf_manager.viewer.current_brf.value() == 0
    brf_manager.calc_brf()
    assert brf_manager.viewer.current_brf.value() == 1
    assert brf_manager.viewer.tbar.isEnabled()


# ---- Test BRFViewer

@pytest.mark.run(order=9)
@pytest.mark.skipif(os.name == 'posix',
                    reason="This feature is not supported on Linux")
def test_save_brf_figure(brf_manager_bot, mocker):
    """
    Test that the BRF figures are saved correctly from the GUI.
    """
    brf_manager, qtbot = brf_manager_bot
    brf_manager.show()

    # Set the water level dataset.
    ppath = osp.join(os.getcwd(), "@ new-prô'jèt!", "@ new-prô'jèt!.gwt")
    projet = ProjetReader(ppath)
    wldset = projet.get_wldset(projet.wldsets[0])
    brf_manager.set_wldset(wldset)

    qtbot.mouseClick(brf_manager.btn_show, Qt.LeftButton)
    qtbot.waitExposed(brf_manager.viewer)

    # Save the figure in the file system.
    filename = "brf_fig1.pdf"
    mocker.patch.object(QFileDialog, 'getSaveFileName',
                        return_value=(filename, "*.pdf"))

    qtbot.mouseClick(brf_manager.viewer.btn_save, Qt.LeftButton)
    qtbot.waitUntil(lambda: osp.exists(filename))
    os.remove(filename)


@pytest.mark.run(order=9)
@pytest.mark.skipif(os.name == 'posix',
                    reason="This feature is not supported on Linux")
def test_graph_panel(brf_manager_bot, mocker):
    brf_manager, qtbot = brf_manager_bot
    brf_manager.show()
    graph_opt_panel = brf_manager.viewer.graph_opt_panel

    # Set the water level dataset.
    ppath = osp.join(os.getcwd(), "@ new-prô'jèt!", "@ new-prô'jèt!.gwt")
    projet = ProjetReader(ppath)
    wldset = projet.get_wldset(projet.wldsets[0])
    brf_manager.set_wldset(wldset)

    qtbot.mouseClick(brf_manager.btn_show, Qt.LeftButton)
    qtbot.waitExposed(brf_manager.viewer)

    # Toggle on the panel and assert it is shown correctly.
    assert(graph_opt_panel.isVisible() is False)
    qtbot.mouseClick(brf_manager.viewer.btn_setp, Qt.LeftButton)
    assert(graph_opt_panel.isVisible())

    # Assert the default values for the y-axis :

    assert(graph_opt_panel.ymin is None)
    assert(graph_opt_panel.ymax is None)
    assert(graph_opt_panel.yscale is None)

    graph_opt_panel._ylim['auto'].setChecked(False)
    assert(graph_opt_panel.ymin == 0)
    assert(graph_opt_panel.ymax == 1)

    # Assert the default values for the x-axis :

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

    # Assert when the value of time_units change :

    graph_opt_panel._xlim['units'].setCurrentIndex(0)
    assert(graph_opt_panel.time_units == 'hours')
    assert(graph_opt_panel.xmin == 0)
    assert(graph_opt_panel._xlim['min'].value() == 0)
    assert(graph_opt_panel.xmax == 1)
    assert(graph_opt_panel._xlim['max'].value() == 24)
    assert(graph_opt_panel.xscale == 1)
    assert(graph_opt_panel._xlim['scale'].value() == 24)

    # Assert the default values for the artists :

    assert graph_opt_panel.show_ebar is True
    assert graph_opt_panel.draw_line is False
    assert graph_opt_panel.markersize == 5

    # Toggle off the panel and assert it is hidden correctly.
    qtbot.mouseClick(brf_manager.viewer.btn_setp, Qt.LeftButton)
    assert(brf_manager.viewer.graph_opt_panel.isVisible() is False)


@pytest.mark.run(order=9)
@pytest.mark.skipif(os.name == 'posix',
                    reason="This feature is not supported on Linux")
def test_del_brf_result(brf_manager_bot, mocker):
    """
    Test that the BRF figures are saved correctly from the GUI.
    """
    brf_manager, qtbot = brf_manager_bot
    brf_manager.show()

    # Set the water level dataset.
    ppath = osp.join(os.getcwd(), "@ new-prô'jèt!", "@ new-prô'jèt!.gwt")
    projet = ProjetReader(ppath)
    wldset = projet.get_wldset(projet.wldsets[0])
    brf_manager.set_wldset(wldset)

    # Delete the brf and assert the GUI is updated as expected.
    assert brf_manager.viewer.current_brf.value() == 1
    qtbot.mouseClick(brf_manager.viewer.btn_del, Qt.LeftButton)
    assert brf_manager.viewer.current_brf.value() == 0
    assert brf_manager.viewer.tbar.isEnabled() is False


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
    # pytest.main()
