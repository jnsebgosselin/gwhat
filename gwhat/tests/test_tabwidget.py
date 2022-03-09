# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

# ---- Standard library imports
import sys
import os
import os.path as osp
sys.path.append(osp.dirname(osp.dirname(osp.realpath(__file__))))

# ---- Third parties imports
import pytest
from flaky import flaky
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget

# ---- Local imports
from gwhat.widgets.tabwidget import TabWidget
from gwhat.widgets.updates import WorkerUpdates
import gwhat.widgets.updates


# =============================================================================
# ---- Fixtures
# =============================================================================
@pytest.fixture
def tabwidget_bot(qtbot):
    tabwidget = TabWidget()
    tabwidget.addTab(QWidget(), 'Tab#1')
    tabwidget.addTab(QWidget(), 'Tab#2')
    tabwidget.addTab(QWidget(), 'Tab#3')

    qtbot.addWidget(tabwidget)

    return tabwidget, qtbot


@pytest.fixture
def worker_updates_bot(qtbot):
    worker_updates = WorkerUpdates()
    return worker_updates, qtbot


# =============================================================================
# ---- Tests
# =============================================================================
@flaky(max_runs=3)
@pytest.mark.skipif(not os.name == 'nt', reason="It fails often on Travis")
def test_worker_updates(worker_updates_bot):
    """
    Assert that the worker to check for updates on the GitHub API is
    working as expected.
    """
    worker_updates, qtbot = worker_updates_bot

    gwhat.widgets.updates.__version__ = "0.1.0"
    worker_updates.start()
    qtbot.waitSignal(worker_updates.sig_ready)
    assert worker_updates.error is None
    assert worker_updates.update_available is True

    gwhat.widgets.updates.__version__ = "0.1.0.dev"
    worker_updates.start()
    qtbot.waitSignal(worker_updates.sig_ready)
    assert worker_updates.error is None
    assert worker_updates.update_available is False

    gwhat.widgets.updates.__version__ = "10.0.0"
    worker_updates.start()
    qtbot.waitSignal(worker_updates.sig_ready)
    assert worker_updates.error is None
    assert worker_updates.update_available is False


@flaky(max_runs=3)
def test_update_manager(tabwidget_bot):
    tabwidget, qtbot = tabwidget_bot
    tabwidget.show()

    # Show about window.
    qtbot.mouseClick(tabwidget.about_btn, Qt.LeftButton)
    qtbot.addWidget(tabwidget.about_win)

    # Click on the button to check for updates and assert that the manager
    # is initialized and showed correctly.
    assert tabwidget.about_win.manager_updates is None

    qtbot.mouseClick(tabwidget.about_win.btn_check_updates, Qt.LeftButton)
    assert tabwidget.about_win.manager_updates
    qtbot.addWidget(tabwidget.about_win.manager_updates)

    qtbot.waitSignal(
        tabwidget.about_win.manager_updates.thread_updates.started)
    qtbot.waitSignal(
        tabwidget.about_win.manager_updates.worker_updates.sig_ready)
    qtbot.waitSignal(
        tabwidget.about_win.manager_updates.thread_updates.finished)
    qtbot.waitUntil(
        lambda: not tabwidget.about_win.manager_updates.thread_updates.isRunning(),
        timeout=10000)


def test_tabwidget_index_memory(tabwidget_bot):
    tabwidget, qtbot = tabwidget_bot
    tabwidget.show()

    tabbar = tabwidget.tabBar()
    assert tabbar.previousIndex() == -1
    tabbar.setCurrentIndex(1)
    assert tabbar.previousIndex() == 0
    tabbar.setCurrentIndex(2)
    assert tabbar.previousIndex() == 1
    tabbar.setCurrentIndex(0)
    assert tabbar.previousIndex() == 2


if __name__ == "__main__":
    pytest.main(['-x', osp.basename(__file__), '-v', '-rw'])
    # pytest.main()
