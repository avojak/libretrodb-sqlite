# Libretro DB SQLite Converter

Tool to convert the Libretro database files (i.e. RetroArch `.rdb` files) into a single SQLite database file. In some cases, client applications may find a SQLite database easier to consume than the `.rdb` files.

## Prerequisites

- Obtain the `.rdb` file(s): https://github.com/libretro/RetroArch/blob/master/libretro-db/README.md

## Usage

```bash
$ python3 main.py [--rdb-dir RDB_DIR] [--output OUTPUT]
```

For example:

```bash
$ python3 main.py --rdb-dir ~/libretro-super/retroarch/media/libretrodb/rdb --output ~/libretrodb.sqlite
```

## Output Schema

### `games`

| Column | Data Type |
| ------ | --------- |
| id | INTEGER PRIMARY KEY |
| serial_id | TEXT |
| rom_id | INTEGER |
| developer_id | INTEGER |
| franchise_id | INTEGER |
| release_year | INTEGER |
| release_month | INTEGER |
| region_id | INTEGER |
| genre_id | INTEGER |
| description | TEXT |
| display_name | TEXT |
| boxart_url | TEXT |
| platform_id | INTEGER |

### `roms`

| Column | Data Type |
| ------ | --------- |
| id | INTEGER PRIMARY KEY |
| name | TEXT |
| md5 | TEXT |

### `developers`

| Column | Data Type |
| ------ | --------- |
| id | INTEGER PRIMARY KEY |
| name | TEXT |

### `franchises`

| Column | Data Type |
| ------ | --------- |
| id | INTEGER PRIMARY KEY |
| name | TEXT |

### `regions`

| Column | Data Type |
| ------ | --------- |
| id | INTEGER PRIMARY KEY |
| name | TEXT |

### `genres`

| Column | Data Type |
| ------ | --------- |
| id | INTEGER PRIMARY KEY |
| name | TEXT |

### `platforms`

| Column | Data Type |
| ------ | --------- |
| id | INTEGER PRIMARY KEY |
| name | TEXT |

### `manufacturers`

| Column | Data Type |
| ------ | --------- |
| id | INTEGER PRIMARY KEY |
| name | TEXT |