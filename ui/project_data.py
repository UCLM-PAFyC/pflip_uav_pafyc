# -*- coding: utf-8 -*-

from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5 import QtCore
from qgis.core import (Qgis, QgsMessageLog, QgsCoordinateReferenceSystem)
# import Python classes
import os
from shutil import *
from ..classes.qgis3_api_operations import Qgis3ApiOperations
from ..classes.db_operations import *
from ..classes.model_db_manager_definitions import ModelDbManagerDefinitions as modeldb
from .. import config as c
import sys
sys.path.append(os.path.dirname(__file__))
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__),
                                            'project_data.ui'),
                               resource_suffix='')
import shutil

class Projectdata(QtWidgets.QDialog,
                  FORM_CLASS):
    """
    Brief: Clase diálogo para matriculación de datos generales del proyecto
    """
    def __init__(self,
                 path_pflipuav_projects,
                 path_plugin,
                 iface,
                 lst_gral_data_prj,
                 parent=None):
        """
        brief: función inicializadora de la clase
        :param path_pflipuav_projects: path de los proyectos PFLIPUAV
        :type path_pflipuav_projects: str
        :param path_plugin: path del plugin
        :type path_plugin: str
        :param iface: referencia al QGIS interface
        :type iface: QgsInterface
        :param lst_gral_data_prj: contenedor lista para almacenar parámetros tras salvar datos generales
        :type lst_gral_data_prj: list
        :return:
        """
        super(Projectdata, self).__init__(parent)

        self.lst_gral_data_prj = lst_gral_data_prj # contenedor para recopilar datos generales del proyecto
        self.iface = iface # Save reference to the QGIS interface
        self.path_plugin = path_plugin

        self.db_op = DbOperations(self.iface)  # new db operations

        self.q3_api_op = Qgis3ApiOperations(self.iface)

        # Set up the user interface from Designer.
        self.setupUi(self)

        # rellena el path project
        self.path_pflipuav_projects = path_pflipuav_projects
        self.lineEdit_pathSqlite.setText(self.path_pflipuav_projects)

        # qsettings: fichero que almacena los últimos valores introducidos por el usuario en la aplicación en anteriores sesiones
        path_file_qsettings =  self.path_plugin + '/templates/qsettings.ini'
        self.my_qsettings = QtCore.QSettings(path_file_qsettings,QtCore.QSettings.IniFormat)

        self.initialize()

    def cpp_project_db_creation(self):

        # nemo
        nemo = self.lineEdit_Nemo.text()
        if len(nemo) == 0:
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                "Mnemonic code project is required",
                                                Qgis.Critical,
                                                10)
            return

        # crea la estructura de directorios
        str_new_path_project = self.path_pflipuav_projects + c.CONST_SEPARATOR_DIRECTORIES + nemo
        self.dir_new_path_project_normalize = os.path.normcase(str_new_path_project)
        if not os.path.exists(self.dir_new_path_project_normalize):
            os.makedirs(self.dir_new_path_project_normalize)

        str_common_directory = self.path_pflipuav_projects + c.CONST_SEPARATOR_DIRECTORIES + c.CONST_COMMON_DATA_DIRNAME
        common_directory_normalize = os.path.normcase(str_common_directory)
        if not os.path.exists(common_directory_normalize):
            os.makedirs(common_directory_normalize)

        str_proj_data_directory = self.dir_new_path_project_normalize + c.CONST_SEPARATOR_DIRECTORIES + c.CONST_PROJ_DATA_DIRNAME
        dir_proj_data_directory_normalize = os.path.normcase(str_proj_data_directory)
        if not os.path.exists(dir_proj_data_directory_normalize):
            os.makedirs(dir_proj_data_directory_normalize)

        # copia del template sqlite a la ruta path_project/nemo.sqlite
        str_sqlite_db_filename = nemo + ".sqlite"
        self.path_db_project = os.path.join(self.dir_new_path_project_normalize,
                                            str_sqlite_db_filename)

        # comprueba si existe el la base de datos sqlite en directorio destino
        if os.path.exists(self.path_db_project):
            str_msg = "Error copying sqlite database. Filename [%s] exists in target directory" % self.path_db_project
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                str_msg,
                                                Qgis.Critical,
                                                10)
            return

        str_msg_log = "Path DB project: %s" % self.path_db_project
        QgsMessageLog.logMessage(str_msg_log,
                                 c.CONST_PFLIPUAV_TITLE,
                                 Qgis.Info)

        template_db = self.path_plugin + '/templates/PFLIP_template_db.sqlite'
        if not os.path.exists(template_db):
            str_msg = ('Not exists template database:\n{}'.format(template_db))
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                str_msg,
                                                Qgis.Critical,
                                                10)
            return
        if os.path.exists(self.path_db_project):
            os.remove(self.path_db_project)
            if os.path.exists(self.path_db_project):
                str_msg = ('Error removing existing database:\n{}'.format(self.path_db_project))
                self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                    str_msg,
                                                    Qgis.Critical,
                                                    10)
                return
        dest = shutil.copyfile(template_db, self.path_db_project)
        if not os.path.exists(self.path_db_project):
            str_msg = ('Error copying database:\n{}'.format(self.path_db_project))
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                str_msg,
                                                Qgis.Critical,
                                                10)
            return

        self.con_db_template = self.db_op.connection_sqlite(self.path_db_project)
        if self.con_db_template is None:
            self.close()
            return
        sqls = self.get_sqls_create_database()
        self.db_op.execute_sqls(self.con_db_template, sqls)
        # 3. Rellena el combobox con crs de qgis a partir de la tabla de la base de datos srs.db filtrada con los CRSs que se van a utilizar y rellena el diccionario
        self.dictionary_crs = self.fill_combo_crs(self.path_db_project,
                                                  self.str_srsid_map_canvas)
        if self.dictionary_crs is None:
            self.close()
            self.con_db_template.close()
            return

        self.lineEdit_Nemo.setEnabled(False)
        self.toolButton_createDb.setEnabled(False)
        self.mGroupBox_projectHeaderData.setVisible(True)

    def create_spatial_tables(self,
                              path_db_project,
                              str_internal_id_crs_selected):

        # crea capas espaciales para pintar
        str_code_crs_epsg = self.q3_api_op.get_strcrscode_InternalCrsId2PostgisCrsId(str_internal_id_crs_selected)

        # creación de la capas SpatiaLite para dibujar en el CRS del proyecto PLIPUAV
        self.db_op.create_spatial_table(path_db_project,
                                        modeldb.TABLE_SPATIAL_LAYER_ZONE_TABLE_NAME,
                                        str_code_crs_epsg,
                                        modeldb.GEOM_TYPE_POLYGON)
        self.db_op.create_spatial_table(path_db_project,
                                        modeldb.TABLE_SPATIAL_LAYER_VECTOR_TABLE_NAME,
                                        str_code_crs_epsg,
                                        modeldb.GEOM_TYPE_LINESTRING)
        self.db_op.create_spatial_table(path_db_project,
                                        modeldb.TABLE_SPATIAL_LAYER_LANDING_POINT_TABLE_NAME,
                                        str_code_crs_epsg,
                                        modeldb.GEOM_TYPE_POINT)
        self.db_op.create_spatial_table(path_db_project,
                                        modeldb.TABLE_SPATIAL_LAYER_TAKEOFF_POINT_TABLE_NAME,
                                        str_code_crs_epsg,
                                        modeldb.GEOM_TYPE_POINT)
        self.db_op.create_spatial_table(path_db_project,
                                        modeldb.TABLE_SPATIAL_LAYER_AXIS_TABLE_NAME,
                                        str_code_crs_epsg,
                                        modeldb.GEOM_TYPE_LINESTRING)

        # añade campos de geometría a tablas de salida
        table_name = c.CONST_PFLIPUAV_LAYER_IMAGES
        geom_field_name = "geom_2d_fp_m"
        geom_type = "POLYGON"
        str_dimensions = str(2)
        self.db_op.add_geometry_output_tables(self.path_db_project,
                                              table_name,
                                              geom_field_name,
                                              str_code_crs_epsg,
                                              geom_type,
                                              str_dimensions)
        table_name = c.CONST_PFLIPUAV_LAYER_STEREO_PAIRS
        geom_field_name = "geom_2d_fp_m"
        geom_type = "POLYGON"
        str_dimensions = str(2)
        self.db_op.add_geometry_output_tables(self.path_db_project,
                                              table_name,
                                              geom_field_name,
                                              str_code_crs_epsg,
                                              geom_type,
                                              str_dimensions)
        table_name = c.CONST_PFLIPUAV_LAYER_STRIPS
        geom_field_name = "geom_3d_axis_m"
        geom_type = "LINESTRINGZ"
        str_dimensions = str(3)
        self.db_op.add_geometry_output_tables(self.path_db_project,
                                              table_name,
                                              geom_field_name,
                                              str_code_crs_epsg,
                                              geom_type,
                                              str_dimensions)

    def fill_combo_crs(self,
                       path_db_project,
                       str_srsid_map_canvas):
        """
        brief: habilita el combobox con los crs de proyecto y rellena el diccionario con pares id interno QGIS (srsid)
                - descripciones a partir de la base de datos plantilla porque hasta que no se salva no se sabe
                donde está la base de datos del proyecto.
        :param path_db_project: path de la base de datos plantilla
        :type path_db_project: str
        :param str_srsid_map_canvas: cadena de texto con identificador interno de QGIS del CRS del mapcanvas
        :type str_srsid_map_canvas: str
        :return: pares id interno QGIS (srsid) - descripciones
        :rtype: dict
        """
        self.comboBox_CRSproject.clear()
        self.comboBox_CRSproject.setEnabled(True)  # habilita el combobox
        self.comboBox_CRSproject.addItem("--- Select Coordinate Reference System name ---")  # añade la primera línea

        # añade el current srs mapcanvas al combo seleccionable
        self.str_srsid_map_canvas = str_srsid_map_canvas
        int_srsid_map_canvas = int(str_srsid_map_canvas)

        # busca si el CRS del mapcanvas es uno de los CRS PLIPUAV
        str_sql = "SELECT %s, %s FROM %s WHERE %s = 1 ORDER BY %s ASC" % (modeldb.TBL_SRS_FIELD_ID,
                                                                          modeldb.TBL_SRS_FIELD_DESCRIPTION,
                                                                          modeldb.TABLE_SRS_TABLE_NAME,
                                                                          modeldb.TBL_SRS_FIELD_USE_PFLIPUAV,
                                                                          modeldb.TBL_SRS_FIELD_ID)
        list_data = self.db_op.execute_query(self.con_db_template, str_sql, self.db_op.SQL_TYPE_SELECT)
        if list_data is None: return None

        self.control_is_mapcanvas_crs_pflipuav = False # inicializa a Falso
        for row in list_data:
            current_srs_id = row[0] #identificador interno de qgis
            if current_srs_id == int_srsid_map_canvas:
                self.control_is_mapcanvas_crs_pflipuav = True # el CRS mapcanvas es de los disponibles en PLIPUAV
                #añade el item al combo
                current_qgs_crs = QgsCoordinateReferenceSystem(int_srsid_map_canvas,
                                                               QgsCoordinateReferenceSystem.InternalCrsId)
                str_item_current_crs = "Current CRS mapcanvas: %s - CRS %s" % (current_qgs_crs.description(),
                                                                               self.str_authid_map_canvas)
                pixmap_current_crs = QPixmap(":/plugins/pflip_uav_pafyc/icons/CRS.png", "16x16")
                icon_current_crs = QIcon(pixmap_current_crs)
                self.comboBox_CRSproject.addItem(str_item_current_crs)
                self.comboBox_CRSproject.setItemIcon(1,icon_current_crs)
                break

        # mensaje para indicar que el CRS del mapcanvas no es uno de los nuestros
        if not self.control_is_mapcanvas_crs_pflipuav:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setText("Current CRS is not on the list of CRS available for PLIPUAV")
            msg.setWindowTitle(c.CONST_PFLIPUAV_TITLE)
            msg.exec_()

        # ejecuta consulta para cargar los CRSs PLIPUAV
        list_data = self.db_op.execute_query(self.con_db_template, str_sql, self.db_op.SQL_TYPE_SELECT)
        if list_data is None: return None

        # incializa matriz asociativa con el par identificador interno de qgis (key) - descripcion (value)
        dictionary = {}
        for row in list_data:
            current_srs_id = row[0] #identificador interno de qgis
            current_description_crs = row[1] #descripción
            dictionary[current_description_crs] = current_srs_id
            self.comboBox_CRSproject.addItem(row[1]) #añade descripción al combobox
        self.con_db_template.close()
        return dictionary

    def get_sqls_create_database(self):
        sqls = []
        sql = "CREATE TABLE IF NOT EXISTS \"flight_block_ercMav\" ("
        sql += "	\"id_erc\"	NUMERIC(5) NOT NULL,"
        sql += "	\"def_erc\"	VARCHAR(100),"
        sql += "	PRIMARY KEY(\"id_erc\")"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"flight_block_egiMav\" ("
        sql += "	\"id_egi\"	NUMERIC(5) NOT NULL,"
        sql += "	\"def_egi\"	VARCHAR(100),"
        sql += "	PRIMARY KEY(\"id_egi\")"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"flight_block_ealMav\" ("
        sql += "	\"id_eal\"	NUMERIC(5) NOT NULL,"
        sql += "	\"def_eal\"	VARCHAR(100),"
        sql += "	PRIMARY KEY(\"id_eal\")"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"fields_descriptions\" ("
        sql += "	\"id\"	INTEGER NOT NULL,"
        sql += "	\"table\"	VARCHAR(255) NOT NULL,"
        sql += "	\"fieldname\"	VARCHAR(255),"
        sql += "	\"version_firmaware\"	VARCHAR(50),"
        sql += "	\"pk\"	BOOL NOT NULL DEFAULT FALSE,"
        sql += "	\"required\"	BOOL NOT NULL DEFAULT FALSE,"
        sql += "	\"var_python\"	VARCHAR(255),"
        sql += "	\"widget\"	VARCHAR(255),"
        sql += "	\"label\"	VARCHAR(255),"
        sql += "	\"etiqueta\"	VARCHAR(255),"
        sql += "	\"what_this\"	TEXT,"
        sql += "	\"que_es\"	TEXT,"
        sql += "	\"page_toolbox\"	VARCHAR(255),"
        sql += "	\"panel_group\"	VARCHAR(255),"
        sql += "	\"type_sqlite\"	VARCHAR(255),"
        sql += "	\"type_python\"	VARCHAR(255),"
        sql += "	\"unit\"	VARCHAR(255),"
        sql += "	\"qsettings\"	BOOL NOT NULL DEFAULT FALSE,"
        sql += "	\"default_value\"	REAL,"
        sql += "	\"max_value\"	REAL,"
        sql += "	\"min_value\"	REAL,"
        sql += "	\"decimals\"	NUMERIC(5),"
        sql += "	\"single_step\"	REAL,"
        sql += "	\"precision\"	NUMERIC(5),"
        sql += "	\"planificacion\"	BOOL NOT NULL DEFAULT FALSE,"
        sql += "	\"notes\"	TEXT,"
        sql += "	PRIMARY KEY(\"id\")"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"firmware\" ("
        sql += "	\"id_firmware\"	NUMERIC(5),"
        sql += "	\"des_firmware\"	VARCHAR(255),"
        sql += "	\"is_obsolete\"	BOOL NOT NULL DEFAULT FALSE"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"lnk_battery_firmware\" ("
        sql += "	\"id_lnk_battery_firmware\"	INTEGER NOT NULL,"
        sql += "	\"id_battery\"	INTEGER,"
        sql += "	\"id_firmware\"	NUMERIC(5),"
        sql += "	\"is_active\"	BOOL NOT NULL DEFAULT FALSE,"
        sql += "	PRIMARY KEY(\"id_lnk_battery_firmware\")"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"camera\" ("
        sql += "	\"cod_camera\"	VARCHAR(100) NOT NULL,"
        sql += "	\"trademark\"	VARCHAR(100) NOT NULL,"
        sql += "	\"rows\"	NUMERIC(5) NOT NULL,"
        sql += "	\"columns\"	NUMERIC(5) NOT NULL,"
        sql += "	\"focal\"	REAL,"
        sql += "	\"geometric_res\"	REAL NOT NULL,"
        sql += "	\"coor_x_ppa\"	REAL NOT NULL,"
        sql += "	\"coor_y_ppa\"	REAL NOT NULL,"
        sql += "	\"order_combo\"	NUMERIC(5),"
        sql += "	PRIMARY KEY(\"cod_camera\"),"
        sql += "	FOREIGN KEY(\"cod_camera\") REFERENCES \"camera\"(\"cod_camera\") ON UPDATE CASCADE ON DELETE CASCADE"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"flight_block_erc\" ("
        sql += "	\"id_erc\"	NUMERIC(5) NOT NULL,"
        sql += "	\"def_erc\"	VARCHAR(100),"
        sql += "	PRIMARY KEY(\"id_erc\")"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"flight_block_eal\" ("
        sql += "	\"id_eal\"	NUMERIC(5) NOT NULL,"
        sql += "	\"def_eal\"	VARCHAR(100),"
        sql += "	PRIMARY KEY(\"id_eal\")"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"battery\" ("
        sql += "	\"id_battery\"	INTEGER NOT NULL,"
        sql += "	\"des_battery\"	VARCHAR(100),"
        sql += "	\"charge\"	INTEGER,"
        sql += "	\"duration_battery\"	INTEGER,"
        sql += "	\"per_reduction\"	REAL,"
        sql += "	\"per_confidence\"	REAL,"
        sql += "	\"is_active\"	BOOL NOT NULL DEFAULT FALSE,"
        sql += "	PRIMARY KEY(\"id_battery\"),"
        sql += "	FOREIGN KEY(\"id_battery\") REFERENCES \"battery\"(\"id_battery\") ON UPDATE CASCADE ON DELETE CASCADE"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"project\" ("
        sql += "	\"id_project\"	NUMERIC(5) NOT NULL,"
        sql += "	\"path_project\"	VARCHAR(255),"
        sql += "	\"nemo\"	VARCHAR(255),"
        sql += "	\"title\"	VARCHAR(255),"
        sql += "	\"author\"	VARCHAR(255),"
        sql += "	\"path_sqlite_db\"	VARCHAR(255),"
        sql += "	\"crs_code\"	INTEGER,"
        sql += "	\"company\"	VARCHAR(255),"
        sql += "	\"path_logo\"	VARCHAR(255),"
        sql += "	\"path_logo_2\"	varchar(255),"
        sql += "	PRIMARY KEY(\"id_project\")"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"flight_block_c_axis\" ("
        sql += "	\"id\"	INTEGER NOT NULL,"
        sql += "	\"cod_flight_block\"	VARCHAR(50) NOT NULL,"
        sql += "	\"id_axis\"	NUMERIC(5) NOT NULL,"
        sql += "	PRIMARY KEY(\"id\")"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"flight_block\" ("
        sql += "	\"cod_flight_block\"	VARCHAR(50) NOT NULL,"
        sql += "	\"cod_camera\"	VARCHAR(100) NOT NULL DEFAULT '-1',"
        sql += "	\"dtm_path\"	TEXT,"
        sql += "	\"id_tof\"	NUMERIC(5) NOT NULL DEFAULT -1,"
        sql += "	\"id_lnd\"	NUMERIC(5) NOT NULL DEFAULT -1,"
        sql += "	\"id_firmware\"	NUMERIC(5) NOT NULL DEFAULT -1,"
        sql += "	\"id_fb_type\"	NUMERIC(5) NOT NULL DEFAULT -1,"
        sql += "	\"gsd\"	REAL NOT NULL,"
        sql += "	\"tol_gsd\"	REAL NOT NULL,"
        sql += "	\"foward_overlap\"	REAL NOT NULL,"
        sql += "	\"side_overlap\"	REAL NOT NULL,"
        sql += "	\"ac_gps\"	REAL NOT NULL,"
        sql += "	\"ac_omg\"	REAL NOT NULL,"
        sql += "	\"ac_phi\"	REAL NOT NULL,"
        sql += "	\"ac_kap\"	REAL NOT NULL,"
        sql += "	\"id_trajectory_type\"	NUMERIC(5) NOT NULL DEFAULT -1,"
        sql += "	\"cruise_speed\"	REAL NOT NULL DEFAULT 4,"
        sql += "	\"ascent_speed\"	REAL NOT NULL,"
        sql += "	\"descent_speed\"	REAL NOT NULL,"
        sql += "	\"lea\"	REAL NOT NULL,"
        sql += "	\"initial_height\"	REAL NOT NULL,"
        sql += "	\"id_nbk\"	NUMERIC(5),"
        sql += "	\"end_height\"	REAL NOT NULL,"
        sql += "	\"wpb\"	REAL NOT NULL,"
        sql += "	\"images_item\"	NUMERIC(5) NOT NULL,"
        sql += "	\"shot_interval\"	REAL NOT NULL,"
        sql += "	\"omega_angle\"	REAL NOT NULL,"
        sql += "	\"phi_angle\"	REAL NOT NULL,"
        sql += "	\"id_erc\"	NUMERIC(5),"
        sql += "	\"id_eal\"	NUMERIC(5),"
        sql += "	\"id_egi\"	NUMERIC(5),"
        sql += "	\"id_shp\"	NUMERIC(5),"
        sql += "	\"ssh\"	REAL NOT NULL,"
        sql += "	\"gpa\"	REAL NOT NULL,"
        sql += "	\"id_wae\"	NUMERIC(5),"
        sql += "	\"wal\"	REAL NOT NULL,"
        sql += "	\"was\"	REAL NOT NULL,"
        sql += "	\"id_process_st\"	NUMERIC(5) NOT NULL DEFAULT 0,"
        sql += "	\"npsf\"	NUMERIC(5) NOT NULL DEFAULT 3,"
        sql += "	\"id_mounting_type\"	NUMERIC(5) NOT NULL DEFAULT -1,"
        sql += "	\"id_type_gimbel_mount\"	NUMERIC(5) NOT NULL DEFAULT -1,"
        sql += "	\"offset_omega\"	REAL NOT NULL,"
        sql += "	\"offset_phi\"	REAL NOT NULL,"
        sql += "	\"offset_kappa\"	REAL NOT NULL,"
        sql += "	\"flight_duration\"	REAL,"
        sql += "	\"gcp_calibration_path\"	TEXT,"
        sql += "	\"gcp_is_fixed\"	INTEGER,"
        sql += "	\"gcp_separation_dtm\"	REAL,"
        sql += "	\"gcp_precision_pix\"	REAL,"
        sql += "	\"gcp_2dprecision\"	REAL,"
        sql += "	\"gcp_hprecision\"	REAL,"
        sql += "	\"gcp_image_precision\"	REAL,"
        sql += "	\"gcp_prefix\"	TEXT,"
        sql += "	\"gcp_process_st\"	INTEGER DEFAULT 0,"
        sql += "	\"av_height_obj\"	FLOAT,"
        sql += "	\"n_strips\"	INTEGER NOT NULL DEFAULT 1,"
        sql += "	\"id_zone\"	INTEGER NOT NULL DEFAULT -1,"
        sql += "	\"id_vector\"	INTEGER NOT NULL DEFAULT -1,"
        sql += "	PRIMARY KEY(\"cod_flight_block\"),"
        sql += "	FOREIGN KEY(\"cod_flight_block\") REFERENCES \"flight_block\"(\"cod_flight_block\") ON UPDATE CASCADE ON DELETE CASCADE"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"flight_block_type_gimbal_mount\" ("
        sql += "	\"id_type_gimbal_mount\"	NUMERIC(5) NOT NULL,"
        sql += "	\"def_type_gimbal_mount\"	VARCHAR(100),"
        sql += "	PRIMARY KEY(\"id_type_gimbal_mount\")"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"flight_block_mounting_type\" ("
        sql += "	\"id_mounting_type\"	NUMERIC(5) NOT NULL,"
        sql += "	\"def_mounting_type\"	VARCHAR(100),"
        sql += "	PRIMARY KEY(\"id_mounting_type\"),"
        sql += "	FOREIGN KEY(\"id_mounting_type\") REFERENCES \"flight_block_mounting_type\"(\"id_mounting_type\") ON UPDATE CASCADE ON DELETE CASCADE"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"flight_block_type\" ("
        sql += "	\"id_fb_type\"	NUMERIC(5) NOT NULL,"
        sql += "	\"def_fb_type\"	VARCHAR(100),"
        sql += "	PRIMARY KEY(\"id_fb_type\")"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"flight_block_nbk\" ("
        sql += "	\"id_nbk\"	NUMERIC(5) NOT NULL,"
        sql += "	\"des_nbk\"	VARCHAR(100),"
        sql += "	PRIMARY KEY(\"id_nbk\")"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"output_c_strips\" ("
        sql += "	\"azi_mean\"	REAL,"
        sql += "	\"azimuth\"	REAL,"
        sql += "	\"base_mn\"	REAL,"
        sql += "	\"cod_flight_block\"	VARCHAR(50),"
        sql += "	\"code_strip\"	VARCHAR(100),"
        sql += "	\"crs\"	INTEGER,"
        sql += "	\"ctr_length\"	INTEGER,"
        sql += "	\"ctr_pgmt\"	INTEGER,"
        sql += "	\"g2d_fp_wkt\"	TEXT,"
        sql += "	\"g2d_ndax_wkt\"	TEXT,"
        sql += "	\"g2d_stfp_wkt\"	TEXT,"
        sql += "	\"g2d_tfp_wkt\"	TEXT,"
        sql += "	\"g3d_axis_wkt_m\"	TEXT,"
        sql += "	\"g3d_ndax_wkt\"	TEXT,"
        sql += "	\"gsd_max\"	REAL,"
        sql += "	\"gsd_mean\"	REAL,"
        sql += "	\"gsd_min\"	REAL,"
        sql += "	\"id_strips\"	VARCHAR(100),"
        sql += "	\"img_fst\"	VARCHAR(100),"
        sql += "	\"img_lst\"	VARCHAR(100),"
        sql += "	\"length\"	REAL,"
        sql += "	\"lmax_mtns\"	REAL,"
        sql += "	\"fw_ov_mn\"	REAL,"
        sql += "	\"fw_ov_mx\"	REAL,"
        sql += "	\"num_imgs\"	INTEGER,"
        sql += "	\"pgsd_mt\"	REAL,"
        sql += "	\"rowid\"	INTEGER NOT NULL,"
        sql += "	\"sd_ov_mn\"	REAL,"
        sql += "	\"sd_ov_mx\"	REAL,"
        sql += "	\"type\"	VARCHAR(50),"
        sql += "	PRIMARY KEY(\"rowid\")"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"output_c_stereo_pairs\" ("
        sql += "	\"b_h_Fact\"	REAL,"
        sql += "	\"cod_flight_block\"	VARCHAR(50),"
        sql += "	\"crs\"	INTEGER,"
        sql += "	\"g2d_fp_wkt_m\"	TEXT,"
        sql += "	\"g2d_tfp_wkt\"	TEXT,"
        sql += "	\"id_stereo_pairs\"	VARCHAR(100),"
        sql += "	\"img_a_cd\"	VARCHAR(100),"
        sql += "	\"img_a_id\"	VARCHAR(100),"
        sql += "	\"img_b_cd\"	VARCHAR(100),"
        sql += "	\"img_b_id\"	VARCHAR(100),"
        sql += "	\"mn_h_fly\"	REAL,"
        sql += "	\"rowid\"	INTEGER NOT NULL,"
        sql += "	\"ster_bs\"	REAL,"
        sql += "	\"strip_cd\"	VARCHAR(100),"
        sql += "	\"strip_id\"	VARCHAR(100),"
        sql += "	PRIMARY KEY(\"rowid\")"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"output_c_images\" ("
        sql += "	\"H_max\"	REAL,"
        sql += "	\"H_min\"	REAL,"
        sql += "	\"H_nadir\"	REAL,"
        sql += "	\"H_pc\"	REAL,"
        sql += "	\"azi_fly\"	REAL,"
        sql += "	\"azimuth\"	REAL,"
        sql += "	\"cod_flight_block\"	VARCHAR(50),"
        sql += "	\"chng_rou\"	REAL,"
        sql += "	\"code_image\"	VARCHAR(100),"
        sql += "	\"crs\"	NUMERIC(5),"
        sql += "	\"ctr_crou\"	NUMERIC(5),"
        sql += "	\"ctr_gsd\"	NUMERIC(5),"
        sql += "	\"ctr_ln_cv\"	NUMERIC(5),"
        sql += "	\"ctr_tr_cv\"	NUMERIC(5),"
        sql += "	\"pc_fc\"	REAL,"
        sql += "	\"pc_sc\"	REAL,"
        sql += "	\"g2d_fp_wkt_m\"	TEXT,"
        sql += "	\"g2d_tfp_wkt\"	TEXT,"
        sql += "	\"g3d_fp_wkt\"	TEXT,"
        sql += "	\"g3d_ndir_wkt\"	TEXT,"
        sql += "	\"g3d_pc_wkt\"	TEXT,"
        sql += "	\"gsd_emc\"	REAL,"
        sql += "	\"gsd_max\"	REAL,"
        sql += "	\"gsd_mean\"	REAL,"
        sql += "	\"gsd_min\"	REAL,"
        sql += "	\"gsd_pc\"	REAL,"
        sql += "	\"gsd_theo\"	REAL,"
        sql += "	\"id_image\"	VARCHAR(100),"
        sql += "	\"fw_ov_af\"	REAL,"
        sql += "	\"fw_ov_bf\"	REAL,"
        sql += "	\"rowid\"	INTEGER NOT NULL,"
        sql += "	\"sensor_cd_OBSOLETO\"	VARCHAR(50),"
        sql += "	\"strip_cd\"	VARCHAR(100),"
        sql += "	\"strip_id\"	VARCHAR(100),"
        sql += "	\"strip_pos\"	VARCHAR(100),"
        sql += "	\"sd_ov_af\"	REAL,"
        sql += "	\"sd_ov_bf\"	REAL,"
        sql += "	PRIMARY KEY(\"rowid\")"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"output_strips_images\" ("
        sql += "	\"cod_flight_block\"	VARCHAR(50),"
        sql += "	\"img_id\"	VARCHAR(50),"
        sql += "	\"pk\"	INTEGER NOT NULL,"
        sql += "	\"strip_id\"	VARCHAR(50),"
        sql += "	PRIMARY KEY(\"pk\")"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"output_strips_connections\" ("
        sql += "	\"azi_fst\"	REAL,"
        sql += "	\"azi_snd\"	REAL,"
        sql += "	\"cod_flight_block\"	VARCHAR(50),"
        sql += "	\"ctr_intr\"	NUMERIC(5),"
        sql += "	\"id_fst\"	VARCHAR(100),"
        sql += "	\"id_snd\"	VARCHAR(100),"
        sql += "	\"mx_im_sz\"	REAL,"
        sql += "	\"orientat\"	VARCHAR(50),"
        sql += "	\"pk\"	INTEGER NOT NULL,"
        sql += "	\"spr_max\"	REAL,"
        sql += "	\"spr_min\"	REAL,"
        sql += "	\"type\"	VARCHAR(50),"
        sql += "	\"type_fst\"	VARCHAR(100),"
        sql += "	\"type_snd\"	VARCHAR(100),"
        sql += "	\"used\"	NUMERIC(5),"
        sql += "	PRIMARY KEY(\"pk\")"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"output_side_overlap\" ("
        sql += "	\"cod_flight_block\"	VARCHAR(50),"
        sql += "	\"img_id\"	VARCHAR(50),"
        sql += "	\"pk\"	NUMERIC(5) NOT NULL,"
        sql += "	\"side_overlap\"	REAL,"
        sql += "	\"strip_id\"	VARCHAR(10),"
        sql += "	PRIMARY KEY(\"pk\")"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"flight_block_shp\" ("
        sql += "	\"id_shp\"	NUMERIC(5) NOT NULL,"
        sql += "	\"def_shp\"	VARCHAR(100),"
        sql += "	PRIMARY KEY(\"id_shp\")"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"flight_block_egi\" ("
        sql += "	\"id_egi\"	NUMERIC(5) NOT NULL,"
        sql += "	\"def_egi\"	VARCHAR(100),"
        sql += "	PRIMARY KEY(\"id_egi\")"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"flight_block_trajectory_type\" ("
        sql += "	\"id_trajectory_type\"	NUMERIC(5) NOT NULL,"
        sql += "	\"def_trajectory_type\"	VARCHAR(100),"
        sql += "	PRIMARY KEY(\"id_trajectory_type\")"
        sql += ");"
        sqls.append(sql)
        sql = "CREATE TABLE IF NOT EXISTS \"srs_prj\" ("
        sql += "	\"srs_id\"	INTEGER NOT NULL,"
        sql += "	\"description\"	TEXT NOT NULL,"
        sql += "	\"use_prj\"	INTEGER,"
        sql += "	PRIMARY KEY(\"srs_id\")"
        sql += ");"
        sqls.append(sql)
        sql = "INSERT INTO \"flight_block_ercMav\" (\"id_erc\",\"def_erc\") VALUES (0,'Landing at current position'),"
        sql += " (2,'Continue the waypoint mission'),"
        sql += " (3,'Go to Home position and landing');"
        sqls.append(sql)
        sql = "INSERT INTO \"flight_block_egiMav\" (\"id_egi\",\"def_egi\") VALUES (0,'Landing. (pitch & roll commands allowed)');"
        sqls.append(sql)
        sql = "INSERT INTO \"flight_block_ealMav\" (\"id_eal\",\"def_eal\") VALUES (0,'Descend slowly at current position'),"
        sql += " (2,'Continue the mission (disabled)'),"
        sql += " (3,'Go to Home position and landing');"
        sqls.append(sql)
        sql = "INSERT INTO \"fields_descriptions\" (\"id\",\"table\",\"fieldname\",\"version_firmaware\",\"pk\",\"required\",\"var_python\",\"widget\",\"label\",\"etiqueta\",\"what_this\",\"que_es\",\"page_toolbox\",\"panel_group\",\"type_sqlite\",\"type_python\",\"unit\",\"qsettings\",\"default_value\",\"max_value\",\"min_value\",\"decimals\",\"single_step\",\"precision\",\"planificacion\",\"notes\") VALUES (1,'output_c_stereo_pairs','gid','all',1,0,NULL,NULL,NULL,NULL,NULL,'Clave primaria del par estereoscópico.',NULL,NULL,'INTEGER',NULL,NULL,1,NULL,NULL,NULL,NULL,NULL,NULL,1,'Se cambia el nombre del campo de pk a gid por convecionalismo con QGIS y para más claridad'),"
        sql += " (2,'output_c_stereo_pairs','id_stereo_pairs','all',0,0,NULL,NULL,NULL,NULL,NULL,'Identificador del par estereoscópico formado por la concatenación de los identificadores de las imágenes.',NULL,NULL,'VARCHAR(100)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (3,'output_c_stereo_pairs','cod_flight_block','all',0,0,NULL,NULL,NULL,NULL,NULL,'Código del bloque de vuelo al que pertenece el par estereoscópico.',NULL,NULL,'VARCHAR(50)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (4,'output_c_stereo_pairs','strip_cd','all',0,0,NULL,NULL,NULL,NULL,NULL,'Código de la pasada a la que pertenece el par estereoscópico.',NULL,NULL,'VARCHAR(100)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,'ver si se puede pasar a un entero'),"
        sql += " (5,'output_c_stereo_pairs','strip_id','all',0,0,NULL,NULL,NULL,NULL,NULL,'Identificador de la pasada a la que pertenece el par estereoscópico.',NULL,NULL,'VARCHAR(100)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,'ver si se puede pasar a un entero'),"
        sql += " (6,'output_c_stereo_pairs','img_a_cd','all',0,0,NULL,NULL,NULL,NULL,NULL,'Código de la imagen anterior, de las dos imágenes del par estereoscópico.',NULL,NULL,'VARCHAR(100)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,'ver si se puede pasar a un entero'),"
        sql += " (7,'output_c_stereo_pairs','img_a_id','all',0,0,NULL,NULL,NULL,NULL,NULL,'Identificador de la imagen anterior, de las dos imágenes del par estereoscópico.',NULL,NULL,'VARCHAR(100)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (8,'output_c_stereo_pairs','img_b_cd','all',0,0,NULL,NULL,NULL,NULL,NULL,'Código de la imagen posterior, de las dos imágenes del par estereoscópico.',NULL,NULL,'VARCHAR(100)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,'ver si se puede pasar a un entero'),"
        sql += " (9,'output_c_stereo_pairs','img_b_id','all',0,0,NULL,NULL,NULL,NULL,NULL,'Identificador de la imagen posterior,  de las dos imágenes del par estereoscópico.',NULL,NULL,'VARCHAR(100)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (10,'output_c_stereo_pairs','crs','all',0,0,NULL,NULL,NULL,NULL,NULL,'Código EPSG del CRS al que se referien las geometrías.',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (11,'output_c_stereo_pairs','mn_h_fly','all',0,0,NULL,NULL,NULL,NULL,NULL,'Altura media de vuelo sobre el terreno, en m.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (12,'output_c_stereo_pairs','ster_bs','all',0,0,NULL,NULL,NULL,NULL,NULL,'Base estereoscópica, en m.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (13,'output_c_stereo_pairs','b_h_Fact','all',0,0,NULL,NULL,NULL,NULL,NULL,'Factor base frente altura media de vuelo sobre el terreno, adimensional.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (14,'output_c_stereo_pairs','g2d_tfp_wkt','all',0,0,NULL,NULL,NULL,NULL,NULL,'Geometría poligonal 2D de la huella teórica.',NULL,NULL,'TEXT',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (15,'output_c_stereo_pairs','g2d_fp_wkt_m','all',0,0,NULL,NULL,NULL,NULL,NULL,'Geometría poligonal 2D de la huella contra el MDT.',NULL,NULL,'TEXT',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (16,'output_c_images','gid','all',1,0,NULL,NULL,NULL,NULL,NULL,'Clave primaria de la imagen.',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,'Se cambia el nombre del campo de pk a gid por convecionalismo con QGIS y para más claridad'),"
        sql += " (17,'output_c_images','id_image','all',0,0,NULL,NULL,NULL,NULL,NULL,'Identificador de la imagen. Se concatena con _, por ejemplo, 1_1',NULL,NULL,'VARCHAR(100)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,'Es del tipo 1_1'),"
        sql += " (18,'output_c_images','cod_flight_block','all',0,0,NULL,NULL,NULL,NULL,NULL,'Código del bloque de vuelo al que pertenece la imagen.',NULL,NULL,'VARCHAR(50)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (19,'output_c_images','code_image','all',0,0,NULL,NULL,NULL,NULL,NULL,'Código de la imagen.',NULL,NULL,'VARCHAR(100)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,'Mirar en código programa si se puede pasar a integer'),"
        sql += " (20,'output_c_images','strip_cd','all',0,0,NULL,NULL,NULL,NULL,NULL,'Código de la pasada a la que pertenece la imagen.',NULL,NULL,'VARCHAR(100)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,'Mirar en código programa si se puede pasar a integer'),"
        sql += " (21,'output_c_images','strip_id','all',0,0,NULL,NULL,NULL,NULL,NULL,'Identificador de la pasadas a la que pertenece la imagen.',NULL,NULL,'VARCHAR(100)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,'Mirar en código programa si se puede pasar a integer'),"
        sql += " (22,'output_c_images','sensor_cd_OBSOLETO','all',0,0,NULL,NULL,NULL,NULL,NULL,'Código de la cámara con que se ha adquirido la imagen. Es una cadena de texto del tipo OptioA40',NULL,NULL,'VARCHAR(50)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,'CANDIDATO A QUITAR'),"
        sql += " (23,'output_c_images','crs','all',0,0,NULL,NULL,NULL,NULL,NULL,'Código EPSG del CRS al que se refieren las geometrías.',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (24,'output_c_images','gsd_theo','all',0,0,NULL,NULL,NULL,NULL,NULL,'GSD teórico, en m.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (25,'output_c_images','gsd_mean','all',0,0,NULL,NULL,NULL,NULL,NULL,'GSD medio, en m.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (26,'output_c_images','gsd_max','all',0,0,NULL,NULL,NULL,NULL,NULL,'GSD máximo, en m.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (27,'output_c_images','gsd_min','all',0,0,NULL,NULL,NULL,NULL,NULL,'GSD mínimo, en m.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (28,'output_c_images','gsd_pc','all',0,0,NULL,NULL,NULL,NULL,NULL,'GSD de la la proyección del PPA contra el MDT, en m.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (29,'output_c_images','gsd_emc','all',0,0,NULL,NULL,NULL,NULL,NULL,'EMC del GSD medio, en m.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (30,'output_c_images','omega','all',0,0,NULL,NULL,NULL,NULL,NULL,'Giro omega, en DEG.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,'david: en el ejemplo del programa de c++ no sale este campo, sin embargo si que está en field_descriptions'),"
        sql += " (31,'output_c_images','phi','all',0,0,NULL,NULL,NULL,NULL,NULL,'Giro phi, en DEG.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,'david: en el ejemplo del programa de c++ no sale este campo, sin embargo si que está en field_descriptions'),"
        sql += " (32,'output_c_images','kappa','all',0,0,NULL,NULL,NULL,NULL,NULL,'Giro kappa, en DEG.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,'david: en el ejemplo del programa de c++ no sale este campo, sin embargo si que está en field_descriptions'),"
        sql += " (33,'output_c_images','azi_fly','all',0,0,NULL,NULL,NULL,NULL,NULL,'Azimut de vuelo, en DEG, calculado con dos centros de proyección consecutivos.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (34,'output_c_images','azimuth','all',0,0,NULL,NULL,NULL,NULL,NULL,'Azimut, en DEG, calculado con el giro kappa.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (35,'output_c_images','H_pc','all',0,0,NULL,NULL,NULL,NULL,NULL,'Altitud ortométrica del centro de proyección, en m.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (36,'output_c_images','H_nadir','all',0,0,NULL,NULL,NULL,NULL,NULL,'Altitud ortométrica del nadir, en m.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (37,'output_c_images','H_max','all',0,0,NULL,NULL,NULL,NULL,NULL,'Altitud ortométrica máxima de la huella, en m.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (38,'output_c_images','H_min','all',0,0,NULL,NULL,NULL,NULL,NULL,'Altitud ortométrica mínima de la huella, en m.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (39,'output_c_images','gps_time','all',0,0,NULL,NULL,NULL,NULL,NULL,'Tiempo GPS, en segundos respecto a la semana GPS.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,'david: en el ejemplo del programa de c++ no sale este campo, sin embargo si que está en field_descriptions'),"
        sql += " (40,'output_c_images','fly_date','all',0,0,NULL,NULL,NULL,NULL,NULL,'Fecha de vuelo.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,'david: en el ejemplo del programa de c++ no sale este campo, sin embargo si que está en field_descriptions'),"
        sql += " (41,'output_c_images','fw_ov_af','all',0,0,NULL,NULL,NULL,NULL,NULL,'Recubrimiento longitudinal posterior, en tanto por ciento.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (42,'output_c_images','fw_ov_bf','all',0,0,NULL,NULL,NULL,NULL,NULL,'Recubrimiento longitudinal anterior, en tanto por ciento.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (43,'output_c_images','sd_ov_af','all',0,0,NULL,NULL,NULL,NULL,NULL,'Recubrimiento transversal posterior, en tanto por ciento.',NULL,NULL,'VARCHAR(100)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (44,'output_c_images','sd_ov_bf','all',0,0,NULL,NULL,NULL,NULL,NULL,'Recubrimiento transversal anterior, en tanto por ciento.',NULL,NULL,'VARCHAR(100)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (45,'output_c_images','vertical','all',0,0,NULL,NULL,NULL,NULL,NULL,'Verticalidad, en DEG.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,'david: en el ejemplo del programa de c++ no sale este campo, sin embargo si que está en field_descriptions'),"
        sql += " (46,'output_c_images','chng_ver','all',0,0,NULL,NULL,NULL,NULL,NULL,'Cambio en el ángulo de verticalidad, en DEG.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,'david: en el ejemplo del programa de c++ no sale este campo, sin embargo si que está en field_descriptions'),"
        sql += " (47,'output_c_images','solar','all',0,0,NULL,NULL,NULL,NULL,NULL,'Altura solar, en DEG.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,'david: en el ejemplo del programa de c++ no sale este campo, sin embargo si que está en field_descriptions'),"
        sql += " (48,'output_c_images','drift','all',0,0,NULL,NULL,NULL,NULL,NULL,'Deriva, en DEG.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,'david: en el ejemplo del programa de c++ no sale este campo, sin embargo si que está en field_descriptions'),"
        sql += " (49,'output_c_images','chng_rou','all',0,0,NULL,NULL,NULL,NULL,NULL,'Cambio de rumbo, en DEG.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (50,'output_c_images','img_near','all',0,0,NULL,NULL,NULL,NULL,NULL,'Identificador de la imagen de planificación más cercana.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,'david: en el ejemplo del programa de c++ no sale este campo, sin embargo si que está en field_descriptions'),"
        sql += " (51,'output_c_images','pc_fc','all',0,0,NULL,NULL,NULL,NULL,NULL,'Primera coordenada del centro de proyección, en m.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (52,'output_c_images','pc_sc','all',0,0,NULL,NULL,NULL,NULL,NULL,'Segunda coordenada del centro de proyección, en m.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (53,'output_c_images','plan_dis','all',0,0,NULL,NULL,NULL,NULL,NULL,'Separación a la imagen de planificación más cercana, en m.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,'david: en el ejemplo del programa de c++ no sale este campo, sin embargo si que está en field_descriptions'),"
        sql += " (54,'output_c_images','strip_pos','all',0,0,NULL,NULL,NULL,NULL,NULL,'Posición en la pasada desde el extremo de la misma.',NULL,NULL,'VARCHAR(100)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,'Mirar en código programa si se puede pasar a integer'),"
        sql += " (55,'output_c_images','ctr_gsd','all',0,0,NULL,NULL,NULL,NULL,NULL,'Control del GSD (1-Cumple, 0-No cumple).',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (56,'output_c_images','ctr_ln_cv','all',0,0,NULL,NULL,NULL,NULL,NULL,'Control del recubrimiento longitudinal (1-Cumple, 0-No cumple).',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (57,'output_c_images','ctr_tr_cv','all',0,0,NULL,NULL,NULL,NULL,NULL,'Control del recubrimiento transversal (1-Cumple, 0-No cumple).',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (58,'output_c_images','ctr_solar','all',0,0,NULL,NULL,NULL,NULL,NULL,'Control de la altura solar (1-Cumple, 0-No cumple).',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,'david: en el ejemplo del programa de c++ no sale este campo, sin embargo si que está en field_descriptions'),"
        sql += " (59,'output_c_images','ctr_vert','all',0,0,NULL,NULL,NULL,NULL,NULL,'Control de la verticalidad (1-Cumple, 0-No cumple).',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,'david: en el ejemplo del programa de c++ no sale este campo, sin embargo si que está en field_descriptions'),"
        sql += " (60,'output_c_images','ctr_cver','all',0,0,NULL,NULL,NULL,NULL,NULL,'Control del cambio de verticalidad (1-Cumple, 0-No cumple).',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,'david: en el ejemplo del programa de c++ no sale este campo, sin embargo si que está en field_descriptions'),"
        sql += " (61,'output_c_images','ctr_drft','all',0,0,NULL,NULL,NULL,NULL,NULL,'Control de la deriva (1-Cumple, 0-No cumple).',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,'david: en el ejemplo del programa de c++ no sale este campo, sin embargo si que está en field_descriptions'),"
        sql += " (62,'output_c_images','ctr_crou','all',0,0,NULL,NULL,NULL,NULL,NULL,'Control del cambio de rumbo (1-Cumple, 0-No cumple).',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (63,'output_c_images','ctr_pdis','all',0,0,NULL,NULL,NULL,NULL,NULL,'Control de la diferencia a planificación (1-Cumple, 0-No cumple).',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,'david: en el ejemplo del programa de c++ no sale este campo, sin embargo si que está en field_descriptions'),"
        sql += " (64,'output_c_images','ctr_date','all',0,0,NULL,NULL,NULL,NULL,NULL,'Control de la fecha de vuelo (1-Cumple, 0-No cumple).',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,'david: en el ejemplo del programa de c++ no sale este campo, sin embargo si que está en field_descriptions'),"
        sql += " (65,'output_c_images','g3d_pc_wkt','all',0,0,NULL,NULL,NULL,NULL,NULL,'Geometría puntual 3D del centro de proyección.',NULL,NULL,'TEXT',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (66,'output_c_images','g3d_ndir_wkt','all',0,0,NULL,NULL,NULL,NULL,NULL,'Geometría puntual 3D de la proyección del PPA contra el MDT.',NULL,NULL,'TEXT',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (67,'output_c_images','g2d_tfp_wkt','all',0,0,NULL,NULL,NULL,NULL,NULL,'Geometría poligonal 2D de la huella teórica.',NULL,NULL,'TEXT',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (68,'output_c_images','g2d_fp_wkt_m','all',0,0,NULL,NULL,NULL,NULL,NULL,'Geometría poligonal 2D de la huella contra el MDT.',NULL,NULL,'TEXT',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,'geometría maestra'),"
        sql += " (69,'output_c_images','g3d_fp_wkt','all',0,0,NULL,NULL,NULL,NULL,NULL,'Geometría poligonal 3D de la huella contra el MDT.',NULL,NULL,'TEXT',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (70,'output_c_strips','gid','all',1,0,NULL,NULL,NULL,NULL,NULL,'Clave primaria de la pasada.',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,'Se cambia el nombre del campo de pk a gid por convecionalismo con QGIS y para más claridad'),"
        sql += " (71,'output_c_strips','id_strips','all',0,0,NULL,NULL,NULL,NULL,NULL,'Identificador de la pasada.',NULL,NULL,'VARCHAR(100)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,'ver si se puede pasar a entero'),"
        sql += " (72,'output_c_strips','cod_flight_block','all',0,0,NULL,NULL,NULL,NULL,NULL,'Código del bloque al que pertenece la pasada.',NULL,NULL,'VARCHAR(50)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (73,'output_c_strips','code_strip','all',0,0,NULL,NULL,NULL,NULL,NULL,'Código de la pasada.',NULL,NULL,'VARCHAR(100)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,'ver si se puede pasar a un entero'),"
        sql += " (74,'output_c_strips','type','all',0,0,NULL,NULL,NULL,NULL,NULL,'Tipo de la pasada en función de su orientación (NS, EO, …).',NULL,NULL,'VARCHAR(50)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (75,'output_c_strips','azimuth','all',0,0,NULL,NULL,NULL,NULL,NULL,'Azimut de la pasada definido por sus extremos, en DEG.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (76,'output_c_strips','crs','all',0,0,NULL,NULL,NULL,NULL,NULL,'Código EPSG del CRS al que se refieren las geometrías.',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (77,'output_c_strips','fw_ov_mx','all',0,0,NULL,NULL,NULL,NULL,NULL,'Valor máximo del recubrimiento longitudinal, en tanto por ciento.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (78,'output_c_strips','fw_ov_mn','all',0,0,NULL,NULL,NULL,NULL,NULL,'Valor mínimo del recubrimiento longitudinal, en tanto por ciento.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (79,'output_c_strips','sd_ov_mx','all',0,0,NULL,NULL,NULL,NULL,NULL,'Valor máximo del recubrimiento transversal, en tanto por ciento.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (80,'output_c_strips','sd_ov_mn','all',0,0,NULL,NULL,NULL,NULL,NULL,'Valor mínimo del recubrimiento transversal, en tanto por ciento.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (81,'output_c_strips','gsd_mean','all',0,0,NULL,NULL,NULL,NULL,NULL,'GSD medio, en m.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (82,'output_c_strips','gsd_max','all',0,0,NULL,NULL,NULL,NULL,NULL,'GSD máximo, en m.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (83,'output_c_strips','gsd_min','all',0,0,NULL,NULL,NULL,NULL,NULL,'GSD mínimo, en m.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (84,'output_c_strips','img_fst','all',0,0,NULL,NULL,NULL,NULL,NULL,'Identificador de la primera imagen de la pasada. Cadena de texto concatenada con _',NULL,NULL,'VARCHAR(100)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (85,'output_c_strips','img_lst','all',0,0,NULL,NULL,NULL,NULL,NULL,'Identificador de la última imagen de la pasada. Cadena de texto concatenada con _',NULL,NULL,'VARCHAR(100)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (86,'output_c_strips','num_imgs','all',0,0,NULL,NULL,NULL,NULL,NULL,'Número de imágenes de la pasada.',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (87,'output_c_strips','pgsd_mt','all',0,0,NULL,NULL,NULL,NULL,NULL,'Porcentaje de imágenes con GSD mayor que la tolerancia.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (88,'output_c_strips','lmax_mtns_OBSOLETO','all',0,0,NULL,NULL,NULL,NULL,NULL,'Longitud del máximo número de hojas del MTN50 admitido.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (89,'output_c_strips','length','all',0,0,NULL,NULL,NULL,NULL,NULL,'Longitud de la pasada, en metros.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (90,'output_c_strips','azi_mean','all',0,0,NULL,NULL,NULL,NULL,NULL,'Azimut medio, en DEG.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (91,'output_c_strips','fly_date','all',0,0,NULL,NULL,NULL,NULL,NULL,'Fecha de vuelo.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,'david: en el ejemplo del programa de c++ no sale este campo, sin embargo si que está en field_descriptions'),"
        sql += " (92,'output_c_strips','gpst_min','all',0,0,NULL,NULL,NULL,NULL,NULL,'Mínimo tiempo GPS, en segundos respecto a la semana GPS.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (93,'output_c_strips','gpst_max','all',0,0,NULL,NULL,NULL,NULL,NULL,'Máximo tiempo GPS, en segundos respecto a la semana GPS.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (94,'output_c_strips','base_mn','all',0,0,NULL,NULL,NULL,NULL,NULL,'Base media, en m.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (95,'output_c_strips','ctr_length','all',0,0,NULL,NULL,NULL,NULL,NULL,'Control de la longitud (1-Cumple, 0-No cumple).',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (96,'output_c_strips','ctr_pgmt','all',0,0,NULL,NULL,NULL,NULL,NULL,'Control del porcentage de imágenes con GSD mayor que la tolerancia (1-Cumple, 0-No cumple).',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (97,'output_c_strips','g3d_axis_wkt_m','all',0,0,NULL,NULL,NULL,NULL,NULL,'Geometría lineal 3D del eje de vuelo.',NULL,NULL,'TEXT',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (98,'output_c_strips','g3d_ndax_wkt','all',0,0,NULL,NULL,NULL,NULL,NULL,'Geometría lineal 3D del nadir.',NULL,NULL,'TEXT',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (99,'output_c_strips','g2d_ndax_wkt','all',0,0,NULL,NULL,NULL,NULL,NULL,'Geometría lineal 2D del nadir.',NULL,NULL,'TEXT',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (100,'output_c_strips','g2d_tfp_wkt','all',0,0,NULL,NULL,NULL,NULL,NULL,'Geometría poligonal 2D de la huella teórica.',NULL,NULL,'TEXT',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (101,'output_c_strips','g2d_fp_wkt','all',0,0,NULL,NULL,NULL,NULL,NULL,'Geometría poligonal 2D de la huella contra el MDT..',NULL,NULL,'TEXT',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (102,'output_c_strips','g2d_stfp_wkt','all',0,0,NULL,NULL,NULL,NULL,NULL,'Geometría poligonal 2D de la zona con estereoscopía de la huella contra el MDT.',NULL,NULL,'TEXT',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (103,'output_strips_images','pk','all',1,0,NULL,NULL,NULL,NULL,NULL,'Clave primaria de las imágenes por pasada.',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (104,'output_strips_images','img_id','all',0,0,NULL,NULL,NULL,NULL,NULL,'Identificador de las imágenes por pasada.',NULL,NULL,'VARCHAR(50)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (105,'output_strips_images','cod_flight_block','all',0,0,NULL,NULL,NULL,NULL,NULL,'Código del bloque al que pertenece la imagen y la pasada.',NULL,NULL,'VARCHAR(50)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (106,'output_strips_images','strip_id','all',0,0,NULL,NULL,NULL,NULL,NULL,'Identificador de la pasada.',NULL,NULL,'VARCHAR(50)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (107,'output_strips_connections','pk','all',1,0,NULL,NULL,NULL,NULL,NULL,'Clave primaria.',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (108,'output_strips_connections','cod_flight_block','all',0,0,NULL,NULL,NULL,NULL,NULL,'Código del bloque al que pertenece la conexión entre pasadas.',NULL,NULL,'VARCHAR(50)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (109,'output_strips_connections','id_fst','all',0,0,NULL,NULL,NULL,NULL,NULL,'Identificador de la primera pasada.',NULL,NULL,'VARCHAR(100)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (110,'output_strips_connections','id_snd','all',0,0,NULL,NULL,NULL,NULL,NULL,'Identificador de la segunda pasada.',NULL,NULL,'VARCHAR(100)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (111,'output_strips_connections','type_fst','all',0,0,NULL,NULL,NULL,NULL,NULL,'Tipo de la primera pasada en función de su orientación (EO, NS, …).',NULL,NULL,'VARCHAR(100)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (112,'output_strips_connections','type_snd','all',0,0,NULL,NULL,NULL,NULL,NULL,'Tipo de la segunda pasada en función de su orientación (EO, NS, …).',NULL,NULL,'VARCHAR(100)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (113,'output_strips_connections','type','all',0,0,NULL,NULL,NULL,NULL,NULL,'Tipo del solape: transversal, longitudinal u oblicuo.',NULL,NULL,'VARCHAR(50)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (114,'output_strips_connections','orientat','all',0,0,NULL,NULL,NULL,NULL,NULL,'Orientación de la pasada: superior o inferior.',NULL,NULL,'VARCHAR(50)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (115,'output_strips_connections','azi_fst','all',0,0,NULL,NULL,NULL,NULL,NULL,'Azimut de la primera pasada, en DEG.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (116,'output_strips_connections','azi_snd','all',0,0,NULL,NULL,NULL,NULL,NULL,'Azimut de la segunda pasada, en DEG.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (117,'output_strips_connections','spr_max','all',0,0,NULL,NULL,NULL,NULL,NULL,'Máxima separación entre los ejes de las pasadas, en m.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (118,'output_strips_connections','spr_min','all',0,0,NULL,NULL,NULL,NULL,NULL,'Mínima separación entre los ejes de las pasadas, en m.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (119,'output_strips_connections','mx_im_sz','all',0,0,NULL,NULL,NULL,NULL,NULL,'Tamaño máximo de una imagen en el sentido ortogonal a la dirección de vuelo, en m.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (120,'output_strips_connections','used','all',0,0,NULL,NULL,NULL,NULL,NULL,'1-Utilizada, 0-No utilizada, para el cálculo de los recubrimientos transversales en las imágenes.',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (121,'output_strips_connections','ctr_intr','all',0,0,NULL,NULL,NULL,NULL,NULL,'Control del solape longitudinal entre pasadas (1-Cumple, 0-No cumple).',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (122,'output_side_overlap','pk','all',1,0,NULL,NULL,NULL,NULL,NULL,'Clave primaria del recubrimiento transversal.',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (123,'output_side_overlap','cod_flight_block','all',0,0,NULL,NULL,NULL,NULL,NULL,'Código del bloque.',NULL,NULL,'VARCHAR(50)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (124,'output_side_overlap','img_id','all',0,0,NULL,NULL,NULL,NULL,NULL,'Identificador de la imagen.',NULL,NULL,'VARCHAR(50)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (125,'output_side_overlap','strip_id','all',0,0,NULL,NULL,NULL,NULL,NULL,'Identificador de la pasada.',NULL,NULL,'VARCHAR(10)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,'Comprobar si es siempre un número y si se puede concatenar. Si es un entero pasar a ese tipo de campo.'),"
        sql += " (126,'output_side_overlap','side_overlap','all',0,0,NULL,NULL,NULL,NULL,NULL,'Recubrimiento transversal, en tanto por ciento.',NULL,NULL,'REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (127,'flight_blocks','pk','all',1,1,NULL,NULL,NULL,NULL,NULL,'Clave primaria del bloque de vuelo.',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,'Campo candidato a eliminar por pertenecer a una tabla obsoleta. Los datos de esta tabla MFLiP se almacenan ahora en la tabla flight_block'),"
        sql += " (128,'flight_blocks','cod_flight_block','all',0,0,NULL,NULL,NULL,NULL,NULL,'Código del bloque.',NULL,NULL,'VARCHAR(50)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),"
        sql += " (129,'flight_blocks','type','all',0,0,NULL,NULL,NULL,NULL,NULL,'Tipo del bloque.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (131,'flight_blocks','planning','all',0,0,NULL,NULL,NULL,NULL,NULL,'Código del bloque de planificación correspondiente, si es un bloque de ejecución y se ha definido.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (132,'flight_blocks','sensor_cd','all',0,0,NULL,NULL,NULL,NULL,NULL,'Código del sensor, si todas las imágenes del bloque se han adquirido con el mismo sensor.',NULL,NULL,'VARCHAR(50)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,'Campo candidato a eliminar por pertenecer a una tabla obsoleta. Los datos de esta tabla MFLiP se almacenan ahora en la tabla flight_block'),"
        sql += " (133,'flight_blocks','crs','all',0,0,NULL,NULL,NULL,NULL,NULL,'Código EPSG del CRS al que se refieren las geometrías.',NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,'Campo candidato a eliminar por pertenecer a una tabla obsoleta. Los datos de esta tabla MFLiP se almacenan ahora en la tabla flight_block'),"
        sql += " (134,'flight_blocks','g2d_stfp','all',0,0,NULL,NULL,NULL,NULL,NULL,'Geometría poligonal 2D de la zona de la huella contra el MDT con estereoscopía.',NULL,NULL,'TEXT',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,1,'Campo candidato a eliminar por pertenecer a una tabla obsoleta. Los datos de esta tabla MFLiP se almacenan ahora en la tabla flight_block. Este campo se incorpora a la tabla flight_block de SOGEDRON'),"
        sql += " (135,'images_radiometry','pk','all',0,0,NULL,NULL,NULL,NULL,NULL,'Clave primaria de las estadísticas radiométricas de la imagen.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (136,'images_radiometry','cod_flight_block','all',0,0,NULL,NULL,NULL,NULL,NULL,'Código del bloque al que pertenece la imagen, si se ha podido extraer del nombre del fichero de la imagen.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (137,'images_radiometry','strip_cd','all',0,0,NULL,NULL,NULL,NULL,NULL,'Código de la pasada a la que pertenece la imagen, si se ha podido extraer del nombre del fichero de la imagen.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (138,'images_radiometry','image_cd','all',0,0,NULL,NULL,NULL,NULL,NULL,'Código de la imagen, si se ha podido extraer del nombre del fichero de la imagen.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (139,'images_radiometry','id','all',0,0,NULL,NULL,NULL,NULL,NULL,'Nombre del fichero de la imagen sin la ruta, utilizado como identificador único.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (140,'images_radiometry','rows','all',0,0,NULL,NULL,NULL,NULL,NULL,'Número de filas de la imagen.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (141,'images_radiometry','columns','all',0,0,NULL,NULL,NULL,NULL,NULL,'Número de columnas de la imagen.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (142,'images_radiometry','no_bands','all',0,0,NULL,NULL,NULL,NULL,NULL,'Número de bandas de la imagen.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (143,'images_radiometry','p_min_r','all',0,0,NULL,NULL,NULL,NULL,NULL,'Porcentaje de píxeles en el nivel digital 0 (mínimo) del rojo.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (144,'images_radiometry','p_min_g','all',0,0,NULL,NULL,NULL,NULL,NULL,'Porcentaje de píxeles en el nivel digital 0 (mínimo) del verde.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (145,'images_radiometry','p_min_b','all',0,0,NULL,NULL,NULL,NULL,NULL,'Porcentaje de píxeles en el nivel digital 0 (mínimo) del azul.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (146,'images_radiometry','p_min_ir','all',0,0,NULL,NULL,NULL,NULL,NULL,'Porcentaje de píxeles en el nivel digital 0 (mínimo) del infrarrojo.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (147,'images_radiometry','mean_pmn','all',0,0,NULL,NULL,NULL,NULL,NULL,'Porcentaje de píxeles en el nivel digital 0 (mínimo) para la media de RGB.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (148,'images_radiometry','p_max_r','all',0,0,NULL,NULL,NULL,NULL,NULL,'Porcentaje de píxeles en el nivel digital 255 (máximo) del rojo.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (149,'images_radiometry','p_max_g','all',0,0,NULL,NULL,NULL,NULL,NULL,'Porcentaje de píxeles en el nivel digital 255 (máximo) del verde.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (150,'images_radiometry','p_max_b','all',0,0,NULL,NULL,NULL,NULL,NULL,'Porcentaje de píxeles en el nivel digital 255 (máximo) del azul.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (151,'images_radiometry','p_max_ir','all',0,0,NULL,NULL,NULL,NULL,NULL,'Porcentaje de píxeles en el nivel digital 255 (máximo) del infrarrojo.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (152,'images_radiometry','mean_pmx','all',0,0,NULL,NULL,NULL,NULL,NULL,'Porcentaje de píxeles en el nivel digital 255 (máximo) para la media de RGB.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (153,'images_radiometry','mean_r','all',0,0,NULL,NULL,NULL,NULL,NULL,'Media de los niveles digitales del rojo.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (154,'images_radiometry','mean_g','all',0,0,NULL,NULL,NULL,NULL,NULL,'Media de los niveles digitales del verde.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (155,'images_radiometry','mean_b','all',0,0,NULL,NULL,NULL,NULL,NULL,'Media de los niveles digitales del azul.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (156,'images_radiometry','mean_ir','all',0,0,NULL,NULL,NULL,NULL,NULL,'Media de los niveles digitales del infrarrojo.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (157,'images_radiometry','mean','all',0,0,NULL,NULL,NULL,NULL,NULL,'Media de las medias de RGB.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (158,'images_radiometry','std_r','all',0,0,NULL,NULL,NULL,NULL,NULL,'Desviación típica de la media de los niveles digitales del rojo.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (159,'images_radiometry','std_g','all',0,0,NULL,NULL,NULL,NULL,NULL,'Desviación típica de la media de los niveles digitales del verde.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (160,'images_radiometry','std_b','all',0,0,NULL,NULL,NULL,NULL,NULL,'Desviación típica de la media de los niveles digitales del azul.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (161,'images_radiometry','std_ir','all',0,0,NULL,NULL,NULL,NULL,NULL,'Desviación típica de la media de los niveles digitales del infrarrojo.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (162,'images_radiometry','mean_std','all',0,0,NULL,NULL,NULL,NULL,NULL,'Desviación típica de la media de las medias de RGB.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (163,'images_radiometry','min_r','all',0,0,NULL,NULL,NULL,NULL,NULL,'Nivel digital mínimo del rojo.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (164,'images_radiometry','min_g','all',0,0,NULL,NULL,NULL,NULL,NULL,'Nivel digital mínimo del verde.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (165,'images_radiometry','min_b','all',0,0,NULL,NULL,NULL,NULL,NULL,'Nivel digital mínimo del azul.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (166,'images_radiometry','min_ir','all',0,0,NULL,NULL,NULL,NULL,NULL,'Nivel digital mínimo del infrarrojo.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (167,'images_radiometry','mean_min','all',0,0,NULL,NULL,NULL,NULL,NULL,'Nivel digital mínimo de la media de RGB.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (168,'images_radiometry','max_r','all',0,0,NULL,NULL,NULL,NULL,NULL,'Nivel digital máximo del rojo.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (169,'images_radiometry','max_g','all',0,0,NULL,NULL,NULL,NULL,NULL,'Nivel digital máximo del verde.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (170,'images_radiometry','max_b','all',0,0,NULL,NULL,NULL,NULL,NULL,'Nivel digital máximo del azul.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (171,'images_radiometry','max_ir','all',0,0,NULL,NULL,NULL,NULL,NULL,'Nivel digital máximo del infrarrojo.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (172,'images_radiometry','mean_max','all',0,0,NULL,NULL,NULL,NULL,NULL,'Nivel digital máximo de la media de RGB.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (173,'images_radiometry','h_path','all',0,0,NULL,NULL,NULL,NULL,NULL,'Ruta de los histogramas, de las imágenes con los histogramas.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (174,'images_radiometry','thumb_fl','all',0,0,NULL,NULL,NULL,NULL,NULL,'Nombre del fichero de la imagen de baja resolución sin la ruta.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (175,'images_radiometry','h_fl_all','all',0,0,NULL,NULL,NULL,NULL,NULL,'Nombre del fichero del histograma conjunto de todas las bandas sin la ruta.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (176,'images_radiometry','h_file_r','all',0,0,NULL,NULL,NULL,NULL,NULL,'Nombre del fichero del histograma del rojo sin la ruta.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (178,'images_radiometry','h_file_g','all',0,0,NULL,NULL,NULL,NULL,NULL,'Nombre del fichero del histograma del verde sin la ruta.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (179,'images_radiometry','h_file_b','all',0,0,NULL,NULL,NULL,NULL,NULL,'Nombre del fichero del histograma del azul sin la ruta.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (180,'images_radiometry','h_fl_ir','all',0,0,NULL,NULL,NULL,NULL,NULL,'Nombre del fichero del histograma del infrarrojo sin la ruta.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (181,'images_radiometry','h_f_mean','all',0,0,NULL,NULL,NULL,NULL,NULL,'Nombre del fichero del histograma de la media de RGB sin la ruta.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (182,'images_radiometry','ctr_mn_r','all',0,0,NULL,NULL,NULL,NULL,NULL,'Resultado del control del nivel digital 0 (mínimo) para el rojo (1-Cumple, 0-No cumple).',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (183,'images_radiometry','ctr_mn_g','all',0,0,NULL,NULL,NULL,NULL,NULL,'Resultado del control del nivel digital 0 (mínimo) para el verde (1-Cumple, 0-No cumple).',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (184,'images_radiometry','ctr_mn_b','all',0,0,NULL,NULL,NULL,NULL,NULL,'Resultado del control del nivel digital 0 (mínimo) para el azul (1-Cumple, 0-No cumple).',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (185,'images_radiometry','c_mn_ir','all',0,0,NULL,NULL,NULL,NULL,NULL,'Resultado del control del nivel digital 0 (mínimo) para el infrarrojo (1-Cumple, 0-No cumple).',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (186,'images_radiometry','c_mn_rgb','all',0,0,NULL,NULL,NULL,NULL,NULL,'Resultado del control del nivel digital 0 (mínimo) para la media de RGB (1-Cumple, 0-No cumple).',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (187,'images_radiometry','ctr_mx_r','all',0,0,NULL,NULL,NULL,NULL,NULL,'Resultado del control del nivel digital 0 (máximo) para el rojo (1-Cumple, 0-No cumple).',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (188,'images_radiometry','ctr_mx_g','all',0,0,NULL,NULL,NULL,NULL,NULL,'Resultado del control del nivel digital 0 (máximo) para el verde (1-Cumple, 0-No cumple).',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (189,'images_radiometry','ctr_mx_b','all',0,0,NULL,NULL,NULL,NULL,NULL,'Resultado del control del nivel digital 0 (máximo) para el azul (1-Cumple, 0-No cumple).',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (190,'images_radiometry','c_mx_ir','all',0,0,NULL,NULL,NULL,NULL,NULL,'Resultado del control del nivel digital 0 (máximo) para el infrarrojo (1-Cumple, 0-No cumple).',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (191,'images_radiometry','c_mx_rgb','all',0,0,NULL,NULL,NULL,NULL,NULL,'Resultado del control del nivel digital 0 (máximo) para la media de RGB (1-Cumple, 0-No cumple).',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (192,'images_radiometry','pr_time','all',0,0,NULL,NULL,NULL,NULL,NULL,'Momento en que se han calculado las estadísticas radiométricas de la imagen.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (193,'images_radiometry','ctr_r','all',0,0,NULL,NULL,NULL,NULL,NULL,'Control final de la banda del rojo, incumple si incumple el mínimo o el máximo (1-Cumple, 0-No cumple).',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (194,'images_radiometry','ctr_g','all',0,0,NULL,NULL,NULL,NULL,NULL,'Control final de la banda del verde, incumple si incumple el mínimo o el máximo (1-Cumple, 0-No cumple).',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (195,'images_radiometry','ctr_b','all',0,0,NULL,NULL,NULL,NULL,NULL,'Control final de la banda del azul, incumple si incumple el mínimo o el máximo (1-Cumple, 0-No cumple).',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (196,'images_radiometry','ctr_ir','all',0,0,NULL,NULL,NULL,NULL,NULL,'Control final de la banda del infrarrojo, incumple si incumple el mínimo o el máximo (1-Cumple, 0-No cumple).',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (197,'images_radiometry','ctr_full','all',0,0,NULL,NULL,NULL,NULL,NULL,'Control final, incumple si incumple alguna de las bandas (1-Cumple, 0-No cumple).',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (198,'images_radiometry','nd_nv_r','all',0,0,NULL,NULL,NULL,NULL,NULL,'Relación de los niveles digitales de la banda del rojo no existentes en ningún píxel.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (199,'images_radiometry','nd_nv_g','all',0,0,NULL,NULL,NULL,NULL,NULL,'Relación de los niveles digitales de la banda del verde no existentes en ningún píxel.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (200,'images_radiometry','nd_nv_b','all',0,0,NULL,NULL,NULL,NULL,NULL,'Relación de los niveles digitales de la banda del azul no existentes en ningún píxel.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (201,'images_radiometry','nd_nv_ir','all',0,0,NULL,NULL,NULL,NULL,NULL,'Relación de los niveles digitales de la banda del infrarrojo no existentes en ningún píxel.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (202,'images_radiometry','n_nv_r','all',0,0,NULL,NULL,NULL,NULL,NULL,'Número de niveles digitales de la banda del rojo que no están en ningún píxel.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (203,'images_radiometry','n_nv_g','all',0,0,NULL,NULL,NULL,NULL,NULL,'Número de niveles digitales de la banda del verde que no están en ningún píxel.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (204,'images_radiometry','n_nv_b','all',0,0,NULL,NULL,NULL,NULL,NULL,'Número de niveles digitales de la banda del azul que no están en ningún píxel.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (205,'images_radiometry','n_nv_ir','all',0,0,NULL,NULL,NULL,NULL,NULL,'Número de niveles digitales de la banda del infrarrojo que no están en ningún píxel.',NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (206,'flight_block','cod_flight_block','all',1,1,NULL,'comboBox_FlightBlock',NULL,NULL,NULL,'Código de bloque de vuelo','-','-','VARCHAR(50)',NULL,'adimensional',0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (208,'flight_block','cod_camera','all',0,1,'str_cod_camera','comboBox_Camera','Sensor',NULL,NULL,'código de cámara','Project data definition','General data','VARCHAR(100)',NULL,'adimensional',0,NULL,NULL,NULL,NULL,NULL,NULL,0,'20140628: Cambiado Label \"Camera:\" por \"Sensor:\". En comboBox_Camera cambiar el default item \"--- Select camera ---\" por \"--- Select onboard sensor ---\"'),"
        sql += " (209,'flight_block','id_tof','all',0,1,'id_tof / str_id_tof','comboBox_tofPoints','Takeoff point',NULL,NULL,'Identificador del punto de despegue grabado en la tabla c_tof','Project data definition','Spatial Data','NUMERIC(5)','integer','adimensional',0,-1.0,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (210,'flight_block','id_lnd','all',0,1,'id_lnd / str_id_lnd','comboBox_lndPoints','Landing Point',NULL,NULL,'identificador del punto de aterrizaje. Posibles valores: (-1: punto de despegue, 0: último punto, >0 identificador de punto grabado en la tabla c_lnd)','Project data definition','Spatial Data','NUMERIC(5)','integer','adimensional',0,-1.0,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (211,'flight_block','id_firmware','all',0,1,'str_id_firmware','comboBox_Firmware','UAV model',NULL,NULL,'identificador de la versión de firmware','Project data definition','General Data','NUMERIC(5)',NULL,'adimensional',0,-1.0,NULL,NULL,NULL,NULL,NULL,0,'20140628: Cambiado Label \"Firmware version:\" por \"UAV model:\". En comboBox_Firmware cambiar el default item \"--- Select firmware version ---\" por \"--- Select UAV & firmware version ---\"'),"
        sql += " (212,'flight_block','gsd','all',0,1,'gsd','doubleSpinBox_gsd','Ground Sample Distance (GSD)','Ground Sample Distance (GSD)','Dimension of ground represented by each pixel. Por example, an image with a GSD of 1 m, each pixel represents an area of land of 1 meter','Dimensión de terreno representada por cada pixel. Por ejemplo, en una imagen con un GSD de 1 metro, cada píxel representa un área de terreno de un 1 m2','Geometric Navigation parameters','Flight Planning: Geometric Parameters','REAL','float','m',1,0.015,10000.0,0.001,4,0.001,4,0,'Modificado 20140224: qsettings ON. 20150717: Se cambia default_value a 15mm, decimals/precision 4 y single_step a 1mm para ajustarse mejor a las restricciones legales de altura'),"
        sql += " (213,'flight_block','tol_gsd','all',0,1,'gsd_tolerance','doubleSpinBox_tolGsd','Tolerance GSD','Tolerancia GSD','Factor that permits remove the abrup changes in height during flight. While GSD values obtained for the main points are within the values set as tolerance, the device does not change the flight height. At the beginning of each pass is reset again flying height to match the GSD defined theorical value','Factor que permite eliminar los cambios bruscos de altura durante el vuelo. Mientras los valores GSD obtenidos para los puntos principales se encuentren dentro de los valores establecidos como tolerancia, el dispositivo no modifica la altura de vuelo. Al inicio de cada pasada se reajusta de nuevo la altura de vuelo para hacerla coincidir con el valor GSD teórico definido','Geometric Navigation parameters','Flight Planning: Geometric Parameters','REAL','float','%',1,10.0,200.0,0.0,1,1.0,1,0,'Modificado 20140224: qsettings ON. Carlos cambia max_value de 100 a 200'),"
        sql += " (214,'flight_block','foward_overlap','all',0,1,'overlap_fwd','doubleSpinBox_overlapFwd','Forward overlap','Recubrimiento Longitudinal','Overlap between consecutive photogram in the direction in which it moves the Microdron. A default value of 60% is proposed, however, this value can be changed','Solape entre fotogramas consecutivos en la dirección en la que se mueve el Microdron. Se propone un valor por defecto del 60%, no obstante, este valor puede ser modificado.','Geometric Navigation parameters','Flight Planning: Geometric Parameters','REAL','float','%',1,80.0,95.0,0.0,1,1.0,1,0,'Modificado 20140224: qsettings ON. Carlos cambia el default value de 60 a 80.'),"
        sql += " (215,'flight_block','side_overlap','all',0,1,'overlap_side','doubleSpinBox_overlapSide','Side overlap','Recubrimiento Transversal','Spacing between two axes of flight for two adjacent path. A default value of 20% is proposed, however, this value can be changed','Espaciamiento entre dos ejes de vuelo para dos recorridos adyacentes. Se propone un valor por defecto del 20%, no obstante, este valor puede ser modificado.','Geometric Navigation parameters','Flight Planning: Geometric Parameters','REAL','float','%',1,30.0,95.0,0.0,1,1.0,1,0,'Modificado 20140224: qsettings ON. Carlos cambia el default value de 20 a 30.'),"
        sql += " (216,'flight_block','ac_gps','all',0,1,'gps_precision','doubleSpinBox_accGps','GPS','GPS','Accuracy of GPS navigation device Microdron. The program suggests a default value of 3 m. These precision values can influence the coating, especially in low-height flight made.','Precisión del dispositivo GPS de navegación del Microdron. El programa propone por defecto un valor de 3 m. Estos valores de precisión pueden influir en los recubrimientos, sobre todo en vuelos realizados a poca altura','Geometric Navigation parameters','Accuracy of the Camera INS Parameters','REAL','float','m',1,2.0,10.0,0.0,1,0.5,3,0,'Modificado 20140224: qsettings ON: Carlos cambia el default value de 3 a 2. PENDIENTE INCORPORARLO AL CÓDIGO. También se cambia el paso'),"
        sql += " (217,'flight_block','ac_omg','all',0,1,'omega_precision','doubleSpinBox_accOmega','Omega','Omega','Tilt angle of the camera refers to the turn axis parallel to the direction and the image. The influence of this value is greater tan to the rest due to that the stabilization is done by gravity.','Ángulo de inclinación de la cámara referido al eje de giro perpendicular a la dirección Y de la imagen. Este valor está controlado por el servo de la cámara.','Geometric Navigation parameters','Accuracy of the Camera INS Parameters','REAL','float','DEG',1,99.0,99.0,0.0,2,0.1,8,0,'- 20140625: Se fija el min_value a 0. El max_value depende ahora del nº de columnas, resolución geométrica, dirección de vuelo y focal del sensor y de forward y side overlap. El default value será fijado a partir del correspondiente parámetro grabado en el panel de camera.   Por tanto, este parámetro estará deshabilitado hasta que la camera no haya sido seleccionada. - Modificado 20140224: qsettings ON: Carlos cambia el dominio de [360, -360] a [90,-90]. También se cambia el paso.'),"
        sql += " (218,'flight_block','ac_phi','all',0,1,'phi_precision','doubleSpinBox_accPhi','Phi','Phi','Tilt angle of the camera refers to the turn axis parallel to the direction and the image. The influence of this value is greater tan to the rest due to that the stabilization is done by gravity','Ángulo de inclinación de la cámara referido al eje de giro paralelo a la dirección Y de la imagen. La influencia de este ángulo es mayor a la del resto debido a que la estabilización se realiza por gravedad.','Geometric Navigation parameters','Accuracy of the Camera INS Parameters','REAL','float','DEG',1,99.0,99.0,0.0,2,0.1,8,0,'- 20140625: Se fija el min_value a 0. El max_value depende ahora del nº de columnas, resolución geométrica, dirección de vuelo y focal del sensor y de forward y side overlap. El default value será fijado a partir del correspondiente parámetro grabado en el panel de camera.   Por tanto, este parámetro estará deshabilitado hasta que la camera no haya sido seleccionada. - 20140224: qsettings ON. Carlos cambia el dominio de [360, -360] a [90,-90]. También se cambia el paso. También se cambia el default value de 2 a 0,5'),"
        sql += " (219,'flight_block','ac_kap','all',0,1,'kappa_precision','doubleSpinBox_accGps','Kappa','Kappa','Defined rotation angle about the vertical axis of the reference frame. Controlled by Microdron own.','Ángulo de giro definido respecto al eje vertical del marco de referencia. Controlado por el propio Microdron.','Geometric Navigation parameters','Accuracy of the Camera INS Parameters','REAL','float','DEG',1,99.0,10.0,0.0,2,0.1,8,0,'20140625: El default value será establecido a partir de la grabación en el panel del sensor. Este comando aparecerá deshabilitado hasta que no se haya seleccionado la camara. 20140624: cambio el rango de 90,-90 a 10,-10. Modificado 20140224: qsettings ON. Carlos cambia el dominio de [360, -360] a [90,-90]. También se cambia el paso. Modificado en reunión 20140522 se cambia el default value de 0,2 a 0,5.'),"
        sql += " (223,'flight_block','lea','all',0,1,'zone_lineal_magnification','doubleSpinBox_linealEnlargement','Linear enlargement of the area','Ampliación lineal de la zona','Represents the enlargement in meters that we give to the planned area for the flight','Representa la ampliación en metros que le queremos dar a la zona planificada para el vuelo','Project data definition','Spatial Data','REAL','float','m',1,6.0,10000.0,0.0,1,1.0,NULL,0,'Modificado 20140224: qsettings ON'),"
        sql += " (224,'flight_block','dist_prev_point_OBSOLETO_BORRAR','all',0,1,'dist_stop','doubleSpinBox_distStop','Distance for previous point of stop','Distancia para punto previo de parada','Distance in meters, before of the tapping point, at which the Microdones begins to slow down to come to a half','Distancia en metros, anterior al punto de toma, a la que el Microdrones comienza a disminuir su velocidad hasta llegar a detenerse','-','-','REAL','float','m',0,5.0,61.0,0.0,1,1.0,NULL,0,'20140213: email cespadas. … De todos modos, es muy probable que dejemos de necesitar este parámetro. En las versiones antiguas de firmaware lo necesitabamos para evitar que debido a la inercia el dron se pasará del punto, es decir marcaba el inicio de la desaceleración. En las versiones actuales de firmware ya hay un comando específico para que el dron gestione de forma autónoma dicha deceleración. Pero hasta que no lo validemos en un test no puedo confirmar la eliminación de esta variable. Es posible que lleguemos a necesitarlo en los cambios de dirección de vuelo (inicio de cada pasada). Aunque no es un parámetro específico de seguridad lo incluiré en dicha pestaña. Más adelante ya veremos dónde lo dejamos definitivamente.'),"
        sql += " (225,'flight_block','initial_height','all',0,1,'takeoff_height','doubleSpinBox_heightStart','Height at the start of a route','Altura al iniciar la ruta','It is the height at which the flight begins automatically. The MDT is usually defined at ground level. It should consider the possibility of beginning the automatic flight from roofs, building roof, etc. Or even after raising the Dron in manual mode at a certain height. In such cases these values should be reflected in this setting','Es la altura en la que comienza el vuelo en modo automático. El MDT habitualmente está definido a nivel del suelo. Se debe tener en cuenta la posibilidad de iniciar el vuelo automático desde azoteas, tejados de edificios, etc. O incluso después de elevar el Dron en modo manual a una cierta altura. En tales casos dichos valores deberían ser reflejados en esta opción','Geometric Navigation parameters','UAV navigation parameters','REAL','float','m',1,0.0,500.0,-100.0,1,1.0,NULL,0,'Modificado 20140224: qsettings ON. Carlos cambia el valor máximo de 50 a 500. Modificado 20150325: Cambia el default value de 2 a 0. Se cambia en el qsettings.ini. 20150617: Se cambia el min value de 0 a -100 por la posibilidad de despegar en zonas desmontadas  o pozos.'),"
        sql += " (226,'flight_block','end_height','all',0,1,'landing_height','doubleSpinBox_heightEnd','Height at the end of a route','Altura al finalizar la ruta','Point from which the Microdones leaves the descent stretch defined by the “descent speed” parameter. A default value of 30m is proposed. The device stops for 5 seconds and begins to fall in automatic mode at a speed of 0,1 m/s','Punto a partir del cual Microdrones abandona el tramo de descenso definido por el parámetro “velocidad de descenso”. Por defecto se propone un valor de 30 m. El dispositivo se detiene durante 5 segundos y comienza a descender en modo automático a una velocidad de 0,1 m/s','Geometric Navigation parameters','UAV navigation parameters','REAL','float','m',1,30.0,500.0,5.0,1,5.0,NULL,0,'Modificado 20140224: qsettings ON. Carlos cambia el valor máximo de 50 a 500 y el paso de 1 a 5'),"
        sql += " (227,'flight_block','hbl','all',0,1,'height_before_landing','doubleSpinBox_HBL','Height Before Landing (m) #HBL:','Altura previa de aterrizaje','It manages de height of the mission last WP, before starting the vertical landing procedure. Default and minimum value matchs the landing height. Only having into account if the HBL checkBox is disabled','Gestiona la altura del punto final de misión, antes de iniciar el procedimiento de aterrizaje.','Geometric Navigation parameters','Safety parameters / Optional parameters','NUMERIC(5)','float','m',0,-1.0,500.0,-1.0,1,1.0,NULL,0,'20170317: Nota Carlos: Campo actualizado, sustituye al antiguo \"images_per_item\" (actualmente obsoleto).'),"
        sql += " (228,'flight_block','g2d_stfp','all',0,1,NULL,'-','-','-',NULL,'Geometría poligonal 2D de la zona de la huella contra el MDT con estereoscopía','-','-','REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (229,'flight_block','dtm_path','all',0,1,'str_dtm_path','lineEdit_pathDTM','path DTM',NULL,NULL,'ruta del MDT','Project data definition','Spatial Data','TEXT',NULL,'adimensional',0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (230,'camera','cod_camera','all',1,1,'str_cod_camera','lineEdit_code','Code','Código',NULL,'Un proyecto puede incluir varias cámaras en un contenedor indexado por este parámetro, de manera que debe ser único. Es una cadena de caracteres',NULL,'Camera','VARCHAR(100)','String','w/u',0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (231,'camera','trademark','all',0,1,'str_cam_trademark','lineEdit_Trademark','Trademark','Marca',NULL,'Es una cadena de caracteres que almacena la marca de la cámara',NULL,'Camera','VARCHAR(100)','String','w/u',0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (232,'flight_block','id_mounting_type','all',0,0,'cam_id_mounting_type','comboBox_mountingType','Yaw angle',NULL,NULL,NULL,NULL,'Camera','NUMERIC(5)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,'20140628: pasa de la tabla [camera] a la tabla [flight_block]'),"
        sql += " (233,'camera','rows','all',0,0,'rows_digital_sensor','spinBox_rows','Rows','Filas',NULL,'Número entero con las filas del formato de la imagen',NULL,'Camera','NUMERIC(5)','Interger','w/u',0,10000.0,20000.0,100.0,0,1.0,NULL,0,NULL),"
        sql += " (234,'camera','columns','all',0,0,'columns_digital_sensor','spinBox_columns','Columns','Columnas',NULL,'Número entero con las columnas del formato de la imagen',NULL,'Camera','NUMERIC(5)','Interger','w/u',0,5000.0,20000.0,100.0,0,1.0,NULL,0,NULL),"
        sql += " (235,'camera','focal','all',0,0,'focal','doubleSpinBox_focal','Focal','Focal',NULL,'Número en doble precisión con la distancia focal calibrada de la cámara expresada en milímetros',NULL,'Camera','REAL','Float','mm',0,100000.0,500000.0,1000.0,3,1000.0,3,0,NULL),"
        sql += " (236,'camera','geometric_res','all',0,0,'geometric_resolution','doubleSpinBox_resolution','Geometric resolution','Resolución Geométrica',NULL,' Tamaño del píxel. Número en doble precisión con la resolución geométrica de la cámara expresada en milímetros.',NULL,'Camera','REAL','Float','mm',0,10.0,500.0,1.0,3,1.0,4,0,NULL),"
        sql += " (237,'camera','coor_x_ppa','all',0,0,'xppa','doubleSpinBox_xppa','xPPA','xPPA',NULL,'Número en doble precisión con la coordenada X expresada en milímetros del Punto Principal de Autocolimación. Se obtiene del certificado de calibración de la cámara',NULL,'Camera','REAL','Float','mm',0,0.0,1000.0,-1000.0,3,1000.0,3,0,NULL),"
        sql += " (238,'camera','coor_y_ppa','all',0,0,'yppa','doubleSpinBox_yppa','yPPA','yPPA',NULL,'Número en doble precisión con la coordenada Y expresada en milímetros del Punto Principal de Autocolimación. Se obtiene del certificado de calibración de la cámara',NULL,'Camera','REAL','Float','mm',0,0.0,1000.0,-1000.0,3,1000.0,3,0,NULL),"
        sql += " (239,'camera','ang_nadiral_ELIMINADO','all',0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'Camera','REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,'20140628: Se elimina este campo por indicación de Carlos'),"
        sql += " (240,'camera','ang_kappa_ELIMINADO','all',0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'Camera','REAL',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,'20140628: Se elimina este campo por indicación de Carlos'),"
        sql += " (241,'project','id_project','all',1,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'NUMERIC(5)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (242,'project','path_project','all',0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'VARCHAR(50)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (243,'project','nemo','all',0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'VARCHAR(255)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (244,'project','title','all',0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'VARCHAR(255)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (245,'project','author','all',0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'VARCHAR(255)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (246,'project','path_sqlite_db','all',0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'VARCHAR(50)',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (247,'project','crs_code','all',0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'INTEGER',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (248,'flight_block','id_fb_type','all',0,1,'id_fb_type','comboBox_FlightType','Aerial mission','Tipo de vuelo','Type of photogrammetric flight for planning: 1.-Linear route. 2.-Polygonal area. 3.-Oblique flight for mapping steep slope areas','Tipo de vuelo fotogramétrico a planificar:     1.-Trazado lineal con ancho de banda. 2.-Zona poligonal. 3.Vuelo oblicuo para zonas de fuerte pendiente.','Project data definition','General Data','NUMERIC(5)','integer','adimensional',1,-1.0,NULL,NULL,NULL,NULL,NULL,0,'20140628: Cambiado Label \"Flight type:\" por \"Aerial mission:\". En comboBox_FlightType cambiar el default item \"--- Select type of flight ---\" por \"--- Select photogrammetric mission type ---\" 20140225. Nuevo parámetro añadido .Referenciado a la tabla flight_block_type. Pendiente desarrollo funcionalidad'),"
        sql += " (250,'flight_block','id_trajectory_type','all',0,1,'id_trajectory_type','comboBox_trajectoryType','UAV trajectory mode','Tipo de trayectoria del UAV','Trajectory type between WPs, options: 1.- Diagonal all WP (warning! Collision risk with obstacles in TOF and LND operations).  2.- DV / DH all WP.  3.- Diagonal except TOF.  4.- Diagonal except TOF&LND. 5.- Diagonal except LND.','Define el tipo de trayectoria entre Waypoints, opciones:  1.- Diagonal siempre (ojo riesgo de colisión con obstáculos en despegue y aterrizaje). 2.- DeltaV / DeltaH todos los WP.    3.- Diagonal excepto trayectoria de despegue.   4.- Diagonal excepto despegue y aterrizaje.  5.- Diagonal excepto aterrizaje','Geometric Navigation parameters','UAV navigation parameters','NUMERIC(5)','integer','adimensional',1,-1.0,NULL,NULL,NULL,NULL,NULL,0,'Nuevo parámetro añadido 20140225. Notas Carlos: En el script clásico de navegación la posición planimétrica de los Waypoints se definía mediante el comando PMH y los desplazamientos verticales mediante el comando PMV (no era posible realizar desplazamientos diagonales). En las nuevas versiones de firmware es posible realizar ambos movimientos combinados (diagonal) lo que permite ahorrar energía y por ende aumentar la autonomía. Esto se realiza mediante el comando PMC (Position Move Combined)'),"
        sql += " (251,'flight_block','smooth_v','all',0,1,'smooth_v','checkBox_SmoothV','Smooth trajectory: Vertical','Suavizar trayectoria: Vertical','When enabled, it smooths the calculated rough height profile, by writing in the script navigation a b-spline command','Cuando está activado, suaviza los quiebros del pefil vertical calculado, mediante el envío de un comando de navegación suavizada de tipo b-spline','Geometric Navigation parameters','UAV navigation parameters','INTEGER','integer',NULL,0,-1.0,1.0,-1.0,0,'NULL',1,0,'20170320: Nuevo parámetro para escribir comando para suavizar trayectoria vertical. Antiguo campo reservado a \"wpb\" ahora obsoleto eliminado'),"
        sql += " (252,'flight_block','shot_interval','all',0,1,'shot_interval','doubleSpinBox_shotInterval','Shot interval (s.)','Intervalo de disparos (s)','it controls the interval between photo shots','Controla el tiempo entre disparos consecutivos de fotos. TIM, tiempo de retardo para disparo de fotos, en WP sin NBK TIM = al valor introducido en el panel. En WP con NBK no se incluye este comando','Geometric Navigation parameters','Imaging acquisition parameters','REAL','float','s',1,5.0,60.0,0.0,1,1.0,1,0,'Controla la espera en el WP para estabilizar el disparo.  // 20170412: modificado min_value = 0.0 s  (anterior 0.1 s)'),"
        sql += " (253,'flight_block','phi_angle','all',0,1,'phi_angle','doubleSpinBox_phiAngle','Phi angle (DEG)','Ángulo Phi (DEG)','Parameter to establish the sensor Roll angle (around the gimbal Y axis).  Domain [-25, 25]deg CCW (positive: to the left sight // negative: to the right sight). Nadiral shots: Roll=0. ','Traducir','Geometric Navigation parameters','Imaging acquisition parameters','REAL','float','DEG',0,0.0,45.0,-45.0,2,5.0,2,0,'Nuevo parámetro añadido 20140228: El rango max-min dependerá del tipo de servo montado y del valor offset de calibración del soporte. Los valores indicados son aproximados. Controla el ángulo phi de la cámara (0=nadiral, rango= -45º a 45º). Nota(*) Los rangos pueden variar dependiendo del sistema gimbal utilizado.'),"
        sql += " (254,'flight_block','omega_angle','all',0,1,'omega_angle','doubleSpinBox_omegaAngle','Omega angle (DEG)','Ángulo Omega (DEG)','Parameter to establish the sensor Tilt angle (around the gimbal X axis).  Domain [-20, 70]deg CCW (positive: forward sight // negative: backward sight). Nadiral shots: Pitch=0. ','Traducir','Geometric Navigation parameters','Imaging acquisition parameters','REAL','float','DEG',0,0.0,70.0,-20.0,2,5.0,2,0,'Nuevo parámetro añadido 20140228:  El rango max-min dependerá del tipo de servo montado y del valor offset de calibración del soporte. Los valores indicados son aproximados. Controla el ángulo omega de la cámara (0=nadiral 90=horizontal). Nota(*) Los rangos pueden variar dependiendo del sistema gimbal utilizado. - 20150412: El criterio angular de microdrones para omega es considerar el nadir como omega=90 y la visual horizontal como omega=0'),"
        sql += " (255,'flight_block','id_erc','all',0,1,'id_erc','comboBox_ERC','Emergency Radio Control  #ERC','Emergency Radio Control  #ERC','Security parameter that defines the action to perform in case that the drone loses the RC signal:  0.- Descend slowly at current position to touch ground.  1.- The drone stops, keeping position and altitude until low battery level.  2.- The drone continues the Waypoint route according the planning.  3.-It starts the \"Go Home\" procedure.','Parámetro de seguridad que establece la acción a realizar en caso que el dron pierda la señal del control remoto:    0.- Desciende lentamente hasta llegar al suelo.   1.- Se detiene y permanece estático manteniendo posición y altura, hasta que el nivel de batería sea bajo.  2.-Continúa la ruta planificada según lo previsto.  3.-Inicia el procedimiento de vuelta a casa. 20150325: se añade la 4 opción al comboBox y el valor ahora es el introducido en el diálogo, no la constante c.CONST_MICRODRON_CMD_ERC_DEFAULT_VALUE','Security parameters','Setting security actions','NUMERIC(5)','integer','adimensional',1,NULL,NULL,NULL,NULL,NULL,NULL,0,'Nuevo parámetro añadido 20140228. Los valores con -1 deberían incluir default value = null. Después de hacerlo creo que hubiera sido mejor gestionarlo con comboBox'),"
        sql += " (256,'flight_block','id_eal','all',0,1,'id_eal','comboBox_EAL','Emergency Accumul. Low  #EAL','Emergency Accumul. Low  #EAL','Security parameter to establish the action to perform in case of low battery level:  0.- Descend slowly at current position to touch ground.  1.- The drone stops, keeping position and altitude until low battery level.  2.- The drone continues the Waypoint route according the planning.  3.-It starts the \"Go Home\" procedure.','Parámetro de seguridad que establece la acción a realizar en caso de alcanzar nivel bajo de batería:    0.- Desciende lentamente hasta llegar al suelo.   1.- Se detiene y permanece estático manteniendo posición y altura, hasta que el nivel de batería sea bajo.  2.-Continúa la ruta planificada según lo previsto.  3.-Inicia el procedimiento de vuelta a casa.','Security parameters','Setting security actions','NUMERIC(5)','integer','adimensional',0,NULL,NULL,NULL,NULL,NULL,NULL,0,'Nuevo parámetro añadido 20140228. Los valores con -1 deberían incluir default value = null. Después de hacerlo creo que hubiera sido mejor gestionarlo con comboBox. DUDA DAMI: ¿CUÁL SERÍA EL VALOR POR DEFECTO?. 20150325: se añade la 4 opción al comboBox y el valor ahora es el introducido en el diálogo, no la constante c.CONST_MICRODRON_CMD_EAL_DEFAULT_VALUE'),"
        sql += " (257,'flight_block','id_egi','all',0,1,'id_egi','comboBox_EGI','Emergency GPS Invalid  #EGI','Emergency GPS Invalid  #EGI','Security parameter to establish the action to perform in case of GPS loss:  0.- Descend slowly while it is dragged by the wind to touch ground.  1.-Keep altitude while it is dragged by the wind.','Parámetro de seguridad que establece la acción a realizar en caso de pérdida de GPS:    0.- Desciende lentamente mientras es arrastrado por el viento hasta llegar al suelo.   1.- Mantiene la altitud mientras es arrastrado por el viento.','Security parameters','Setting security actions','NUMERIC(5)','integer','adimensional',0,NULL,NULL,NULL,NULL,NULL,NULL,0,'Nuevo parámetro añadido 20140228. Los valores con -1 deberían incluir default value = null. Después de hacerlo creo que hubiera sido mejor gestionarlo con comboBox. DUDA DAMI: ¿CUÁL SERÍA EL VALOR POR DEFECTO?'),"
        sql += " (258,'flight_block','id_shp','all',0,1,'id_shp','comboBox_SHP','Select Homing Position #SHP','Select Homing Position #SHP','Security parameter to establish the \"Home\" position as a secure point where the drone leads in case of emergency. Options:  1.-Match the landing point of the planned route.  2.-Match the take-off point of the planned route.  3.-Other different spot (it requires select a point)','Parámetro de seguridad para establecer la posición \"Home\" o punto seguro donde el dron se dirigirá en caso de situación de emergencia, opciones:  1.-Punto previsto para el aterrizaje en la ruta programada.  2.-Punto previsto de despegue en la ruta programada.  3.-Otra posición definida por el usuario (requiere selección de punto)','Security parameters','Setting parameters && special tasks','NUMERIC(5)','integer','adimensional',0,1.0,NULL,NULL,NULL,NULL,NULL,0,'Nuevo parámetro añadido 20140228: tal vez sea mejor gestionarlos como comboBox'),"
        sql += " (259,'flight_block','ssh','all',0,1,'ssh','doubleSpinBox_SSH',' Setting Secure Height (m) #SSH',' Setting Secure Height (m) #SSH','Security parameter to establish the minimum height of flight (in meters), once the Homing action is started. Its objective is to avoid possible collision with obstacles found in the Home drone path.','Parámetro de seguridad que establece la altura de vuelo mínima en metros, una vez se inicia la acción \"Go Home\". Su objetivo es evitar que el dron colisione con algún obstáculo en su recorrido de vuelta a casa.','Security parameters','Setting parameters && special tasks','REAL','float','m',0,50.0,100.0,20.0,2,5.0,2,0,'Nuevo parámetro añadido 20140228: tal vez sea mejor gestionarlos como comboBox'),"
        sql += " (260,'flight_block','gpa','all',0,1,'gpa','doubleSpinBox_GPA',' General Pos. Accuracy (m) #GPA',' General Pos. Accuracy (m) #GPA:','Parameter to establish the tolerance position (in meters), to reach the Waypoints of the planned route.','Parámetro que establece la tolerancia posicional (en metros), para que el dron alcance los Waypoint de la ruta planificada.','Security parameters','Setting parameters && special tasks','REAL','float','m',0,2.0,10.0,1.0,1,1.0,1,0,'Nuevo parámetro añadido 20140228: tal vez sea mejor gestionarlos como comboBox'),"
        sql += " (261,'flight_block','fit_axis','all',0,1,'fit_axis','checkBox_fitAxis','Trajectory matchs the axis geometry ','Trajectoria ajustada a la geometría del eje','When checked, it calculates a trajectory that matches exactly the geometry of the selected axis in Lineal Missions, improving the flight efficiency. But in case of small forward overlap or sharp changes of direction, the stereoscopic overlap could not cover the desired buffer.','Si está marcado, calcula una trayectoria que ajusta exactamente con la geometría del eje seleccionado (Mission Lineal), mejorando la eficiencia del vuelo. Precaución: En caso de bajo recubrimiento longitudinal o cambios bruscos de dirección, el recubrimiento estereoscópico del buffer deseado podría verse comprometido.','Geometric Navigation parameters','UAV navigation parameters','INTEGER','integer','adimensional',0,-1.0,1.0,-1.0,0,NULL,'NULL',0,'20170403: Nuevo parámetro para hacer coincidir la mision lineal calculada con el eje seleccionado. Antiguo campo reservado a \"WAE\" ahora obsoleto eliminado'),"
        sql += " (262,'flight_block','was','all',0,0,'was','doubleSpinBox_WAS','Waypoint AutoStart (m) #WAS','Waypoint AutoStart (m) #WAS','Special command for the drone reach a specific height (in meters) before start the WP route.','Comando especial para que el dron  alcance una altura (en metros) determinada antes de iniciar la ruta automática planificada','Security parameters','Setting parameters && special tasks -> Optional parameters','REAL','float','m',0,50.0,500.0,5.0,1,1.0,1,0,'Si el checkbox se desactiva, el valor de este parámetro se fija en -1. Inicialmente activado. Nuevo parámetro añadido 20140228:  Este parámetro no es obligatorio, se podría controlar con un checkbox.  Los objetos WAS y WAL el usuario podría decidir no incluirlos. Este parámetro no es imprescindible.  20150103: Carlos:  introducir en la fórmula de cálculo del comando PMV (altura),   creo que en la versión de C++ no se tenía en cuenta y como siempre  era un valor muy bajo no nos habíamos dado cuenta (lo volveré a revisar) 20150325: max_value pasa de 20 a 100. 20150325: Se sustituye la palabra del comando c.CONST_MICRODRON_CMD_WAS x  c.CONST_MICRODRON_CMD_PMV  y la constante c.CONST_MICRODRON_CMD_WAS_DEFAULT_VALUE es ahora el valor introducido en el panel. 20150617: Se cambian los valores defualt, min y max de (10,1,100) a (50,5,120)'),"
        sql += " (263,'flight_block','wal','all',0,0,'wal','doubleSpinBox_WAL','WP AutoLanding (m/s) #WAL','WP AutoLanding (m/s) #WAL','Special command for the drone starts a protocol of autolanding at the given vertical speed (m/s), once the the WP route has ended.','Comando especial para que el dron inicie un auto-aterrizaje a la velocidad de descenso dada  (m/s) una vez haya finalizado la ruta planificada','Security parameters','Setting parameters && special tasks -> Optional parameters','REAL','float',NULL,0,0.5,0.5,0.5,1,0.1,1,0,'Si el checkbox se desactiva, el valor de este parámetro se fija en -1. Inicialmente activado. Nuevo parámetro añadido 20140228:  Este parámetro no es obligatorio, se podría controlar con un checkbox.  Los objetos WAS y WAL el usuario podría decidir no incluirlos. Este parámetro no es imprescindible.'),"
        sql += " (264,'flight_block','id_nbk','all',0,1,'id_nbk','comboBox_NBK','No Braking','Sin frenado en WPs','NBK command manages wether the drone stop or not in the Waypoints.   0.- OFF (slow down according with the WPB factor and finally the drone stops the specified time).  1.- Enabled, the drone doesn''t stop in the WP (only works in straight trajectories)','Determina si el dron se detiene o no en los Waypoints. 0.- OFF (desacelera según valor WPB y se detiene el tiempo especificado).  1.- Activado, no frena a su paso por los WP (sólo en trayectorias sensiblemente rectas).','Geometric Navigation parameters','Imaging acquisition parameters','NUMERIC(5)','integer','adimensional',1,NULL,NULL,NULL,NULL,NULL,NULL,0,'Nuevo parámetro añadido 20140225. DUDA DAMI ¿ALGÚN VALOR POR DEFECTO?'),"
        sql += " (267,'flight_block','id_process_st','all',0,1,'id_process_status_fb','-','-','-',NULL,'Indica el estado de procesamiento. Posibles valores: [0] - no procesado [1] - procesado',NULL,'-','INTEGER','integer','-',0,0.0,NULL,NULL,NULL,NULL,NULL,0,NULL),"
        sql += " (268,'flight_block','npsf','all',0,1,NULL,'comboBox_numberOfPointsInSideFrame','Points by footprint side',NULL,'Number of points on each side of the picture frame is divided to generate their mark against the DTM','Número de puntos en que se divide cada lado del marco de la imagen para generar su huella contra el MDT','Geometric Navigation parameters','Flight Planning: Geometric Parameters',NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,0,'3,5,7,9,11,,,,,,49'),"
        sql += " (269,'flight_block','offset_omega','all',0,0,'str_offset_omega','doubleSpinBox_offsetOmega','omega (DEG)','omega (DEG)',NULL,NULL,NULL,'Mount offsets','REAL',NULL,'DEG',1,0.0,10.0,-10.0,1,1.0,NULL,0,'20180329: Se fijan los valores min y max: (-10 ,10 )'),"
        sql += " (270,'flight_block','offset_phi','all',0,0,'str_offset_phi','doubleSpinBox_offsetPhi','phi (DEG)','phi (DEG)',NULL,NULL,NULL,'Mount offsets','REAL',NULL,'DEG',1,0.0,10.0,-10.0,1,1.0,NULL,0,'20180329: Se fijan los valores min y max: (-10 ,10 )'),"
        sql += " (271,'flight_block','offset_kappa','all',0,0,'str_offset_kappa','doubleSpinBox_offsetKappa','kappa(DEG)','kappa(DEG)',NULL,NULL,NULL,'Mount offsets','REAL',NULL,'DEG',1,0.0,10.0,-10.0,1,1.0,NULL,0,'20140628: pasa de la tabla [camera] a la tabla [flight_block]'),"
        sql += " (272,'flight_block','id_type_gimbel_mount','all',0,0,NULL,'comboBox_typeGimbalMount','   Type of gimbal mount',NULL,NULL,NULL,NULL,NULL,'NUMERIC(5)','integer','adimensional',0,-1.0,NULL,NULL,NULL,NULL,NULL,0,'20140628: nuevo parámetro introducido por Carlos'),"
        sql += " (273,'flight_block','flight_duration','all',0,0,NULL,'timeEdit','Estimated longest flight:',NULL,NULL,'Duración estimada del vuelo más largo',NULL,'Processing results','REAL',NULL,'segundos',0,NULL,NULL,NULL,NULL,NULL,NULL,0,'20140719: Creado para que persista esta información en cada bloque de vuelo'),"
        sql += " (279,'flight_block','ascent_speed','Eiffage_UAV_firmware_1',0,1,'ascent_speed','doubleSpinBox_speedAsc','Ascent speed','Velocidad ascenso','Maximum Asccent Speed for the mission. Maximum allowed value is 2.5 m/s (Carabo S3) ???','Máxima Velocidad de Ascenso para la misión. Valor Máximo admitido para Carabo S3 = 2.5 m/s','Geometric Navigation parameters','UAV navigation parameters','REAL','float','m/s',0,3.0,3.0,0.1,1,0.5,'NULL',0,'Datos sin verificar: DIEGO'),"
        sql += " (280,'flight_block','cruise_speed','Eiffage_UAV_firmware_1',0,1,'cruising_speed','doubleSpinBox_speedCruising','Cruising speed','Velocidad crucero','Maximum Ground Speed for this missión. Maximum allowed value is 9 m/s (Carabo S3) ???','Máxima Velocidad en Tierra para la misión. Valor Máximor admitido para Carabo S3 = 9 m/s ???','Geometric Navigation parameters','UAV navigation parameters','REAL','float','m/s',0,6.0,9.0,0.1,1,0.5,'NULL',0,'Datos sin verificar: DIEGO'),"
        sql += " (281,'flight_block','descent_speed','Eiffage_UAV_firmware_1',0,1,'decrease_speed','doubleSpinBox_speedDes','Descent speed','Velocidad descenso','Maximum Descent Speed for the mission. Maximum allowed value is 1.5 m/s (Carabo S3) ???','Máxima Velocidad de Descenso para la misión. Valor Máximo admitido para Carabo S3 = 1.5 m/s','Geometric Navigation parameters','UAV navigation parameters','REAL','float','m/s',0,2.0,9.0,0.1,1,0.5,'NULL',0,'Datos sin verificar: DIEGO'),"
        sql += " (282,'flight_block','av_height_obj','all',0,0,'average_height_object','doubleSpinBox_averageHeightObject','Average Height Object','Altura media del objeto',NULL,NULL,'Geometric Navigation','Spatial data','FLOAT','float','m',0,0.0,80.0,0.0,1,0.1,NULL,'FALSE','20190916: Alta nuevo parámetro');"
        sqls.append(sql)
        sql = "INSERT INTO \"firmware\" (\"id_firmware\",\"des_firmware\",\"is_obsolete\") VALUES (1,'FC2_6_Rev_090617',1),"
        sql += " (2,'FC2_7_Rev_100218',1),"
        sql += " (3,'Eiffage_UAV_firmware_1',0),"
        sql += " (4,'md4_1000_FNC_4.2',1),"
        sql += " (5,'md4_1000_FC2_8_NC26',1),"
        sql += " (6,'md4_200_FC2_8_NC26',1);"
        sqls.append(sql)
        sql = "INSERT INTO \"lnk_battery_firmware\" (\"id_lnk_battery_firmware\",\"id_battery\",\"id_firmware\",\"is_active\") VALUES (8,1,5,0),"
        sql += " (9,2,5,1),"
        sql += " (10,3,5,0),"
        sql += " (11,4,6,0),"
        sql += " (12,5,6,1),"
        sql += " (13,1,4,1),"
        sql += " (14,2,4,0),"
        sql += " (15,3,4,0),"
        sql += " (16,7,3,1),"
        sql += " (17,6,3,0);"
        sqls.append(sql)
        sql = "INSERT INTO \"camera\" (\"cod_camera\",\"trademark\",\"rows\",\"columns\",\"focal\",\"geometric_res\",\"coor_x_ppa\",\"coor_y_ppa\",\"order_combo\") VALUES ('ADCLite_CREA','Canon',1536,2048,8.0,0.0032,0.0,0.0,8),"
        sql += " ('EP1_99','olympus',3024,4032,16.82,0.0043,0.0,0.0,9),"
        sql += " ('ILCE-5000','Sony',3632,5456,20.0,0.00425,0.0,0.0,6),"
        sql += " ('ILCE-7R','Sony',4912,7360,36.0,0.00485,0.0,0.0,1),"
        sql += " ('Ixus115HS','Canon',3000,4000,4.941,0.0015,0.0,0.0,10),"
        sql += " ('Ixus115HS_Z2','Canon',3000,4000,5.944,0.0015,0.0,0.0,7),"
        sql += " ('OptioA40','Pentax',3000,4000,7.941,0.0018,0.0,0.0,11),"
        sql += " ('ph320','flir',620,440,19.0,0.038,0.0,0.0,12),"
        sql += " ('ILCE_5100 - f.20mm','Sony',4000,6000,20.0,0.00391,0.0,0.0,3),"
        sql += " ('ILCE_5100 - f.16mm','Sony',4000,6000,16.0,0.00391,0.0,0.0,2),"
        sql += " ('DSC_RX1RM2 - f.36mm','Sony',5304,7952,35.0,0.00452,0.0,0.0,4),"
        sql += " ('Sequoia','Parrot',960,1280,3.98,0.00375,0.0,0.0,5),"
        sql += " ('Yi_16MP - f.3mm','Xiaomi',3456,4608,2.75,0.00134,0.0,0.0,13),"
        sql += " ('ILCE_5100(xf) - f.20mm','Sony',6000,4000,20.0,0.00391,0.0,0.0,14);"
        sqls.append(sql)
        sql = "INSERT INTO \"flight_block_erc\" (\"id_erc\",\"def_erc\") VALUES (0,'Descend slowly at current position'),"
        sql += " (2,'Continue the Waypoint route'),"
        sql += " (3,'Go to Home position and landing'),"
        sql += " (4,'Return by the Waypoint path');"
        sqls.append(sql)
        sql = "INSERT INTO \"flight_block_eal\" (\"id_eal\",\"def_eal\") VALUES (0,'Descend slowly at current position'),"
        sql += " (1,'Hover at the current position'),"
        sql += " (2,'Continue the Waypoint route'),"
        sql += " (3,'Go to Home position and landing'),"
        sql += " (4,'Return by the Waypoint path');"
        sqls.append(sql)
        sql = "INSERT INTO \"battery\" (\"id_battery\",\"des_battery\",\"charge\",\"duration_battery\",\"per_reduction\",\"per_confidence\",\"is_active\") VALUES (1,'22.2V_6S2P_14600_LiPo',14600,3000,1.0,0.7,1),"
        sql += " (2,'22.2V_6S2P_13000_LiPo',13000,2700,1.0,0.7,1),"
        sql += " (3,'22.2V_6S2P_12200_LiPo',12200,2400,1.0,0.7,1),"
        sql += " (4,'14.8V_4S1P_2500_LiPo',2500,1400,1.0,0.7,1),"
        sql += " (5,'14.8V_4S1P_2750_LiPo',2750,1700,1.0,0.7,1),"
        sql += " (6,'14.8V_4S1P_5200_LiPo',5200,1500,1.0,0.7,1),"
        sql += " (7,'22.8V_6S1P_5200_LiHv',5200,2200,1.0,0.95,1);"
        sqls.append(sql)
        sql = "INSERT INTO \"flight_block_type_gimbal_mount\" (\"id_type_gimbal_mount\",\"def_type_gimbal_mount\") VALUES (1,'1.- Brushed, 2 axis gimbaled (pitch & roll)'),"
        sql += " (2,'2.- Brushless, 2 axis  gimbaled (pitch & roll)'),"
        sql += " (3,'3.- Brushed, pitch gimbaled / Roll free'),"
        sql += " (4,'4.- Brushed, pitch gimbaled / Roll UAV fixed');"
        sqls.append(sql)
        sql = "INSERT INTO \"flight_block_mounting_type\" (\"id_mounting_type\",\"def_mounting_type\") VALUES (3,'+Y axis forward (0 deg.)');"
        sqls.append(sql)
        sql = "INSERT INTO \"flight_block_mounting_type\" (\"id_mounting_type\",\"def_mounting_type\") VALUES (1,'+X axis forward (-90 deg.)');"
        sqls.append(sql)
        sql = "INSERT INTO \"flight_block_type\" (\"id_fb_type\",\"def_fb_type\") VALUES (1,'Polygonal area from linear route'),"
        sql += " (2,'Zonal area'),"
        sql += " (3,'Prepare flight blocks from lineal axis segmentation');"
        sqls.append(sql)
        sql = "INSERT INTO \"flight_block_nbk\" (\"id_nbk\",\"des_nbk\") VALUES (0,'0.- Yes (obsolete)'),"
        sql += " (1,'1.- Disabled (default)');"
        sqls.append(sql)
        sql = "INSERT INTO \"flight_block_shp\" (\"id_shp\",\"def_shp\") VALUES (1,'Landing Point (default)'),"
        sql += " (2,'Take-off Point'),"
        sql += " (3,'Other spot');"
        sqls.append(sql)
        sql = "INSERT INTO \"flight_block_egi\" (\"id_egi\",\"def_egi\") VALUES (1,'Keep altitude dragged by the wind');"
        sqls.append(sql)
        sql = "INSERT INTO \"flight_block_trajectory_type\" (\"id_trajectory_type\",\"def_trajectory_type\") VALUES (1,'1.-GSD & tolerance based'),"
        sql += " (2,'2.-Simplified GSD based'),"
        sql += " (3,'3.-Averaged Horizontal Strip'),"
        sql += " (4,'4.-Constant Slope Strip'),"
        sql += " (5,'5.-Best Constant Slope Strip');"
        sqls.append(sql)
        sql = "INSERT INTO \"srs_prj\" (\"srs_id\",\"description\",\"use_prj\") VALUES (2102,'ETRS89 / UTM zone 29N',1),"
        sql += " (2103,'ETRS89 / UTM zone 30N',1),"
        sql += " (2104,'ETRS89 / UTM zone 31N',1),"
        sql += " (3085,'WGS 84 / UTM zone 1N',1),"
        sql += " (3086,'WGS 84 / UTM zone 2N',1),"
        sql += " (3087,'WGS 84 / UTM zone 3N',1),"
        sql += " (3088,'WGS 84 / UTM zone 4N',1),"
        sql += " (3089,'WGS 84 / UTM zone 5N',1),"
        sql += " (3090,'WGS 84 / UTM zone 6N',1),"
        sql += " (3091,'WGS 84 / UTM zone 7N',1),"
        sql += " (3092,'WGS 84 / UTM zone 8N',1),"
        sql += " (3093,'WGS 84 / UTM zone 9N',1),"
        sql += " (3094,'WGS 84 / UTM zone 10N',1),"
        sql += " (3095,'WGS 84 / UTM zone 11N',1),"
        sql += " (3096,'WGS 84 / UTM zone 12N',1),"
        sql += " (3097,'WGS 84 / UTM zone 13N',1),"
        sql += " (3098,'WGS 84 / UTM zone 14N',1),"
        sql += " (3099,'WGS 84 / UTM zone 15N',1),"
        sql += " (3100,'WGS 84 / UTM zone 16N',1),"
        sql += " (3101,'WGS 84 / UTM zone 17N',1),"
        sql += " (3102,'WGS 84 / UTM zone 18N',1),"
        sql += " (3103,'WGS 84 / UTM zone 19N',1),"
        sql += " (3104,'WGS 84 / UTM zone 20N',1),"
        sql += " (3105,'WGS 84 / UTM zone 21N',1),"
        sql += " (3106,'WGS 84 / UTM zone 22N',1),"
        sql += " (3107,'WGS 84 / UTM zone 23N',1),"
        sql += " (3108,'WGS 84 / UTM zone 24N',1),"
        sql += " (3109,'WGS 84 / UTM zone 25N',1),"
        sql += " (3110,'WGS 84 / UTM zone 26N',1),"
        sql += " (3111,'WGS 84 / UTM zone 27N',1),"
        sql += " (3112,'WGS 84 / UTM zone 28N',1),"
        sql += " (3113,'WGS 84 / UTM zone 29N',1),"
        sql += " (3114,'WGS 84 / UTM zone 30N',1),"
        sql += " (3115,'WGS 84 / UTM zone 31N',1),"
        sql += " (3116,'WGS 84 / UTM zone 32N',1),"
        sql += " (3117,'WGS 84 / UTM zone 33N',1),"
        sql += " (3118,'WGS 84 / UTM zone 34N',1),"
        sql += " (3119,'WGS 84 / UTM zone 35N',1),"
        sql += " (3120,'WGS 84 / UTM zone 36N',1),"
        sql += " (3121,'WGS 84 / UTM zone 37N',1),"
        sql += " (3122,'WGS 84 / UTM zone 38N',1),"
        sql += " (3123,'WGS 84 / UTM zone 39N',1),"
        sql += " (3124,'WGS 84 / UTM zone 40N',1),"
        sql += " (3125,'WGS 84 / UTM zone 41N',1),"
        sql += " (3126,'WGS 84 / UTM zone 42N',1),"
        sql += " (3127,'WGS 84 / UTM zone 43N',1),"
        sql += " (3128,'WGS 84 / UTM zone 44N',1),"
        sql += " (3129,'WGS 84 / UTM zone 45N',1),"
        sql += " (3130,'WGS 84 / UTM zone 46N',1),"
        sql += " (3131,'WGS 84 / UTM zone 47N',1),"
        sql += " (3132,'WGS 84 / UTM zone 48N',1),"
        sql += " (3133,'WGS 84 / UTM zone 49N',1),"
        sql += " (3134,'WGS 84 / UTM zone 50N',1),"
        sql += " (3135,'WGS 84 / UTM zone 51N',1),"
        sql += " (3136,'WGS 84 / UTM zone 52N',1),"
        sql += " (3137,'WGS 84 / UTM zone 53N',1),"
        sql += " (3138,'WGS 84 / UTM zone 54N',1),"
        sql += " (3139,'WGS 84 / UTM zone 55N',1),"
        sql += " (3140,'WGS 84 / UTM zone 56N',1),"
        sql += " (3141,'WGS 84 / UTM zone 57N',1),"
        sql += " (3142,'WGS 84 / UTM zone 58N',1),"
        sql += " (3143,'WGS 84 / UTM zone 59N',1),"
        sql += " (3144,'WGS 84 / UTM zone 60N',1),"
        sql += " (3151,'WGS 84 / UTM zone 1S',1),"
        sql += " (3152,'WGS 84 / UTM zone 2S',1),"
        sql += " (3153,'WGS 84 / UTM zone 3S',1),"
        sql += " (3154,'WGS 84 / UTM zone 4S',1),"
        sql += " (3155,'WGS 84 / UTM zone 5S',1),"
        sql += " (3156,'WGS 84 / UTM zone 6S',1),"
        sql += " (3157,'WGS 84 / UTM zone 7S',1),"
        sql += " (3158,'WGS 84 / UTM zone 8S',1),"
        sql += " (3159,'WGS 84 / UTM zone 9S',1),"
        sql += " (3160,'WGS 84 / UTM zone 10S',1),"
        sql += " (3161,'WGS 84 / UTM zone 11S',1),"
        sql += " (3162,'WGS 84 / UTM zone 12S',1),"
        sql += " (3163,'WGS 84 / UTM zone 13S',1),"
        sql += " (3164,'WGS 84 / UTM zone 14S',1),"
        sql += " (3165,'WGS 84 / UTM zone 15S',1),"
        sql += " (3166,'WGS 84 / UTM zone 16S',1),"
        sql += " (3167,'WGS 84 / UTM zone 17S',1),"
        sql += " (3168,'WGS 84 / UTM zone 18S',1),"
        sql += " (3169,'WGS 84 / UTM zone 19S',1),"
        sql += " (3170,'WGS 84 / UTM zone 20S',1),"
        sql += " (3171,'WGS 84 / UTM zone 21S',1),"
        sql += " (3172,'WGS 84 / UTM zone 22S',1),"
        sql += " (3173,'WGS 84 / UTM zone 23S',1),"
        sql += " (3174,'WGS 84 / UTM zone 24S',1),"
        sql += " (3175,'WGS 84 / UTM zone 25S',1),"
        sql += " (3176,'WGS 84 / UTM zone 26S',1),"
        sql += " (3177,'WGS 84 / UTM zone 27S',1),"
        sql += " (3178,'WGS 84 / UTM zone 28S',1),"
        sql += " (3179,'WGS 84 / UTM zone 29S',1),"
        sql += " (3180,'WGS 84 / UTM zone 30S',1),"
        sql += " (3181,'WGS 84 / UTM zone 31S',1),"
        sql += " (3182,'WGS 84 / UTM zone 32S',1),"
        sql += " (3183,'WGS 84 / UTM zone 33S',1),"
        sql += " (3184,'WGS 84 / UTM zone 34S',1),"
        sql += " (3185,'WGS 84 / UTM zone 35S',1),"
        sql += " (3186,'WGS 84 / UTM zone 36S',1),"
        sql += " (3187,'WGS 84 / UTM zone 37S',1),"
        sql += " (3188,'WGS 84 / UTM zone 38S',1),"
        sql += " (3189,'WGS 84 / UTM zone 39S',1),"
        sql += " (3190,'WGS 84 / UTM zone 40S',1),"
        sql += " (3191,'WGS 84 / UTM zone 41S',1),"
        sql += " (3192,'WGS 84 / UTM zone 42S',1),"
        sql += " (3193,'WGS 84 / UTM zone 43S',1),"
        sql += " (3194,'WGS 84 / UTM zone 44S',1),"
        sql += " (3195,'WGS 84 / UTM zone 45S',1),"
        sql += " (3196,'WGS 84 / UTM zone 46S',1),"
        sql += " (3197,'WGS 84 / UTM zone 47S',1),"
        sql += " (3198,'WGS 84 / UTM zone 48S',1),"
        sql += " (3199,'WGS 84 / UTM zone 49S',1),"
        sql += " (3200,'WGS 84 / UTM zone 50S',1),"
        sql += " (3201,'WGS 84 / UTM zone 51S',1),"
        sql += " (3202,'WGS 84 / UTM zone 52S',1),"
        sql += " (3203,'WGS 84 / UTM zone 53S',1),"
        sql += " (3204,'WGS 84 / UTM zone 54S',1),"
        sql += " (3205,'WGS 84 / UTM zone 55S',1),"
        sql += " (3206,'WGS 84 / UTM zone 56S',1),"
        sql += " (3207,'WGS 84 / UTM zone 57S',1),"
        sql += " (3208,'WGS 84 / UTM zone 58S',1),"
        sql += " (3209,'WGS 84 / UTM zone 59S',1),"
        sql += " (3210,'WGS 84 / UTM zone 60S',1),"
        sql += " (27158,'REGCAN95 / UTM zone 27N',1),"
        sql += " (27159,'REGCAN95 / UTM zone 28N',1); "
        sqls.append(sql)
        sql = "CREATE UNIQUE INDEX IF NOT EXISTS \"fields_descriptions_idx_table_fielname\" ON \"fields_descriptions\" ("
        sql += "	\"table\","
        sql += "	\"fieldname\","
        sql += "	\"version_firmaware\""
        sql += ");"
        sqls.append(sql)
        sql = "CREATE INDEX IF NOT EXISTS \"batterylnk_battery_firmware\" ON \"lnk_battery_firmware\" ("
        sql += "	\"id_battery\""
        sql += ");"
        sqls.append(sql)
        sql = "CREATE UNIQUE INDEX IF NOT EXISTS \"flight_block_c_axis_cod_flight_block_axis\" ON \"flight_block_c_axis\" ("
        sql += "	\"cod_flight_block\","
        sql += "	\"id_axis\""
        sql += ");"
        sqls.append(sql)
        sql = "CREATE INDEX IF NOT EXISTS \"c_lndflight_block\" ON \"flight_block\" ("
        sql += "	\"id_lnd\""
        sql += ");"
        sqls.append(sql)
        return sqls

    def get_str_srsid_mapcanvas(self):
        """
        brief: obtiene el identificador interno de QGIS (InternalCrsId) del CRS del mapcanvas
        :return: identificador interno de QGIS (InternalCrsId) del CRS del mapcanvas
        :rtype: str
        """
        current_crs_map_canvas = self.iface.mapCanvas().mapSettings().destinationCrs() # devuelve un QgsCoordinateReferenceSystem con crs del mapcanvas
        str_current_crs_map_canvas = str(current_crs_map_canvas.srsid())
        self.msg_information_crs = "*** Initial CRS Mapcanvas ***\n"
        # self.msg_information_crs += self.instaceDatabase.metadata_crs_object(str_current_crs_map_canvas)
        return str_current_crs_map_canvas

    def get_str_srsid_selectcombo(self):
        """
        brief: obtiene el identificador interno de QGIS (InternalCrsId) del CRS seleccionado en el combobox con signal
                cambio de índice en el combobox
        :return: identificador interno de QGIS (InternalCrsId) del CRS seleccionado en el combobox
        :rtype: str
        """
        # si la selección es el primer elemento
        current_index = self.comboBox_CRSproject.currentIndex()
        if current_index == 0:
            return -1
        else:
            if current_index == 1 and self.control_is_mapcanvas_crs_pflipuav: # current CRS mapcanvas
                str_srsid_selectcombo = self.str_srsid_map_canvas
            else:
                current_description = self.comboBox_CRSproject.currentText()
                str_srsid_selectcombo = str(self.dictionary_crs[current_description])
                self.set_crs_mapcanvas(str_srsid_selectcombo) #pone el crs del mapcanvas al seleccionado

        #self.msg_information_crs += "*** CRS selected ***\n"
        #self.msg_information_crs += self.instaceDatabase.metadata_crs_object(str_srsid_selectcombo)
        return str_srsid_selectcombo

    def initialize(self):
        # SIGNAL/SLOT connections in order:
        self.toolButton_SaveProject.clicked.connect(self.save_project_header_data)
        self.toolButton_SearchPathLogo.clicked.connect(self.path_logo_from_file)
        self.toolButton_SearchPathLogo_2.clicked.connect(self.path_logo2_from_file)
        self.toolButton_createDb.clicked.connect(self.cpp_project_db_creation)

        # SEE: Deshabilitar la proyección sobre la marcha ya no es una opción en QGIS 3.0
        # https://issues.qgis.org/issues/11644
        # 1. activa la reproyección al vuelo en el mapcanvas de QGIS
        # self.iface.mapCanvas().mapSettings().setProjectionsEnabled(True) # Enable on the fly reprojections

        # 2. obtiene una cadena con identificador del crs del mapcanvas
        self.str_srsid_map_canvas = self.get_str_srsid_mapcanvas()
        self.str_authid_map_canvas = self.q3_api_op.get_strcrscode_InternalCrsId2authid(self.str_srsid_map_canvas)

        self.mGroupBox_projectHeaderData.setVisible(False)

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

    def save_project_header_data(self):
        """
        brief:  - copia la base de datos template al nuevo espacio de trabajo PFLIP
                - consulta insert en la tabla [project] de valores generales del proyecto en la BD sqlite del proyecto
                - crea capas GIS auxiliares para digitalizar zonas, ejes, lnd, tof points y axis. Pero no las carga
                - crea campos de geometría en las capas de salida sobre la BD del proyecto
        :return:
        """
        #nemo
        nemo = self.lineEdit_Nemo.text()
        if len(nemo) == 0:
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                "Mnemonic code project is required",
                                                Qgis.Critical,
                                                10)
            return
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
        #cadena de texto identificador interno crs qgis
        str_internal_id_crs_selected = self.get_str_srsid_selectcombo()

        if str_internal_id_crs_selected == -1:
            msg_combobox = "Select coordinate reference system name"
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                msg_combobox,
                                                Qgis.Critical,
                                                10)
            return

        # carga en el contenedor lista los valores almacenados
        self.lst_gral_data_prj.append(nemo)
        self.lst_gral_data_prj.append(title)
        self.lst_gral_data_prj.append(author)
        self.lst_gral_data_prj.append(str_internal_id_crs_selected)
        self.lst_gral_data_prj.append(self.path_db_project)
        self.lst_gral_data_prj.append(self.msg_information_crs)
        self.lst_gral_data_prj.append(company)
        self.lst_gral_data_prj.append(path_logo)
        self.lst_gral_data_prj.append(path_logo_2)
        self.lst_gral_data_prj.append(self.dir_new_path_project_normalize)

        con_db_project = self.db_op.connection_sqlite(self.path_db_project)

        # create project table
        """
        str_sql = "CREATE TABLE IF NOT EXISTS %s (" % modeldb.TABLE_PROJECT_TABLE_NAME
        str_sql += "\"%s\" %s PRIMARY KEY, " % (modeldb.TBL_PROJECT_FIELD_ID_PROJECT, modeldb.SPATIALITE_FIELD_TYPE_INTEGER)
        str_sql += "\"%s\" %s, " % (modeldb.TBL_PROJECT_FIELD_PATH_PROJECT, modeldb.SPATIALITE_FIELD_TYPE_TEXT)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_PROJECT_FIELD_NEMO, modeldb.SPATIALITE_FIELD_TYPE_TEXT)
        str_sql += "\"%s\" %s, " % (modeldb.TBL_PROJECT_FIELD_TITLE, modeldb.SPATIALITE_FIELD_TYPE_TEXT)
        str_sql += "\"%s\" %s, " % (modeldb.TBL_PROJECT_FIELD_AUTHOR, modeldb.SPATIALITE_FIELD_TYPE_TEXT)
        str_sql += "\"%s\" %s, " % (modeldb.TBL_PROJECT_FIELD_PATH_SQLITE_DB, modeldb.SPATIALITE_FIELD_TYPE_TEXT)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_PROJECT_FIELD_CRS_CODE, modeldb.SPATIALITE_FIELD_TYPE_TEXT)
        str_sql += "\"%s\" %s, " % (modeldb.TBL_PROJECT_FIELD_COMPANY, modeldb.SPATIALITE_FIELD_TYPE_TEXT)
        str_sql += "\"%s\" %s, " % (modeldb.TBL_PROJECT_FIELD_PATH_LOGO, modeldb.SPATIALITE_FIELD_TYPE_TEXT)
        str_sql += "\"%s\" %s" % (modeldb.TBL_PROJECT_FIELD_PATH_LOGO_2, modeldb.SPATIALITE_FIELD_TYPE_TEXT)
        str_sql += ");"
        self.db_op.execute_query(con_db_project, str_sql, self.db_op.SQL_TYPE_CREATE_TABLE)
        """
        # grabación de los datos generales del proyecto en la bd
        str_sql = "INSERT INTO %s (" % modeldb.TABLE_PROJECT_TABLE_NAME
        str_sql += "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) VALUES (" % (modeldb.TBL_PROJECT_FIELD_ID_PROJECT,
                                                                         modeldb.TBL_PROJECT_FIELD_PATH_PROJECT,
                                                                         modeldb.TBL_PROJECT_FIELD_NEMO,
                                                                         modeldb.TBL_PROJECT_FIELD_TITLE,
                                                                         modeldb.TBL_PROJECT_FIELD_AUTHOR,
                                                                         modeldb.TBL_PROJECT_FIELD_PATH_SQLITE_DB,
                                                                         modeldb.TBL_PROJECT_FIELD_CRS_CODE,
                                                                         modeldb.TBL_PROJECT_FIELD_COMPANY,
                                                                         modeldb.TBL_PROJECT_FIELD_PATH_LOGO,
                                                                         modeldb.TBL_PROJECT_FIELD_PATH_LOGO_2)
        str_sql += "1, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'" % (self.dir_new_path_project_normalize,
                                                                                nemo,
                                                                                title,
                                                                                author,
                                                                                self.path_db_project,
                                                                                str_internal_id_crs_selected,
                                                                                company,
                                                                                path_logo,
                                                                                path_logo_2)
        str_sql += ");"
        self.db_op.execute_query(con_db_project, str_sql, self.db_op.SQL_TYPE_INSERT)

        # create flight_block table
        """
        str_sql = "CREATE TABLE IF NOT EXISTS %s (" % modeldb.TABLE_FLIGHT_BLOCK_TABLE_NAME
        str_sql += "\"%s\" %s PRIMARY KEY, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_COD_FLIGHT_BLOCK, modeldb.TBL_FLIGHT_BLOCK_FIELD_COD_FLIGHT_BLOCK_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL DEFAULT %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_COD_CAMERA, modeldb.TBL_FLIGHT_BLOCK_FIELD_COD_CAMERA_FIELD_TYPE, modeldb.TBL_FLIGHT_BLOCK_FIELD_COD_CAMERA_DEFAULT_VALUE)
        str_sql += "\"%s\" %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_DTM_PATH, modeldb.TBL_FLIGHT_BLOCK_FIELD_DTM_PATH_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL DEFAULT %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_TOF, modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_TOF_FIELD_TYPE, modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_TOF_DEFAULT_VALUE)
        str_sql += "\"%s\" %s NOT NULL DEFAULT %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_LND, modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_LND_FIELD_TYPE, modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_LND_DEFAULT_VALUE)
        str_sql += "\"%s\" %s NOT NULL DEFAULT %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_FIRMWARE, modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_FIRMWARE_FIELD_TYPE, modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_FIRMWARE_DEFAULT_VALUE)
        str_sql += "\"%s\" %s NOT NULL DEFAULT %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_FB_TYPE, modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_FB_TYPE_FIELD_TYPE, modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_FB_TYPE_DEFAULT_VALUE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_GSD, modeldb.TBL_FLIGHT_BLOCK_FIELD_GSD_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_TOL_GSD, modeldb.TBL_FLIGHT_BLOCK_FIELD_TOL_GSD_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_FOWARD_OVERLAP, modeldb.TBL_FLIGHT_BLOCK_FIELD_FOWARD_OVERLAP_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_SIDE_OVERLAP, modeldb.TBL_FLIGHT_BLOCK_FIELD_SIDE_OVERLAP_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_AC_GPS, modeldb.TBL_FLIGHT_BLOCK_FIELD_AC_GPS_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_AC_OMG, modeldb.TBL_FLIGHT_BLOCK_FIELD_AC_OMG_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_AC_PHI, modeldb.TBL_FLIGHT_BLOCK_FIELD_AC_PHI_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_AC_KAP, modeldb.TBL_FLIGHT_BLOCK_FIELD_AC_KAP_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL DEFAULT %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_TRAJECTORY_TYPE, modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_TRAJECTORY_TYPE_FIELD_TYPE, modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_TRAJECTORY_TYPE_DEFAULT_VALUE)
        str_sql += "\"%s\" %s NOT NULL DEFAULT %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_CRUISE_SPEEP, modeldb.TBL_FLIGHT_BLOCK_FIELD_CRUISE_SPEEP_FIELD_TYPE, modeldb.TBL_FLIGHT_BLOCK_FIELD_CRUISE_SPEEP_DEFAULT_VALUE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_ASCENT_SPEED, modeldb.TBL_FLIGHT_BLOCK_FIELD_ASCENT_SPEED_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_DESCENT_SPEED, modeldb.TBL_FLIGHT_BLOCK_FIELD_DESCENT_SPEED_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_LEA, modeldb.TBL_FLIGHT_BLOCK_FIELD_LEA_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_INITIAL_HEIGHT, modeldb.TBL_FLIGHT_BLOCK_FIELD_INITIAL_HEIGHT_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_NBK, modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_NBK_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_END_HEIGHT, modeldb.TBL_FLIGHT_BLOCK_FIELD_END_HEIGHT_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_WPB, modeldb.TBL_FLIGHT_BLOCK_FIELD_WPB_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_IMAGES_ITEM, modeldb.TBL_FLIGHT_BLOCK_FIELD_IMAGES_ITEM_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_SHOT_INTERVAL, modeldb.TBL_FLIGHT_BLOCK_FIELD_SHOT_INTERVAL_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_OMEGA_ANGLE, modeldb.TBL_FLIGHT_BLOCK_FIELD_OMEGA_ANGLE_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_PHI_ANGLE, modeldb.TBL_FLIGHT_BLOCK_FIELD_PHI_ANGLE_FIELD_TYPE)
        str_sql += "\"%s\" %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_ERC, modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_ERC_FIELD_TYPE)
        str_sql += "\"%s\" %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_EAL, modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_EAL_FIELD_TYPE)
        str_sql += "\"%s\" %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_EGI, modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_EGI_FIELD_TYPE)
        str_sql += "\"%s\" %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_SHP, modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_SHP_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_SSH, modeldb.TBL_FLIGHT_BLOCK_FIELD_SSH_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_GPA, modeldb.TBL_FLIGHT_BLOCK_FIELD_GPA_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_WAE, modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_WAE_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_WAL, modeldb.TBL_FLIGHT_BLOCK_FIELD_WAL_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_WAS, modeldb.TBL_FLIGHT_BLOCK_FIELD_WAS_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL DEFAULT %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_PROCESS_ST, modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_PROCESS_ST_FIELD_TYPE, modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_PROCESS_ST_DEFAULT_VALUE)
        str_sql += "\"%s\" %s NOT NULL DEFAULT %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_NPSF, modeldb.TBL_FLIGHT_BLOCK_FIELD_NPSF_FIELD_TYPE, modeldb.TBL_FLIGHT_BLOCK_FIELD_NPSF_DEFAULT_VALUE)
        str_sql += "\"%s\" %s NOT NULL DEFAULT %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_MOUNTING_TYPE, modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_MOUNTING_TYPE_FIELD_TYPE, modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_MOUNTING_TYPE_DEFAULT_VALUE)
        str_sql += "\"%s\" %s NOT NULL DEFAULT %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_TYPE_GIMBEL_MOUNT, modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_TYPE_GIMBEL_MOUNT_FIELD_TYPE, modeldb.TBL_FLIGHT_BLOCK_FIELD_ID_TYPE_GIMBEL_MOUNT_DEFAULT_VALUE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_OFFSET_OMEGA, modeldb.TBL_FLIGHT_BLOCK_FIELD_OFFSET_OMEGA_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_OFFSET_PHI, modeldb.TBL_FLIGHT_BLOCK_FIELD_OFFSET_PHI_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_OFFSET_KAPPA, modeldb.TBL_FLIGHT_BLOCK_FIELD_OFFSET_KAPPA_FIELD_TYPE)
        str_sql += "\"%s\" %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_FLIGHT_DURATION, modeldb.TBL_FLIGHT_BLOCK_FIELD_FLIGHT_DURATION_FIELD_TYPE)
        str_sql += "\"%s\" %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_GCP_CALIBRATION_PATH, modeldb.TBL_FLIGHT_BLOCK_FIELD_GCP_CALIBRATION_PATH_FIELD_TYPE)
        str_sql += "\"%s\" %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_GCP_IS_FIXED, modeldb.TBL_FLIGHT_BLOCK_FIELD_GCP_IS_FIXED_FIELD_TYPE)
        str_sql += "\"%s\" %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_GCP_SEPARATION_DTM, modeldb.TBL_FLIGHT_BLOCK_FIELD_GCP_SEPARATION_DTM_FIELD_TYPE)
        str_sql += "\"%s\" %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_GCP_PRECISION_PIX, modeldb.TBL_FLIGHT_BLOCK_FIELD_GCP_PRECISION_PIX_FIELD_TYPE)
        str_sql += "\"%s\" %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_GCP_2DPRECISION, modeldb.TBL_FLIGHT_BLOCK_FIELD_GCP_2DPRECISION_FIELD_TYPE)
        str_sql += "\"%s\" %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_GCP_HPRECISION, modeldb.TBL_FLIGHT_BLOCK_FIELD_GCP_HPRECISION_FIELD_TYPE)
        str_sql += "\"%s\" %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_GCP_IMAGE_PRECISION, modeldb.TBL_FLIGHT_BLOCK_FIELD_GCP_IMAGE_PRECISION_FIELD_TYPE)
        str_sql += "\"%s\" %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_GCP_PREFIX, modeldb.TBL_FLIGHT_BLOCK_FIELD_GCP_PREFIX_FIELD_TYPE)
        str_sql += "\"%s\" %s DEFAULT %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_GCP_PROCESS_ST, modeldb.TBL_FLIGHT_BLOCK_FIELD_GCP_PROCESS_ST_FIELD_TYPE, modeldb.TBL_FLIGHT_BLOCK_FIELD_GCP_PROCESS_ST_DEFAULT_VALUE)
        str_sql += "\"%s\" %s, " % (modeldb.TBL_FLIGHT_BLOCK_FIELD_AV_HEIGHT_OBJ, modeldb.TBL_FLIGHT_BLOCK_FIELD_AV_HEIGHT_OBJ_FIELD_TYPE)
        str_sql += "\"%s\" %s NOT NULL DEFAULT %s" % (modeldb.TBL_FLIGHT_BLOCK_FIELD_N_STRIPS, modeldb.TBL_FLIGHT_BLOCK_FIELD_N_STRIPS_FIELD_TYPE, modeldb.TBL_FLIGHT_BLOCK_FIELD_N_STRIPS_DEFAULT_VALUE)
        str_sql += ");"
        self.db_op.execute_query(con_db_project, str_sql, self.db_op.SQL_TYPE_CREATE_TABLE)
        """

        self.create_spatial_tables(self.path_db_project,
                                   str_internal_id_crs_selected)

        # mensaje final
        str_final_msg = "Project %s registered successfully" % c.CONST_PFLIPUAV_TITLE
        self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                            str_final_msg,
                                            Qgis.Info,
                                            10)

        con_db_project.close()  # cierra la base de datos del proyecto
        self.close()  # cierra el dialogo

    def set_crs_mapcanvas(self,
                          str_id_internal):
        """
        brief: pone el crs del mapcanvas a partir de un identificador interno qgis
        param[in]: cadena de texto con el identificador interno qgis del crs
        """
        int_id_internal = int(str_id_internal)
        self.iface.mapCanvas().mapSettings().setDestinationCrs(QgsCoordinateReferenceSystem(int_id_internal,
                                                                                            QgsCoordinateReferenceSystem.InternalCrsId))