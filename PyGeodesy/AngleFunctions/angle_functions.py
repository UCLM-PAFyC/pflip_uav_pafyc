# -*- coding: utf-8 -*-

# Import the PyQt and QGIS libraries
from PyQt5.QtWidgets import (QMessageBox)

# Importa la funciones matemáticas de la librería estándar de Python. Este módulo siempre está disponible.
# Proporciona acceso a las funciones matemáticas definidas por la norma C. 
from math import *

#valores constantes
ANGLEFUNCTIONS_CONST_NULL_VALUE = -999999.999
CONST_PI = 4 * atan(1.0)
CONST_TWOPI = 2 * CONST_PI
CONST_PIOVERTWO = CONST_PI / 2.0
CONST_DEG2RAD = CONST_PI * 180.0
CONST_RAD2DEG = 180.0 / CONST_PI
CONST_RAD2GRA = 200.0 / CONST_PI
CONST_DEG2GRA = 180.0 / 200.0
CONST_DEGSECINRAD = CONST_PI / 648000.0
CONST_GRASECINRAD = CONST_PI / 2000000.0
#const double AngleFunctions::_epsilon = 10.0 * std::numeric_limits<double>::epsilon()
#int AngleFunctions::_numdec = 15

class AngleFunctions:
    """Clase de librería de conversión entre unidades angulares.
    Esta librería incorpora sencillas operaciones de conversión entre formatos 
    angulares. Incluye el formato seudo decimal sexagesimal. """
    
    def __init__(self):
        """inicialización del cuerpo de la clase"""
        
        #para mostrar mensanjes de depuración del código
        self.MsgBoxDebug = QMessageBox()
    
    def deg2gra(self, value):
        """
        brief: Paso de ángulo en DEG a GRAD.
        param[in]: value - Ángulo en DEG.
        return: Ángulo en GRAD.
        """
        return (value*200.0/180.0) 
    
    def deg2pseudo(self, value):
        """
        brief: Pasa un ángulo en DEG a formato pseudo decimal sexagesimal. 
        param[in]: Ángulo en DEG
        return: Ángulo en pseudosexa (positivo o negativo).
        """           
        #paso a radianes
        value_rad = self.deg2rad(value)
        return self.rad2pseudo(value_rad)       
    
    def deg2rad(self, value):
        """         
        brief: Paso de ángulo en RAD a DEG.
        param[in]: value - Ángulo en RAD.
        return: Ángulo en DEG.
        """
        return (value*CONST_PI/180.0)
    
    def gra2deg(self,value):
        """
        brief: Paso de ángulo en GRAD a DEG.
        param[in]: value - Ángulo en GRAD.
        return: Ángulo en DEG.        
        """
        return(value*180.0/200.0)
    
    def gra2pseudo(self, value):
        """
        brief: Pasa un ángulo en GRA a formato pseudo decimal sexagesimal. 
        param[in]: Ángulo en GRA
        return: Ángulo en pseudosexa (positivo o negativo).
        """           
        #paso a radianes
        value_rad = self.gra2rad(value)
        return self.rad2pseudo(value_rad) 

    def gra2rad(self,value):
        """
        brief: Paso de ángulo en GRAD a RAD.
        param[in]: value - Ángulo en GRAD.
        return: Ángulo en RAD.
        """
        return(value*CONST_PI/200.0)
        
    def parte_entera(self, value):
        """
        brief: Devuelve la parte entera de un numero.
                Si llega un numero tipo 36.99999999991 se supone que era 37        
        param[in]: Número a truncar
        return: Parte entera
        """
        x = abs(value)
        if(abs(x-round(x)))<0.0000000001:
            x = round(x)
        else: 
            x = floor(x)
        if value < 0:            
            x = -x
        return x
    
    def pseudo2deg(self,pseudosexa):
        """
        brief: Pasa un ángulo de formato pseudo decimal sexagesimal a DEG.                
        param[in]: Ángulo en pseudosexa (positivo o negativo). 
        return: Ángulo en DEG.
        """
        value_rad = self.pseudo2rad(pseudosexa)
        return(self.rad2deg(value_rad))
    
    def pseudo2gra(self,pseudosexa):
        """
        brief: Pasa un ángulo de formato pseudo decimal sexagesimal a GRA.                
        param[in]: Ángulo en pseudosexa (positivo o negativo). 
        return: Ángulo en GRA.
        """
        value_rad = self.pseudo2rad(pseudosexa)
        return(self.rad2gra(value_rad))
            
    def pseudo2rad(self,pseudosexa):
        """
        brief: Pasa un ángulo de formato pseudo decimal sexagesimal a radianes.                
        param[in]: Ángulo en pseudosexa (positivo o negativo).
        En el formato seudo decimal sexagesimal:
        - La parte entera son grados, de -180 a 180
        - Los dos primeros decimales son los minutos, de 00 a 59
        - Los decimales tercero y cuarto son los segundos, de 00 a 59
        - A partir del quinto decimal es la fracción de segundo
        return: Ángulo en radianes.
        """
        if pseudosexa >= 180 or pseudosexa <= -180:
            strMsgAviso = "La parte entera (grados) debe ser menor de 180 y mayor de -180"
            self.MsgBoxDebug.setWindowTitle("Error en angulo en formato seudo decimal sexagesimal")
            self.MsgBoxDebug.setText(strMsgAviso)
            self.MsgBoxDebug.exec_()
            return ANGLEFUNCTIONS_CONST_NULL_VALUE
                       
        if pseudosexa<0:
            sig=-1
            pseudosexa = abs(pseudosexa)
        else:
            sig = 1
        degrees = self.parte_entera(pseudosexa)

        self.print_cadenas("degrees", degrees)        
        pseudosexa = (pseudosexa - degrees) * 100
        minutes = self.parte_entera(pseudosexa)
        if minutes > 59:
            strMsgAviso = "Los minutos son mayores que 59"
            self.MsgBoxDebug.setWindowTitle("Error en angulo en formato seudo decimal sexagesimal")
            self.MsgBoxDebug.setText(strMsgAviso)
            self.MsgBoxDebug.exec_()
            return ANGLEFUNCTIONS_CONST_NULL_VALUE
        self.print_cadenas("minutes", minutes)
        seconds = (pseudosexa-minutes) * 100
        if seconds > 59:
            strMsgAviso = "Los segundos son mayores que 59"
            self.MsgBoxDebug.setWindowTitle("Error en angulo en formato seudo decimal sexagesimal")
            self.MsgBoxDebug.setText(strMsgAviso)
            #self.MsgBoxDebug.exec_()
            return ANGLEFUNCTIONS_CONST_NULL_VALUE
        self.print_cadenas("pseudo3", seconds)
        degsexa = degrees + minutes / 60.0 + seconds / 3600.0
        radianes = sig * (degsexa * CONST_PI / 180.0)
        return radianes        
            
    def rad2deg(self,value):
        """
        brief: Paso de ángulo en RAD a DEG.
        param[in]: value - Ángulo en RAD.
        return: Ángulo en DEG.     
        """
        return(value*180.0/CONST_PI)
    
    def rad2gra(self,value):
        """
        brief: Cambio de formato de angulos.
        param[in]: value - Ángulo en RAD.
        return: Ángulo en GRAD.        
        """
        return(value*200.0/CONST_PI)
    
    def rad2pseudo(self,radianes):
        """
        brief:  Paso de ángulo en RAD a GRAD.
                Pasa un ángulo de radianes a formato pseudo decimal sexagesimal.
                Ejemplo: 40.24305678 son 40 g. 24 m. 30.5678 seg. sexagesimales
        param[in]: Ángulo en radianes. 
        return: Ángulo en pseudosexa ( positivo o negativo ).
        """
        degsexa = abs(radianes *180.0/CONST_PI)
        degrees = self.parte_entera(degsexa)
        degsexa = (degsexa-degrees) * 100 * 0.6
        minutes = self.parte_entera(degsexa)
        degsexa = (degsexa-minutes) * 100 * 0.6
        seconds = degsexa
        if abs(seconds-60) < 0.000001:
            minutes = minutes + 1
            seconds = 0
        if abs(minutes-60) < (0.000001/60):
            degrees = degrees + 1
            minutes = 0
        pseudosexa = degrees + minutes / 100.0 + seconds / 10000.0
        if radianes<0:
            pseudosexa = -pseudosexa
        return pseudosexa
        
    def print_cadenas(self, cadena, number_real):
        strResultado = "%.10f" % number_real
        print(cadena + " = " + strResultado)
        
#instance = AngleFunctions()
#valuePrueba = 179.5999
#resultado = instance.rad2pseudo(valuePrueba)
#resultado = instance.pseudo2rad(valuePrueba)
#instance.print_cadenas("Resultado",resultado)

#help(instance)