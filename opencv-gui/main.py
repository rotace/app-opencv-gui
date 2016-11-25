import sys
from PyQt5 import QtGui, QtWidgets, QtCore
import cv2
from gui import forms, main_window
import gui.names as nm
import imageprocess as ip


class MainForm(QtWidgets.QMainWindow, main_window.Ui_MainWindow):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)
        self.actionClose.triggered.connect(QtWidgets.qApp.quit)
        self.actionCanny.triggered.connect(self.add_form_canny)
        self.actionCvtColor.triggered.connect(self.add_form_cvt_color)
        self.actionThreshold.triggered.connect(self.add_form_threshold)
        self.actionFindContours.triggered.connect(self.add_form_find_contours)
        self.actionDrawContours.triggered.connect(self.add_form_draw_contours)
        self.pushButtonDelete.clicked.connect(lambda: self.del_form())
        self.show()

        self.capture = cv2.VideoCapture(0)
        self.scene = QtWidgets.QGraphicsScene()
        self.pixitem = QtWidgets.QGraphicsPixmapItem()
        self.scene.addItem(self.pixitem)
        self.graphicsView.setScene(self.scene)

        self.form_list = []
        self.image_list = []
        self.toolBox.removeItem(0)
        self.add_form_input()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_image)
        self.timer.start(100)

    def add_form_input(self):
        self.add_form(forms.inputForm(), nm.Module.Input.value)

    def add_form_canny(self):
        self.add_form(forms.CannyForm(), nm.Module.Canny.value)

    def add_form_cvt_color(self):
        self.add_form(forms.cvtColorForm(), nm.Module.CvtColor.value)

    def add_form_threshold(self):
        self.add_form(forms.thresholdForm(), nm.Module.Thresh.value)

    def add_form_find_contours(self):
        self.add_form(forms.findContoursForm(), nm.Module.FindCnt.value)

    def add_form_draw_contours(self):
        self.add_form(forms.drawContoursForm(), nm.Module.DrawCnt.value)

    def add_form(self, form, string):
        success, image = self.capture.read()
        obj_img = ip.ImageObj(image, ip.Color.BGR)
        index = self.toolBox.currentIndex()+1
        self.form_list.insert(index, form)
        self.image_list.insert(index, obj_img)
        self.toolBox.insertItem(index, form, string)
        self.toolBox.setCurrentIndex(index)
        self.update_form()

    def del_form(self):
        index = self.toolBox.currentIndex()
        if index == -1 or index == 0:
            pass
        else:
            self.toolBox.removeItem(index)
            del self.form_list[index]
            del self.image_list[index]
            self.update_form()

    def update_form(self):
        image_label_list = []
        for form in self.form_list:
            image_label_list.append(form.get_name())
            form.set_image_label_list(image_label_list)

    def update_image(self):
        success, image = self.capture.read()
        assert(success)
        obj_img = ip.ImageObj(image, ip.Color.BGR)
        self.image_list[0] = ip.cvt_color(obj_img, ip.Color.RGB)

        for (index, form) in enumerate(self.form_list):
            root = form.get_xml_element()
            assert(root is not None)
            self.image_list[index] = self.excute_image_processing(root)

        image = self.image_list[-1].image
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

    def excute_image_processing(self, root):
        module_str = root.get('name')
        img_index = int(root.find('common').find('picture_number').text)
        cnt_index = int(root.find('common').find('contour_number').text)
        obj_img = self.image_list[img_index]
        obj_cnt = self.image_list[cnt_index]
        if module_str == nm.Module.Input:
            return self.image_list[0]
        elif module_str == nm.Module.Canny:
            min_val = int(root.find('min').text)
            max_val = int(root.find('max').text)
            return ip.canny(obj_img, min_val, max_val)
        elif module_str == nm.Module.CvtColor:
            code = str(root.find('code').text)
            return ip.cvt_color(obj_img, ip.Color[code])
        elif module_str == nm.Module.Thresh:
            thresh = int(root.find('thresh').text)
            max_val = int(root.find('maxVal').text)
            thresh_type = str(root.find('thresholdType').text)
            return ip.threshold(obj_img, thresh,
                                max_val, ip.Thresh[thresh_type])
        elif module_str == nm.Module.FindCnt:
            mode = str(root.find('mode').text)
            method = str(root.find('method').text)
            return ip.find_contours(obj_img,
                                    ip.ContourMode[mode],
                                    ip.ContourMethod[method])
        elif module_str == nm.Module.DrawCnt:
            return ip.draw_contours(obj_img, obj_cnt)
        else:
            assert(False)
            return None


def main():
    app = QtWidgets.QApplication(sys.argv)
    MainForm()
    app.exec_()

if __name__ == "__main__":
    main()
