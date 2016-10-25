

SRCS = main_window.ui common_ui.ui\
       input_ui.ui \
       Canny_ui.ui cvtColor_ui.ui
OBJS = ${SRCS:.ui=.py}

.SUFFIXES:
.SUFFIXES: .ui .py

all:$(OBJS)

.ui.py:
		pyuic5 $< -o $@

clean:
		rm -rf *.pyc *_ui.py
