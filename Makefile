.PHONY : build clean

ifeq ($(OS),Windows_NT)
FILE_NAME = 'Windows10.zip'
else
FILE_NAME = 'macOS.zip'
endif

build: dist
	cp README.md config.yaml dist
	tar -czf $(FILE_NAME) dist
	rm -rf build main.spec

dist: main.py
	pyinstaller -F main.py

clean:
	rm -rf output dist build apicache-py3 logs
	rm -f logs.txt macOS.zip Windows10.zip pywikibot.lwp throttle.ctrl