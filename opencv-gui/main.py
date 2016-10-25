import sys
from PyQt5 import QtGui, QtWidgets, QtCore
from xml.etree import ElementTree
import numpy as np
import cv2
from gui import forms, main_window


class MainForm(QtWidgets.QMainWindow, main_window.Ui_MainWindow):
    def __init__(self):
        super(self.__class__,self).__init__()
        self.setupUi(self)
        self.actionClose.triggered.connect(QtWidgets.qApp.quit)
        self.actionCanny.triggered.connect(self.add_form_canny)
        self.actionCvtColor.triggered.connect(self.add_form_cvtcolor)
        self.pushButtonDelete.clicked.connect(lambda: self.del_form())
        self.show()

        self.capture = cv2.VideoCapture(0)
        self.scene   = QtWidgets.QGraphicsScene()
        self.pixitem = QtWidgets.QGraphicsPixmapItem()
        self.scene.addItem(self.pixitem)
        self.graphicsView.setScene(self.scene)

        self.form_list  = []
        self.picture_list = []
        self.toolBox.removeItem(0)
        self.add_form_input()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_picture)
        self.timer.start(100)

    def add_form_input(self):
        self.add_form(forms.inputForm(),"input")

    def add_form_canny(self):
        self.add_form(forms.CannyForm(),"Canny")

    def add_form_cvtcolor(self):
        self.add_form(forms.cvtColorForm(),"cvtColor")

    def add_form(self,form,string):
        success, picture = self.capture.read()
        index = self.toolBox.currentIndex()+1
        self.form_list.insert(index,form)
        self.picture_list.insert(index,picture)
        self.toolBox.insertItem(index,form,string)
        self.toolBox.setCurrentIndex(index)
        self.update_form()

    def del_form(self):
        index = self.toolBox.currentIndex()
        if index == -1 or index == 0:
            pass
        else:
            self.toolBox.removeItem(index)
            del self.form_list[index]
            del self.picture_list[index]
            self.update_form()

    def update_form(self):
        picture_label_list = []
        for form in self.form_list:
            picture_label_list.append(form.get_name())
            form.set_picture_label_list(picture_label_list)

    def update_picture(self):
        success, self.picture_list[0] = self.capture.read()
        if not success:
            # message
            pass

        self.picture_list[0] = cv2.cvtColor(self.picture_list[0],cv2.COLOR_BGR2RGB)

        for (index,form) in enumerate(self.form_list):
            root = form.get_xml_element()
            assert( root is not None )
            self.picture_list[index] = self.excute_image_processing(root,self.picture_list)

        picture = self.picture_list[-1]
        if   len(picture.shape)==2: # gray scale
            h,w = picture.shape
            self.image = QtGui.QImage(picture.data, w, h, w, QtGui.QImage.Format_Indexed8)
        elif len(picture.shape)==3: # RGB color
            h,w,d = picture.shape
            self.image = QtGui.QImage(picture.data, w, h, w*d, QtGui.QImage.Format_RGB888)

        self.pixmap = QtGui.QPixmap.fromImage(self.image)
        self.pixitem.setPixmap(self.pixmap)

    def excute_image_processing(self,root,picture_list):
        module_str = root.get('name')
        index = int(root.find('common').find('picture_number').text)
        picture = picture_list[index]
        if   module_str == "input":
            return picture_list[0]
        elif module_str == "Canny":
            min_int = int(root.find('min').text)
            max_int = int(root.find('max').text)
            picture = cv2.Canny(picture,min_int,max_int)
            return picture
        elif module_str == "cvtColor":
            picture = cv2.cvtColor(picture,cv2.COLOR_RGB2GRAY)
            return picture

def main():
    app = QtWidgets.QApplication(sys.argv)
    form = MainForm()
    app.exec_()

if __name__ == "__main__":
    main()
