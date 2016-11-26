from enum import Enum


class Module(Enum):
    Input = "input"
    Canny = "Canny"
    CvtColor = "cvtColor"
    Thresh = "threshold"
    FindCnt = "findContours"
    DrawCnt = "drawContours"
