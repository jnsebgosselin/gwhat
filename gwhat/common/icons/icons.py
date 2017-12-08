# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

from __future__ import division, unicode_literals

# ---- Imports: standard libraries

import os

# ---- Imports: third parties

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QToolButton

dirname = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Icons')


class IconDB(object):
    def __init__(self):
        self.iconSize = QSize(32, 32)
        self.iconSize2 = QSize(20, 20)

        self.banner = os.path.join(dirname, 'WHAT_banner_750px.png')
        self.master = QIcon(os.path.join(dirname, 'WHAT'))
        self.info = QIcon(os.path.join(dirname, 'info'))

        self.calc_brf = QIcon(os.path.join(dirname, 'start'))
        self.setup = QIcon(os.path.join(dirname, 'page_setup'))
        self.new_project = QIcon(os.path.join(dirname, 'new_project'))
        self.openFolder = QIcon(os.path.join(dirname, 'folder'))
        self.openFile = QIcon(os.path.join(dirname, 'open_file'))
        self.clear = QIcon(os.path.join(dirname, 'clear-search'))
        self.importFile = QIcon(os.path.join(dirname, 'open_project'))
        self.download = QIcon(os.path.join(dirname, 'download'))

        self.tridown = QIcon(os.path.join(dirname, 'triangle_down'))
        self.triright = QIcon(os.path.join(dirname, 'triangle_right'))

        self.go_previous = QIcon(os.path.join(dirname, 'go-previous'))
        self.go_next = QIcon(os.path.join(dirname, 'go-next'))
        self.go_last = QIcon(os.path.join(dirname, 'go-last'))
        self.go_first = QIcon(os.path.join(dirname, 'go-first'))
        self.go_up = QIcon(os.path.join(dirname, 'go-up'))

        self.play = QIcon(os.path.join(dirname, 'start'))
        self.forward = QIcon(os.path.join(dirname, 'start_all'))

        self.refresh = QIcon(os.path.join(dirname, 'refresh'))

        self.stop = QIcon(os.path.join(dirname, 'process-stop'))
        self.search = QIcon(os.path.join(dirname, 'search'))
        self.settings = QIcon(os.path.join(dirname, 'settings'))

        # ---- Download Weather Data

        self.staList = QIcon(os.path.join(dirname, 'note'))
        self.plus_sign = QIcon(os.path.join(dirname, 'plus_sign'))
        self.add2list = QIcon(os.path.join(dirname, 'add2list'))
        self.todate = QIcon(os.path.join(dirname, 'calendar_todate'))
        self.fromdate = QIcon(os.path.join(dirname, 'calendar_fromdate'))

        # ---- BRF

        self.select_range = QIcon(os.path.join(dirname, 'select_range'))

        # ---- HydroCalc

        self.zoom_out = QIcon(os.path.join(dirname, 'zoom_out'))
        self.zoom_in = QIcon(os.path.join(dirname, 'zoom_in'))

        # ---- Hydrograph Toolbar

        self.toggleMode = QIcon(os.path.join(dirname, 'toggleMode2'))

        self.undo = QIcon(os.path.join(dirname, 'undo'))
        self.clear_search = QIcon(os.path.join(dirname, 'clear-search'))
        self.home = QIcon(os.path.join(dirname, 'home'))
        self.MRCalc = QIcon(os.path.join(dirname, 'MRCalc'))
        self.edit = QIcon(os.path.join(dirname, 'edit'))
        self.pan = QIcon(os.path.join(dirname, 'pan'))
        self.add_point = QIcon(os.path.join(dirname, 'add_point'))
        self.erase = QIcon(os.path.join(dirname, 'erase'))
        self.erase2 = QIcon(os.path.join(dirname, 'erase2'))
        self.findPeak = QIcon(os.path.join(dirname, 'find_peak'))
        self.findPeak2 = QIcon(os.path.join(dirname, 'find_peak2'))
        self.showDataDots = QIcon(os.path.join(dirname, 'show_datadots'))

        self.stratigraphy = QIcon(os.path.join(dirname, 'stratigraphy'))
        self.recharge = QIcon(os.path.join(dirname, 'recharge'))
        self.calendar = QIcon(os.path.join(dirname, 'Calendar'))

        self.page_setup = QIcon(os.path.join(dirname, 'page_setup'))
        self.fit_y = QIcon(os.path.join(dirname, 'fit_y'))
        self.fit_x = QIcon(os.path.join(dirname, 'fit_x'))
        self.save_graph_config = QIcon(os.path.join(dirname, 'save_config'))
        self.load_graph_config = QIcon(os.path.join(dirname, 'load_config'))

        self.closest_meteo = QIcon(os.path.join(dirname, 'closest_meteo'))

        self.draw_hydrograph = QIcon(os.path.join(dirname, 'stock_image'))
        self.save = QIcon(os.path.join(dirname, 'save'))
        self.meteo = QIcon(os.path.join(dirname, 'meteo'))

        self.work = QIcon(os.path.join(dirname, 'work'))
        self.color_picker = QIcon(os.path.join(dirname, 'color_picker'))

        # ---- Fill Weather Data

        self.merge_data = QIcon(os.path.join(dirname, 'merge_data'))
        self.fill_data = QIcon(os.path.join(dirname, 'fill_data'))
        self.fill_all_data = QIcon(os.path.join(dirname, 'fill_all_data'))

        # ---- Weather Averages

        self.showGrid = QIcon(os.path.join(dirname, 'grid'))
        self.export_data = QIcon(os.path.join(dirname, 'export-data'))


class QToolButtonBase(QToolButton):
    def __init__(self, Qicon, *args, **kargs):
        super(QToolButtonBase, self).__init__(*args, **kargs)

        self.setIcon(Qicon)
        self.setAutoRaise(True)
        self.setFocusPolicy(Qt.NoFocus)

#        name = str(id(self))
#        self.setObjectName(name)
#        ss = ("#%s {"
#              "background-color: transparent;"
#              "}"
#              "#%s:hover {"
#              "background-color: rgba(0, 0, 0, 35);"
#              "}"
#              "#%s:pressed {"
#              "background-color: rgba(0, 0, 0, 85);"
#              "}") % (name, name, name)
#
#        self.setStyleSheet(ss)


class QToolButtonNormal(QToolButtonBase):
    def __init__(self, Qicon, *args, **kargs):
        super(QToolButtonNormal, self).__init__(Qicon, *args, **kargs)
        self.setIconSize(QSize(28, 28))


class QToolButtonSmall(QToolButtonBase):
    def __init__(self, Qicon, *args, **kargs):
        super(QToolButtonSmall, self).__init__(Qicon, *args, **kargs)
        self.setIconSize(QSize(20, 20))
