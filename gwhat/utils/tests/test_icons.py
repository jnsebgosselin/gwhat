# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © Sardes Project Contributors
# Copyright © Spyder Project Contributors
#
# This files is derived from code borrowed from the Spyder project, originally
# distributed under the MIT license.
# (https://github.com/spyder-ide/spyder)
#
# This file as a whole is part of Sardes and is distributed under the terms
# of the GNU General Public License.
# (https://github.com/cgq-qgc/sardes)
# -----------------------------------------------------------------------------


"""Tests for Sardes icons"""

# Third party imports
import pytest
from qtpy.QtGui import QIcon

# Local imports
from sardes.config.icons import LOCAL_ICONS, FA_ICONS, get_icon


def test_icon_mapping(qtbot):
    """
    Test that all the entries on the icon dicts for QtAwesome and
    local icons are valid.
    """

    # Check each entry of the dict and try to get the respective icon
    for name in FA_ICONS.keys():
        icon = get_icon(name)
        assert isinstance(icon, QIcon), name
        assert not icon.isNull(), name
    for name in LOCAL_ICONS.keys():
        icon = get_icon(name)
        assert isinstance(icon, QIcon), name
        assert not icon.isNull(), name


if __name__ == "__main__":
    pytest.main(['-x', __file__, '-v', '-rw'])
