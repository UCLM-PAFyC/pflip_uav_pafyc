# -*- coding: utf-8 -*-

# import PyQGIS classes
from qgis.core import (Qgis)

# Proporciona acceso a las funciones matemáticas definidas por la norma C.
from math import *

# self classes
from ...classes.db_operations import *
from ...classes.qgis3_api_operations import Qgis3ApiOperations
from ...PyGeodesy.PyGeoid.py_geoid import *

from ... import config as c # valores constantes

#valores constantes
GEODETIC_CALCULATIONS_CONST_PI = 4 * atan(1.0)
GEODETIC_CALCULATIONS_NULL_VALUE = -999999.999
GEODETIC_CALCULATIONS_CONST_ANGULAR_TOLERANCE = 0.000001/3600.0 * GEODETIC_CALCULATIONS_CONST_PI / 180.0
GEODETIC_CALCULATIONS_CONST_LINEAR_TOLERANCE = 0.0001
GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE = GEODETIC_CALCULATIONS_CONST_PI / 2.0
GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE = - GEODETIC_CALCULATIONS_CONST_PI / 2.0
GEODETIC_CALCULATIONS_CONST_MAX_LONGITUDE = GEODETIC_CALCULATIONS_CONST_PI
GEODETIC_CALCULATIONS_CONST_MIN_LONGITUDE = - GEODETIC_CALCULATIONS_CONST_PI
GEODETIC_CALCULATIONS_CONST_MAX_SEMI_MAYOR_AXIS = 6380000.0
GEODETIC_CALCULATIONS_CONST_MIN_SEMI_MAYOR_AXIS = 6370000.0
GEODETIC_CALCULATIONS_CONST_MAX_INVERSE_FLATTENING = 350.0
GEODETIC_CALCULATIONS_CONST_MIN_INVERSE_FLATTENING = 250.0

#"defines" GeodeticCalculations.h 
GEODETIC_CALCULATIONS_NO_ERROR = 0 #Valor devuelto por las funciones si no se produce error.
GEODETIC_CALCULATIONS_LATITUDE_ERROR = 1001 #Latitud geodésica fuera de dominio.
GEODETIC_CALCULATIONS_LONGITUDE_ERROR = 1002 #Longitud geodésica fuera de dominio.
GEODETIC_CALCULATIONS_A_ERROR = 1003 #Semieje mayor del elipsoide fuera de dominio.
GEODETIC_CALCULATIONS_INV_F_ERROR = 1004 #Inverso del aplanamiento del elipsoide fuera de dominio.
GEODETIC_CALCULATIONS_GLOBAL_MAX_LONGITUDE = 180.00000000 #Valor global máximo para la longitud geodésica, en DEG.
GEODETIC_CALCULATIONS_GLOBAL_MIN_LONGITUDE = -180.00000000 #Valor global mínimo para la longitud geodésica, en DEG.
GEODETIC_CALCULATIONS_GLOBAL_MAX_LATITUDE = 90.00000000 #Valor global máximo para la latitud geodésica, en DEG.
GEODETIC_CALCULATIONS_GLOBAL_MIN_LATITUDE = -90.00000000 #Valor global mínimo para la latitud geodésica, en DEG.

#"defines" MapProjections.h que no están en GeodeticCalculations.h, ahora toman el sufijo GEODETIC_CALCULATIONS_*
GEODETIC_CALCULATIONS_UTM_ZONE_WIDTH = 6.0*GEODETIC_CALCULATIONS_CONST_PI/180.0 #Anchura del huso para la proyección UTM.
GEODETIC_CALCULATIONS_UTM_MIN_ZONE = 1 #Mínimo valor del huso para la proyección UTM.
GEODETIC_CALCULATIONS_UTM_MAX_ZONE = 60 #Máximo valor del huso para la proyección UTM.
GEODETIC_CALCULATIONS_UTM_MAX_CONVERGENCE_ANGLE = 7.0*GEODETIC_CALCULATIONS_CONST_PI/180.0 #Máximo valor de la convergencia de meridianos, en RAD. Está calculada para meter un huso en el adyacente.
GEODETIC_CALCULATIONS_UTM_MIN_CONVERGENCE_ANGLE = -7.0*GEODETIC_CALCULATIONS_CONST_PI/180.0 #Mínimo valor de la convergencia de meridianos, en RAD. Está calculada para meter un huso en el adyacente.
GEODETIC_CALCULATIONS_TMERC_MAX_ORIGIN_LATITUDE = GEODETIC_CALCULATIONS_CONST_PI / 2.0 #Máximo valor de la latitud geodésica del paralelo origen para la proyección Transversa de Mercator, en RAD.
GEODETIC_CALCULATIONS_TMERC_MIN_ORIGIN_LATITUDE = - GEODETIC_CALCULATIONS_CONST_PI / 2.0 #Mínimo valor de la latitud geodésica del paralelo origen para la proyección Transversa de Mercator, en RAD.
GEODETIC_CALCULATIONS_TMERC_MAX_SCALE_FACTOR = 3.0 #Máximo valor del factor de escala para la proyección Transversa de Mercator, en adimensional.
GEODETIC_CALCULATIONS_TMERC_MIN_SCALE_FACTOR = 0.3 #Mínimo valor del factor de escala para la proyección Transversa de Mercator, en adimensional.
GEODETIC_CALCULATIONS_TMERC_MAX_CENTRAL_MERIDIAN = GEODETIC_CALCULATIONS_CONST_PI #Máximo valor de la longitud geodésica del meridiano central para la proyección Transversa de Mercator, en RAD.
GEODETIC_CALCULATIONS_TMERC_MIN_CENTRAL_MERIDIAN = -GEODETIC_CALCULATIONS_CONST_PI #Mínimo valor de la longitud geodésica del meridiano central para la proyección Transversa de Mercator, en RAD.
GEODETIC_CALCULATIONS_TMERC_MAX_INC_LONGITUDE = 9.0*GEODETIC_CALCULATIONS_CONST_PI/180.0 #/// Máximo valor del incremento de longitud geodésica respecto al meridiano central para la proyección Transversa de Mercator, en RAD.
GEODETIC_CALCULATIONS_MAPPROJ_CENTRAL_MERIDIAN_ERROR = 2006 #Longitud geodésica del meridiano central fuera de dominio.
GEODETIC_CALCULATIONS_MAPPROJ_SCALE_FACTOR_ERROR = 2007 #Factor de escala fuera de dominio.
GEODETIC_CALCULATIONS_MAPPROJ_EASTING_ERROR = 2009 #Coordenada este mayor que el valor máximo.
GEODETIC_CALCULATIONS_MAPPROJ_NORTHING_ERROR = 2010 #Coordenada norte mayor que el valor máximo.
GEODETIC_CALCULATIONS_UTM_ZONE_ERROR = 2014 #Huso de la proyección UTM fuera del intervalo válido [1,60].
GEODETIC_CALCULATIONS_UTM_CONVERGENCE_ANGLE_ERROR = 2017 #Convergencia de meridianos fuera de dominio

class GeodeticCalculations:
    """
    Brief: Esta librería incorpora funciones para resolver los problemas más comunes de geodesia
    """    
    def __init__(self,
                 iface,
                 path_db_project,
                 path_plugin):
        """
        Brief:inicialización del cuerpo de la clase
        """
        self.iface = iface        
        self.path_db_project = path_db_project
        self.path_plugin = path_plugin

        self.db_op = DbOperations(self.iface)  # new db operations
        self.q3_api_op = Qgis3ApiOperations(self.iface)
        self.instance_py_geoid = PyGeoid(self.iface,
                                         self.path_plugin) # instancia a pygeoid

    def aut_lat_2_gd_lat(self, authalic, inv_f):
        """
        brief: Paso de latitud autálica a latitud geodésica.
        param[in]: authalic - Latitud autálica, en RAD.
        param[in]: inv_f - Inverso del aplanamiento del elipsoide.
        return[0]: Entero con el estado del error
        return[1]: Latitud geodésica calculada, en RAD.        
        """
        
        if authalic < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or authalic > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            #Latitud geodésica fuera de dominio - 1001
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR, GEODETIC_CALCULATIONS_NULL_VALUE

        if inv_f != 0.0 and (inv_f < GEODETIC_CALCULATIONS_CONST_MIN_INVERSE_FLATTENING or inv_f > GEODETIC_CALCULATIONS_CONST_MAX_INVERSE_FLATTENING):
            #Inverso del aplanamiento del elipsoide fuera de dominio. - 1004
            return GEODETIC_CALCULATIONS_INV_F_ERROR, GEODETIC_CALCULATIONS_NULL_VALUE
        
        if authalic == - GEODETIC_CALCULATIONS_CONST_PI / 2.0 or authalic == GEODETIC_CALCULATIONS_CONST_PI / 2.0:
            geodetic = authalic
        else:
            e2 = 2.0/inv_f-pow(1.0 /inv_f, 2.0)
            sqrt_e2 = sqrt(e2)
            qp = (1.0-e2)*(1.0/(1.0-e2)-1.0/(2.0*sqrt_e2)*log((1.0-sqrt_e2)\
                /(1.0+sqrt_e2)))
            q = qp * sin(authalic)
            latitude_ini = asin(q/2.0)
            control = 0
            tolerance = GEODETIC_CALCULATIONS_CONST_ANGULAR_TOLERANCE
            while control == 0:
                sin_latitude = sin(latitude_ini)
                c = q/(1.0-e2)-sin_latitude/(1.0-e2*pow(sin_latitude,2.0))\
                    +1.0/(2.0*sqrt_e2)*log((1.0-sqrt_e2*sin_latitude)\
                    /(1.0+sqrt_e2*sin_latitude))
                latitude = latitude_ini+pow(1.0-e2*pow(sin_latitude,2.0),2.0)\
                    /(2.0*cos(latitude_ini))*c
                if (fabs(latitude-latitude_ini)>tolerance):
                    latitude_ini = latitude
                else:
                    control = 1
            geodetic = latitude
        return GEODETIC_CALCULATIONS_NO_ERROR, geodetic           
    
    def azimuth(self,xi, yi, xj, yj):
        """
        brief: Cálculo del azimut en el plano.
        param[in]: xi - Coordenada x del punto inicial, en metros.
        param[in]: yi - Coordenada y del punto inicial, en metros.
        param[in]: xj - Coordenada x del punto final, en metros.
        param[in]: yj - Coordenada y del punto final, en metros.
        return[0]: Entero con el estado del error
        return[1]: azimuth - Azimut calculado, en RAD.
        """
        ax = xj-xi
        ay = yj-yi
        azimuth = atan2(ax ,ay)
        if(azimuth < 0.0):
            azimuth = azimuth + 2.0 * GEODETIC_CALCULATIONS_CONST_PI

        return GEODETIC_CALCULATIONS_NO_ERROR, \
               azimuth

    def azimuth_geodesico(self,
                          xi,
                          yi,
                          xj,
                          yj,
                          int_crs_point):
        """
        Calcula el azimuth geodésico aplicando la convergencia de meridianos
        :param xi:
        :param yi:
        :param xj:
        :param yj:
        :param int_crs_point:
        :return:
        """

        # calculo del acimut cartográfico
        control,cartographic_azimuth = self.azimuth(xi,
                                                    yi,
                                                    xj,
                                                    yj)

        # calculo de la convergencia de meridianos
        if (int_crs_point == 3857 or int_crs_point == 32661 or int_crs_point == 32761): # WGS 84 / Pseudo Mercator or WGS/UPS North y y WGS/UPS South
            convergencia_i = 0.0
        else:
            # transformación de coordenadas a latitud, longitud
            int_crs_geodesico = 4326
            if (int_crs_point != int_crs_geodesico):
                qgs_point_transform_i = self.q3_api_op.transform_point_coordinates(xi,
                                                                                   yi,
                                                                                   int_crs_point,
                                                                                   int_crs_geodesico)
                longitud_i = qgs_point_transform_i.x()
                latitud_i = qgs_point_transform_i.y()

                qgs_point_transform_j = self.q3_api_op.transform_point_coordinates(xj,
                                                                                   yj,
                                                                                   int_crs_point,
                                                                                   int_crs_geodesico)
                longitud_j = qgs_point_transform_j.x()
                latitud_j = qgs_point_transform_j.y()

            else:
                longitud_i = xi
                latitud_i = yi
                longitud_j = xj
                latitud_j = yj

            longitud_i_rad = longitud_i * GEODETIC_CALCULATIONS_CONST_PI / 180.0
            latitud_i_rad = latitud_i * GEODETIC_CALCULATIONS_CONST_PI / 180.0

            longitud_j_rad = longitud_j * GEODETIC_CALCULATIONS_CONST_PI / 180.0
            latitud_j_rad = latitud_j * GEODETIC_CALCULATIONS_CONST_PI / 180.0

            control,zone_i = self.utm_zone_from_epsg_code(int_crs_point)
            if control == GEODETIC_CALCULATIONS_UTM_ZONE_ERROR:
                self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                    "Zone UTM out of range",
                                                    Qgis.Critical,
                                                    10)
                return

            #control2,zone_i = self.utm_zone(longitud_i_rad)
            #control3,zone_j = self.utm_zone(longitud_j_rad)

            # parámetros EPSG 4326 WGS84
            a = 6378137 #TODO: cogerlo desde la base de datos
            inv_f = 298.257223563 #TODO: cogerlo desde la base de datos

            control,convergencia_i = self.utm_convergence_angle(latitud_i_rad,
                                                                longitud_i_rad,
                                                                zone_i,
                                                                a,
                                                                inv_f)
            #TODO: control
            """
            control,convergencia_j = self.utm_convergence_angle(latitud_j_rad,
                                                                longitud_j_rad,
                                                                zone_j,
                                                                a,
                                                                inv_f)
            """

        geodetic_azimuth = cartographic_azimuth + convergencia_i
        return geodetic_azimuth

    def crs_operation_is_lat_long_from_epsg_code(self,
                                                 crs,
                                                 path_db_project):
        """
        Brief:
        """
        b_is_lat_long = False

        conexion = self.db_op.connection_sqlite(path_db_project)
        cursor_db_project = conexion.cursor()

        field_epsg = 'COORD_REF_SYS_CODE'
        field_coord_ref_sys_kind = 'COORD_REF_SYS_KIND'
        table_crs = 'crs'

        str_sql = "SELECT " + field_coord_ref_sys_kind + " FROM "+ table_crs + " WHERE " + field_epsg + " = "
        str_sql += str(crs) + ";"
        cursor_db_project.execute(str_sql)
        for row in cursor_db_project.fetchall():
            value_db = row[0] # en este caso value y key son lo mismo

        value_crs_projected_in_database = "projected"
        value_crs_geographic_in_database = "geographic 2D"

        if value_db == value_crs_geographic_in_database:
           b_is_lat_long = True

        conexion.close() #se cierra la base de datos
        return b_is_lat_long

    def crs_operation_to_geocentric_from_geoid_height(self,
                                                      int_crs_point,
                                                      first_coordinate,
                                                      second_coordinate,
                                                      third_coordinate,
                                                      ellipsoid_height_tof,
                                                      tof_height):
        """
        Brief: Método para pasar la posición de un punto a coordenadas cartesianas a partir de su posición planimétrica
                y de la altitud ortométrica. El sistema de coordenadas de la posición planimétrica se corresponde
                al CRS indicado.
        :param crs: Código EPSG del CRS de la posición planimétrica del punto. (4258)
        :type crs: int
        :param first_coordinate: Primera coordenada de la posición planimétrica del punto, si es geodésica en DEG
        :type first_coordinate: float
        :param second_coordinate: Segunda coordenada de la posición planimétrica del punto, si es geodésica en DEG
        :type second_coordinate: float
        :param third_coordinate: Altitud ortométrica (dtm_height + height_of_flight), en metros
        :type third_coordinate: float
        :param ellipsoid_height_tof: altura elipsoidal del tof point
        :type ellipsoid_height_tof: float
        :param tof_height: altura sobre el terreno del tof
        :type tof_height: float
        :return: estado y coordenadas geocéntricas
        """

        # Si el crs origen es proyectado hay que pasar al elipsoide
        # cambio de CRS
        if (int_crs_point != c.CONST_MICRODRON_WAY_POINT_LIBRARY_POSTGIS_SRID_CRS_CODE):
            #third_coordinate = 0.0 # Esta no se utiliza porque es transformacion entre geodesicas (long,lat)

            qgs_point_transform = self.q3_api_op.transform_point_coordinates(first_coordinate,
                                                                             second_coordinate,
                                                                             int_crs_point,
                                                                             c.CONST_MICRODRON_WAY_POINT_LIBRARY_POSTGIS_SRID_CRS_CODE)

            first_coordinate_transform = qgs_point_transform.x()
            second_coordinate_transform = qgs_point_transform.y()
        else:
            first_coordinate_transform = first_coordinate
            second_coordinate_transform = second_coordinate

        # parámetros EPSG 4326 WGS84
        """
        a = 6378137 #TODO: cogerlo desde la base de datos
        inv_f = 298.257223563 #TODO: cogerlo desde la base de datos
        """

        # parámetros EPSG 4258 ETRS89
        a = 6378137 #TODO: cogerlo desde la base de datos
        inv_f = 298.257222101 #TODO: cogerlo desde la base de datos

        ondulation = self.instance_py_geoid.get_ondulation_from_geoid_interpolate(first_coordinate_transform,
                                                                                  second_coordinate_transform,
                                                                                  c.CONST_MICRODRON_WAY_POINT_LIBRARY_POSTGIS_SRID_CRS_CODE)

        current_ellipsoid_height = third_coordinate + ondulation

        height_over_takeoff = (current_ellipsoid_height - (ellipsoid_height_tof + tof_height))* -1.0

        latitude_rad = second_coordinate_transform * GEODETIC_CALCULATIONS_CONST_PI / 180.0
        longitude_rad = first_coordinate_transform * GEODETIC_CALCULATIONS_CONST_PI / 180.0

        geocal,first_coordinate_transform_geocentric,second_coordinate_transform_geocentric,third_coordinate_transform_geocentric = \
            self.geodetic_2_geocentric(latitude_rad,
                                       longitude_rad,
                                       height_over_takeoff,
                                       a,
                                       inv_f)
        if(geocal != GEODETIC_CALCULATIONS_NO_ERROR):
            return False,\
                   0.0,\
                   0.0,\
                   0.0
        return True,\
               first_coordinate_transform_geocentric,\
               second_coordinate_transform_geocentric,\
               third_coordinate_transform_geocentric

    def crs_operation_xform_from_postgis_srid_epsg_code(self,
                                                        x_input,
                                                        y_input,
                                                        int_crs_src,
                                                        int_crs_dest):
        #TODO: función obsoleta. Reimplementada en la clase Database
        """
        Brief: Transforma coordenadas con QGIS
        :param x_input: coordenada x de entrada
        :param y_input: coordenada y de entrada
        :param int_crs_src: entero con el CRS de EPSG (postgisSrid) de entrada
        :param int_crs_dest: entero con el CRS de EPSG (postgisSrid) de salida
        :return: (primera coordenada transformada, segunda coordenada transformada)
        """

        try:
            crs_src = QgsCoordinateReferenceSystem(int_crs_src)
            crs_dest = QgsCoordinateReferenceSystem(int_crs_dest)
            xform = QgsCoordinateTransform(crs_src,
                                           crs_dest,
                                           QgsProject.instance())

            # forward transformation: src -> dest
            pt1 = xform.transform(x_input,
                                  y_input)
            #print "Transformed point:", pt1
            first_coordinate = pt1.x()
            second_coordinate = pt1.y()

            # inverse transformation: dest -> src
            # pt2 = xform.transform(pt1, QgsCoordinateTransform.ReverseTransform)
            # print "Transformed back:", pt2

            return first_coordinate,second_coordinate

        except:
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                    "Failed coordinates transformation",
                                                Qgis.Critical,
                                                10)

    def distance(self, xi, yi, xj, yj):
        """
        brief: Cálculo de la distancia en el plano.
        param[in]: xi - Coordenada x del punto inicial, en metros.
        param[in]: yi - Coordenada y del punto inicial, en metros.
        param[in]: xj - Coordenada x del punto final, en metros.
        param[in]: yj - Coordenada y del punto final, en metros.
        return[0]: Entero con el estado del error
        return[1]: distance - Distancia calculada, en metros.
        """
        ax = xj-xi
        ay = yj-yi
        distance = sqrt(pow(ax,2.0)+pow(ay,2.0))
        return GEODETIC_CALCULATIONS_NO_ERROR, distance

    def ellipsoid_direct_problem(self, initial_latitude, initial_longitude, azimuth, distance, a, inv_f):
        """
        brief: Solución del problema directo de la geodesia sobre el elipsoide.
        param[in]: initial_latitude - Latitud geodésica origen, en RAD.
        param[in]: initial_longitude - Longitud geodésica origen, en RAD.
        param[in]: azimuth - Azimut de la linea, en RAD.
        param[in]: distance - Distancia de la linea, en metros.
        param[in]: a - Semieje mayor del elipsoide, en metros.
        param[in]: inv_f - Inverso del aplanamiento del elipsoide.
        return[0]: Entero con el estado del error
        return[1]: final_latitude - Latitud geodésica final calculada, en RAD.
        return[2]: final_longitude - Longitud geodésica final calculada, en RAD.
        """
            
        if initial_latitude < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or initial_latitude > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
        if initial_longitude < GEODETIC_CALCULATIONS_CONST_MIN_LONGITUDE or initial_longitude > GEODETIC_CALCULATIONS_CONST_MAX_LONGITUDE:
            return GEODETIC_CALCULATIONS_LONGITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
        if inv_f != 0.0 and (a < GEODETIC_CALCULATIONS_CONST_MIN_SEMI_MAYOR_AXIS or a > GEODETIC_CALCULATIONS_CONST_MAX_SEMI_MAYOR_AXIS):
            return GEODETIC_CALCULATIONS_A_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
        if inv_f != 0.0 and (inv_f < GEODETIC_CALCULATIONS_CONST_MIN_INVERSE_FLATTENING or inv_f > GEODETIC_CALCULATIONS_CONST_MAX_INVERSE_FLATTENING):
            return GEODETIC_CALCULATIONS_INV_F_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
       
        if(inv_f == 0):
            error,final_latitude,final_longitude = self.sphere_direct_problem(initial_latitude,initial_longitude, azimuth,distance,a)
            if(error != 0):
                return error
        else:               
            e2 = 2.0/inv_f-pow(1.0/inv_f,2.0)
            filast = -2.0*GEODETIC_CALCULATIONS_CONST_PI
            lonlast = -2.0*GEODETIC_CALCULATIONS_CONST_PI
            step = 1
            control = 1
            tolerance = GEODETIC_CALCULATIONS_CONST_LINEAR_TOLERANCE
            while(control == 1):
                latn = initial_latitude
                lon = initial_longitude
                azn = azimuth
                h = distance / step
                for i in range (step):
                    lat = latn
                    az = azn
                    rni = a/pow(1.0-e2*pow(sin(lat),2.0),0.5)
                    rmi = a*(1.0-e2)/pow(1.0-e2*pow(sin(lat),2.0),1.5)
                    k1 = h*cos(az)/rmi
                    ll1 = h*sin(az)/(rni*cos(lat))
                    m1 = h*tan(lat)*sin(az)/rni
                    lat = latn+(k1/2.0)
                    az = azn+(m1/2.0)
                    rni = a/pow(1.0-e2*pow(sin(lat),2.0),0.5)
                    rmi = a*(1.0-e2)/pow(1.0-e2*pow(sin(lat),2.0),1.5)
                    k2 = h*cos(az)/rmi
                    ll2 = h*sin(az)/(rni*cos(lat))
                    m2 = h*tan(lat)*sin(az)/rni
                    lat = latn+(k2/2.0)
                    az = azn+(m2/2.0)
                    rni = a/pow(1.0-e2*pow(sin(lat),2.0),0.5)
                    rmi = a*(1.0-e2)/pow(1.0-e2*pow(sin(lat),2.0),1.5)
                    k3 = h*cos(az)/rmi
                    ll3 = h*sin(az)/(rni*cos(lat))
                    m3 = h*tan(lat)*sin(az)/rni
                    lat = latn+k3
                    az = azn+m3
                    rni = a/pow(1.0-e2*pow(sin(lat),2.0),0.5)
                    rmi = a*(1.0-e2)/pow(1.0-e2*pow(sin(lat),2.0),1.5)
                    k4 = h*cos(az)/rmi
                    ll4 = h*sin(az)/(rni*cos(lat)) 
                    m4 = h*tan(lat)*sin(az)/rni
                    latn = latn+(k1+2.0*k2+2.0*k3+k4)/6.0
                    lon = lon+(ll1+2.0*ll2+2.0*ll3+ll4)/6.0
                    azn = azn+(m1+2.0*m2+2.0*m3+m4)/6.0
                
                rni = a/pow(1.0-e2*pow(sin(latn),2.0),0.5)
                rmi = a*(1.0-e2)/pow(1.0-e2*pow(sin(latn),2.0),1.5)
                efi = rmi*fabs(latn-filast)
                elon = cos(latn)*rni*fabs(lon-lonlast)
                edis = sqrt(pow(efi,2.0)+pow(elon,2.0))
                if(edis < tolerance):
                    control = 0
                else:
                    step = step*2
                    filast = latn
                    lonlast = lon
                lon2 = lon
                fi2 = latn
                if(lon2 > GEODETIC_CALCULATIONS_CONST_PI):
                    lon2 = lon2-2.0*GEODETIC_CALCULATIONS_CONST_PI
                if(lon2 < -GEODETIC_CALCULATIONS_CONST_PI):
                    lon2 = 2.0*GEODETIC_CALCULATIONS_CONST_PI+lon2
                if(fabs(fi2) > GEODETIC_CALCULATIONS_CONST_PI/2.0):
                    if(initial_longitude <= 0.0):
                        lon2 = GEODETIC_CALCULATIONS_CONST_PI+lon2
                    else:
                        lon2 = initial_longitude-GEODETIC_CALCULATIONS_CONST_PI
                    if(fi2 > 0.0):
                        fi2 = GEODETIC_CALCULATIONS_CONST_PI/2.0-(fi2-GEODETIC_CALCULATIONS_CONST_PI/2.0)
                    else:
                        fi2 = -GEODETIC_CALCULATIONS_CONST_PI/2.0-(fi2+GEODETIC_CALCULATIONS_CONST_PI/2.0)
                if(fabs(fabs(lon2)-GEODETIC_CALCULATIONS_CONST_PI) < GEODETIC_CALCULATIONS_CONST_ANGULAR_TOLERANCE):
                    lon2=GEODETIC_CALCULATIONS_CONST_PI            
            final_latitude = fi2
            final_longitude = lon2        
        if final_latitude < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or final_latitude > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            #1001 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
        if final_longitude < GEODETIC_CALCULATIONS_CONST_MIN_LONGITUDE or final_longitude > GEODETIC_CALCULATIONS_CONST_MAX_LONGITUDE:
            #1002 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LONGITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE      
        return GEODETIC_CALCULATIONS_NO_ERROR, final_latitude, final_longitude

    def ellipsoid_inverse_problem(self,initial_latitude, initial_longitude, final_latitude, final_longitude, a, inv_f):
        """
        brief: Solución del problema inverso de la geodesia sobre el elipsoide.
        param[in]: initial_latitude - Latitud geodésica origen, en RAD.
        param[in]: initial_longitude - Longitud geodésica origen, en RAD.
        param[in]: final_latitude - Latitud geodésica final, en RAD.
        param[in]: final_longitude - Longitud geodésica final, en RAD.
        param[in]: a - Semieje mayor del elipsoide, en metros.
        param[in]: inv_f - Inverso del aplanamiento del elipsoide.
        return[0]: Entero con el estado de error.
        return[1]: azimuth - Azimut calculado de la linea, en RAD.
        return[2]: distance - Distancia calculada de la linea, en metros.
        """        
        if initial_latitude < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or initial_latitude > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            #1001 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
        if initial_longitude < GEODETIC_CALCULATIONS_CONST_MIN_LONGITUDE or initial_longitude > GEODETIC_CALCULATIONS_CONST_MAX_LONGITUDE:
            #1002 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LONGITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
        if final_latitude < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or final_latitude > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            #1001 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
        if final_longitude < GEODETIC_CALCULATIONS_CONST_MIN_LONGITUDE or final_longitude > GEODETIC_CALCULATIONS_CONST_MAX_LONGITUDE:
            #1002 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LONGITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
        if inv_f != 0.0 and (a < GEODETIC_CALCULATIONS_CONST_MIN_SEMI_MAYOR_AXIS or a > GEODETIC_CALCULATIONS_CONST_MAX_SEMI_MAYOR_AXIS):
            #1003 - Semieje mayor del elipsoide fuera de dominio.
            return GEODETIC_CALCULATIONS_A_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
        if inv_f != 0.0 and (inv_f < GEODETIC_CALCULATIONS_CONST_MIN_INVERSE_FLATTENING or inv_f > GEODETIC_CALCULATIONS_CONST_MAX_INVERSE_FLATTENING):
            #1004 - Inverso del aplanamiento del elipsoide fuera de dominio.
            return GEODETIC_CALCULATIONS_INV_F_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE

        if(inv_f == 0):
            state,azimuth,distance = self.sphere_inverse_problem(initial_latitude,initial_longitude,final_latitude,final_longitude,a)
            if(state != 0):
                return state,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
        else:
            e2 = 2.0/inv_f-pow(1.0/inv_f,2.0)
            b = a-a/inv_f
            ee2 = (2.0/inv_f-pow(1.0/inv_f,2.0))/pow((1.0-1.0/inv_f),2.0)
            u1 = atan(sqrt(1.0-e2)*tan(initial_latitude))
            u2 = atan(sqrt(1.0-e2)*tan(final_latitude))
            w0 = final_longitude-initial_longitude
            dww = 0
            dwant = 0
            tolerance = GEODETIC_CALCULATIONS_CONST_ANGULAR_TOLERANCE
            control = 0
            radius = a
            e4 = pow(e2,2.0)
            e6 = pow(e2,3.0)
            e8 = pow(e2,4.0)
            while(control == 0):
                ll2 = initial_longitude+w0+dww
                if(ll2 > GEODETIC_CALCULATIONS_CONST_PI):
                    ll2 = ll2-2.0*GEODETIC_CALCULATIONS_CONST_PI
                if(ll2 < -GEODETIC_CALCULATIONS_CONST_PI):
                    ll2 = ll2+2.0*GEODETIC_CALCULATIONS_CONST_PI
                if(fabs(fabs(ll2)-GEODETIC_CALCULATIONS_CONST_PI) < GEODETIC_CALCULATIONS_CONST_ANGULAR_TOLERANCE):
                    ll2 = GEODETIC_CALCULATIONS_CONST_PI
                state,a12,sig = self.sphere_inverse_problem(u1,initial_longitude,u2,ll2,radius)
                if(state!=0):
                    return state,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE                    
                state,a21,sig = self.sphere_inverse_problem(u2,ll2,u1,initial_longitude,radius)
                if(state!=0):
                   return state,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
                mm = atan2(tan(u1),cos(a12))
                m = asin(sin(a12)*cos(u1))
                sig = sig/radius
                cms = cos(mm+sig)
                sms = sin(mm+sig)
                cm = cos(m)
                sm = sin(m)
                cmm = cos(mm)
                smm = sin(mm)
                int1 = sig+1.0/2.0*pow(cm,2.0)*cms*sms-1.0/2.0*pow(cm,2.0)*sig\
                        -1.0/2.0*pow(cm,2.0)*cmm*smm
                int2 = sig+pow(cm,2.0)*cms*sms-pow(cm,2.0)*sig\
                        -1.0/4.0*pow(cm,4)*pow(sms,3)*cms
                int2 = int2-3.0/8.0*pow(cm,4.0)*cms*sms+3.0/8.0*pow(cm,4.0)*sig\
                        -pow(cm,2.0)*cmm*smm
                int2 = int2+1.0/4.0*pow(cm,4.0)*pow(smm,3.0)*cmm+3.0/8.0\
                        *pow(cm,4.0)*cmm*smm
                int3 = sig+3.0/2.0*pow(cm,2.0)*cms*sms-3.0/2.0*pow(cm,2.0)\
                        *sig-3.0/4.0*pow(cm,4.0)*pow(sms,3.0)*cms
                int3 = int3-9.0/8.0*pow(cm,4.0)*cms*sms+9.0/8.0*pow(cm,4.0)\
                        *sig+1.0/6.0*pow(cm,6.0)*pow(sms,5.0)*cms
                int3 = int3+5.0/24.0*pow(cm,6.0)*pow(sms,3.0)*cms+5.0/16.0\
                        *pow(cm,6)*cms*sms
                int3 = int3-5.0/16.0*pow(cm,6.0)*sig-3.0/2.0*pow(cm,2.0)*cmm\
                        *smm+3.0/4.0*pow(cm,4.0)*pow(smm,3.0)*cmm
                int3 = int3+9.0/8.0*pow(cm,4.0)*cmm*smm-1.0/6.0*pow(cm,6.0)\
                        *pow(smm,5.0)*cmm
                int3 = int3-5.0/24.0*pow(cm,6.0)*pow(smm,3.0)*cmm-5.0/16.0\
                        *pow(cm,6.0)*cmm*smm
                dww = e2*sm/2.0*(sig+e2/4.0*int1+e4/8.0*int2+5.0/64.0*e6*int3)
                if(fabs(dww-dwant) < tolerance):
                    control = 1
                else:
                    dwant = dww
               
            sig = sig*radius
            s = 0.0
            u1n = u1
            lon1n = initial_longitude
            a12n = a12
            if(sig > 100000.0):
                disn = 100000.0
            else:
                disn = sig
            sigres = sig
            while(sigres > 0):
                mm = atan2(tan(u1n),cos(a12n))
                m = asin(sin(a12n)*cos(u1n))
                sig1 = disn/radius
                cms = cos(mm+sig1)
                sms = sin(mm+sig1)
                cm = cos(m)
                sm = sin(m)
                cmm = cos(mm)
                cmm2 = pow(cmm,2.0)
                cmm3 = pow(cmm,3.0)
                smm = sin(mm)
                smm2 = pow(smm,2.0)
                smm3 = pow(smm,3.0)
                k2 = ee2*pow(cm,2.0)
                k4 = pow(k2,2.0)
                k6 = pow(k2,3.0)
                ukm = 1.0+k2*pow(smm,2.0)
                ukm05 = pow(ukm,0.5)
                ukm2 = pow(ukm,2.0)
                ukm3 = pow(ukm,3.0)
                spaux1 = ukm05*sig1+k2*smm*cmm/2.0/ukm05*pow(sig1,2.0)
                spaux2 = 1.0/3.0*ukm05*(0.5*k2*(-smm2+cmm2)/ukm-0.5*k4*smm2*cmm2/ukm2)*pow(sig1,3)
                spaux3 = 0.25*ukm05*(-0.5*k4*smm*cmm*(-smm2+cmm2)/ukm2-2.0/3.0*k2*smm*cmm/ukm+0.5*k6*smm3*cmm3/ukm3)*pow(sig1,4.0)
                sp = b*(spaux1+spaux2+spaux3)
                s = s+sp
                rp1 = cos(u1n)
                state,u2n,lon2n = self.sphere_direct_problem(u1n,lon1n,a12n,disn,radius)
                if(state!= 0):
                    return state,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
                state,a21n,sobra = self.sphere_inverse_problem(u2n,lon2n,u1n,lon1n,radius)
                if(state!=0):
                    return state,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
                if(a21n >= GEODETIC_CALCULATIONS_CONST_PI):
                    a12n = a21n-GEODETIC_CALCULATIONS_CONST_PI
                if(a21n < GEODETIC_CALCULATIONS_CONST_PI):
                    a12n = a21n+GEODETIC_CALCULATIONS_CONST_PI
                u1n = u2n
                lon1n = lon2n
                sigres = sigres-disn
                if(sigres > 100000.0):
                    disn = 100000.0
                else:
                    disn = sigres		
            azimuth = a12
            distance = s
        return GEODETIC_CALCULATIONS_NO_ERROR, azimuth, distance

    def enu_2_geocentric(self,longitude,latitude,inc_e,inc_n,inc_u):
        """
        brief Paso de un vector de coordenadas geodésicas locales ENU a cartesianas cartesianas geocéntricas.
        param[in]: latitude - Latitud geodésica, en RAD.
        param[in]: longitude - Longitud geodésica, en RAD.
        param[in]: inc_e - Componente este, en metros.
        param[in]: inc_n - Componente norte, en metros.
        param[in]: inc_u - Componente cenital, en metros.
        return[0]: Entero con el estado de error.
        return[1]: inc_x - Incremento de coordenada x cartesiana geocéntrica, en metros.
        return[2]: inc_y - Incremento de coordenada y cartesiana geocéntrica, en metros.
        return[3]: inc_z- Incremento de coordenada z cartesiana geocéntrica, en metros.
        """
        if (latitude < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or
            latitude > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE):
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE
        
        if (longitude < GEODETIC_CALCULATIONS_CONST_MIN_LONGITUDE or 
            longitude>GEODETIC_CALCULATIONS_CONST_MAX_LONGITUDE):
            return GEODETIC_CALCULATIONS_LONGITUDE_ERROR,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE
        
        inc_x = -sin(longitude)*inc_e-sin(latitude)*cos(longitude)*inc_n\
                +cos(latitude)*cos(longitude)*inc_u
        inc_y = cos(longitude)*inc_e-sin(latitude)*sin(longitude)*inc_n\
                +cos(latitude)*sin(longitude)*inc_u
        inc_z = cos(latitude)*inc_n+sin(latitude)*inc_u
        
        return GEODETIC_CALCULATIONS_NO_ERROR,inc_x,inc_y,inc_z 

    def enu_2_polar(self,inc_e,inc_n,inc_u):
        """
        brief: Paso de un vector de coordenadas geodésicas locales ENU a coordenadas geodésicas locales polares.
        param[in]: inc_e - Componente este, en metros.
        param[in]: inc_n - Componente norte, en metros.
        param[in]: inc_u - Componente cenital, en metros.
        return[0] Entero con el estado de error.
        return[1]: azimuth - azimut del vector, en RAD.
        return[2]: vertical - ángulo cenital, en RAD.
        return[3]: spatial_distance - longitud del vector, en metros.
        """
        spatial_distance = sqrt(pow(inc_n,2.0)+pow(inc_e,2.0)+pow(inc_u,2.0))
        vertical = GEODETIC_CALCULATIONS_CONST_PI/2.0-asin(inc_u/(spatial_distance))
        azimuth = atan2(inc_e,inc_n)
        if(azimuth < 0.0):
            azimuth = azimuth+2.0*GEODETIC_CALCULATIONS_CONST_PI
        
        return GEODETIC_CALCULATIONS_NO_ERROR,azimuth,vertical,spatial_distance

    def geocentric_2_enu(self,latitude,longitude,inc_x,inc_y,inc_z):
        """      
        brief Paso de un vector de coordenadas cartesianas geocéntricas a coordenadas geodésica locales ENU.
        param[in]: latitude - Latitud geodésica, en RAD.
        param[in]: longitude - Longitud geodésica, en RAD.
        param[in]: inc_x - Incremento de coordenada x cartesiana geocéntrica, en metros
        param[in]: inc_y - Incremento de coordenada y cartesiana geocéntrica, en metros
        param[in]: inc_z - Incremento de coordenada z cartesiana geocéntrica, en metros
        return[0]: Entero con el estado de error.
        return[1]: inc_e - componente este, en metros
        return[2]: inc_n - componente norte, en metros
        return[3]: inc_u - componente cenital, en metros
        """
        if (latitude < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or
            latitude > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE):
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE
        
        if (longitude < GEODETIC_CALCULATIONS_CONST_MIN_LONGITUDE or 
            longitude>GEODETIC_CALCULATIONS_CONST_MAX_LONGITUDE):
            return GEODETIC_CALCULATIONS_LONGITUDE_ERROR,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE
        
        inc_e = -sin(longitude)*inc_x+cos(longitude)*inc_y
        inc_n = -sin(latitude)*cos(longitude)*inc_x-sin(latitude)*sin(longitude)\
                *inc_y+cos(latitude)*inc_z    
        inc_u = cos(latitude)*cos(longitude)*inc_x+cos(latitude)*sin(longitude)\
                *inc_y+sin(latitude)*inc_z
        
        return GEODETIC_CALCULATIONS_NO_ERROR,inc_e,inc_n,inc_u

    def geocentric_2_geodetic(self,x,y,z,a,inv_f):
        """
        brief Paso de coordenadas cartesianas geocéntricas a coordenadas geodésicas.
        param[in]: x - Coordenada x cartesiana geocéntrica, en metros.
        param[in]: y - Coordenada y cartesiana geocéntrica, en metros.
        param[in]: z - Coordenada z cartesiana geocéntrica, en metros.
        param[in]: a - Semieje mayor del elipsoide, en metros.
        param[in]: inv_f - Inverso del aplanamiento del elipsoide.
        return[0]: Entero con el estado de error.
        return[1]: latitude - latitud geodésica, en RAD.
        return[2]: longitude -  longitud geodésica, en RAD.
        return[3]: h - altitud elipsoidal, en  metros.
        """
        
        if inv_f != 0.0 and (a < GEODETIC_CALCULATIONS_CONST_MIN_SEMI_MAYOR_AXIS or a > GEODETIC_CALCULATIONS_CONST_MAX_SEMI_MAYOR_AXIS):
            #1003 - Semieje mayor del elipsoide fuera de dominio.
            return GEODETIC_CALCULATIONS_A_ERROR,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE
        if inv_f != 0.0 and (inv_f < GEODETIC_CALCULATIONS_CONST_MIN_INVERSE_FLATTENING or inv_f > GEODETIC_CALCULATIONS_CONST_MAX_INVERSE_FLATTENING):
            #1004 - Inverso del aplanamiento del elipsoide fuera de dominio.
            return GEODETIC_CALCULATIONS_INV_F_ERROR,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE
                
        lon = atan2(y,x)
        if inv_f == 0:
            helip = sqrt(pow(x,2.0)+pow(y,2.0)+pow(z,2.0))-a
            lat = asin(z/(a+helip))
        else:
            e2 = 2.0/inv_f-pow(1.0/inv_f,2.0)
            tolerance = GEODETIC_CALCULATIONS_CONST_ANGULAR_TOLERANCE
            p = sqrt(pow(x,2.0)+pow(y,2.0))
            lat0 = atan(z/p/(1.0-e2)) 
            control = 0
            while(control==0):
                state,gnp = self.radius_first_vertical(lat0,a,inv_f)
                if (state!=0):
                    return state,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE
                helip = p/cos(lat0)-gnp
                lat = atan(z/p*(gnp+helip)/(gnp*(1-e2)+helip))
                if (fabs(lat-lat0) > tolerance):
                    lat0=lat
                else:
                   control=1
        if (lat < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or
            lat > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE):
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE
        
        if (lon < GEODETIC_CALCULATIONS_CONST_MIN_LONGITUDE or 
            lon >GEODETIC_CALCULATIONS_CONST_MAX_LONGITUDE):
            return GEODETIC_CALCULATIONS_LONGITUDE_ERROR,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE

        latitude = lat
        longitude = lon
        h  = helip
        return GEODETIC_CALCULATIONS_NO_ERROR,latitude,longitude,h
        
    def geodetic_2_geocentric(self,latitude,longitude,h,a,inv_f):
        """
        Paso de coordenadas geodésicas a coordenadas cartesianas geocéntricas
        :param latitude: latitude - Latitud geodésica, en RAD
        :type latitude: float
        :param longitude: longitude - Longitud geodésica, en RAD
        :type longitude: float
        :param h: Altitud elipsoidal, en  metros
        :type h: float
        :param a: Semieje mayor del elipsoide, en metros
        :type a: float
        :param inv_f: Inverso del aplanamiento del elipsoide
        :return:    x - coordenada x cartesiana geocéntrica, en metros.
                    y - coordenada y cartesiana geocéntrica, en metros.
                    z - coordenada z cartesiana geocéntrica, en metros.
        :rtype: float
        """

        if latitude < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or latitude > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            #1001 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE
            
        if longitude < GEODETIC_CALCULATIONS_CONST_MIN_LONGITUDE or longitude > GEODETIC_CALCULATIONS_CONST_MAX_LONGITUDE:
            #1002 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LONGITUDE_ERROR,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE
            
        if inv_f != 0.0 and (a < GEODETIC_CALCULATIONS_CONST_MIN_SEMI_MAYOR_AXIS or a > GEODETIC_CALCULATIONS_CONST_MAX_SEMI_MAYOR_AXIS):
            #1003 - Semieje mayor del elipsoide fuera de dominio.
            return GEODETIC_CALCULATIONS_A_ERROR,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE
            
        if inv_f != 0.0 and (inv_f < GEODETIC_CALCULATIONS_CONST_MIN_INVERSE_FLATTENING or inv_f > GEODETIC_CALCULATIONS_CONST_MAX_INVERSE_FLATTENING):
            #1004 - Inverso del aplanamiento del elipsoide fuera de dominio.
            return GEODETIC_CALCULATIONS_INV_F_ERROR,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE
        
        if inv_f==0:
            n = a
            x = (n+h)*cos(latitude)*cos(longitude)
            y = (n+h)*cos(latitude)*sin(longitude)
            z = (n+h)*sin(latitude)        
        else:
            e2 = 2.0/inv_f-pow(1.0/inv_f,2.0)
            state,n = self.radius_first_vertical(latitude,a,inv_f)
            if state!= 0:
                return state,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE
               
            x = (n+h)*cos(latitude)*cos(longitude)
            y = (n+h)*cos(latitude)*sin(longitude)
            z = (n*(1.0-e2)+h)*sin(latitude)
        
        return GEODETIC_CALCULATIONS_NO_ERROR,x,y,z

    def gd_lat_2_aut_lat(self,geodetic,inv_f):
        """
        brief Paso de latitud geodésica a latitud autálica.
        param[in]: geodetic - Latitud geodésica, en RAD.
        param[in]: inv_f - Inverso del aplanamiento del elipsoide.
        return[0]: Entero con el estado de error.
        return[1]: authalic - latitud autálica calculada, en RAD.
        """
        
        if geodetic < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or geodetic > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            #1001 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE

        if inv_f != 0.0 and (inv_f < GEODETIC_CALCULATIONS_CONST_MIN_INVERSE_FLATTENING or inv_f > GEODETIC_CALCULATIONS_CONST_MAX_INVERSE_FLATTENING):
            #1004 - Inverso del aplanamiento del elipsoide fuera de dominio.
            return GEODETIC_CALCULATIONS_INV_F_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE
        
        if geodetic == -GEODETIC_CALCULATIONS_CONST_PI/2.0 or geodetic == GEODETIC_CALCULATIONS_CONST_PI/2.0:
            authalic = geodetic
        else:
            e2 = 2.0/inv_f-pow(1.0/inv_f,2.0)
            sqrt_e2 = sqrt(e2)
            s_lat = sin(geodetic)
            q = (1.0-e2)*(s_lat/(1.0-e2*pow(s_lat,2.0))-1.0/(2.0*sqrt_e2)\
                *log((1.0-sqrt_e2*s_lat)/(1.0+sqrt_e2*s_lat)))
            qp = (1.0-e2)*(1.0/(1.0-e2)-1.0/(2.0*sqrt_e2)\
                *log((1.0-sqrt_e2)/(1.0+sqrt_e2)))
            q_over_qp = q/qp
            if q_over_qp > 1:
                q_over_qp = 1
            if q_over_qp < -1:
                q_over_qp = -1
            authalic = asin(q_over_qp)
            
        return GEODETIC_CALCULATIONS_NO_ERROR,authalic

    def gd_lat_2_iso_lat(self,geodetic,inv_f):
        """
        brief Paso de latitud geodésica a latitud isométrica.
        param[in]: geodetic - Latitud geodésica, en RAD.
        param[in]: inv_f - Inverso del aplanamiento del elipsoide.
        return[0]: Entero con el estado de error.
        return[1]: isometric - latitud isométrica calculada, en RAD.
        """
       
        if geodetic < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or geodetic > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            #1001 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR, GEODETIC_CALCULATIONS_NULL_VALUE
        if inv_f != 0.0 and (inv_f < GEODETIC_CALCULATIONS_CONST_MIN_INVERSE_FLATTENING or inv_f > GEODETIC_CALCULATIONS_CONST_MAX_INVERSE_FLATTENING):
            #1004 - Inverso del aplanamiento del elipsoide fuera de dominio.
            return GEODETIC_CALCULATIONS_INV_F_ERROR, GEODETIC_CALCULATIONS_NULL_VALUE
        
        c1 = tan(GEODETIC_CALCULATIONS_CONST_PI/4.0+geodetic/2.0)
        if inv_f==0:
            isometric=log(c1)
        else:
            sqrt_e2 = sqrt(2.0/inv_f-pow(1.0/inv_f,2.0))
            c2 = pow((1.0-sqrt_e2*sin(geodetic))/(1.0+sqrt_e2*sin(geodetic)),(sqrt_e2/2.0))
            isometric = log(c1*c2)
            
        return GEODETIC_CALCULATIONS_NO_ERROR,isometric
    
    def gd_lat_2_rect_lat(self,geodetic,a,inv_f):
        """
        brief Paso de latitud geodésica a latitud rectificante.
        param[in]: geodetic - Latitud geodésica, en RAD.
        param[in]: a - Semieje mayor del elipsoide, en metros.
        param[in]: inv_f - Inverso del aplanamiento del elipsoide.
        return[0]: Entero con el estado de error.
        return[1]: rectifying - latitud rectificada calculada, en RAD.
        """
  
        if geodetic < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or geodetic > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            #1001 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR, GEODETIC_CALCULATIONS_NULL_VALUE

        if inv_f != 0.0 and (a < GEODETIC_CALCULATIONS_CONST_MIN_SEMI_MAYOR_AXIS or a > GEODETIC_CALCULATIONS_CONST_MAX_SEMI_MAYOR_AXIS):
            #1003 - Semieje mayor del elipsoide fuera de dominio.
            return GEODETIC_CALCULATIONS_A_ERROR, GEODETIC_CALCULATIONS_NULL_VALUE

        if inv_f != 0.0 and (inv_f < GEODETIC_CALCULATIONS_CONST_MIN_INVERSE_FLATTENING or inv_f > GEODETIC_CALCULATIONS_CONST_MAX_INVERSE_FLATTENING):
            #1004 - Inverso del aplanamiento del elipsoide fuera de dominio.
            return GEODETIC_CALCULATIONS_INV_F_ERROR, GEODETIC_CALCULATIONS_NULL_VALUE
                    
        geoCalError,longMer = self.longitude_meridian(geodetic,a,inv_f)
        if geoCalError!= 0:
            return geoCalError, GEODETIC_CALCULATIONS_NULL_VALUE
                   
        geoCalError,longMerHalfPi = self.longitude_meridian(GEODETIC_CALCULATIONS_CONST_PI/2.0,a,inv_f)
        if geoCalError!= 0:
            return geoCalError, GEODETIC_CALCULATIONS_NULL_VALUE
                   
        rectifying = GEODETIC_CALCULATIONS_CONST_PI/2.0*longMer/longMerHalfPi
        return GEODETIC_CALCULATIONS_NO_ERROR,rectifying

    def get_ellipsoid_height(self,
                             int_crs_point,
                             first_coordinate,
                             second_coordinate,
                             third_coordinate):
        """
        Brief: Obtiene la altura elipsoidal de un punto
        :param crs: Código EPSG del CRS de la posición planimétrica del punto. (4258)
        :type crs: int
        :param first_coordinate: Primera coordenada de la posición planimétrica del punto, si es geodésica en DEG
        :type first_coordinate: float
        :param second_coordinate: Segunda coordenada de la posición planimétrica del punto, si es geodésica en DEG
        :type second_coordinate: float
        :param third_coordinate: Altitud ortométrica (dtm_height + height_of_flight), en metros
        :type third_coordinate: float
        :return: altura elipsoidal
        """

        # Si el crs origen es proyectado hay que pasar al elipsoide
        # cambio de CRS
        if (int_crs_point != c.CONST_MICRODRON_WAY_POINT_LIBRARY_POSTGIS_SRID_CRS_CODE): # CRS - EPSG: 4258 ETRS89
            qgs_point_transform = self.q3_api_op.transform_point_coordinates(first_coordinate,
                                                                             second_coordinate,
                                                                             int_crs_point,
                                                                             c.CONST_MICRODRON_WAY_POINT_LIBRARY_POSTGIS_SRID_CRS_CODE)

            first_coordinate_transform = qgs_point_transform.x()
            second_coordinate_transform = qgs_point_transform.y()
        else:
            first_coordinate_transform = first_coordinate
            second_coordinate_transform = second_coordinate

        # parámetros EPSG 4326 WGS84
        """
        a = 6378137 #TODO: cogerlo desde la base de datos
        inv_f = 298.257223563 #TODO: cogerlo desde la base de datos
        """

        # parámetros EPSG 4258 ETRS89
        a = 6378137 #TODO: cogerlo desde la base de datos
        inv_f = 298.257222101 #TODO: cogerlo desde la base de datos

        ondulation = self.instance_py_geoid.get_ondulation_from_geoid_interpolate(first_coordinate_transform,
                                                                                  second_coordinate_transform,
                                                                                  c.CONST_MICRODRON_WAY_POINT_LIBRARY_POSTGIS_SRID_CRS_CODE)

        ellipsoid_height = third_coordinate + ondulation

        return ellipsoid_height

    def iso_lat_2_gd_lat(self,isometric,inv_f):
        """
        brief Paso de latitud isométrica a latitud geodésica.
        param[in]: isometric - Latitud isometrica, en RAD.
        param[in]: inv_f - Inverso del aplanamiento del elipsoide.
        return[0]: Entero con el estado de error.
        return[1]: geodetic - latitud geodésica calculada, en RAD.
        """
        t=0
        if inv_f != 0.0 and (inv_f < GEODETIC_CALCULATIONS_CONST_MIN_INVERSE_FLATTENING or inv_f > GEODETIC_CALCULATIONS_CONST_MAX_INVERSE_FLATTENING):
            #1004 - Inverso del aplanamiento del elipsoide fuera de dominio.
            return GEODETIC_CALCULATIONS_INV_F_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE
                
        if inv_f == 0:
            geodetic = 2.0*(atan(exp(isometric)/c)-GEODETIC_CALCULATIONS_CONST_PI/4.0)
        else:
            sqrt_e2 = sqrt(2.0/inv_f-pow(1.0/inv_f,2.0))
            tolerance = GEODETIC_CALCULATIONS_CONST_ANGULAR_TOLERANCE
            fi1 = 2.0*(atan(exp(isometric))-GEODETIC_CALCULATIONS_CONST_PI/4.0) 
            while t == 0:
                c = pow(((1.0-sqrt_e2*sin(fi1))/(1.0+sqrt_e2*sin(fi1))),(sqrt_e2/2.0))
                fi2 = 2.0*(atan(exp(isometric)/c)-GEODETIC_CALCULATIONS_CONST_PI/4.0)
                if (fabs(fi2-fi1)>tolerance):
                    fi1=fi2
                else:
                    t=1
            
        if fi2 < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or fi2 > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE
        geodetic = fi2
        return GEODETIC_CALCULATIONS_NO_ERROR,geodetic

    def longitude_meridian(self,latitude,a,inv_f):
        """
        brief Cálculo de la longitud de arco de meridiano para una latitud geodésica y un elipsoide.
        param[in]: latitude - Latitud geodésica, en RAD.
        param[in]: a - Semieje mayor del elipsoide, en metros.
        param[in]: inv_f - Inverso del aplanamiento del elipsoide.
        return[0]: Entero con el estado de error.
        return[1]: longmer - longitud calculada, en metros.
        """

        if latitude < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or latitude > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            #1001 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE
            
        if inv_f != 0.0 and (a < GEODETIC_CALCULATIONS_CONST_MIN_SEMI_MAYOR_AXIS or a > GEODETIC_CALCULATIONS_CONST_MAX_SEMI_MAYOR_AXIS):
            #1003 - Semieje mayor del elipsoide fuera de dominio.
            return GEODETIC_CALCULATIONS_A_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE
            
        if inv_f != 0.0 and (inv_f < GEODETIC_CALCULATIONS_CONST_MIN_INVERSE_FLATTENING or inv_f > GEODETIC_CALCULATIONS_CONST_MAX_INVERSE_FLATTENING):
            #1004 - Inverso del aplanamiento del elipsoide fuera de dominio.
            return GEODETIC_CALCULATIONS_INV_F_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE

        if inv_f == 0:
            longmer = a*latitude
        else:
            e2 = 2.0/inv_f-pow(1.0/inv_f,2.0)
            c0 = a*(1.0-e2)
            s = sin(latitude)
            c = cos(latitude)
            c1 = latitude
            c2 = 3.0/2.0*e2*(-1.0/2.0*c*s+1.0/2.0*latitude)
            c3 = 15.0/8.0*pow(e2,2.0)*(-1.0/4.0*pow(s,3.0)*c-3.0/8.0*c*s+3.0/8.0*latitude)
            c4 = 35.0/16.0*pow(e2,3.0)*(-1.0/6.0*pow(s,5.0)*c-5.0/24.0*pow(s,3.0)*c-5.0/16.0*c*s+5.0/16.0*latitude)
            c51 = -1.0/8.0*pow(s,7.0)*c-7.0/48.0*pow(s,5.0)*c
            c52 = -35.0/192.0*pow(s,3.0)*c-35.0/128.0*c*s+35.0/128.0*latitude
            c5 = 315.0/128.0*pow(e2,4.0)*(c51+c52)
            c61 = -1.0/10.0*pow(s,9.0)*c-9.0/80.0*pow(s,7.0)*c-21.0/160.0*pow(s,5.0)*c
            c62 = -21.0/128.0*pow(s,3.0)*c-63.0/256.0*c*s+63.0/256.0*latitude
            c6 = 693.0/256.0*pow(e2,5.0)*(c61+c62)
            longmer = c0*(c1+c2+c3+c4+c5+c6)
        
        return GEODETIC_CALCULATIONS_NO_ERROR,longmer
        
    def longitude_meridian_2_gd_lat(self,longmer,a,inv_f):
        """
        brief Cálculo de la latitud geodésica a partir de la longitud de arco de meridiano para una latitud y un elipsoide.
        param[in]: longmer - Longitud de arco de meridiano, en metros.
        param[in]: a - Semieje mayor del elipsoide, en metros.
        param[in]: inv_f - Inverso del aplanamiento del elipsoide.
        return[0]: Entero con el estado de error.
        return[1]: latitude - latitud geodésica calculada, en RAD. 
        """
        control = 0
        if inv_f != 0.0 and (a < GEODETIC_CALCULATIONS_CONST_MIN_SEMI_MAYOR_AXIS or a > GEODETIC_CALCULATIONS_CONST_MAX_SEMI_MAYOR_AXIS):
            #1003 - Semieje mayor del elipsoide fuera de dominio.
            return GEODETIC_CALCULATIONS_A_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE
            
        if inv_f != 0.0 and (inv_f < GEODETIC_CALCULATIONS_CONST_MIN_INVERSE_FLATTENING or inv_f > GEODETIC_CALCULATIONS_CONST_MAX_INVERSE_FLATTENING):
            #1004 - Inverso del aplanamiento del elipsoide fuera de dominio.
            return GEODETIC_CALCULATIONS_INV_F_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE
                
        if(inv_f==0):
            latitude=longmer/a
        else:
            e2 = 2.0/inv_f-pow(1.0/inv_f,2.0)
            tolerance = GEODETIC_CALCULATIONS_CONST_ANGULAR_TOLERANCE
            c0 = a*(1.0-e2)
            fi0 = longmer/c0
            while control == 0:
                s = sin(fi0)
                c = cos(fi0)
                c2 = 3.0/2.0*e2*(-1.0/2.0*c*s+1.0/2.0*fi0)
                c3 = 15.0/8.0*pow(e2,2.0)*(-1.0/4.0*pow(s,3.0)*c-3.0/8.0*c*s+3.0/8.0*fi0)
                c4 = 35.0/16.0*pow(e2,3.0)*(-1.0/6.0*pow(s,5.0)*c-5.0/24.0\
                    *pow(s,3.0)*c-5.0/16.0*c*s+5.0/16.0*fi0)
                c51 = -1.0/8.0*pow(s,7.0)*c-7.0/48.0*pow(s,5.0)*c
                c52 = -35.0/192.0*pow(s,3.0)*c-35.0/128.0*c*s+35.0/128.0*fi0
                c5 = 315.0/128.0*pow(e2,4.0)*(c51+c52)
                c61 = -1.0/10.0*pow(s,9.0)*c-9.0/80.0*pow(s,7.0)*c-21.0/160.0\
                    *pow(s,5.0)*c
                c62 = -21.0/128.0*pow(s,3.0)*c-63.0/256.0*c*s+63.0/256.0*fi0
                c6 = 693.0/256.0*pow(e2,5.0)*(c61+c62)
                fi = longmer/c0-(c2+c3+c4+c5+c6)
                if (fabs(fi-fi0)>tolerance):
                    fi0=fi
                else:
                    control=1
            latitude = fi
        if latitude < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or latitude > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
        #1001 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE
        
        return GEODETIC_CALCULATIONS_NO_ERROR,latitude  
        
    def polar_2_enu(self,azimuth,vertical,spatial_distance):
        """
        brief Paso de un vector de coordenadas geodésicas locales polares a coordenadas geodésicas locales ENU.
        param[in]: azimuth - Azimut del vector, en RAD.
        param[in]: vertical - Ángulo cenital, en RAD.
        param[in]: spatial_distance Longitud del vector, en metros.
        return[0]: Entero con el estado de error.
        return[1]: inc_e - componente este, en metros.
        return[2]: inc_n - componente norte, en metros.
        return[3]: inc_u - componente cenital, en metros.
        """
        inc_u = spatial_distance*cos(vertical)
        inc_n = spatial_distance*sin(vertical)*cos(azimuth)
        inc_e = spatial_distance*sin(vertical)*sin(azimuth)
        
        return GEODETIC_CALCULATIONS_NO_ERROR,inc_u,inc_n,inc_e
        
    def radius_euler(self,rn,rm,azimuth):
        """
        brief Cálculo del radio de Euler en un punto del elipsoide y para un azimut geodésico.
        param[in]: rn - Radio del primer vertical, en metros.
        param[in]: rm - Radio de la elipse meridiana, en metros.
        param[in]: azimuth - Azimuth de la línea, en RAD.
        return[0]: Entero con el estado de error.
        return[1]: radius- radio calculado, en metros.
        """
        radius = 1.0/(pow(cos(azimuth),2.0)/rm+pow(sin(azimuth),2.0)/rn)
        return GEODETIC_CALCULATIONS_NO_ERROR,radius
        
    def radius_gauss(self,latitude,a,inv_f):
        """
        brief Cálculo del radio de Gauss para una latitud geodésica y un elipsoide.
        param[in]: latitude - Latitud geodésica, en RAD.
        param[in]: a - Semieje mayor del elipsoide, en metros.
        param[in]: inv_f - Inverso del aplanamiento del elipsoide.
        return[0]: Entero con el estado de error.
        return[1]: radius - radio calculado, en metros.
        """
        if latitude < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or latitude > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            #1001 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE
        
        state,rn = self.radius_first_vertical(latitude,a,inv_f)
        if (state!=0):
            return state,GEODETIC_CALCULATIONS_NULL_VALUE
        state,rm = self.radius_meridian_ellipse(latitude,a,inv_f)
        if (state!=0):
            return state,GEODETIC_CALCULATIONS_NULL_VALUE
            
        radius = sqrt(rm*rn)
        
        return GEODETIC_CALCULATIONS_NO_ERROR,radius
        
    def radius_first_vertical(self,latitude,a,inv_f):
        """
        brief Cálculo del radio del primer vertical para una latitud geodésica y un elipsoide.
        param[in]: latitude - Latitud geodésica, en RAD.
        param[in]: a - Semieje mayor del elipsoide, en metros.
        param[in]: inv_f - Inverso del aplanamiento del elipsoide.
        return[0]: Entero con el estado de error.
        return[1]: radius - radio calculado, en metros.
        """
        
        if latitude < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or latitude > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            #1001 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE
        
        if inv_f != 0.0 and (a < GEODETIC_CALCULATIONS_CONST_MIN_SEMI_MAYOR_AXIS or a > GEODETIC_CALCULATIONS_CONST_MAX_SEMI_MAYOR_AXIS):
            #1003 - Semieje mayor del elipsoide fuera de dominio.
            return GEODETIC_CALCULATIONS_A_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE        
        
        if inv_f != 0.0 and (inv_f < GEODETIC_CALCULATIONS_CONST_MIN_INVERSE_FLATTENING or inv_f > GEODETIC_CALCULATIONS_CONST_MAX_INVERSE_FLATTENING):
            #1004 - Inverso del aplanamiento del elipsoide fuera de dominio.
            return GEODETIC_CALCULATIONS_INV_F_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE        

        if inv_f == 0:
            radius=a
        else:
            e2 = 2.0/inv_f-pow(1.0/inv_f,2.0)
            radius = a/sqrt(1.0-e2*pow(sin(latitude),2.0))
        
        return GEODETIC_CALCULATIONS_NO_ERROR,radius
        
    def radius_meridian_ellipse(self,latitude,a,inv_f):
        """
        brief Cálculo del radio de la elipse meridiana para una latitud geodésica y un elipsoide.
        param[in]: latitude - Latitud geodésica, en RAD.
        param[in]: a - Semieje mayor del elipsoide, en metros.
        param[in]: inv_f - Inverso del aplanamiento del elipsoide.
        return[0]: Entero con el estado de error.
        return[1]: radius - radio calculado, en metros.
        """
       
        if latitude < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or latitude > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            #1001 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE
                        
        if inv_f != 0.0 and (a < GEODETIC_CALCULATIONS_CONST_MIN_SEMI_MAYOR_AXIS or a > GEODETIC_CALCULATIONS_CONST_MAX_SEMI_MAYOR_AXIS):
            #1003 - Semieje mayor del elipsoide fuera de dominio.
            return GEODETIC_CALCULATIONS_A_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE
            
        if inv_f != 0.0 and (inv_f < GEODETIC_CALCULATIONS_CONST_MIN_INVERSE_FLATTENING or inv_f > GEODETIC_CALCULATIONS_CONST_MAX_INVERSE_FLATTENING):
            #1004 - Inverso del aplanamiento del elipsoide fuera de dominio.
            return GEODETIC_CALCULATIONS_INV_F_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE
        
        if inv_f ==0:
            radius=a
        else:
            e2 = 2.0/inv_f-pow(1.0/inv_f,2.0)
            radius = a*(1.0-e2)/pow(1.0-e2*pow(sin(latitude),2.0),3.0/2.0)
        return GEODETIC_CALCULATIONS_NO_ERROR,radius

    def rect_lat_2_gd_lat(self,rectifying,a,inv_f):
        """
        brief Paso de latitud rectificada a latitud geodésica.
        param[in]: rectifying Latitud rectificada, en RAD.
        param[in]: a - Semieje mayor del elipsoide, en metros.
        param[in]: inv_f - Inverso del aplanamiento del elipsoide.
        return[0]: Entero con el estado de error.
        return[1]: geodetic -latitud geodésica calculada, en RAD.
        """
        if rectifying < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or rectifying > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            #1001 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE
                        
        if inv_f != 0.0 and (a < GEODETIC_CALCULATIONS_CONST_MIN_SEMI_MAYOR_AXIS or a > GEODETIC_CALCULATIONS_CONST_MAX_SEMI_MAYOR_AXIS):
            #1003 - Semieje mayor del elipsoide fuera de dominio.
            return GEODETIC_CALCULATIONS_A_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE
            
        if inv_f != 0.0 and (inv_f < GEODETIC_CALCULATIONS_CONST_MIN_INVERSE_FLATTENING or inv_f > GEODETIC_CALCULATIONS_CONST_MAX_INVERSE_FLATTENING):
            #1004 - Inverso del aplanamiento del elipsoide fuera de dominio.
            return GEODETIC_CALCULATIONS_INV_F_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE
        
        geoCalError,longMerHalfPi = self.longitude_meridian(GEODETIC_CALCULATIONS_CONST_PI/2.0,a,inv_f)
        if geoCalError!= 0:
            return geoCalError, GEODETIC_CALCULATIONS_NULL_VALUE
        
        longMer = 2.0/GEODETIC_CALCULATIONS_CONST_PI*longMerHalfPi
        geoCalError,geodetic = self.longitude_meridian_2_gd_lat(longMer,a,inv_f)
        if geoCalError != 0:
            return geoCalError, GEODETIC_CALCULATIONS_NULL_VALUE
        
        return GEODETIC_CALCULATIONS_NO_ERROR,geodetic
        
    def sphere_axis_rotation_forward(self,beforeLatitude,beforeLongitude,newNorthPole,newOriginLongitude):
        """
        brief Paso directo en el cambio de polo en la esfera.
        param[in]: beforeLatitude     Latitud geodésica antes del cambio de polo, en RAD.
        param[in]: beforeLongitude    Longitud geodésica antes del cambio de polo, en RAD.
        param[in]: newNorthPole       Latitud geodésica del punto que sera el nuevo polo, en RAD.
        param[in]: newOriginLongitude Longitud geodésica del punto que sera el nuevo polo, en RAD.
        return[0]: Entero con el estado de error.
        return[1]: afterLatitude      latitud geodésica despues del cambio de polo, en RAD.
        return[2]: afterLongitude     longitud geodésica despues del cambio de polo, en RAD.
        return[3]: convergence        ángulo que hay que restar a las geodésicas en la
                                       esfera tras el cambio de base para obtener las
                                       correspondientes geodésicas antes del cambio de polo
        """

        if beforeLatitude < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or beforeLatitude > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            #1001 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE                    
            
        if beforeLongitude < GEODETIC_CALCULATIONS_CONST_MIN_LONGITUDE or beforeLongitude > GEODETIC_CALCULATIONS_CONST_MAX_LONGITUDE:
            #1002 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LONGITUDE_ERROR,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE  

        if newNorthPole < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or newNorthPole > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            #1001 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE  
            
        if newOriginLongitude < GEODETIC_CALCULATIONS_CONST_MIN_LONGITUDE or newOriginLongitude > GEODETIC_CALCULATIONS_CONST_MAX_LONGITUDE:
            #1002 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LONGITUDE_ERROR,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE  

        sin_nol = sin(newOriginLongitude)
        cos_nol = cos(newOriginLongitude)
        sin_nnp = sin(newNorthPole)
        cos_nnp = cos(newNorthPole)
        mr11 = -sin_nnp*cos_nol
        mr12 = -sin_nnp*sin_nol
        mr13 = cos_nnp
        mr21 = sin_nol
        mr22 = -cos_nol
        mr23 = 0.0
        mr31 = cos_nnp*cos_nol
        mr32 = cos_nnp*sin_nol
        mr33 = sin_nnp
        vp1 = cos(beforeLatitude)*cos(beforeLongitude)
        vp2 = cos(beforeLatitude)*sin(beforeLongitude)
        vp3 = sin(beforeLatitude)
        vpr1 = mr11*vp1+mr12*vp2+mr13*vp3
        vpr2 = mr21*vp1+mr22*vp2+mr23*vp3
        vpr3 = mr31*vp1+mr32*vp2+mr33*vp3
        afterLatitude = asin(vpr3)
        afterLongitude = atan2(vpr2,vpr1)
        geoCalError,azimuth,distance = self.sphere_inverse_problem(beforeLatitude,beforeLongitude,newNorthPole,newOriginLongitude,1.0)# ESTO SIEMPRE VA A DAR EL ERROR 1003
        if geoCalError!= 0:
            return geoCalError,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE  
        convergence = 2.0*GEODETIC_CALCULATIONS_CONST_PI-azimuth
        if convergence<0:
            convergence = convergence+2.0*GEODETIC_CALCULATIONS_CONST_PI
        return GEODETIC_CALCULATIONS_NO_ERROR,afterLatitude,afterLongitude,convergence
        
    def sphere_axis_rotation_inverse(self,afterLatitude,afterLongitude,newNorthPole,newOriginLongitude):
        """
        brief Paso inverso en el cambio de polo en la esfera.
        param[in]: afterLatitude      Latitud geodésica despues del cambio de polo, en RAD.
        param[in]: afterLongitude     Longitud geodésica despues del cambio de polo, en RAD.
        param[in]: newNorthPole       Latitud geodésica del punto que sera el nuevo polo, en RAD.
        param[in]: newOriginLongitude Longitud geodésica del punto que sera el nuevo polo, en RAD.
        return[0]: Entero con el estado de error.
        return[1]: beforeLatitude     latitud geodésica antes del cambio de polo, en RAD.
        return[2]: beforeLongitude    longitud geodésica antes del cambio de polo, en RAD.
        return[3]: convergence        ángulo que hay que restar a las geodésicas en la
                                       esfera tras el cambio de base para obtener las
                                       correspondientes geodésicas antes del cambio de polo

        """
        if afterLatitude < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or afterLatitude > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            #1001 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE  
            
        if afterLongitude < GEODETIC_CALCULATIONS_CONST_MIN_LONGITUDE or afterLongitude > GEODETIC_CALCULATIONS_CONST_MAX_LONGITUDE:
            #1002 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LONGITUDE_ERROR,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE  

        if newNorthPole < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or newNorthPole > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            #1001 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE  
            
        if newOriginLongitude < GEODETIC_CALCULATIONS_CONST_MIN_LONGITUDE or newOriginLongitude > GEODETIC_CALCULATIONS_CONST_MAX_LONGITUDE:
            #1002 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LONGITUDE_ERROR,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE  

        sin_nol = sin(newOriginLongitude)
        cos_nol = cos(newOriginLongitude)
        sin_nnp = sin(newNorthPole)
        cos_nnp = cos(newNorthPole)
        mr11 = -sin_nnp*cos_nol
        mr21 = -sin_nnp*sin_nol
        mr31 = cos_nnp
        mr12 = sin_nol
        mr22 = -cos_nol
        mr32 = 0.0
        mr13 = cos_nnp*cos_nol
        mr23 = cos_nnp*sin_nol
        mr33 = sin_nnp
        vp1 = cos(afterLatitude)*cos(afterLongitude)
        vp2 = cos(afterLatitude)*sin(afterLongitude)
        vp3 = sin(afterLatitude)
        vpr1 = mr11*vp1+mr12*vp2+mr13*vp3
        vpr2 = mr21*vp1+mr22*vp2+mr23*vp3
        vpr3 = mr31*vp1+mr32*vp2+mr33*vp3
        beforeLatitude = asin(vpr3)
        beforeLongitude = atan2(vpr2,vpr1)
        geoCalError,azimuth,distance = self.sphere_inverse_problem(beforeLatitude,beforeLongitude,newNorthPole,newOriginLongitude,1.0)# ESTO SIEMPRE VA A DAR EL ERROR 1003
        if geoCalError!=0:
            return geoCalError,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE,\
                    GEODETIC_CALCULATIONS_NULL_VALUE  
        convergence = 2.0*GEODETIC_CALCULATIONS_CONST_PI-azimuth
        if(convergence < 0):
            convergence = convergence+2.0*GEODETIC_CALCULATIONS_CONST_PI
        return GEODETIC_CALCULATIONS_NO_ERROR,beforeLatitude,beforeLongitude,convergence
        
    def sphere_direct_problem(self, initial_latitude, initial_longitude, azimuth, distance, radius):
        """
        brief: Solución del problema directo de la geodesia sobre la esfera.
        param[in]: initial_latitude - Latitud geodésica origen, en RAD.
        param[in]: initial_longitude - Longitud geodésica origen, en RAD.
        param[in]: azimuth - Azimuth de la linea, en RAD.
        param[in]: distance - Distancia de la linea, en metros.
        param[in]: radius - Radio de la esfera, en metros.
        return[0]: Entero con el estado de error.
        return[1]: final_latitude - latitud geodésica final calculada, en RAD.
        return[2]: final_longitude - longitud geodésica final calculada, en RAD.
        """
        if initial_latitude < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or initial_latitude > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            #1001 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
        if initial_longitude < GEODETIC_CALCULATIONS_CONST_MIN_LONGITUDE or initial_longitude > GEODETIC_CALCULATIONS_CONST_MAX_LONGITUDE:
            #1002 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LONGITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
        if radius < GEODETIC_CALCULATIONS_CONST_MIN_SEMI_MAYOR_AXIS or radius > GEODETIC_CALCULATIONS_CONST_MAX_SEMI_MAYOR_AXIS: 
            #1003 - Semieje mayor del elipsoide fuera de dominio.
            return GEODETIC_CALCULATIONS_A_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
        
        azi = azimuth
        s = distance
        sl1 = sin(initial_longitude)
        cl1 = cos(initial_longitude)
        sf1 = sin(initial_latitude)
        cf1 = cos(initial_latitude)
        mrt11 = -sf1*cl1
        mrt21 = -sf1*sl1
        mrt31 = cf1
        mrt12 = sl1
        mrt22 = -cl1
        mrt32 = 0
        mrt13 = cf1*cl1
        mrt23 = cf1*sl1
        mrt33 = sf1
        if(s > (GEODETIC_CALCULATIONS_CONST_PI * radius)):
            if(azi >= GEODETIC_CALCULATIONS_CONST_PI):
                azi = azi - GEODETIC_CALCULATIONS_CONST_PI
            else:
                azi = azi + GEODETIC_CALCULATIONS_CONST_PI                
            s = 2.0*GEODETIC_CALCULATIONS_CONST_PI*radius-s        
        
        if(azi <= GEODETIC_CALCULATIONS_CONST_PI):
            lon2g = -azi
        else:
            lon2g = 2 * GEODETIC_CALCULATIONS_CONST_PI - azi
        fi2g = GEODETIC_CALCULATIONS_CONST_PI/2.0-s/radius
        r2g1 = cos(fi2g)*cos(lon2g)
        r2g2 = cos(fi2g)*sin(lon2g)
        r2g3 = sin(fi2g)
        r21 = mrt11*r2g1+mrt12*r2g2+mrt13*r2g3
        r22 = mrt21*r2g1+mrt22*r2g2+mrt23*r2g3
        r23 = mrt31*r2g1+mrt32*r2g2+mrt33*r2g3
        final_longitude = atan2(r22,r21)
        final_latitude = asin(r23)
        if final_latitude < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or final_latitude > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            #1001 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
        if final_longitude < GEODETIC_CALCULATIONS_CONST_MIN_LONGITUDE or final_longitude > GEODETIC_CALCULATIONS_CONST_MAX_LONGITUDE:
            #1002 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LONGITUDE_ERROR ,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE   
        return GEODETIC_CALCULATIONS_NO_ERROR, final_longitude, final_latitude

    def sphere_inverse_problem(self,initial_latitude,initial_longitude,final_latitude,final_longitude,radius):
        """
        brief Solución del problema inverso de la geodesia sobre la esfera.
        param[in]: initial_latitude - Latitud geodésica origen, en RAD.
        param[in]: initial_longitude - Longitud geodésica origen, en RAD.
        param[in]: final_latitude - Latitud geodésica final, en RAD.
        param[in]: final_longitude - Longitud geodésica final, en RAD.
        param[in]: radius - Radio de la esfera, en metros.
        return[0]: Entero con el estado de error.
        return[1]: azimuth - Azimuth calculado de la linea, en RAD.
        return[2]: distance - Distancia calculada de la linea, en metros.        
        """
        tolerance = 1e-11 #DUDA: fijamos tolerance en los defines iniciales?

        if initial_latitude < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or initial_latitude > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            #1001 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
        if initial_longitude < GEODETIC_CALCULATIONS_CONST_MIN_LONGITUDE or initial_longitude > GEODETIC_CALCULATIONS_CONST_MAX_LONGITUDE:
            #1002 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LONGITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
        if final_latitude < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or final_latitude > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            #1001 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
        if final_longitude < GEODETIC_CALCULATIONS_CONST_MIN_LONGITUDE or final_longitude > GEODETIC_CALCULATIONS_CONST_MAX_LONGITUDE:
            #1002 - Longitud geodésica fuera de dominio.
            return GEODETIC_CALCULATIONS_LONGITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
        if radius < GEODETIC_CALCULATIONS_CONST_MIN_SEMI_MAYOR_AXIS or radius > GEODETIC_CALCULATIONS_CONST_MAX_SEMI_MAYOR_AXIS:
            #1003 - Semieje mayor del elipsoide fuera de dominio.
            return GEODETIC_CALCULATIONS_A_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE	    
        r21 = cos(final_latitude)*cos(final_longitude)
        r22 = cos(final_latitude)*sin(final_longitude)
        r23 = sin(final_latitude) 
        sl1 = sin(initial_longitude) 
        cl1 = cos(initial_longitude)
        sf1 = sin(initial_latitude)
        cf1 = cos(initial_latitude)
        mr11 = -sf1*cl1
        mr12 = -sf1*sl1
        mr13 = cf1
        mr21 = sl1
        mr22 = -cl1
        mr23 = 0
        mr31 = cf1*cl1
        mr32 = cf1*sl1
        mr33 = sf1
        r2g1 = mr11*r21+mr12*r22+mr13*r23
        r2g2 = mr21*r21+mr22*r22+mr23*r23
        r2g3 = mr31*r21+mr32*r22+mr33*r23
        lon2g = atan2(r2g2,r2g1)
        fi2g = asin(r2g3)
        if(lon2g<0.0):
            azi12 = fabs(lon2g)
        else:
            azi12 = 2.0 * GEODETIC_CALCULATIONS_CONST_PI - lon2g
        if (2.0 * GEODETIC_CALCULATIONS_CONST_PI - azi12) < tolerance:
            azi12 = 0.0
        distance = fabs(GEODETIC_CALCULATIONS_CONST_PI / 2.0 - fi2g) * radius
        azimuth = azi12

        return GEODETIC_CALCULATIONS_NO_ERROR, azimuth, distance

    def tmerc_fwd(self,latitude,longitude,originLatitude,centralMeridian,scaleFactor,falseEasting,falseNorthing,a,inv_f):
        """
        brief: Paso de coordenadas geodésicas a la proyección Transversa de Mercator.
        param[in]: latitude - Latitud geodésicaen RAD., en el dominio [-pi/2,pi/2].
        param[in]: longitude - Longitud geodésicaen RAD., en el dominio ]-pi,pi].
        param[in]: originLatitude - Latitud geodésica origenen RAD., en el dominio [-pi/2,pi/2].
        param[in]: centralMeridian - Longitud geodésica del meridiano centralen RAD., en el dominio ]-pi,pi].
        param[in]: scaleFactor - Factor de escala adimensional.
        param[in]: falseEasting - Coordenada este para el meridiano central, en metros.
        param[in]: falseNorthing - Coordenada norte para el paralelo geodésico origen, en metros.
        param[in]: a - Semieje mayor del elipsoide en metros, en metros.
        param[in]: inv_f - Inverso del aplanamiento del elipsoide adimensional.
        return[0]: Entero con el estado de error.
        return[1]: easting - coordenada Este calculada, en metros.
        return[2]: northing - coordenada Norte calculada, en metros.
        """
        angTolerance = GEODETIC_CALCULATIONS_CONST_ANGULAR_TOLERANCE 

        # Control del dominio de la latitud geodésica
        if latitude < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or latitude > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
            
        #Control del dominio de la longitud geodésica
        if longitude < GEODETIC_CALCULATIONS_CONST_MIN_LONGITUDE or longitude > GEODETIC_CALCULATIONS_CONST_MAX_LONGITUDE:
            return GEODETIC_CALCULATIONS_LONGITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
        
        # Control del dominio de la latitud geodésica
        if originLatitude < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or originLatitude > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
    
        #Control del dominio de la latitud geodésica del paralelo origen
        if originLatitude < GEODETIC_CALCULATIONS_TMERC_MIN_ORIGIN_LATITUDE or originLatitude > GEODETIC_CALCULATIONS_TMERC_MAX_ORIGIN_LATITUDE:
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE

        #Control del dominio de la longitud geodésica del meridiano central
        if centralMeridian < GEODETIC_CALCULATIONS_TMERC_MIN_CENTRAL_MERIDIAN or centralMeridian > GEODETIC_CALCULATIONS_TMERC_MAX_CENTRAL_MERIDIAN:
            return GEODETIC_CALCULATIONS_MAPPROJ_CENTRAL_MERIDIAN_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE

        #Control del dominio del factor de escala
        if scaleFactor < GEODETIC_CALCULATIONS_TMERC_MIN_SCALE_FACTOR or scaleFactor > GEODETIC_CALCULATIONS_TMERC_MAX_SCALE_FACTOR:
            return GEODETIC_CALCULATIONS_MAPPROJ_SCALE_FACTOR_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE

        #Control del dominio del semieje mayor del elipsoide
        if inv_f!=0.0 and (a < GEODETIC_CALCULATIONS_CONST_MIN_SEMI_MAYOR_AXIS or a > GEODETIC_CALCULATIONS_CONST_MAX_SEMI_MAYOR_AXIS):
            return GEODETIC_CALCULATIONS_A_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE

        #Control del dominio del inverso del aplanamiento del elipsoide
        if inv_f!=0.0 and (inv_f < GEODETIC_CALCULATIONS_CONST_MIN_INVERSE_FLATTENING or inv_f > GEODETIC_CALCULATIONS_CONST_MAX_INVERSE_FLATTENING):
            return GEODETIC_CALCULATIONS_INV_F_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE

        if longitude < 0.0:
            longitude += (2.0*GEODETIC_CALCULATIONS_CONST_PI)
        if centralMeridian < 0.0:
            centralMeridian += (2.0*GEODETIC_CALCULATIONS_CONST_PI)
        incLongitude=longitude-centralMeridian
        if incLongitude > GEODETIC_CALCULATIONS_CONST_PI:
            incLongitude -= (2.0*GEODETIC_CALCULATIONS_CONST_PI)
        if incLongitude < -GEODETIC_CALCULATIONS_CONST_PI:
            incLongitude +=(2.0*GEODETIC_CALCULATIONS_CONST_PI)

        _checkIncrementLongitudeInTm = True #Método establecer si se debe hacer control del incremento de longitud geodésica respecto al meridiano central del huso. Por defecto se pone a TRUE en el constructor.

        if(_checkIncrementLongitudeInTm):
            #Control del dominio del incremento de longitud geodésica respecto del meridiano central
            if fabs(incLongitude) > GEODETIC_CALCULATIONS_TMERC_MAX_INC_LONGITUDE + angTolerance:
                return GEODETIC_CALCULATIONS_MAPPROJ_CENTRAL_MERIDIAN_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
        s = sin(latitude)
        c = cos(latitude)
        t = s/c

        if inv_f == 0.0:
            easting = a*scaleFactor*gsl_atanh(c*sin(incLongitude))
            northing = a*scaleFactor*(atan(t/cos(incLongitude))-originLatitude)
        else:
            e2 = 2.0/inv_f-pow(1.0/inv_f,2.0)
            ee2=e2/(1.0-e2)
            nu = sqrt(ee2)*c
            geoCalError,n = self.radius_first_vertical(latitude,a,inv_f)
            if(geoCalError!=0):
                return geoCalError,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
            c2 = pow(c,2.0)
            c3 = pow(c,3.0)
            c4 = pow(c,4.0)
            c5 = pow(c,5.0)
            c6 = pow(c,6.0)
            c7 = pow(c,7.0)
            c8 = pow(c,8.0)
            c9 = pow(c,9.0)
            c10 = pow(c,10.0)
            c11 = pow(c,11.0)
            c12 = pow(c,12.0)
            t2 = pow(t,2.0)
            t4 = pow(t,4.0)
            t6 = pow(t,6.0)
            t8 = pow(t,8.0)
            t10 = pow(t,10.0)
            t12 = pow(t,12.0)
            nu2 = pow(nu,2.0)
            nu4 = pow(nu,4.0)
            nu6 = pow(nu,6.0)
            nu8 = pow(nu,8.0)
            nu10 = pow(nu,10.0)
            nu12 = pow(nu,12.0)
            nu14 = pow(nu,14.0)
            nu16 = pow(nu,16.0)
            nu18 = pow(nu,18.0)
            nu20 = pow(nu,20.0)
            il = incLongitude
            il2 = pow(il,2.0)
            il3 = pow(il,3.0)
            il4 = pow(il,4.0)
            il5 = pow(il,5.0)
            il6 = pow(il,6.0)
            il7 = pow(il,7.0)
            il8 = pow(il,8.0)
            il9 = pow(il,9.0)
            il10 = pow(il,10.0)
            il11 = pow(il,11.0)
            il12 = pow(il,12.0)
            x10 = n*c
            x30 = n*c3/6.0*(1.0+nu2-t2)
            x50 = n*c5/120.0*(5.0-18.0*t2+t4+2.0*nu2*(7.0-29.0*t2)\
                    +nu4*(13.0-64.0*t2)+4.0*nu6*(1.0-6.0*t2))
            x70 = n*c7/5040.0*(61.0-479.0*t2+179.0*t4-t6+nu2\
                    *(331.0-3298.0*t2+1771.0*t4)+5.0*nu4*(143.0-1731.0*t2+1216.0*t4)\
                    +nu6*(769.0-10964.0*t2+9480.0*t4)+4.0*nu8*(103.0-1690.0\
                    *t2+1728.0*t4)+8.0*nu10*(11.0-204.0*t2+240.0*t4))
            x90 = n*c9/362880.0*(1385.0-19028.0*t2+18270.0*t4-1636.0*t6\
                    +t8+4*nu2*(3071.0-53535.0*t2+72717.0*t4-11797.0*t6)\
                    +42.0*nu4*(1079.0-22654.0*t2+39355.0*t4-9152.0*t6)\
                    +84.0*nu6*(1081.0-26437.0*t2+55510.0*t4-16596.0*t6)\
                    +3.0*nu8*(35747.0-994992.0*t2+2436448.0*t4-881664.0*t6)\
                    +24.0*nu10*(3121.0-97202.0*t2+270864.0*t4-114240.0*t6)\
                    +16.0*nu12*(1795.0-61744.0*t2+192348.0*t4-92160.0*t6)\
                    +64.0*nu14*(73.0-2745.0*t2+9432.0*t4-5040.0*t6))
            x110 = n*c11/39916800.0*(50521.0-1073517.0*t2+1949762.0\
                    *t4-540242.0*t6+14757.0*t8-t10+nu2*(663061.0-17594876.0*t2\
                    +43255806.0*t4-18928316.0*t6+1205941.0*t8)+10.0*nu4\
                    *(365573.0-11538395.0*t2+35378667.0*t4-20914069.0*t6+2111296.0\
                    *t8)+2.0*nu6*(5646709.0-205537746.0*t2+749466741.0\
                    *t4-552425084.0*t6+75476280.0*t8)+3.0*nu8\
                    *(7251983.0-297992239.0*t2+1252929256.0*t4\
                    -1098016304.0*t6+187181568.0*t8)+3.0*nu10\
                    *(9093467.0-415270424.0*t2+1970402816.0*t4-1990049088.0\
                    *t6+403226880.0*t8)+8.0*nu12*(2795947.0-140210892.0*t2\
                    +738954680.0*t4-841506840.0*t6+196300800.0*t8)+64.0*nu14\
                    *(181280.0-9888775.0*t2+57188844.0*t4-72256680.0*t6\
                    +18975600.0*t8)+64.0*nu16*(54112.0-3186343.0*t2+20027304.0\
                    *t4-27729936.0*t6+8064000.0*t8)+256.0*nu18*(1774.0-112047.0\
                    *t2+759474.0*t4-1141200.0*t6+362880.0*t8))
            easting = scaleFactor*(x10*il+x30*il3+x50*il5+x70*il7+x90*il9+x110*il11)
            geoCalError,longMerLat = self.longitude_meridian(latitude,a,inv_f)
            if geoCalError!= 0:
                return geoCalError,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
            if originLatitude == 0.0:
                longMerOriLat = 0
            else:
                geoCalError,longMerOriLat = self.longitude_meridian(originLatitude,a,inv_f)
                if(geoCalError!=0):
                    return geoCalError,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE

            y00 = longMerLat-longMerOriLat
            y20 = n*c2*t/2.0
            y40 = n*c4*t/24.0*(5.0-t2+9.0*nu2+4.0*nu4)
            y60 = n*c6*t/720.0*(61.0-58.0*t2+t4+5.0*nu4*(89.0-136.0*t2)\
                    +30.0*nu2*(9.0-11.0*t2)+12.0*nu6*(27.0-50.0*t2)+8.0*nu8*(11.0-24.0*t2))
            y80 = n*c8*t/40320.0*(1385.0-3111.0*t2+543.0*t4-t6+21.0*nu2\
                    *(519.0-1562.0*t2+439.0*t4)+21.0*nu4*(1639.0-6147.0*t2\
                    +2364.0*t4)+21.0*nu6*(2685.0-12004.0*t2+5800.0*t4)+24.0\
                    *nu8*(2119.0-10962.0*t2+6328.0*t4)+48.0*nu10*(501.0-2936.0\
                    *t2+1960.0*t4)+64.0*nu12*(73.0-477.0*t2+360.0*t4))
            y100 = n*c10*t/3628800.0*(50521.0-206276.0*t2+101166.0*t4-4916.0\
                    *t6+t8+180.0*nu2*(3403.0-18211.0*t2+13345.0*t4-1329.0*t6)\
                    +10.0*nu4*(304319.0-1995438.0*t2+1921083.0*t4-287944.0*t6)\
                    +1764.0*nu6*(4677.0-36081.0*t2+42622.0*t4-8420.0*t6)+3.0\
                    *nu8*(4501907.0-39770624.0*t2+55294736.0*t4-13415808.0*t6)\
                    +360.0*nu10*(38263.0-379690.0*t2+604288.0*t4-172480.0*t6)\
                    +64.0*nu12*(134264.0-1475140.0*t2+2634795.0*t4-859680.0*t6)\
                    +576.0*nu14*(5224.0-62841.0*t2+124120.0*t4-45360.0*t6)+256.0\
                    *nu16*(1774.0-23157.0*t2+50004.0*t4-20160.0*t6))
            y120 = n*c12*t/479001600.0*(2702765.0-17460701.0*t2+16889786.0*t4\
                    -2819266.0*t6+44281.0*t8-t10+33.0*nu2*(1407933.0-11604668.0\
                    *t2+15691278.0*t4-4376508.0*t6+183613.0*t8)+22.0*nu4\
                    *(14943197.0-148368637.0*t2+254823357.0*t4-98835787.0*t6\
                    +6937022.0*t8)+66.0*nu6*(19637685.0-226691218.0*t2+468302229.0\
                    *t4-2303348508.0*t6+22503800.0*t8)+11.0*nu8*(291287467.0\
                    -3816686007.0*t2+9160219344.0*t4-5415555968.0*t6+671328384.0\
                    *t8)+99.0*nu10*(52970419.0-774283096.0*t2+2108068176.0\
                    *t4-1446975744.0*t6+215568640.0*t8)+4.0*nu12*(1448764771.0\
                    -23317854076.0*t2+70778414608.0*t4-55066922064.0*t6+9518065920.0\
                    *t8)+48.0*nu14*(89401503.0-1568269028.0*t2+5237711952.0*t4\
                    -4538661600.0*t6+888148800.0*t8)+64.0*nu16*(31961980.0-606076217.0\
                    *t2+2204324568.0*t4-2099265696.0*t6+456825600.0*t8)+384.0*nu18\
                    *(1480293.0-30139018.0*t2+118386084.0*t4-122618880.0*t6+29272320.0\
                    *t8)+512.0*nu20*(136883.0-2975559.0*t2+12537288.0*t4-14004720.0*t6+3628800.0*t8))
            northing = scaleFactor*(y00+y20*il2+y40*il4+y60*il6+y80*il8+y100*il10+y120*il12)
        easting += falseEasting
        northing += falseNorthing
        return GEODETIC_CALCULATIONS_NO_ERROR,easting,northing

    def tmerc_inv(self,easting,northing,originLatitude,centralMeridian,scaleFactor,falseEasting,falseNorthing,a,inv_f):
        """
        brief Paso de la proyección Transversa de Mercator a coordenadas geodésicas
        param[in]: easting - Coordenada Este, en metros.
        param[in]: northing - Coordenada Norte, en metros.
        param[in]: originLatitude - Latitud geodésica origenen RAD., en el dominio [-pi/2,pi/2].
        param[in]: centralMeridian - Longitud geodésica del meridiano centralen RAD., en el dominio ]-pi,pi].
        param[in]: scaleFactor - Factor de escala adimensional.
        param[in]: falseEasting - Coordenada Este para el meridiano central, en metros.
        param[in]: falseNorthing - Coordenada norte para el paralelo geodésico origen, en metros.
        param[in]: a - Semieje mayor del elipsoide, en metros.
        param[in]: inv_f - Inverso del aplanamiento del elipsoide adimensional.
        return[0]: Entero con el estado de error.
        return[1]: latitude - latitud geodésica calculada, en RAD.
        return[2]. longitude - longitud geodésica calculada, en RAD.
        """
        
        # Control del dominio de la latitud geodésica
        if originLatitude < GEODETIC_CALCULATIONS_TMERC_MIN_ORIGIN_LATITUDE or originLatitude > GEODETIC_CALCULATIONS_TMERC_MAX_ORIGIN_LATITUDE:
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE        
        
        #Control del dominio de la longitud geodésica del meridiano central
        if centralMeridian < GEODETIC_CALCULATIONS_TMERC_MIN_CENTRAL_MERIDIAN or centralMeridian > GEODETIC_CALCULATIONS_TMERC_MAX_CENTRAL_MERIDIAN:
            return GEODETIC_CALCULATIONS_MAPPROJ_CENTRAL_MERIDIAN_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
        
        #Control del dominio del factor de escala
        if scaleFactor < GEODETIC_CALCULATIONS_TMERC_MIN_SCALE_FACTOR or scaleFactor > GEODETIC_CALCULATIONS_TMERC_MAX_SCALE_FACTOR:
            return GEODETIC_CALCULATIONS_MAPPROJ_SCALE_FACTOR_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
        
        #Control del dominio del semieje mayor del elipsoide
        if inv_f!=0.0 and (a < GEODETIC_CALCULATIONS_CONST_MIN_SEMI_MAYOR_AXIS or a > GEODETIC_CALCULATIONS_CONST_MAX_SEMI_MAYOR_AXIS):
            return GEODETIC_CALCULATIONS_A_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE    
           
        #Control del dominio del inverso del aplanamiento del elipsoide
        if inv_f!=0.0 and (inv_f < GEODETIC_CALCULATIONS_CONST_MIN_INVERSE_FLATTENING or inv_f > GEODETIC_CALCULATIONS_CONST_MAX_INVERSE_FLATTENING):
            return GEODETIC_CALCULATIONS_INV_F_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
    
        maxLongitude = centralMeridian + GEODETIC_CALCULATIONS_TMERC_MAX_INC_LONGITUDE
        
        if maxLongitude > GEODETIC_CALCULATIONS_CONST_PI:
            maxLongitude-=(2.0*GEODETIC_CALCULATIONS_CONST_PI)
            
        maxLatitude = GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE
        
        _checkIncrementLongitudeInTm = True  #Método establecer si se debe hacer control del incremento de longitud geodésica respecto al meridiano central del huso. Por defecto se pone a TRUE en el constructor.
        
        if (_checkIncrementLongitudeInTm):
            geoCalError,maxEasting,aux = self.tmerc_fwd(0.0,maxLongitude,originLatitude,centralMeridian,scaleFactor,falseEasting,falseNorthing,a,inv_f)
            if(geoCalError!=0):
                return geoCalError,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
                   
        geoCalError,aux,maxNorthing = self.tmerc_fwd(maxLatitude,maxLongitude,originLatitude,centralMeridian,scaleFactor,falseEasting,falseNorthing,a,inv_f)
        if geoCalError!= 0:
            return geoCalError,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
        
        if (_checkIncrementLongitudeInTm):
            #Control del dominio de la coordenada este
            if (fabs(easting) > maxEasting):
                return GEODETIC_CALCULATIONS_MAPPROJ_EASTING_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
           
        #Control del dominio de la coordenada norte
        if (fabs(northing) > maxNorthing):
            return GEODETIC_CALCULATIONS_MAPPROJ_NORTHING_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
    
        easting = (easting-falseEasting)/scaleFactor
        northing = (northing-falseNorthing)/scaleFactor
        if (inv_f==0.0):
            D=northing/a+originLatitude
            latitude=asin(sin(D)/cosh(easting/a))
            incLongitude=atan2(sinh(easting/a),cos(D))
        else:
            e2=2.0/inv_f-pow(1.0/inv_f,2.0)
            ee2=e2/(1.0-e2)
            if (originLatitude==0.0):
                longMerOriLat=0
            else:
                geoCalError,longMerOriLat = self.longitude_meridian(originLatitude,a,inv_f)
                if(geoCalError!= 0):
                    return geoCalError,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
                
            longMerLat = longMerOriLat+northing
            geoCalError,lat0 = self.longitude_meridian_2_gd_lat(longMerLat,a,inv_f)
            if(geoCalError!= 0):
                return geoCalError,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE
            
            t = tan(lat0)
            c = cos(lat0)
            nu = sqrt(ee2)*c
            v = sqrt(1.0+pow(nu,2.0))
            geoCalError,n = self.radius_first_vertical(lat0,a,inv_f)
            if(geoCalError!=0):
                return geoCalError,GEODETIC_CALCULATIONS_NULL_VALUE,GEODETIC_CALCULATIONS_NULL_VALUE

            v2 = pow(v,2.0)
            n2 = pow(n,2.0)
            n3 = pow(n,3.0)
            n4 = pow(n,4.0)
            n5 = pow(n,5.0)
            n6 =pow(n,6.0)
            n7 = pow(n,7.0)
            n8 = pow(n,8.0)
            n9 = pow(n,9.0)
            n10 = pow(n,10.0)
            n11 = pow(n,11.0)
            n12 = pow(n,12.0)
            t2 = pow(t,2.0)
            t4 = pow(t,4.0)
            t6 = pow(t,6.0)
            t8 = pow(t,8.0)
            t10 = pow(t,10.0)
            t12 = pow(t,12.0)
            nu2 = pow(nu,2.0)
            nu4 = pow(nu,4.0)
            nu6 = pow(nu,6.0)
            nu8 = pow(nu,8.0)
            nu10 = pow(nu,10.0)
            nu12 = pow(nu,12.0)
            nu14 = pow(nu,14.0)
            nu16 = pow(nu,16.0)
            nu18 =pow(nu,18.0)
            nu20 = pow(nu,20.0)
            l10 = 1.0/(n*c)
            l30 = -(1.0+(2.0*t2)+nu2)/(6.0*n3*c)
            l50 = 1.0/(120.0*n5*c)*(5.0+28.0*t2+24.0*t4+2.0*nu2*(3.0+4.0*t2)\
                -nu4*(3.0-4.0*t2)-4.0*nu6*(1.0-6.0*t2))
            l70 = -1.0/(5040.0*n7*c)*(61.0+662.0*t2+1320.0*t4+720.0*t6\
                +nu2*(107.0+440.0*t2+336.0*t4)+nu4*(43.0-234.0*t2-192.0*t4)\
                +nu6*(97.0-772.0*t2+408.0*t4)+4.0*nu8*(47.0-598.0*t2+384.0*t4)\
                +8.0*nu10*(11.0-204.0*t2+240.0*t4))
            l90 = 1.0/(362880.0*n9*c)*(1385.0+24568.0*t2+83664.0*t4+100800.0\
                *t6+40320.0*t8+4.0*nu2*(779.0+6684.0*t2+11952.0*t4+6048.0*t6)\
                +6.0*nu4*(193.0-824.0*t2-3456.0*t4-2304.0*t6)+4.0*nu6\
                *(-875.0+6776.0*t2+144.0*t4+2304.0*t6)-nu8*(11735.0-185496.0\
                *t2+195984.0*t4-9792.0*t6)-24.0*nu10*(845.0-19138.0*t2+34056.0\
                *t4-7440.0*t6)-16.0*nu12*(1009.0-30232.0*t2+77472.0*t4-27360.0\
                *t6)-64.0*nu14*(73.0-2745.0*t2+9432.0*t4-5040.0*t6))
            l110 = -1.0/(39916800.0*n11*c)*(50521.0+1326122.0*t2+6749040.0*t4\
                +13335840.0*t6+11491200.0*t8+3628800.0*t10+nu2*(138933.0\
                +2036560.0*t2+6269472.0*t4+7032960.0*t6+2661120.0*t8)\
                +2*nu4*(48681.0+5830.0*t2-837504.0*t4-1558656.0*t6-760320.0*t8)\
                +2*nu6*(28437.0-469300.0*t2+346512.0*t4+820224.0*t6+506880.0*t8)\
                +nu8*(604269.0-10449622.0*t2+13657104.0*t4-2708640.0*t6-737280.0\
                *t8)+nu10*(2216241.0-57880088.0*t2+128998080.0*t4-43649280.0\
                *t6+2102400.0*t8)+8.0*nu12*(511071.0-17943890.0*t2+59277264.0\
                *t4-35452800.0*t6+3116160.0*t8)+64.0*nu14*(64548.0-2856695.0\
                *t2+12610728.0*t4-11073888.0*t6+1733760.0*t8)+64.0*nu16\
                *(33696.0-1806745.0*t2+10070676.0*t4-11870928.0*t6+2741760.0\
                *t8)+256.0*nu18*(1774.0-112047.0*t2+759474.0*t4-1141200.0*t6+362880.0*t8))
            b20 = -(t*v2)/(2.0*n2)
            b40 = t*v2/(24.0*n4)*(5.0+3.0*t2+nu2*(1.0-9.0*t2)-4.0*nu4)
            b60 = -(t*v2)/(720.0*n6)*(61.0+90.0*t2+45.0*t4+2*nu2*(23.0-126.0\
                    *t2-45.0*t4)-3.0*nu4*(1.0+25.0*t2)*(1.0-3.0*t2)+4.0*nu6\
                    *(25.0+21.0*t2)+8.0*nu8*(11.0-24.0*t2))
            b80 = t*v2/(40320.0*n8)*(1385.0+3633.0*t2+4095.0*t4+1575.0*t6\
                    +3.0*nu2*(577.0-3127.0*t2-2457.0*t4-945.0*t6)+3.0*nu4\
                    *(-191.0-2815.0*t2+6775.0*t4+1575.0*t6)+nu6*(-2927.0+9609.0\
                    *t2+10551.0*t4-11025.0*t6)+24.0*nu8*(-367.0+808.0*t2-293.0\
                    *t4)+48.0*nu10*(-239.0+935.0*t2-184.0*t4)+64.0*nu12\
                    *(-73.0+477.0*t2-360.0*t4))
            b100 = t*v2/(3628800.0*n10)*(-50521.0-204180.0*t2-383670.0*t4\
                    -321300.0*t6-99225.0*t8+4.0*nu2*(-22103.0+117216.0*t2\
                    +148770.0*t4+128520.0*t6+42525.0*t8)+2.0*nu4*(-4475.0-398088.0\
                    *t2-884502.0*t4-434160.0*t6-127575.0*t8)+4.0*nu6*(-11981.0\
                    -58422.0*t2-431676.0*t4+557190.0*t6+99225.0*t8)+5.0*nu8\
                    *(-111269.0+329652.0*t2+348714.0*t4+213156.0*t6-178605.0*t8)\
                    +8.0*nu10*(-207487.0+1114515.0*t2-413325.0*t4-155295.0*t6)\
                    +256.0*nu12*(-9487.0+70869.0*t2-64260.0*t4+6795.0*t6)\
                    +64.0*nu14*(-26600.0+268119.0*t2-394101.0*t4+82440.0*t6)\
                    +256.0*nu16*(-1774.0+23157.0*t2-50004.0*t4+20160.0*t6))
            b120 = t*v2/(479001600.0*n12)*(2702765.0+15487263.0*t2+42660090.0\
                    *t4+57900150.0*t6+38201625.0*t8+9823275.0*t10+nu2\
                    *(6081221.0-30400713.0*t2-53715222.0*t4-78601050.0*t6\
                    -57848175.0*t8-16372125.0*t10)+6.0*nu4*(356193.0-14000767.0\
                    *t2+29923818.0*t4+21839202.0*t6+14150565.0*t8+3898125.0*t10)\
                    +6.0*nu6*(-583553.0+1354237.0*t2+54038142.0*t4-66690654.0\
                    *t6-21868605.0*t8-5457375.0*t10)+3.0*nu8*(-9305437.0+43020697.0\
                    *t2-51419658.0*t4-173555382.0*t6+122444775.0*t8+16372125.0*t10)\
                    +3.0*nu10*(-55827477.0+341692937.0*t2-194663802.0*t4+12943530.0\
                    *t6+87942735.0*t8-36018675.0*t10)+12.0*nu12*(-41013457.0+369373336.0\
                    *t2-413242506.0*t4+16888800.0*t6+898515.0*t8)+48.0*nu14*\
                    (-16591909.0+197580371.0*t2-362243859.0*t4+114551949.0*t6+531000.0*t8)\
                    +192.0*nu16*(-3793824.0+56786251.0*t2-145872564.0*t4+82552293.0*t6-7894440.0*t8)\
                    +128.0*nu18*(-2753297.0+50256327.0*t2-168878178.0*t4+139318848.0*t6-23224320.0*t8)\
                    +512.0*nu20*(-136883.0+2975559.0*t2-12537288.0*t4+14004720.0*t6-3628800.0*t8))
            x = easting
            x2 = pow(easting,2.0)
            x3 = pow(easting,3.0)
            x4 = pow(easting,4.0)
            x5 = pow(easting,5.0)
            x6 = pow(easting,6.0)
            x7 = pow(easting,7.0)
            x8 = pow(easting,8.0)
            x9 = pow(easting,9.0)
            x10 = pow(easting,10.0)
            x11 = pow(easting,11.0)
            x12 = pow(easting,12.0)
            latitude = lat0+b20*x2+b40*x4+b60*x6+b80*x8+b100*x10+b120*x12
            incLongitude = l10*x+l30*x3+l50*x5+l70*x7+l90*x9+l110*x11
        
        longitude = centralMeridian+incLongitude
        if (longitude<=-GEODETIC_CALCULATIONS_CONST_PI):
            longitude+=(2*GEODETIC_CALCULATIONS_CONST_PI)
        if(longitude>GEODETIC_CALCULATIONS_CONST_PI):
            longitude-=(2*GEODETIC_CALCULATIONS_CONST_PI)
        return GEODETIC_CALCULATIONS_NO_ERROR,latitude,longitude
        
    def utm_central_meridian(self,zone):
        """
        brief Determinación del huso de la proyección UTM y de la longitud geodésica del meridiano central.
        param[in]: zone - Número de huso en el dominio de 1 a 60.        
        return[0]: Entero con el estado de error.
        return[1]: centralMeridian - longitud geodésica del meridiano central del huso calculada, en RAD.
        """
       
        zoneWidth = GEODETIC_CALCULATIONS_UTM_ZONE_WIDTH*180.0/GEODETIC_CALCULATIONS_CONST_PI
    
        # Control del dominio del huso
        if zone < GEODETIC_CALCULATIONS_UTM_MIN_ZONE or zone > GEODETIC_CALCULATIONS_UTM_MAX_ZONE:
            return GEODETIC_CALCULATIONS_UTM_ZONE_ERROR,GEODETIC_CALCULATIONS_NULL_VALUE
    
        aux = -177.0
    
        #aux=round(aux+(zone-1.0)*zoneWidth)
        aux = aux+(zone-1.0)*zoneWidth
        auxAbs = fabs(aux)
        auxFloor = floor(auxAbs)
        auxCeil = ceil(auxAbs)
        auxRound = auxFloor
        if((auxCeil-auxAbs) < (auxAbs-auxFloor)):
            auxRound=auxCeil
        if(aux<0):
            auxRound=-auxRound
        aux = auxRound
    
        aux*=GEODETIC_CALCULATIONS_CONST_PI/180.0
        centralMeridian = aux
    
        #if(zone>=31) *centralMeridian=(zoneWidth*zone-183.0)*pi/180.0
        #else *centralMeridian=(zoneWidth*zone+177.0)*pi/180.0
        
        if(centralMeridian > GEODETIC_CALCULATIONS_CONST_PI):
            centralMeridian -= (2.0*GEODETIC_CALCULATIONS_CONST_PI)
        
        return GEODETIC_CALCULATIONS_NO_ERROR, centralMeridian
                    
    def utm_convergence_angle(self,
                              latitude,
                              longitude,
                              zone,
                              a,
                              inv_f):
        """
        brief Cálculo de la convergencia de meridianos en la proyección utm en un huso especificado.
        param[in]: latitude - Latitud geodésica, en radianes.
        param[in]: longitude - Longitud geodésica, en radianes.
        param[in]: zone - Huso en el que se quiere calcular.
        param[in]: a - Semieje mayor del elipsoide, en metros.
        param[in]: inv_f - Inverso del aplanamiento del elipsoide adimensional.
        return[0]: Entero con el estado de error.
        return[1]: convergenceAngle - convergencia de meridianos calculada, en RAD.
        """
        angTolerance = GEODETIC_CALCULATIONS_CONST_ANGULAR_TOLERANCE
    
        # Control del dominio de la latitud geodésica
        if latitude < GEODETIC_CALCULATIONS_CONST_MIN_LATITUDE or latitude > GEODETIC_CALCULATIONS_CONST_MAX_LATITUDE:
            return GEODETIC_CALCULATIONS_LATITUDE_ERROR,\
                   GEODETIC_CALCULATIONS_NULL_VALUE
    
        #Control del dominio de la longitud geodésica
        if longitude < GEODETIC_CALCULATIONS_CONST_MIN_LONGITUDE or longitude > GEODETIC_CALCULATIONS_CONST_MAX_LONGITUDE:
            return GEODETIC_CALCULATIONS_LONGITUDE_ERROR,\
                   GEODETIC_CALCULATIONS_NULL_VALUE
    
        #Control del dominio del huso
        if zone < GEODETIC_CALCULATIONS_UTM_MIN_ZONE or zone > GEODETIC_CALCULATIONS_UTM_MAX_ZONE:
            return GEODETIC_CALCULATIONS_UTM_ZONE_ERROR,\
                   GEODETIC_CALCULATIONS_NULL_VALUE

        #Control del dominio del semieje mayor del elipsoide
        if inv_f != 0.0 and (a < GEODETIC_CALCULATIONS_CONST_MIN_SEMI_MAYOR_AXIS or a > GEODETIC_CALCULATIONS_CONST_MAX_SEMI_MAYOR_AXIS):
            return GEODETIC_CALCULATIONS_A_ERROR,\
                   GEODETIC_CALCULATIONS_NULL_VALUE
    
        #Control del dominio del inverso del aplanamiento del elipsoide
        if inv_f != 0.0 and (inv_f < GEODETIC_CALCULATIONS_CONST_MIN_INVERSE_FLATTENING or inv_f > GEODETIC_CALCULATIONS_CONST_MAX_INVERSE_FLATTENING):
            return GEODETIC_CALCULATIONS_INV_F_ERROR,\
                   GEODETIC_CALCULATIONS_NULL_VALUE
    
        mapProjError,centralMeridian = self.utm_central_meridian(zone)
        if(mapProjError!= 0):
            return mapProjError,GEODETIC_CALCULATIONS_NULL_VALUE
        
        if(longitude < 0.0):
            longitude += (2.0*GEODETIC_CALCULATIONS_CONST_PI)
            
        if(centralMeridian < 0.0):
            centralMeridian += (2.0*GEODETIC_CALCULATIONS_CONST_PI)
        incLongitude = longitude-centralMeridian
        if(incLongitude > GEODETIC_CALCULATIONS_CONST_PI):
            incLongitude -= (2.0*GEODETIC_CALCULATIONS_CONST_PI)
        if(incLongitude < -GEODETIC_CALCULATIONS_CONST_PI):
            incLongitude += (2.0*GEODETIC_CALCULATIONS_CONST_PI)
    
        s = sin(latitude)
        c = cos(latitude)
        t = s/c
        if (inv_f==0.0):
            e2=0.0
            ee2=0.0
            n=a*cos(latitude)
        else:
            e2 = 2.0/inv_f-pow(1.0/inv_f,2.0)
            ee2 = e2/(1.0-e2)
            nu = sqrt(ee2)*c
            geoCalError,n = self.radius_first_vertical(latitude,a,inv_f)
            if(geoCalError!=0):
                return geoCalError,GEODETIC_CALCULATIONS_NULL_VALUE
            
        c2 = pow(c,2.0)
        c3 = pow(c,3.0)
        c4 = pow(c,4.0)
        c5 = pow(c,5.0)
        c6 = pow(c,6.0)
        t2 = pow(t,2.0)
        t4 = pow(t,4.0)
        t6 = pow(t,6.0)
        nu2 = pow(nu,2.0)
        nu4 = pow(nu,4.0)
        nu6 = pow(nu,6.0)
        nu8 = pow(nu,8.0)
        nu10 = pow(nu,10.0)
        nu12 = pow(nu,12.0)
        il = incLongitude
        il2 = pow(il,2.0)
        il3 = pow(il,3.0)
        il4 = pow(il,4.0)
        il5 = pow(il,5.0)
        il6 = pow(il,6.0)
        il7 = pow(il,7.0)
    
        conv1 = il*s+il3/3.0*s*c2*(1.0+3.0*nu2+2.0*nu4)+il5/15.0*s*c4\
                *(2.0-t2+15.0*nu2-15.0*nu2*t2+35.0*nu4-50.0*nu4*t2+33.0\
                *nu6-60.0*nu6*t2+11.0*nu8-24.0*nu8*t2)
        conv21 = il7/5040.0*s*c6
        conv22 = (-148.0-3427.0*t2+18.0*t4-1387.0*t6+2023.0*nu2-46116.0*nu2*t2+5166.0*nu2\
                  *t4+18984.0*nu4-100212.0*nu4*t2+57624.0*nu4*t4)
        conv23 = (34783.0*nu6-219968.0*nu6*t2+144900.0*nu6*t4+36180.0\
                  *nu8-261508.0*nu8*t2+155904.0*nu8*t4+18472.0*nu10-114528.0\
                  *nu10*t2+94080.0*nu10*t4+4672.0*nu12-30528.0*nu12*t2+23040.0*nu12*t4)
        conv2 = conv21*(conv22+conv23)
        convergenceAngle = conv1 + conv2
    
        #Control del dominio de la latitud geodésica
        if convergenceAngle > GEODETIC_CALCULATIONS_UTM_MAX_CONVERGENCE_ANGLE or\
                        convergenceAngle < GEODETIC_CALCULATIONS_UTM_MIN_CONVERGENCE_ANGLE:
            return GEODETIC_CALCULATIONS_UTM_CONVERGENCE_ANGLE_ERROR,\
                   GEODETIC_CALCULATIONS_NULL_VALUE

        return GEODETIC_CALCULATIONS_NO_ERROR,\
               convergenceAngle
                    
    def utm_sc_zone(self,latitude,longitude):
        """
        brief Determinación del huso de la proyección UTM con la consideración de los casos especiales contemplados en GeoTrans.
        param[in]: latitude - Latitud geodésicaen RAD., en el dominio [-80.5,84.5].
        param[in]: longitude - Longitud geodésicaen RAD., en el dominio ]-pi,pi].
        return[0]: Entero con el estado de error.
        return[1]: zone - número de huso calculado, en el dominio de 1 a 60.
        """
    
        zoneWidth = GEODETIC_CALCULATIONS_UTM_ZONE_WIDTH
        incrLongitude = longitude + GEODETIC_CALCULATIONS_CONST_PI
        zones = incrLongitude/GEODETIC_CALCULATIONS_UTM_ZONE_WIDTH
        tempZone = int(ceil(zones))
        
        #tempZone = (int)ceil(zones)
        
        #if (zones-temp_zone+1.0)<ggloGlobalVar.precision.angular
        #      temp_zone = temp_zone-1 %estamos en el huso anterior
       
        #if(longitude<pi) zones=31.0+longitude*180.0/pi/zoneWidth
        #else zones=longitude*180.0/pi/zoneWidth-29.0
        #tempZone=(int)floor(zones)
        #if(tempZone>60) tempZone=1
    
        #UTM special cases
        latDegrees = latitude*180.0/GEODETIC_CALCULATIONS_CONST_PI
        longDegrees = longitude*180.0/GEODETIC_CALCULATIONS_CONST_PI

        if((latDegrees>55) and (latDegrees<64) and (longDegrees>-1) and (longDegrees<3)):
            tempZone = 31
        #El incremento de longitud se amplia a 4
    
        if((latDegrees>55) and (latDegrees<64) and (longDegrees>2) and (longDegrees<12)):
            tempZone= 32
        #El incremento de longitud se amplia a 7
    
        if((latDegrees>71) and (longDegrees>-1) and (longDegrees<9)):
            tempZone = 31
        #El incremento de longitud se amplia a 6
    
        if((latDegrees>71) and (longDegrees>8) and (longDegrees<21)):
            tempZone = 33
        #El incremento de longitud se amplia a 7
    
        if((latDegrees>71) and (longDegrees>20) and (longDegrees<33)):
            tempZone = 35
        #El incremento de longitud se amplia a 7
    
        if((latDegrees>71) and (longDegrees>32) and (longDegrees<42)):
            tempZone= 37
    
        zone = tempZone
        
        return GEODETIC_CALCULATIONS_NO_ERROR,\
               zone

    def utm_zone(self,
                 longitude):
        """
        Brief: determinación del huso de la proyección UTM
        :param longitude: Longitud geodésicaen RAD., en el dominio ]-pi,pi]
        :type longitude: float
        :return: Entero con el estado de error y zone entero para almacenar el número de huso, en el dominio de 1 a 60
        :rtype: int
        """
        zone_width = GEODETIC_CALCULATIONS_UTM_ZONE_WIDTH
        incr_longitude = longitude + GEODETIC_CALCULATIONS_CONST_PI
        zones = incr_longitude / zone_width
        temp_zone = int(ceil(zones))
               
        zone = temp_zone
        return GEODETIC_CALCULATIONS_NO_ERROR,\
               zone

    def utm_zone_from_epsg_code(self,
                                int_epsg_code):
        """
        Brief: determinación del huso de la proyección UTM a partir del código EPSG
        :param int_epsg_code: código EPSG
        :type int_epsg_code: int
        :return: Entero con el estado de error y zone entero para almacenar el número de huso, en el dominio de 1 a 60
        """
        #TODO: quedan pendientes excepciones EPSG 3857, 4082 y 4083

        #excepciones
        if int_epsg_code == 4082: # REGCAN95 / UTM zone 27N
            int_huso = 27
            return GEODETIC_CALCULATIONS_NO_ERROR,\
                   int_huso

        if int_epsg_code == 4083: # REGCAN95 / UTM zone 28N
            int_huso = 28
            return GEODETIC_CALCULATIONS_NO_ERROR,\
                   int_huso

        str_epsg_code = str(int_epsg_code)

        str_huso_decena = str_epsg_code[-2]
        str_huso_unidad = str_epsg_code[-1]

        if str_huso_decena == "0":
            str_huso = str_huso_unidad
        else:
            str_huso = str_huso_decena + str_huso_unidad

        int_huso = int(str_huso)

        #Control del dominio del huso
        if int_huso < GEODETIC_CALCULATIONS_UTM_MIN_ZONE or int_huso > GEODETIC_CALCULATIONS_UTM_MAX_ZONE:
            return GEODETIC_CALCULATIONS_UTM_ZONE_ERROR,\
                   GEODETIC_CALCULATIONS_NULL_VALUE

        return GEODETIC_CALCULATIONS_NO_ERROR,\
               int_huso