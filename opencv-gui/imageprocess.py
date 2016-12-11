import cv2
import enum
import error
import numpy as np
import pyocr
from PIL import Image


class ImageObj():
    def __init__(self, image, code, contours=None):
        self.set(image, code, contours)

    def set(self, image, code, contours=None):
        self.image = image
        self.code = code
        self.contours = contours


class Canny():
    name = 'Canny'

    @staticmethod
    def get_image(root, obj, _):
        min_val = int(root.find('min').text)
        max_val = int(root.find('max').text)
        image = cv2.Canny(obj.image, min_val, max_val)
        return ImageObj(image, CvtColor.Codes.GRAY, obj.contours)


class CvtColor():
    name = 'cvtColor'

    code_names = ['BGR', 'RGB', 'HSV', 'HLS', 'GRAY']
    Codes = enum.IntEnum('Color', code_names)
    cv2_cvt_codes = \
        [[None, cv2.COLOR_BGR2RGB, cv2.COLOR_BGR2HSV,
         cv2.COLOR_BGR2HLS, cv2.COLOR_BGR2GRAY],
         [cv2.COLOR_RGB2BGR, None, cv2.COLOR_RGB2HSV,
          cv2.COLOR_RGB2HLS, cv2.COLOR_RGB2GRAY],
         [cv2.COLOR_HSV2BGR, cv2.COLOR_HSV2RGB, None, None, None],
         [cv2.COLOR_HLS2BGR, cv2.COLOR_HLS2RGB, None, None, None],
         [cv2.COLOR_GRAY2BGR, cv2.COLOR_GRAY2RGB, None, None, None]]

    @classmethod
    def get_image(cls, root, obj, _):
        code = cls.Codes[str(root.find('code').text)]
        cv2_cvt_code = cls.cv2_cvt_codes[obj.code-1][code-1]
        if cv2_cvt_code is None:
            return ImageObj(obj.image, obj.code, obj.contours)
        else:
            image = cv2.cvtColor(obj.image, cv2_cvt_code)
            return ImageObj(image, code, obj.contours)


class Thresh():
    name = 'threshold'

    thresh_type_names = \
        ['BINARY', 'BINARY_INV', 'TRUNC', 'TOZERO', 'TOZERO_INV']
    ThreshTypes = enum.IntEnum('Thresh', thresh_type_names)
    cv2_thresh_types = \
        [cv2.THRESH_BINARY, cv2.THRESH_BINARY_INV, cv2.THRESH_TRUNC,
         cv2.THRESH_TOZERO, cv2.THRESH_TOZERO_INV]

    @classmethod
    def get_image(cls, root, obj, _):
        thresh = int(root.find('thresh').text)
        max_val = int(root.find('maxVal').text)
        thresh_type_str = str(root.find('threshType').text)
        thresh_type = cls.ThreshTypes[thresh_type_str]
        cv2_thresh_type = cls.cv2_thresh_types[thresh_type-1]
        _, image = cv2.threshold(obj.image, thresh, max_val, cv2_thresh_type)
        return ImageObj(image, obj.code, obj.contours)


class FindCnt():
    name = 'findContours'

    mode_names = ['LIST', 'EXTERNAL', 'CCOMP', 'TREE']
    Modes = enum.IntEnum('ContourMode', mode_names)
    cv2_modes = \
        [cv2.RETR_LIST, cv2.RETR_EXTERNAL, cv2.RETR_CCOMP, cv2.RETR_TREE]

    method_names = ['NONE', 'SIMPLE', 'TC89_L1', 'TC89_KCOS']
    Methods = enum.IntEnum('ContourMethod', method_names)
    cv2_methods = \
        [cv2.CHAIN_APPROX_NONE, cv2.CHAIN_APPROX_SIMPLE,
         cv2.CHAIN_APPROX_TC89_L1, cv2.CHAIN_APPROX_TC89_KCOS]

    @classmethod
    def get_image(cls, root, obj, _):
        mode = cls.Modes[str(root.find('mode').text)]
        method = cls.Methods[str(root.find('method').text)]
        cv2_mode = cls.cv2_modes[mode-1]
        cv2_method = cls.cv2_methods[method-1]
        if len(obj.image.shape) is not 2:
            raise error.ModuleError('input image should be one color only!')
        image = obj.image.copy()
        contours, hierarchy = cv2.findContours(image, cv2_mode, cv2_method)
        return ImageObj(image, obj.code, contours)


class DrawCnt():
    name = 'drawContours'

    @staticmethod
    def get_image(root, obj_img, obj_cnt):
        cnt_index = -1
        color = (0, 255, 0)
        thickness = 3
        image = obj_img.image.copy()
        cv2.drawContours(image, obj_cnt.contours,
                         cnt_index, color, thickness)
        return ImageObj(image, obj_img.code, obj_cnt.contours)


class kNNnumber():
    name = 'kNNnumber'

    def __init__(self):
        train_color = cv2.imread('./digits.png')
        train_gray = cv2.cvtColor(train_color, cv2.COLOR_BGR2GRAY)
        train_cell = [np.hsplit(row, 100) for row in np.vsplit(train_gray, 50)]
        x = np.array(train_cell)
        train = x[:, :].reshape(-1, 400).astype(np.float32)
        k = np.arange(10)
        train_labels = np.repeat(k, 500)[:, np.newaxis]
        self.knn = cv2.KNearest()
        self.knn.train(train, train_labels)

    def get_image(self, root, obj, _):
        k = int(root.find('K').text)
        if len(obj.image.shape) is not 2:
                raise error.ModuleError('input image must be one color only!')
        test_gray = cv2.resize(obj.image, (20, 20))
        test = test_gray.reshape(-1, 400).astype(np.float32)
        ret, result, neighbours, dist = self.knn.find_nearest(test, k)
        image = obj.image.copy()
        cv2.rectangle(image, (0, 0), (100, 100), (0, 0, 0), -1)
        cv2.putText(image, str(int(result[0][0])), (0, 100),
                    cv2.FONT_HERSHEY_PLAIN, 8, (255, 255, 255))
        return ImageObj(image, obj.code, obj.contours)


class Pyocr():
    name = 'PyOCR'

    psmodes_names = \
        ['Orientation_and_script_detection_(OSD)_only.',
         'Automatic_page_segmentation_with_OSD.',
         'Automatic_page_segmentation_but_no_OSD_or_OCR.',
         'Fully_automatic_page_segmentation_but_no_OSD._(Default)',
         'Assume_a_single_column_of_text_of_variable_sizes.',
         'Assume_a_single_uniform_block_of_vertically_aligned_text.',
         'Assume_a_single_uniform_block_of_text.',
         'Treat_the_image_as_a_single_text_line.',
         'Treat_the_image_as_a_single_word.',
         'Treat_the_image_as_a_single_word_in_a_circle.',
         'Treat_the_image_as_a_single_character.']
    PSModes = enum.IntEnum('PageSegmentationMode', psmodes_names)

    def __init__(self):
        self.tools = pyocr.get_available_tools()
        if len(self.tools) == 0:
                raise error.ModuleError('No OCR tool found')
        self.tool_names = map(lambda n:n.get_name(), self.tools)
        self.setTool(self.tool_names[0])

    def setTool(self, tool_name):
        for tool in self.tools:
            if tool.get_name() == tool_name:
                self.tool = tool
                break
        self.lang_names = self.tool.get_available_languages()

    def get_image(self, root, obj, _):
        lang = str(root.find('lang').text)
        psmode = self.PSModes[str(root.find('psmode').text)]-1
        image = obj.image.copy()
        builder = pyocr.builders.WordBoxBuilder(tesseract_layout=psmode)
        res = self.tool.image_to_string(Image.fromarray(image),
                                        lang=lang,
                                        builder=builder)
        for d in res:
            print d.content
            cv2.rectangle(image, d.position[0], d.position[1], (0, 0, 255), 2)
            cv2.putText(image, (d.content).encode('utf-8'), d.position[0],
                        cv2.FONT_HERSHEY_PLAIN, 8, (0, 0, 0))
        return ImageObj(image, obj.code, obj.contours)
