
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

    def insert_sql(self, sql_server, database, username, password, table_name=None, columns=None, values=None, column_number_variable=None):
        # try:
        #     value_list = values.replace("'", '"', -1)
        #     value_list = value_list.split(",")
        #     value_list = json.loads(value_list)
        # except Exception:
        #     print("[WARNING] Error parsing string to array. Continuing anyway.")

        # # Workaround D:
        # if not isinstance(value_list, list):
        #     return {
        #         "success": False,
        #         "reason": "Error: input isnt a list. Remove # to use this action.", 
        #         "valid": [],
        #         "invalid": [],
        #     }
        
        try:
            conn = self.connection(sql_server,database,username,password)
            conn.autocommit=False
            cursor = conn.cursor()
            value_list = values.replace("'", '"', -1)
            value_list = [values]
            cursor.execute("INSERT INTO " + table_name + " " + columns + " " + "VALUES " + column_number_variable, value_list)
        except Exception:
            my_error = {"result": traceback.format_exc()}
            conn.rollback()
            return my_error
        else:
            count = cursor.rowcount()
            cursor.close()
            conn.commit()
            conn.close()
            return {"result": str(count)}
        finally:
            conn.autocommit=True

    def delete_sql(self, sql_server, database, username, password, query=None):
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

    def update_sql(self, sql_server, database, username, password, query=None):
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