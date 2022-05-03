SHELL      := /bin/bash
PYTHON_EXE := python3

LIBRETRO_DATABASE_GIT_URL := https://github.com/libretro/libretro-database.git
LIBRETRO_DATABASE_TAG     := v1.10.3

BUILD_DIR             := build
LIBRETRO_DATABASE_DIR := $(BUILD_DIR)/libretro-database
LIBRETRO_RDB_DIR      := $(LIBRETRO_DATABASE_DIR)/rdb
LIBRETRO_SUPER_DIR    := $(LIBRETRO_DATABASE_DIR)/libretro-super
LIBRETRO_DB_TOOL_EXE  := $(LIBRETRO_SUPER_DIR)/retroarch/libretro-db/libretrodb_tool

SQLITE_DATABASE_FILE    := $(BUILD_DIR)/libretrodb.sqlite
SQLITE_DATABASE_ARCHIVE := $(SQLITE_DATABASE_FILE).tgz

# Setup the build directory
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(LIBRETRO_RDB_DIR): $(LIBRETRO_DATABASE_DIR) $(LIBRETRO_SUPER_DIR)

# Retrieve the libretro-database repository
$(LIBRETRO_DATABASE_DIR): | $(BUILD_DIR)
	git clone $(LIBRETRO_DATABASE_GIT_URL) $(LIBRETRO_DATABASE_DIR)
	git -C $(LIBRETRO_DATABASE_DIR) checkout tags/$(LIBRETRO_DATABASE_TAG)

# Build the libretro-database repository
$(LIBRETRO_SUPER_DIR): | $(LIBRETRO_DATABASE_DIR)
	$(MAKE) -C $(LIBRETRO_DATABASE_DIR) build

# Ensure that the libretrodb_tool is built
$(LIBRETRO_DB_TOOL_EXE): | $(LIBRETRO_SUPER_DIR)
	$(MAKE) -C $(LIBRETRO_DATABASE_DIR) build

# Generates the .sqlite database file
$(SQLITE_DATABASE_FILE): $(LIBRETRO_RDB_DIR) $(LIBRETRO_DB_TOOL_EXE)
	$(PYTHON_EXE) main.py \
		--rdb-dir=$(LIBRETRO_RDB_DIR) \
		--output=$(SQLITE_DATABASE_FILE) \
		--libretrodb-tool=$(LIBRETRO_DB_TOOL_EXE)

# Creates a .tgz archive from the .sqlite file
$(SQLITE_DATABASE_ARCHIVE): $(SQLITE_DATABASE_FILE)
	tar -czf $(SQLITE_DATABASE_ARCHIVE) $(SQLITE_DATABASE_FILE)

.PHONY: database
database: $(SQLITE_DATABASE_FILE)
	$(info $(shell du -sh $(SQLITE_DATABASE_FILE)))
	$(info $(shell sha256sum $(SQLITE_DATABASE_FILE)))

.PHONY: archive
archive: $(SQLITE_DATABASE_ARCHIVE)
	$(info $(shell du -sh $(SQLITE_DATABASE_ARCHIVE)))
	$(info $(shell sha256sum $(SQLITE_DATABASE_ARCHIVE)))

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