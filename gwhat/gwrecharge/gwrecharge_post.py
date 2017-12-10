# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

from __future__ import division, unicode_literals

# ---- Standard library imports

# from datetime import date
import csv

# ---- Third party imports

import numpy as np
import matplotlib as mpl
from xlrd import xldate_as_tuple
# from xlrd.xldate import xldate_from_date_tuple
import matplotlib.pyplot as plt

# ---- Imports: local

from gwhat.common.utils import save_content_to_csv
from gwhat.gwrecharge.gwrecharge_calc2 import calcul_glue_yearly_rechg


def calcul_glue(p, yrs_range=None):

    # --------------------------------------------------------- Fetch Data ----

    data = np.load('GLUE.npy').item()



    rechg = np.array(data['recharge'])
    etr = np.array(data['etr'])
    ru = np.array(data['ru'])
    hydro = np.array(data['hydrograph'])
    RMSE = np.array(data['RMSE'])

    TIME = np.array(data['Time'])
    YEARS = np.array(data['Year']).astype(int)
    MONTHS = np.array(data['Month']).astype(int)
    PTOT = np.array(data['Weather']['Ptot']).astype(int)

    deltat = data['deltat']
    Sy = np.array(data['Sy'])
    RASmax = np.array(data['RASmax'])
    Cru = np.array(data['Cru'])

    print('')
    print('range Sy = %0.3f to %0.3f' % (np.min(Sy), np.max(Sy)))
    print('range RASmax = %d to %d' % (np.min(RASmax), np.max(RASmax)))
    print('range Cru = %0.3f to %0.3f' % (np.min(Cru), np.max(Cru)))
    print('')

    # -------------------------------------------------------- Calcul GLUE ----

    RMSE = RMSE/np.sum(RMSE)  # Rescaling

    N = len(p)
    M = len(TIME)

    glue_etr = np.zeros((M, N))
    glue_rechg = np.zeros((M, N))
    glue_ru = np.zeros((M, N))

    for i in range(M):
        isort = np.argsort(rechg[:, i])  # Sorting predicted values
        CDF = np.cumsum(RMSE[isort])     # Cumulative Density Function
        glue_rechg[i, :] = np.interp(p, CDF, rechg[isort, i])

        isort = np.argsort(etr[:, i])
        CDF = np.cumsum(RMSE[isort])
        glue_etr[i, :] = np.interp(p, CDF, etr[isort, i])

        isort = np.argsort(ru[:, i])
        CDF = np.cumsum(RMSE[isort])
        glue_ru[i, :] = np.interp(p, CDF, ru[isort, i])

    # ------------------------------------------------------ Calcul Yearly ----

    # Convert daily to hydrological year. An hydrological year is defined from
    # October 1 to September 30 of the next year.
    if yrs_range:
        yr2plot = np.arange(yrs_range[0], yrs_range[1]).astype('int')
    else:
        yr2plot = np.arange(np.min(YEAR), np.max(YEAR)).astype('int')

    NYear = len(yr2plot)
    glue_rechg_yr = np.zeros((NYear, N))
    glue_etr_yr = np.zeros((NYear, N))
    glue_ru_yr = np.zeros((NYear, N))
    ptot_yr = np.zeros(NYear)
    years = []

    # if deltat > 0:
    #     for i, t in enumerate(TIME):
    #         date = xldate_as_tuple(t+deltat, 0)
    #         YEARS[i] = date[0]
    #         MONTHS[i] = date[1]

    for i in range(NYear):
        yr0 = yr2plot[i]
        yr1 = yr0 + 1
        years.append("'%s-'%s" % (str(yr0)[-2:], str(yr1)[-2:]))

        indx0 = np.where((YEARS == yr0) & (MONTHS == 10))[0][0]
        indx1 = np.where((YEARS == yr1) & (MONTHS == 9))[0][-1]

        glue_rechg_yr[i, :] = np.sum(glue_rechg[indx0:indx1+1, :], axis=0)
        glue_etr_yr[i, :] = np.sum(glue_etr[indx0:indx1+1, :], axis=0)
        glue_ru_yr[i, :] = np.sum(glue_ru[indx0:indx1+1, :], axis=0)

        ptot_yr[i] = np.sum(PTOT[indx0:indx1+1])

    return years, ptot_yr, glue_rechg_yr, glue_etr_yr, glue_ru_yr


def write_GLUE50_budget(yrs_range=None):
    years, ptot, rechg, etr, ru = calcul_glue([0.5], yrs_range)

    filecontent = [['hydrological year', 'Ptot (mm)', 'Rechg (mm)', 'ETR (mm)',
                   'Ru']]
    for i in range(len(years)):
        filecontent.append([years[i], ptot[i], rechg[i][0], etr[i][0],
                            ru[i][0]])
    save_content_to_csv('glue50_results.csv', filecontent)


def plot_rechg_GLUE(data, lang='English', Ymin0=None, Ymax0=None,
                    yrs_range=None):

    p = [0.05, 0.25, 0.5, 0.75, 0.95]
    year_labels, glue_rechg_yr = calcul_glue_yearly_rechg(data, p, yrs_range)

    max_rechg_yrly = glue_rechg_yr[:, -1]
    min_rechg_yrly = glue_rechg_yr[:, 0]
    prob_rechg_yrly = glue_rechg_yr[:, 2]
    glue25_yr = glue_rechg_yr[:, 1]
    glue75_yr = glue_rechg_yr[:, -2]

    # ---- Produce Figure

    fig = plt.figure(figsize=(11.0, 6))
    fig.patch.set_facecolor('white')

    fheight = fig.get_figheight()
    fwidth = fig.get_figwidth()

    left_margin = 1
    right_margin = 0.35
    bottom_margin = 1.1
    top_margin = 0.25

    x0 = left_margin / fwidth
    y0 = bottom_margin / fheight
    w0 = 1 - (left_margin + right_margin) / fwidth
    h0 = 1 - (bottom_margin + top_margin) / fheight

    # ------------------------------------------------------ AXES CREATION ----

    ax0 = fig.add_axes([x0, y0, w0, h0])
    ax0.patch.set_visible(False)
    for axis in ['top', 'bottom', 'left', 'right']:
        ax0.spines[axis].set_linewidth(0.5)
    ax0.set_axisbelow(True)

    # --------------------------------------------------------- AXIS RANGE ----

    if yrs_range:
        yrs2plot = np.arange(yrs_range[0], yrs_range[1]).astype('int')
    else:
        years = np.array(data['Year']).astype(int)
        yrs2plot = np.arange(np.min(years), np.max(years)).astype('int')

    Xmin0 = min(yrs2plot)-1
    Xmax0 = max(yrs2plot)+1

    if Ymax0 is None:
        Ymax0 = np.max(max_rechg_yrly) + 50
    if Ymin0 is None:
        Ymin0 = 0

    # --------------------------------------------------- XTICKS FORMATING ----

    ax0.xaxis.set_ticks_position('bottom')
    ax0.tick_params(axis='x', direction='out', pad=1)
    ax0.set_xticks(yrs2plot)
    ax0.xaxis.set_ticklabels(year_labels, rotation=45, ha='right')

    # --------------------------------------------------- YTICKS FORMATING ----

    if np.max(max_rechg_yrly) < 250:
        yticks = np.arange(0, Ymax0+1, 25)
    else:
        yticks = np.arange(0, Ymax0+1, 100)

    ax0.yaxis.set_ticks_position('left')
    ax0.set_yticks(yticks)
    ax0.tick_params(axis='y', direction='out', gridOn=True, labelsize=12)
    ax0.grid(axis='y', color=[0.35, 0.35, 0.35], linestyle=':',
             linewidth=0.5, dashes=[0.5, 5])

    ax0.set_yticks(np.arange(0, Ymax0, 25), minor=True)
    ax0.tick_params(axis='y', direction='out', which='minor', gridOn=False)

    # --------------------------------------------------------- AXIS RANGE ----

    ax0.axis([Xmin0, Xmax0, Ymin0, Ymax0])

    # ------------------------------------------------------------- LABELS ----

    ylabl = 'Annual Recharge (mm/y)'
    xlabl = ('Hydrological Years (October 1st of one ' +
             'year to September 30th of the next)')
    if lang == 'French':
        ylabl = "Recharge annuelle (mm/a)"
        xlabl = ("Années Hydrologiques (1er octobre d'une année "
                 "au 30 septembre de la suivante)")
#        xlabl = (u"Années Hydrologiques (1er octobre d'une " +
#                 u"année au 30 septembre de l'année suivante)")

    ax0.set_ylabel(ylabl, fontsize=16,
                   verticalalignment='bottom')
    ax0.yaxis.set_label_coords(-0.065, 0.5)

    ax0.set_xlabel(xlabl, fontsize=16, verticalalignment='top')
    ax0.xaxis.set_label_coords(0.5, -0.175)

    # ------------------------------------------------------------- PLOTTING --

#    ax0.plot(yr2plot, ptot_yrly-900, marker='s', zorder=0)

    # ---- Recharge ----

    ax0.plot(yrs2plot, prob_rechg_yrly, ls='--', color='0.35', zorder=100)

    yerr = [prob_rechg_yrly-min_rechg_yrly, max_rechg_yrly-prob_rechg_yrly]
    herr = ax0.errorbar(yrs2plot, prob_rechg_yrly, yerr=yerr,
                        fmt='o', capthick=1, capsize=4, ecolor='0',
                        elinewidth=1, mfc='White', mec='0', ms=5,
                        markeredgewidth=1, zorder=200)

    h25 = ax0.plot(yrs2plot, glue25_yr, color='red', dashes=[3, 5], alpha=0.65)
    ax0.plot(yrs2plot, glue75_yr, color='red', dashes=[3, 5], alpha=0.65)

    # --------------------------------------------------------------- Legend --

    lg_handles = [herr[0], herr[1], h25[0]]
    lg_labels = ['Recharge (GLUE 50)', 'Recharge (GLUE 5/95)',
                 'Recharge (GLUE 25/75)']

    ax0.legend(lg_handles, lg_labels, ncol=3, fontsize=12, frameon=False,
               numpoints=1, loc='upper left')

    # ------------------------------------------------------------- Averages --

    print('Mean annual Recharge (GLUE 95) = %0.f mm/y' %
          np.mean(max_rechg_yrly))
    print('Mean annual Recharge (GLUE 50)= %0.f mm/y' %
          np.mean(prob_rechg_yrly))
    print('Mean annual Recharge (GLUE 5) = %0.f mm/y' %
          np.mean(min_rechg_yrly))

    if lang == 'French':
        text = 'Recharge annuelle moyenne :\n'
        text += '(GLUE 5) %d mm/a ; ' % np.mean(min_rechg_yrly)
        text += '(GLUE 25) %d mm/a ; ' % np.mean(glue25_yr)
        text += '(GLUE 50) %d mm/a ; ' % np.mean(prob_rechg_yrly)
        text += '(GLUE 75) %d mm/a ; ' % np.mean(glue75_yr)
        text += '(GLUE 95) %d mm/a' % np.mean(max_rechg_yrly)
    else:
        text = 'Mean annual recharge :\n'
        text += '(GLUE 5) %d mm/y ; ' % np.mean(min_rechg_yrly)
        text += '(GLUE 25) %d mm/y ; ' % np.mean(glue25_yr)
        text += '(GLUE 50) %d mm/y ; ' % np.mean(prob_rechg_yrly)
        text += '(GLUE 75) %d mm/y ; ' % np.mean(glue75_yr)
        text += '(GLUE 95) %d mm/y' % np.mean(max_rechg_yrly)

    dx, dy = 5/72, 5/72
    padding = mpl.transforms.ScaledTranslation(dx, dy, fig.dpi_scale_trans)
    transform = ax0.transAxes + padding
    ax0.text(0, 0, text, va='bottom', ha='left',
             fontsize=12, transform=transform)

    # ----- Some Calculation ----

    # print('')
    # print('%d behavioural realizations' % len(RMSE))
    # indx = np.where(prob_rechg_yrly == np.max(prob_rechg_yrly))[0][0]
    # print('Max. Recharge is %d mm/y at year %s' %
    #       (np.max(prob_rechg_yrly), xtcklabl[indx]))
    # indx = np.where(prob_rechg_yrly == np.min(prob_rechg_yrly))[0][0]
    # print('Min. Recharge is %d mm/y at year %s' %
    #       (np.min(prob_rechg_yrly), xtcklabl[indx]))
    # Runcer = max_rechg_yrly - min_rechg_yrly
    # print('Max uncertainty is %d mm/y at year %s'
    #       % (np.max(Runcer),
    #          xtcklabl[np.where(Runcer == np.max(Runcer))[0][0]]))
    # print('Min uncertainty is %d mm/y at year %s'
    #       % (np.min(Runcer),
    #          xtcklabl[np.where(Runcer == np.min(Runcer))[0][0]]))


# =============================================================================


def plot_water_budget_yearly(YEARS, PRECIP, RECHG, ETR, RU,
                             language='English'):

    fig = plt.figure(figsize=(15, 7))
    fig.patch.set_facecolor('white')

    fheight = fig.get_figheight()
    fwidth = fig.get_figwidth()

    left_margin = 1
    right_margin = 0.25
    bottom_margin = 1.25
    top_margin = 0.25

    x0 = left_margin / fwidth
    y0 = bottom_margin / fheight
    w0 = 1 - (left_margin + right_margin) / fwidth
    h0 = 1 - (bottom_margin + top_margin) / fheight

    # -------------------------------------------------------- AXES CREATION --

    ax0 = fig.add_axes([x0, y0, w0, h0])
    ax0.patch.set_visible(False)
    for axis in ['top', 'bottom', 'left', 'right']:
        ax0.spines[axis].set_linewidth(0.5)

    # ----------------------------------------------------------- AXIS RANGE --

    N = len(YEARS)

    Ymin0 = 0
    Ymax0 = 1600

    Xmin0 = 0 - 0.5
    Xmax0 = N - 0.5

    # ----------------------------------------------------- XTICKS FORMATING --

    ax0.xaxis.set_ticks_position('bottom')
    ax0.tick_params(axis='x', direction='out', gridOn=False, labelsize=14)
    ax0.set_xticks(np.arange(N))
    ax0.xaxis.set_ticklabels(YEARS, rotation=45, ha='right')

    # ----------------------------------------------------- YTICKS FORMATING --

    ax0.yaxis.set_ticks_position('left')
    ax0.tick_params(axis='y', direction='out', gridOn=True, labelsize=14)

    ax0.set_yticks(np.arange(0, Ymax0, 50), minor=True)
    ax0.tick_params(axis='y', direction='out', which='minor', gridOn=False)

    # ----------------------------------------------------------- AXIS RANGE --

    ax0.axis([Xmin0, Xmax0, Ymin0, Ymax0])

    # --------------------------------------------------------------- LABELS --

    ylabl = 'Equivalent Water (mm)'
    xlabl = ('Hydrological Years (October 1st of one ' +
             'year to September 30th of the next)')
    if language == 'French':
        ylabl = "Colonne d'eau équivalente (mm)"
        xlabl = ("Année Hydrologique (1er octobre d'une " +
                 "année au 30 septembre de l'année suivante)")

    mplJS.set_xlabel(ax0, xlabl, fontsize=18, labelpad=15)
    mplJS.set_ylabel(ax0, ylabl, fontsize=18, labelpad=15, position='left')

#    ax0.set_ylabel(ylabl, fontsize=16, va='bottom')
#    ax0.yaxis.set_label_coords(-0.055, 0.5)

#    ax0.set_xlabel(xlabl, fontsize=16, verticalalignment='top')
#    ax0.xaxis.set_label_coords(0.5, -0.125)

    # ------------------------------------------------------------- PLOTTING --

    colors = [[0./255, 128./255, 255./255],
              [0./255, 76./255, 153./255],
              [0./255, 25./255, 51./255],
              [102./255, 178./255, 255./255]]

    labels = ['Total Precipitation', 'Recharge', 'Runoff',
              'Real Evapotranspiration']
    if language == 'French':
        labels = ['Précipitations totales', 'Recharge', 'Ruissellement',
                  'Évapotranspiration réelle']

    MARKER = ['o', 'h', 's', 'D']
    DATA = [PRECIP, RECHG, RU, ETR]

    for i in range(4):
        ax0.plot(np.arange(len(DATA[i])), DATA[i], color=colors[i],
                 mec='white', marker=MARKER[i], ms=9, dashes=[5, 2],
                 label=labels[i], clip_on=False, zorder=100, alpha=0.85)

    # --------------------------------------------------------------- LEGEND --

    ax0.legend(ncol=4, numpoints=1, fontsize=14, frameon=False,
               loc='upper left', bbox_to_anchor=[0, 1])

    # -------------------------------------------------------------------------

    mplJS.set_margins(fig, borderpad=10)
    fig.savefig('yearly_budget.pdf')


# =============================================================================


def plot_water_budget_yearly2(years, PRECIP, RECHG, ETR, RU,
                              language='English'):

    fig = plt.figure(figsize=(15, 7))
    fig.patch.set_facecolor('white')

    fheight = fig.get_figheight()
    fwidth = fig.get_figwidth()

    left_margin = 1
    right_margin = 0.25
    bottom_margin = 1.25
    top_margin = 0.25

    x0 = left_margin / fwidth
    y0 = bottom_margin / fheight
    w0 = 1 - (left_margin + right_margin) / fwidth
    h0 = 1 - (bottom_margin + top_margin) / fheight

    # -------------------------------------------------------- AXES CREATION --

    ax0 = fig.add_axes([x0, y0, w0, h0])
    ax0.patch.set_visible(False)
    for axis in ['top', 'bottom', 'left', 'right']:
        ax0.spines[axis].set_linewidth(0.5)

    # ----------------------------------------------------------- AXIS RANGE --

    NYear = len(years)

    Ymin0 = 0
    Ymax0 = 1600

    Xmin0 = 0
    Xmax0 = NYear * 3

    # ----------------------------------------------------- XTICKS FORMATING --

    xtckpos = np.arange(NYear * 3 + 1)

    ax0.xaxis.set_ticks_position('bottom')
    ax0.tick_params(axis='x', direction='out')
    ax0.xaxis.set_ticklabels([])
    ax0.set_xticks(xtckpos[::3])

    ax0.set_xticks(xtckpos[::3] + 1.5, minor=True)
    ax0.tick_params(axis='x', which='minor', length=0, labelsize=14, pad=2)
    ax0.xaxis.set_ticklabels(years, minor=True, rotation=45, ha='right')

    # ----------------------------------------------------- YTICKS FORMATING --

    ax0.yaxis.set_ticks_position('left')
    ax0.tick_params(axis='y', direction='out', gridOn=True, labelsize=14)

    ax0.set_yticks(np.arange(0, Ymax0, 50), minor=True)
    ax0.tick_params(axis='y', direction='out', which='minor', gridOn=False)

    ax0.set_axisbelow(True)

    # ----------------------------------------------------------- AXIS RANGE --

    ax0.axis([Xmin0, Xmax0, Ymin0, Ymax0])

    # --------------------------------------------------------------- LABELS --

    ylabl = 'Equivalent Water (mm)'
    xlabl = ('Hydrological Years (October 1st of one ' +
             'year to September 30th of the next)')
    if language == 'French':
        ylabl = "Colonne d'eau équivalente (mm)"
        xlabl = ("Année Hydrologique (1er octobre d'une " +
                 "année au 30 septembre de l'année suivante)")

    mplJS.set_xlabel(ax0, xlabl, fontsize=18, labelpad=15)
    mplJS.set_ylabel(ax0, ylabl, fontsize=18, labelpad=15, position='left')

    # ------------------------------------------------------------- PLOTTING --
#
    COLOR = [[0/255, 25/255, 51/255],
             [0/255, 76/255, 153/255],
             [0/255, 128/255, 255/255],
             [102/255, 178/255, 255/255]]

    labels = ['Total Precipitation', 'Recharge', 'Runoff',
              'Real Evapotranspiration']
    if language == 'French':
        labels = ['Précipitations totales', 'Recharge', 'Ruissellement',
                  'Évapotranspiration réelle']

    bar_width = 0.85

    ax0.bar(xtckpos[1::3], PRECIP, align='center', width=bar_width,
            color=COLOR[0], edgecolor='None', label=labels[0])

    var2plot = RECHG + ETR + RU
    ax0.bar(xtckpos[2::3], var2plot, align='center', width=bar_width,
            color=COLOR[3], edgecolor='None', label=labels[2])

    var2plot = RECHG + ETR
    ax0.bar(xtckpos[2::3], var2plot, align='center', width=bar_width,
            color=COLOR[2], edgecolor='None', label=labels[3])

    var2plot = RECHG
    ax0.bar(xtckpos[2::3], var2plot, align='center', width=bar_width,
            color=COLOR[1], edgecolor='None', label=labels[1])

    # -------------------------------------------------------- PLOTTING TEXT --

    for i in range(NYear):
        y = PRECIP[i]/2
        x = 1 + 3 * i
        txt = '%0.1f' % PRECIP[i]
        ax0.text(x, y, txt, color='white', va='center', ha='center',
                 rotation=90, fontsize=10)

        y = RECHG[i]/2
        x = 2 + 3 * i
        txt = '%0.1f' % RECHG[i]
        ax0.text(x, y, txt, color='white', va='center', ha='center',
                 rotation=90, fontsize=10)

        y = ETR[i]/2 + RECHG[i]
        x = 2 + 3 * i
        txt = '%0.1f' % ETR[i]
        ax0.text(x, y, txt, color='black', va='center', ha='center',
                 rotation=90, fontsize=10)

        y = RU[i]/2 + RECHG[i] + ETR[i]
        x = 2 + 3 * i
        txt = '%0.1f' % RU[i]
        ax0.text(x, y, txt, color='black', va='center', ha='center',
                 rotation=90, fontsize=10)

    # --------------------------------------------------------------- LEGEND --

    ax0.legend(loc=2, ncol=4, numpoints=1, fontsize=14, frameon=False)

    mplJS.set_margins(fig, borderpad=10)
    fig.savefig('yearly_budget2.pdf')


# =============================================================================


def main():

    years, ptot, rechg, etr, ru = calcul_glue([0.05, 0.25, 0.5, 0.75, 0.95],
                                              [2000, 2016])

#    write_GLUE50_budget(yrs_range=[2000, 2016])

#    plot_water_budget_yearly(years, ptot, rechg[:, 2], etr[:, 2], ru[:, 2],
#                             language='French')
#    plot_water_budget_yearly2(years, ptot, rechg[:, 2], etr[:, 2], ru[:, 2],
#                              language='English')
    plot_rechg_GLUE('French', yrs_range=[2000, 2016])

if __name__ == '__main__':
    plt.rc('font', family='Arial')
    plt.close('all')
    main()
    plt.show()
