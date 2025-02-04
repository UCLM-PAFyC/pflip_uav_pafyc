# -*- coding: utf-8 -*-

# Import PyQt5 classes
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5 import QtCore

# import Python classes
import os

#others imports
from ..classes.db_operations import *
from ..classes.qgis3_api_operations import Qgis3ApiOperations


# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
import sys
sys.path.append(os.path.dirname(__file__))
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__),
                                            'update_camera_dlg.ui'),
                               resource_suffix='')

class updateCameraDlg(QtWidgets.QDialog,
                      FORM_CLASS):
    """
    brief:
    """
    def __init__(self,
                 iface,
                 path_db_project,
                 str_cod_sensor,
                 parent=None):
        """
        Brief: Iniciliaza la clase
        :param iface: iface - interfaz de usuario QGIS
        :type iface: QgsInterface
        :param path_db_project: path de la base de datos del proyecto PLIPUAV
        :type path_db_project: str
        :param str_cod_sensor: código de la cámara a editar
        :type str_cod_sensor: str
        """
        super(updateCameraDlg, self).__init__(parent)

        self.iface = iface # Save reference to the QGIS interface
        self.db_op = DbOperations(self.iface)  # new db operations
        self.q3_api_op = Qgis3ApiOperations(self.iface)

        # path de las bases de datos template y de proyecto
        self.path_db_project = path_db_project

        self.str_cod_sensor = str_cod_sensor # codigo de sensor a actualizar

        # Set up the user interface from Designer
        self.setupUi(self)

        self.initialize() # inicializa los valores desde la BD

        # SIGNAL/SLOT connections in order:
        self.toolButton_updateCamera.clicked.connect(self.update_camera)

    def initialize(self):
        """
        Brief: inicializa los parámetros de la ui a partir de los datos grabados en la BD
        """
        # conexión con la base de datos
        con_db_project = self.db_op.connection_sqlite(self.path_db_project)
        cursor_db_project = con_db_project.cursor()

        # recupera los datos grabados en la BD
        str_sql = "SELECT * FROM camera WHERE cod_camera = '" + self.str_cod_sensor + "';"
        cursor_db_project.execute(str_sql)

        for row in cursor_db_project.fetchall():
            str_cam_trademark = row[1]
            str_cam_rows = row[2]
            str_cam_columns = row[3]
            str_cam_focal = row[4]
            str_cam_geom_resolution = row[5]
            str_cam_xppa = row[6]
            str_cam_yppa = row[7]

        con_db_project.close() #cierra la base de datos

        # pone los valores de la ui con los valores grabados en la BD
        self.lineEdit_code.setText(self.str_cod_sensor)
        self.lineEdit_Trademark.setText(str_cam_trademark)
        self.spinBox_columns.setValue(str_cam_columns)
        self.spinBox_rows.setValue(str_cam_rows)
        self.doubleSpinBox_focal.setValue(str_cam_focal)
        self.doubleSpinBox_resolution.setValue(str_cam_geom_resolution)
        self.doubleSpinBox_xppa.setValue(str_cam_xppa)
        self.doubleSpinBox_yppa.setValue(str_cam_yppa)

    def update_camera(self):
        """
        Brief:
        """
        # 1. Recopila valores introducidos en el panel
        #str_code = self.lineEdit_code.text()
        str_trademark = self.lineEdit_Trademark.text()
        str_columns = str(self.spinBox_columns.value())
        str_rows = str(self.spinBox_rows.value())
        str_focal = str(self.doubleSpinBox_focal.value())
        str_geometric_resolution = str(self.doubleSpinBox_resolution.value())
        str_xppa = str(self.doubleSpinBox_xppa.value())
        str_yppa = str(self.doubleSpinBox_yppa.value())

        # 2. Consulta insert grabación en db_project
        str_query = "UPDATE camera SET "
        str_query += "trademark = '" + str_trademark + "',"
        str_query += "rows = " + str_rows + ","
        str_query += "columns = " + str_columns + ","
        str_query += "focal = " + str_focal + ","
        str_query += "geometric_res = " + str_geometric_resolution + ","
        str_query += "coor_x_ppa = " + str_xppa + ","
        str_query += "coor_y_ppa = " + str_yppa + " "
        str_query += "WHERE cod_camera = '" + self.str_cod_sensor + "';"
        self.db_op.execute_query_old(self.path_db_project,
                                     str_query)

        # 3. carga tabla camera (no espacial) en QGIS
        self.q3_api_op.load_to_qgis(False,
                                    self.path_db_project,
                                    "camera",
                                    "no_spatial",
                                    "",
                                    None)

        self.close()