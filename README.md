## 启动项目

使用 flask 方式启动

```
$ flask --app=api/app run
  * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

## 在线演示

访问地址：https://vercel-python-flask-demo.vercel.app/

- 返回 json 数据。https://vercel-python-flask-demo.vercel.app/json

``` python
@app.route('/json')
def test_json():
    return {'name': 'vercel'}
```

- 返回 html 字符串。https://vercel-python-flask-demo.vercel.app/html-str

``` python
@app.route('/html-str')
def html1():
    return '<html><body><h1>Hello, World!</h1></body></html>'
```

- 返回 html 模板。https://vercel-python-flask-demo.vercel.app/html-template

``` python
@app.route('/html-template')
def html2():
    return render_template('index.html', title='Welcome', message='Hello, World!')
```

- 查询 mysql 数据库并返回查询结果。https://vercel-python-flask-demo.vercel.app/mysql-query

## 说明

1. api 目录

vercel 部署 python flask 项目，必须在根目录下创建 api 目录 (目录名必须是 api，这样 vercel 才会识别为 Functions)，flask 的入口文件放在 api 目录下面，flask 文件可以随意取，比如 index.py, app.py 都可以；

2. 如果使用了 Flask 的 html template 功能，需要手动设置 templates 路径：

```
# 目录结构
|-- vercel-python-flask-demo
  |-- api
    |-- app.py    # flask 入口文件
  |-- static
    |-- css
      |-- style.css
  |-- templates
    |-- index.html
```

在 api/app.py 中设置 templates 路径:

``` python
from flask import Flask, render_template

# 根据上面的目录结构，设置 template 路径为 ../templates
app = Flask(__name__, template_folder="../templates", static_folder="../static")

# ...
```

3. requirements.txt 文件

项目中使用到的 python 依赖需要记录在这里面，这样部署之后 vercel 会下载相关依赖。

4. vercel.json 文件

告诉 vercel 入口文件在哪里。

以本项目为例，flask 入口文件为 /api/app.py，json 中就是这个地址。

如果你的 flask 入口文件是 /api/index.py，那么你的 json 里就是 '/api/index'

``` json
{
    "rewrites": [
      { "source": "/(.*)", "destination": "/api/app" }
    ]
}
```