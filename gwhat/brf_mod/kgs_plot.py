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


class FigureLabels(object):
    LANGUAGES = ['english', 'french']

    def __init__(self, language):
        if language.lower() == 'french':
            self.lag = 'Lag temporel (jours)'
            self.lag_hr = 'Lag temporel (heures)'
            self.A = 'Réponse barométrique cumulative'
            self.title = 'Puits %s du %s au %s'
        else:
            self.lag = 'Time Lag (days)'
            self.lag_hr = 'Time Lag (hours)'
            self.A = 'Cumulative Response Function'
            self.title = ('Well %s from %s to %s')


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

    def empty_BRF(self):
        ax = self.axes[0]
        ax.set_visible(False)

    def plot_BRF(self, lag, A, err, date0, date1, well, msize=0,
                 draw_line=True, ylim=[None, None], xlim=[None, None],
                 time_units='auto', xscl=None, yscl=None):
        ax = self.axes[0]
        ax.set_visible(True)

        # ---- Xticks labels time_units

        if time_units not in ['days', 'hours', 'auto']:
            raise ValueError("time_units value must be either :",
                             ['days', 'hours', 'auto'])
        if time_units == 'auto':
            time_units = 'days' if np.max(lag) >= 2 else 'hours'
        if time_units == 'hours':
            lag = lag * 24
            xlim[0] = None if xlim[0] is None else xlim[0]*24
            xlim[1] = None if xlim[1] is None else xlim[1]*24

        # ---- Axis Labels

        if time_units == 'hours':
            ax.set_xlabel(self.fig_labels.lag_hr, fontsize=14, labelpad=8)
        else:
            ax.set_xlabel(self.fig_labels.lag, fontsize=14, labelpad=8)

        ax.set_ylabel(self.fig_labels.A, fontsize=14)

        # ---- Axis Limits

        xmin = 0 if xlim[0] is None else xlim[0]
        xmax = np.max(lag) if xlim[1] is None else xlim[1]

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

        # ---- Xticks ans Yticks Setup

        yscl = 0.2 if yscl is None else yscl
        ax.set_yticks(np.arange(ymin, ymax+yscl, yscl))

        if time_units == 'hours':
            # We want the ticks to be a multiple of 24.
            if xscl is None:
                if np.floor(xmax) > 24*7:
                    xscl = 24
                elif np.floor(xmax) > 48:
                    xscl = 12
                elif np.floor(xmax) > 12:
                    xscl = 4
                else:
                    xscl = 1
            else:
                xscl *= 24
        elif time_units == 'days':
            if xscl is None:
                xscl = 1
        ax.set_xticks(np.arange(xmin, xmax+xscl, xscl))

        ax.axis([xmin, xmax+10**-12, ymin-10**-12, ymax+10**-12])

        # ---- Update the data

        self.line.set_xdata(lag)
        self.line.set_ydata(A)
        self.line.set_visible(draw_line)

        indexes = np.where((lag >= xmin) & (lag <= xmax) &
                           (A >= ymin) & (A <= ymax)
                           )[0]

        self.markers.set_xdata(lag[indexes])
        self.markers.set_ydata(A[indexes])
        self.markers.set_markersize(msize)

        self.errbar.remove()
        if len(err) > 0:
            self.errbar = ax.fill_between(lag, A+err, A-err, edgecolor='0.65',
                                          color='0.75', clip_on=True)
        else:
            self.errbar, = ax.plot([], [])
        self.title.set_text(self.fig_labels.title % (well, date0, date1))
