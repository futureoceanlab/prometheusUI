CC = gcc
CFLAGS += -Wall

BIN_NAME = prom-cli
BUILD_DIR = build
OUTPUT = $(BUILD_DIR)/$(BIN_NAME)
INSTALL_DIR = /usr/bin

INC_DIR = -Iinclude

SOURCES += src/main.c
SOURCES += src/network.c
SOURCES += src/api.c
SOURCES += src/modclk.c
SOURCES += src/capture.c

LIBS += -lpigpio -lrt

all: $(OUTPUT)

$(OUTPUT): $(BUILD_DIR)
	$(CC) $(CFLAGS) $(INC_DIR) -o $(OUTPUT) $(SOURCES) $(LIBS)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

install: $(OUTPUT)
	sudo cp $(OUTPUT) $(INSTALL_DIR)

clean:
	rm -rf $(BUILD_DIR)
