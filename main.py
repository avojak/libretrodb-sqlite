#!/usr/bin/env python3

import argparse
import json
import os
import sqlite3
import subprocess

from pathlib import Path
from subprocess import PIPE

class Logger:

    def __init__(self):
        self.CRED = '\033[91m'
        self.CGREEN = '\033[92m'
        self.CEND = '\033[0m'

    def error(self, msg):
        print("{cred}{msg}{cend}".format(cred=self.CRED, msg=msg, cend=self.CEND))

    def info(self, msg):
        print(msg)

    def success(self, msg):
        print("{cgreen}{msg}{cend}".format(cgreen=self.CGREEN, msg=msg, cend=self.CEND))

class Platform:

    def __init__(self, name, manufacturer_id):
        self.id = None
        self.name = name
        self.manufacturer_id = manufacturer_id

class ROM:

    def __init__(self, serial, name, md5):
        self.id = None
        self.serial = serial
        self.name = name
        self.md5 = md5

class Game:

    def __init__(self, display_name, full_name, serial, developer_id, publisher_id, rating_id, users, franchise_id, release_year, release_month, region_id, genre_id, platform_id):
        self.id = None
        self.display_name = display_name
        self.full_name = full_name
        self.serial = serial
        self.developer_id = developer_id
        self.publisher_id = publisher_id
        self.rating_id = rating_id
        self.users = users
        self.franchise_id = franchise_id
        self.release_year = release_year
        self.release_month = release_month
        self.region_id = region_id
        self.genre_id = genre_id
        self.platform_id = platform_id

    """
    Merge other game into self by deferring to non-null fields.
    """
    def join(self, other):
        if self.display_name is None and other.display_name is not None:
            self.display_name = other.display_name
        if self.full_name is None and other.full_name is not None:
            self.full_name = other.full_name
        if self.serial is None and other.serial is not None:
            self.serial = other.serial
        if self.developer_id is None and other.developer_id is not None:
            self.developer_id = other.developer_id
        if self.publisher_id is None and other.publisher_id is not None:
            self.publisher_id = other.publisher_id
        if self.rating_id is None and other.rating_id is not None:
            self.rating_id = other.rating_id
        if self.users is None and other.users is not None:
            self.users = other.users
        if self.franchise_id is None and other.franchise_id is not None:
            self.franchise_id = other.franchise_id
        if self.release_year is None and other.release_year is not None:
            self.release_year = other.release_year
        if self.release_month is None and other.release_month is not None:
            self.release_month = other.release_month
        if self.region_id is None and other.region_id is not None:
            self.region_id = other.region_id
        if self.genre_id is None and other.genre_id is not None:
            self.genre_id = other.genre_id
        if self.platform_id is None and other.platform_id is not None:
            self.platform_id = other.platform_id

class Converter:

    def __init__(self, rdb_dir, output_file, libretrodb_tool):
        self.logger = Logger()
        self.rdb_dir = self._validate_rdb_dir(rdb_dir)
        self.output_file = self._validate_output_file(output_file)
        self.libretrodb_tool = self._validate_libretrodb_tool(libretrodb_tool)
        # Create storage for parsed data prior to insertion in the database
        self.developers = dict()
        self.publishers = dict()
        self.ratings = dict()
        self.franchises = dict()
        self.regions = dict()
        self.genres = dict()
        self.platforms = dict()
        self.manufacturers = dict()
        self.games = dict()
        self.roms = dict()

    """
    Ensure that the provided directory of .rdb files exists.
    """
    def _validate_rdb_dir(self, rdb_dir):
        if not os.path.isdir(rdb_dir):
            self.logger.error("{} is not a directory".format(rdb_dir))
            exit(1)
        return rdb_dir

    """
    Ensure that the provided output file doesn't already exist.
    """
    def _validate_output_file(self, output_file):
        if os.path.isfile(output_file):
            self.logger.error("{} already exists".format(output_file))
            exit(1)
        return output_file

    """
    Ensure that the libretrodb_tool executable is on the PATH.
    """
    # def _ensure_libretrodb_tool(self):
    #     proc = subprocess.Popen(["which", "libretrodb_tool"], stdout=PIPE, stderr=PIPE)
    #     stdout, stderr = proc.communicate()
    #     if proc.returncode != 0:
    #         print("libretrodb_tool not found")
    #         exit(1)
    #     executable = stdout.decode('utf-8').strip()
    #     print("Found libretrodb_tool executable: {}".format(executable))
    #     return executable

    """
    Ensure that the libretrodb_tool can be found
    """
    def _validate_libretrodb_tool(self, libretrodb_tool):
        if not os.path.isfile(libretrodb_tool):
            self.logger.error("{} not found".format(libretrodb_tool))
            exit(1)
        return libretrodb_tool
    
    """
    Reads the content of a SQL file as a string.
    """
    def _load_sql(self, sql_file):
        file = open(sql_file, 'r')
        sql = file.read()
        file.close()
        return sql

    """
    Run the conversion tool.
    """
    def run(self):
        # Iterate over the .rdb files in the input directory and parse all data
        for file in [f for f in os.listdir(self.rdb_dir) if os.path.isfile(os.path.join(self.rdb_dir, f))]:
            if not file.endswith('.rdb'):
                self.logger.info("Skipping non-RDB file: {}".format(file))
                continue
            self._parse_platform_file(os.path.join(self.rdb_dir, file))
            # break # TODO: Remove this
        
        # Open the database connection
        connection = sqlite3.connect(self.output_file)
        cursor = connection.cursor()

        # Create the SQLite database
        cursor.executescript(self._load_sql("./sql/create_tables.sql"))

        # Insert data into the database
        self._insert_developers(cursor)
        self._insert_publishers(cursor)
        self._insert_ratings(cursor)
        self._insert_franchises(cursor)
        self._insert_genres(cursor)
        self._insert_manufacturers(cursor)
        self._insert_platforms(cursor)
        self._insert_regions(cursor)
        self._insert_games(cursor)
        self._insert_roms(cursor)

        # Commit changes to the database
        connection.commit()
        connection.close()

        # TODO: Create compressed file

    """
    Parses a single platform .rdb file.
    """
    def _parse_platform_file(self, rdb_file):
        self.logger.info("Parsing {}".format(rdb_file))

        # Try to parse out the manufacturer and platfrom from the .rdb filename
        system_fullname = Path(rdb_file).stem
        manufacturer_name = system_fullname.split(" - ")[0] if system_fullname.find(" - ") != -1 else None
        platform_name = system_fullname[system_fullname.find(" - ") + len(" - "):] if system_fullname.find(" - ") != -1 else system_fullname
        
        # Save the manufacturer name and generate an ID
        if manufacturer_name is not None and manufacturer_name not in self.manufacturers:
            self.manufacturers[manufacturer_name] = len(self.manufacturers) + 1

        # Create and save a platform model
        manufacturer_id = self.manufacturers[manufacturer_name] if manufacturer_name is not None else None
        platform = Platform(platform_name, manufacturer_id)
        platform.id = len(self.platforms) + 1
        self.platforms[platform_name] = platform

        # Parse the file line-by-line
        proc = subprocess.Popen([self.libretrodb_tool, rdb_file, "list"], stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        # if proc.returncode != 0:
            # XXX: For some reason this command has a return code of 1, but everything appears to run successfully
            # print("Error while running the libretrodb_tool against .rdb file: {}".format(stderr.decode('utf-8')))
            # return
        for line in stdout.decode('utf-8').strip().split("\n"):
            self._parse_line(line, platform.id)

    """
    Parses a single line of JSON from the .rdb file.
    """
    def _parse_line(self, json_str, platform_id):
        # Parse the string as JSON
        try:
            json_obj = json.loads(json_str)
        except json.decoder.JSONDecodeError as e:
            self.logger.error("Error while parsing JSON: {}".format(str(e)))
            self.logger.error("Original JSON string: {}".format(json_str))
            return

        # Extract the fields from the JSON
        serial = self._get_json_value(json_obj, 'serial')
        md5 = self._get_json_value(json_obj, 'md5')
        developer = self._get_json_value(json_obj, 'developer')
        publisher = self._get_json_value(json_obj, 'publisher')
        rating = self._get_json_value(json_obj, 'esrb_rating')
        users = self._get_json_value(json_obj, 'users')
        franchise = self._get_json_value(json_obj, 'franchise')
        release_year = self._get_json_value(json_obj, 'releaseyear')
        release_month = self._get_json_value(json_obj, 'releasemonth')
        size = self._get_json_value(json_obj, 'size')
        rom_name = self._get_json_value(json_obj, 'rom_name')
        region = self._get_json_value(json_obj, 'region')
        genre = self._get_json_value(json_obj, 'genre')
        # description = self._get_json_value(json_obj, 'description') # This field in the dataset doesn't currently provide any added value
        full_name = self._get_json_value(json_obj, 'name')
        
        # Build the display name from the full name, but ignore all the trailing parenthesis-wrapped meta-tags
        if full_name is None:
            display_name = None
        else:
            display_name = full_name.split("(")[0].strip() if "(" in full_name else full_name

        # Save potentially common references to developers, franchises, regions and genres, and assign an ID
        if developer is not None and developer not in self.developers:
            self.developers[developer] = len(self.developers) + 1
        if publisher is not None and publisher not in self.publishers:
            self.publishers[publisher] = len(self.publishers) + 1
        if rating is not None and rating not in self.ratings:
            self.ratings[rating] = len(self.ratings) + 1
        if franchise is not None and franchise not in self.franchises:
            self.franchises[franchise] = len(self.franchises) + 1
        if region is not None and region not in self.regions:
            self.regions[region] = len(self.regions) + 1
        if genre is not None and genre not in self.genres:
            self.genres[genre] = len(self.genres) + 1

        developer_id = self.developers[developer] if developer is not None else None
        publisher_id = self.publishers[publisher] if publisher is not None else None
        rating_id = self.ratings[rating] if rating is not None else None
        franchise_id = self.franchises[franchise] if franchise is not None else None
        region_id = self.regions[region] if region is not None else None
        genre_id = self.genres[genre] if genre is not None else None

        # Build the ROM and Game objects. Note that ROMs and games should be 1:1.
        rom = ROM(serial, rom_name, md5)
        rom_id = len(self.roms) + 1
        rom.id = rom_id
        self.roms[rom_id] = rom

        game = Game(display_name, full_name, serial, developer_id, publisher_id, rating_id, users, franchise_id, release_year, release_month, region_id, genre_id, platform_id)
        if serial in self.games:
            self.games[serial].join(game)
        else:
            id = len(self.games) + 1
            game.id = id
            self.games[serial] = game
    
    """
    Insert the manufacturers into the database.
    """
    def _insert_manufacturers(self, cursor):
        for key,value in self.manufacturers.items():
            (id, name) = (value, key)
            cursor.execute(self._load_sql("./sql/insert_manufacturer.sql"), (id, name))
        self.logger.success("Inserted {} manufacturers into database".format(len(self.manufacturers)))
    
    """
    Insert the platforms into the database.
    """
    def _insert_platforms(self, cursor):
        for key,value in self.platforms.items():
            cursor.execute(self._load_sql("./sql/insert_platform.sql"), (value.id, value.name, value.manufacturer_id))
        self.logger.success("Inserted {} platforms into database".format(len(self.platforms)))

    """
    Insert the developers into the database.
    """
    def _insert_developers(self, cursor):
        for key,value in self.developers.items():
            (id, name) = (value, key)
            cursor.execute(self._load_sql("./sql/insert_developer.sql"), (id, name))
        self.logger.success("Inserted {} developers into database".format(len(self.developers)))

    """
    Insert the publishers into the database.
    """
    def _insert_publishers(self, cursor):
        for key,value in self.publishers.items():
            (id, name) = (value, key)
            cursor.execute(self._load_sql("./sql/insert_publisher.sql"), (id, name))
        self.logger.success("Inserted {} publishers into database".format(len(self.publishers)))
    
    """
    Insert the ratings into the database.
    """
    def _insert_ratings(self, cursor):
        for key,value in self.ratings.items():
            (id, name) = (value, key)
            cursor.execute(self._load_sql("./sql/insert_rating.sql"), (id, name))
        self.logger.success("Inserted {} ratings into database".format(len(self.ratings)))

    """
    Insert the franchises into the database.
    """
    def _insert_franchises(self, cursor):
        for key,value in self.franchises.items():
            (id, name) = (value, key)
            cursor.execute(self._load_sql("./sql/insert_franchise.sql"), (id, name))
        self.logger.success("Inserted {} franchises into database".format(len(self.franchises)))

    """
    Insert the regions into the database.
    """
    def _insert_regions(self, cursor):
        for key,value in self.regions.items():
            (id, name) = (value, key)
            cursor.execute(self._load_sql("./sql/insert_region.sql"), (id, name))
        self.logger.success("Inserted {} regions into database".format(len(self.regions)))

    """
    Insert the genres into the database.
    """
    def _insert_genres(self, cursor):
        for key,value in self.genres.items():
            (id, name) = (value, key)
            cursor.execute(self._load_sql("./sql/insert_genre.sql"), (id, name))
        self.logger.success("Inserted {} genres into database".format(len(self.genres)))

    """
    Insert the games into the database.
    """
    def _insert_games(self, cursor):
        for key,value in self.games.items():
            game = value
            cursor.execute(self._load_sql("./sql/insert_game.sql"), (
                game.id, 
                game.serial,
                game.developer_id,
                game.publisher_id,
                game.rating_id,
                game.users,
                game.franchise_id,
                game.release_year,
                game.release_month,
                game.region_id,
                game.genre_id,
                game.display_name,
                game.full_name,
                game.platform_id))
        self.logger.success("Inserted {} games into database".format(len(self.games)))

    """
    Insert the ROMs into the database.
    """
    def _insert_roms(self, cursor):
        # cursor.execute(self._load_sql("./sql/insert_rom.sql"), (game.rom.id, game.rom.name, game.rom.md5))
        for key,value in self.roms.items():
            rom = value
            cursor.execute(self._load_sql("./sql/insert_rom.sql"), (rom.id, rom.serial, rom.name, rom.md5))
        self.logger.success("Inserted {} ROMs into database".format(len(self.roms)))

    def _get_json_value(self, json_obj, key):
        return json_obj[key] if key in json_obj else None

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--rdb-dir', type=str, nargs=1, default=['./rdb'])
    parser.add_argument('--output', type=str, nargs=1, default=['libretrodb.sqlite'])
    parser.add_argument('--libretrodb-tool', type=str, nargs=1, default=['libretrodb_tool'])
    args = parser.parse_args()
    Converter(args.rdb_dir[0], args.output[0], args.libretrodb_tool[0]).run()
