.PHONY : build clean

ifeq ($(OS),Windows_NT)
FILE_NAME = 'Windows10.zip'
else
FILE_NAME = 'OS X.zip'
endif

build: dist
	tar -czf $(FILE_NAME) dist
	rm -rf build main.spec

dist: main.py
	pyinstaller -F main.py

clean:
	rm -r output dist build
	rm logs.txt main.spec