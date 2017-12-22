# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

import os
from gwhat import __rootdir__
__install_dir__ = os.path.join(__rootdir__, 'brf_mod')

from gwhat.brf_mod.kgs_brf import (produce_BRFInputtxt, produce_par_file,
                                   run_kgsbrf, read_BRFOutput)
from gwhat.brf_mod.kgs_gui import BRFManager
