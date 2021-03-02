# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

"""Qt utilities"""

# ---- Third party imports
from PyQt5.QtCore import QByteArray, Qt, QSize
from PyQt5.QtWidgets import QWidget, QSizePolicy, QToolButton

from gwhat.utils.icons import get_icon


def qbytearray_to_hexstate(qba):
    """Convert QByteArray object to a str hexstate."""
    return str(bytes(qba.toHex().data()).decode())


def hexstate_to_qbytearray(hexstate):
    """Convert a str hexstate to a QByteArray object."""
    return QByteArray().fromHex(str(hexstate).encode('utf-8'))


def create_toolbar_stretcher():
    """Create a stretcher to be used in a toolbar """
    stretcher = QWidget()
    stretcher.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    return stretcher


def create_toolbutton(parent, text=None, shortcut=None, icon=None, tip=None,
                      toggled=None, triggered=None,
                      autoraise=True, text_beside_icon=False, iconsize=None):
    """Create a QToolButton with the provided settings."""
    button = QToolButton(parent)

    if text is not None:
        button.setText(text)

    if icon is not None:
        icon = get_icon(icon) if isinstance(icon, str) else icon
        button.setIcon(icon)

    if tip is not None:
        button.setToolTip(tip)

    if text_beside_icon:
        button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

    button.setAutoRaise(autoraise)

    if triggered is not None:
        button.clicked.connect(triggered)

    if toggled is not None:
        button.toggled.connect(toggled)
        button.setCheckable(True)

    if shortcut is not None:
        if isinstance(shortcut, (list, tuple)):
            for sc in shortcut:
                button.setShortcut(sc)
        else:
            button.setShortcut(shortcut)

    if iconsize is not None:
        button.setIconSize(QSize(iconsize, iconsize))

    return button
