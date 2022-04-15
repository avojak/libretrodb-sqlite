#!/usr/bin/env python3

import argparse
import json
import os
import sqlite3
import subprocess

from subprocess import PIPE

class Converter:

    def __init__(self, rdb_dir, output_file):
        self.rdb_dir = self._validate_rdb_dir(rdb_dir)
        self.output_file = self._validate_output_file(output_file)
        #print(self.rdb_dir)
        #print(self.output_file)
        self.libretrodb_tool = self._ensure_libretrodb_tool()
        self.roms = dict()
        self.developers = dict()
        self.franchises = dict()
        # self.regions = dict()
        self.genres = dict()
        # self.platforms = dict()
        # self.manufacturers = dict()
        self.games = dict()

    """
    Ensure that the provided directory of .rdb files exists.
    """
    def _validate_rdb_dir(self, rdb_dir):
        if not os.path.isdir(rdb_dir):
            print("{} is not a directory".format(rdb_dir))
            exit(1)
        return rdb_dir

    """
    Ensure that the provided output file doesn't already exist.
    """
    def _validate_output_file(self, output_file):
        if os.path.isfile(output_file):
            print("{} already exists".format(output_file))
            exit(1)
        return output_file

    """
    Ensure that the libretrodb_tool executable is on the PATH.
    """
    def _ensure_libretrodb_tool(self):
        proc = subprocess.Popen(["which", "libretrodb_tool"], stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            print("libretrodb_tool not found")
            exit(1)
        executable = stdout.decode('utf-8').strip()
        print("Found libretrodb_tool executable: {}".format(executable))
        return executable

    """
    Create and initialize the database.
    """
    def _create_database(self):
        connection = sqlite3.connect(self.output_file)
        cursor = connection.cursor()
        cursor.executescript(self._load_sql("./sql/create_tables.sql"))
        connection.commit()
        connection.close()
    
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
        # Create the SQLite database
        self._create_database()
        # Iterate over the .rdb files in the input directory
        for file in [f for f in os.listdir(self.rdb_dir) if os.path.isfile(os.path.join(self.rdb_dir, f))]:
            if not file.endswith('.rdb'):
                print("Skipping non-RDB file: {}".format(file))
                continue
            self._convert_file(os.path.join(self.rdb_dir, file))
            return # TODO: Remove this

    """
    Converts a single .rdb file into SQLite.
    """
    def _convert_file(self, rdb_file):
        print("  > Converting: {}".format(rdb_file))
        proc = subprocess.Popen([self.libretrodb_tool, rdb_file, "list"], stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        # if proc.returncode != 0:
            # XXX: For some reason this command has a return code of 1, but everything appears to run successfully
            # print("Error while running the libretrodb_tool against .rdb file: {}".format(stderr.decode('utf-8')))
            # return
        for line in stdout.decode('utf-8').strip().split("\n"):
            self._convert_line(line)

    """
    Converts a single line of JSON and inserts it into the database.
    """
    def _convert_line(self, json_str):
        # print(json_str)
        try:
            json_obj = json.loads(json_str)
        except json.decoder.JSONDecodeError as e:
            print("Error while parsing JSON: {}".format(e.msg))
            print("Original JSON string: {}".format(json_str))
            return
        serial = self._get_json_value(json_obj, 'serial')
        md5 = self._get_json_value(json_obj, 'md5')
        developer = self._get_json_value(json_obj, 'developer')
        franchise = self._get_json_value(json_obj, 'franchise')
        release_year = self._get_json_value(json_obj, 'release_year')
        release_month = self._get_json_value(json_obj, 'release_month')
        size = self._get_json_value(json_obj, 'size')
        rom_name = self._get_json_value(json_obj, 'rom_name')
        genre = self._get_json_value(json_obj, 'genre')
        description = self._get_json_value(json_obj, 'description')
        display_name = self._get_json_value(json_obj, 'name')

        # TODO: This needs some work to deconflict entries and potentially combine data
        #       There are many duplicate entries where the name or MD5 of the ROM is
        #       identical. This script should take that into account and rather than
        #       simply ignoring the second entry, check if the empty fields in the first
        #       can be filled with data from the second, etc.

        self._try_insert_developer(developer)
        self._try_insert_franchise(franchise)
        self._try_insert_genre(genre)        
        # self._try_insert_manufacturer(genre)
        self._try_insert_rom(rom_name, md5)
        self._insert_game(
            serial, 
            None if md5 is None else self.roms[md5],
            None if developer is None else self.developers[developer],
            None if franchise is None else self.franchises[franchise],
            release_year,
            release_month,
            None if genre is None else self.genres[genre],
            description,
            display_name)
    
    def _try_insert_developer(self, developer):
        if not developer in self.developers and developer is not None:
            id = len(self.developers) + 1
            self._sql_exec(self._load_sql("./sql/insert_developer.sql"), (id, developer))
            self.developers[developer] = id

    def _try_insert_franchise(self, franchise):
        if not franchise in self.franchises and franchise is not None:
            id = len(self.franchises) + 1
            self._sql_exec(self._load_sql("./sql/insert_franchise.sql"), (id, franchise))
            self.franchises[franchise] = id

    def _try_insert_genre(self, genre):
        if not genre in self.genres and genre is not None:
            id = len(self.genres) + 1
            self._sql_exec(self._load_sql("./sql/insert_genre.sql"), (id, genre))
            self.genres[genre] = id

    # def _try_insert_manufacturer(self, manufacturer):
    #     if not manufacturer in self.manufacturers and manufacturer is not None:
    #         id = len(self.manufacturers) + 1
    #         self._sql_exec(self._load_sql("./sql/insert_manufacturer.sql"), (id, manufacturer))
    #         self.manufacturers[manufacturer] = id

    def _try_insert_rom(self, name, md5):
        if md5 is None or name is None:
            return
        if not md5 in self.roms:
            id = len(self.roms) + 1
            self._sql_exec(self._load_sql("./sql/insert_rom.sql"), (id, name, md5))
            self.roms[md5] = id
    
    def _insert_game(self, serial_id, rom_id, developer_id, franchise_id, release_year, release_month, genre_id, description, display_name):
        id = len(self.games) + 1
        self._sql_exec(self._load_sql("./sql/insert_game.sql"), (id, serial_id, rom_id, developer_id, franchise_id, release_year, release_month, genre_id, description, display_name))
        self.games[id] = id

    def _sql_exec(self, sql, values):
        connection = sqlite3.connect(self.output_file)
        cursor = connection.cursor()
        cursor.execute(sql, values)
        connection.commit()
        connection.close()

    def _get_json_value(self, json_obj, key):
        return json_obj[key] if key in json_obj else None

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--rdb-dir', type=str, nargs=1, default=['./rdb'])
    parser.add_argument('--output', type=str, nargs=1, default=['libretrodb.sqlite'])
    args = parser.parse_args()
    Converter(args.rdb_dir[0], args.output[0]).run()