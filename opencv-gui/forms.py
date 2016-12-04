from PyQt5 import QtWidgets
from xml.etree import ElementTree

import imageprocess as ip
from gui import common_ui
from gui import input_ui
from gui import canny_ui
from gui import cvt_color_ui
from gui import threshold_ui
from gui import find_contours_ui
from gui import draw_contours_ui
from gui import knn_number_ui


class commonForm(QtWidgets.QWidget, common_ui.Ui_Form):
    def __init__(self):
        super(commonForm, self).__init__()
        self.setupUi(self)

    def set_image_label_list(self, image_label_list):
        self.comboBox1.clear()
        self.comboBox1.addItems(image_label_list[:-1])
        self.comboBox1.setCurrentIndex(len(image_label_list[:-1])-1)
        self.comboBox2.clear()
        self.comboBox2.addItems(image_label_list[:-1])
        self.comboBox2.setCurrentIndex(len(image_label_list[:-1])-1)

    def get_xml_element(self):
        root = ElementTree.Element('common')
        elem1 = ElementTree.SubElement(root, 'picture_number')
        elem1.text = str(self.comboBox1.currentIndex())
        elem2 = ElementTree.SubElement(root, 'contour_number')
        elem2.text = str(self.comboBox2.currentIndex())
        return root


class AbstractForm(QtWidgets.QWidget):
    def __init__(self):
        super(AbstractForm, self).__init__()
        self.setupUi(self)

    def get_xml_element(self):
        return None


class inputForm(AbstractForm, input_ui.Ui_Form):
    def __init__(self):
        super(inputForm, self).__init__()

    def get_name(self):
        return 'input'

    def set_image_label_list(self, image_label_list):
        pass

    def get_xml_element(self):
        root = ElementTree.Element('module')
        root.set('name', 'input')
        root_cmn = ElementTree.SubElement(root, 'common')
        elem1 = ElementTree.SubElement(root_cmn, 'picture_number')
        elem1.text = str(0)
        elem2 = ElementTree.SubElement(root_cmn, 'contour_number')
        elem2.text = str(0)
        return root


class CannyForm(AbstractForm, canny_ui.Ui_Form):
    def __init__(self):
        super(CannyForm, self).__init__()
        self.commonForm = commonForm()
        self.widget_1.layout().addWidget(self.commonForm)

    def get_name(self):
        return ip.Canny.name

    def set_image_label_list(self, image_label_list):
        self.commonForm.set_image_label_list(image_label_list)

    def get_xml_element(self):
        root = ElementTree.Element('module')
        root.set('name', ip.Canny.name)
        root.append(self.commonForm.get_xml_element())
        elem1 = ElementTree.SubElement(root, 'min')
        elem1.text = str(self.spinBoxMin.value())
        elem2 = ElementTree.SubElement(root, 'max')
        elem2.text = str(self.spinBoxMax.value())
        return root


class cvtColorForm(AbstractForm, cvt_color_ui.Ui_Form):
    def __init__(self):
        super(cvtColorForm, self).__init__()
        self.commonForm = commonForm()
        self.widget_1.layout().addWidget(self.commonForm)
        for i in ip.CvtColor.CvtCodes:
            self.comboBox.addItem(i.name)

    def get_name(self):
        return ip.CvtColor.name

    def set_image_label_list(self, image_label_list):
        self.commonForm.set_image_label_list(image_label_list)

    def get_xml_element(self):
        root = ElementTree.Element('module')
        root.set('name', ip.CvtColor.name)
        root.append(self.commonForm.get_xml_element())
        elem1 = ElementTree.SubElement(root, 'code')
        elem1.text = str(self.comboBox.currentText())
        return root


class thresholdForm(AbstractForm, threshold_ui.Ui_Form):
    def __init__(self):
        super(thresholdForm, self).__init__()
        self.commonForm = commonForm()
        self.widget_1.layout().addWidget(self.commonForm)
        for i in ip.Thresh.ThreshTypes:
            self.comboBox.addItem(i.name)

    def get_name(self):
        return ip.Thresh.name

    def set_image_label_list(self, image_label_list):
        self.commonForm.set_image_label_list(image_label_list)

    def get_xml_element(self):
        root = ElementTree.Element('module')
        root.set('name', ip.Thresh.name)
        root.append(self.commonForm.get_xml_element())
        elem1 = ElementTree.SubElement(root, 'thresh')
        elem1.text = str(self.spinBoxThresh.value())
        elem2 = ElementTree.SubElement(root, 'maxVal')
        elem2.text = str(self.spinBoxMaxVal.value())
        elem3 = ElementTree.SubElement(root, 'thresholdType')
        elem3.text = str(self.comboBox.currentText())
        return root


class findContoursForm(AbstractForm, find_contours_ui.Ui_Form):
    def __init__(self):
        super(findContoursForm, self).__init__()
        self.commonForm = commonForm()
        self.widget_1.layout().addWidget(self.commonForm)
        for i in ip.FindCnt.Modes:
            self.comboBoxMode.addItem(i.name)
        for i in ip.FindCnt.Methods:
            self.comboBoxMethod.addItem(i.name)

    def get_name(self):
        return ip.FindCnt.name

    def set_image_label_list(self, image_label_list):
        self.commonForm.set_image_label_list(image_label_list)

    def get_xml_element(self):
        root = ElementTree.Element('module')
        root.set('name', ip.FindCnt.name)
        root.append(self.commonForm.get_xml_element())
        elem1 = ElementTree.SubElement(root, 'mode')
        elem1.text = str(self.comboBoxMode.currentText())
        elem2 = ElementTree.SubElement(root, 'method')
        elem2.text = str(self.comboBoxMethod.currentText())
        return root


class drawContoursForm(AbstractForm, draw_contours_ui.Ui_Form):
    def __init__(self):
        super(drawContoursForm, self).__init__()
        self.commonForm = commonForm()
        self.widget_1.layout().addWidget(self.commonForm)

    def get_name(self):
        return ip.DrawCnt.name

    def set_image_label_list(self, image_label_list):
        self.commonForm.set_image_label_list(image_label_list)

    def get_xml_element(self):
        root = ElementTree.Element('module')
        root.set('name', ip.DrawCnt.name)
        root.append(self.commonForm.get_xml_element())
        return root


class kNNnumberForm(AbstractForm, knn_number_ui.Ui_Form):
    def __init__(self):
        super(kNNnumberForm, self).__init__()
        self.commonForm = commonForm()
        self.widget_1.layout().addWidget(self.commonForm)

    def get_name(self):
        return ip.kNNnumber.name

    def set_image_label_list(self, image_label_list):
        self.commonForm.set_image_label_list(image_label_list)

    def get_xml_element(self):
        root = ElementTree.Element('module')
        root.set('name', ip.kNNnumber.name)
        root.append(self.commonForm.get_xml_element())
        elem1 = ElementTree.SubElement(root, 'K')
        elem1.text = str(self.spinBoxK.value())
        return root
