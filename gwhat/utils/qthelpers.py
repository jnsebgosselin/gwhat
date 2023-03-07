# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

"""Extension of the Qt helpers module."""

from apputils.qthelpers import *
import apputils.qthelpers

# ---- Local library imports
from gwhat.utils.icons import get_icon


def create_toolbutton(*args, **kwargs):
    """
    Extend create_toolbutton so that we can pass the name of an
    icon instead of a QIcon object.
    """
    if len(args) >= 3 and isinstance(args[4], str):
        args[4] = get_icon(args[4])
    if 'icon' in kwargs and isinstance(kwargs['icon'], str):
        kwargs['icon'] = get_icon(kwargs['icon'])
    return apputils.qthelpers.create_toolbutton(*args, **kwargs)


def create_action(*args, **kwargs):
    """
    Extend create_action so that we can pass the name of an
    icon instead of a QIcon object.
    """
    if len(args) >= 3 and isinstance(args[4], str):
        args[4] = get_icon(args[4])
    if 'icon' in kwargs and isinstance(kwargs['icon'], str):
        kwargs['icon'] = get_icon(kwargs['icon'])
    return apputils.qthelpers.create_action(*args, **kwargs)
