from flask import Flask, render_template, jsonify, request, abort
from schema.models import Entity, create_player

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    id = request.args.get('id', '')
    return jsonify(ok=Entity(id).exists())

@app.route('/register')
def register():
    player = create_player()
    return jsonify(id=player.id)

@app.route('/admin')
def admin():
    # No security for now, lawl
    return render_template('admin.html', entities=Entity.all())

@app.route('/command')
def command():
    id = request.args.get('id', '')
    command = request.args.get('command', '')

    entity = Entity(id)
    if not entity.exists():
        abort(404)

    entity.perform(command)

    return None, 204
