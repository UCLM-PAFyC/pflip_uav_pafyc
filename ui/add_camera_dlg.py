# -*- coding: utf-8 -*-

# Import PyQt5 classes
from PyQt5 import uic
from PyQt5 import QtWidgets

# import PyQGIS classes
from qgis.core import Qgis

#others imports
from ..classes.qgis3_api_operations import Qgis3ApiOperations
from ..classes.db_operations import *

from .. import config as c # valores constantes

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
import sys
import csv

sys.path.append(os.path.dirname(__file__))
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__),
                                            'add_camera_dlg.ui'),
                               resource_suffix='')

class addCameraDlg(QtWidgets.QDialog,
                   FORM_CLASS):
    """
    brief:
    """
    def __init__(self,
                 iface,
                 lst_add_camera,
                 path_db_project,
                 path_csv_file_sensors,
                 parent=None):
        """
        Brief: Iniciliaza la clase
        :param iface: iface - interfaz de usuario QGIS
        :type iface: QgsInterface
        :param lst_add_camera: contenedor lista para almacenar parámetros tras salvar valores introducidos en el panel
        :type lst_add_camera: list
        :param path_db_project: path de la base de datos del proyecto
        :type path_db_project: str
        """
        super(addCameraDlg, self).__init__(parent)

        self.lst_add_camera_dlg = lst_add_camera
        self.path_csv_file_sensors = path_csv_file_sensors
        self.iface = iface # Save reference to the QGIS interface

        self.q3_api_op = Qgis3ApiOperations(self.iface)
        self.db_op = DbOperations(self.iface)  # new db operations

        # path de las bases de datos de proyecto
        self.path_db_project = path_db_project

        # Set up the user interface from Designer.
        self.setupUi(self)

        # SIGNAL/SLOT connections in order:
        self.toolButton_addCamera.clicked.connect(self.add_camera)

    def add_camera(self):
        """
        Brief: recopila variables introducidas en el dialogo y graba en la base de datos
        """

        # 1. Recopilar valores introducidos en el panel
        str_code = self.lineEdit_code.text()
        str_trademark = self.lineEdit_Trademark.text()
        str_columns = str(self.spinBox_columns.value())
        str_rows = str(self.spinBox_rows.value())
        str_focal = str(self.doubleSpinBox_focal.value())
        str_geometric_resolution = str(self.doubleSpinBox_resolution.value())
        str_xppa = str(self.doubleSpinBox_xppa.value())
        str_yppa = str(self.doubleSpinBox_yppa.value())

        # calcula el máximo valor introducido en el campo [order_combo]
        str_fieldname = "order_combo"
        str_tablename = "camera"
        int_max_order = self.db_op.get_max_value_field_from_table_db(self.path_db_project,
                                                                     str_fieldname,
                                                                     str_tablename)
        int_current_order = int_max_order + 1
        str_current_order = str(int_current_order)

        # control valores introducidos
        if len(str_code) == 0:
            msg_code = "Select camera code"
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                msg_code,
                                                Qgis.Critical,
                                                10)
            return

        self.lst_add_camera_dlg.append(str_code)

        if len(str_trademark) == 0:
            msg_code = "Select trademark"
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                msg_code,
                                                Qgis.Critical,
                                                10)
            return

        # 3. Consulta insert grabación en db_project
        str_query = "INSERT INTO camera (cod_camera,trademark,rows,columns,focal,geometric_res,coor_x_ppa,coor_y_ppa,order_combo) "
        str_query += "VALUES ("
        str_query += "'" + str_code + "',"
        str_query += "'" + str_trademark + "',"
        str_query += str_rows + ","
        str_query += str_columns + ","
        str_query += str_focal + ","
        str_query += str_geometric_resolution + ","
        str_query += str_xppa + ","
        str_query += str_yppa + ","
        str_query += str_current_order + ");"

        self.db_op.execute_query_old(self.path_db_project,
                                     str_query)

        # consulta sensors grabados en el csv y almacena en una lista las keys
        if self.path_csv_file_sensors is not None:
            list_cod_camera_csv = []
            file_csv_sensors = open(self.path_csv_file_sensors, 'r')
            with file_csv_sensors:
                reader = csv.reader(file_csv_sensors, delimiter=';')
                next(reader, None)  # skip the headers
                for current_csv_sensor in reader:
                    current_cod_camera_csv = current_csv_sensor[0]
                    list_cod_camera_csv.append(current_cod_camera_csv)

            if str_code not in list_cod_camera_csv:
                file_csv_sensors = open(self.path_csv_file_sensors, 'a')
                with file_csv_sensors:
                    writer = csv.writer(file_csv_sensors, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    writer.writerow([str_code, str_trademark, str_rows, str_columns, str_focal, str_geometric_resolution, str_xppa, str_yppa])

        # carga tabla camera (no espacial) en QGIS
        self.q3_api_op.load_to_qgis(False,
                                    self.path_db_project,
                                    "camera",
                                    "no_spatial",
                                    "",
                                    None)
        self.close()  # cierra el diálogo