.PHONY : build clean

ifeq ($(OS),Windows_NT)
FILE_NAME = 'Windows10.zip'
else
FILE_NAME = 'macOS.zip'
endif

build: dist
	cp README.md config_simple.yaml dist
	mv dist/config_simple.yaml dist/config.yaml
	tar -czf $(FILE_NAME) dist
	rm -rf build main.spec

dist: main.py
	pyinstaller -F main.py
# change to rx r r so that the program can be executed
# ignores the error generated under Windows
	chmod 544 dist/main || true

clean:
	rm -rf output dist build apicache-py3 logs
	rm -f logs.txt macOS.zip Windows10.zip pywikibot.lwp throttle.ctrl