from flask import Flask, render_template
import pymysql
import os
from contextlib import contextmanager
from dotenv import load_dotenv
import requests

# 代理服务器配置
proxy_info = {
    "username": "psud56605-region-US",
    "password": "gdwkhht1",
    "host": "us.cliproxy.io",
    "port": "3010"
}

# 加载 .env 文件中的环境变量
load_dotenv()

app = Flask(__name__,
            template_folder="../templates",
            static_folder="../static"
            )


@app.route('/')
def home():
    return 'Hello, World!'


@app.route('/proxy')
def test_proxy_request():
    # 构建代理URL - 使用正确的格式
    # 格式应该是: http://username:password@host:port
    proxy_url = f"http://{proxy_info['username']}:{proxy_info['password']}@{proxy_info['host']}:{proxy_info['port']}"
    print(f"当前代理地址: {proxy_url}")

    # 代理IP地址
    proxy_data = {
        'http': proxy_url,
        'https': proxy_url,
    }

    # 客户端说明
    head_data = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0',
        'Connection': 'keep-alive'
    }

    try:
        response = requests.get('https://ipapi.co/json/',
                                headers=head_data, proxies=proxy_data)
        data = response.json()

        # 只返回指定信息
        result = {
            'IP地址': data.get('ip', '未知'),
            '国家': data.get('country_name', '未知'),
            '地区': data.get('region', '未知'),
            '城市': data.get('city', '未知')
        }

        return result
    except Exception as e:
        print(f"代理请求失败: {str(e)}")
        return {'错误': f"代理请求失败: {str(e)}"}


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
