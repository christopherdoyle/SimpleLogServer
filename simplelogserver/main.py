# flake8: noqa: E402
from __future__ import annotations

from gevent import monkey

monkey.patch_all()

import datetime
import json
import logging
import os
import threading
import uuid

import pymongo
from gevent.pywsgi import WSGIServer
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler

from . import bottle
from . import logserver

ROOT = os.path.dirname(os.path.realpath(__file__))

logger = logging.getLogger(__name__)
client = pymongo.MongoClient("localhost", 27017)
database = client["simplelogs"]
collection = database["logdata"]
app = bottle.Bottle()
listeners = {}


@app.route("/")
def index():
    return bottle.template("index_template", update_timestamp=datetime.datetime.now())


@app.route(r"<filename:re:.*\.css>")
def serve_stylesheets(filename: str):
    return bottle.static_file(filename, root=os.path.join(ROOT, "static", "css"))


@app.route(r"<filename:re:.*\.js>")
def serve_javascript(filename: str):
    return bottle.static_file(filename, root=os.path.join(ROOT, "static", "js"))


@app.route("/websocket")
def handle_websocket():
    wsock = bottle.request.environ.get("wsgi.websocket")
    ws_id = uuid.uuid4()
    if not wsock:
        bottle.abort(400, "Expected WebSocket request.")

    while True:
        try:
            message = wsock.receive()
            data = json.loads(message)
            if data["type"] == "bulk":
                try:
                    nrecords = int(data["n"])
                except (TypeError, ValueError):
                    continue
                else:
                    records = (
                        collection.find()
                        .sort("timestamp", pymongo.DESCENDING)
                        .limit(nrecords)
                    )
                    # TODO move the reverse into the mongo query, or just sort it in JS
                    for record in reversed(list(records)):
                        wsock.send(
                            logserver.document_to_json(dict(type="record", data=record))
                        )
                    wsock.send(json.dumps(dict(type="state", data="end")))
            elif data["type"] == "update":
                # TODO include timestamp and only notify on records since this point
                # from_timestamp = data["timestamp"]
                listeners[ws_id] = (wsock,)
        except WebSocketError:
            break

    if ws_id in listeners:
        del listeners[ws_id]


def notify_listeners():
    change_stream = collection.watch()
    for change in change_stream:
        if change["operationType"] != "insert":
            break
        record = change["fullDocument"]
        for _, (wsock,) in listeners.items():
            wsock.send(logserver.document_to_json(dict(type="record", data=record)))


def main() -> None:
    log_server = logserver.ThreadingTCPServer(collection)
    log_server_thread = threading.Thread(target=log_server.serve_forever)
    log_server_thread.daemon = True
    log_server_thread.start()

    notify_thread = threading.Thread(target=notify_listeners)
    notify_thread.daemon = True
    notify_thread.start()

    bottle.TEMPLATE_PATH = [os.path.join(ROOT, "views")]
    server = WSGIServer(("0.0.0.0", 8080), app, handler_class=WebSocketHandler)
    server.serve_forever()
    log_server.shutdown()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
