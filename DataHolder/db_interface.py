from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
import sqlite3
import mariadb
from urllib.request import pathname2url
import logging
from DataHolder.data_item import DataItemSpec


class DBInterface(ABC):

    def __init__(self, specifics: DBSpecifics):
        self.specifics = specifics
        self.con = self.init_connection(specifics)

    @abstractmethod
    def init_connection(self, specifics: DBSpecifics) -> sqlite3.Connection | mariadb.Connection:
        pass

    def post_init_check(self, table: str, signals: list[str]):
        if table not in self.get_table_names():
            self.create_table(table, signals)
        else:
            if self.check_columns(table=table, columns=['timestamp'] + signals) is False:
                logging.error(f"Existing database, table {table} has different columns: {self.get_column_names(table)} "
                              f"vs. {['timestamp'] + signals}")

    def check_columns(self, table: str, columns: list[str]) -> bool:
        logging.debug(f"Checking columns of database, table={table}, against used columns: {columns}")
        for column in self.get_column_names(table):
            if column not in columns:
                logging.debug(f"column {column} not found in columns {columns}")
                return False
        return True

    @abstractmethod
    def create_table(self, table: str, signals: list[str]):
        pass

    @abstractmethod
    def get_table_names(self) -> list[str]:
        pass

    @abstractmethod
    def get_column_names(self, table: str) -> list[str]:
        pass

    def get_count(self, table: str) -> int:
        cur = self.con.cursor()
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
        except (sqlite3.OperationalError, mariadb.ProgrammingError):
            return 0
        res = cur.fetchone()
        return res[0]

    def get_data_items(self, table: str, idx: int, elements: list[str]):
        cur = self.con.cursor()
        cur.execute("SELECT timestamp" +
                    "".join([f", {element}" for element in elements]) +
                    f" FROM {table} WHERE rowid=?", (idx+1,))  # sqlite rowid starts at 1
        res = cur.fetchone()
        if res is None:
            res = [None] * (len(elements) + 1)
        return res

    @abstractmethod
    def insert_data_item(self, table: str, idx: int, data_item_spec: DataItemSpec, array: list[float | None]):
        pass

    def append_data_item(self, table: str, data_item_spec: DataItemSpec, array: list[float | None]):
        cur = self.con.cursor()
        non_null_elements = [element for i, element in enumerate(data_item_spec.get_elements()) if array[i+1] is not None]
        cur.execute(f"INSERT INTO {table} (timestamp" +
                    "".join([f", {item}" for item in non_null_elements]) +
                    ") VALUES (" + str(array[0]) +
                    "".join([f", {item}" for item in array[1:] if item is not None]) + ")")
        self.con.commit()

    def modify_element(self, table: str, idx: int, element: str, value: float):
        cur = self.con.cursor()
        cur.execute(f"UPDATE {table} SET {element}=? WHERE rowid=?", (value, idx+1))
        self.con.commit()

    def get_all_data(self, table: str) -> dict[str, list[float]]:
        cur = self.con.cursor()
        cur.execute("SELECT timestamp" +
                    "".join([f", {element}" for element in self.get_column_names(table)]) +
                    f" FROM {table}")
        fetched = cur.fetchall()
        res: dict[str, list[float]] = {col: [] for col in ['timestamp'] + self.get_column_names(table)}
        for i, values in enumerate(res.values()):
            for row in fetched:
                values.append(row[i])
        return res

    @abstractmethod
    def size(self) -> int:
        pass


class SQLiteDBInterface(DBInterface):

    def __init__(self, specifics: SQLiteDBSpecifics):
        super().__init__(specifics)

    def init_connection(self, specifics: DBSpecifics) -> sqlite3.Connection:
        sqlite_spec = SQLiteDBSpecifics.cast_from_super(specifics)
        db_file_name = sqlite_spec.filename
        try:
            dburi = 'file:{}?mode=rw'.format(pathname2url(db_file_name))
            con = sqlite3.connect(dburi, uri=True, check_same_thread=False)
            logging.info(f"Sqlite database {db_file_name} found")
        except sqlite3.OperationalError:  # does not exist
            con = sqlite3.connect(db_file_name, check_same_thread=False)
            logging.info("Creating Sqlite database")
        return con

    def create_table(self, table: str, signals: list[str]):
        cur = self.con.cursor()
        s = (f"CREATE TABLE IF NOT EXISTS {table} "
             f"(timestamp int") +\
            "".join([f", {signal} real" for signal in signals]) + ")"
        logging.debug(f"sql create table: {s}")
        cur.execute(s)
        self.con.commit()

    def get_table_names(self) -> list[str]:
        cur = self.con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        res = cur.fetchall()
        logging.debug(f"table names: {res}")
        return [item[0] for item in res]

    def get_column_names(self, table: str) -> list[str]:
        cur = self.con.cursor()
        cur.execute(f"pragma table_info({table})")
        res = cur.fetchall()
        logging.debug(f"pragma result: {res}")
        return [item[1] for item in res if item[1] != "timestamp"]

    def insert_data_item(self, table: str, idx: int, data_item_spec: DataItemSpec, array: list[float | None]):
        cur = self.con.cursor()
        cur.execute(f"UPDATE {table} SET timestamp=? " +
                    "".join([f", {element}=?" for element in data_item_spec.get_elements()]) +
                    "WHERE rowid=?", array + [idx+1])
        self.con.commit()

    def size(self) -> int:
        cur = self.con.cursor()
        cur.execute(f"pragma page_count;")
        page_count = cur.fetchall()[0][0]
        cur.execute(f"pragma page_size;")
        page_size = cur.fetchall()[0][0]
        return page_count * page_size


class MariaDBInterface(DBInterface):

    def __init__(self, specifics: MariaDBSpecifics):
        super().__init__(specifics)

    def init_connection(self, specifics: DBSpecifics) -> mariadb.Connection:
        maria_spec = MariaDBSpecifics.cast_from_super(specifics)
        try:
            conn = MariaDBInterface.connect(maria_spec, connect_host_only=False)
        except mariadb.Error as e:
            conn = MariaDBInterface.connect(maria_spec, connect_host_only=True)
            cur = conn.cursor()
            cur.execute(f"CREATE DATABASE home_power")
            conn = MariaDBInterface.connect(maria_spec, connect_host_only=False)
        return conn

    @staticmethod
    def connect(specifics: MariaDBSpecifics, connect_host_only: bool) -> mariadb.Connection:
        return mariadb.connect(
            user=specifics.user,
            password=specifics.pwd,
            host=specifics.host,
            port=specifics.port,
            database=specifics.database if connect_host_only is False else None
        )

    def create_table(self, table: str, signals: list[str]):
        cur = self.con.cursor()
        s = (f"CREATE TABLE IF NOT EXISTS {table} "
             f"(rowid INTEGER AUTO_INCREMENT PRIMARY KEY,"
             f"timestamp int") +\
            "".join([f", {signal} real" for signal in signals]) + ")"
        logging.debug(f"sql create table: {s}")
        cur.execute(s)
        self.con.commit()

    def get_table_names(self) -> list[str]:
        cur = self.con.cursor()
        cur.execute(f"SHOW TABLES;")
        res = cur.fetchall()
        return [item[0] for item in res]

    def get_column_names(self, table: str) -> list[str]:
        cur = self.con.cursor()
        cur.execute(f"SHOW columns FROM {table};")
        res = cur.fetchall()
        return [item[0] for item in res if item[0] != "rowid" and item[0] != "timestamp"]

    def insert_data_item(self, table: str, idx: int, data_item_spec: DataItemSpec, array: list[float | None]):
        cur = self.con.cursor()
        cur.execute(f"UPDATE {table} SET timestamp={array[0]} " +
                    "".join([f", {element}={array[i+1]}" for i, element in enumerate(data_item_spec.get_elements())]) +
                    f"WHERE rowid={idx+1}")
        self.con.commit()

    def size(self) -> int:
        database = getattr(self.specifics, "database")
        cur = self.con.cursor()
        cur.execute(f"SELECT table_schema AS Databases_list, table_name AS Tables_list, "
                    f"ROUND(data_length + index_length, 2) AS size FROM information_schema.TABLES "
                    f"WHERE table_schema = '{database}';")
        self.con.commit()
        res = cur.fetchall()
        return int(res[0][2])


class DBType(Enum):
    DB_MARIA = auto()
    DB_SQLITE = auto()


class DBSpecifics(ABC):
    pass


@dataclass
class MariaDBSpecifics(DBSpecifics):
    user: str
    pwd: str
    host: str
    port: int
    database: str

    @staticmethod
    def cast_from_super(spec: DBSpecifics) -> MariaDBSpecifics:
        return MariaDBSpecifics(user=getattr(spec, 'user'),
                                pwd=getattr(spec, 'pwd'),
                                host=getattr(spec, 'host'),
                                port=getattr(spec, 'port'),
                                database=getattr(spec, 'database')
                                )

    def __repr__(self):
        return f"DB: {self.database}, {self.user}@{self.host}"


@dataclass
class SQLiteDBSpecifics(DBSpecifics):
    filename: str

    @staticmethod
    def cast_from_super(spec: DBSpecifics) -> SQLiteDBSpecifics:
        return SQLiteDBSpecifics(filename=getattr(spec, 'filename'))

    def __repr__(self):
        return self.filename


@dataclass
class DBSpecifier:
    key: str
    type: DBType
    specifics: DBSpecifics


class DBInterfaceFactory:

    def __init__(self):
        pass

    @staticmethod
    def get_db(specifier: DBSpecifier) -> DBInterface:
        if specifier.type == DBType.DB_SQLITE:
            return SQLiteDBInterface(SQLiteDBSpecifics.cast_from_super(specifier.specifics))
        elif specifier.type == DBType.DB_MARIA:
            return MariaDBInterface(MariaDBSpecifics.cast_from_super(specifier.specifics))
        else:
            raise NotImplementedError


if __name__ == "__main__":
    from Utils.settings import Settings

    maria_db = MariaDBInterface(Settings().get_mariadb_specifics(''))
    print(f"get_all_data = {maria_db.get_all_data("detail_long_term")}")

    logging.basicConfig(filename=r'..\data\log.txt', )
    logging.getLogger().setLevel(logging.DEBUG)
    sqlite_db = SQLiteDBInterface(SQLiteDBSpecifics(r'..\data\test.db'))
    sqlite_db.create_table("test_table_1", ["sig_1", "sig_2", "sig_3"])
    sqlite_db.create_table("test_table_2", ["sig_4", "sig_5", "sig_6"])
    print(f"check = {sqlite_db.check_columns("test_table_2", ["sig_4", "sig_5", "sig_6"])}")
    print(f"table names = {sqlite_db.get_table_names()}")
    print(f"column names = {sqlite_db.get_column_names("test_table_2")}")
    data_item_spec = DataItemSpec({"sig_1": "unit_1", "sig_2": "unit_2"})
    sqlite_db.append_data_item("test_table_1", data_item_spec, [1.0, 2.0, 3.0])
    sqlite_db.append_data_item("test_table_1", data_item_spec, [4.0, 5.0, 6.0])
    sqlite_db.insert_data_item("test_table_1", 1, data_item_spec, [11.0, 12.0, 13.0])
    sqlite_db.modify_element("test_table_1", 1, "sig_1", 11.0)
    sqlite_db.modify_element("test_table_1", 1, "sig_2", 2.22)
    print(f"count = {sqlite_db.get_count("test_table_1")}")
    print(f"count = {sqlite_db.get_count("non_existent")}")
    print(f"get_data_items = {sqlite_db.get_data_items("test_table_1", 1, ["sig_1", "sig_2"])}")
    print(f"get_data_items = {sqlite_db.get_data_items("test_table_2", 1, ["sig_4", "sig_5"])}")
    print(f"get_all_data = {sqlite_db.get_all_data("test_table_1")}")
    print(f"size = {sqlite_db.size()}")


    maria_db = MariaDBInterface(Settings().get_mariadb_specifics(''))
    maria_db.create_table("test_table_1", ["sig_1", "sig_2", "sig_3"])
    maria_db.create_table("test_table_2", ["sig_4", "sig_5", "sig_6"])
    print(f"check = {maria_db.check_columns("test_table_2", ["sig_4", "sig_5", "sig_6"])}")
    print(f"table names = {maria_db.get_table_names()}")
    print(f"column names = {maria_db.get_column_names("test_table_2")}")
    data_item_spec = DataItemSpec({"sig_1": "unit_1", "sig_2": "unit_2"})
    maria_db.append_data_item("test_table_1", data_item_spec, [1.0, 2.0, 3.0])
    maria_db.append_data_item("test_table_1", data_item_spec, [4.0, 5.0, 6.0])
    maria_db.insert_data_item("test_table_1", 1, data_item_spec, [11.0, 12.0, 13.0])
    maria_db.modify_element("test_table_1", 1, "sig_1", 11.0)
    maria_db.modify_element("test_table_1", 1, "sig_2", 2.22)
    print(f"count = {maria_db.get_count("test_table_1")}")
    print(f"count = {maria_db.get_count("non_existent")}")
    print(f"get_data_items = {maria_db.get_data_items("test_table_1", 1, ["sig_1", "sig_2"])}")
    print(f"get_data_items = {maria_db.get_data_items("test_table_2", 1, ["sig_4", "sig_5"])}")

    print(f"get_data_items = {maria_db.get_data_items("meterstand", 1, ["timestamp", "USAGE_TARIFF_1"])}")

    print(f"get_all_data = {maria_db.get_all_data("test_table_1")}")
    print(f"size = {maria_db.size()}")
