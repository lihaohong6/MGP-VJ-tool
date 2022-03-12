.PHONY : build clear

build:
	pyinstaller -F main.py

clean:
	rm -r output
	rm logs.txt