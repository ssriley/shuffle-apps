
import datetime
from logging import exception
import json
import traceback
import pyodbc

from walkoff_app_sdk.app_base import AppBase


class SS_MS_SQL(AppBase):
    """
    An example of a Walkoff App.
    Inherit from the AppBase class to have Redis, logging, and console
    logging set up behind the scenes.
    """

    __version__ = "1.0.0"
    app_name = (
        "SS - Microsoft SQL"  # this needs to match "name" in api.yaml for WALKOFF to work
    )

    def __init__(self, redis, logger, console_logger=None):
        """
        Each app should have this __init__ to set up Redis and logging.
        :param redis:
        :param logger:
        :param console_logger:
        """
        super().__init__(redis, logger, console_logger)
    
    def connection(self, sql_server, database, username=None, password=None):
        conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};'
                              'SERVER=' + sql_server + ';'
                              'DATABASE=' + database + ';'
                              'UID=' + username + ';'
                              'PWD=' + password + ';'
                              'TrustServerCertificate=YES;'
                              )
        return conn
                                                    

    def run_sql_query(self, sql_server, database, username, password, query=None):
        try:
            conn = self.connection(sql_server,database,username,password)
            cursor = conn.cursor()
            cursor.execute(query)
            row_headers = [x[0] for x in cursor.description]
            json_data = []
            for result in cursor.fetchall():
                json_data.append(dict(zip(row_headers, result)))
            result = cursor
            cursor.close()
            conn.close()
            return json.dumps(json_data, indent=4)
        except Exception:
            my_error = {"result": traceback.format_exc()}
            return my_error

    def insert_records_sql(self, sql_server, database, username, password, table_name=None, columns=None, values=None):
        
        try:
            conn = self.connection(sql_server,database,username,password)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO " + table_name + " " + columns + " " + "VALUES " + values)
        except Exception:
            my_error = {"result": traceback.format_exc()}
            conn.rollback()
            return my_error
        else:
            cursor.close()
            conn.commit()
            conn.close()
            return {"result": "finished"}

    def delete_records_sql(self, sql_server, database, username, password, table_name=None, where_clause=None):
        try:
            conn = self.connection(sql_server,database,username,password)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM " + table_name + " WHERE " + where_clause)
        except Exception:
            my_error = {"result": traceback.format_exc()}
            conn.rollback()
            return my_error
        else:
            cursor.close()
            conn.commit()
            conn.close()
            return {"result": "finished"}

    def update_records_sql(self, sql_server, database, username, password, table_name=None, column_name=None, new_value=None, where_clause=None):
        try:
            conn = self.connection(sql_server,database,username,password)
            cursor = conn.cursor()
            cursor.execute("UPDATE " + table_name + " SET " + column_name + " = " + new_value + " WHERE " + where_clause)
        except Exception:
            my_error = {"result": traceback.format_exc()}
            conn.rollback()
            return my_error
        else:
            cursor.close()
            conn.commit()
            conn.close()
            return {"result": "finished"}

    def raw_modify_records_query(self, sql_server, database, username, password, query=None):
        try:
            conn = self.connection(sql_server,database,username,password)
            cursor = conn.cursor()
            cursor.execute(query)
            cursor.close()
            conn.commit()
            conn.close()
            return {"result": "finished"}
        except Exception:
            my_error = {"result": traceback.format_exc()}
            return my_error

if __name__ == "__main__":
    SS_MS_SQL.run()
