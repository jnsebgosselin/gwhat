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
from qtpy.QtWidgets import QMessageBox

# ---- Local imports
from gwhat.widgets.updates import WorkerUpdates, ManagerUpdates
import gwhat.widgets.updates


# =============================================================================
# ---- Fixtures
# =============================================================================
@pytest.fixture
def update_worker(qtbot):
    update_worker = WorkerUpdates()
    return update_worker


@pytest.fixture
def update_manager(qtbot):
    update_manager = ManagerUpdates()
    return update_manager


# =============================================================================
# ---- Tests
# =============================================================================
@flaky(max_runs=3)
def test_worker_updates(update_worker, qtbot):
    """
    Assert that the worker to check for updates on the GitHub API is
    working as expected.
    """
    gwhat.widgets.updates.__version__ = "0.1.0"
    update_worker.start()
    assert update_worker.error is None
    assert update_worker.update_available is True

    gwhat.widgets.updates.__version__ = "0.1.0.dev"
    update_worker.start()
    assert update_worker.error is None
    assert update_worker.update_available is False

    gwhat.widgets.updates.__version__ = "10.0.0"
    update_worker.start()
    assert update_worker.error is None
    assert update_worker.update_available is False


@flaky(max_runs=3)
def test_update_manager(update_manager, qtbot, mocker):
    """
    Test that the widget to check for updates on the GitHub API is
    working as expected.
    """
    qmsgbox_patcher = mocker.patch.object(
        QMessageBox, 'exec_', return_value=QMessageBox.Ok)

    with qtbot.waitSignal(update_manager.thread_updates.finished):
        update_manager.start_updates_check()
    qtbot.waitUntil(
        lambda: not update_manager.thread_updates.isRunning(),
        timeout=10000)

    assert qmsgbox_patcher.call_count == 1


if __name__ == "__main__":
    pytest.main(['-x', __file__, '-v', '-rw'])
