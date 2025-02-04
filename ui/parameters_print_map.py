# -*- coding: utf-8 -*-

# Import PyQt5 classes
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5 import QtCore

# import PyQGIS classes
from qgis.core import Qgis

# import Python classes
import os

# import self classes
from ..classes.print_map import *
from .. import config as c # valores constantes

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
import sys
sys.path.append(os.path.dirname(__file__))
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__),
                                            'parameters_print_map.ui'),
                               resource_suffix='')

class parametersPrintMap(QtWidgets.QDialog,
                         FORM_CLASS):
    """
    brief: Clase diálogo para matriculación de datos generales del proyecto
    """
    def __init__(self,
                 iface,
                 path_file_map_pdf,
                 cod_flight_block_dlg,
                 path_plugin,
                 path_db_project,
                 nemo,
                 title,
                 author,
                 company,
                 path_logo,
                 path_logo_2,
                 crs_project,
                 str_firmware,
                 parent=None):
        """
        brief: función inicializadora de la clase
        """
        super(parametersPrintMap, self).__init__(parent)

        # Set up the user interface from Designer.
        self.setupUi(self)

        self.iface = iface # Save reference to the QGIS interface
        self.path_file_map_pdf = path_file_map_pdf
        self.cod_flight_block_dlg = cod_flight_block_dlg
        self.path_plugin = path_plugin
        self.path_db_project = path_db_project
        self.nemo = nemo
        self.title = title
        self.author = author
        self.company = company
        self.path_logo = path_logo
        self. path_logo_2 = path_logo_2
        self.crs_project = crs_project
        self.str_firmware = str_firmware

        # rellena lineEdits con valores actuales
        self.lineEdit_Nemo.setText(nemo)
        self.lineEdit_TitleProject.setText(title)
        self.lineEdit_AuthorProject.setText(author)
        self.lineEdit_Company.setText(company)
        self.lineEdit_pathLogo.setText(path_logo)
        self.lineEdit_pathLogo2.setText(path_logo_2)
        self.lineEdit_CRS.setText(crs_project)
        self.lineEdit_flightBlockCode.setText(cod_flight_block_dlg)

        # qsettings: fichero que almacena los últimos valores introducidos por el usuario en la aplicación en anteriores sesiones
        path_file_qsettings = self.path_plugin + '/templates/qsettings.ini'
        self.my_qsettings = QtCore.QSettings(path_file_qsettings,QtCore.QSettings.IniFormat)

        # SIGNAL/SLOT connections in order:
        self.toolButton_process.clicked.connect(self.print_map)

    def print_map(self):
        """
        Brief: salida gráfica
        """
        map_scale_factor = self.mQgsDoubleSpinBox_scaleFactor.value()
        map_number_grid_divisions = self.mQgsSpinBox_numberGridDivisions.value()


        instance_print_map_class = PrintMap(self.iface,
                                            self.path_db_project,
                                            self.path_file_map_pdf,
                                            self.nemo,
                                            self.cod_flight_block_dlg,
                                            self.title,
                                            self.author,
                                            self.company,
                                            self.crs_project,
                                            map_scale_factor,
                                            map_number_grid_divisions,
                                            self.path_logo,
                                            self.path_logo_2,
                                            self.str_firmware)

        process_result = instance_print_map_class.process()
        if process_result:
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                "Impresión de mapa finalizada con éxito",
                                                Qgis.Info,
                                                20)
        else:
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                "Existe un error en la impresión de mapa",
                                                Qgis.Critical,
                                                20)
        self.close()