SHELL := /bin/bash

PYTHON_EXE             := python3
LIBRETRO_SUPER_GIT_URL := https://github.com/libretro/libretro-super.git

BUILD_DIR            := build
LIBRETRO_SUPER_DIR   := $(BUILD_DIR)/libretro-super
RETROARCH_DIR        := $(LIBRETRO_SUPER_DIR)/retroarch
RDB_DIR              := $(RETROARCH_DIR)/media/libretrodb/rdb
LIBRETRO_DB_DIR      := $(RETROARCH_DIR)/libretro-db
LIBRETRO_DB_TOOL_EXE := $(LIBRETRO_DB_DIR)/libretrodb_tool

SQLITE_DATABASE_FILE    := $(BUILD_DIR)/libretrodb.sqlite
SQLITE_DATABASE_ARCHIVE := $(SQLITE_DATABASE_FILE).tgz

# Setup the build directory
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Retrieve the libretro-super repository
$(LIBRETRO_SUPER_DIR): | $(BUILD_DIR)
	git clone $(LIBRETRO_SUPER_GIT_URL) $(LIBRETRO_SUPER_DIR)

# Retrieve the Retroarch data and build the database
$(RETROARCH_DIR): $(LIBRETRO_SUPER_DIR)
	cd $(LIBRETRO_SUPER_DIR) && \
		./libretro-fetch.sh retroarch && \
		./libretro-build-database.sh

# Build the libretrodb_tool
$(LIBRETRO_DB_TOOL_EXE): $(RETROARCH_DIR)
	$(MAKE) -C $(LIBRETRO_DB_DIR) libretrodb_tool

# Generates the .sqlite database file
$(SQLITE_DATABASE_FILE): $(LIBRETRO_DB_TOOL_EXE)
	$(PYTHON_EXE) main.py \
		--rdb-dir=$(RDB_DIR) \
		--output=$(SQLITE_DATABASE_FILE) \
		--libretrodb-tool=$(LIBRETRO_DB_TOOL_EXE)


# Creates a .tgz archive from the .sqlite file
$(SQLITE_DATABASE_ARCHIVE): $(SQLITE_DATABASE_FILE)
	tar -czf $(SQLITE_DATABASE_ARCHIVE) $(SQLITE_DATABASE_FILE)

.PHONY: database
database: $(SQLITE_DATABASE_FILE)

.PHONY: archive
archive: $(SQLITE_DATABASE_ARCHIVE)

.PHONY: all
all: database archive

.PHONY: clean-db
clean-db: clean-archive
	rm -f $(SQLITE_DATABASE_FILE)

.PHONY: clean-archive
clean-archive:
	rm -f $(SQLITE_DATABASE_FILE).tgz

.PHONY: clean-all
clean-all: clean-db clean-archive
	rm -rf $(BUILD_DIR)