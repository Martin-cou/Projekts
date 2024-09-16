from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
import urllib.parse as urlparse
import json
import urllib.parse
import sqlite3

def db_init():
    connection = sqlite3.connect('user.db')
    cur = connection.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name Text NOT NULL,
            address Text,
            salary FLOAT,
            age INTEGER NOT NULL
            )''')
    connection.commit()
    return connection

class WebTasks(BaseHTTPRequestHandler):
    db_connection = db_init()
    def do_GET(self):
        if self.path.startswith('/users/'):
            users_path = urlparse.urlparse(self.path)
            query_users = urlparse.parse_qs(users_path.query)

            user_id = query_users.get('id', [None])[0]
            name = query_users.get('name', [None])[0]

            if user_id:
                result = self.find_by_id(user_id)
            if name:
                result = self.find_by_name(name)
                self.send_response(200)
            else:
                result = {"status": "error", "reason": "id or name is needed"}
                self.send_response(400)

            # send headers
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            # printing result
            self.wfile.write(json.dumps(result, indent=4).encode('utf-8'))

        else:
            # parse parameters from path
            path = urlparse.urlparse(self.path)
            query = urlparse.parse_qs(path.query)

            # parse variables from parameters
            a = query.get('a', [None])[0]
            b = query.get('b', [None])[0]
            op = query.get('op', [None])[0]

            # declaration of result variable
            full_result = {}

            try:
                # change type of variables
                a = float(a)
                b = float(b)
                # Call method for operations and time
                full_result = self.do_operation(a, b, op)
                time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # result
                full_result = {
                    "status": "ok",
                    "result": full_result,
                    "time": time
                }
                # http response code 200 that all is ok
                self.send_response(200)
            except ValueError:
                full_result = {
                    "status": "error",
                    "reason": "a not found in query string"
                }
                # http response code 200 that there is an error
                self.send_response(400)

            # send headers
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            # printing result
            self.wfile.write(json.dumps(full_result, indent=4).encode('utf-8'))

    def do_POST(self):
        if self.path == '/users/':

            length = int(self.headers['Content-Length'])
            data = self.rfile.read(length)    #read data
            data = json.loads(data)  #convert json

            # get data
            name = data.get('name')
            address = data.get('address')
            age = data.get('age')
            salary = data.get('salary')

            try:
                result = self.save_user(name, address, age, salary)
                # Send success response
                self.send_response(201)  # HTTP 201 Created
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.wfile.write(json.dumps({"status": "Success", "result": result}, indent=4).encode('utf-8'))
                self.wfile.write(json.dumps({"time" : time}, indent=4).encode('utf-8'))

            except Exception as e:
                # Handle user already exists error
                self.send_response(400)  # HTTP 400 Bad Request
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}, indent=4).encode('utf-8'))

            #self.save_user(name, address, age, salary)


    # method for operation tasks
    def do_operation(self, a, b, op):

        if op == '%2b':
            decoded_op = urllib.parse.unquote(op)
            op = decoded_op

        if op == '+':
            return a + b
        if op == '*':
            return a * b
        if op == '-':
            return a - b
        if op == '/':
            if b == 0:
                raise ValueError("Division by zero")
            else:
                return a / b

        else:
            raise ValueError(f"Unsupported operation: {op}")

    # method for save user to DB
    def save_user(self, name, address, age, salary):
        # DB connection
        cursor = self.db_connection.cursor()

        # checking if user is existing
        cursor.execute('''
                SELECT id FROM user WHERE name = ?
            ''', (name,))

        existing_user = cursor.fetchone()

        if existing_user:
            raise Exception(f"User with name '{name}' already exists.")

        cursor.execute('''
            INSERT INTO user (name, address, age, salary)
            VALUES (?, ?, ?, ?)
        ''',(name, address, age, salary))

        id_user = cursor.lastrowid

        self.db_connection.commit()

        return {
            "id": id_user,
            "name": name,
            "address": address,
            "age": age,
            "salary": salary
        }

    # method for DB search by id
    def find_by_id(self, user_id):
        cursor = self.db_connection.cursor()

        query = 'SELECT id, name, address, age, salary FROM user WHERE name = ?'
        cursor.execute(query, (user_id,))

        result = cursor.fetchone()
        if result:
            return {
            "id": result[0],
            "name": result[1],
            "address": result[2],
            "age": result[3],
            "salary": result[4]
        }
        else :
            return {"status": "error", "reason": "User not found",}

    # method for DB search by name
    def find_by_name (self, name):
        cursor = self.db_connection.cursor()

        query = 'SELECT id, name, address, age, salary FROM user WHERE name = ?'
        cursor.execute(query, (name,))

        result = cursor.fetchone()
        if result:
            return {
            "id": result[0],
            "name": result[1],
            "address": result[2],
            "age": result[3],
            "salary": result[4]
        }
        else :
            return {"status": "error", "reason": "User not found", "user": name}

# actual server run
def run(server_class=HTTPServer, handler=WebTasks, port=8000):
    server_add = ('', port)
    httpd = server_class(server_add, handler)
    print("connecting")

    httpd.serve_forever()

run()