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
from .. classes.db_operations import *
from .. import config as c # valores constantes

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
import sys
sys.path.append(os.path.dirname(__file__))
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__),
                                            'update_project_data.ui'),
                               resource_suffix='')

class editProjectData(QtWidgets.QDialog,
                      FORM_CLASS):
    """
    brief: Clase diálogo para matriculación de datos generales del proyecto
    """
    def __init__(self,
                 iface,
                 list_edit_project,
                 path_plugin,
                 path_project,
                 path_db_project,
                 nemo,
                 title,
                 author,
                 company,
                 path_logo,
                 path_logo_2,
                 crs_project,
                 parent=None):
        """
        brief: función inicializadora de la clase
        param[in]: path del proyecto PFLIPUAV
        param[in]: path del plugin
        param[in]: referencia al QGIS interface
        param[in]: contenedor lista para almacenar parámetros tras salvar datos generales
        """
        super(editProjectData, self).__init__(parent)

        # Set up the user interface from Designer.
        self.setupUi(self)

        self.iface = iface # Save reference to the QGIS interface
        self.db_op = DbOperations(self.iface)  # new db operations
        self.list_edit_project = list_edit_project # contenedor para recopilar datos generales del proyecto
        self.path_plugin = path_plugin
        self.path_db_project = path_db_project

        # rellena lineEdits con valores actuales
        self.lineEdit_pathSqlite.setText(path_project)
        self.lineEdit_Nemo.setText(nemo)
        self.lineEdit_TitleProject.setText(title)
        self.lineEdit_AuthorProject.setText(author)
        self.lineEdit_Company.setText(company)
        self.lineEdit_pathLogo.setText(path_logo)
        self.lineEdit_pathLogo_2.setText(path_logo_2)
        self.lineEdit_CRS.setText(crs_project)

        # qsettings: fichero que almacena los últimos valores introducidos por el usuario en la aplicación en anteriores sesiones
        path_file_qsettings = self.path_plugin + '/templates/qsettings.ini'
        self.my_qsettings = QtCore.QSettings(path_file_qsettings,QtCore.QSettings.IniFormat)

        # SIGNAL/SLOT connections in order:
        self.toolButton_SaveProject.clicked.connect(self.update_project)
        self.toolButton_SearchPathLogo.clicked.connect(self.path_logo_from_file)
        self.toolButton_SearchPathLogo_2.clicked.connect(self.path_logo2_from_file)

    def path_logo_from_file(self):
        """
        Brief: carga el logo desde un fichero
        """
        self.lineEdit_pathLogo.clear()
        self.lineEdit_pathLogo.setEnabled(False)

        str_path_directory_logo = os.path.normcase( self.path_plugin + c.CONST_SEPARATOR_DIRECTORIES + "icons")

        str_path_logo, str_filter = QtWidgets.QFileDialog.getOpenFileName(caption=c.CONST_PFLIPUAV_TITLE + ": Open main logo file",
                                                                          directory=str_path_directory_logo,
                                                                          filter="Fichero png (*.png);;Todos los ficheros (*)")
        if len(str_path_logo) > 0:
            self.path_logo_file_normalizado = os.path.normcase(str_path_logo)
            self.lineEdit_pathLogo.setEnabled(True)
            self.lineEdit_pathLogo.setText(self.path_logo_file_normalizado)
        else:
            self.lineEdit_pathLogo.clear()

    def path_logo2_from_file(self):
        """
        Brief: carga el logo desde un fichero
        """
        self.lineEdit_pathLogo_2.clear()
        self.lineEdit_pathLogo_2.setEnabled(False)

        str_path_directory_logo = os.path.normcase(self.path_plugin + c.CONST_SEPARATOR_DIRECTORIES + "icons")

        str_path_logo, str_filter = QtWidgets.QFileDialog.getOpenFileName(caption=c.CONST_PFLIPUAV_TITLE + ": Open secondary logo file",
                                                                          directory=str_path_directory_logo,
                                                                          filter="Fichero png (*.png);;Todos los ficheros (*)")
        if len(str_path_logo) > 0:
            self.path_logo_file_normalizado = os.path.normcase(str_path_logo)
            self.lineEdit_pathLogo_2.setEnabled(True)
            self.lineEdit_pathLogo_2.setText(self.path_logo_file_normalizado)
        else:
            self.lineEdit_pathLogo_2.clear()

    def update_project(self):
        """
        brief:
        """

        #title
        title = self.lineEdit_TitleProject.text()
        if len(title) == 0:
            title = "unknown"

        #author
        author = self.lineEdit_AuthorProject.text()
        if len(author) == 0:
            author = "unknown"

        #company
        company = self.lineEdit_Company.text()
        if len(company) == 0:
            company = "unknown"

        #path logo
        path_logo = self.lineEdit_pathLogo.text()
        if len(path_logo) == 0:
            path_logo = ""

        #path logo 2
        path_logo_2 = self.lineEdit_pathLogo_2.text()
        if len(path_logo_2) == 0:
            path_logo_2 = ""

        #carga en el contenedor lista los valores almacenados
        self.list_edit_project.append(title)
        self.list_edit_project.append(author)
        self.list_edit_project.append(company)
        self.list_edit_project.append(path_logo)
        self.list_edit_project.append(path_logo_2)

        # grabación de los datos generales del proyecto en la bd
        str_query = "UPDATE project SET "
        str_query += "title ='" + title + "',"
        str_query += "author ='" + author + "',"
        str_query += "company ='" + company + "',"
        str_query += "path_logo ='" + path_logo + "',"
        str_query += "path_logo_2 ='" + path_logo_2 + "' "
        str_query += "WHERE id_project = 1;"

        self.db_op.execute_query_old(self.path_db_project,
                                     str_query)

        # mensaje final
        str_final_msg = "Project " + c.CONST_PFLIPUAV_TITLE + " updated successfully"
        self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                            str_final_msg,
                                            Qgis.Info,
                                            5)
        self.close() # cierra el dialogo