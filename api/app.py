from flask import Flask, render_template
import pymysql
import os
from contextlib import contextmanager
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

app = Flask(__name__, 
    template_folder="../templates", 
    static_folder="../static"
)

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/json')
def test_json():
    return {'name': 'vercel'}

@app.route('/html-str')
def html_str():
    return '<html><body><h1>Hello, World!</h1></body></html>'

@app.route('/html-template')
def html_template():
    return render_template('index.html', title='Welcome', message='Hello, World!')


class DatabaseConnection:
    def __init__(self, charset='utf8mb4'):
        self.host = os.getenv('DB_HOST')
        self.user = os.getenv('DB_USER')
        self.password = os.getenv('DB_PWD')
        self.database = os.getenv('DB_NAME')
        self.charset = charset

    @contextmanager
    def connect(self):
        connection = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            charset=self.charset
        )
        try:
            yield connection
        finally:
            connection.close()

    def execute_query(self, query, params=None):
        with self.connect() as connection:
            with connection.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchall()

    def execute_non_query(self, query, params=None):
        with self.connect() as connection:
            with connection.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                connection.commit()

@app.route('/mysql-query')
def mysql_query():
    db = DatabaseConnection()
    result = db.execute_query("SELECT * FROM users")
    return list(result)
