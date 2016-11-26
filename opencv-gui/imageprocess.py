import cv2
import enum


class ImageObj():
    def __init__(self, image, code, contours=None):
        self.set(image, code, contours)

    def set(self, image, code, contours=None):
        self.image = image
        self.code = code
        self.contours = contours


def canny(obj, minval, maxval):
    image = cv2.Canny(obj.image, minval, maxval)
    return ImageObj(image, Color.GRAY, obj.contours)


def cvt_color(obj, code):
    cvt_code = cvt_codes[obj.code-1][code-1]
    if cvt_code is None:
        return ImageObj(obj.image, obj.code, obj.contours)
    else:
        image = cv2.cvtColor(obj.image, cvt_code)
        return ImageObj(image, code, obj.contours)

color_array = ["BGR", "RGB", "HSV", "HLS", "GRAY"]
Color = enum.IntEnum("Color", color_array)
cvt_codes = \
    [[None, cv2.COLOR_BGR2RGB, cv2.COLOR_BGR2HSV,
     cv2.COLOR_BGR2HLS, cv2.COLOR_BGR2GRAY],
     [cv2.COLOR_RGB2BGR, None, cv2.COLOR_RGB2HSV,
      cv2.COLOR_RGB2HLS, cv2.COLOR_RGB2GRAY],
     [cv2.COLOR_HSV2BGR, cv2.COLOR_HSV2RGB, None, None, None],
     [cv2.COLOR_HLS2BGR, cv2.COLOR_HLS2RGB, None, None, None],
     [cv2.COLOR_GRAY2BGR, cv2.COLOR_GRAY2RGB, None, None, None]]


def threshold(img_obj, thresh, max_val, thresh_type):
    _, image = cv2.threshold(img_obj.image, thresh, max_val,
                             thresh_types[thresh_type-1])
    return ImageObj(image, img_obj.code, img_obj.contours)

thresh_array = ["BINARY", "BINARY_INV", "TRUNC", "TOZERO", "TOZERO_INV"]
Thresh = enum.IntEnum("Thresh", thresh_array)
thresh_types = [cv2.THRESH_BINARY, cv2.THRESH_BINARY_INV, cv2.THRESH_TRUNC,
                cv2.THRESH_TOZERO, cv2.THRESH_TOZERO_INV]


def find_contours(obj, cnt_mode, cnt_method):
    assert(len(obj.image.shape) == 2)
    image = obj.image.copy()
    contours, hierarchy = cv2.findContours(image,
                                           contour_modes[cnt_mode-1],
                                           contour_methods[cnt_method-1])
    return ImageObj(image, obj.code, contours)

contour_mode_array = ["LIST", "EXTERNAL", "CCOMP", "TREE"]
ContourMode = enum.IntEnum("ContourMode", contour_mode_array)
contour_modes = [cv2.RETR_LIST, cv2.RETR_EXTERNAL,
                 cv2.RETR_CCOMP, cv2.RETR_TREE]

contour_method_array = ["NONE", "SIMPLE", "TC89_L1", "TC89_KCOS"]
ContourMethod = enum.IntEnum("ContourMethod", contour_method_array)
contour_methods = [cv2.CHAIN_APPROX_NONE, cv2.CHAIN_APPROX_SIMPLE,
                   cv2.CHAIN_APPROX_TC89_L1, cv2.CHAIN_APPROX_TC89_KCOS]


def draw_contours(obj_img, obj_cnt,
                  cnt_index=-1, color=(0, 255, 0), thickness=3):
    image = obj_img.image.copy()
    cv2.drawContours(image, obj_cnt.contours,
                     cnt_index, color, thickness)
    return ImageObj(image, obj_img.code, obj_cnt.contours)
