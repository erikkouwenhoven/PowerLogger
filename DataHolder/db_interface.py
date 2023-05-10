import os
import sqlite3
from urllib.request import pathname2url
import logging
from Utils.settings import Settings


class DBInterface:

    def __init__(self, signals):
        dbFilename = os.path.join(Settings().data_dir_name(), Settings().db_filename())
        try:
            dburi = 'file:{}?mode=rw'.format(pathname2url(dbFilename))
            self.con = sqlite3.connect(dburi, uri=True, check_same_thread=False)
            logging.info(f"Database {dbFilename} found")
        except sqlite3.OperationalError:  # does not exist
            self.con = self.createDB(dbFilename, signals)
        if self.check_columns(table="data", columns=['timestamp'] + [str(signal) for signal in signals]) is False:
            logging.error("Existing database has different columns")

    def createDB(self, dbFilename, signals):
        logging.info("Creating database")
        con = sqlite3.connect(dbFilename, check_same_thread=False)
        cur = con.cursor()
        s = "CREATE TABLE data (timestamp int" +\
            "".join([f", {signal} real" for signal in signals]) + ")"
        logging.debug(f"sql create table: {s}")
        cur.execute(s)
        con.commit()
        return con

    def check_columns(self, table, columns):
        logging.debug(f"Checking columns of database, table={table}, against used columns: {columns}")
        for column in self.get_column_names(table):
            if column not in columns:
                return False
        return True

    def get_column_names(self, table):
        cur = self.con.cursor()
        cur.execute(f"pragma table_info({table})")
        res = cur.fetchall()
        logging.debug(f"pragma result: {res}")
        return [item[1] for item in res]

    def get_count(self):
        cur = self.con.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM data")
        except sqlite3.OperationalError:
            return 0
        res = cur.fetchone()
        return res[0]

    def get_data_item(self, idx, elements):
        cur = self.con.cursor()
        s = "SELECT timestamp " + "".join([f", {element}" for element in elements]) + "FROM data WHERE rowid=?"
        print(s)
        cur.execute("SELECT timestamp" +
                    "".join([f", {element}" for element in elements]) +
                    " FROM data WHERE rowid=?", (idx+1,))  # sqlite rowid starts at 1
        res = cur.fetchone()
        if res is None:
            res = [None] * (len(elements) + 1)
        print(f"result from get_data_item {res}")
        return res

    def insert_data_item(self, idx, elements, array):
        cur = self.con.cursor()
        cur.execute("UPDATE data SET timestamp=? " +
                    "".join([f", {element}=?" for element in elements]) +
                    "WHERE rowid=?", array + (idx+1))
        self.con.commit()

    def append_data_item(self, data_item_spec, array):
        logging.debug(f"append_data_item: data_item_spec = {data_item_spec}; array = {array}")
        cur = self.con.cursor()
        cur.execute("INSERT INTO data (timestamp" +
                    "".join([f", {element}" for element in data_item_spec.get_elements()]) +
                    ") VALUES (" + str(array[0]) +
                    "".join([f", {item}" for item in array[1:]]) + ")")
        self.con.commit()

    def get_all_data(self):
        cur = self.con.cursor()
        cur.execute("SELECT * FROM data")
        fetched = cur.fetchall()
        print(f"lengte binnengehaalde data {len(fetched)}")
        res = {col: [] for col in self.get_column_names('data')}
        for i, values in enumerate(res.values()):
            for row in fetched:
                values.append(row[i])
        for key in res:
            print(f"res[{key}] heeft lengte {len(res[key])}")
        return res

