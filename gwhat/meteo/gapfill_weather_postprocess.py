# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.


# ---- Standard Library Imports
import csv
import os

# ---- Third Party Imports
from matplotlib.figure import Figure as MplFigure
from matplotlib.transforms import ScaledTranslation
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

import numpy as np
from scipy.stats._continuous_distns import gamma

from xlrd.xldate import xldate_from_date_tuple

# ---- Local Library Imports
from gwhat.common.utils import save_content_to_csv


class PostProcessErr(object):

    SUPPORTED_FIG_FORMATS = ['pdf', 'svg']
    SUPPORTED_LANGUAGES = ['English', 'French']

    def __init__(self, fname):
        self.Yp = None  # Predicted value at target station
        self.Ym = None  # Measured value at target station
        self.Time = None
        self.Date = None

        self.staName = None
        self.climID = None
        self.set_fig_format(self.SUPPORTED_FIG_FORMATS[0])
        self.set_fig_language(self.SUPPORTED_LANGUAGES[0])

        self.fname = fname
        self.dirname = os.path.dirname(self.fname)

        self.load_err_file()

    # ---- Figure extension and format

    @property
    def fig_ext(self):
        """Figure extension to use for saving the figures."""
        return '.' + self.fig_format

    @property
    def fig_format(self):
        """Figure format to use for saving the figures."""
        return self.__fig_format

    def set_fig_format(self, fig_format):
        """Set the format that will be used for saving the figures."""
        if fig_format in self.SUPPORTED_FIG_FORMATS:
            self.__fig_format = fig_format
        else:
            print("Supported figure formats are:",  self.SUPPORTED_FIG_FORMATS)
            raise ValueError

    # ---- Language

    @property
    def fig_language(self):
        """Language of the figure labels."""
        return self.__fig_language

    def set_fig_language(self, language):
        """Set the language of the figure labels."""
        if language in self.SUPPORTED_LANGUAGES:
            self.__fig_language = language
        else:
            print("Supported language:",  self.SUPPORTED_LANGUAGES)
            raise ValueError

    # ---- Open and Load files

    def open_err_file(self, filename):
        """Open .err file and return None if it fails."""
        for dlm in [',', '\t']:
            with open(self.fname) as f:
                reader = list(csv.reader(f, delimiter=dlm))
                for line in reader:
                    try:
                        if line[0] == 'VARIABLE':
                            return reader
                    except IndexError:
                        continue
        else:
            print('The format of the .err file is wrong.')
            return None

    def load_err_file(self):
        """Read .err file and return None if it fails."""
        reader = self.open_err_file(self.fname)
        if reader is None:
            return

        for row, line in enumerate(reader):
            try:
                if line[0] == 'VARIABLE':
                    break
                elif line[0] == 'Station Name':
                    self.staName = reader[row][1]
                elif line[0] == 'Climate Identifier':
                    self.climID = reader[row][1]
            except IndexError:
                continue
        row += 1

        # ------------------------------------------------ Re-Organizes Data --

        # Get unique weather variable names

        DATA = np.array(reader[row:])
        self.varNames = np.unique(DATA[:, 0])
        self.varTypes = ['continuous'] * (len(self.varNames))

        # Splits data acoording to the weather variables found.

        self.Yp, self.Ym, self.Time, self.Date = [], [], [], []
        for i, var in enumerate(self.varNames):
            indx = np.where(DATA[:, 0] == var)[0]

            self.Yp.append(DATA[indx, 7].astype(float))
            self.Ym.append(DATA[indx, 8].astype(float))

            y = DATA[indx, 1].astype(int)
            m = DATA[indx, 2].astype(int)
            d = DATA[indx, 3].astype(int)

            # ---- Time ----

            t = np.zeros(len(y))
            for date in range(len(y)):
                t[date] = (xldate_from_date_tuple((y[date],
                                                   m[date],
                                                   d[date]), 0)
                           - xldate_from_date_tuple((y[date], 1, 1), 0))

            self.Time.append(t)
            self.Date.append([y, m, d])

            # ---- Weather Variable Type ----

            # If the proportion of zeros in the data series is higher
            # than 25%, the data type is set as an event-based weather
            # variable. Otherwise, default value is kept and variable is
            # considered to be continuous in time.
            #
            # The precipitation (solid, liquid or total) is a good example of
            # an event-based variable, while air temperature (min, max or mean)
            # is a good example of a continuous variable.

            pc0 = len(np.where(self.Ym[i] == 0)[0]) / float(len(self.Ym[i]))
            if pc0 > 0.25:
                self.varTypes[i] = 'event-based'

        return

    def generates_graphs(self):
        """Generates all the graphs from the err file."""
        for i in range(len(self.Yp)):
            name = self.varNames[i]
            name = name.lower()
            name = name.replace(" ", "_")
            name = name.replace("(", "")
            name = name.replace(")", "")
            print(name)
            fname = '%s/%s%s' % (self.dirname, name, self.fig_ext)
            print('------------------------')
            print('Generating %s.' % (os.path.basename(fname)))
            print('------------------------')
            plot_est_err(self.Ym[i], self.Yp[i], self.varNames[i],
                         fname, self.fig_language)

            if self.varNames[i] == 'Total Precip (mm)':
                fname = '%s/%s%s' % (self.dirname, 'precip_PDF', self.fig_ext)
                plot_gamma_dist(self.Ym[i], self.Yp[i],
                                fname, self.fig_language)
                print('Generating %s.' % (os.path.basename(fname)))

    def generates_summary(self):

        Ypre = self.Yp
        Ymes = self.Ym

        for i in range(len(Ypre)):

            RMSE = (np.mean((Ypre[i] - Ymes[i]) ** 2)) ** 0.5
            MAE = np.mean(np.abs(Ypre[i] - Ymes[i]))
            ME = np.mean(Ypre[i] - Ymes[i])
            r = np.corrcoef(Ypre[i], Ymes[i])[1, 0]

            Emax = np.min(Ypre[i] - Ymes[i])
            Emin = np.max(Ypre[i] - Ymes[i])

            dirname = 'summary/'
            if not os.path.exists(dirname):
                os.mkdir(dirname)
            filename = dirname + self.varNames[i] + '.csv'

            # ---- Generate File ----

            if not os.path.exists(filename):
                header = [['Station', 'RMSE', 'MAE', 'ME',
                           'r', 'Emax', 'Emin']]
                save_content_to_csv(filename, header)

            # ---- Write Stats to File ----

            rowcontent = [[self.staName, '%0.1f' % RMSE, '%0.1f' % MAE,
                           '%0.2f' % ME, '%0.3f' % r, '%0.1f' % Emax,
                           '%0.1f' % Emin]]
            save_content_to_csv(filename, rowcontent, mode='a')


def plot_est_err(Ymes, Ypre, varName, fname, language='English'):

    Ymax = np.ceil(np.max(Ymes)/10)*10
    Ymin = np.floor(np.min(Ymes)/10)*10

    fw, fh = 6, 6
    fig = MplFigure(figsize=(fw, fh))
    canvas = FigureCanvas(fig)

    # ---- Create Axes

    leftMargin = 1. / fw
    rightMargin = 0.25 / fw
    bottomMargin = 0.8 / fh
    topMargin = 0.25 / fh

    x0 = leftMargin
    y0 = bottomMargin
    w0 = 1 - (leftMargin + rightMargin)
    h0 = 1 - (bottomMargin + topMargin)

    ax0 = fig.add_axes([x0, y0, w0, h0])
    ax0.set_axisbelow(True)
    ax0.grid(axis='both', color='0.', linestyle='--', linewidth=0.5,
             dashes=[0.5, 3])

    # ---- Plot

    # Estimation Error
    hscat, = ax0.plot(Ymes, Ypre, '.', mec='k', mfc='k', ms=12, alpha=0.35)
    hscat.set_rasterized(True)

    # 1:1 Line
    dl = 12    # dashes length
    ds = 6     # spacing between dashes
    dew = 0.5  # dashes edge width
    dlw = 1.5  # dashes line width

    # Plot a white contour line
    ax0.plot([Ymin, Ymax], [Ymin, Ymax], '-w', lw=dlw + 2 * dew, alpha=1)

    # Plot a black dashed line
    hbl, = ax0.plot([Ymin, Ymax], [Ymin, Ymax], 'k', lw=dlw,
                    dashes=[dl, ds], dash_capstyle='butt')

    # ---- Text

    # Calculate Statistics

    RMSE = (np.mean((Ypre - Ymes) ** 2)) ** 0.5
    MAE = np.mean(np.abs(Ypre - Ymes))
    ME = np.mean(Ypre - Ymes)
    r = np.corrcoef(Ypre, Ymes)[1, 0]
    print('RMSE=%0.1f ; MAE=%0.1f ; ME=%0.2f ; r=%0.3f' %
          (RMSE, MAE, ME, r))

    Emax = np.min(Ypre - Ymes)
    Emin = np.max(Ypre - Ymes)

    print('Emax=%0.1f ; Emin=%0.1f' % (Emax, Emin))

    # Generate and Plot Labels

    if varName in ['Max Temp (deg C)', 'Mean Temp (deg C)',
                   'Min Temp (deg C)']:
        units = u'°C'
    elif varName in ['Total Precip (mm)']:
        units = 'mm'
    else:
        units = ''

    tcontent = [u'RMSE = %0.1f %s' % (RMSE, units),
                u'MAE = %0.1f %s' % (MAE, units),
                u'ME = %0.2f %s' % (ME, units),
                u'r = %0.3f' % (r)]
    tcontent = list(reversed(tcontent))
    for i in range(len(tcontent)):
        dx, dy = -10 / 72., 10 * (i+1) / 72.
        padding = ScaledTranslation(dx, dy, fig.dpi_scale_trans)
        transform = ax0.transAxes + padding
        ax0.text(0, 0, tcontent[i], ha='left', va='bottom', fontsize=16,
                 transform=transform)

    # ---- Get Labels Win. Extents

    hext, vext = np.array([]), np.array([])
    renderer = canvas.get_renderer()
    for text in ax0.texts:
        bbox = text.get_window_extent(renderer)
        bbox = bbox.transformed(ax0.transAxes.inverted())
        hext = np.append(hext, bbox.width)
        vext = np.append(vext, bbox.height)

    # ---- Position Labels in Axes

    x0 = 1 - np.max(hext)
    y0 = 0
    for i, text in enumerate(ax0.texts):
        text.set_position((x0, y0))
        y0 += vext[i]

    # ----- Labels

    ax0.xaxis.set_ticks_position('bottom')
    ax0.yaxis.set_ticks_position('left')
    ax0.tick_params(axis='both', direction='out', labelsize=14)

    if varName == 'Max Temp (deg C)':
        if language == 'French':
            var = u'Températures maximales journalières %s (°C)'
        else:
            var = u'%s Daily Max Temperature (°C)'
    elif varName == 'Mean Temp (deg C)':
        if language == 'French':
            var = u'Températures moyennes journalières %s (°C)'
        else:
            var = u'%s Daily Mean Temperature (°C)'
    elif varName == 'Min Temp (deg C)':
        if language == 'French':
            var = u'Températures minimales journalières %s (°C)'
        else:
            var = u'%s Daily Min Temperature (°C)'
    elif varName == 'Total Precip (mm)':
        if language == 'French':
            var = u'Précipitations totales journalières %s (mm)'
        else:
            var = '%s Daily Total Precipitation (mm)'
    else:
        var = ''

    if language == 'French':
        ax0.set_xlabel(var % u'mesurées', fontsize=16, labelpad=15)
        ax0.set_ylabel(var % u'prédites', fontsize=16, labelpad=15)
    else:
        ax0.set_xlabel(var % 'Measured', fontsize=16, labelpad=15)
        ax0.set_ylabel(var % 'Predicted', fontsize=16, labelpad=15)

    # ---- Axis

    ax0.axis([Ymin, Ymax, Ymin, Ymax])

    # ---- Legend

    if language == 'French':
        lglabels = ['Données journalières', '1:1']
    else:
        lglabels = ['Daily weather data', '1:1']

    ax0.legend([hscat, hbl], lglabels,
               loc='upper left', numpoints=1, frameon=False, fontsize=16)

    # ---- Draw

    fig.savefig(fname, dpi=300)

    return canvas


def plot_gamma_dist(Ymes, Ypre, fname, language='English'):

    fw, fh = 6, 6
    fig = MplFigure(figsize=(fw, fh), facecolor='white')
    canvas = FigureCanvas(fig)

    # ---- Create Axes

    leftMargin = 1.1 / fw
    rightMargin = 0.25 / fw
    bottomMargin = 0.85 / fh
    topMargin = 0.25 / fh

    x0 = leftMargin
    y0 = bottomMargin
    w0 = 1 - (leftMargin + rightMargin)
    h0 = 1 - (bottomMargin + topMargin)

    ax0 = fig.add_axes([x0, y0, w0, h0])
    ax0.set_yscale('log', nonposy='clip')

    Xmax = max(np.ceil(np.max(Ymes)/10.) * 10, 80)

    # ---- Plots

    c1, c2 = '#6495ED', 'red'

    if language == 'French':
        lg_labels = [u'DP des données mesurées', u'FDP Gamma (mesurée)',
                     u'FDP Gamma (estimée)']
    else:
        lg_labels = ['Measured data PDF', 'Gamma PDF (measured)',
                     'Gamma PDF (estimated)']

    # Histogram

    ax0.hist(Ymes, bins=20, color=c1, histtype='stepfilled', density=True,
             alpha=0.25, ec=c1, label=lg_labels[0])

    # Measured Gamma PDF

    alpha, loc, beta = gamma.fit(Ymes)
    x = np.arange(0.5, Xmax, 0.1)
    ax0.plot(x, gamma.pdf(x, alpha, loc=loc, scale=beta), '-', lw=2,
             alpha=1., color=c1, label=lg_labels[1])

    # Predicted Gamma PDF

    alpha, loc, beta = gamma.fit(Ypre)
    x = np.arange(0.5, Xmax, 0.1)
    ax0.plot(x, gamma.pdf(x, alpha, loc=loc, scale=beta), '--r',
             lw=2, alpha=0.85, color=c2, label=lg_labels[2])

    # ---- Axis Limits

    ax0.axis(xmin=0, xmax=Xmax, ymax=1)

    # ---- Labels

    # Setup axis labels

    if language == 'French':
        ax0.set_xlabel(u'Précipitations totales journalières (mm)',
                       fontsize=18, labelpad=15)
        ax0.set_ylabel('Probabilité', fontsize=18, labelpad=15)
    else:
        ax0.set_xlabel('Daily Total Precipitation (mm)', fontsize=18,
                       labelpad=15)
        ax0.set_ylabel('Probability', fontsize=18, labelpad=15)

    # Setup yticks labels

    ax0.xaxis.set_ticks_position('bottom')
    ax0.yaxis.set_ticks_position('left')
    ax0.tick_params(axis='both', direction='out', labelsize=14)
    ax0.tick_params(axis='both', which='minor', direction='out',
                    labelsize=14)

    canvas.draw()
    ylabels = []
    for i, label in enumerate(ax0.get_yticks()):
        if label >= 1:
            ylabels.append('%d' % label)
        elif label <= 10**-3:
            ylabels.append('$\\mathdefault{10^{%d}}$' % np.log10(label))
        else:
            ylabels.append(str(label))
    ax0.set_yticklabels(ylabels)

    # ---- Legend

    lg = ax0.legend(loc='upper right', frameon=False)

    # ---- Wet Days Comparison --

    # ---- Generate text

    preWetDays = np.where(Ypre > 0)[0]
    mesWetDays = np.where(Ymes > 0)[0]

    f = len(preWetDays) / float(len(mesWetDays)) * 100

    if f > 100:
        if language == 'French':
            msg = 'Nombre de jours pluvieux surestimé de %0.1f%%' % (f - 100)
        else:
            msg = 'Number of wet days overestimated by %0.1f%%' % (f - 100)
    else:
        if language == 'French':
            msg = 'Nombre de jours pluvieux sous-estimé de %0.1f%%' % (100 - f)
        else:
            msg = 'Number of wet days underestimated by %0.1f%%' % (100 - f)

    # ---- Get Legend Box Position and Extent

    canvas.draw()
    bbox = lg.get_window_extent(canvas.get_renderer())
    bbox = bbox.transformed(ax0.transAxes.inverted())

    dx, dy = 5/72., 5/72.
    padding = ScaledTranslation(dx, dy, fig.dpi_scale_trans)
    transform = ax0.transAxes + padding

    ax0.text(0., 0., msg, transform=transform, va='bottom', ha='left')

    # ---- Draw

    fig.savefig(fname)  # A canvas.draw() is included with this.
    return canvas


def plot_rmse_vs_time(Ymes, Ypre, Time, Date, name):

    fw, fh = 6, 6
    fig = MplFigure(figsize=(fw, fh), facecolor='white')
    canvas = FigureCanvas(fig)

    # ---- Create Axes

    leftMargin = 0.75 / fw
    rightMargin = 0.75 / fw
    bottomMargin = 0.75 / fh
    topMargin = 0.75 / fh

    x0, y0 = leftMargin, bottomMargin
    w0 = 1 - (leftMargin + rightMargin)
    h0 = 1 - (bottomMargin + topMargin)

    ax0 = fig.add_axes([x0, y0, w0, h0], polar=True)

    # ---- Plot Data

    # Estimation Error

    Yerr = np.abs(Ypre - Ymes)
    Time *= 2 * np.pi / 365.

    c = '0.4'
    ax0.plot(Time, Yerr, '.', mec=c, mfc=c, ms=15, alpha=0.5)

    # RMSE Polygon

    Months = Date[1]
    RMSE = np.zeros(12)
    mfd = np.zeros(12)
    for m in range(12):
        mfd[m] = (xldate_from_date_tuple((2000, m+1, 1), 0) -
                  xldate_from_date_tuple((2000, 1, 1), 0))
        indx = np.where(Months == m+1)[0]
        RMSE[m] = (np.mean(Yerr[indx] ** 2)) ** 0.5

    # Transform first day of the month to radians
    mfd = mfd * 2 * np.pi / 365.

    # Add first point at the end to close the polygon
    mfd = np.append(mfd, mfd[0])
    RMSE = np.append(RMSE, RMSE[0])
    ax0.plot(mfd, RMSE * 5, ls='--', c='red', lw=2, mec='b', mew=3, mfc='b',
             ms=10, dash_capstyle='round', dash_joinstyle='round')

    # ---- Labels

    ax0.tick_params(axis='both', direction='out', labelsize=16)
    ax0.set_xticklabels(['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                         'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'])
    ax0.set_xticks(mfd)

    ax0.set_yticklabels([])
    ax0.set_yticks([])
    ax0.set_rmax(1.1 * np.max(Yerr))
    # ax0.set_rgrids([10,20,30,40,50,60,70,80,90], angle=345.)

    # ---- Draw

    fig.savefig(name + '_polar_error.pdf')
    canvas.show()


def compute_wet_days_LatexTable(dirname):
    fname = 'wet_days_0.5mm.csv'
    fcontent = [['station', 'Meas. wet days', 'Pred. wet days', 'Err.(days)',
                 'Err.(%)']]

    for root, directories, filenames in os.walk(dirname):
        for filename in filenames:
            if os.path.splitext(filename)[1] == '.err':
                print('---- %s ----' % os.path.basename(root))
                pperr = PostProcessErr(os.path.join(root, filename))

                preWetDays = np.where(pperr.Yp[3] > 0.5)[0]
                mesWetDays = np.where(pperr.Ym[3] > 0.5)[0]

                Npre = len(preWetDays)
                Nmes = len(mesWetDays)
                f = (Npre - Nmes) / float(Nmes) * 100

                print('Averaged nbr. of meas. wet days per year = %0.1f days'
                      % (Nmes/30.))
                print('Averaged nbr. of pred. wet days per year = %0.1f days'
                      % (Npre/30.))
                print('Estimation Error = %0.1f days' % ((Npre-Nmes)/30.))
                print('Estimation Error = %0.1f %%' % (f))

                MI = np.mean(pperr.Ym[3][mesWetDays])
                SD = np.std(pperr.Ym[3][mesWetDays])
                print('Precipitation intensity = %0.1f mm/day' % MI)
                print('Precipitation sdt = %0.1f mm/day' % SD)

                fcontent.append([pperr.staName,
                                 '%d' % (Nmes/30.),
                                 '%d' % (Npre/30.),
                                 '%d' % ((Npre-Nmes)/30.),
                                 '%0.1f' % f])
    save_content_to_csv(fname, fcontent, mode='a')


def compute_err_boxplot(dirname):

    Ym_tot = []
    Yp_tot = []

    for root, directories, filenames in os.walk(dirname):
        for filename in filenames:
            if os.path.splitext(filename)[1] == '.err':
                print('---- %s ----' % os.path.basename(root))
                pperr = PostProcessErr(os.path.join(root, filename))

                Ym_tot.extend(pperr.Ym)
                Yp_tot.extend(pperr.Yp)


# ---- if __name__ == '__main__'

if __name__ == '__main__':
    dirname = ("C:\\Users\\jsgosselin\\GWHAT\\Projects\\"
               "Example\\Meteo\\Output\\FARNHAM (7022320)"
               )
    filename = os.path.join(dirname, "FARNHAM (7022320)_2005-2010.err")
    post_worker = PostProcessErr(filename)
    post_worker.set_fig_format("pdf")
