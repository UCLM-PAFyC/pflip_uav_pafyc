# -*- coding: utf-8 -*-

# Import PyQt5 classes
from PyQt5 import uic
from PyQt5 import QtWidgets

# import PyQGIS classes
from qgis.gui import QgsMessageBar
from qgis.core import Qgis

# Import Python classes
import os

from .. import config as c # valores constantes

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
import sys
sys.path.append(os.path.dirname(__file__))
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__),
                                            'progress_dialog_dlg.ui'),
                               resource_suffix='')

class progressDialogDlg(QtWidgets.QDialog,
                        FORM_CLASS):
    """
    Brief:
    """

    def __init__(self,
                 iface,
                 parent=None):
        """

        :param iface:
        :param parent:
        :return:
        """
        super(progressDialogDlg, self).__init__(parent)

        self.iface = iface # Save reference to the QGIS interface

        # Set up the user interface from Designer.
        self.setupUi(self)

    def clear_text(self,
                   int_pos):
        """

        :param int_pos:
        :return:
        """

        if int_pos < 0 or int_pos > 1:
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                "Invalid position in progress dialog",
                                                Qgis.CRITICAL,
                                                10)
            return

        if int_pos == 0:
            self.textEdit_first.clear()
        else:
            self.textEdit_second.clear()

    def enabled_suprocess(self,
                          is_enabled):
        """

        :param is_enabled:
        :return:
        """
        if is_enabled:
            self.groupBox_second.setVisible(True)
        else:
            self.groupBox_second.setVisible(False)

    def insert_text(self,
                    int_pos,
                    str_value):
        """

        :param int_pos:
        :param str_value:
        :return:
        """
        if int_pos < 0 or int_pos > 1:
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                "Invalid position in progress dialog",
                                                Qgis.Critical,
                                                10)
            return

        if int_pos == 0:
            self.textEdit_first.append(str_value)
        else:
            self.textEdit_second.append(str_value)

    def set_title_process(self,
                          int_pos,
                          str_value):
        """

        :param int_pos:
        :param str_value:
        :return:
        """

        if int_pos < 0 or int_pos > 1:
            self.iface.messageBar().pushMessage(c.CONST_PFLIPUAV_TITLE,
                                                "Invalid position in progress dialog",
                                                Qgis.Critical,
                                                10)
            return

        if int_pos == 0:
            str_title = "Main process: " + str_value
            self.groupBox_first.setTitle(str_title)
        else:
            str_title = "Secondary process: " + str_value
            self.groupBox_second.setTitle(str_title)