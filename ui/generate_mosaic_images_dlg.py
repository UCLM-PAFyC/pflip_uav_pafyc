# -*- coding: utf-8 -*-

# Import PyQt5 classes
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5 import QtCore

# Import PyQGIS classes
from qgis.gui import QgsMessageBar
from qgis.core import (Qgis, QgsRectangle)

# others imports
import os, fnmatch

# import self classes
from .. import config as c # valores constantes

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
import sys
sys.path.append(os.path.dirname(__file__))
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__),
                                            'generate_mosaic_images_dlg.ui'),
                               resource_suffix='')

class generateMosaicImages(QtWidgets.QDialog,
                           FORM_CLASS):

    def __init__(self,
                 iface,
                 current_path_project_directory,
                 path_plugin,
                 parent=None):
        """
        Brief: clase inicializadora del dialogo
        :param iface: para trabajar con la interfaz de usuario de QGIS
        :type iface: QgsInterface
        """
        super(generateMosaicImages, self).__init__(parent)

        self.iface = iface # Save reference to the QGIS interface
        self.current_path_project_directory = current_path_project_directory
        self.mapcanvasQgis = self.iface.mapCanvas()


        # qsettings: fichero que almacena los últimos valores introducidos por el usuario en la aplicación en anteriores sesiones
        #path_file_qsettings = os.path.normcase(os.path.join(path_plugin,'/templates/qsettings.ini'))
        path_file_qsettings = os.path.normpath(path_plugin + '/templates/qsettings.ini')
        self.my_qsettings = QtCore.QSettings(path_file_qsettings,QtCore.QSettings.IniFormat)

        # Set up the user interface from Designer.
        self.setupUi(self)

        # inicializa ruta del directorio de salida con valor introducido en QSettings
        self.path_output_dir = self.my_qsettings.value("path_output_dir_mosaic")
        self.lineEdit_pathDir.setText(self.path_output_dir)

        # inicializa visualización de botones
        self.toolButton_process.setEnabled(True)
        self.toolButton_saveImage.setEnabled(False)
        self.toolButton_mosaic.setEnabled(False)

        # SIGNAL/SLOT connections in order:
        self.toolButton_mosaic.clicked.connect(self.mosaic)
        self.toolButton_process.clicked.connect(self.process)
        self.toolButton_saveImage.clicked.connect(self.save_image)
        self.comboBox_output_directory.currentIndexChanged.connect(self.changed_combo_output_directory)

    def changed_combo_output_directory(self):
        """

        :return:
        """
        # establece el directorio de trabajo a partir de valor introducido en el comboBox correspondiente
        int_current_index_combo = self.comboBox_output_directory.currentIndex()
        if int_current_index_combo == 0:
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                "Select output directory",
                                                Qgis.Critical,
                                                10)
            return

        if int_current_index_combo == 1: # common data
            self.path_output_dir = \
                os.path.normcase(self.my_qsettings.value("default_path_workspace_directory") + c.CONST_SEPARATOR_DIRECTORIES + c.CONST_COMMON_DATA_DIRNAME)
            if not os.path.exists(self.path_output_dir):
                os.makedirs(self.path_output_dir)

            # actualiza el valor del último path del fichero qsetting.ini
            self.my_qsettings.setValue("path_output_dir_mosaic",
                                       self.path_output_dir)
            self.lineEdit_pathDir.setText(self.path_output_dir)
            self.lineEdit_pathDir.setEnabled(True)

        if int_current_index_combo == 2: # project_data
            self.path_output_dir = \
                os.path.normcase(self.current_path_project_directory + c.CONST_SEPARATOR_DIRECTORIES + c.CONST_PROJ_DATA_DIRNAME + c.CONST_SEPARATOR_DIRECTORIES + c.CONST_MOSAICS_DIRNAME)
            if not os.path.exists(self.path_output_dir):
                os.makedirs(self.path_output_dir)

            # actualiza el valor del último path del fichero qsetting.ini
            self.my_qsettings.setValue("path_output_dir_mosaic",
                                       self.path_output_dir)
            self.lineEdit_pathDir.setText(self.path_output_dir)
            self.lineEdit_pathDir.setEnabled(True)

        if int_current_index_combo == 3: # user selection
            self.search_output_directory()

        if not os.path.exists(self.path_output_dir):
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                "Don't exits path output directory: " + self.path_output_dir,
                                                Qgis.Critical,
                                                10)
            return

    def mosaic(self):
        """
        Brief: monta la cadena gdal_merge para producir el mosaico

        """
        mosaic_filename = 'mosaic.tif'
        path_mosaic_ouput_filename = os.path.normcase(os.path.join(self.path_output_dir,
                                                                   mosaic_filename))

        if os.path.exists(path_mosaic_ouput_filename):
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                "Mosaic file exists in output directory",
                                                Qgis.Critical,
                                                10)
            return

        # forma cadena de texto con todos los ficheros .tif producidos en el directorio de salida
        for root, dirs,files in os.walk(self.path_output_dir):
            str_cadena_paths_input_to_mocaic = ''
            for file in fnmatch.filter(files,'*.tif'):
                path_input_current_filename = os.path.normcase(os.path.join(self.path_output_dir,file))
                str_cadena_paths_input_to_mocaic  += path_input_current_filename + ' '

        str_cadena_merge = 'gdal_merge -o '
        str_cadena_merge += path_mosaic_ouput_filename + ' '
        str_cadena_merge += str_cadena_paths_input_to_mocaic

        os.system(str_cadena_merge)

        self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                            "Mosaic generated",
                                            Qgis.Info,
                                            10)

        self.toolButton_mosaic.setEnabled(False)
        self.toolButton_process.setEnabled(True)

        #TODO: cargar el raster producido?

        self.close() #cierra el dialogo

    def process(self):
        """
        Brief: inicia el procesamiento tras pulsar el botón correspondiente
        """

        qgs_rect_mapcanvas = self.mapcanvasQgis.extent()
        width_source = qgs_rect_mapcanvas.width()
        height_source = qgs_rect_mapcanvas.height()
        #scale_source = self.mapcanvasQgis.scale()
        self.xmin_source = qgs_rect_mapcanvas.xMinimum()
        self.ymin_source = qgs_rect_mapcanvas.yMinimum()
        self.xmax_source = qgs_rect_mapcanvas.xMaximum()
        self.ymax_source = qgs_rect_mapcanvas.yMaximum()

        mapunitsperpixel_source = self.mapcanvasQgis.mapUnitsPerPixel()
        user_output_resolution = self.doubleSpinBox_outputResolution.value()
        if user_output_resolution >= mapunitsperpixel_source:
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                "User output resolution is larger than map units per pixel MapCanvas",
                                                Qgis.Critical,
                                                10)
            return

        factor_scale = user_output_resolution / mapunitsperpixel_source

        self.width_malla = width_source * factor_scale
        self.height_malla = height_source * factor_scale

        self.range_malla = int(1/factor_scale)

        # inicializa row column min y max
        self.current_row_min = 0
        self.current_column_min = 0
        self.current_row_max = 1
        self.current_column_max = 1

        self.zoom_row_column(self.current_row_min,
                             self.current_column_min,
                             self.current_row_max,
                             self.current_column_max)

        self.toolButton_process.setEnabled(False)
        self.toolButton_saveImage.setEnabled(True)

    def save_image(self):
        """
        Brief: Salva la imagen en el directorio de salida y actualiza índices row - column min y rox - column max
        """
        output_filename = "output_" + str(self.current_row_min) + str(self.current_column_min) + ".tif"
        path_output_filename = os.path.join(self.path_output_dir,
                                            output_filename)
        self.mapcanvasQgis.saveAsImage(path_output_filename,
                                       None,
                                       'TIF')

        if self.current_column_max > self.range_malla:
            if self.current_row_max > self.range_malla:
                self.toolButton_saveImage.setEnabled(False)
                self.toolButton_mosaic.setEnabled(True)
                self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                    "Tiles generated",
                                                    Qgis.Info,
                                                    10)
                # zoom al estado original
                qgs_rect_origin = QgsRectangle(self.xmin_source,
                                               self.ymin_source,
                                               self.xmax_source,
                                               self.ymax_source)

                self.mapcanvasQgis.setExtent(qgs_rect_origin)
                self.mapcanvasQgis.refresh()

                return
            else: # avance en columna
                self.current_row_min += 1
                self.current_row_max += 1
                self.current_column_min = 0
                self.current_column_max = 1
        else: # avance en filas
            self.current_column_min += 1
            self.current_column_max += 1

        self.zoom_row_column(self.current_row_min,
                             self.current_column_min,
                             self.current_row_max,
                             self.current_column_max)

    def search_output_directory(self):
        self.lineEdit_pathDir.clear()
        self.lineEdit_pathDir.setEnabled(False)

        # captura a partir de explorador del path del proyecto
        self.path_output_dir = (QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                           "Select output directory",
                                                                           self.my_qsettings.value("path_output_dir_mosaic"),
                                                                           QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks))

        if len(self.path_output_dir) == 0: #si no se introduce ningún path
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                "Select output directory",
                                                Qgis.Critical,
                                                10)
            return
        else:
            # actualiza el valor del último path del fichero qsetting.ini
            self.my_qsettings.setValue("path_output_dir_mosaic",
                                       self.path_output_dir)
            self.lineEdit_pathDir.setText(self.path_output_dir)
            self.lineEdit_pathDir.setEnabled(True)

    def zoom_row_column(self,
                        row_min,
                        column_min,
                        row_max,
                        column_max):
        """
        Brief: Realiza un zoom a partir de la row - column min y row - column max del mallado producido
        :param row_min: fila min
        :type row_min: int
        :param column_min: columna min
        :type column_min: int
        :param row_max: row max
        :type row_max: int
        :param column_max: columna max
        :type column_max: int
        """
        x_min_malla = self.xmin_source + column_min * self.width_malla
        y_min_malla = self.ymin_source + row_min  * self.height_malla
        x_max_malla = self.xmin_source + column_max * self.width_malla
        y_max_malla = self.ymin_source + row_max * self.height_malla

        qgs_rect_malla = QgsRectangle(x_min_malla,y_min_malla,x_max_malla,y_max_malla)
        self.mapcanvasQgis.setExtent(qgs_rect_malla)
        self.mapcanvasQgis.refresh()