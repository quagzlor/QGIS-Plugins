# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MINotes
                                 A QGIS plugin
 Plugin to make notes on pixel values of MI data
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-10-06
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Divij Gurpreet Singh
        email                : m5242105@u-aizu.ac.jp
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction,QFileDialog
from qgis.gui import QgsMapToolEmitPoint, QgsMapToolPan
from qgis.core import QgsPointXY

import csv #For writing csv stuff
import matplotlib.pyplot as plt #For spectra graphs

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .MI_Notes_dialog import MINotesDialog
import os.path



class MINotes:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'MINotes_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&MI Notes')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

        #Map Emit tool to get coordinates
        self.canvas = self.iface.mapCanvas()
        self.pointTool = QgsMapToolEmitPoint(self.canvas)
        self.pointTool.canvasClicked.connect( self.display_point )

        #Pan tool, for when stopping pixel selection
        self.panTool = QgsMapToolPan(self.canvas)

        #Arrays to save stuff
        self.xydata = [] #Saves co ordinates
        self.xynotes = [] #Saves notes
        self.edit_index = 0 #Saves the index for the co ordinates being edited
        

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('MINotes', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/MI_Notes/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'MI Notes'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True



    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&MI Notes'),
                action)
            self.iface.removeToolBarIcon(action)


    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = MINotesDialog()

            #Keep window on top
            self.dlg.setWindowFlags(Qt.WindowStaysOnTopHint)

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        #result = self.dlg.exec_()
        # See if OK was pressed
        #if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            #pass

        
        #Linking Buttons#

        #For selecting the loading and saving files
        self.dlg.SaveFileSelect.clicked.connect(self.select_output_file)
        self.dlg.LoadFileSelect.clicked.connect(self.select_input_file)

        #For the actual loading and saving
        self.dlg.SaveFileButton.clicked.connect(self.write_to_file)
        self.dlg.LoadFileButton.clicked.connect(self.read_from_file)

        #Starting and stopping pixel selection
        self.dlg.PixelStart.clicked.connect(self.pixel_start)
        self.dlg.PixelStop.clicked.connect(self.pixel_stop)

        #Loading and saving pixel data and editing
        self.dlg.XYLoad.clicked.connect(self.load_edit_xy)
        self.dlg.XYSave.clicked.connect(self.save_edit_xy)

        self.dlg.SpectraDraw.clicked.connect(self.mi_spectra_graph)
        

    def pixel_start(self): #Sets map tool to co ordinate emitter
        # this QGIS tool emits as QgsPoint after each click on the map canvas
        self.canvas.setMapTool(self.pointTool)

    def pixel_stop(self): #Sets map tool to pan
        # this QGIS tool emits as QgsPoint after each click on the map canvas
        self.canvas.setMapTool(self.panTool)

    def display_point(self,pointTool): #Used to get coordinate from map
        self.xydata.append([pointTool[0],pointTool[1]])
        self.xynotes.append('Note: ')
        self.combo_populate()
        
    def select_output_file(self): #File Dialog to select file to save
        filename, _filter = QFileDialog.getSaveFileName(
            self.dlg, "Select output file ","", '*.csv')
        self.dlg.SaveFileLine.setText(filename)

    def select_input_file(self): #File Dialog to select file to load
        filename, _filter = QFileDialog.getOpenFileName(
            self.dlg, "Select output file ","", '*.csv')
        self.dlg.LoadFileLine.setText(filename)

    def write_to_file(self): #Writes data to a csv file
        filename = self.dlg.SaveFileLine.text()
        with open(filename,'w',newline='',encoding='utf-8') as outfile:
            writer = csv.writer(outfile)

            outdata = []

            for i in range(len(self.xydata)):
                outdata.append([self.xydata[i][0],self.xydata[i][1],self.xynotes[i]])
            print (outdata)
            writer.writerows(outdata)

    def read_from_file(self): #Loads data from csv file
        filename = self.dlg.LoadFileLine.text()

        self.xydata = []
        self.xynotes = []

        with open(filename,'r',newline='',encoding='utf-8') as infile:
            reader = csv.reader(infile, delimiter=',')
            for row in reader:
                x_coordinate = float(row[0])
                y_coordinate = float(row[1])

                self.xydata.append([x_coordinate,y_coordinate])
                self.xynotes.append(row[2])

        self.combo_populate()


    def combo_populate(self): #Populates the dropdown combo box
        self.dlg.XYCombo.clear()

        for index in range(len(self.xydata)):
            self.dlg.XYCombo.addItem(str(index+1)+': '+str(self.xydata[index][0])+'|'+str(self.xydata[index][1]))

    def load_edit_xy(self): #Loads Co ordinates and Notes into text boxes
        self.edit_index = self.dlg.XYCombo.currentIndex()

        x_coordinate,y_coordinate = self.xy_format()
        self.dlg.XYCoordinateBox.setPlainText(x_coordinate+'\n'+y_coordinate)

        self.dlg.XYNoteBox.setPlainText(self.xynotes[self.edit_index])

    def xy_format(self): #Formats XY Coordinates for text box
        x_coordinate = 'X: '+str(self.xydata[self.edit_index][0])
        y_coordinate = 'Y: '+str(self.xydata[self.edit_index][1])

        return x_coordinate,y_coordinate

    def xy_unformat(self): #Formats XY Coordinates from text box to floats
        xy_data = self.dlg.XYCoordinateBox.toPlainText().split('\n')
        x_coordinate = xy_data[0]
        y_coordinate = xy_data[1]

        x_coordinate = float(x_coordinate[2:].strip())
        y_coordinate = float(y_coordinate[2:].strip())

        return x_coordinate,y_coordinate

    def save_edit_xy(self): #Saves Co ordinates and Notes from text boxes
        self.xynotes[self.edit_index] = self.dlg.XYNoteBox.toPlainText()

        x_coordinate,y_coordinate = self.xy_unformat()
        self.xydata[self.edit_index][0] = x_coordinate
        self.xydata[self.edit_index][1] = y_coordinate

    def mi_spectra_graph(self): #Draws a graph of the spectra reading using matplotlib
        bands = [1,2,3,4,5,6,7,8,9]
        x_coordinate = self.xydata[self.edit_index][0]
        y_coordinate = self.xydata[self.edit_index][1]

        band_data = self.get_mi_band_data(x_coordinate,y_coordinate)

        plt.plot(bands,band_data)
        plt.xlabel("Band")
        plt.show()

    def get_mi_band_data(self,x_coordinate,y_coordinate): #Gets the band information for the given coordinates
        layer = self.iface.activeLayer()
        data = []
        for i in range(9):
            val, res = layer.dataProvider().sample(QgsPointXY(x_coordinate,y_coordinate),i)
            data.append(val)
        return data