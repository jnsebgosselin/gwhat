# -*- coding: utf-8 -*-
"""
Copyright 2014-2015 Jean-Sebastien Gosselin

email: jnsebgosselin@gmail.com

This file is part of WHAT (Well Hydrograph Analysis Toolbox)..

WHAT is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

#---- STANDARD LIBRARY IMPORTS ----

import sys

#---- THIRD PARTY IMPORTS ----

from PySide import QtGui, QtCore

#---- PERSONAL IMPORTS ----

import database as db

#===============================================================================
     
class AboutWhat(QtGui.QWidget):                                                 
    
#===============================================================================
    
    def __init__(self, software_version, last_modification, parent=None): #=====
        super(AboutWhat, self).__init__(parent)
        
        self.parent = parent
        self.software_version = software_version
        self.last_modification = last_modification
        
        self.initUI_About()   
        
    def initUI_About(self): #===================================================
        
        #--------------------------------------------------------- DATABASE ----
        
        iconDB = db.icons()
        styleDB = db.styleUI()

        #------------------------------------------------------ MAIN WINDOW ----
        
        self.setWindowTitle('Search for Weather Stations')
        self.setWindowIcon(iconDB.WHAT)
        self.setMinimumHeight(700)
        
        #----------------------------------------------------- AboutTextBox ----
        
        self.AboutTextBox = QtGui.QTextBrowser()
        self.AboutTextBox.installEventFilter(self)    
        self.AboutTextBox.setReadOnly(True)
        self.AboutTextBox.setFixedWidth(850)
        self.AboutTextBox.setHorizontalScrollBarPolicy(
                                                   QtCore.Qt.ScrollBarAlwaysOff)
        self.AboutTextBox.setOpenExternalLinks(True)
        
        # http://stackoverflow.com/questions/9554435/
        # qtextedit-background-color-change-also-the-color-of-scrollbar        
        self.AboutTextBox.setStyleSheet('QTextEdit {background-color:"white"}')
        
        #http://stackoverflow.com/questions/26441999/
        #how-do-i-remove-the-space-between-qplaintextedit-and-its-contents        
        self.AboutTextBox.document().setDocumentMargin(0)
        
        # self.AboutTextBox.setAlignment(QtCore.Qt.AlignCenter)
        # self.AboutTextBox.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)

        self.set_html_in_AboutTextBox()
                                      
        #-------------------------------------------------------- Main Grid ---- 
        
        grid = QtGui.QGridLayout()
        grid.setSpacing(10)
        
        grid.addWidget(self.AboutTextBox, 0, 1)
        
        grid.setColumnStretch(0, 500)
        grid.setColumnStretch(2, 500)
#        grid.setColumnMinimumWidth(1, 850)
        
        self.setLayout(grid)
        
    def set_html_in_AboutTextBox(self): #=======================================
        
        #---- Image Logo ----
        
        width = self.AboutTextBox.size().width()
        version = self.software_version
        date = self.last_modification
        
        filename = 'Icons/WHAT_banner_850px.png'
        
        about_text =  '''
                      <img src="%s" 
                      align="center" width="%d">
                      ''' % (filename, width)
        
        #---- Header ----
        
        about_text += '''  
                      <br>
                      <p align="center">                      
                      <font size=16><b>%s</b></font>
                      <br>
                      <font size=4>
                        <i>Well Hydrograph Analysis Toolbox</i>
                      </font>
                      <br><br>
                      <b>Copyright 2014-2015 Jean-S&eacute;bastien Gosselin</b>
                      <br>
                      jnsebgosselin@gmail.com
                      <br><br>                         
                      Institut National de la Recherche Scientifique<br>
                      Centre Eau Terre Environnement<br>
                      490 rue de la Couronne, Quebec City, QC, Canada<br>
                      <a href="http://www.ete.inrs.ca/">
                        http://www.ete.inrs.ca                      
                      </a>
                      </p>
                      <br><br>
                      ''' % version
                        
        #---- License ----                
                        
        about_text += '''
                      <p align="justify" style="margin-right:50px; 
                      margin-left:50px">
                        %s is free software: you can redistribute it and/or 
                        modify it under the terms
                        of the GNU General Public License as published by the 
                        Free Software Foundation, either version 3 of the 
                        License, or (at your option) any later version. 
                      </p>
                      <p align="justify" style="margin-right:50px; 
                      margin-left:50px">
                        This program is distributed in the hope that it will be
                        useful, but WITHOUT ANY WARRANTY; without even the
                        implied warranty of MERCHANTABILITY or FITNESS FOR A
                        PARTICULAR PURPOSE. See the GNU General Public 
                        License for more details.
                      </p>
                      <p align="justify" style="margin-right:50px; 
                      margin-left:50px">
                        You should have received a copy of the GNU General  
                        Public License along with this program.  If not, see  
                        <a href="http://www.gnu.org/licenses">
                          http://www.gnu.org/licenses
                        </a>.                                           
                      </p>
                      <p align="right" style="margin-right:50px">
                        Last modification: %s
                      </p>
                      ''' % (version, date)
        
        self.AboutTextBox.setHtml(about_text)
        
    def eventFilter(self, obj, event): #========================================
    
        # http://stackoverflow.com/questions/13788452/
        # pyqt-how-to-handle-event-without-inheritance
    
        # https://srinikom.github.io/pyside-docs/PySide/QtCore/QObject.
        # html#PySide.QtCore.PySide.QtCore.QObject.installEventFilter

        if event.type() == QtCore.QEvent.Type.Resize:
            
            self.set_html_in_AboutTextBox() # To Keep the image logo to the
                                            # same width as the QTextEdit box
            
        elif event.type() == QtCore.QEvent.Type.FontChange:            
            return True # Eat the event to disable zooming
                        
        return QtGui.QWidget.eventFilter(self, obj, event)

if __name__ == '__main__':
    
    app = QtGui.QApplication(sys.argv)

    software_version = 'WHAT Beta 4.1.6'
    last_modification = '24/06/2015' 
    
    instance1 = AboutWhat(software_version, last_modification)
    
    #---- SHOW ----
              
    instance1.show()
    
    qr = instance1.frameGeometry()
    cp = QtGui.QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    instance1.move(qr.topLeft())
        
    sys.exit(app.exec_())