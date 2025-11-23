import re
import time
import sqlite3
import threading

identifier_pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

class NKDBSqlite3:
    def __init__(self, database="./db.sqlite3", timeout=5.0, return_dicts=False, journal_mode="WAL", synchronous="NORMAL"):
        self.database = database
        self.timeout = timeout
        self.return_dicts = return_dicts
        self.verbose_query_output = False
        self.lock = threading.RLock()
        self.connection_arguments = {"timeout": float(self.timeout), "check_same_thread": False}
        self._connect()
        self.execute_pragma("foreign_keys = ON", commit=False)
        if journal_mode:
            self.execute_pragma(f"journal_mode = {journal_mode}", commit=False)
        if synchronous:
            self.execute_pragma(f"synchronous = {synchronous}", commit=False)

    def _connect(self):
        self.connection = sqlite3.connect(self.database, **self.connection_arguments)
        if self.return_dicts:
            self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    def _ensure_open(self):
        if getattr(self, "connection", None) is None:
            self._connect()

    def _quote_identifier(self, identifier):
        if not isinstance(identifier, str) or not identifier_pattern.match(identifier):
            raise ValueError("invalid identifier")
        return f'"{identifier}"'

    def execute_pragma(self, pragma_statement, commit=False):
        with self.lock:
            self._ensure_open()
            query = f"PRAGMA {pragma_statement};"
            if self.verbose_query_output:
                print(f"* [NKDBSqlite3] {query}")
            self.cursor.execute(query)
            if commit:
                self.connection.commit()
            return self.cursor.fetchall()

    def table_exists(self, table_name):
        with self.lock:
            self._ensure_open()
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?;"
            if self.verbose_query_output:
                print(f"* [NKDBSqlite3] {query} params=({table_name!r},)")
            self.cursor.execute(query, (table_name,))
            return self.cursor.fetchone() is not None

    def table_create(self, table_name, column_definitions, if_not_exists=True):
        quoted_table = self._quote_identifier(table_name)
        formatted_columns = []
        for key, value in column_definitions.items():
            column = self._quote_identifier(key) + " " + str(value)
            formatted_columns.append(column)
        condition = "IF NOT EXISTS " if if_not_exists else ""
        query = f"CREATE TABLE {condition}{quoted_table} ({', '.join(formatted_columns)});"
        self.execute(query, (), commit=True)

    def table_drop(self, table_name, if_exists=True):
        if not self.table_exists(table_name):
            return
        quoted_table = self._quote_identifier(table_name)
        condition = "IF EXISTS " if if_exists else ""
        query = f"DROP TABLE {condition}{quoted_table};"
        self.execute(query, (), commit=True)

    def table_list(self):
        with self.lock:
            self._ensure_open()
            query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
            if self.verbose_query_output:
                print(f"* [NKDBSqlite3] {query}")
            self.cursor.execute(query)
            return [row[0] for row in self.cursor.fetchall()]

    def table_columns(self, table_name):
        with self.lock:
            self._ensure_open()
            query = f"PRAGMA table_info({self._quote_identifier(table_name)});"
            if self.verbose_query_output:
                print(f"* [NKDBSqlite3] {query}")
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            return {
                row[1]: {
                    "type": row[2],
                    "notnull": bool(row[3]),
                    "default": row[4],
                    "primary_key": bool(row[5])
                }
                for row in rows
            }

    def select(self, table_name, columns="*", where=None, params=None, order_by=None, limit=None):
        with self.lock:
            self._ensure_open()
            if isinstance(columns, (list, tuple)):
                column_string = ", ".join(
                    [self._quote_identifier(c) if identifier_pattern.match(c) else c for c in columns]
                )
            else:
                column_string = columns
            query = f"SELECT {column_string} FROM {self._quote_identifier(table_name)}"
            if where:
                query += f" WHERE {where}"
            if order_by:
                query += f" ORDER BY {order_by}"
            if limit:
                query += f" LIMIT {int(limit)}"
            query += ";"
            if self.verbose_query_output:
                print(f"* [NKDBSqlite3] {query}")
            self.cursor.execute(query, params or ())
            rows = self.cursor.fetchall()
            if self.return_dicts:
                return [dict(r) for r in rows]
            return rows

    def fetchone(self):
        with self.lock:
            self._ensure_open()
            row = self.cursor.fetchone()
            if self.return_dicts and row is not None:
                return dict(row)
            return row

    def fetchall(self):
        with self.lock:
            self._ensure_open()
            rows = self.cursor.fetchall()
            if self.return_dicts:
                return [dict(r) for r in rows]
            return rows

    def insert(self, table_name, data, commit=True):
        with self.lock:
            self._ensure_open()
            keys = list(data.keys())
            placeholders = ", ".join(["?"] * len(keys))
            quoted_keys = ", ".join(self._quote_identifier(k) for k in keys)
            values = tuple(data[k] for k in keys)
            query = f"INSERT INTO {self._quote_identifier(table_name)} ({quoted_keys}) VALUES ({placeholders});"
            self.execute(query, values, commit=commit)
            return self.cursor.lastrowid

    def update(self, table_name, updates, where=None, where_params=None, commit=True):
        with self.lock:
            self._ensure_open()
            set_clause = ", ".join([f"{self._quote_identifier(k)} = ?" for k in updates.keys()])
            update_values = tuple(updates.values())
            query = f"UPDATE {self._quote_identifier(table_name)} SET {set_clause}"
            if where:
                query += f" WHERE {where}"
                params = update_values + (where_params or ())
            else:
                params = update_values
            query += ";"
            self.execute(query, params, commit=commit)
            return self.cursor.rowcount

    def delete(self, table_name, where=None, params=None, commit=True):
        with self.lock:
            self._ensure_open()
            query = f"DELETE FROM {self._quote_identifier(table_name)}"
            if where:
                query += f" WHERE {where}"
            query += ";"
            self.execute(query, params or (), commit=commit)
            return self.cursor.rowcount

    def executemany(self, query, sequence_of_parameters, commit=True):
        with self.lock:
            self._ensure_open()
            if self.verbose_query_output:
                print(f"* [NKDBSqlite3] executemany {query} (n={len(sequence_of_parameters)})")
            self.cursor.executemany(query, sequence_of_parameters)
            if commit:
                self.connection.commit()
            return self.cursor

    def execute(self, query, parameters=(), commit=False):
        with self.lock:
            self._ensure_open()
            if self.verbose_query_output:
                print(f"* [NKDBSqlite3] {query}")
            start_time = time.time()
            result = None
            try:
                result = self.cursor.execute(query, parameters) if parameters else self.cursor.execute(query)
            finally:
                duration = time.time() - start_time
            if commit:
                self.connection.commit()
            return result

    def close(self):
        with self.lock:
            if getattr(self, "cursor", None):
                try:
                    self.cursor.close()
                except Exception:
                    pass
                self.cursor = None
            if getattr(self, "connection", None):
                try:
                    self.connection.close()
                except Exception:
                    pass
                self.connection = None

    def __enter__(self):
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc, traceback):
        try:
            if exc_type is None:
                self.connection.commit()
        finally:
            self.close()
