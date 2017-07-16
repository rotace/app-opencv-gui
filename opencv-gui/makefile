

python_version_full := $(wordlist 2,4,$(subst ., ,$(shell python --version 2>&1)))
python_version_major := $(word 1,${python_version_full})
python_version_minor := $(word 2,${python_version_full})
python_version_patch := $(word 3,${python_version_full})


all:
	(cd gui; make)

run:all
ifeq (${python_version_major},2)
	python main.py
else
	@echo "!!! python vesrion should be 2.x !!!"
endif

clean:
	rm -rf *.pyc
	(cd gui; make clean)
