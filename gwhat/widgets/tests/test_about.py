# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

# ---- Third parties imports
import pytest
from flaky import flaky
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QMessageBox

# ---- Local imports
from gwhat.widgets.about import AboutWhat


# =============================================================================
# ---- Fixtures
# =============================================================================
@pytest.fixture
def about_dialog(qtbot):
    about_dialog = AboutWhat()
    about_dialog.show()
    qtbot.waitExposed(about_dialog)
    qtbot.addWidget(about_dialog)
    return about_dialog


# =============================================================================
# ---- Tests
# =============================================================================
@flaky(max_runs=3)
def test_about_dialog_updates(about_dialog, qtbot, mocker):
    """
    Test that the button to check for updates in the Aoubt GWHAT dialog
    is working as expected.
    """
    assert about_dialog.manager_updates is None

    # Click on the button to check for updates and assert that the manager
    # is initialized and showed correctly.
    mocker.patch.object(QMessageBox, 'exec_', return_value=QMessageBox.Ok)

    qtbot.mouseClick(about_dialog.btn_check_updates, Qt.LeftButton)
    assert about_dialog.manager_updates

    qtbot.waitSignal(
        about_dialog.manager_updates.thread_updates.started)
    qtbot.waitSignal(
        about_dialog.manager_updates.worker_updates.sig_ready)
    qtbot.waitSignal(
        about_dialog.manager_updates.thread_updates.finished)
    qtbot.waitUntil(
        lambda: not about_dialog.manager_updates.thread_updates.isRunning(),
        timeout=10000)


if __name__ == "__main__":
    pytest.main(['-x', __file__, '-v', '-rw'])
