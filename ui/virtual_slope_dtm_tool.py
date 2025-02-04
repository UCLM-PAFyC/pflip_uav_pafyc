# -*- coding: utf-8 -*-
"""
/***************************************************************************
    QLL3 plugin
        Módulo:     ui_tool_template.py
        Inicio:     2019-10-03
        Autor:      Damián Ortega Terol
        Email:      damian.ortega@correo.gob.es
 ***************************************************************************/
"""
# Import PyQt5 classes
from PyQt5 import uic
from PyQt5.QtCore import (Qt, QVariant)
from PyQt5.QtWidgets import (QDialog, QMessageBox, QFileDialog, QProgressBar, QLabel)

# Import PyQGIS classes
from qgis.core import (Qgis, QgsMapLayerProxyModel, QgsVectorFileWriter, QgsField,
                       QgsPoint, QgsPointXY, QgsGeometry, QgsProject, QgsVectorLayer, QgsCoordinateReferenceSystem,
                       QgsFeature)

from osgeo import gdal, ogr

# Import Python classes
import os
import sys

from shapely.geometry import Point, Polygon
from math import sqrt


# import self classes
from .. import config as c  # constants
from .. classes.qgis3_api_operations import Qgis3ApiOperations

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
sys.path.append(os.path.dirname(__file__))
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__),
                                            'virtual_slope_dtm_tool.ui'),
                               resource_suffix='')

CONST_AXIS_UNION_POINTS_LAYERNAME = "Axis union points"
CONST_BUFFER_LINESTRING_LAYERNAME = "Buffer linestring"
CONST_VERTEXS_LINESTRING_POINTS_LAYERNAME = "Vertexs linestring points"
CONTS_HEIGHT_FIELDNAME = "Height"

class VirtualSlopeDtmTool(QDialog,
                          FORM_CLASS):
    def __init__(self,
                 iface,
                 my_qsettings,
                 path_plugin,
                 parent=None):
        """Constructor"""
        self.iface = iface
        self.my_qsettings = my_qsettings
        self.path_plugin = path_plugin
        self.q3_api_op = Qgis3ApiOperations(self.iface)

        super(VirtualSlopeDtmTool, self).__init__(parent)
        self.setupUi(self)

        self.initialize()
        self.initilize_signals_slots()

    def assign_height_fieldname(self):
        """
        """
        current_point_vector_layer = self.mMapLayerComboBox_pointVectorLayer.currentLayer()
        str_height_field_name = self.comboBox_heightFieldname.currentText()
        # check select fieldname
        if len(str_height_field_name) == 0:
            str_msg = "There is no double type field in the selected layer. Create the corresponding field and run again"
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                str_msg,
                                                Qgis.Critical,
                                                20)
            return

        # check existen valores no nulos en el campo seleccionado
        height_fieldname_is_empty = True
        current_point_vector_layer = self.mMapLayerComboBox_pointVectorLayer.currentLayer()
        for feature in current_point_vector_layer.getFeatures():
            current_value_selected_fielname = feature[str_height_field_name]
            if current_value_selected_fielname > 0:
                height_fieldname_is_empty = False

        if not height_fieldname_is_empty:
            str_msg = "There are values recorded in the selected field [" + str_height_field_name + "]"
            str_msg += ": delete them and run again"
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                str_msg,
                                                Qgis.Critical,
                                                20)
            return

        float_objects_average_height = self.mQgsDoubleSpinBox_objectAverageHeight.value()
        dtm_rlayer = self.mMapLayerComboBox_DTMlayer.currentLayer()
        qgscrs_dtm_rlayer = dtm_rlayer.crs()
        str_epsg_crs_project = str(qgscrs_dtm_rlayer.postgisSrid())  # ej.: "25830"

        # initialize msg errors
        str_msg_errors = ""

        qgsrect_dtm_layer = dtm_rlayer.extent()

        current_point_vector_layer = self.mMapLayerComboBox_pointVectorLayer.currentLayer()
        current_point_vector_layer.startEditing()
        for feature in current_point_vector_layer.getFeatures():
            geom_feature = feature.geometry()
            qgs_point_xy = geom_feature.asPoint()
            coor_x_feature = qgs_point_xy.x()
            coor_y_feature = qgs_point_xy.y()
            if qgsrect_dtm_layer.contains(qgs_point_xy):
                dtm_height_current_feature = self.q3_api_op.get_value_from_raster_file_interpolation(dtm_rlayer,
                                                                                                     coor_x_feature,
                                                                                                     coor_y_feature,
                                                                                                     int(str_epsg_crs_project))
                height_object_over = dtm_height_current_feature + float_objects_average_height
                feature[str_height_field_name] = height_object_over
                current_point_vector_layer.updateFeature(feature)
            else:
                str_msg_errors += "Point coordinates (" + str(coor_x_feature) + ", " + str(coor_y_feature) + ") out of extents DTM layer" + "\n"

        current_point_vector_layer.commitChanges()

        current_point_vector_layer.reload()
        current_point_vector_layer.updateFields()
        current_point_vector_layer.updateExtents()

        if len(str_msg_errors) > 0:
            msg = QMessageBox()
            msg.setWindowTitle("Virtual slope DTM Tool")
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Errors found in the virtual slope generation")
            msg.setInformativeText("Aditional information")
            msg.setDetailedText(str_msg_errors)
            msg.exec_()

    def calculate_height_interpolate(self,
                                     qgspoint_p,
                                     lst_qgspoints_linestring):
        """
        """
        # define our polygon of interest, and the point we'd like to test
        # for the nearest location
        num_points_linestring = len(lst_qgspoints_linestring) - 1
        nearest_qgspoint = None
        min_dist = 9999999999999.0

        height = 9
        for i in range(num_points_linestring):
            segment_start = lst_qgspoints_linestring[i]
            segment_end = lst_qgspoints_linestring[i+1]
            intersection_qgspoint = self.intersect_point_to_line(qgspoint_p,
                                                                 segment_start,
                                                                 segment_end)
            current_distance_p_x_intersection = qgspoint_p.distance(intersection_qgspoint)
            if current_distance_p_x_intersection < min_dist:
                min_dist = current_distance_p_x_intersection
                nearest_qgspoint = intersection_qgspoint
                height = self.calculate_height_interpolate_in_segment(nearest_qgspoint,
                                                                      segment_start,
                                                                      segment_end)
        return height

    def calculate_height_interpolate_in_segment(self,
                                                intersection_qgspoint,
                                                segment_start,
                                                segment_end):
        distance_segment = segment_start.distance(segment_end)
        distance_start_intersection = segment_start.distance(intersection_qgspoint)
        height_increment_end_start = segment_end.z() - segment_start.z()
        height_interpolate = segment_start.z() + height_increment_end_start * distance_start_intersection / distance_segment
        return height_interpolate

    def clicked_groupbox_point_vector_layer(self):
        """
        Habilita / deshabilita resto de groupbox
        """
        if self.mGroupBox_pointVectorLayer.isChecked():
            self.mGroupBox_linestringVectorLayer.setChecked(False)

    def clicked_groupbox_linestring_vector_layer(self):
        """
        Habilita / deshabilita resto de groupbox
        """
        if self.mGroupBox_linestringVectorLayer.isChecked():
            self.mGroupBox_pointVectorLayer.setChecked(False)

    def clicked_radiobutton_generate_axis_union_point(self):
        """
        """
        if self.radioButton_generateAxisUnionPointShp.isChecked():
            self.lineEdit_pathOutputAxisUnionPointsShp.setEnabled(True)
            self.toolButton_searchPathOutputAxisUnionPointsShp.setEnabled(True)
        else:
            self.lineEdit_pathOutputAxisUnionPointsShp.setEnabled(False)
            self.toolButton_searchPathOutputAxisUnionPointsShp.setEnabled(False)

    def fill_fieldnames_in_combo_height_fielnames(self):
        """
        Rellena los campos de la point layer disponibles en el correspondiente desplegable
        """
        self.comboBox_heightFieldname.clear()
        current_point_vector_layer = self.mMapLayerComboBox_pointVectorLayer.currentLayer()
        if current_point_vector_layer is not None:
            prov_current_point_vector_layer = current_point_vector_layer.dataProvider()
            lst_qgsfields_current_point_vector_layer = prov_current_point_vector_layer.fields()
            for qgsfield in lst_qgsfields_current_point_vector_layer:
                if qgsfield.typeName() == "Real":
                    self.comboBox_heightFieldname.addItem(qgsfield.name())

    def generate_buffer_linestring_memory_layer(self,
                                                linestring_memory_layer,
                                                qgsrect_dtm_layer):
        """
        :param linestring_memory_layer:
        :return:
        """
        distance_buffer = self.mQgsDoubleSpinBox_traceWidth.value()

        # remove previous proccessing
        layers = [layer for layer in QgsProject.instance().mapLayers().values()]
        for layer in layers:
            if layer.name() == CONST_BUFFER_LINESTRING_LAYERNAME:
                QgsProject.instance().removeMapLayers([layer.id()])

        str_uri = 'Polygon?crs=epsg:%s&field=id:string(3)' % self.str_epsg_crs_project
        buffer_memory_layer = QgsVectorLayer(str_uri,
                                             CONST_BUFFER_LINESTRING_LAYERNAME,
                                             "memory")
        dataprovider_buffer_memory_layer = buffer_memory_layer.dataProvider()

        qgsrect_dtm_layer_geometry = QgsGeometry.fromRect(qgsrect_dtm_layer)
        for current_feature_linestring_memory_layer in linestring_memory_layer.getFeatures():
            qgs_geometry_current_feature_linestring_memory_layer = current_feature_linestring_memory_layer.geometry()

            if qgs_geometry_current_feature_linestring_memory_layer.intersects(qgsrect_dtm_layer_geometry):
                qgsgeometry_linestring_x_qgsrect_dtm_layer = \
                    qgs_geometry_current_feature_linestring_memory_layer.intersection(qgsrect_dtm_layer_geometry)

            buffer_geometry = qgsgeometry_linestring_x_qgsrect_dtm_layer.buffer(distance_buffer,
                                                                                2)
            #buffer_geometry_x_qgsrect_dtm_layer = buffer_geometry.intersection(QgsGeometry.fromRect(qgsrect_dtm_layer))

            feature_buffer = QgsFeature()
            feature_buffer.setGeometry(buffer_geometry)
            dataprovider_buffer_memory_layer.addFeatures([feature_buffer])
            # FIXME: para cuando hay varios linestrings en la capa
            break

        QgsProject.instance().addMapLayers([buffer_memory_layer])

        path_symbol_qutline_tools = self.path_plugin + '/templates/qgis_templates/style_slope_dtm_tool_buffer_qgis0304.qml'
        buffer_memory_layer.loadNamedStyle(path_symbol_qutline_tools)
        buffer_memory_layer.updateExtents()
        buffer_memory_layer.triggerRepaint()
        self.iface.layerTreeView().refreshLayerSymbology(buffer_memory_layer.id())

        return buffer_memory_layer

    def generate_constant_slope_dtm(self,
                                    path_output_constant_slope_dtm_rlayer,
                                    rlayer_reference,
                                    qgsrect_slope_dtm,
                                    qgs_geometry_buffer,
                                    point_vector_layer):
        """
        """
        no_data_value = -9999

        pixel_size = self.mQgsDoubleSpinBox_pixelSize.value()
        x_min = qgsrect_slope_dtm.xMinimum()
        y_min = qgsrect_slope_dtm.yMinimum()
        x_max = qgsrect_slope_dtm.xMaximum()
        y_max = qgsrect_slope_dtm.yMaximum()

        # Create the destination data source
        cols = int((x_max - x_min) / pixel_size)
        rows = int((y_max - y_min) / pixel_size)

        path_rlayer_ref = rlayer_reference.dataProvider().dataSourceUri()  # existing raster reference filename
        ds = gdal.Open(path_rlayer_ref)  # open existing file
        proj = ds.GetProjection()
        # get a gdal driver to use for raster creation
        driver_tiff = gdal.GetDriverByName("GTiff")  # SEE: https://gdal.org/drivers/raster/index.html
        # create the new raster dataset
        outdata = driver_tiff.Create(path_output_constant_slope_dtm_rlayer,
                                     xsize=cols,
                                     ysize=rows,
                                     bands=1,
                                     eType=gdal.GDT_Float32,
                                     options=['COMPRESS = DEFLATE'])

        outdata.SetGeoTransform((x_min, pixel_size, 0, y_max, 0, -pixel_size))  # set the geotransform
        outdata.SetProjection(proj)  # set the projection
        outband = outdata.GetRasterBand(1)

        array_outband1 = outband.ReadAsArray()

        # xoffset, px_w, rot1, yoffset, px_h, rot2 = ds.GetGeoTransform()
        x0, px_w, rot1, y0, px_h, rot2 = outdata.GetGeoTransform()

        # genera lista de QgsPoints con coordenadas y altitudes de los puntos apoyo
        lst_qgspoints_linestring = []
        if self.mGroupBox_linestringVectorLayer.isChecked():
            str_height_field_name = CONTS_HEIGHT_FIELDNAME
        else:
            str_height_field_name = self.comboBox_heightFieldname.currentText()
        for feature in point_vector_layer.getFeatures():
            geom = feature.geometry()
            qgs_point = geom.asPoint()
            height = feature[str_height_field_name]
            if height >= 0:
                coor_x = qgs_point.x()
                coor_y = qgs_point.y()
                qgs_point = QgsPoint(coor_x,
                                     coor_y,
                                     height)
                lst_qgspoints_linestring.append(qgs_point)

        # initialize progress bar
        progress_message_bar = self.iface.messageBar().createMessage("Generate slope DTM progress")
        qlabel = QLabel()
        progress_message_bar.layout().addWidget(qlabel)
        progress = QProgressBar()
        default_style = "QProgressBar{" + "\n"
        default_style += "\ttext-align: center" + "\n"
        default_style += "}" + "\n"
        default_style += "QProgressBar::chunk {" + "\n"
        default_style += "\tbackground-color: green;"
        default_style += "\twidth: 10 px;"
        default_style += "\tmargin: 1 px;"
        default_style += "}" + "\n"
        progress.setStyleSheet(default_style)
        int_num_pixel = cols * rows
        progress.setMaximum(int_num_pixel)
        progress.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        progress_message_bar.layout().addWidget(progress)
        self.iface.messageBar().pushWidget(progress_message_bar,
                                           Qgis.Info)
        # initialize counters
        count_pixel = 0

        for col in range(cols):
            for row in range(rows):
                count_pixel += 1
                progress.setValue(count_pixel)

                current_coor_x = x0 + pixel_size * col
                current_coor_y = y0 - pixel_size * row
                current_qgspointxy_p = QgsPointXY(current_coor_x,
                                                  current_coor_y)
                geom_current_qgs_point = QgsGeometry.fromPointXY(current_qgspointxy_p)
                if geom_current_qgs_point.intersects(qgs_geometry_buffer):
                    value_height_interpolate = self.calculate_height_interpolate(QgsPoint(current_qgspointxy_p),
                                                                                 lst_qgspoints_linestring)
                    array_outband1[row][col] = value_height_interpolate
                else:
                    array_outband1[row][col] = no_data_value

        outband.WriteArray(array_outband1)
        outband.SetNoDataValue(no_data_value)
        outband.FlushCache()  # save to disk

        ds = None
        outdata = None
        outband = None

        # comprimir despues??
        # ds = gdal.Open(path_output_constant_slope_dtm_rlayer)
        # ds = gdal.Translate('c:/temporalc/output_slope_dtm_compress.tif', ds, options=['COMPRESS = DEFLATE'])
        # ds = None

        #TODO: Eliminar procesamientos anteriores?
        self.iface.addRasterLayer(path_output_constant_slope_dtm_rlayer)

    def generate_linestring_qgslayer_from_point_layer(self,
                                                      point_vector_layer):
        """
        """
        # remove previous proccessing
        layers = [layer for layer in QgsProject.instance().mapLayers().values()]
        for layer in layers:
            if layer.name() == CONST_AXIS_UNION_POINTS_LAYERNAME:
                QgsProject.instance().removeMapLayers([layer.id()])

        str_uri = 'Linestring?crs=epsg:%s&field=id:string(3)' % self.str_epsg_crs_project
        linestring_qgsvector_memory_layer = QgsVectorLayer(str_uri,
                                                           CONST_AXIS_UNION_POINTS_LAYERNAME,
                                                           "memory")

        dataprovider_linestring_qgsvector_layer = linestring_qgsvector_memory_layer.dataProvider()

        lst_qgspointsxy = []
        for current_feature_point in point_vector_layer.getFeatures():
            current_qgspointxy = current_feature_point.geometry().asPoint()
            lst_qgspointsxy.append(current_qgspointxy)

        feature_linestring = QgsFeature()
        feature_linestring.setGeometry(QgsGeometry.fromPolylineXY(lst_qgspointsxy))
        dataprovider_linestring_qgsvector_layer.addFeatures([feature_linestring])

        if self.radioButton_generateAxisUnionPointShp.isChecked():
            path_output_shapefile = self.lineEdit_pathOutputAxisUnionPointsShp.text()
            str_crs_epsg = "epsg:%s" % self.str_epsg_crs_project
            crs = QgsCoordinateReferenceSystem(str_crs_epsg)
            write_error = QgsVectorFileWriter.writeAsVectorFormat(linestring_qgsvector_memory_layer,
                                                                  path_output_shapefile,
                                                                  "UTF-8",
                                                                  crs,
                                                                  "ESRI Shapefile")

            linestring_qgsvector_layer = QgsVectorLayer(path_output_shapefile,
                                                        CONST_AXIS_UNION_POINTS_LAYERNAME,
                                                        "ogr")
        else:
            linestring_qgsvector_layer = linestring_qgsvector_memory_layer

        QgsProject.instance().addMapLayers([linestring_qgsvector_layer])

        path_symbol_qutline_tools = self.path_plugin + '/templates/qgis_templates/style_slope_dtm_tool_axis_union_points_qgis0304.qml'
        linestring_qgsvector_layer.loadNamedStyle(path_symbol_qutline_tools)
        linestring_qgsvector_layer.updateExtents()
        linestring_qgsvector_layer.triggerRepaint()
        self.iface.layerTreeView().refreshLayerSymbology(linestring_qgsvector_layer.id())

        return linestring_qgsvector_layer

    def generate_point_qgslayer_from_linestring_layer(self,
                                                      linestring_qgsvector_layer):
        # remove previous proccessing
        layers = [layer for layer in QgsProject.instance().mapLayers().values()]
        for layer in layers:
            if layer.name() == CONST_VERTEXS_LINESTRING_POINTS_LAYERNAME:
                QgsProject.instance().removeMapLayers([layer.id()])

        dtm_rlayer = self.mMapLayerComboBox_DTMlayer.currentLayer()
        qgsrect_dtm_layer = dtm_rlayer.extent()
        float_objects_average_height = self.mQgsDoubleSpinBox_objectAverageHeight.value()

        # get list vertex
        for current_feature in linestring_qgsvector_layer.getFeatures():
            current_geometry = current_feature.geometry()
            list_vertex_linestring = current_geometry.asPolyline()
            #FIXME: ojo que la capa no tenga varias linstring
            break

        # creación de la memory layer con su modelo de datos
        str_uri = 'Point?crs=epsg:%s' % self.str_epsg_crs_project
        point_qgsvector_memory_layer = QgsVectorLayer(str_uri,
                                                      CONST_VERTEXS_LINESTRING_POINTS_LAYERNAME,
                                                      "memory")
        dataprovider_point_qgsvector_memory_layer = point_qgsvector_memory_layer.dataProvider()

        point_qgsvector_memory_layer.startEditing()
        point_qgsvector_memory_layer.addAttribute(QgsField("id", QVariant.Int))
        point_qgsvector_memory_layer.addAttribute(QgsField(CONTS_HEIGHT_FIELDNAME, QVariant.Double))
        point_qgsvector_memory_layer.commitChanges()

        qgs_fields_point_qgsvector_memory_layer = point_qgsvector_memory_layer.fields()

        vertex_number = 0

        for current_qgs_pointxy in list_vertex_linestring:
            vertex_number += 1
            fet = QgsFeature()
            fet.setFields(qgs_fields_point_qgsvector_memory_layer, True)
            # cálculo de la altura interpolada
            if qgsrect_dtm_layer.contains(current_qgs_pointxy):
                fet["id"] = vertex_number
                fet.setGeometry(QgsGeometry.fromPointXY(current_qgs_pointxy))
                coor_x_feature = current_qgs_pointxy.x()
                coor_y_feature = current_qgs_pointxy.y()
                dtm_height_current_feature = self.q3_api_op.get_value_from_raster_file_interpolation(dtm_rlayer,
                                                                                                     coor_x_feature,
                                                                                                     coor_y_feature,
                                                                                                     int(self.str_epsg_crs_project))
                height_object_over = dtm_height_current_feature + float_objects_average_height
                fet[CONTS_HEIGHT_FIELDNAME] = height_object_over
                dataprovider_point_qgsvector_memory_layer.addFeatures([fet])

        point_qgsvector_memory_layer.reload()
        point_qgsvector_memory_layer.updateFields()
        point_qgsvector_memory_layer.updateExtents()
        QgsProject.instance().addMapLayers([point_qgsvector_memory_layer])

        return point_qgsvector_memory_layer

    def initialize(self):
        """
        Método inicialización
        """
        self.mMapLayerComboBox_pointVectorLayer.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.mMapLayerComboBox_pointVectorLayer.setShowCrs(True)

        self.mMapLayerComboBox_linestringVectorLayer.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.mMapLayerComboBox_linestringVectorLayer.setShowCrs(True)

        self.mMapLayerComboBox_DTMlayer.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.mMapLayerComboBox_DTMlayer.setShowCrs(True)

        self.fill_fieldnames_in_combo_height_fielnames()


    def initilize_signals_slots(self):
        """
        Connect signals / slots
        """
        self.mGroupBox_pointVectorLayer.clicked.connect(self.clicked_groupbox_point_vector_layer)
        self.mGroupBox_linestringVectorLayer.clicked.connect(self.clicked_groupbox_linestring_vector_layer)
        self.radioButton_generateAxisUnionPointShp.clicked.connect(self.clicked_radiobutton_generate_axis_union_point)
        self.toolButton_assignHeight.clicked.connect(self.assign_height_fieldname)
        self.toolButton_process.clicked.connect(self.process)
        self.mMapLayerComboBox_pointVectorLayer.currentIndexChanged.connect(self.fill_fieldnames_in_combo_height_fielnames)
        self.toolButton_searchPathOutputAxisUnionPointsShp.clicked.connect(self.search_path_ouput_axis_union_point_shp)
        self.toolButton_searchPathOutputSlopeDTMFile.clicked.connect(self.search_path_ouput_slope_dtm_file)

    def intersect_point_to_line(self,
                                qgspoint_p,
                                segment_start,
                                segment_end):
        segment_distance = segment_start.distance(segment_end)
        u = ((qgspoint_p.x() - segment_start.x()) *
             (segment_end.x() - segment_start.x()) + (qgspoint_p.y() - segment_start.y()) * (segment_end.y() - segment_start.y())) \
            / (segment_distance ** 2)

        # closest point does not fall within the line segment,
        # take the shorter distance to an endpoint
        if u < 0.00001 or u > 1:
            distance_p_x_segment_start = qgspoint_p.distance(segment_start)
            distance_p_x_segment_end = qgspoint_p.distance(segment_end)
            if distance_p_x_segment_start > distance_p_x_segment_end:
                return segment_end
            else:
                return segment_start
        else:
            coor_x_intersection_point = segment_start.x() + u * (segment_end.x() - segment_start.x())
            coor_y_intersection_point = segment_start.y() + u * (segment_end.y() - segment_start.y())
            return QgsPoint(coor_x_intersection_point,
                            coor_y_intersection_point)

    def process(self):
        """
        """
        # obtiene extension DTM layer
        dtm_rlayer = self.mMapLayerComboBox_DTMlayer.currentLayer()
        qgsrect_dtm_layer = dtm_rlayer.extent()
        # crs dtm_rlayer
        qgscrs_dtm_rlayer = dtm_rlayer.crs()
        self.str_epsg_crs_project = str(qgscrs_dtm_rlayer.postgisSrid())  # ej.: "25830"

        if self.mGroupBox_pointVectorLayer.isChecked():  # by point vector layer  ******************************
            # genera linestring que une los puntos
            current_point_vector_layer = self.mMapLayerComboBox_pointVectorLayer.currentLayer()
            linestring_qgslayer = self.generate_linestring_qgslayer_from_point_layer(current_point_vector_layer)

            # genera buffer memory layer
            buffer_memory_layer = self.generate_buffer_linestring_memory_layer(linestring_qgslayer,
                                                                               qgsrect_dtm_layer)
            # calcula huella dtm slope
            qgsrect_buffer_memory_layer = buffer_memory_layer.extent()
            #qgsrect_slope_dtm = qgsrect_buffer_memory_layer.intersect(qgsrect_dtm_layer)

            for feature_buffer in buffer_memory_layer.getFeatures():
                qgs_geometry_buffer = feature_buffer.geometry()

            path_output_constant_slope_dtm_rlayer = self.lineEdit_pathOutputSlopeDTMfile.text()

            # change raster values
            self.generate_constant_slope_dtm(path_output_constant_slope_dtm_rlayer,
                                             dtm_rlayer,
                                             qgsrect_buffer_memory_layer,
                                             qgs_geometry_buffer,
                                             current_point_vector_layer)

        if self.mGroupBox_linestringVectorLayer.isChecked():  # by linestring vector layer  ****************************
            # genera capa de puntos en los quiebros del linestring y les asigna altura
            linestring_qgslayer = self.mMapLayerComboBox_linestringVectorLayer.currentLayer()
            #FIXME: ojo que la capa no tenga varias linstring
            point_vector_layer = self.generate_point_qgslayer_from_linestring_layer(linestring_qgslayer)

            # genera buffer memory layer
            buffer_memory_layer = self.generate_buffer_linestring_memory_layer(linestring_qgslayer,
                                                                               qgsrect_dtm_layer)
            # calcula huella dtm slope
            qgsrect_buffer_memory_layer = buffer_memory_layer.extent()
            # qgsrect_slope_dtm = qgsrect_buffer_memory_layer.intersect(qgsrect_dtm_layer)

            for feature_buffer in buffer_memory_layer.getFeatures():
                qgs_geometry_buffer = feature_buffer.geometry()

            path_output_constant_slope_dtm_rlayer = self.lineEdit_pathOutputSlopeDTMfile.text()

            # change raster values
            self.generate_constant_slope_dtm(path_output_constant_slope_dtm_rlayer,
                                             dtm_rlayer,
                                             qgsrect_buffer_memory_layer,
                                             qgs_geometry_buffer,
                                             point_vector_layer)

        self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                            "Virtual slope DTM generated succesfully",
                                            Qgis.Info,
                                            10)

    def search_path_ouput_axis_union_point_shp(self):
        """
        Show dialog to select output axis union point shapefile
        """
        str_path_output_axis_union_point_shp, str_filter = QFileDialog.getSaveFileName(caption='Select output axis union point shapefile',
                                                                                       directory="c:/temporalc",
                                                                                       filter="Shapefile (*.shp)")
        if len(str_path_output_axis_union_point_shp) == 0:
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                'Select output axis union point shapefile',
                                                Qgis.Critical,
                                                10)
            self.lineEdit_pathOutputAxisUnionPointsShp.clear()
            return
        else:
            str_path_shp_normalize = os.path.normcase(str_path_output_axis_union_point_shp)
            self.lineEdit_pathOutputAxisUnionPointsShp.setText(str_path_shp_normalize)

    def search_path_ouput_slope_dtm_file(self):
        """
        Show dialog to select output dtm file
        """
        str_path_output_slope_dtm_file, str_filter = QFileDialog.getSaveFileName(caption='Select output slope DTM file',
                                                                                 directory="c:/temporalc",
                                                                                 filter="GeoTIF file (*.tif)")
        if len(str_path_output_slope_dtm_file) == 0:
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                'Select output slope DTM file',
                                                Qgis.Critical,
                                                10)
            self.lineEdit_pathOutputSlopeDTMfile.clear()
            return
        else:
            str_path_dtm_normalize = os.path.normcase(str_path_output_slope_dtm_file)
            self.lineEdit_pathOutputSlopeDTMfile.setText(str_path_dtm_normalize)

    def ui_set_default_values_from_qsettings(self):
        """
        Establece los últimos valores introducidos en un procesamiento anterior recopilados del fichero qsetings.ini
        """
        pass