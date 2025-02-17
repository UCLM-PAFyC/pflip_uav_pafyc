# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PflipUav3
                                 A QGIS plugin
 Photogrammetric and Remote Sensing Flight Planning for unmanned aerial vehicle
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-08-23
        git sha              : $Format:%H$
        copyright            : (C) 2019 by David Hernández López, PAFYC-UCLM
        email                : david.hernandez@uclm.es
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

#SEE: https://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/composer.html
#SEE: https://data.library.virginia.edu/how-to-create-and-export-print-layouts-in-python-for-qgis-3/
#SEE: https://github.com/epurpur/PyQGIS-Scripts/blob/master/CreateLayoutManagerAndExport.py
#SEE: https://doc.qt.io/qt-5/graphicsview.html
#SEE: https://github.com/qgis/QGIS/blob/master/tests/src/python/test_qgslayoutmapgrid.py

# Import PyQt5 classes
from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QFont, QPolygonF, QColor, QPainter

# Import the QGIS libraries
from qgis.core import (QgsProject, QgsPrintLayout, QgsLayoutPoint, QgsLayoutItemLabel, QgsLayoutItemMap,
                       QgsLayoutItemLegend, QgsLayoutItemPolygon,QgsFillSymbol,QgsLayoutItemScaleBar, QgsUnitTypes,
                       QgsLayoutSize, QgsLayoutExporter, QgsLayoutItemPicture, QgsLayoutItemMapGrid, QgsLayoutItemPage,
                       QgsLegendStyle)

class PrintLayout():
    #TODOC:
    def __init__(self,
                 iface,
                 layout_name):
        #TODOC:
        self.iface = iface
        self.layout = self.create_layout(layout_name)

    def add_label_layout_item(self,
                              str_text,
                              qfont,
                              origin_x_mm,
                              origin_y_mm,
                              width_mm,
                              height_mm,
                              h_align,
                              v_align,
                              is_frame_enabled=True,
                              background_qcolor=None,
                              font_color=None,
                              int_page=-1):
        #TODOC:
        qgs_layout_item = QgsLayoutItemLabel(self.layout)
        qgs_layout_item.setText(str_text)
        qgs_layout_item.setFont(qfont)
        self.layout.addLayoutItem(qgs_layout_item)
        qgs_layout_item.attemptMove(QgsLayoutPoint(origin_x_mm, origin_y_mm),
                                    page=int_page)
        if width_mm > 0:
            qgs_layout_size = QgsLayoutSize(width_mm, height_mm)
            qgs_layout_item.setFixedSize(qgs_layout_size)
        else:
            qgs_layout_item.adjustSizeToText()
        qgs_layout_item.setHAlign(h_align)
        qgs_layout_item.setVAlign(v_align)
        if is_frame_enabled: qgs_layout_item.setFrameEnabled(True)  #  frame is drawn around each item by default. You can remove it as follows
        if background_qcolor is not None:
            qgs_layout_item.setBackgroundEnabled(True)
            qgs_layout_item.setBackgroundColor(background_qcolor)
        if font_color is not None:
            qgs_layout_item.setFontColor(font_color)

    def add_legend_layout_item(self,
                               qgslayoutitemmap_linked,
                               str_legend_title,
                               legend_origin_x_mm,
                               legend_origin_y_mm,
                               qfont_title,
                               qfont_group,
                               qfont_subgroup,
                               qfont_symbollabel,
                               float_line_spacing,
                               int_page=-1):
        #TODOC:
        map = QgsLayoutItemMap(self.layout)
        legend = QgsLayoutItemLegend(self.layout)
        legend.setLinkedMap(qgslayoutitemmap_linked) # map is an instance of QgsLayoutItemMap

        legend.attemptMove(QgsLayoutPoint(legend_origin_x_mm, legend_origin_y_mm),
                           page=int_page)
        legend.setTitle(str_legend_title)

        legend.setStyleFont(QgsLegendStyle.Title,
                            qfont_title)
        legend.setStyleFont(QgsLegendStyle.Group,
                            qfont_group)
        legend.setStyleFont(QgsLegendStyle.Subgroup,
                            qfont_subgroup)
        legend.setStyleFont(QgsLegendStyle.SymbolLabel,
                            qfont_symbollabel)
        legend.setLineSpacing(2.0)

        self.layout.addItem(legend)

    def add_map_layout_item(self,
                            list_maplayers,
                            qgs_rectangle,
                            origin_x_mm,
                            origin_y_mm,
                            width_mm,
                            height_mm,
                            float_scale,
                            int_page=-1):
        """This adds a map item to the Print Layout"""
        # intialize the map object,
        map = QgsLayoutItemMap(self.layout)

        # Attempts to update the item's position and size to match the passed rect in layout coordinates.
        # If includesFrame is true, then the position and size specified by rect represents the position and size at for the outside of the item's frame.
        # Note that the final position and size of the item may not match the specified target rect, as data defined item position and size may override the specified value.
        map.attemptSetSceneRect(QRectF(origin_x_mm, origin_y_mm, width_mm, height_mm))
        map.setFrameEnabled(True)

        if list_maplayers != None:
            map.setLayers(list_maplayers)
            #map.setLayers(self.project.mapThemeCollection().masterVisibleLayers())  # remember ANNOTATION!
            # Sets whether the stored layer set should be used or the current layer set of the associated project.
            # This is just a GUI flag, and itself does not change which layers are rendered in the map. Instead, use setLayers() to control which layers are rendered.
        map.setKeepLayerSet(True)
        map.setExtent(qgs_rectangle)
        self.iface.mapCanvas().freeze(True)

        # Amplía el mapa para que la extensión especificada sea ​​completamente visible dentro del elemento del mapa.
        # Este método no cambiará el ancho o la altura del mapa, y puede resultar en una superposición o margen de la extensión especificada.
        # Este método altera implícitamente la escala del mapa.
        map.zoomToExtent(qgs_rectangle)
        if float_scale is not None:
            map.setScale(float_scale)

        self.iface.mapCanvas().freeze(False)
        self.iface.mapCanvas().refresh()

        # Move & Resize
        map.attemptMove(QgsLayoutPoint(origin_x_mm, origin_y_mm),
                        page=int_page)
        map.attemptResize(QgsLayoutSize(width_mm, height_mm))

        self.layout.addLayoutItem(map)
        return map

    def add_map_grid_layout_item(self,
                                 map,
                                 grid_interval):
        #TODOC:

        # create a grid for a map
        map.grid().setEnabled(True)  # Enables a coordinate grid that is shown on top of this composermap
        map.grid().setIntervalX(grid_interval)  # Sets coordinate interval in x-direction for composergrid
        map.grid().setIntervalY(grid_interval)  # Sets coordinate interval in y-direction for composergrid
        map.grid().setAnnotationEnabled(True)  # Sets flag if grid annotation should be shown
        map.grid().setGridLineColor(QColor(0, 176, 246))  # Sets the color of the grid pen
        map.grid().setGridLineWidth(0.5)
        map.grid().setAnnotationPrecision(0)  # Sets coordinate precision for grid annotations
        map.grid().setAnnotationFrameDistance(1)  # Sets distance between map frame and annotations
        map.grid().setAnnotationFontColor(QColor(0, 0, 0))  # Sets font color for grid annotations

        map.grid().setAnnotationDisplay(QgsLayoutItemMapGrid.HideAll, QgsLayoutItemMapGrid.Right)

        map.grid().setAnnotationDisplay(QgsLayoutItemMapGrid.HideAll, QgsLayoutItemMapGrid.Top)

        map.grid().setAnnotationPosition(QgsLayoutItemMapGrid.OutsideMapFrame, QgsLayoutItemMapGrid.Bottom)
        map.grid().setAnnotationDirection(QgsLayoutItemMapGrid.Horizontal, QgsLayoutItemMapGrid.Bottom)

        map.grid().setAnnotationPosition(QgsLayoutItemMapGrid.OutsideMapFrame, QgsLayoutItemMapGrid.Left)
        map.grid().setAnnotationDirection(QgsLayoutItemMapGrid.Vertical, QgsLayoutItemMapGrid.Left)

        # frame
        map.grid().setFrameStyle(QgsLayoutItemMapGrid.Zebra)  # Set grid frame style (NoGridFrame or Zebra)
        map.grid().setFrameWidth(1.5)  # Set grid frame width
        map.grid().setFramePenSize(0.1)  # Sets width of grid pen
        map.grid().setBlendMode(QPainter.CompositionMode_SourceOver)

        # cross grid
        map.grid().setStyle(QgsLayoutItemMapGrid.Cross)  # Sets coordinate grid style to solid or cross
        map.grid().setCrossLength(1.0)  # Sets length of the cross segments (if grid style is cross)
        map.grid().setGridLineWidth(0.1)
        map.grid().setGridLineColor(QColor(0, 176, 246))  # Sets the color of the grid pen
        map.grid().setBlendMode(QPainter.CompositionMode_SourceOver)

        # Updates the bounding rect of this item
        # Call this function before doing any changes related to annotation out of the map rectangle
        map.updateBoundingRect()

    def add_nodes_based_shape_layout_item(self,
                                          props,
                                          origin_x_mm,
                                          origin_y_mm,
                                          width_mm,
                                          height_mm,
                                          int_page=-1):
        #TODOC:
        polygon = QPolygonF()
        polygon.append(QPointF(origin_x_mm, origin_y_mm))
        polygon.append(QPointF(origin_x_mm + width_mm, origin_y_mm))
        polygon.append(QPointF(origin_x_mm + width_mm, origin_y_mm + height_mm))
        polygon.append(QPointF(origin_x_mm, origin_y_mm + height_mm))
        polygon_item = QgsLayoutItemPolygon(polygon, self.layout)
        polygon_item.attemptMove(QgsLayoutPoint(origin_x_mm, origin_y_mm),
                                 page=int_page)
        symbol = QgsFillSymbol.createSimple(props)
        polygon_item.setSymbol(symbol)
        self.layout.addItem(polygon_item)

    def add_picture_layout_item(self,
                                str_path,
                                origin_x_mm,
                                origin_y_mm,
                                width_mm,
                                height_mm,
                                resize_mode,
                                int_page=-1):
        #TODOC:
        picture = QgsLayoutItemPicture(self.layout)  # initialize the picture object
        picture.setPicturePath(str_path)  # set the path of the picture to our image file
        picture.attemptMove(QgsLayoutPoint(origin_x_mm,
                                           origin_y_mm),
                            page=int_page)
        qgs_layout_size = QgsLayoutSize(width_mm, height_mm)
        picture.setFixedSize(qgs_layout_size)
        picture.setResizeMode(resize_mode)  # Sets the resize mode used for drawing the picture within the item bounds
        self.layout.addItem(picture)  # add the logo to the map compisition

    def add_scale_bar_layout_item(self,
                                  int_page=-1):
        #TODOC:
        map = QgsLayoutItemMap(self.layout)
        item = QgsLayoutItemScaleBar(self.layout)
        item.setStyle('Numeric')  # optionally modify the style
        item.setLinkedMap(map)  # map is an instance of QgsLayoutItemMap
        item.applyDefaultSize()
        self.layout.addItem(item)
        item.attemptMove(QgsLayoutPoint(100,100),
                         page=int_page)

    def add_table_layout_item(self):
        #TODOC:
        """
        item.attemptMove(QgsLayoutPoint(1.4, 1.8, QgsUnitTypes.LayoutCentimeters))
        item.attemptResize(QgsLayoutSize(2.8, 2.2, QgsUnitTypes.LayoutCentimeters))
        """
        pass

    def create_layout(self,
                      layout_name):
        #TODOC: initialize new print layout

        """This creates a new print layout"""
        self.project = QgsProject.instance()  # gets a reference to the project instance
        manager = self.project.layoutManager()  # gets a reference to the layout manager

        # remove previous layout with the same layout_name
        layouts_list = manager.printLayouts()
        for layout in layouts_list:
            if layout.name() == layout_name:
                manager.removeLayout(layout)

        layout = QgsPrintLayout(self.project)  # makes a new print layout object, takes a QgsProject as argument
        layout.initializeDefaults()  # Initializes an empty layout
        layout.setUnits(QgsUnitTypes.LayoutMillimeters)
        layout.setName(layout_name)
        qgs_layout_page_collection = layout.pageCollection()  # returns a pointer to the layout's page collection, which stores and manages page items in the layout
        page_1 = qgs_layout_page_collection.pages()[0]
        page_1.setPageSize('A3',
                           QgsLayoutItemPage.Landscape)
        manager.addLayout(layout)
        return layout

    def export(self,
               layout_name,
               path_file_pdf_output):
        #TODOC:
        """This exports a Print Layout as an image"""
        manager = QgsProject.instance().layoutManager()  # this is a reference to the layout Manager, which contains a list of print layouts
        layout = manager.layoutByName(layout_name)  # this accesses a specific layout, by name (which is a string)
        exporter = QgsLayoutExporter(layout)  # this creates a QgsLayoutExporter object
        exporter.exportToPdf(path_file_pdf_output,
                             QgsLayoutExporter.PdfExportSettings())  # this exports a pdf of the layout object

    def format_qfont(self,
                     str_fuente="Calibri",
                     int_size=10,
                     is_bold=False,
                     is_italic=False):
        #TODOC:

        qfont = QFont(str_fuente,
                      int_size)
        if is_bold: qfont.setBold(True)
        if is_italic: qfont.setItalic(True)
        return qfont