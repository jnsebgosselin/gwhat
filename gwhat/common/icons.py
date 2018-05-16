# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

from __future__ import division, unicode_literals

# ---- Imports: standard libraries

import os

# ---- Imports: third parties

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QToolButton

from gwhat import __rootdir__

dirname = os.path.join(__rootdir__, 'ressources', 'icons_png')
ICON_NAMES = {'master': 'WHAT',
              'expand_range_vert': 'expand_range_vert',
              'info': 'info',
              'calc_brf': 'start',
              'setup': 'page_setup',
              'new_project': 'new_project',
              'openFolder': 'folder',
              'openFile': 'open_file',
              'clear': 'clear-search',
              'importFile': 'open_project',
              'download': 'download',
              'tridown': 'triangle_down',
              'triright': 'triangle_right',
              'go_previous': 'go-previous',
              'go_next': 'go-next',
              'go_last': 'go-last',
              'go_first': 'go-first',
              'go_up': 'go-up',
              'play': 'start',
              'forward': 'start_all',
              'refresh': 'refresh',
              'stop': 'process-stop',
              'search': 'search',
              'settings': 'settings',
              'staList': 'note',
              'plus_sign': 'plus_sign',
              'add2list': 'add2list',
              'todate': 'calendar_todate',
              'fromdate': 'calendar_fromdate',
              'select_range': 'select_range',
              'zoom_out': 'zoom_out',
              'zoom_in': 'zoom_in',
              'toggleMode': 'toggleMode2',
              'undo': 'undo',
              'clear_search': 'clear-search',
              'home': 'home',
              'mrc_calc': 'MRCalc',
              'edit': 'edit',
              'pan': 'pan',
              'add_point': 'add_point',
              'erase': 'erase',
              'erase2': 'erase2',
              'findPeak': 'find_peak',
              'findPeak2': 'find_peak2',
              'showDataDots': 'show_datadots',
              'stratigraphy': 'stratigraphy',
              'recharge': 'recharge',
              'calendar': 'Calendar',
              'page_setup': 'page_setup',
              'fit_y': 'fit_y',
              'fit_x': 'fit_x',
              'save_graph_config': 'save_config',
              'load_graph_config': 'load_config',
              'closest_meteo': 'closest_meteo',
              'draw_hydrograph': 'stock_image',
              'save': 'save',
              'meteo': 'meteo',
              'work': 'work',
              'color_picker': 'color_picker',
              'merge_data': 'merge_data',
              'fill_data': 'fill_data',
              'fill_all_data': 'fill_all_data',
              'showGrid': 'grid',
              'export_data': 'export-data',
              'zoom_to_rect': 'zoom_to_rect',
              'show_glue_wl': 'show_glue_wl',
              'show_meteo': 'show_meteo'}

ICON_SIZES = {'large': (32, 32),
              'normal': (28, 28),
              'small': (20, 20)}


def get_icon(name):
    return QIcon(os.path.join(dirname, ICON_NAMES[name]))


def get_iconsize(size):
    return QSize(*ICON_SIZES[size])


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
        self.setIconSize(get_iconsize('normal'))


class QToolButtonSmall(QToolButtonBase):
    def __init__(self, Qicon, *args, **kargs):
        super(QToolButtonSmall, self).__init__(Qicon, *args, **kargs)
        self.setIconSize(get_iconsize('small'))


class QToolButtonVRectSmall(QToolButtonBase):
    def __init__(self, Qicon, *args, **kargs):
        super(QToolButtonVRectSmall, self).__init__(Qicon, *args, **kargs)
        self.setIconSize(QSize(8, 20))
