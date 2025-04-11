from flask import Flask, render_template, request
import pymysql
import os
from contextlib import contextmanager
from dotenv import load_dotenv
import requests
from urllib.parse import urlparse, urljoin
from .redirect_checker import RedirectChecker  # 导入RedirectChecker类而不是check_url函数

# 加载 .env 文件中的环境变量
load_dotenv()

app = Flask(__name__,
            template_folder="../templates",
            static_folder="../static"
            )


@app.route('/')
def home():
    return 'Hello, World!'


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def create_tracking_template(url):
    if not is_valid_url(url):
        return ""
    try:
        # 分割 URL 的基础部分和查询参数
        base_url = url.split('?')[0]
        query_part = url[len(base_url):] if '?' in url else ''

        # 返回 {lpurl} 加上查询参数
        return "{lpurl}" + query_part
    except:
        return ""


@app.route('/proxy', methods=['POST'])
def test_proxy_request():
    try:
        # 获取请求体数据
        request_data = request.get_json()
        if not request_data or 'proxy' not in request_data or 'link' not in request_data:
            return {'error': '请求体必须包含 proxy 和 link 字段'}, 400

        proxy_info = request_data['proxy']
        target_link = request_data['link']
        # 获取可选的 referer 参数，默认为空字符串
        referer = request_data.get('referer', '')

        # 验证代理信息是否完整
        required_fields = ['username', 'password', 'host', 'port']
        if not all(field in proxy_info for field in required_fields):
            return {'error': '代理信息不完整，需要 username、password、host 和 port 字段'}, 400

        # 构建代理URL
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
            'Connection': 'keep-alive',
            'Referer': referer
        }

        # 先获取IP信息
        ip_response = requests.get('https://ipapi.co/json/',
                                 headers=head_data, proxies=proxy_data)
        ip_data = ip_response.json()

        # 使用RedirectChecker检查目标链接
        checker = RedirectChecker()
        redirect_result = checker.check_url(
            url=target_link,
            headers=head_data,
            proxies=proxy_data,
            timeout=5,
            max_hops=10
        )

        print("重定向路径:", " -> ".join(redirect_result['redirect_path']))
        print("最终URL:", redirect_result['target_url'])

        # 获取重定向路径和最终URL
        redirect_path = redirect_result['redirect_path']
        target_url = redirect_result['target_url']

        # 返回结果
        result = {
            'ip_info': {
                'ip': ip_data.get('ip', '未知'),
                'country': ip_data.get('country_name', '未知'),
                'region': ip_data.get('region', '未知'),
                'city': ip_data.get('city', '未知')
            },
            'code': 200,  # 由于我们已经在RedirectChecker中处理了状态码，这里直接返回200
            'redirect_path': redirect_path,
            'target_url': target_url,
            'tracking_template': create_tracking_template(target_url),
            'version': '1.0.0'
        }

        return result
    except Exception as e:
        print(f"请求失败: {str(e)}")
        return {'error': f"请求失败: {str(e)}"}, 500


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
