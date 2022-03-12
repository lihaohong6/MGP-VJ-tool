.PHONY : build clean

ifeq ($(OS),Windows_NT)
FILE_NAME = 'Windows10.zip'
else
FILE_NAME = 'macOS.zip'
endif

build: dist
	tar -czf $(FILE_NAME) dist
	rm -rf build main.spec

dist: main.py
	pyinstaller -F main.py

clean:
	rm -rf output dist build
	rm -f logs.txt main.spec macOS.zip Windows10.zip