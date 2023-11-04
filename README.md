<img src="https://img.shields.io/badge/size-35%20MB-blue"></img>
<img src="https://img.shields.io/badge/compressed%20size-14%20MB-blue"></img>

# SQLite Libretro DB

In some cases, client applications may find a SQLite database easier to consume than the Libretro `.rdb` files. This project provides
the same content* from the Libretro RetroArch database in a single SQLite database file.

\* *Some data is excluded, such as the filesize of the ROM, and all checksums except for MD5*

***Important note:*** The conversion tool here also does some basic deconfliction when there are multiple records for the same ROM MD5 checksum.
The underlying assumption is that if two ROMs have the same checksum, they're the same, and the metadata should be merged in favor of non-null
values. The primary use-case is for client applications to be able to query the database by MD5 checksum of a ROM file, so keep in mind that 
this mindset informed the database schema and how the utility decides which data is duplicated.

## Usage

The pre-built database can be downloaded from the latest GitHub release.

To build from scratch:

```bash
$ make all
```

The build will create both the raw `.sqlite` database file, as well as a compressed `.tgz` version:

```bash
build/libretrodb.sqlite
build/libretrodb.sqlite.tgz
```

## Output Schema

### `games`

| Column | Data Type |
| ------ | --------- |
| id | INTEGER PRIMARY KEY |
| serial_id | TEXT |
| developer_id | INTEGER |
| publisher_id | INTEGER |
| rating_id | INTEGER |
| users | INTEGER |
| franchise_id | INTEGER |
| release_year | INTEGER |
| release_month | INTEGER |
| region_id | INTEGER |
| genre_id | INTEGER |
| display_name | TEXT |
| full_name | TEXT |
| boxart_url | TEXT |
| platform_id | INTEGER |

### `roms`

| Column | Data Type |
| ------ | --------- |
| id | INTEGER PRIMARY KEY |
| serial_id | INTEGER |
| name | TEXT |
| md5 | TEXT |

### `developers`

| Column | Data Type |
| ------ | --------- |
| id | INTEGER PRIMARY KEY |
| name | TEXT |

### `publishers`

| Column | Data Type |
| ------ | --------- |
| id | INTEGER PRIMARY KEY |
| name | TEXT |

### `ratings`

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

## Sample Query

Sample query for data based on a ROM file with the MD5 hash of `27F322F5CD535297AB21BC4A41CBFC12`:

```sql
SELECT games.serial_id,
	games.release_year,
	games.release_month,
	games.display_name,
	games.users,
	developers.name as developer_name,
	publishers.name as publisher_name,
	ratings.name as rating_name,	
	franchises.name as franchise_name,
	regions.name as region_name,
	genres.name as genre_name,
	roms.name as rom_name,
	roms.md5 as rom_md5,
	platforms.name as platform_name,
	manufacturers.name as manufacturer_name
FROM games
	LEFT JOIN developers ON games.developer_id = developers.id
	LEFT JOIN franchises ON games.franchise_id = franchises.id
	LEFT JOIN publishers ON games.publisher_id = publishers.id
	LEFT JOIN ratings ON games.rating_id = ratings.id
	LEFT JOIN genres ON games.genre_id = genres.id
	LEFT JOIN platforms ON games.platform_id = platforms.id
		LEFT JOIN manufacturers ON platforms.manufacturer_id = manufacturers.id
	LEFT JOIN regions ON games.region_id = regions.id
	INNER JOIN roms ON games.serial_id = roms.serial_id
WHERE roms.md5 = "27F322F5CD535297AB21BC4A41CBFC12";
```

Output:

| serial_id | release_year | release_month | display_name | developer_name | franchise_name | region_name | genre_name | rom_name | rom_md5 | platform_name | manufacturer_name |
| --------- | ------------ | ------------- | ------------ | -------------- | -------------- | ----------- | ---------- | -------- | ------- | ------------- | ----------------- |
| 41575245 | 2001 | 9 | Advance Wars | Intelligent Systems | Advance Wars | USA | Strategy | Advance Wars (USA).gba | 27F322F5CD535297AB21BC4A41CBFC12 | Game Boy Advance | Nintendo |

## Artwork

Up to three types of artwork can be retrieved:

1. Cover/box art (i.e. `Named_Boxarts`)
2. In-game snapshots (i.e. `Named_Snaps`)
3. Title screens (i.e. `Named_Titles`)

The pre-URL-encoded format for a request for artwork is:

```
http://thumbnails.libretro.com/[[MANUFACTURER - ]PLATFORM]/[TYPE]/[DISPLAY_NAME].png
```

For example, to retrieve the box art for Advance Wars on the Game Boy Advance:

```
http://thumbnails.libretro.com/Nintendo%20-%20Game%20Boy%20Advance/Named_Boxarts/Advance%20Wars%20%28USA%29.png
```

## License

This data is provided under the same license as the original data files: https://github.com/libretro/libretro-database/blob/master/COPYING