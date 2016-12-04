import sys
import os
from datetime import datetime
from PyQt5 import QtGui, QtWidgets, QtCore
from xml.etree import ElementTree
from xml.dom import minidom
import cv2
from gui import main_window
import forms
import error
import imageprocess as ip

assert(cv2.__version__ == '2.4.11')


class MainForm(QtWidgets.QMainWindow, main_window.Ui_MainWindow):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)
        self.actionOpen.triggered.connect(self.open)
        self.actionSave.triggered.connect(self.save)
        self.actionSave_As.triggered.connect(self.save_as)
        self.actionClose.triggered.connect(QtWidgets.qApp.quit)
        self.actionCanny.triggered.connect(self.add_canny)
        self.actionCvtColor.triggered.connect(self.add_cvt_color)
        self.actionThreshold.triggered.connect(self.add_threshold)
        self.actionFindContours.triggered.connect(self.add_find_contours)
        self.actionDrawContours.triggered.connect(self.add_draw_contours)
        self.actionKNNnumber.triggered.connect(self.add_knn_number)

        self.toolButtonToggle.setCheckable(True)
        self.toolButtonToggle.toggled.connect(self.toggle_video)
        self.toolButtonCapture.clicked.connect(self.update_image)
        self.toolButtonRefresh.clicked.connect(self.refresh_image)
        self.pushButtonDelete.clicked.connect(lambda: self.del_items())
        self.show()

        self.capture = cv2.VideoCapture(0)
        self.scene = QtWidgets.QGraphicsScene()
        self.pixitem = QtWidgets.QGraphicsPixmapItem()
        self.scene.addItem(self.pixitem)
        self.graphicsView.setScene(self.scene)

        self.filename = '/home/yasunori/workspace/myapp/opencv-gui/test.xml'
        self.dirname = '/home/yasunori/workspace/myapp/opencv-gui'
        # self.filename = None
        # self.dirname = '/home'
        self.form_list = []
        self.module_list = []
        self.image_list = []
        self.toolBox.removeItem(0)
        self.add_input()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_image)
        self.timer.start(100)

    def open(self):
        filename_list = QtWidgets.QFileDialog. \
            getOpenFileName(self, 'Open File', self.dirname)
        self.filename = filename_list[0]
        self.dirname = os.path.dirname(self.filename)
        root_top = ElementTree.parse(self.filename)
        print ElementTree.tostring(root_top)

    def save(self):
        if self.filename is None:
            self.save_as()
            return
        root_top = ElementTree.Element('top')
        for (index, form) in enumerate(self.form_list):
            root_form = form.get_xml_element()
            assert(root_form is not None)
            root_top.append(root_form)
        root_top = minidom.parseString(ElementTree.tostring(root_top, 'utf-8'))
        with open(self.filename, "w") as file:
            file.write(root_top.toprettyxml(indent="  "))

    def save_as(self):
        filename_list = QtWidgets.QFileDialog. \
            getSaveFileName(self, 'Save file', self.dirname)
        self.filename = filename_list[0]
        self.dirname = os.path.dirname(self.filename)
        self.save()

    def toggle_video(self, checked):
        if checked:
            self.toolButtonCapture.setEnabled(True)
            self.toolButtonRefresh.setEnabled(True)
            self.timer.stop()
        else:
            self.toolButtonCapture.setEnabled(False)
            self.toolButtonRefresh.setEnabled(False)
            self.timer.start()

    def add_input(self):
        self.insert_items(forms.inputForm(),
                          None,
                          'input')

    def add_canny(self):
        self.insert_items(forms.CannyForm(),
                          None,
                          ip.Canny.name)

    def add_cvt_color(self):
        self.insert_items(forms.cvtColorForm(),
                          None,
                          ip.CvtColor.name)

    def add_threshold(self):
        self.insert_items(forms.thresholdForm(),
                          ip.Thresh(),
                          ip.Thresh.name)

    def add_find_contours(self):
        self.insert_items(forms.findContoursForm(),
                          None,
                          ip.FindCnt.name)

    def add_draw_contours(self):
        self.insert_items(forms.drawContoursForm(),
                          None,
                          ip.DrawCnt.name)

    def add_knn_number(self):
        self.insert_items(forms.kNNnumberForm(),
                          ip.kNNnumber(),
                          ip.kNNnumber.name)

    def insert_items(self, form, module, string):
        index = self.toolBox.currentIndex()+1
        self.image_list.insert(index, self.capture_image())
        self.module_list.insert(index, module)
        self.form_list.insert(index, form)
        self.toolBox.insertItem(index, form, string)
        self.toolBox.setCurrentIndex(index)
        self.update_form()

    def del_items(self):
        index = self.toolBox.currentIndex()
        if index == -1 or index == 0:
            pass
        else:
            self.toolBox.removeItem(index)
            del self.image_list[index]
            del self.module_list[index]
            del self.form_list[index]
            self.update_form()

    def update_form(self):
        image_label_list = []
        for form in self.form_list:
            image_label_list.append(form.get_name())
            form.set_image_label_list(image_label_list)
        self.comboBoxSelectImages.clear()
        self.comboBoxSelectImages.addItems(image_label_list)
        self.comboBoxSelectImages.setCurrentIndex(len(image_label_list)-1)

    def capture_image(self):
        success, self.raw_image = self.capture.read()
        assert(success)
        return ip.ImageObj(self.raw_image, ip.CvtColor.CvtCodes.BGR)

    def update_image(self):
        self.image_list[0] = ip.CvtColor.get_image(self.capture_image(),
                                                   ip.CvtColor.CvtCodes.RGB)
        self.refresh_image()

    def refresh_image(self):
        for (index, form) in enumerate(self.form_list):
            module = self.module_list[index]
            root = form.get_xml_element()
            assert(root is not None)
            try:
                self.image_list[index] = \
                    self.excute_image_processing(root, module)
            except error.ModuleError as e:
                print e, datetime.now()
                self.image_list[index] = None

        if self.image_list[-1] is None:
            image = self.raw_image
        else:
            index = self.comboBoxSelectImages.currentIndex()
            image = self.image_list[index].image

        assert(2 <= len(image.shape) or len(image.shape) <= 3)
        if len(image.shape) == 2:  # gray scale
            h, w = image.shape
            self.qimage = \
                QtGui.QImage(image.data, w, h, w, QtGui.QImage.Format_Indexed8)
        elif len(image.shape) == 3:  # others
            h, w, d = image.shape
            self.qimage = \
                QtGui.QImage(image.data, w, h, w*d, QtGui.QImage.Format_RGB888)

        self.pixmap = QtGui.QPixmap.fromImage(self.qimage)
        self.pixitem.setPixmap(self.pixmap)

    def excute_image_processing(self, root, module):
        module_str = root.get('name')
        img_index = int(root.find('common').find('picture_number').text)
        cnt_index = int(root.find('common').find('contour_number').text)
        obj_img = self.image_list[img_index]
        obj_cnt = self.image_list[cnt_index]

        if obj_img is None or obj_cnt is None:
            raise error.ModuleError('input image or contours is None!')

        if module_str == 'input':
            return self.image_list[0]

        elif module_str == ip.Canny.name:
            min_val = int(root.find('min').text)
            max_val = int(root.find('max').text)
            return ip.Canny.get_image(obj_img, min_val, max_val)

        elif module_str == ip.CvtColor.name:
            module = ip.CvtColor
            code = str(root.find('code').text)
            return module.get_image(obj_img, module.CvtCodes[code])

        elif module_str == ip.Thresh.name:
            module = ip.Thresh
            thresh = int(root.find('thresh').text)
            max_val = int(root.find('maxVal').text)
            thresh_type = str(root.find('thresholdType').text)
            return module.get_image(obj_img, thresh,
                                    max_val, module.ThreshTypes[thresh_type])

        elif module_str == ip.FindCnt.name:
            module = ip.FindCnt
            mode = str(root.find('mode').text)
            method = str(root.find('method').text)
            return module.get_image(obj_img,
                                    module.Modes[mode],
                                    module.Methods[method])

        elif module_str == ip.DrawCnt.name:
            module = ip.DrawCnt
            return module.get_image(obj_img, obj_cnt)

        elif module_str == ip.kNNnumber.name:
            k = int(root.find('K').text)
            return module.get_image(obj_img, k)

        else:
            assert(False)
            return None


def main():
    app = QtWidgets.QApplication(sys.argv)
    MainForm()
    app.exec_()

if __name__ == '__main__':
    main()
