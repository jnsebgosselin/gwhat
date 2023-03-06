# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

"""Qt utilities"""

from __future__ import annotations

from apputils.qthelpers import *
from apputils import qthelpers
from gwhat.utils.icons import get_icon


def create_toolbutton(*args, **kwargs):
    """Create a QToolButton with the provided settings."""
    if len(args) >= 3 and isinstance(args[4], str):
        args[4] = get_icon(args[4])
    if 'icon' in kwargs and isinstance(kwargs['icon'], str):
        kwargs['icon'] = get_icon(kwargs['icon'])
    return qthelpers.create_toolbutton(*args, **kwargs)


def create_action(*args, **kwargs):
    """Create a QToolButton with the provided settings."""
    if len(args) >= 3 and isinstance(args[4], str):
        args[4] = get_icon(args[4])
    if 'icon' in kwargs and isinstance(kwargs['icon'], str):
        kwargs['icon'] = get_icon(kwargs['icon'])
    return qthelpers.create_action(*args, **kwargs)
