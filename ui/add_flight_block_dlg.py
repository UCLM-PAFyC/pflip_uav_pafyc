# -*- coding: utf-8 -*-

# Import PyQt5 classes
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtGui import (QIcon)

# import PyQGIS classes
from qgis.core import Qgis

# Import Python classes
import os

#others imports
from .. classes.db_operations import *

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
import sys
sys.path.append(os.path.dirname(__file__))
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__),
                                            'add_flight_block_dlg.ui'),
                               resource_suffix='')

class addFlightBlockDlg(QtWidgets.QDialog,
                        FORM_CLASS):
    """
    brief: Clase diálogo para matriculación un proyecto de vuelo
    param[in]: ruta del proyecto captura en el diálogo anterior
    param[in]: referencia al QGIS interface
    param[in]: int_photogrammetric_mission_type. Posibles valores [0] - nuevo bloque de vuelo. [1] - copia de vuelo lineal [2] - copia de vuelo zonal
    """
    def __init__(self,
                 iface,
                 lst_flight_block_dlg,
                 path_db_project,
                 int_photogrammetric_mission_type,
                 parent=None):
        """
        brief: función de inicialización
        """
        super(addFlightBlockDlg, self).__init__(parent)
        
        self.lst_flight_block_dlg = lst_flight_block_dlg # contenedor lista para almacenar parámetros tras salvar valores introducidos en el panel de código de bloque de vuelo
        self.iface = iface # Save reference to the QGIS interface
        
        self.path_db_project = path_db_project
        
        self.db_op = DbOperations(self.iface)  # new db operations
        
        # Set up the user interface from Designer.
        self.setupUi(self)
        
        # habilitamos combobox dependiendo de si se esta abriendo un nuevo bloque de vuelo o se está copiando
        self.dictionary_flight_type = self.fill_combo_flight_type(self.path_db_project) # rellena combo flight_type desde la base de datos de PLIPUAV
 
        self.comboBox_FlightType.setCurrentIndex(int_photogrammetric_mission_type)
        if int_photogrammetric_mission_type > 0: # se está copiando un proyecto
            self.comboBox_FlightType.setEnabled(False)

        else:
            self.comboBox_FlightType.setEnabled(True)
        
        # SIGNAL/SLOT connections in order:
        self.comboBox_FlightType.currentIndexChanged.connect(self.changed_combo_flight_type)
        self.toolButton_SaveFlightBlockCode.clicked.connect(self.save_code_flight_block)

    def changed_combo_flight_type(self):
        """
        brief:
        """
        pass
        
        """
        # si la selección es el primer elemento
        current_index = self.comboBox_FlightType.currentIndex()
        if current_index == 0:
            return
        else:            
            str_value = unicode(self.comboBox_FlightType.currentText())
            for key in self.dictionary_flight_type.keys():
                value_dic = self.dictionary_flight_type[key]
                if (value_dic == str_value):
                    str_key_flight_type = str(key)
                    break           
           
            # graba en la tabla flight_block el id_flighttype
            str_sql_update_id_flighttype = "UPDATE flight_block SET id_fb_type = " +  str_key_flight_type \
                + " WHERE cod_flight_block = '" + self.cod_flight_block_dlg + "'"
            self.instaceDatabase.execute_query(self.path_db_project,str_sql_update_id_flighttype)
        """  
    
    def fill_combo_flight_type(self,path):
        """
        brief: rellena el comboBox photogrammetric mission type a partir de los datos almacenados en la tabla correspondiente de la BD plantilla
        param[in]: path de la BD plantilla
        return: diccionario con keys-values
        """
        # vacia el combo
        self.comboBox_FlightType.clear()
       
        # añade la primera línea
        self.comboBox_FlightType.addItem("--- Select photogrammetric mission type ---")
        
        # conexión con la base de datos que contiene los tipos de vuelo        
        con_db_project = self.db_op.connection_sqlite(path)
        cursor_db_project = con_db_project.cursor()
        
        # ejecuta consulta para obtener los datos         
        str_sql = "SELECT id_fb_type,def_fb_type FROM flight_block_type ORDER BY id_fb_type ASC"
        cursor_db_project.execute(str_sql)
        
        # incializa matriz asociativa 
        dictionary = {}
        
        for row in cursor_db_project.fetchall():
            current_flighttype_id = row[0] # key
            current_description_flighttype = row[1] # value
            dictionary[current_flighttype_id] = current_description_flighttype
            if 'Prepare' in  current_description_flighttype:# para que no se incluya 'Prepare flight blocks from lineal axis segmentation'
                continue
            self.comboBox_FlightType.addItem(current_description_flighttype) #añade value al combobox
            
        # añade iconos identificativos
        self.comboBox_FlightType.setItemIcon(1,QIcon(":/plugins/pflip_uav_pafyc/icons/style-line.png"))
        self.comboBox_FlightType.setItemIcon(2,QIcon(":/plugins/pflip_uav_pafyc/icons/polygon.png"))
        # self.comboBox_FlightType.setItemIcon(3, QIcon(":/plugins/pflip_uav_pafyc/icons/buffer.png"))

        con_db_project.close() #cierra la base de datos
        return dictionary 
    
    def save_code_flight_block(self):
        """
        brief: recupera el código de bloque de vuelo (string) y la key del tipo de misión (int) y lo almacena en la lista pasada por referencia
        """
        # vacia la lista que se pasa por referencia
        del self.lst_flight_block_dlg[:]
        
        # 1º código de bloque de vuelo
        str_cod_flight_block_dlg = self.lineEdit_FlightBlockCode.text()
        if len(str_cod_flight_block_dlg) == 0:
            # mensaje error
            str_msg_error_fb_tipo_mision = "Select Flight Block code"
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                str_msg_error_fb_tipo_mision,
                                                Qgis.Critical,
                                                10)
            # vacia la lista que se pasa por referencia
            del self.lst_flight_block_dlg[:]            
            return
        else:
            self.lst_flight_block_dlg.append(str_cod_flight_block_dlg)
            
        # 2º string key tipo de misión (vuelo lineal, vuelo zonal, vuelo oblicuo, vuelo multilinear)
        current_index_tipo_mision = self.comboBox_FlightType.currentIndex()
        
        if current_index_tipo_mision == 0:
            # mensaje error
            str_msg_error_fb_tipo_mision = "Select photogrammetric mission type"
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                str_msg_error_fb_tipo_mision,
                                                Qgis.Critical,
                                                10)
            # vacia la lista que se pasa por referencia
            del self.lst_flight_block_dlg[:]            
            return
        else:            
            str_value = self.comboBox_FlightType.currentText()
            for key in self.dictionary_flight_type.keys():
                value_dic = self.dictionary_flight_type[key]
                if (value_dic == str_value):
                    str_key_flight_type = str(key)                    
                    break 
                
            self.lst_flight_block_dlg.append(int(str_key_flight_type))
        
        # cierra el dialogo
        self.close()