from PyQt5 import QtWidgets
from xml.etree import ElementTree
import distutils.util

import imageprocess as ip
from gui import common_ui
from gui import input_ui
from gui import canny_ui
from gui import cvt_color_ui
from gui import threshold_ui
from gui import adaptive_threshold_ui
from gui import find_contours_ui
from gui import draw_contours_ui
from gui import knn_number_ui
from gui import pyocr_ui


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

    def set_xml_element(self, root):
        box1_index = int(root.find('picture_number').text)
        box2_index = int(root.find('contour_number').text)
        self.comboBox1.setCurrentIndex(box1_index)
        self.comboBox2.setCurrentIndex(box2_index)


class AbstractForm(QtWidgets.QWidget):
    def __init__(self):
        super(AbstractForm, self).__init__()
        self.setupUi(self)

    def get_xml_element(self):
        return None


class inputForm(AbstractForm, input_ui.Ui_Form):
    def __init__(self):
        super(inputForm, self).__init__()
        for i in ip.CvtColor.Codes:
            self.comboBox.addItem(i.name)
        self.comboBox.setCurrentIndex(ip.CvtColor.Codes['RGB']-1)

    def get_name(self):
        return 'input'

    def set_image_label_list(self, image_label_list):
        pass

    def get_xml_element(self):
        root = ElementTree.Element('module')
        root.set('name', self.get_name())
        root_cmn = ElementTree.SubElement(root, 'common')
        elem1 = ElementTree.SubElement(root_cmn, 'picture_number')
        elem1.text = str(0)
        elem2 = ElementTree.SubElement(root_cmn, 'contour_number')
        elem2.text = str(0)
        elem3 = ElementTree.SubElement(root, 'code')
        elem3.text = str(self.comboBox.currentText())
        return root

    def set_xml_element(self, root):
        code = ip.CvtColor.Codes[str(root.find('code').text)]
        self.comboBox.setCurrentIndex(code-1)


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
        root.set('name', self.get_name())
        root.append(self.commonForm.get_xml_element())
        elem1 = ElementTree.SubElement(root, 'min')
        elem1.text = str(self.spinBoxMin.value())
        elem2 = ElementTree.SubElement(root, 'max')
        elem2.text = str(self.spinBoxMax.value())
        return root

    def set_xml_element(self, root):
        self.commonForm.set_xml_element(root.find('common'))
        min_val = int(root.find('min').text)
        max_val = int(root.find('max').text)
        self.spinBoxMin.setValue(min_val)
        self.spinBoxMax.setValue(max_val)


class cvtColorForm(AbstractForm, cvt_color_ui.Ui_Form):
    def __init__(self):
        super(cvtColorForm, self).__init__()
        self.commonForm = commonForm()
        self.widget_1.layout().addWidget(self.commonForm)
        for i in ip.CvtColor.Codes:
            self.comboBox.addItem(i.name)

    def get_name(self):
        return ip.CvtColor.name

    def set_image_label_list(self, image_label_list):
        self.commonForm.set_image_label_list(image_label_list)

    def get_xml_element(self):
        root = ElementTree.Element('module')
        root.set('name', self.get_name())
        root.append(self.commonForm.get_xml_element())
        elem1 = ElementTree.SubElement(root, 'code')
        elem1.text = str(self.comboBox.currentText())
        return root

    def set_xml_element(self, root):
        self.commonForm.set_xml_element(root.find('common'))
        code = ip.CvtColor.Codes[str(root.find('code').text)]
        self.comboBox.setCurrentIndex(code-1)


class thresholdForm(AbstractForm, threshold_ui.Ui_Form):
    def __init__(self):
        super(thresholdForm, self).__init__()
        self.commonForm = commonForm()
        self.widget_1.layout().addWidget(self.commonForm)
        for i in ip.Thresh.ThreshTypes:
            self.comboBoxThresholdType.addItem(i.name)

    def get_name(self):
        return ip.Thresh.name

    def set_image_label_list(self, image_label_list):
        self.commonForm.set_image_label_list(image_label_list)

    def get_xml_element(self):
        root = ElementTree.Element('module')
        root.set('name', self.get_name())
        root.append(self.commonForm.get_xml_element())
        elem = ElementTree.SubElement(root, 'thresh')
        elem.text = str(self.spinBoxThresh.value())
        elem = ElementTree.SubElement(root, 'maxVal')
        elem.text = str(self.spinBoxMaxVal.value())
        elem = ElementTree.SubElement(root, 'threshType')
        elem.text = str(self.comboBoxThresholdType.currentText())
        elem = ElementTree.SubElement(root, 'otsu')
        elem.text = str(self.checkBoxOtsu.isChecked())
        return root

    def set_xml_element(self, root):
        self.commonForm.set_xml_element(root.find('common'))
        th = int(root.find('thresh').text)
        mv = int(root.find('maxVal').text)
        tt = ip.AdaptThresh.ThreshTypes[str(root.find('threshType').text)]
        ot = distutils.util.strtobool(str(root.find('otsu').text))
        self.spinBoxThresh.setValue(th)
        self.spinBoxMaxValue.setValue(mv)
        self.comboBoxThresholdType.setCurrentIndex(tt-1)
        self.checkBoxOtsu.setChecked(ot)


class adaptiveThresholdForm(AbstractForm, adaptive_threshold_ui.Ui_Form):
    def __init__(self):
        super(adaptiveThresholdForm, self).__init__()
        self.commonForm = commonForm()
        self.widget_1.layout().addWidget(self.commonForm)
        for i in ip.AdaptThresh.ThreshTypes:
            self.comboBoxThresholdType.addItem(i.name)
        for i in ip.AdaptThresh.AdaptMethods:
            self.comboBoxAdaptiveMethod.addItem(i.name)

    def get_name(self):
        return ip.Thresh.name

    def set_image_label_list(self, image_label_list):
        self.commonForm.set_image_label_list(image_label_list)

    def get_xml_element(self):
        root = ElementTree.Element('module')
        root.set('name', self.get_name())
        root.append(self.commonForm.get_xml_element())
        elem1 = ElementTree.SubElement(root, 'maxValue')
        elem1.text = str(self.spinBoxMaxValue.value())
        elem2 = ElementTree.SubElement(root, 'adaptiveMethod')
        elem2.text = str(self.comboBoxAdaptiveMethod.currentText())
        elem3 = ElementTree.SubElement(root, 'thresholdType')
        elem3.text = str(self.comboBoxThresholdType.currentText())
        elem4 = ElementTree.SubElement(root, 'blockSize')
        elem4.text = str(self.spinBoxBlockSize.value())
        elem5 = ElementTree.SubElement(root, 'param1')
        elem5.text = str(self.spinBoxParam1.value())
        return root

    def set_xml_element(self, root):
        self.commonForm.set_xml_element(root.find('common'))
        mv = int(root.find('maxValue').text)
        bs = int(root.find('blockSize').text)
        p1 = int(root.find('param1').text)
        am = ip.AdaptThresh.AdaptMethods[str(root.find('adaptiveMethod').text)]
        tt = ip.AdaptThresh.ThreshTypes[str(root.find('thresholdType').text)]
        self.spinBoxMaxValue.setValue(mv)
        self.spinBoxBlockSize.setValue(bs)
        self.spinBoxParam1.setValue(p1)
        self.comboBoxAdaptiveMethod.setCurrentIndex(am-1)
        self.comboBoxThresholdType.setCurrentIndex(tt-1)


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
        root.set('name', self.get_name())
        root.append(self.commonForm.get_xml_element())
        elem1 = ElementTree.SubElement(root, 'mode')
        elem1.text = str(self.comboBoxMode.currentText())
        elem2 = ElementTree.SubElement(root, 'method')
        elem2.text = str(self.comboBoxMethod.currentText())
        return root

    def set_xml_element(self, root):
        self.commonForm.set_xml_element(root.find('common'))
        mode = ip.FindCnt.Modes[str(root.find('mode').text)]
        method = ip.FindCnt.Methods[str(root.find('method').text)]
        self.comboBoxMode.setCurrentIndex(mode-1)
        self.comboBoxMethod.setCurrentIndex(method-1)


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
        root.set('name', self.get_name())
        root.append(self.commonForm.get_xml_element())
        return root

    def set_xml_element(self, root):
        self.commonForm.set_xml_element(root.find('common'))


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
        root.set('name', self.get_name())
        root.append(self.commonForm.get_xml_element())
        elem1 = ElementTree.SubElement(root, 'K')
        elem1.text = str(self.spinBoxK.value())
        return root

    def set_xml_element(self, root):
        self.commonForm.set_xml_element(root.find('common'))
        k = int(root.find('K').text)
        self.spinBoxK.setValue(k)


class pyocrForm(AbstractForm, pyocr_ui.Ui_Form):
    def __init__(self):
        super(pyocrForm, self).__init__()
        self.commonForm = commonForm()
        self.widget_1.layout().addWidget(self.commonForm)
        self.comboBoxTool.currentIndexChanged.connect(self.set_tool)
        for i in ip.Pyocr.PSModes:
            self.comboBoxPSMode.addItem(i.name)
        self.comboBoxPSMode.setCurrentIndex(3)
        self.module = None

    def set_module(self, module):
        self.module = module
        for i in self.module.tool_names:
            self.comboBoxTool.addItem(i)
        return self.module

    def set_tool(self):
        self.module.setTool(self.comboBoxTool.currentText())
        for i in self.module.lang_names:
            self.comboBoxLang.addItem(i)

    def get_name(self):
        return ip.Pyocr.name

    def set_image_label_list(self, image_label_list):
        self.commonForm.set_image_label_list(image_label_list)

    def get_xml_element(self):
        root = ElementTree.Element('module')
        root.set('name', self.get_name())
        root.append(self.commonForm.get_xml_element())
        elem1 = ElementTree.SubElement(root, 'tool')
        elem1.text = str(self.comboBoxTool.currentText())
        elem2 = ElementTree.SubElement(root, 'lang')
        elem2.text = str(self.comboBoxLang.currentText())
        elem3 = ElementTree.SubElement(root, 'psmode')
        elem3.text = str(self.comboBoxPSMode.currentText())
        return root

    def set_xml_element(self, root):
        self.commonForm.set_xml_element(root.find('common'))
        self.comboBoxTool.setCurrentText(str(root.find('tool').text))
        self.comboBoxLang.setCurrentText(str(root.find('lang').text))
        psmode = ip.Pyocr.PSModes[str(root.find('psmode').text)]
        self.comboBoxPSMode.setCurrentIndex(psmode-1)
