#-----------------------------------
# Project Settings
#-----------------------------------

TARGET = fingerprint

CC = sdcc

PORT = /dev/ttyUSB0

#-----------------------------------
# Build
#-----------------------------------

build:
	$(CC) $(TARGET).c
	packihx $(TARGET).ihx > $(TARGET).hex

#-----------------------------------
# Upload
#-----------------------------------

upload:
	./p89pgm $(PORT) $(TARGET).hex

#-----------------------------------
# Clean
#-----------------------------------

clean:
	rm -f *.asm
	rm -f *.ihx
	rm -f *.hex
	rm -f *.lk
	rm -f *.lst
	rm -f *.map
	rm -f *.mem
	rm -f *.rel
	rm -f *.rst
	rm -f *.sym