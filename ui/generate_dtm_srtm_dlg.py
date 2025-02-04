# -*- coding: utf-8 -*-

# Import PyQt5 classes
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5 import QtCore

# Import QGIS classes
from qgis.core import (Qgis, QgsProject, QgsRasterLayer)

# Others imports
import os, fnmatch
import shutil  # para copia de ficheros

# import self classes
from .. import config as c # valores constantes

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
import sys
sys.path.append(os.path.dirname(__file__))
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__),
                                            'generate_dtm_srtm_dlg.ui'),
                               resource_suffix='')

class generateDtmSrtm(QtWidgets.QDialog,
                      FORM_CLASS):
    """
    Brief:
    """
    def __init__(self,
                 iface,
                 path_db_project,
                 path_plugin,
                 list_dir_nivel1,
                 list_dir_nivel2,
                 list_filename_hojas,
                 lst_path_srtm90,
                 parent=None):
        """
        Brief:
        """
        super(generateDtmSrtm, self).__init__(parent)

        self.iface = iface # Save reference to the QGIS interface
        self.path_plugin = path_plugin
        self.list_dir_nivel1 = list_dir_nivel1 # del tipo ['n042']
        self.list_dir_nivel2 = list_dir_nivel2 # del tipo ['n042w006']
        self.list_filename_hojas = list_filename_hojas # del tipo ['GLSDEM_n042w006.tif.gz']
        self.lst_path_srtm90 = lst_path_srtm90


        # qsettings: fichero que almacena los últimos valores introducidos por el usuario en la aplicación en anteriores sesiones
        path_file_qsettings = os.path.normpath(self.path_plugin + '/templates/qsettings.ini')
        self.my_qsettings = QtCore.QSettings(path_file_qsettings,QtCore.QSettings.IniFormat)

        self.path_db_project = path_db_project # path de las bases de datos de proyecto

        # Set up the user interface from Designer.
        self.setupUi(self)

        # inicializa ruta del directorio de salida con valor introducido en QSettings
        self.path_tiles_dtm_srtm = self.my_qsettings.value("path_degrees_tiles_srtm_dtm")
        self.lineEdit_pathDir.setText(self.path_tiles_dtm_srtm)

        # SIGNAL/SLOT connections in order:
        self.toolButton_process.clicked.connect(self.process)
        self.toolButton_searchTilesSrtmDirectory.clicked.connect(self.search_tiles_srtm_directory)

    def process(self):
        """
        Brief: proceso principal
        :return:
        """
        # comprueba si la carpeta con los tiles existe
        self.path_tiles_dtm_srtm = self.lineEdit_pathDir.text()
        if not os.path.exists(self.path_tiles_dtm_srtm):
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                "Don't exits degrees tiles SRTM90 DTM directory: " + self.path_tiles_dtm_srtm,
                                                Qgis.Critical,
                                                10)
            return

        # variables generales a procesado de una o más tiles
        str_name_tiles = "tile_srtm90"
        mosaic_filename = 'mosaic_dtm_srtm90'
        #TODO: pasar a directorio data?
        path_mosaic_output_dirname = os.path.normpath(self.path_plugin + '/generateDtmSrtm/temp')
        num_hojas = len(self.list_filename_hojas)

        #borra las entradas del TOC
        for layer in self.iface.mapCanvas().layers():
            if str_name_tiles == layer.name() or mosaic_filename == layer.name():
                QgsProject.instance().removeMapLayer(layer.id())

        #borra todos los ficheros contenidos en esa carpeta generados anteriormente
        for root,dirs,files in os.walk(path_mosaic_output_dirname):
            for name in files:
                os.remove(os.path.join(root, name))

        if (num_hojas == 1): # la zona cae en una sola hoja
            path_tile_srtm90_zip_destino = os.path.normpath(self.path_plugin + "/generateDtmSrtm/temp/" + str_name_tiles + ".tif.gz")
            dirn1 = self.list_dir_nivel1[0]
            dirn2 = self.list_dir_nivel2[0]
            filename = self.list_filename_hojas[0]
            path_file_dtm_srtm_origen = os.path.normpath(self.path_tiles_dtm_srtm + '/' + dirn1 + '/' + 'GLSDEM_' + dirn2 + '/' + filename)
            #copiar a carpeta workspace
            shutil.copyfile(path_file_dtm_srtm_origen,
                            path_tile_srtm90_zip_destino)
            #descomprimir fichero en destino
            str_cmd = "gzip -d " + path_tile_srtm90_zip_destino
            os.system(str_cmd)

            path_srtm90_tif = os.path.normpath(self.path_plugin + '/generateDtmSrtm/temp/tile_srtm90.tif')

        if (num_hojas > 1): # la zona cae en 2 o más hojas

            #se forma la cadena de hojas afectadas
            for i in range(num_hojas):
                #copiar a carpeta workspace
                path_tile_srtm90_zip_destino = os.path.normpath(self.path_plugin + "/generateDtmSrtm/temp/" + str_name_tiles + "_" + str(i) + ".tif.gz")
                dirn1 = self.list_dir_nivel1[i]
                dirn2 = self.list_dir_nivel2[i]
                filename = self.list_filename_hojas[i]
                path_file_dtm_srtm_origen = os.path.normpath(self.path_tiles_dtm_srtm + '/' + dirn1 + '/' + 'GLSDEM_' + dirn2 + '/' + filename)
                #copiar a carpeta workspace
                shutil.copyfile(path_file_dtm_srtm_origen,
                                path_tile_srtm90_zip_destino)
                #descomprimir fichero en destino
                str_cmd = "gzip -d " + path_tile_srtm90_zip_destino
                os.system(str_cmd)

            # mosaico
            str_mosaic_filename = mosaic_filename + ".tif"
            path_mosaic_output_filename = os.path.normpath(os.path.join(path_mosaic_output_dirname,str_mosaic_filename))

            #si existe mosaico lo borro
            if os.path.exists(path_mosaic_output_filename):
                os.remove(path_mosaic_output_filename)

            # forma cadena de texto con todos los ficheros .tif producidos en el directorio de salida
            for root, dirs,files in os.walk(path_mosaic_output_dirname):
                str_cadena_paths_input_to_mocaic = ''
                for file in fnmatch.filter(files,'*.tif'):
                    path_input_current_filename = os.path.normcase(os.path.join(path_mosaic_output_dirname,file))
                    str_cadena_paths_input_to_mocaic  += path_input_current_filename + ' '

            str_cadena_merge = 'gdal_merge -o '
            str_cadena_merge += path_mosaic_output_filename + ' '
            str_cadena_merge += str_cadena_paths_input_to_mocaic

            os.system(str_cadena_merge)

            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                "Mosaic DTM SRTM90 generated",
                                                Qgis.Info,
                                                10)

            path_srtm90_tif = path_mosaic_output_filename

            #borra tiles generados anteriormente para componer el mosaico
            path_directory_destino = os.path.normpath(self.path_plugin + '/generateDtmSrtm/temp')
            for root,dirs,files in os.walk(path_directory_destino):
                for name in files:
                    if str_name_tiles in name:
                        os.remove(os.path.join(root, name))

        # carga el DTM SRTM90 producido
        fileName = path_srtm90_tif
        fileInfo = QtCore.QFileInfo(fileName)
        baseName = fileInfo.baseName()
        rlayer = QgsRasterLayer(fileName,
                                baseName)

        QgsProject.instance().addMapLayer(rlayer) #añado la capa

        self.lst_path_srtm90.append(path_srtm90_tif)

        self.close()

    def search_tiles_srtm_directory(self):
        """
        Brief: Abre navegador para seleccionar el directorio donde están los tiles
        """
        self.lineEdit_pathDir.clear()
        self.lineEdit_pathDir.setEnabled(False)

        # captura a partir de explorador del path del proyecto
        self.path_tiles_dtm_srtm = (QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                           "Select degrees tiles SRTM90 DTM directory",
                                                                           self.my_qsettings.value("path_degrees_tiles_srtm_dtm"),
                                                                           QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks))

        if len(self.path_tiles_dtm_srtm) == 0: #si no se introduce ningún path
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                "Select degrees tiles SRTM90 DTM directory",
                                                Qgis.Warning,
                                                10)
            return
        else:
            # actualiza el valor del último path del fichero qsetting.ini
            self.my_qsettings.setValue("path_degrees_tiles_srtm_dtm",
                                       self.path_tiles_dtm_srtm)
            self.lineEdit_pathDir.setText(self.path_tiles_dtm_srtm)
            self.lineEdit_pathDir.setEnabled(True)
