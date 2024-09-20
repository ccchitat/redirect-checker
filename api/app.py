from flask import Flask, render_template

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