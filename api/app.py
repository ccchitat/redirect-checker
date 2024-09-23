from flask import Flask, render_template
import pymysql
from contextlib import contextmanager

app = Flask(__name__, template_folder="../templates", static_folder="../static")

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/json')
def test_json():
    return {'name': 'vercel'}

@app.route('/html-str')
def html1():
    return '<html><body><h1>Hello, World!</h1></body></html>'

@app.route('/html-template')
def html2():
    return render_template('index.html', title='Welcome', message='Hello, World!')


db_config = {
    'host': 'mysql.sqlpub.com',
    'user': 'test_vercel',
    'password': 'zULLth3A5Q46EthN',
    'database': 'test_vercel'
}

class DatabaseConnection:
    def __init__(self, host, user, password, database, charset='utf8mb4'):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
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

@app.route('/mysql-init')
def mysql_init():
    db = DatabaseConnection(**db_config)
    db.execute_non_query("""
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    age INT NOT NULL,
    gender ENUM('male', 'female') NOT NULL
);
""")
    return "初始化 users 表成功"

@app.route('/mysql-query')
def mysql_query():
    db = DatabaseConnection(**db_config)
    result = db.execute_query("SELECT * FROM users")
    return list(result)


@app.route('/mysql-insert')
def mysql_insert():
    db = DatabaseConnection(**db_config)
    db.execute_non_query("INSERT INTO users (username, age, gender) VALUES ('John Doe', 30, 'male')")
    return "新增成功"