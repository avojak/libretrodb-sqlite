CREATE TABLE games (
    id INTEGER PRIMARY KEY,
    serial_id TEXT,
    rom_id INTEGER,
    developer_id INTEGER,
    franchise_id INTEGER,
    release_year INTEGER,
    release_month INTEGER,
    region_id INTEGER,
    genre_id INTEGER,
    description TEXT,
    display_name TEXT,
    boxart_url TEXT,
    platform_id INTEGER
);
CREATE TABLE roms (
    id INTEGER PRIMARY KEY,
    name TEXT,
    md5 TEXT
);
CREATE TABLE developers (
    id INTEGER PRIMARY KEY,
    name text
);
CREATE TABLE franchises (
    id INTEGER PRIMARY KEY,
    name text
);
CREATE TABLE regions (
    id INTEGER PRIMARY KEY,
    name text
);
CREATE TABLE genres (
    id INTEGER PRIMARY KEY,
    name text
);
CREATE TABLE platforms (
    id INTEGER PRIMARY KEY,
    name text
);
CREATE TABLE manufacturers (
    id INTEGER PRIMARY KEY,
    name text
);