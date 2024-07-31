import os
import sqlite3
from typing import List, Dict
from urllib.request import pathname2url
import logging
from Utils.settings import Settings
from DataHolder.data_item import DataItemSpec


class DBInterface:

    def __init__(self, table: str, signals: List[str]):
        db_file_name = self.db_file_name()
        try:
            dburi = 'file:{}?mode=rw'.format(pathname2url(db_file_name))
            self.con = sqlite3.connect(dburi, uri=True, check_same_thread=False)
            logging.info(f"Database {db_file_name} found")
        except sqlite3.OperationalError:  # does not exist
            self.con = self.createDB(db_file_name)
        if table not in self.get_table_names():
            self.createTable(table, signals)
        else:
            if self.check_columns(table=table, columns=['timestamp'] + [str(signal) for signal in signals]) is False:
                logging.error("Existing database has different columns")

    @staticmethod
    def createDB(db_file_name: str):
        logging.info("Creating database")
        con = sqlite3.connect(db_file_name, check_same_thread=False)
        return con

    def createTable(self, table: str, signals: List[str]):
        cur = self.con.cursor()
        s = f"CREATE TABLE IF NOT EXISTS {table} (timestamp int" +\
            "".join([f", {signal} real" for signal in signals]) + ")"
        logging.debug(f"sql create table: {s}")
        cur.execute(s)
        self.con.commit()

    @staticmethod
    def db_file_name() -> str:
        return os.path.join(Settings().data_dir_name(), Settings().db_filename())

    def check_columns(self, table: str, columns: List[str]) -> bool:
        logging.debug(f"Checking columns of database, table={table}, against used columns: {columns}")
        for column in self.get_column_names(table):
            if column not in columns:
                return False
        return True

    def get_table_names(self) -> List[str]:
        cur = self.con.cursor()
        cur.execute("SELECT name from sqlite_master WHERE type='table'")
        res = cur.fetchall()
        logging.debug(f"table names: {res}")
        return [item[0] for item in res]

    def get_column_names(self, table: str) -> List[str]:
        cur = self.con.cursor()
        cur.execute(f"pragma table_info({table})")
        res = cur.fetchall()
        logging.debug(f"pragma result: {res}")
        return [item[1] for item in res]

    def get_count(self, table: str) -> int:
        cur = self.con.cursor()
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
        except sqlite3.OperationalError:
            return 0
        res = cur.fetchone()
        return res[0]

    def get_data_items(self, table: str, idx: int, elements: List[str]):
        cur = self.con.cursor()
        cur.execute("SELECT timestamp" +
                    "".join([f", {element}" for element in elements]) +
                    f" FROM {table} WHERE rowid=?", (idx+1,))  # sqlite rowid starts at 1
        res = cur.fetchone()
        if res is None:
            res = [None] * (len(elements) + 1)
        return res

    def insert_data_item(self, table: str, idx: int, data_item_spec: DataItemSpec, array: List[float]):
        cur = self.con.cursor()
        cur.execute(f"UPDATE {table} SET timestamp=? " +
                    "".join([f", {element}=?" for element in data_item_spec.get_elements()]) +
                    "WHERE rowid=?", array + [idx+1])
        self.con.commit()

    def append_data_item(self, table: str, data_item_spec: DataItemSpec, array: List[float]):
        cur = self.con.cursor()
        non_null_elements = [element for i, element in enumerate(data_item_spec.get_elements()) if array[i+1] is not None]
        cur.execute(f"INSERT INTO {table} (timestamp" +
                    "".join([f", {element}" for element in non_null_elements]) +
                    ") VALUES (" + str(array[0]) +
                    "".join([f", {item}" for item in array[1:] if item is not None]) + ")")
        self.con.commit()

    def get_all_data(self, table: str) -> Dict[str, List[float]]:
        cur = self.con.cursor()
        cur.execute(f"SELECT * FROM {table}")
        fetched = cur.fetchall()
        res = {col: [] for col in self.get_column_names(table)}
        for i, values in enumerate(res.values()):
            for row in fetched:
                values.append(row[i])
        return res

