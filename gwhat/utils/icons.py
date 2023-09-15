# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

# ---- Standard library imports
import os
import os.path as osp

from qtapputils.icons import IconManager
from qtapputils.colors import DEFAULT_ICON_COLOR
from gwhat.config.gui import GREEN, RED

# ---- Local imports
from gwhat import __rootdir__

DIRNAME = os.path.join(__rootdir__, 'ressources', 'icons_png')
GWHAT_ICONS = {
    'master': 'WHAT',
    'expand_range_vert': 'expand_range_vert',
    'calc_brf': 'start',
    'setup': 'page_setup',
    'openFolder': 'folder',
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
    'settings': 'settings',
    'staList': 'note',
    'add2list': 'add2list',
    'todate': 'calendar_todate',
    'fromdate': 'calendar_fromdate',
    'select_range': 'select_range',
    'toggleMode': 'toggleMode2',
    'undo': 'undo',
    'mrc_calc': 'MRCalc',
    'erase2': 'erase2',
    'showDataDots': 'show_datadots',
    'stratigraphy': 'stratigraphy',
    'recharge': 'recharge',
    'page_setup': 'page_setup',
    'fit_y': 'fit_y',
    'fit_x': 'fit_x',
    'save_graph_config': 'save_config',
    'load_graph_config': 'load_config',
    'closest_meteo': 'closest_meteo',
    'draw_hydrograph': 'stock_image',
    'meteo': 'meteo',
    'work': 'work',
    'color_picker': 'color_picker',
    'merge_data': 'merge_data',
    'fill_data': 'fill_data',
    'fill_all_data': 'fill_all_data',
    'showGrid': 'grid',
    'export_data': 'export-data',
    'show_glue_wl': 'show_glue_wl',
    'show_meteo': 'show_meteo',
    'manual_measures': 'manual_measures',
    'rect_select': 'rect_select',
    'rect_select_clear': 'rect_select_clear'
    }

LOCAL_ICONS = {
    key: osp.join(DIRNAME, val) for key, val in GWHAT_ICONS.items()}

QTA_ICONS = {
    'arrow_left': [
        ('mdi.arrow-left-thick',),
        {'scale_factor': 1.2}],
    'arrow_right': [
        ('mdi.arrow-right-thick',),
        {'scale_factor': 1.2}],
    'arrow_up': [
        ('mdi.arrow-up-thick',),
        {'scale_factor': 1.2}],
    'arrow_down': [
        ('mdi.arrow-down-thick',),
        {'scale_factor': 1.2}],
    'calendar': [
        ('mdi.calendar-question',),
        {'scale_factor': 1.3}],
    'clear_changes': [
        ('mdi.close-circle-outline',),
        {'color': RED, 'scale_factor': 1.3}],
    'close': [
        ('mdi.close-thick',),
        {'scale_factor': 1.3}],
    'close_all': [
        ('fa.close', 'fa.close', 'fa.close'),
        {'options': [{'scale_factor': 0.6,
                      'offset': (0.3, -0.3),
                      'color': DEFAULT_ICON_COLOR},
                     {'scale_factor': 0.6,
                      'offset': (-0.3, -0.3),
                      'color': DEFAULT_ICON_COLOR},
                     {'scale_factor': 0.6,
                      'offset': (0.3, 0.3),
                      'color': DEFAULT_ICON_COLOR}]}],
    'console': [
        ('mdi.console',),
        {'scale_factor': 1.3}],
    'content_duplicate': [
        ('mdi.content-duplicate',),
        {'scale_factor': 1.2}],
    'commit_changes': [
        ('mdi.check-circle-outline',),
        {'color': GREEN, 'scale_factor': 1.3}],
    'copy_clipboard': [
        ('mdi.content-copy',),
        {'scale_factor': 1.2}],
    'delete_data': [
        ('mdi.delete-forever',),
        {'scale_factor': 1.4}],
    'erase_data': [
        ('mdi.eraser',),
        {'scale_factor': 1.3}],
    'expand_all': [
        ('mdi.arrow-expand-all',),
        {'scale_factor': 1.3}],
    'folder_open': [
        ('mdi.folder-open',),
        {'scale_factor': 1.3}],
    'home': [
        ('mdi.home',),
        {'scale_factor': 1.3}],
    'info': [
        ('mdi.information-outline',),
        {'scale_factor': 1.3}],
    'information': [
        ('mdi.information-variant',),
        {'scale_factor': 1.3}],
    'language': [
        ('mdi.web',),
        {'scale_factor': 1.3}],
    'link': [
        ('mdi.link',),
        {'rotated': 90}],
    'link_off': [
        ('mdi.link-off',),
        {'rotated': 90}],
    'pencil_add': [
        ('mdi.pencil-plus',),
        {'scale_factor': 1.2}],
    'pencil_del': [
        ('mdi.pencil-minus',),
        {'scale_factor': 1.2}],
    'pan': [
        ('mdi.pan',),
        {'scale_factor': 1.3}],
    'play_start': [
        ('mdi.play',),
        {'color': GREEN, 'scale_factor': 1.5}],
    'report_bug': [
        ('mdi.bug',),
        {'scale_factor': 1.4}],
    'save': [
        ('fa.save',),
        {'scale_factor': 1.3}],
    'search': [
        ('fa5s.search',)],
    'square': [
        ('mdi.square-outline',),
        ],
    'tria_down': [
        ('mdi.triangle-outline',),
        {'rotated': 180}],
    'tria_up': [
        ('mdi.triangle-outline',),
        ],
    'undo_changes': [
        ('mdi.undo-variant',),
        {'scale_factor': 1.3}],
    'zoom_in': [
        ('mdi.plus-circle-outline',),
        {'scale_factor': 1.2}],
    'zoom_out': [
        ('mdi.minus-circle-outline',),
        {'scale_factor': 1.2}],
    'zoom_to_rect': [
        ('mdi.selection-search',),
        {'scale_factor': 1.2}],
    }

ICOM = IconManager(qta_icons=QTA_ICONS, local_icons=LOCAL_ICONS)

get_icon = ICOM.get_icon
get_iconsize = ICOM.get_iconsize
get_standard_icon = ICOM.get_standard_icon
get_standard_iconsize = ICOM.get_standard_iconsize
