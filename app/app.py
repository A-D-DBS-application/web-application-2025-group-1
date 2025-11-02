from flask import Flask

app = Flask(__name__)

@app.route('/')
def html():
    return '<h1>stoel</h1>'

@app.route('/s')
def index():
    return 'stoel'

@app.route('/multiply/<int:n1>/<int:n2>')
def multiply(n1, n2):
    return f'{n1} * {n2} = {n1*n2}'

if __name__ == '__main__':
    app.run(debug=True)