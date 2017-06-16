# -*- coding: utf-8 -*-
"""
Copyright 2014-2017 Jean-Sebastien Gosselin
email: jean-sebastien.gosselin@ete.inrs.ca

This file is part of WHAT (Well Hydrograph Analysis Toolbox).

WHAT is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""

# Standard library imports :

import os
import csv

# Third party imports :

import numpy as np
import matplotlib.pyplot as plt
from xlrd import xldate_as_tuple

# Local imports :
try:
    from kgs_brf.kgs_plot import plot_BRF
except ImportError:  # to run this module standalone
    print('Running module as a standalone script...')
    import sys
    import platform
    from os.path import dirname, realpath
    root = dirname(dirname(realpath(__file__)))
    sys.path.append(root)

    from kgs_brf.kgs_plot import plot_BRF


def produce_BRFInputtxt(well, time, wl, bp, et):

    comment = 'No comment men'
    wlu = 'feet'
    bpu = 'feet'
    etu = 'NONE'
    sampleinterval = time[1]-time[0]
    timeunits = 'days'
    N = len(time)

    yr, mth, day, hr, mn, sec = xldate_as_tuple(time[0], 0)
    dst = '%02d/%02d/%d, %02d:%02d:%02d' % (yr, mth, day, hr, mn, sec)

    yr, mth, day, hr, mn, sec = xldate_as_tuple(time[-1], 0)
    det = '%02d/%02d/%d, %02d:%02d:%02d' % (yr, mth, day, hr, mn, sec)

    fcontent = []
    fcontent.append(['Comment: %s' % comment])
    fcontent.append(['Well: %s' % well])
    fcontent.append(['WL Units: %s' % wlu])
    fcontent.append(['BP Units: %s' % bpu])
    fcontent.append(['ET Units: %s' % etu])

    fcontent.append(['Sample Interval: %f' % sampleinterval])
    fcontent.append(['Time Units: %s' % timeunits])
    fcontent.append(['Data Start Time: %s' % dst])
    fcontent.append(['Data End Time: %s' % det])

    fcontent.append(['Number of Data: %d' % N])
    fcontent.append(['Time WL BP ET'])

    wl = (100-wl)*3.28084
    bp = bp*3.28084
    t = time-time[0]

    for i in range(N):
        fcontent.append([time[i], wl[i], bp[i], et[i]])

    dirname = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(dirname, 'BRFInput.txt')
    with open(filename, 'w', encoding='utf8') as f:
        writer = writer = csv.writer(f, delimiter='\t', lineterminator='\n')
        writer.writerows(fcontent)


def produce_par_file(lagBP, lagET, detrend, correct):
    dirname = os.path.dirname(os.path.realpath(__file__))
    brfinput = os.path.join(dirname, 'BRFInput.txt')
    brfoutput = os.path.join(dirname, 'BRFOutput.txt')
    wlcinput = os.path.join(dirname, 'WLCInput.txt')
    wlcoutput = os.path.join(dirname, 'WLCOutput.txt')

    par = []
    par.append(['BRF Option (C[ompute] or R[ead]): Compute'])
    par.append(['BRF Input Data File: %s' % brfinput])
    par.append(['Number of BP Lags:  %d' % lagBP])
    par.append(['Number of BP ET:  %d' % lagET])
    par.append(['BRF Output Data File: %s' % brfoutput])
    par.append(['Detrend data? (Y[es] or N[o]): %s' % detrend])
    par.append(['Correct WL? (Y[es] or N[o]): %s' % correct])
    par.append(['WLC Input Data File: %s' % wlcinput])
    par.append(['WLC Output Data File: %s' % wlcoutput])

    filename = os.path.join(dirname, 'kgs_brf.par')
    with open(filename, 'w', encoding='utf8') as f:
        writer = csv.writer(f, delimiter='\t',  lineterminator='\n')
        writer.writerows(par)


def run_kgsbrf():
    dirname = os.path.dirname(os.path.realpath(__file__))
    exename = os.path.join(dirname, 'kgs_brf.exe')
    parname = os.path.join(dirname, 'kgs_brf.par')

    os.system('""%s" < "%s""' % (exename, parname))

#    process = QtCore.QProcess()
#    process.start(exename+" < "+ parname)
#    process.waitForFinished()
#    process.close()


def load_BRFOutput(show_ebar=True, msize=5, draw_line=False,
                   ylim=[None, None]):
    dirname = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(dirname, 'BRFOutput.txt')

    with open(filename, 'r') as f:
        reader = list(csv.reader(f))

    header = []
    for row in reader:
        header.append(row)
        if 'LagNo Lag A sdA SumA sdSumA B sdB SumB sdSumB' in row[0]:
            break

    well = header[2][0].split()[-1]
    date0 = header[8][0].split()[-1]
    date1 = header[9][0].split()[-1]

    data = reader[len(header):]
    dataf = []
    count = 1
    for row in data:
        if count == 1:
            dataf.append([float(i) for i in row[0].split()])
            count += 1
        elif count in [2, 3]:
            dataf[-1].extend([float(i) for i in row[0].split()])
            count += 1
        elif count == 4:
            dataf[-1].extend([float(i) for i in row[0].split()])
            count = 1

    dataf = np.array(dataf)

    lag = dataf[:, 1]
    A = dataf[:, 4]
    err = dataf[:, 5]

    plt.close('all')
    if show_ebar:
        plot_BRF(lag, A, err, date0, date1, well, msize, draw_line, ylim)
    else:
        plot_BRF(lag, A, [], date0, date1, well, msize, draw_line, ylim)
    plt.show()


if __name__ == "__main__":
#    plt.close('all')
    # produce_par_file()
    run_kgsbrf()
    # os.system("kgs_brf.exe" + " < " + "kgs_brf.par")
#    load_BRFOutput(show_ebar=True, msize=5, draw_line=False)
#    plt.show()
