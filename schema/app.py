from flask import Flask, render_template, jsonify, request, abort
from schema.models import redis

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# TODO: Implement real authentication
@app.route('/login')
def login():
    id = request.args.get('id', '')
    return jsonify(ok=True)

# TODO: Target the correct zone
@app.route('/command')
def command():
    id = request.args.get('id', '')
    command = request.args.get('command', '')

    redis.rpush('zone:default:incoming', ' '.join((id, command)))

    return None, 204
