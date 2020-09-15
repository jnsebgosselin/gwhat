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

# ---- Third party imports
from appconfigs.user import UserConfig
from appconfigs.base import get_config_dir

# ---- Local imports
from gwhat import __appname__


CONFIG_DIR = get_config_dir(__appname__)
if bool(os.environ.get('GWHAT_PYTEST')):
    CONFIG_DIR += '_pytest'

DEFAULTS = [
    ('main',
        {'fontsize_global': 14,
         'fontsize_console': 12,
         'fontsize_menubar': 12,
         'last_project_filepath': '../Projects/Example/Example.gwt'
         }
     ),
    ('brf',
        {'graphs_labels_language': 'english'}
     ),
]


# =============================================================================
# Config instance
# =============================================================================
# IMPORTANT NOTES:
# 1. If you want to *change* the default value of a current option, you need to
#    do a MINOR update in config version, e.g. from 3.0.0 to 3.1.0
# 2. If you want to *remove* options that are no longer needed in our codebase,
#    or if you want to *rename* options, then you need to do a MAJOR update in
#    version, e.g. from 3.0.0 to 4.0.0
# 3. You don't need to touch this value if you're just adding a new option
CONF_VERSION = '1.0.0'

# Setup the main configuration instance.
LOAD = False if bool(os.environ.get('GWHAT_PYTEST')) else True
try:
    CONF = UserConfig('gwhat', defaults=DEFAULTS, load=LOAD,
                      version=CONF_VERSION, path=CONFIG_DIR,
                      backup=True, raw_mode=True)
except Exception:
    CONF = UserConfig('gwhat', defaults=DEFAULTS, load=False,
                      version=CONF_VERSION, path=CONFIG_DIR,
                      backup=True, raw_mode=True)
