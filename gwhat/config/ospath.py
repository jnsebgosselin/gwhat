# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

# ---- Standard imports
import os
import os.path as osp

# ---- Third party imports
from gwhat.config.main import CONF
from gwhat import __rootdir__


def save_path_to_configs(section, option, path):
    """
    Save a path in the config file for the specified section and option.
    """
    path = osp.abspath(path)
    path = path.replace('\\', '/')
    CONF.set(section, option, path)


def get_path_from_configs(section, option):
    """
    Return a path saved in the config file at the specified section and option.
    """
    # We need to change the working directory in case this function is not
    # called from mainwindow.py.
    cwd = os.getcwd()
    os.chdir(__rootdir__)
    abspath = osp.abspath(osp.normpath(CONF.get(section, option)))
    os.chdir(cwd)
    return abspath
