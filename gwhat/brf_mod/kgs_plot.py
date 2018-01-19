# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# Standard library imports:
# from datetime import datetime

# ---- Imports: third parties

import matplotlib as mpl
import numpy as np


class FigureLabels():
    LANGUAGES = ['english', 'french']

    def __init__(self, language):
        self.lag = 'Time Lag (days)'
        self.A = 'Cumulative Response Function'
        self.title = ('Well %s from %s to %s')

        if language.lower() == 'french':
            self.lag = 'Lag temporel (h)'
            self.A = 'Réponse barométrique cumulative'
            self.title = 'Puits %s du %s au %s'


class BRFFigure(mpl.figure.Figure):
    def __init__(self, lang='English'):
        super(BRFFigure, self).__init__()
        lang = lang if lang.lower() in FigureLabels.LANGUAGES else 'English'
        self.__figlang = lang
        self.__figlabels = FigureLabels(lang)

        # ---- Figure Creation

        fig_width = 8
        fig_height = 5

        self.set_size_inches(fig_width, fig_height)
        self.patch.set_facecolor('white')

        left_margin = 0.8
        right_margin = 0.25
        bottom_margin = 0.75
        top_margin = 0.25

        # ---- Axe Setup

        ax = self.add_axes([left_margin/fig_width, bottom_margin/fig_height,
                            1 - (left_margin + right_margin)/fig_width,
                            1 - (bottom_margin + top_margin)/fig_height],
                           zorder=1)
        ax.set_visible(False)

        # ---- Ticks Setup

        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')
        ax.tick_params(axis='both', which='major', direction='out',
                       gridOn=True)

        # ---- Axis Labels

        ax.set_xlabel(self.fig_labels.lag, fontsize=14, labelpad=8)
        ax.set_ylabel(self.fig_labels.A, fontsize=14)

        # ---- Artists Init

        self.line, = ax.plot([], [], ls='-', color='blue', linewidth=1.5,
                             zorder=20, clip_on=True)

        self.markers, = ax.plot([], [], color='0.1', mec='0.1', marker='.',
                                ls='None', ms=5, zorder=30, mew=1,
                                clip_on=False)

        self.errbar, = ax.plot([], [])

        offset = mpl.transforms.ScaledTranslation(
                0, -5/72, self.dpi_scale_trans)

        self.title = ax.text(0.5, 1, '', ha='center', va='top', fontsize=14,
                             transform=ax.transAxes+offset)

    @property
    def fig_labels(self):
        return self.__figlabels

    @property
    def fig_language(self):
        return self.__figlang

    def set_language(self, lang):
        """
        Sets the language of the figure labels and update the labels
        of the axis, but not the title of the figure.
        """
        lang = lang if lang.lower() in FigureLabels.LANGUAGES else 'English'
        self.__figlang = lang
        self.__figlabels = FigureLabels(lang)

        ax = self.axes[0]
        ax.set_xlabel(self.fig_labels.lag, fontsize=14, labelpad=8)
        ax.set_ylabel(self.fig_labels.A, fontsize=14)

    def empty_BRF(self):
        ax = self.axes[0]
        ax.set_visible(False)

    def plot_BRF(self, lag, A, err, date0, date1, well, msize=0,
                 draw_line=True, ylim=[None, None]):
        ax = self.axes[0]
        ax.set_visible(True)

        lag_max = np.max(lag)

        # ---- Ticks Setup

        TCKPOS = np.arange(0, max(lag_max+1, 10), 1)
        ax.set_xticks(TCKPOS)

        TCKPOS = np.arange(-10, 10, 0.2)
        ax.set_yticks(TCKPOS)

        # ---- Axis Limits

        if ylim[0] is None:
            if len(err) > 0:
                ymin = min(np.floor(np.min(A-err)/0.2)*0.2, 0)
            else:
                ymin = min(np.floor(np.min(A)/0.2)*0.2, 0)
        else:
            ymin = ylim[0]

        if ylim[1] is None:
            if len(err) > 0:
                ymax = max(np.ceil(np.max(A+err)/0.2)*0.2, 1)
            else:
                ymax = max(np.ceil(np.max(A)/0.2)*0.2, 1)
        else:
            ymax = ylim[1]

        ymin += -10**-12
        ymax += 10**-12

        ax.axis([0, lag_max, ymin, ymax])

        # ---- Update the data

        self.line.set_xdata(lag)
        self.line.set_ydata(A)
        self.line.set_visible(draw_line)

        self.markers.set_xdata(lag)
        self.markers.set_ydata(A)
        self.markers.set_markersize(msize)

        self.errbar.remove()
        if len(err) > 0:
            self.errbar = ax.fill_between(lag, A+err, A-err, edgecolor='0.65',
                                          color='0.75', clip_on=True)
        else:
            self.errbar, = ax.plot([], [])
        self.title.set_text(self.fig_labels.title % (well, date0, date1))
