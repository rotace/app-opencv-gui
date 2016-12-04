

SRCS = main_window.ui common_ui.ui\
       input_ui.ui \
       canny_ui.ui cvt_color_ui.ui threshold_ui.ui\
			 find_contours_ui.ui draw_contours_ui.ui\
			 knn_number_ui.ui
OBJS = ${SRCS:.ui=.py}

.SUFFIXES:
.SUFFIXES: .ui .py

all:$(OBJS)

.ui.py:
		pyuic5 $< -o $@

clean:
		rm -rf *.pyc *_ui.py
