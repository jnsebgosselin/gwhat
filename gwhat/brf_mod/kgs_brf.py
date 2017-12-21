# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Standard library imports

import os
import csv
import sys

# ---- Third party imports

import numpy as np
from xlrd import xldate_as_tuple

# ---- Local imports

from gwhat.brf_mod import __install_dir__


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

    filename = os.path.join(__install_dir__, 'BRFInput.txt')
    with open(filename, 'w', encoding='utf8') as f:
        writer = writer = csv.writer(f, delimiter='\t', lineterminator='\n')
        writer.writerows(fcontent)


def produce_par_file(lagBP, lagET, detrend, correct):
    brfinput = os.path.join(__install_dir__, 'BRFInput.txt')
    brfoutput = os.path.join(__install_dir__, 'BRFOutput.txt')
    wlcinput = os.path.join(__install_dir__, 'WLCInput.txt')
    wlcoutput = os.path.join(__install_dir__, 'WLCOutput.txt')

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

    filename = os.path.join(__install_dir__, 'kgs_brf.par')
    with open(filename, 'w', encoding='utf8') as f:
        writer = csv.writer(f, delimiter='\t',  lineterminator='\n')
        writer.writerows(par)


def run_kgsbrf():
    exename = os.path.join(__install_dir__, 'kgs_brf.exe')
    parname = os.path.join(__install_dir__, 'kgs_brf.par')
    if os.path.exists(exename) and os.path.exists(parname):
        if os.name == 'nt':
            os.system('""%s" < "%s""' % (exename, parname))
        elif os.name == 'posix':
            # import subprocess
            os.system('"wine "%s" < "%s""' % (exename, parname))
            # subprocess.call(["wine", "%s < %s" % (exename, parname)])

#    process = QtCore.QProcess()
#    process.start(exename+" < "+ parname)
#    process.waitForFinished()
#    process.close()


def read_BRFOutput():
    filename = os.path.join(__install_dir__, 'BRFOutput.txt')
    with open(filename, 'r') as f:
        reader = list(csv.reader(f))

    header = []
    for row in reader:
        header.append(row)
        if 'LagNo Lag A sdA SumA sdSumA B sdB SumB sdSumB' in row[0]:
            break

    # well = header[2][0].split()[-1]
    # date0 = header[8][0].split()[-1]
    # date1 = header[9][0].split()[-1]

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

    return lag, A, err


if __name__ == "__main__":
#    plt.close('all')
    # produce_par_file()
    run_kgsbrf()
    load_BRFOutput(show_ebar=True, msize=5, draw_line=False)
#    plt.show()
