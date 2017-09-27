# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 01:50:50 2017
@author: jsgosselin
"""

# ---- Standard library imports

import sys
import os.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

# ---- Third parties imports

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget

# ---- Local imports

from widgets.tabwidget import TabWidget                                # nopep8


# Qt Test Fixtures
# --------------------------------


@pytest.fixture
def tabwidget_bot(qtbot):
    tabwidget = TabWidget()
    tabwidget.addTab(QWidget(), 'Tab#1')
    tabwidget.addTab(QWidget(), 'Tab#2')
    tabwidget.addTab(QWidget(), 'Tab#3')

    tabwidget.aboutwhat.setModal(False)

    qtbot.addWidget(tabwidget)

    return tabwidget, qtbot

# Tests
# -------------------------------


def test_tabwidget_and_about_window(tabwidget_bot):
    tabwidget, qtbot = tabwidget_bot
    tabwidget.show()

    qtbot.mouseClick(tabwidget.about_btn, Qt.LeftButton)
    assert tabwidget.aboutwhat.isVisible()
    tabwidget.aboutwhat.close()


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


if __name__ == "__main__":                                   # pragma: no cover
    pytest.main([os.path.basename(__file__)])
    # pytest.main()
