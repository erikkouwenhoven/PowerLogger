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
            self.con = sqlite3.connect(dburi, uri=True)
            logging.info(f"Database {dbFilename} found")
        except sqlite3.OperationalError:  # does not exist
            self.con = self.createDB(dbFilename, signals)
        if self.check_columns(table="data", columns=['timestamp'] + signals) is False:
            logging.error("Existing database has different columns")

    def createDB(self, dbFilename, signals):
        logging.info("Creating database")
        con = sqlite3.connect(dbFilename)
        cur = con.cursor()
        s = "CREATE TABLE data (timestamp int" +\
            "".join([f", {signal} real" for signal in signals]) + ")"
        print(f"sql create table: {s}")
        cur.execute("CREATE TABLE data (timestamp int" +\
                    "".join([f", {signal} real" for signal in signals]) + ")")
        con.commit()
        return con

    def check_columns(self, table, columns):
        cur = self.con.cursor()
        cur.execute(f"pragma table_info({table})")
        res = cur.fetchall()
        print(f"pragma result: {res}")
        columnNames = [item[1] for item in res]
        print(f"columnNames: {columnNames}")
        for column in columnNames:
            if column not in res:
                return False
        return True
