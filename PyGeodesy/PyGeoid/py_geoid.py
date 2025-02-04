# -*- coding: utf-8 -*-

# import PyQt5 classes
from PyQt5.QtCore import QFileInfo

# import PyQQGIS classes
from qgis.core import (QgsRasterLayer)

#import self classes
from ...classes.qgis3_api_operations import Qgis3ApiOperations

from ... import config as c

import os

class PyGeoid:
    """
    Brief:
    """
    def __init__(self,
                 iface,
                 path_plugin):
        """
        Brief:inicialización del cuerpo de la clase
        """
        self.iface = iface        
        self.q3_api_op = Qgis3ApiOperations(self.iface)

        # ruta del geoide
        path_directory_geoid = "PyGeodesy/PyGeoid/geoids/geoid.tif"
        self.str_path_geoid = os.path.normcase(os.path.join(path_plugin,
                                                            path_directory_geoid))

    def get_ondulation_from_geoid_interpolate(self,
                                              first_coordinate,
                                              second_coordinate,
                                              int_crs_point_transform):
        """
        Brief:
        """
        if os.path.exists(self.str_path_geoid):
            fileName = self.str_path_geoid
            fileInfo = QFileInfo(fileName)
            baseName = fileInfo.baseName()


            #TODO: aquí pide el CRS del MDT. Ver si se puede meter por código.
            rlayer = QgsRasterLayer(fileName,
                                    baseName)
            ondulation = self.q3_api_op.get_value_from_raster_file_interpolation(rlayer,
                                                                                 first_coordinate,
                                                                                 second_coordinate,
                                                                                 int_crs_point_transform)
            return ondulation
        else:
            return 0.0