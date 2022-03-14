# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © 2014-2021 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# Source: http://www.gnu.org/licenses/gpl-howto.html

# It is often said when developing interfaces that you need to fail fast,
# and iterate often. When creating a UI, you will make mistakes. Just keep
# moving forward, and remember to keep your UI out of the way.
# http://blog.teamtreehouse.com/10-user-interface-design-fundamentals
# -----------------------------------------------------------------------------

# ---- Standard library imports
import os
import platform
import sys
import traceback
from time import ctime
from multiprocessing import freeze_support

# ---- Third party imports
from qtpy.QtCore import QObject, Signal, QUrl
from PyQt5.QtGui import QDesktopServices
from qtpy.QtWidgets import QMainWindow, QWidget, QGridLayout

# ---- Local imports
from gwhat import __namever__, __appname__, __project_url__
from gwhat.config.main import CONF
from gwhat.config.ospath import save_path_to_configs, get_path_from_configs
import gwhat.HydroPrint2 as HydroPrint
import gwhat.HydroCalc2 as HydroCalc
from gwhat.widgets.about import AboutWhat
from gwhat.widgets.tabwidget import TabWidget
from gwhat.widgets.console import StreamConsole
from gwhat.projet.manager_projet import ProjetManager
from gwhat.projet.manager_data import DataManager
from gwhat.utils import icons
from gwhat.utils.qthelpers import (
    create_toolbutton, qbytearray_to_hexstate, hexstate_to_qbytearray)


freeze_support()


class MainWindow(QMainWindow):

    def __init__(self, except_hook=None, splash=None):
        super().__init__()
        self.splash = splash
        self.except_hook = except_hook
        if except_hook is not None:
            except_hook.sig_except_caught.connect(self._handle_except)

        self.setWindowTitle(__namever__)
        self.setWindowIcon(icons.get_icon('master'))

        if platform.system() == 'Windows':
            import ctypes
            myappid = 'gwhat_application'  # arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                myappid)

        # Setup the project manager. and data managers.
        self.show_splash_message("Initializing project and data managers...")
        self.pmanager = ProjetManager(self)
        self.pmanager.currentProjetChanged.connect(self.new_project_loaded)

        # Setup the data manager.
        self.dmanager = DataManager(parent=self, pm=self.pmanager)
        self.dmanager.sig_new_console_msg.connect(self.write2console)

        # Generate the GUI.
        self.setup()
        self._restore_window_geometry()
        self._restore_window_state()

        # Load the last opened project.
        projectfile = get_path_from_configs('main', 'last_project_filepath')
        result = self.pmanager.load_project(projectfile)
        if result is False:
            self.tab_hydrograph.setEnabled(False)
            self.tab_hydrocalc.setEnabled(False)

    def setup(self):
        """
        Setup the GUI of the main window.
        """
        self.show_splash_message("Initializing main window...")

        # Setup mainwindow tab widget.
        self.tab_widget = TabWidget()
        self.tab_widget.setCornerWidget(self.pmanager)

        # Setup About GWHAT.
        self.about_win = None
        self.about_btn = create_toolbutton(
            self,
            icon='info',
            text="About...",
            tip='About GWHAT...',
            triggered=lambda: self.show_about_dialog())
        self.tab_widget.add_button(self.about_btn)

        # Setup report bug button.
        self.bug_btn = create_toolbutton(
            self,
            icon='report_bug',
            text="Report...",
            tip='Report issue...',
            triggered=lambda: QDesktopServices.openUrl(
                QUrl(__project_url__ + "/issues")))
        self.tab_widget.add_button(self.bug_btn)

        # Setup GWHAT message console.
        self.console = StreamConsole()
        msg = '<font color=black>Thanks for using %s.</font>' % __appname__
        self.write2console(msg)
        msg = ('Please help GWHAT by reporting bugs on our '
               '<a href="https://github.com/jnsebgosselin/gwhat/issues">'
               'Issues Tracker</a>.')
        self.write2console('<font color=black>%s</font>' % msg)

        self.btn_console = create_toolbutton(
            self,
            icon='console',
            text="Console...",
            tip="GWHAT console...",
            triggered=lambda: self.console.show())
        self.tab_widget.add_button(self.btn_console)

        # Setup the tab plot hydrograph.
        self.show_splash_message("Initializing plot hydrograph...")
        self.tab_hydrograph = HydroPrint.HydroprintGUI(
            self.dmanager, parent=self)
        self.tab_widget.addTab(self.tab_hydrograph, 'Plot Hydrograph')
        self.tab_hydrograph.ConsoleSignal.connect(self.write2console)

        # Setup the tab analyse hydrograph.
        self.show_splash_message("Initializing analyse hydrograph...")
        self.tab_hydrocalc = HydroCalc.WLCalc(self.dmanager)
        self.tab_widget.addTab(self.tab_hydrocalc, 'Analyze Hydrograph')
        self.tab_hydrocalc.tools['mrc'].sig_new_mrc.connect(
            self.tab_hydrograph.mrc_wl_changed)
        self.tab_hydrocalc.rechg_eval_widget.sig_new_gluedf.connect(
            self.tab_hydrograph.glue_wl_changed)

        # Add each tab to the tab widget.
        self.tab_widget.currentChanged.connect(self.sync_datamanagers)
        self.tab_widget.setCurrentIndex(
            CONF.get('main', 'mainwindow_current_tab'))
        self.sync_datamanagers()

        # Setup the layout of the main widget.
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_grid = QGridLayout(main_widget)
        main_grid.addWidget(self.tab_widget, 0, 0)
        main_grid.addWidget(
            self.tab_hydrocalc.rechg_eval_widget.progressbar, 3, 0)

    def show_about_dialog(self):
        """
        Create and show the About GWHAT window when the about button
        is clicked.
        """
        pytesting = os.environ.get('GWHAT_PYTEST', 'False') == 'True'
        if self.about_win is None:
            self.about_win = AboutWhat(self, pytesting)
        if pytesting:
            self.about_win.show()
        else:
            self.about_win.exec_()

    def write2console(self, text):
        """
        This function is the bottle neck through which all messages writen
        in the console must go through.
        """
        textime = '<font color=black>[%s] </font>' % ctime()[4:-8]
        self.console.write(textime + text)

    def sync_datamanagers(self):
        """
        Move the data manager from tab 'Plot Hydrograph' to tab
        'Analyze Hydrograph' and vice-versa.
        """
        max_width = self.dmanager.sizeHint().width()
        for i in range(self.tab_widget.count()):
            max_width = max(
                max_width,
                self.tab_widget.widget(i).right_panel.sizeHint().width())
        for i in range(self.tab_widget.count()):
            self.tab_widget.widget(i).layout().setColumnMinimumWidth(
                2, max_width)
        self.tab_widget.currentWidget().right_panel.layout().addWidget(
            self.dmanager, 0, 0)

    def new_project_loaded(self):
        """Handles when a new project is loaded in the project manager."""

        # Save the project file path in the configs.
        save_path_to_configs('main', 'last_project_filepath',
                             self.pmanager.projet.filename)

        # Update the GUI.
        self.tab_hydrograph.setEnabled(True)
        self.tab_hydrocalc.setEnabled(True)

    def show_splash_message(self, message):
        """Set splash text."""
        if self.splash is not None:
            self.splash.showMessage(message)

    # ---- Qt method override/extension
    def closeEvent(self, event):
        """Qt method override to close the project before close the app."""
        self._save_window_geometry()
        self._save_window_state()
        CONF.set(
            'main', 'mainwindow_current_tab', self.tab_widget.currentIndex())

        print('Closing projet')
        self.pmanager.close()
        self.dmanager.close()

        print('Closing GWHAT')
        self.console.close()
        if self.about_win is not None:
            self.about_win.close()
        self.tab_hydrocalc.close()
        self.tab_hydrograph.close()
        event.accept()

    # ---- Main window settings
    def _restore_window_geometry(self):
        """
        Restore the geometry of this mainwindow from the value saved
        in the config.
        """
        hexstate = CONF.get('main', 'window/geometry', None)
        if hexstate:
            hexstate = hexstate_to_qbytearray(hexstate)
            self.restoreGeometry(hexstate)
        else:
            from gwhat.config.gui import INIT_MAINWINDOW_SIZE
            self.resize(*INIT_MAINWINDOW_SIZE)

    def _save_window_geometry(self):
        """
        Save the geometry of this mainwindow to the config.
        """
        hexstate = qbytearray_to_hexstate(self.saveGeometry())
        CONF.set('main', 'window/geometry', hexstate)

    def _restore_window_state(self):
        """
        Restore the state of this mainwindow’s toolbars and dockwidgets from
        the value saved in the config.
        """
        # Then we appply saved configuration if it exists.
        hexstate = CONF.get('main', 'window/state', None)
        if hexstate:
            hexstate = hexstate_to_qbytearray(hexstate)
            self.restoreState(hexstate)

    def _save_window_state(self):
        """
        Save the state of this mainwindow’s toolbars and dockwidgets to
        the config.
        """
        hexstate = qbytearray_to_hexstate(self.saveState())
        CONF.set('main', 'window/state', hexstate)

    # ---- Handlers
    def _handle_except(self, log_msg):
        """
        Handle raised exceptions that have not been handled properly
        internally and need to be reported for bug fixing.
        """
        from gwhat.widgets.dialogs import ExceptDialog
        except_dialog = ExceptDialog(log_msg)
        except_dialog.exec_()


class ExceptHook(QObject):
    """
    A Qt object to caught exceptions and emit a formatted string of the error.
    """
    sig_except_caught = Signal(str)

    def __init__(self):
        super().__init__()
        sys.excepthook = self.excepthook

    def excepthook(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions."""
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        if not issubclass(exc_type, SystemExit):
            log_msg = ''.join(traceback.format_exception(
                exc_type, exc_value, exc_traceback))
            self.sig_except_caught.emit(log_msg)


def except_hook(cls, exception, traceback):
    """
    Used to override the default sys except hook so that this application
    doesn't automatically exit when an unhandled exception occurs.

    See this StackOverflow answer for more details :
    https://stackoverflow.com/a/33741755/4481445
    """
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    from gwhat.utils.qthelpers import create_qapplication
    app = create_qapplication()

    from gwhat.widgets.splash import SplashScrn
    splash = SplashScrn()
    splash.showMessage(f"Starting {__namever__}...")

    sys.excepthook = except_hook
    except_hook = ExceptHook()

    print("Initializing MainWindow...")
    main = MainWindow(except_hook, splash)
    splash.finish(main)
    main.show()
    print("Successfully initialized MainWindow.")

    sys.exit(app.exec_())
