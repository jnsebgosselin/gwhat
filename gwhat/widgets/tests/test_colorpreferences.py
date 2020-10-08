# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------


# ---- Standard library imports
import os
os.environ['GWHAT_PYTEST'] = 'True'

# ---- Third party imports
import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

# ---- Local imports
from gwhat.widgets.colorpreferences import (
    ColorsManager, ColorPreferencesDialog, QColorDialog)


# =============================================================================
# ---- Pytest Fixtures
# =============================================================================
@pytest.fixture
def color_preferences_dialog(qtbot):
    # We want to reset the color preferences to default so that each test
    # can run independently one from another.
    colors_manager = ColorsManager()
    colors_manager.reset_defaults()
    colors_manager.save_colors()

    # Create a wldset object from a file.
    dialog = ColorPreferencesDialog()
    qtbot.addWidget(dialog)
    dialog.show()
    return dialog


# =============================================================================
# ---- Tests
# =============================================================================
def test_load_colors(color_preferences_dialog, qtbot):
    """
    Test that the color prefenreces dialog is loading the colors from
    the configs as expected.
    """
    colors_manager = ColorsManager()
    for key, button in color_preferences_dialog._color_buttons.items():
        button_rgb = list(button.palette().base().color().getRgb()[:-1])
        assert button_rgb == colors_manager.RGB[key]


def test_pick_color(color_preferences_dialog, qtbot, mocker):
    """
    Test that picking a new color is working as expected.
    """
    colors_manager = ColorsManager()

    # Pick a new color for the 'Rain' button.
    mocker.patch.object(
        QColorDialog, 'getColor', return_value=QColor(24, 25, 26))
    clicked_button = color_preferences_dialog._color_buttons['Rain']
    qtbot.mouseClick(clicked_button, Qt.LeftButton)

    # Assert that the picked color was applid to the 'Rain' button.
    clicked_button_rgb = list(
        clicked_button.palette().base().color().getRgb()[:-1])
    assert clicked_button_rgb == [24, 25, 26]

    # Assert that the new picked color was not saved to the configs.
    colors_manager.load_colors()
    assert colors_manager.RGB['Rain'] == [23, 52, 88]


def test_accept_new_colors(color_preferences_dialog, qtbot, mocker):
    """
    Test that the colors displayed in the dialog are correctly saved
    in the config when they are accepted by the user.
    """
    # Change the colors for the 'Rain' and 'Snow' buttons.
    color_preferences_dialog._color_buttons['Rain'].setStyleSheet(
        "background-color: rgb(%i,%i,%i)" % (1, 2, 3))
    color_preferences_dialog._color_buttons['Snow'].setStyleSheet(
        "background-color: rgb(%i,%i,%i)" % (4, 5, 6))

    # Assert that clicking the Ok button save the new colors to the
    # configs and close the dialog.
    qtbot.mouseClick(color_preferences_dialog.btn_ok, Qt.LeftButton)

    colors_manager = ColorsManager()
    assert colors_manager.RGB['Rain'] == [1, 2, 3]
    assert colors_manager.RGB['Snow'] == [4, 5, 6]
    assert not color_preferences_dialog.isVisible()


def test_reset_defaults(color_preferences_dialog, qtbot, mocker):
    """
    Test that resetting the colors to their default values is working
    as expected.
    """
    # Change the colors for the 'Rain' and 'Snow' buttons.
    color_preferences_dialog._color_buttons['Rain'].setStyleSheet(
        "background-color: rgb(%i,%i,%i)" % (1, 2, 3))
    color_preferences_dialog._color_buttons['Snow'].setStyleSheet(
        "background-color: rgb(%i,%i,%i)" % (4, 5, 6))

    # Assert that clicking the Apply button save the new colors to the
    # configs and does NOT the dialog.
    qtbot.mouseClick(color_preferences_dialog.btn_apply, Qt.LeftButton)

    colors_manager = ColorsManager()
    assert colors_manager.RGB['Rain'] == [1, 2, 3]
    assert colors_manager.RGB['Snow'] == [4, 5, 6]
    assert color_preferences_dialog.isVisible()

    # Reset the colors to their default values and assert that the color
    # for the 'Rain' and 'Snow' button was changed correctly.
    qtbot.mouseClick(color_preferences_dialog.btn_reset, Qt.LeftButton)

    assert list(
        color_preferences_dialog._color_buttons['Rain']
        .palette().base().color().getRgb()[:-1]
        ) == [23, 52, 88]
    assert list(
        color_preferences_dialog._color_buttons['Snow']
        .palette().base().color().getRgb()[:-1]
        ) == [165, 165, 165]

    # Assert that the default colors were not saved to the configs.
    colors_manager = ColorsManager()
    assert colors_manager.RGB['Rain'] == [1, 2, 3]
    assert colors_manager.RGB['Snow'] == [4, 5, 6]


def test_cancel_color_changes(color_preferences_dialog, qtbot, mocker):
    """
    Test that cancelling changes made to the color preferences is working as
    expected.
    """
    # Pick a new color for the 'Rain' button.
    mocker.patch.object(
        QColorDialog, 'getColor', return_value=QColor(24, 25, 26))
    rain_button = color_preferences_dialog._color_buttons['Rain']
    qtbot.mouseClick(rain_button, Qt.LeftButton)

    assert list(
        color_preferences_dialog._color_buttons['Rain']
        .palette().base().color().getRgb()[:-1]
        ) == [24, 25, 26]

    # Cancel the changes.
    qtbot.mouseClick(color_preferences_dialog.btn_cancel, Qt.LeftButton)
    assert not color_preferences_dialog.isVisible()

    colors_manager = ColorsManager()
    assert colors_manager.RGB['Rain'] == [23, 52, 88]

    # Show back the color preferences dialog and assert that the color for the
    # rain button was resetted to its initial value as expected.
    color_preferences_dialog.show()
    assert list(
        color_preferences_dialog._color_buttons['Rain']
        .palette().base().color().getRgb()[:-1]
        ) == [23, 52, 88]


if __name__ == "__main__":
    pytest.main(['-x', __file__, '-v', '-rw'])
