# -*- coding: utf-8 -*-
"""
Created on Sun Jul  5 00:28:27 2015

@author: jsgosselin
"""

# STANDARD LIBRARY IMPORTS :
import sys

# THIRD PARTY IMPORTS :
from PySide import QtGui, QtCore

# PERSONAL IMPORTS :
import database as db


###############################################################################


class VSep(QtGui.QFrame):  # vertical separators
    def __init__(self, parent=None):
        super(VSep, self).__init__(parent)
        self.setFrameStyle(db.styleUI().VLine)


###############################################################################


class MyQToolButton(QtGui.QToolButton):

    def __init__(self, Qicon, ToolTip, IconSize=db.styleUI().iconSize,
                 autoRaise=True, enabled=True, *args, **kargs):
        super(MyQToolButton, self).__init__(*args, **kargs)

        self.setIcon(Qicon)
        self.setToolTip(ToolTip)
        self.setAutoRaise(autoRaise)
        self.setIconSize(IconSize)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setEnabled(enabled)


###############################################################################


class MyQErrorMessageBox(QtGui.QMessageBox):

    def __init__(self, parent=None):
        super(MyQErrorMessageBox, self).__init__(parent)

        self.setIcon(QtGui.QMessageBox.Warning)
        self.setWindowTitle('Error Message')
        self.setWindowIcon(db.Icons().WHAT)


###############################################################################


class QToolPanel(QtGui.QWidget):

    """
    A custom widget that mimicks the behavior of the "Tools" sidepanel in
    Adobe Acrobat. It is derived from a QToolBox with the following variants:

    1. Only one tool can be displayed at a time.
    2. Unlike the stock QToolBox widget, it is possible to hide all the tools.
    3. It is also possible to hide the current displayed tool by clicking on
       its header.
    4. The tools that are hidden are marked by a right-arrow icon, while the
       tool that is currently displayed is marked with a down-arrow icon.
    5. Closed and Expanded arrows can be set from custom icons.
    """

    def __init__(self, parent=None):
        super(QToolPanel, self).__init__(parent)

        self.__iclosed = QtGui.QWidget().style().standardIcon(
            QtGui.QStyle.SP_ToolBarHorizontalExtensionButton)
        self.__iexpand = QtGui.QWidget().style().standardIcon(
            QtGui.QStyle.SP_ToolBarVerticalExtensionButton)

        self.setLayout(QtGui.QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        self.__currentIndex = -1

    def setIcons(self, ar_right, ar_down):  # =================================
        self.__iclosed = ar_right
        self.__iexpand = ar_down

    def addItem(self, tool, text):  # =========================================

        N = self.layout().rowCount()

        # Add Header :

        head = QtGui.QPushButton(text)
        head.setIcon(self.__iclosed)
        head.clicked.connect(self.__isClicked__)
        head.setStyleSheet("QPushButton {text-align:left;}")

        self.layout().addWidget(head, N-1, 0)

        # Add Item in a ScrollArea :

        scrollarea = QtGui.QScrollArea()
        scrollarea.setFrameStyle(0)
        scrollarea.hide()
        scrollarea.setStyleSheet("QScrollArea {background-color:transparent;}")
        scrollarea.setWidgetResizable(True)

        tool.setObjectName("myViewport")
        tool.setStyleSheet("#myViewport {background-color:transparent;}")
        scrollarea.setWidget(tool)

        self.layout().addWidget(scrollarea, N, 0)
        self.layout().setRowStretch(N+1, 100)

    def __isClicked__(self):  # ===============================================

        for row in range(0, self.layout().rowCount()-1, 2):

            head = self.layout().itemAtPosition(row, 0).widget()
            tool = self.layout().itemAtPosition(row+1, 0).widget()

            if head == self.sender():
                if self.__currentIndex == row:
                    # if clicked tool is open, close it
                    head.setIcon(self.__iclosed)
                    tool.hide()
                    self.__currentIndex = -1
                else:
                    # if clicked tool is closed, expand it
                    head.setIcon(self.__iexpand)
                    tool.show()
                    self.__currentIndex = row
            else:
                # close all the other tools so that only one tool can be
                # expanded at a time.
                head.setIcon(self.__iclosed)
                tool.hide()


###############################################################################

class MyHorizHeader(QtGui.QHeaderView):

    # https://forum.qt.io/topic/30598/
    # solved-how-to-display-subscript-text-in-header-of-qtableview/5

    # http://stackoverflow.com/questions/1956542/
    # how-to-make-item-view-render-rich-html-text-in-qt

    # http://stackoverflow.com/questions/2336079/
    # can-i-have-more-than-one-line-in-a-table-header-in-qt

    def __init__(self, parent=None):
        super(MyHorizHeader, self).__init__(QtCore.Qt.Horizontal, parent)

        # http://stackoverflow.com/questions/18777554/
        # why-wont-my-custom-qheaderview-allow-sorting/18777555#18777555

        self.setClickable(True)
        self.setHighlightSections(True)
        self.showSectionSep = False
        self.container = '''
                         <table border="0" cellpadding="0" cellspacing="0"
                                align="center" width="100%%">
                           <tr>
                             <td valign=middle align=center
                                 style="padding-top:4px; padding-bottom:4px">
                               %s
                             </td>
                           </tr>
                         </table>
                         '''
        # Arbitrary init value. This is updated as columns are added
        # to the table.
        self.heightHint = 20

    def paintSection(self, painter, rect, logicalIndex):  # ===================

        # This is used only if "showSectionSep == True. Otherwise, the header
        # is painted with the method "paintHeader"

        if not rect.isValid():
            return

        opt = QtGui.QStyleOptionHeader()
        opt.initFrom(self)
        opt.rect = rect
        opt.section = logicalIndex
        opt.text = ""

        visual = self.visualIndex(logicalIndex)
        if self.count() == 1:
            opt.position = QtGui.QStyleOptionHeader.OnlyOneSection
        elif visual == 0:
            opt.position = QtGui.QStyleOptionHeader.Beginning
        elif visual == self.count() - 1:
            opt.position = QtGui.QStyleOptionHeader.End
        else:
            opt.position = QtGui.QStyleOptionHeader.Middle

        self.style().drawControl(QtGui.QStyle.CE_Header, opt, painter, self)


    def paintEvent(self, event): #----------------------------------------------

        qp = QtGui.QPainter()

        qp.begin(self.viewport())

        if self.showSectionSep:
            QtGui.QHeaderView.paintEvent(self, event)
        else:
            qp.save()
            self.paintHeader(qp)
            qp.restore()

        qp.save()
        self.paintLabels(qp)
        qp.restore()

        qp.end()


    def paintLabels(self, qp): #------------------------------------------------

        headerTable  = '''
                       <table border="0" cellpadding="0" cellspacing="0"
                              align="center" width="100%%">
                         <tr>
                           <td colspan="3"></td>
                           <td colspan="4" align=center style="padding-top:4px">
                             Correlation Coefficients
                           </td>
                         </tr>
                         <tr>
                           <td colspan="3"></td>
                           <td colspan="4"><hr width=100%%></td>
                         </tr>
                         <tr>
                       '''
        for logicalIndex in range(self.count()):

            label = str(self.model().headerData(logicalIndex,
                                                self.orientation()))

            #------------------------------------------ Highlighting Header ----

            if self.highlightSections():
                selectedIndx = self.selectionModel().selectedIndexes()
                for index in selectedIndx:
                    if (logicalIndex == index.column()) == True:
                        label = '<b>%s<b>' % label
                        break
                    else:
                        pass

            sectionWidth = self.sectionSize(logicalIndex)
            headerTable += '''
                           <td valign=middle align=center width=%d
                            style="padding-top:0px; padding-bottom:4px">
                             %s
                           </td>
                           ''' % (sectionWidth, label)
        headerTable += '''
                         </tr>
                       </table>
                       '''

        TextDoc = QtGui.QTextDocument()
        TextDoc.setTextWidth(self.size().width())
        TextDoc.setDocumentMargin(0)
        TextDoc.setHtml(headerTable)
        self.heightHint = TextDoc.size().height()

        TextDoc.drawContents(qp,
                             QtCore.QRect(0, 0, self.size().width(),
                                                self.size().height()))

    def paintHeader(self, qp): #------------------------------------------------

        # Paint the header box for the entire width of the table.
        # This effectively eliminates the separators between each
        # individual section.

        opt = QtGui.QStyleOptionHeader()
        opt.rect = QtCore.QRect(0, 0, self.size().width(), self.size().height())

        self.style().drawControl(QtGui.QStyle.CE_Header, opt, qp, self)

    def sizeHint(self): #-------------------------------------------------------

        baseSize = QtGui.QHeaderView.sizeHint(self)
        baseSize.setHeight(self.heightHint)

        return baseSize




##===============================================================================
#class MyQNavigationToolbar(QtGui.QWidget):
#    """
#    This is a work-in-progress to be able to build a navigation toolbar with
#    a memory.
#    """
##===============================================================================
#
#    currentContentChanged = QtCore.Signal(str)
#
#    def __init__(self, parent=None):
#        super(MyQNavigationToolbar, self).__init__(parent)
#
#        self.currentIndex = 0
#        self.contentMemory = []
#        self.currentContent = ''
#
#        self.initUI()
#
#    def initUI(self):
#
#        iconDB = db.icons()
#        styleDB = db.styleUI()
#
#        self.btn_goNext = QtGui.QToolButton()
#        self.btn_goNext.setIcon(iconDB.go_next)
#        self.btn_goNext.setAutoRaise(True)
#        self.btn_goNext.setToolTip('Click to go forward.')
#        self.btn_goNext.setIconSize(styleDB.iconSize2)
#        self.btn_goNext.setEnabled(False)
#
#        self.btn_goPrevious = QtGui.QToolButton()
#        self.btn_goPrevious.setIcon(iconDB.go_previous)
#        self.btn_goPrevious.setAutoRaise(True)
#        self.btn_goPrevious.setToolTip('Click to go back.')
#        self.btn_goPrevious.setIconSize(styleDB.iconSize2)
#        self.btn_goPrevious.setEnabled(False)
#
#        self.btn_goLast = QtGui.QToolButton()
#        self.btn_goLast.setIcon(iconDB.go_last)
#        self.btn_goLast.setAutoRaise(True)
#        self.btn_goLast.setToolTip('Click to go last.')
#        self.btn_goLast.setIconSize(styleDB.iconSize2)
#        self.btn_goLast.setEnabled(False)
#
#        self.btn_goFirst = QtGui.QToolButton()
#        self.btn_goFirst.setIcon(iconDB.go_first)
#        self.btn_goFirst.setAutoRaise(True)
#        self.btn_goFirst.setToolTip('Click to go first.')
#        self.btn_goFirst.setIconSize(styleDB.iconSize2)
#        self.btn_goFirst.setEnabled(False)
#
#        goToolbar_grid = QtGui.QGridLayout()
#        goToolbar_widg = QtGui.QFrame()
#
#        col = 0
#        goToolbar_grid.addWidget(self.btn_goFirst, 0, col)
#        col += 1
#        goToolbar_grid.addWidget(self.btn_goPrevious, 0, col)
#        col += 1
#        goToolbar_grid.addWidget(self.btn_goNext, 0, col)
#        col += 1
#        goToolbar_grid.addWidget(self.btn_goLast, 0, col)
#
#        goToolbar_grid.setContentsMargins(0, 0, 0, 0) # [L, T, R, B]
#        goToolbar_grid.setSpacing(5)
#
#        goToolbar_widg.setLayout(goToolbar_grid)
#
#        #----------------------------------------------------------- EVENTS ----
#
#        self.btn_goLast.clicked.connect(self.button_isClicked)
#        self.btn_goFirst.clicked.connect(self.button_isClicked)
#        self.btn_goNext.clicked.connect(self.button_isClicked)
#        self.btn_goPrevious.clicked.connect(self.button_isClicked)
#
#    def button_isClicked(self):
#
#         # http://zetcode.com/gui/pysidetutorial/eventsandsignals/
#
#        button = self.sender()
#
#        if button == self.btn_goFirst:
#            self.currentIndex = 0
#
#        elif button == self.btn_goLast:
#            self.currentIndex = len(self.contentMemory) - 1
#
#        elif button == self.btn_goPrevious:
#            self.currentIndex += -1
#
#        elif button == self.btn_goNext:
#            self.currentIndex += 1
#
#        self.currentContent = self.contentMemory(self.currentIndex)
#
#        self.update_current_state()
#
#    def update_current_state(self): #===========================================
#
#        if len(self.contentMemory) > 1:
#
#            if self.currentIndex == (len(self.contentMemory) - 1):
#                self.btn_goLast.setEnabled(False)
#                self.btn_goNext.setEnabled(False)
#                self.btn_goFirst.setEnabled(True)
#                self.btn_goPrevious.setEnabled(True)
#            elif self.currentIndex == 0:
#                self.btn_goLast.setEnabled(True)
#                self.btn_goNext.setEnabled(True)
#                self.btn_goFirst.setEnabled(False)
#                self.btn_goPrevious.setEnabled(False)
#            else:
#                self.btn_goLast.setEnabled(True)
#                self.btn_goNext.setEnabled(True)
#                self.btn_goFirst.setEnabled(True)
#                self.btn_goPrevious.setEnabled(True)
#
#        else:
#
#            self.btn_goLast.setEnabled(False)
#            self.btn_goNext.setEnabled(False)
#            self.btn_goFirst.setEnabled(False)
#            self.btn_goPrevious.setEnabled(False)
#
#        self.currentContentChanged.emit(self.currentContent)
#
#
#    def addContent(self, content):
#
#        self.contentMemory.append(content)
#        self.currentIndex = len(self.contentMemory) - 1
#        self.currentContent = self.contentMemory(self.currentIndex)
#
#        self.update_current_state()
#
#    def clear(self):
#
#        self.currentIndex = 0
#        self.contentMemory = []
#        self.currentContent = ''
#
#        self.update_current_state()





if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)

    instance1 = QToolPanel()

    #---- SHOW ----

    instance1.show()

    qr = instance1.frameGeometry()
    cp = QtGui.QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    instance1.move(qr.topLeft())

    instance1.addItem(QtGui.QLabel('Example Toolbox'), 'Tool #1')
    instance1.addItem(QtGui.QLabel('Example Toolbox'), 'Tool #2')

    sys.exit(app.exec_())
