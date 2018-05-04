# -*- coding: utf-8 -*-

# Copyright (C) 2005-2005 Trolltech AS. All rights reserved.
# http://www.trolltech.com/products/qt/opensource.html
#
# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
#
# This code is derived from a code provided in the example classes of the Qt
# Tookit by Trolltech AS, licensed under the terms of the GNU General Public
# License version 2.0 as published by the Free Software Foundation.

from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QRect
from PyQt5.QtGui import QImage, QPixmap, QPainter
from PyQt5.QtWidgets import QFrame, QScrollArea, QApplication, QWidget


class FigureCanvas(QFrame):

    def __init__(self, parent=None):
        super(FigureCanvas, self).__init__(parent)

        self.setLineWidth(2)
        self.setMidLineWidth(1)
        self.setStyleSheet("background-color: white")

        self.img = []
        self.qpix_buff = []

    def load_mpl_figure(self, mplfig, view_dpi):

        self.qpix_buff = []

        # ---------------------------------------------------- figure size ----

        bbox = mplfig.get_window_extent()
        self.fwidth = bbox.width
        self.fheight = bbox.height

        # ------------------------------------------ save figure to buffer ----

        # http://stackoverflow.com/questions/8598673/
        # how-to-save-a-pylab-figure-into-in-memory-file-which-can-be-read
        # -into-pil-image/8598881#8598881

        # http://stackoverflow.com/questions/1300908/
        # load-blob-image-data-into-qpixmap

        # Scale dpi of figure to view_dpi

        orig_fig_dpi = mplfig.get_dpi()
        mplfig.dpi = view_dpi

        # Propagate changes to renderer :

        mplfig.canvas.draw()
        renderer = mplfig.canvas.get_renderer()
        orig_ren_dpi = renderer.dpi
        renderer.dpi = view_dpi

        # Generate img buffer :

        imgbuf = mplfig.canvas.buffer_rgba()
        imgwidth = int(renderer.width)
        imgheight = int(renderer.height)

        # Restore fig and renderer dpi

        renderer.dpi = orig_ren_dpi
        mplfig.dpi = orig_fig_dpi

        # Convert buffer to QPixmap :

        self.img = QImage(imgbuf, imgwidth, imgheight, QImage.Format_ARGB32)
        self.img = QImage.rgbSwapped(self.img)
        self.img = QPixmap(self.img)

    def paintEvent(self, event):
        """Qt method override to paint a custom image on the Widget."""
        super(FigureCanvas, self).paintEvent(event)

        qp = QPainter()
        qp.begin(self)

        # Prepare paint rect :

        fw = self.frameWidth()
        rect = QRect(0 + fw, 0 + fw,
                     self.size().width() - 2 * fw,
                     self.size().height() - 2 * fw)

        # Check/update image buffer :

        qpix2print = None
        for qpix in self.qpix_buff:
            if qpix.size().width() == rect.width():
                qpix2print = qpix
                break

        if qpix2print is None:
            qpix2print = self.img.scaledToWidth(
                rect.width(), mode=Qt.SmoothTransformation)
            self.qpix_buff.append(qpix2print)

        # Draw pixmap :

#        qp.setRenderHint(QPainter.Antialiasing, True)
        qp.drawPixmap(rect, qpix2print)

        qp.end()


class ImageViewer(QScrollArea):                           # ImageViewer #
    """
    A scrollarea that displays a single FigureCanvas with zooming and panning
    capability with CTRL + Mouse_wheel and Left-press mouse button event.
    """

    zoomChanged = pyqtSignal(float)

    def __init__(self, parent=None):
        super(ImageViewer, self).__init__(parent)

        self.setWindowTitle('Image Viewer')
        self.setAlignment(Qt.AlignCenter)

        # Init. variable :

        self.scaleFactor = 0
        self.scaleStep = 1.2
        self.pan = False

        self.sfmax = 3
        self.sfmin = -3

        # ---- image container Set Up ----

        self.imageCanvas = FigureCanvas()

        self.imageCanvas.installEventFilter(self)
        self.setWidget(self.imageCanvas)

    def eventFilter(self, widget, event):
        """A filter to control the zooming and panning of the figure canvas."""

        # http://stackoverflow.com/questions/17525608/
        # event-filter-cannot-intercept-wheel-event-from-qscrollarea

        # http://stackoverflow.com/questions/20420072/
        # pyside-keypressevent-catching-enter-or-return

        # http://stackoverflow.com/questions/19113532/
        # qgraphicsview-zooming-in-and-out-under-mouse-position
        # -using-mouse-wheel

        # ZOOM ----------------------------------------------------------------

        if event.type() == QEvent.Wheel:

            # http://stackoverflow.com/questions/8772595/
            # how-to-check-if-a-key-modifier-is-pressed-shift-ctrl-alt

            modifiers = QApplication.keyboardModifiers()

            if modifiers == Qt.ControlModifier:
                if event.angleDelta().y() > 0:
                    self.zoomIn()
                else:
                    self.zoomOut()
                return True
            else:
                return False

        # PAN -----------------------------------------------------------------

        # Set ClosedHandCursor:

        elif event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                QApplication.setOverrideCursor(Qt.ClosedHandCursor)
                self.pan = True
                self.xclick = event.globalX()
                self.yclick = event.globalY()

        # Reset Cursor:

        elif event.type() == QEvent.MouseButtonRelease:
            QApplication.restoreOverrideCursor()
            self.pan = False

        # Move  ScrollBar:

        elif event.type() == QEvent.MouseMove:
            if self.pan is True:
                dx = self.xclick - event.globalX()
                self.xclick = event.globalX()

                dy = self.yclick - event.globalY()
                self.yclick = event.globalY()

                scrollBarH = self.horizontalScrollBar()
                scrollBarH.setValue(scrollBarH.value() + dx)

                scrollBarV = self.verticalScrollBar()
                scrollBarV.setValue(scrollBarV.value() + dy)

        return QWidget.eventFilter(self, widget, event)

    def zoomIn(self):
        """Scale the image up by one scale step."""
        if self.scaleFactor < self.sfmax:
            self.scaleFactor += 1
            self.scale_image()
            self.adjust_scrollbar(self.scaleStep)
        self.zoomChanged.emit(self.get_scaling())

    def zoomOut(self):
        """Scale the image down by one scale step."""
        if self.scaleFactor > self.sfmin:
            self.scaleFactor -= 1
            self.scale_image()
            self.adjust_scrollbar(1/self.scaleStep)
        self.zoomChanged.emit(self.get_scaling())

    def get_scaling(self):
        """Return the current scaling of the figure in percent."""
        return self.scaleStep**self.scaleFactor*100

    def scale_image(self):
        """Scale the image size."""
        new_width = int(self.imageCanvas.fwidth *
                        self.scaleStep ** self.scaleFactor)
        new_height = int(self.imageCanvas.fheight *
                         self.scaleStep ** self.scaleFactor)

        self.imageCanvas.setFixedSize(new_width, new_height)

    def load_mpl_figure(self, mplfig, view_dpi=150):
        self.imageCanvas.load_mpl_figure(mplfig, view_dpi)
        self.scale_image()
        self.imageCanvas.repaint()

    def reset_original_image(self):
        """Reset the image to its original size."""
        self.scaleFactor = 0
        self.scale_image()

    def adjust_scrollbar(self, f):
        """
        Adjust the scrollbar position to take into account the zooming of
        the figure.
        """
        # Adjust horizontal scrollbar :
        hb = self.horizontalScrollBar()
        hb.setValue(int(f * hb.value() + ((f - 1) * hb.pageStep()/2)))

        # Adjust the vertical scrollbar :
        vb = self.verticalScrollBar()
        vb.setValue(int(f * vb.value() + ((f - 1) * vb.pageStep()/2)))


if __name__ == '__main__':  # =================================================

    import sys
    import matplotlib.pyplot as plt
    import numpy as np
    plt.ioff()

    app = QApplication(sys.argv)

    # generate a mpl figure ---------------------------------------------------

    # generate data:

    N = 150
    x = np.random.rand(N)
    y = np.random.rand(N)
    colors = np.random.rand(N)
    area = np.pi * (15 * np.random.rand(N)) ** 2

    # setup figure and plot data:

    fig, ax = plt.subplots(facecolor='white', figsize=(8, 8))
    ax.scatter(x, y, s=area, c=colors, alpha=0.5)

    # display it in a image viewer --------------------------------------------

    imageViewer = ImageViewer()
    imageViewer.setMinimumSize(450, 450)
    imageViewer.load_mpl_figure(fig)
    imageViewer.show()

    sys.exit(app.exec_())
