#!/usr/bin/env python

from flask import Flask, Response, render_template, jsonify, request, abort
from figment import Zone, Entity
from example.aspects import *
import random
import json

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

    zone = Zone.from_config('default')
    zone.enqueue_command(id, command)

    return None, 204

@app.route('/register')
def register():
    zone = Zone.from_config('default')

    player = Entity(
        'Player' + str(random.randint(1000, 9999)),
        'A fellow player.',
        [Positioned(is_container=True, container_id='startroom'), Emotes()]
    )

    zone.enqueue_import(player)

    return jsonify(id=player.id)

def _listen(zone, id):
    print "Subscribing to %s" % id
    for message in zone.listen(id):
        yield 'data: %s\n\n' % json.dumps({"type": "message", "content": message})

@app.route('/listen/<id>')
def listen(id):
    zone = Zone.from_config('default')
    return Response(_listen(zone, id), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
