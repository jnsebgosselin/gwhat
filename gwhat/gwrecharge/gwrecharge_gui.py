# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

import time

# ---- Imports: third parties

from PyQt5.QtCore import Qt, QThread
from PyQt5.QtCore import pyqtSlot as QSlot
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtWidgets import (QWidget, QGridLayout, QPushButton, QProgressBar,
                             QLabel, QSizePolicy, QScrollArea, QApplication,
                             QMessageBox)

# ---- Imports: local

from gwhat.widgets.buttons import ExportDataButton
from gwhat.common.widgets import QFrameLayout, QDoubleSpinBox, HSep
from gwhat.gwrecharge.gwrecharge_calc2 import RechgEvalWorker
from gwhat.gwrecharge.gwrecharge_plot_results import FigureStackManager
from gwhat.gwrecharge.glue import GLUEDataFrameBase
from gwhat.common.icons import QToolButtonSmall
from gwhat.common import icons


class RechgEvalWidget(QFrameLayout):

    sig_new_gluedf = QSignal(GLUEDataFrameBase)

    def __init__(self, parent):
        super(RechgEvalWidget, self).__init__(parent)
        self.setWindowTitle('Recharge Calibration Setup')
        self.setWindowFlags(Qt.Window)

        self.wxdset = None
        self.wldset = None
        self.figstack = FigureStackManager(parent=self)

        self.progressbar = QProgressBar()
        self.progressbar.setValue(0)
        self.progressbar.hide()
        self.__initUI__()

        # Set the worker and thread mechanics

        self.rechg_worker = RechgEvalWorker()
        self.rechg_worker.sig_glue_finished.connect(self.receive_glue_calcul)
        self.rechg_worker.sig_glue_progress.connect(self.progressbar.setValue)

        self.rechg_thread = QThread()
        self.rechg_worker.moveToThread(self.rechg_thread)
        self.rechg_thread.started.connect(self.rechg_worker.eval_recharge)

    def __initUI__(self):

        class QRowLayout(QWidget):
            def __init__(self, items, parent=None):
                super(QRowLayout, self).__init__(parent)

                layout = QGridLayout()
                for col, item in enumerate(items):
                    layout.addWidget(item, 0, col)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setColumnStretch(0, 100)
                self.setLayout(layout)

        # ---- Parameters

        # Specific yield (Sy) :

        self.QSy_min = QDoubleSpinBox(0.05, 3)
        self.QSy_min.setRange(0.001, 1)

        self.QSy_max = QDoubleSpinBox(0.2, 3)
        self.QSy_max.setRange(0.001, 1)

        # Maximum readily available water (RASmax) :

        # units=' mm'

        self.QRAS_min = QDoubleSpinBox(5)
        self.QRAS_min.setRange(0, 999)

        self.QRAS_max = QDoubleSpinBox(40)
        self.QRAS_max.setRange(0, 999)

        # Runoff coefficient (Cro) :

        self.CRO_min = QDoubleSpinBox(0.1, 3)
        self.CRO_min.setRange(0, 1)

        self.CRO_max = QDoubleSpinBox(0.3, 3)
        self.CRO_max.setRange(0, 1)

        # Snowmelt parameters :

        # units=' °C'

        self._Tmelt = QDoubleSpinBox(0, 1)
        self._Tmelt.setRange(-25, 25)

        # units=' mm/°C'

        self._CM = QDoubleSpinBox(4, 1, 0.1, )
        self._CM.setRange(0.1, 100)

        # units=' days'

        self._deltaT = QDoubleSpinBox(0, 0, )
        self._deltaT.setRange(0, 999)

        class QLabelCentered(QLabel):
            def __init__(self, text):
                super(QLabelCentered, self).__init__(text)
                self.setAlignment(Qt.AlignCenter)

        # ---- Parameters

        params_group = QFrameLayout()
        params_group.setContentsMargins(10, 5, 10, 0)  # (L, T, R, B)
        params_group.setObjectName("viewport")
        params_group.setStyleSheet("#viewport {background-color:transparent;}")

        row = 0
        params_group.addWidget(QLabel('Sy :'), row, 0)
        params_group.addWidget(self.QSy_min, row, 1)
        params_group.addWidget(QLabelCentered('to'), row, 2)
        params_group.addWidget(self.QSy_max, row, 3)
        row += 1
        params_group.addWidget(QLabel('RAS<sub>max</sub> :'), row, 0)
        params_group.addWidget(self.QRAS_min, row, 1)
        params_group.addWidget(QLabelCentered('to'), row, 2)
        params_group.addWidget(self.QRAS_max, row, 3)
        params_group.addWidget(QLabel('mm'), row, 4)
        row += 1
        params_group.addWidget(QLabel('Cro :'), row, 0)
        params_group.addWidget(self.CRO_min, row, 1)
        params_group.addWidget(QLabelCentered('to'), row, 2)
        params_group.addWidget(self.CRO_max, row, 3)
        row += 1
        params_group.setRowMinimumHeight(row, 10)
        row += 1
        params_group.addWidget(QLabel('Tmelt :'), row, 0)
        params_group.addWidget(self._Tmelt, row, 1)
        params_group.addWidget(QLabel('°C'), row, 2, 1, 3)
        row += 1
        params_group.addWidget(QLabel('CM :'), row, 0)
        params_group.addWidget(self._CM, row, 1)
        params_group.addWidget(QLabel('mm/°C'), row, 2, 1, 3)
        row += 1
        params_group.addWidget(QLabel('deltaT :'), row, 0)
        params_group.addWidget(self._deltaT, row, 1)
        params_group.addWidget(QLabel('days'), row, 2, 1, 3)
        row += 1
        params_group.setRowStretch(row, 100)
        params_group.setColumnStretch(5, 100)

        # ---- Layout ----

        qtitle = QLabel('Parameter Range')
        qtitle.setAlignment(Qt.AlignCenter)

        sa = QScrollArea()
        sa.setWidget(params_group)
        sa.setWidgetResizable(True)
        sa.setFrameStyle(0)
        sa.setStyleSheet("QScrollArea {background-color:transparent;}")
        sa.setSizePolicy(QSizePolicy(QSizePolicy.Ignored,
                                     QSizePolicy.Preferred))

        # ---- Main Layout

        self.addWidget(qtitle, 0, 0)
        self.addWidget(HSep(), 1, 0)
        self.addWidget(sa, 2, 0)
        self.addWidget(HSep(), 3, 0)
        self.setRowMinimumHeight(4, 5)
        self.addWidget(self.setup_toolbar(), 5, 0)

        self.setRowStretch(2, 100)
        self.setVerticalSpacing(5)
        self.setContentsMargins(0, 0, 0, 10)   # (L, T, R, B)

    def setup_toolbar(self):
        """Setup the toolbar of the widget. """
        toolbar = QWidget()

        btn_calib = QPushButton('Compute Recharge')
        btn_calib.clicked.connect(self.btn_calibrate_isClicked)

        self.btn_show_result = QToolButtonSmall(icons.get_icon('search'))
        self.btn_show_result.clicked.connect(self.figstack.show)
        self.btn_show_result.setToolTip("Show GLUE results.")

        self.btn_save_glue = ExportGLUEButton(self.wxdset)

        layout = QGridLayout(toolbar)
        layout.addWidget(btn_calib, 0, 0)
        layout.addWidget(self.btn_show_result, 0, 1)
        layout.addWidget(self.btn_save_glue, 0, 2)
        layout.setContentsMargins(10, 0, 10, 0)  # (L, T, R, B)

        return toolbar

    def set_wldset(self, wldset):
        """Set the namespace for the water level dataset."""
        self.wldset = wldset
        gluedf = None if wldset is None else wldset.get_glue_at(-1)
        if gluedf is not None:
            self._setup_ranges_from_wldset(gluedf)
        self.figstack.set_gluedf(gluedf)
        self.btn_save_glue.set_model(gluedf)

    def _setup_ranges_from_wldset(self, gluedf):
        """
        Set the parameter range values from the last values that were used
        to produce the last GLUE results saved into the project.
        """
        if gluedf is not None:
            self.QSy_min.setValue(min(gluedf['ranges']['Sy']))
            self.QSy_max.setValue(max(gluedf['ranges']['Sy']))

            self.CRO_min.setValue(min(gluedf['ranges']['Cro']))
            self.CRO_max.setValue(max(gluedf['ranges']['Cro']))

            self.QRAS_min.setValue(min(gluedf['ranges']['RASmax']))
            self.QRAS_max.setValue(max(gluedf['ranges']['RASmax']))

            self._Tmelt.setValue(gluedf['params']['tmelt'])
            self._CM.setValue(gluedf['params']['CM'])
            self._deltaT.setValue(gluedf['params']['deltat'])

    def get_Range(self, name):
        if name == 'Sy':
            return [self.QSy_min.value(), self.QSy_max.value()]
        elif name == 'RASmax':
            return [self.QRAS_min.value(), self.QRAS_max.value()]
        elif name == 'Cro':
            return [self.CRO_min.value(), self.CRO_max.value()]
        else:
            raise ValueError('Name must be either Sy, Rasmax or Cro.')

    @property
    def Tmelt(self):
        return self._Tmelt.value()

    @property
    def CM(self):
        return self._CM.value()

    @property
    def deltaT(self):
        return self._deltaT.value()

    def btn_calibrate_isClicked(self):
        """
        Handles when the button to compute recharge and its uncertainty is
        clicked.
        """
        self.start_glue_calcul()

    def start_glue_calcul(self):
        """
        Start the method to evaluate ground-water recharge and its
        uncertainty.
        """
        # Set the parameter ranges.

        self.rechg_worker.Sy = self.get_Range('Sy')
        self.rechg_worker.Cro = self.get_Range('Cro')
        self.rechg_worker.RASmax = self.get_Range('RASmax')

        self.rechg_worker.TMELT = self.Tmelt
        self.rechg_worker.CM = self.CM
        self.rechg_worker.deltat = self.deltaT

        # Set the data and check for errors.

        error = self.rechg_worker.load_data(self.wxdset, self.wldset)
        if error is not None:
            QMessageBox.warning(self, 'Warning', error, QMessageBox.Ok)
            return

        # Start the computation of groundwater recharge.

        self.progressbar.show()
        waittime = 0
        while self.rechg_thread.isRunning():
            time.sleep(0.1)
            waittime += 0.1
            if waittime > 15:
                print('Impossible to quit the thread.')
                return
        self.rechg_thread.start()

    def receive_glue_calcul(self, glue_dataframe):
        """
        Handle the plotting of the results once ground-water recharge has
        been evaluated.
        """
        self.rechg_thread.quit()
        self.progressbar.hide()
        if glue_dataframe is None:
            msg = ("Recharge evaluation was not possible because all"
                   " the models produced were deemed non-behavioural."
                   "\n\n"
                   "This usually happens when the range of values for"
                   " Sy, RASmax, and Cro are too restrictive or when the"
                   " Master Recession Curve (MRC) does not represent well the"
                   " behaviour of the observed hydrograph.")
            QMessageBox.warning(self, 'Warning', msg, QMessageBox.Ok)
        else:
            self.wldset.clear_glue()
            self.wldset.save_glue(glue_dataframe)
            self.sig_new_gluedf.emit(glue_dataframe)

            self.btn_save_glue.set_model(glue_dataframe)
            self.figstack.set_gluedf(glue_dataframe)


class ExportGLUEButton(ExportDataButton):
    """
    A toolbutton with a popup menu that handles the export of GLUE data
    to file.
    """
    MODEL_TYPE = GLUEDataFrameBase
    TOOLTIP = "Export GLUE data."

    def __init__(self, model=None, workdir=None, parent=None):
        super(ExportGLUEButton, self).__init__(model, workdir, parent)

    def setup_menu(self):
        """Setup the menu of the button tailored to the model."""
        super(ExportGLUEButton, self).setup_menu()
        self.menu().addAction('Export GLUE water budget as...',
                              self.save_water_budget_tofile)
        self.menu().addAction('Export GLUE water levels as...',
                              self.save_water_levels_tofile)

    # ---- Export data

    @QSlot()
    def save_water_budget_tofile(self):
        """
        Prompt a dialog to select a file and save the GLUE water budget.
        """
        fname = self.select_savefilename("Save GLUE water budget",
                                         "glue_water_budget.xlsx",
                                         "*.xlsx;;*.xls;;*.csv")
        if fname:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                self.model.save_mly_glue_budget_to_file(fname)
            except PermissionError:
                self.show_permission_error()
                self.save_water_budget_tofile()
            QApplication.restoreOverrideCursor()

    @QSlot()
    def save_water_levels_tofile(self):
        """
        Prompt a dialog to select a file and save the GLUE water levels.
        """
        fname = self.select_savefilename("Save GLUE water levels",
                                         "glue_water_levels.xlsx",
                                         "*.xlsx;;*.xls;;*.csv")
        if fname:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                self.model.save_glue_waterlvl_to_file(fname)
            except PermissionError:
                self.show_permission_error()
                self.save_water_levels_tofile()
            QApplication.restoreOverrideCursor()


# %% ---- if __name__ == '__main__'

if __name__ == '__main__':
    from gwhat.gwrecharge.gwrecharge_calc2 import load_glue_from_npy
    from gwhat.gwrecharge.glue import GLUEDataFrame
    import sys

    app = QApplication(sys.argv)

    GLUE_RAWDATA = load_glue_from_npy('glue_rawdata.npy')
    GLUE_DF = GLUEDataFrame(GLUE_RAWDATA)

    BTN_EXPORT_GLUE = ExportGLUEButton(GLUE_DF)
    BTN_EXPORT_GLUE.show()

    sys.exit(app.exec_())
