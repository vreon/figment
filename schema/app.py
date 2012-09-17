from flask import Flask, render_template, jsonify, request, abort
from schema.models import redis

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# TODO: Assume entity exists for now
@app.route('/login')
def login():
    id = request.args.get('id', '')
    return jsonify(ok=True)

@app.route('/admin')
def admin():
    # No security for now, lawl
    return render_template('admin.html', entities=Entity.all())

@app.route('/command')
def command():
    id = request.args.get('id', '')
    command = request.args.get('command', '')

    redis.rpush('incoming', ' '.join((id, command)))

    return None, 204
