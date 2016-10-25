import sys
from PyQt5 import QtGui, QtWidgets, QtCore
from xml.etree import ElementTree

import common_ui
import input_ui, Canny_ui, cvtColor_ui

class commonFoam(QtWidgets.QWidget, common_ui.Ui_Form):
    def __init__(self):
        super(commonFoam,self).__init__()
        self.setupUi(self)
    def set_picture_label_list(self,picture_label_list):
        self.comboBox.clear()
        self.comboBox.addItems(picture_label_list[:-1])
    def get_xml_element(self):
        root = ElementTree.Element('common')
        num_elem = ElementTree.SubElement(root,'picture_number')
        num_elem.text = str(self.comboBox.currentIndex())
        num_elem.set('type','int')
        return root

class AbstractForm(QtWidgets.QWidget):
    def __init__(self):
        super(AbstractForm,self).__init__()
        self.setupUi(self)

    def get_xml_element(self):
        return None

class inputForm(AbstractForm,input_ui.Ui_Form):
    def __init__(self):
        super(inputForm,self).__init__()
    def get_name(self):
        return "input"
    def set_picture_label_list(self,picture_label_list):
        pass
    def get_xml_element(self):
        root = ElementTree.Element('module')
        common = ElementTree.SubElement(root,'common')
        num_elem = ElementTree.SubElement(common,'picture_number')
        num_elem.text = str(0)
        num_elem.set('type','int')
        root.set('name','input')
        return root

class CannyForm(AbstractForm, Canny_ui.Ui_Form):
    def __init__(self):
        super(CannyForm,self).__init__()
        self.commonFoam = commonFoam()
        self.widget_1.layout().addWidget(self.commonFoam)
    def get_name(self):
        return "Canny"
    def set_picture_label_list(self,picture_label_list):
        self.commonFoam.set_picture_label_list(picture_label_list)
    def get_xml_element(self):
        root = ElementTree.Element('module')
        root.append(self.commonFoam.get_xml_element())
        root.set('name','Canny')
        min_elem = ElementTree.SubElement(root,'min')
        min_elem.text = str(self.spinBoxMin.value())
        min_elem.set('type','int')
        max_elem = ElementTree.SubElement(root,'max')
        max_elem.text = str(self.spinBoxMax.value())
        max_elem.set('type','int')
        return root

class cvtColorForm(AbstractForm, cvtColor_ui.Ui_Form):
    def __init__(self):
        super(cvtColorForm,self).__init__()
        self.commonFoam = commonFoam()
        self.widget_1.layout().addWidget(self.commonFoam)
    def get_name(self):
        return "cvtColor"
    def set_picture_label_list(self,picture_label_list):
        self.commonFoam.set_picture_label_list(picture_label_list)
    def get_xml_element(self):
        root = ElementTree.Element('module')
        root.append(self.commonFoam.get_xml_element())
        root.set('name','cvtColor')
        return root
