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

# GROUPS & LAYERS NAMES  ***********************************************************************************************
CONST_PFLIPUAV_TITLE = "PFlip-UAV"

CONST_PFLIPUAV_GROUP_AUX_GIS_LAYERS = "PFlip-UAV aux GIS layers"
CONST_PFLIPUAV_LAYER_AXIS = "c_axis"
CONST_PFLIPUAV_LAYER_BUFFER = "c_buffer_temp"
CONST_PFLIPUAV_LAYER_LANDING_POINT = "c_lnd"
CONST_PFLIPUAV_LAYER_TAKEOFF_POINT = "c_tof"
CONST_PFLIPUAV_LAYER_VECTOR = "c_vector"
CONST_PFLIPUAV_LAYER_ZONE = "c_zone"

CONST_PFLIPUAV_GROUP_OUPUT_GIS_LAYERS = "PFlip-UAV ouput GIS layers"
CONST_PFLIPUAV_LAYER_STEREO_PAIRS = "output_c_stereo_pairs"
CONST_PFLIPUAV_LAYER_IMAGES = "output_c_images"
CONST_PFLIPUAV_LAYER_STRIPS = "output_c_strips"
# 20190205: nombre
CONST_PFLIPUAV_LAYER_WAYPOINTS = "output_images_pc"
#CONST_PLIPUAV_LAYER_STEREO_AREA = "output_stereo_area"
#CONST_PLIPUAV_LAYER_IMAGES_FPR = "output_images_footprint"

CONST_PFLIPUAV_GROUP_OUPUT_MEMORY_GIS_LAYERS = "PFlip-UAV ouput Memory layers"
CONST_PFLIPUAV_MEMORY_LAYER_STEREO_PAIRS = "stereo_pairs"
CONST_PFLIPUAV_MEMORY_LAYER_FOOTPRNTS = "footprints"
CONST_PFLIPUAV_MEMORY_LAYER_WAYPOINTS = "waypoints"
CONST_PFLIPUAV_MEMORY_LAYER_STRIPS = "strips"
CONST_PFLIPUAV_MEMORY_LAYER_ORIGIN_POINT = "Axis amplied origin points"
CONST_PFLIPUAV_MEMORY_LAYER_END_POINTS = "Axis amplied end points"

# Mission types  *******************************************************************************************************
CONST_MISSION_TYPE_LINEAL = "Polygonal area from linear route"
CONST_MISSION_TYPE_ZONAL = "Zonal area"
CONST_MISSION_TYPE_PREPARE_FLIGHT_BLOCKS = "Prepare flight blocks from lineal axis segmentation"

# CONSTANTES GENERALES  ************************************************************************************************
CONST_STR_NO_VALID = "No valid"
CONST_DEFAULT_VALUE_KEY_COMBOS = -1
CONST_TAB_MSG_LOG = "    "
CONST_NO_DOUBLE = -999999.999 # Valor para definir un double no válido
CONST_DEFAULT_STRIP_TYPE = "Pasada_EO"

# constantes para el manejo de estructura de directorios  **************************************************************
CONST_COMMON_DATA_DIRNAME = "common_data"
CONST_PROJ_DATA_DIRNAME = "data"
CONST_MOSAICS_DIRNAME = "mosaics"
CONST_SEPARATOR_DIRECTORIES = "/"

# "defines" GeodesyDefinitions  ****************************************************************************************
CONST_PROJECTION_PRECISION_FRAMES = 4 # Precisión en la impresión de marcos de hojas en coordenadas proyectadas.

# technical specification_definitions  *********************************************************************************
CONST_ETG_GSD = 0.100 # Valor teórico del tamaño de pixel en el terreno
CONST_LONGITUDINAL_CONVERING_TOLERANCE = 0.0 # Tolerancia de variación del GSD expresado en tanto por ciento. 20150417: anteriormente el valor estaba establecido a 3.0
CONST_TRANSVERSAL_CONVERING_TOLERANCE = 0.0

# other parameters  ****************************************************************************************************
CONST_PARAMETER_PARALLEL_STRIPS_ANGULAR_TOLERANCE_DEFAULT_VALUE = 10.0
CONST_STRIPS_LINEAR_TOLERANCE_DEFAULT_VALUE = 0.6

# "defines" PhotogrammetryDefinitions.h  *******************************************************************************
CONST_PHOTOGRAMMETRY_STRING_SEPARATOR = "_"
CONST_TRANSVERSAL_COVERING_LOWER = "Posterior"
CONST_TRANSVERSAL_COVERING_UPPER = "Anterior"
CONST_SEPARATOR_IMAGES_IDS_IN_STEREOPAIR_ID = ":"
CONST_STRIPS_CONNECTION_LONGITUDINAL = "Longitudinal"
CONST_STRIPS_CONNECTION_OBLIQUE = "Oblicuo"
CONST_STRIPS_CONNECTION_TRANSVERSAL = "Transversal"
CONST_UAV_ACCELERATION_DEFAULT = 0.8
CONST_UAV_ACCELERATION_UPWARD_DEFAULT = 0.8
CONST_UAV_ACCELERATION_DOWNWARD_DEFAULT = 1.5
#CONST_UAV_BATTERY_FACTOR_DEFAULT = 1.0 # ahora se controla con las baterías
CONST_UAV_DECCELERATION_DEFAULT = -1.3
CONST_UAV_DECCELERATION_UPWARD_DEFAULT = -1.5
CONST_UAV_DECCELERATION_DOWNWARD_DEFAULT = -0.8
CONST_UAV_OMEGA_INITIAL_DEFAULT = 0.0

# "defines" CaraboWayPointLibrary.h  ***********************************************************************************
CONST_MICRODRON_CMD_CST = "CST" # Definición del comando CST
CONST_MICRODRON_CMD_CST_IMAGE_CAPTURE_VALUE = "1" # Definición del valor para capturar una imagen para el comando CST
CONST_MICRODRON_CMD_CSR = "CSR" # Definición del comando CSR
CONST_MICRODRON_CMD_CSS = "CSS" # Definición del comando CSS
CONST_MICRODRON_CMD_CWP = "CWP" # Definición del comando CWP
CONST_MICRODRON_CMD_CWP_RC = "0" # Definición del valor de CWP a controlado por Control Remoto (RC)
CONST_MICRODRON_CMD_CWP_WP = "1" # Definición del valor de CWP a controlado por Way Point (WP)
CONST_MICRODRON_CMD_EAL = "EAL" # Definición del comando EAL 
CONST_MICRODRON_CMD_EGI = "EGI" # Definición del comando EGI
CONST_MICRODRON_CMD_ERC = "ERC" # Definición del comando ERC 
CONST_MICRODRON_CMD_GPA = "GPA" # Definición del comando GPF
CONST_MICRODRON_CMD_GPA_UNIT_FACTOR = 10.0 # Definición del factor de unidad para el comando GPA a partir de metros.
CONST_MICRODRON_CMD_GPF = "GPF" # Definición del comando GPF
CONST_MICRODRON_CMD_GPF_DEFAULT_VALUE = "1" # Definición del valor por defecto para el comando GPF
CONST_MICRODRON_CMD_IOC = "IOC" # Definición del comando IOC
CONST_MICRODRON_CMD_IOC1_UNIT_FACTOR = 10.0 # Definición del factor de unidad para el comando IOC 1,
CONST_MICRODRON_CMD_INCREMENT_TIME_CAPTURE_IMAGE_TIME_COMPUTATION = 1.0 # Definición del incremento de tiempo a computar por imagen en el fichero de tiempos,no influye en el fichero de navegación. Se expresa en segundos.
CONST_MICRODRON_CMD_NBK = "NBK" # Definición del comando NBK
CONST_MICRODRON_CMD_PMC = "PMC"
CONST_MICRODRON_CMD_PMH = "PMH" # Definición del comando PMH
CONST_MICRODRON_CMD_PMH_UNIT_FACTOR = 100.0 # Definición del factor de unidad para el comando PMH a partir de metros.
CONST_MICRODRON_CMD_PMV = "PMV" # Definición del comando PMV
CONST_MICRODRON_CMD_PMV_UNIT_FACTOR = 100.0 # Definición del factor de unidad para el comando PMV a partir de metros.
CONST_MICRODRON_CMD_SHP = "SHP" # Definición del comando SHP, incluido por Carlos 2011-02-21
CONST_MICRODRON_CMD_SHP_UNIT_FACTOR = 100.0 # Definición del factor de unidad para el comando SHP a partir de metros, Carlos 2011-02-21 
CONST_MICRODRON_CMD_SHS = "SHS" # Definición del comando SHS
CONST_MICRODRON_CMD_SHS_LOW_VALUE = 1.0 # Definición del valor de velocidad lenta para el comando SHS, Carlos 2011-02-21
CONST_MICRODRON_CMD_SHS_UNIT_FACTOR = 10.0 # Definición del factor de unidad para el comando SHS a partir de m/s.
CONST_MICRODRON_CMD_SVS = "SVS" # Definición del comando SVS 
CONST_MICRODRON_CMD_SVS_DEFAULT_VALUE = 2.0 # Definición del valor por defecto para el comando SVS, Carlos 2011-02-21
CONST_MICRODRON_CMD_SVS_UNIT_FACTOR = 10.0 # Definición del factor de unidad para el comando SVS a partir de m/s.
CONST_MICRODRON_CMD_SSH = "SSH" # Definición del comando SSH
CONST_MICRODRON_CMD_SSH_UNIT_FACTOR = 100.0 # Definición del factor de unidad para el comando SSH a partir de metros.
CONST_MICRODRON_CMD_SYS = "SYS" # Definición del comando SYS 
CONST_MICRODRON_CMD_SYS_DEFAULT_VALUE = 30.0 # Definición del valor por defecto para el comando SYS
CONST_MICRODRON_CMD_SYS_UNIT_FACTOR = 10.0
CONST_MICRODRON_CMD_TIM = "TIM" # Definición del comando TIM
CONST_MICRODRON_CMD_TIM_UNIT_FACTOR = 10.0 # Definición del factor de unidad para el comando TIM a partir de segundos.CONST_MICRODRON_CMD_TIME_PRECISION = 1 # Precisión en tiempo en segundos.
CONST_MICRODRON_CMD_TIME_PRECISION = "1" # Precisión en tiempo en segundos. En el programa C++ es un entero no un string
CONST_MICRODRON_CMD_TIME_TO_INITIALIZE_ROUTE = 30.0 # Definición del tiempo en segundos desde el fin de ruta automática hasta landing, Carlos 2011-02-21
CONST_MICRODRON_CMD_WAE = "WAE" # Definición del comando WAE
CONST_MICRODRON_CMD_WAL = "WAL" # Definición del comando WAL
CONST_MICRODRON_CMD_WAL_UNIT_FACTOR = 10.0 # Definición del factor de unidad para el comando WAL a partir de m/s.
CONST_MICRODRON_CMD_WAS_UNIT_FACTOR = 10.0 # Definición del factor de unidad para el comando WAS a partir de metros.
CONST_MICRODRON_CMD_WPB = "WPB" # Definición del comando WAS
CONST_MICRODRON_CMD_YSF = "YSF" # Definición del comando YSF
CONST_MICRODRON_CMD_YSF_UNIT_FACTOR = 10.0 # Definición del factor de unidad para el comando YSF a partir de deg/s.
CONST_MICRODRON_TOLERANCE_LANDING = 2.0 # Tolerancia distancia para punto aterrizaje. Distancia mínima para que se mueva en horizontal hasta el punto de aterrizaje. 
CONST_MICRODRON_WAY_POINT_LIBRARY_ANGLE_TOLERANCE = 0.1 # Definición de tolerancia en ángulo en DEG
CONST_MICRODRON_WAY_POINT_LIBRARY_INTERNAL_QGIS_CRS_CODE = 3390 # EPSG 4258
CONST_MICRODRON_WAY_POINT_LIBRARY_POSTGIS_SRID_CRS_CODE = 4258

# new CONSTANTS PLIPUAV 3  *********************************************************************************************
CONST_CARABO_S3_AC_030406 = "Eiffage_UAV_firmware_1"