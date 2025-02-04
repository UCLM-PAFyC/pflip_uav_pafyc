# -*- coding: utf-8 -*-
"""
/***************************************************************************
    PFliP-UAV
        Módulo:     qutline_dlg.py
        Inicio:     2019-10-03
        Autor:
        Email:
 ***************************************************************************/
"""
# Import PyQt5 classes
from PyQt5 import uic
from PyQt5.QtCore import QVariant
from PyQt5.QtWidgets import QDialog, QApplication

# Import PyQGIS classes
from qgis.core import (Qgis, QgsProject, QgsMapLayerProxyModel, QgsPoint, QgsPointXY, QgsFeature, QgsGeometry,
                       QgsVectorLayer, QgsField, QgsFields, QgsDataSourceUri)
from qgis.gui import QgsMapToolEmitPoint

# Import Python classes
import os
import sys
import math

# import self classes
from .. import config as c  # constants

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
sys.path.append(os.path.dirname(__file__))
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__),
                                            'qutline_dlg.ui'),
                               resource_suffix='')

CONST_QUTLINE_POINTS_LAYERNAME = 'Qutline points'

class QutlineTool(QDialog,
                  FORM_CLASS):
    def __init__(self,
                 iface,
                 my_qsettings,
                 cod_flight_block,
                 path_plugin,
                 path_db_project,
                 str_epsg_crs_project,
                 parent=None):
        """Constructor"""
        self.iface = iface
        self.my_qsettings = my_qsettings
        self.cod_flight_block = cod_flight_block
        self.path_plugin = path_plugin
        self.path_db_project = path_db_project
        self.str_epsg_crs_project = str_epsg_crs_project

        self.qgs_mapcanvas = self.iface.mapCanvas()

        super(QutlineTool, self).__init__(parent)
        self.setupUi(self)

        self.initialize()
        self.initilize_signals_slots()

    def calc_dimensions_segmentation(self):
        """
        """
        line_layer_to_cut = self.mMapLayerComboBox_layerToTrim.currentLayer()
        selected_features = line_layer_to_cut.selectedFeatures()
        num_features_selected = len(selected_features)
        if  num_features_selected == 0:  # ningún eje seleccionado
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                "Qutline: Select an axis",
                                                Qgis.Critical,
                                                20)
            return

        if num_features_selected >= 2:  # más de dos features seleccionadas
            str_msg = "Qutline: " + str(num_features_selected) + " features selected"
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                str_msg,
                                                Qgis.Critical,
                                                20)
            return

        # cálculo de la longitud total del eje seleccionado
        qgs_geometry_selected_feature = selected_features[0].geometry()
        length_selected_feature = qgs_geometry_selected_feature.length()
        str_length_selected_feature = "%.1f" % length_selected_feature
        self.lineEdit_lengthSelectedFeatureCalculated.setText(str_length_selected_feature)

        segment_fixed_distance = self.mQgsDoubleSpinBox_fixedDistance.value()
        number_of_segments_calculated = length_selected_feature / segment_fixed_distance
        int_number_of_segments_calculated = int(number_of_segments_calculated)
        int_number_of_segments = int_number_of_segments_calculated + 1
        residuo = length_selected_feature - int_number_of_segments_calculated * segment_fixed_distance
        str_number_of_segments_calculated = "%s (%s of %.1f m / residue %.1f m)" % (str(int_number_of_segments), str(int_number_of_segments_calculated), segment_fixed_distance, residuo)
        self.lineEdit_numberOfSegmentsCalculated.setText(str_number_of_segments_calculated)

        number_of_segments = self.mQgsSpinBox_numberOfSegments.value()
        segment_length_calculated = length_selected_feature / number_of_segments
        str_segment_length_calculated = "%.1f" % segment_length_calculated
        self.lineEdit_segmentLengthCalculated.setText(str(str_segment_length_calculated))

    def clicked_groupbox_fixed_distance(self):
        """
        Habilita / deshabilita resto de groupbox
        """
        if self.mGroupBox_byFixedDistance.isChecked():
            self.mGroupBox_byNumberOfSegments.setChecked(False)

    def clicked_groupbox_number_segments(self):
        """
        Habilita / deshabilita resto de groupbox
        """
        if self.mGroupBox_byNumberOfSegments.isChecked():
            self.mGroupBox_byFixedDistance.setChecked(False)

    def generate_cut_points_layer(self,
                                  length_segment,
                                  length_selected_feature,
                                  qgs_geometry_selected_feature):
        """
        Genera capa de puntos de corte
        """
        # remove previous proccessing
        layers = [layer for layer in QgsProject.instance().mapLayers().values()]
        for layer in layers:
            if layer.name() == CONST_QUTLINE_POINTS_LAYERNAME:
                QgsProject.instance().removeMapLayers([layer.id()])

        m_puntos = []
        str_uri = "Point?crs=epsg:%s&field=id:string(3)" % (self.str_epsg_crs_project)
        layer_puntos = QgsVectorLayer(str_uri,
                                      CONST_QUTLINE_POINTS_LAYERNAME,
                                      "memory")
        dist_acumulada = 0

        while dist_acumulada <= length_selected_feature:
            vertice_corte = qgs_geometry_selected_feature.interpolate(dist_acumulada).asPoint()
            m_puntos.append(vertice_corte)
            dist_acumulada = dist_acumulada + length_segment

        vertice_corte = qgs_geometry_selected_feature.interpolate(length_selected_feature).asPoint()  # añade el ultimo punto
        m_puntos.append(vertice_corte)
        for j in range(len(m_puntos)):
            vpr = layer_puntos.dataProvider()
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(m_puntos[j])))
            vpr.addFeatures([f])

        QgsProject.instance().addMapLayers([layer_puntos])
        path_symbol_qutline_tools = self.path_plugin + '/templates/qgis_templates/style_qutline_points_qgis0304.qml'
        layer_puntos.loadNamedStyle(path_symbol_qutline_tools)
        layer_puntos.updateExtents()
        layer_puntos.triggerRepaint()
        self.iface.layerTreeView().refreshLayerSymbology(layer_puntos.id())
        layer_puntos.updateExtents()
        if self.mGroupBox_generateTofLndPoints.isChecked():
            self.generate_tof_lnd_point(m_puntos)

    def generate_tof_lnd_point(self,
                               lst_cut_qgspoints_xy):
        """

        """
        offset_distance = self.mQgsDoubleSpinBox_offsetDistance.value()
        uri = QgsDataSourceUri()
        uri.setDatabase(self.path_db_project)
        schema = ""
        geom_column = "the_geom"

        # qgsvector layer tof point
        table = c.CONST_PFLIPUAV_LAYER_TAKEOFF_POINT
        uri.setDataSource(schema, table, geom_column)
        qgsvectorlayer_tof_points = QgsVectorLayer(uri.uri(),
                                                   table,
                                                   'spatialite')
        provider_qgsvectorlayer_tof_points = qgsvectorlayer_tof_points.dataProvider()
        qgsfields_tof_layer = qgsvectorlayer_tof_points.fields()
        qgsfeature_tof_point = QgsFeature()
        qgsfeature_tof_point.setFields(qgsfields_tof_layer,
                                       True)

        # qgsvector layer landing point
        table = c.CONST_PFLIPUAV_LAYER_LANDING_POINT
        uri.setDataSource(schema, table, geom_column)
        qgsvectorlayer_landing_points = QgsVectorLayer(uri.uri(),
                                                       table,
                                                       'spatialite')
        provider_qgsvectorlayer_landing_points = qgsvectorlayer_landing_points.dataProvider()
        qgsfields_landing_layer = qgsvectorlayer_landing_points.fields()
        qgsfeature_lnd_point = QgsFeature()
        qgsfeature_lnd_point.setFields(qgsfields_landing_layer,
                                       True)

        # initialize counters
        num_stations = len(lst_cut_qgspoints_xy)
        cont_station = 0

        for current_station in lst_cut_qgspoints_xy:
            x_coor_cut_point = current_station.x()
            y_coor_cut_point = current_station.y()
            if self.radioButton_allStations.isChecked():
                if cont_station < num_stations-1:
                    new_tof_qgspointxy = QgsPointXY(x_coor_cut_point - offset_distance,
                                                    y_coor_cut_point)
                    new_geom_tof_point = QgsGeometry.fromPointXY(new_tof_qgspointxy)
                    qgsfeature_tof_point.setGeometry(new_geom_tof_point)
                    provider_qgsvectorlayer_tof_points.addFeatures([qgsfeature_tof_point])

                if cont_station > 0:
                    new_lnd_qgspointxy = QgsPointXY(x_coor_cut_point + offset_distance,
                                                    y_coor_cut_point)
                    new_geom_lnd_point = QgsGeometry.fromPointXY(new_lnd_qgspointxy)
                    qgsfeature_lnd_point.setGeometry(new_geom_lnd_point)
                    provider_qgsvectorlayer_landing_points.addFeatures([qgsfeature_lnd_point])

            if self.radioButton_altenativeStations.isChecked():
                if cont_station % 2 != 0:
                    new_tof_qgspointxy = QgsPointXY(x_coor_cut_point - offset_distance,
                                                    y_coor_cut_point)
                    new_geom_tof_point = QgsGeometry.fromPointXY(new_tof_qgspointxy)
                    qgsfeature_tof_point.setGeometry(new_geom_tof_point)
                    provider_qgsvectorlayer_tof_points.addFeatures([qgsfeature_tof_point])

                    new_lnd_qgspointxy = QgsPointXY(x_coor_cut_point + offset_distance,
                                                    y_coor_cut_point)
                    new_geom_lnd_point = QgsGeometry.fromPointXY(new_lnd_qgspointxy)
                    qgsfeature_lnd_point.setGeometry(new_geom_lnd_point)
                    provider_qgsvectorlayer_landing_points.addFeatures([qgsfeature_lnd_point])

            cont_station += 1

        # reload & update vector layers
        qgsvectorlayer_tof_points.reload()
        qgsvectorlayer_tof_points.updateFields()
        qgsvectorlayer_tof_points.updateExtents()

        qgsvectorlayer_landing_points.reload()
        qgsvectorlayer_landing_points.updateFields()
        qgsvectorlayer_landing_points.updateExtents()

    def initialize(self):
        """
        Método inicialización
        """
        self.mMapLayerComboBox_layerToTrim.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.mMapLayerComboBox_layerToTrim.setShowCrs(True)

        self.click_maptool = QgsMapToolEmitPoint(self.qgs_mapcanvas)
        self.click_maptool.canvasClicked.connect(self.select_feature_maptool)
        self.qgs_mapcanvas.setMapTool(self.click_maptool)

    def initilize_signals_slots(self):
        """
        Connect signals / slots
        """
        self.mGroupBox_byFixedDistance.clicked.connect(self.clicked_groupbox_fixed_distance)
        self.mGroupBox_byNumberOfSegments.clicked.connect(self.clicked_groupbox_number_segments)
        self.toolButton_ViewTableLayerToTrim.clicked.connect(self.view_table_layer_to_trim)
        self.toolButton_calcDimesionsSegmentation.clicked.connect(self.calc_dimensions_segmentation)
        self.toolButton_process.clicked.connect(self.process)

    def open_manual_help(self):
        """
        Brief: Abre el manual de usuario
        """
        str_path_manual = os.path.normcase(self.plugin_dir + "\\" + c.CONST_STR_USER_MANUAL_SUBDIRECTORY + "\\" + c.CONST_STR_USER_MANUAL_FILENAME)
        os.startfile(str_path_manual)

    def process(self):
        """
        """
        line_layer_to_cut = self.mMapLayerComboBox_layerToTrim.currentLayer()
        selected_features = line_layer_to_cut.selectedFeatures()
        provider_line_layer_to_cut = line_layer_to_cut.dataProvider()
        num_features_selected = len(selected_features)
        if  num_features_selected == 0:  # ningún eje seleccionado
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                "Qutline: Select an axis",
                                                Qgis.Critical,
                                                20)
            return

        if num_features_selected >= 2:  # más de dos features seleccionadas
            str_msg = "Qutline: " + str(num_features_selected) + " features selected"
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                str_msg,
                                                Qgis.Critical,
                                                20)
            return

        str_id_c_axis = selected_features[0]['id_c_axis']
        # cálculo de la longitud total del eje seleccionado
        qgs_geometry_selected_feature = selected_features[0].geometry()
        length_selected_feature = qgs_geometry_selected_feature.length()

        if self.mGroupBox_byFixedDistance.isChecked():  # by fixed distance  *******************************************
            fixed_distance = self.mQgsDoubleSpinBox_fixedDistance.value()
            if fixed_distance >= length_selected_feature:
                str_msg = "Qutline: The length of the established section is greater than that of the selected feature"
                self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                    str_msg,
                                                    Qgis.Critical,
                                                    20)
                return

            # inicialización variables para recorrer la geometria del eje vertice a vertice
            length_divisions = fixed_distance
            index_vertex = 0
            qgspoint_vertex = qgs_geometry_selected_feature.vertexAt(0)  # return QgsPoint del primer vértice del eje
            qgspoint_previous_vertex = qgspoint_vertex
            accumulated_distance = 0.0
            lst_qgspoints = []
            lst_lines = []
            cut = length_divisions
            while qgspoint_vertex != QgsPoint(0, 0) and not qgspoint_vertex.isEmpty():
                accumulated_distance += math.sqrt(qgspoint_vertex.distanceSquared(qgspoint_previous_vertex))
                if (accumulated_distance < cut):
                    lst_qgspoints.append(qgspoint_vertex)
                else:
                    # Get an interpolated point on the geometry at the specified distance. Returns QgsGeometry
                    qgsgeometry_cut_vertex = qgs_geometry_selected_feature.interpolate(cut)
                    # Get the contents of the geometry as a 2-dimensional point. Return QgsPointXY
                    qgspointxy_cut_vertex = qgsgeometry_cut_vertex.asPoint()
                    qgspoint_cut_vertex = QgsPoint(qgspointxy_cut_vertex)
                    lst_qgspoints.append(qgspoint_cut_vertex)
                    lst_lines.append(lst_qgspoints)
                    lst_qgspoints = []
                    lst_qgspoints.append(qgspoint_cut_vertex)
                    index_vertex -= 1
                    cut += length_divisions
                qgspoint_previous_vertex = qgspoint_vertex
                index_vertex += 1
                qgspoint_vertex = qgs_geometry_selected_feature.vertexAt(index_vertex)  # return QgsPoint de un vértice

            # línea tramo final
            lst_lines.append(lst_qgspoints)

        if self.mGroupBox_byNumberOfSegments.isChecked():  # by number of segments  ************************************
            number_of_segments = self.mQgsSpinBox_numberOfSegments.value()
            # Inicializamos las variabales para recorrer la geometria vertice a vertice
            length_divisions = qgs_geometry_selected_feature.length() / number_of_segments
            index_vertex = 0
            qgspoint_vertex = qgs_geometry_selected_feature.vertexAt(0)
            qgspoint_previous_vertex = qgspoint_vertex
            accumulated_distance = 0
            lst_qgspoints = []
            lst_lines = []
            cut = length_divisions

            while qgspoint_vertex != QgsPoint(0, 0):
                accumulated_distance = accumulated_distance + math.sqrt(qgspoint_vertex.distanceSquared(qgspoint_previous_vertex))
                if (accumulated_distance < cut):
                    lst_qgspoints.append(qgspoint_vertex)
                else:
                    # Get an interpolated point on the geometry at the specified distance. Returns QgsGeometry
                    qgsgeometry_cut_vertex = qgs_geometry_selected_feature.interpolate(cut)
                    # Get the contents of the geometry as a 2-dimensional point. Return QgsPointXY
                    qgspointxy_cut_vertex = qgsgeometry_cut_vertex.asPoint()
                    qgspoint_cut_vertex = QgsPoint(qgspointxy_cut_vertex)
                    lst_qgspoints.append(qgspoint_cut_vertex)
                    lst_lines.append(lst_qgspoints)
                    lst_qgspoints = []
                    lst_qgspoints.append(qgspoint_cut_vertex)
                    index_vertex -= 1
                    cut += length_divisions
                qgspoint_previous_vertex = qgspoint_vertex
                index_vertex += 1
                qgspoint_vertex = qgs_geometry_selected_feature.vertexAt(index_vertex)

        # Add segments to original layer
        qgsfields_axis_layer = line_layer_to_cut.fields()
        qgsfeature_segment = QgsFeature()
        qgsfeature_segment.setFields(qgsfields_axis_layer,
                                     True)
        count_segment = 1
        for plinea in lst_lines:
            line_start = plinea[0]
            line_end = plinea[len(plinea) - 1]
            new_geom = QgsGeometry.fromPolyline([line_start, line_end])
            for lpunto in range(1, len(plinea) - 1):
                new_geom.insertVertex(plinea[lpunto].x(), plinea[lpunto].y(), lpunto)
            qgsfeature_segment.setGeometry(new_geom)
            str_cod_segment = self.cod_flight_block + "#" + str(str_id_c_axis) + "#" + str(count_segment)
            # qgsfeature_segment['id_c_axis'] = count_segment
            qgsfeature_segment['cod_segment'] = str_cod_segment
            count_segment += 1
            provider_line_layer_to_cut.addFeatures([qgsfeature_segment])

        """
        line_layer_to_cut.startEditing()
        features = line_layer_to_cut.getFeatures()

        count_segment = 1
        for current_features in features:
            # longitudfd = feature_c.geometry().length()
            # feature_c['Longitud'] = longitudfd
            # feature_c['FID'] = feature_c.id()
            str_cod_segment = self.cod_flight_block + "#" + str(str_id_c_axis) + "#" + str(count_segment)
            current_features['cod_segment'] = str_cod_segment
            line_layer_to_cut.updateFeature(current_features)
            count_segment += 1

        line_layer_to_cut.commitChanges()
        """
        line_layer_to_cut.startEditing()
        line_layer_to_cut.commitChanges()

        line_layer_to_cut.reload()
        line_layer_to_cut.updateFields()
        line_layer_to_cut.updateExtents()

        self.generate_cut_points_layer(length_divisions,
                                       length_selected_feature,
                                       qgs_geometry_selected_feature)

        self.view_table_layer_to_trim()

        self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                            "Qutline: Segmentation finished",
                                            Qgis.Info,
                                            10)

    def select_feature_maptool(self,
                               point):
        # cada vez que seleccione una nueva capa se borra la selección
        for layer in self.qgs_mapcanvas.layers():
            if layer.type() == layer.VectorLayer:
                layer.removeSelection()
        self.qgs_mapcanvas.refresh()

        qgsgeometry_point = QgsGeometry.fromPointXY(point)
        gqsgeometry_point_buffer = qgsgeometry_point.buffer((self.qgs_mapcanvas.mapUnitsPerPixel()*2),
                                                            0)
        qrect_gqsgeometry_point_buffer = gqsgeometry_point_buffer.boundingBox()
        line_layer_to_cut = self.mMapLayerComboBox_layerToTrim.currentLayer()
        line_layer_to_cut.removeSelection()
        line_layer_to_cut.selectByRect(qrect_gqsgeometry_point_buffer,
                                       False)
        selected_features = line_layer_to_cut.selectedFeatures()
        num_features_selected = len(selected_features)
        if num_features_selected >= 2:  # más de dos features seleccionadas
            str_msg = "Qutline: " + str(num_features_selected) + " features selected"
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                str_msg,
                                                Qgis.Warning,
                                                20)

    def ui_set_default_values_from_qsettings(self):
        """
        Establece los últimos valores introducidos en un procesamiento anterior recopilados del fichero qsetings.ini
        """
        pass

    def view_table_layer_to_trim(self):
        """
        """
        vl = self.mMapLayerComboBox_layerToTrim.currentLayer()

        """
        widgets = QApplication.instance().allWidgets()
        attrTables = [d for d in widgets if
                      d.objectName() == u'QgsAttributeTableDialog' or d.objectName() == u'AttributeTable']
        for x in attrTables:
            if vl.name() in x.windowTitle():
                x.close()
        """
        self.iface.showAttributeTable(vl)