# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © SARDES Project Contributors
# https://github.com/cgq-qgc/sardes
#
# This file is part of SARDES.
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

"""
Tests for the dialogs.py module.
"""

# ---- Third party imports
import pytest
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication

# ---- Local imports
from gwhat import get_versions, __namever__
from gwhat.widgets.dialogs import ExceptDialog, EXCEPT_DIALOG_MSG_CANVAS


# =============================================================================
# ---- Fixtures
# =============================================================================
@pytest.fixture
def log_msg():
    return 'test_log_message'


@pytest.fixture
def except_dialog(qtbot, log_msg):
    except_dialog = ExceptDialog(log_msg)
    return except_dialog


# =============================================================================
# ---- Tests
# =============================================================================
def test_except_dialog(except_dialog, log_msg, qtbot):
    versions = get_versions()
    expected_msg = EXCEPT_DIALOG_MSG_CANVAS.format(
        namever=__namever__,
        python_ver=versions['python'],
        bitness=versions['bitness'],
        qt_ver=versions['qt'],
        qt_api=versions['qt_api'],
        qt_api_ver=versions['qt_api_ver'],
        os_name=versions['system'],
        os_ver=versions['release'],
        log_msg=log_msg)
    assert except_dialog.get_error_infotext() == expected_msg

    # Test that copying the error info to the clipboard is working as
    # expected.
    QApplication.clipboard().clear()
    assert QApplication.clipboard().text() == ''
    qtbot.mouseClick(except_dialog.copy_btn, Qt.LeftButton)
    assert QApplication.clipboard().text() == expected_msg


if __name__ == "__main__":
    pytest.main(['-x', __file__, '-v', '-rw', '-s'])
