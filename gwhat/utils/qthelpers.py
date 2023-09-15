# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

"""Extension of the Qt helpers module."""

from qtapputils import qthelpers
from qtapputils.qthelpers import *
from gwhat.utils.icons import ICOM


def create_toolbutton(*args, **kwargs):
    """
    Expand qtapputils function to accept string for the 'icon' and 'iconsize'
    arguments.
    """
    if len(args) >= 4 and isinstance(args[3], str):
        args[3] = ICOM.get_icon(args[3])
    elif 'icon' in kwargs and isinstance(kwargs['icon'], str):
        kwargs['icon'] = ICOM.get_icon(kwargs['icon'])

    if len(args) >= 10 and isinstance(args[9], str):
        args[9] = ICOM.get_iconsize(args[9])
    elif 'iconsize' in kwargs and isinstance(kwargs['iconsize'], str):
        kwargs['iconsize'] = ICOM.get_iconsize(kwargs['iconsize'])

    return qthelpers.create_toolbutton(*args, **kwargs)


def create_action(*args, **kwargs):
    """Expand qtapputils function to accept string for the 'icon' argument."""
    if len(args) >= 4 and isinstance(args[3], str):
        args[3] = ICOM.get_icon(args[3])
    elif 'icon' in kwargs and isinstance(kwargs['icon'], str):
        kwargs['icon'] = ICOM.get_icon(kwargs['icon'])
    return qthelpers.create_action(*args, **kwargs)
