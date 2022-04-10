from __future__ import annotations

import datetime
import io
import logging
import pickle
import socket
import socketserver
import struct
import traceback

import bson.json_util
import pymongo
from bson.raw_bson import RawBSONDocument

logger = logging.getLogger(__name__)


def format_exception(ei) -> str:
    """
    From logging.Formatter.formatException.

    Format and return the specified exception information as a string.

    This default implementation just uses
    traceback.print_exception()
    """
    sio = io.StringIO()
    tb = ei[2]
    traceback.print_exception(ei[0], ei[1], tb, None, sio)
    s = sio.getvalue()
    sio.close()
    if s[-1:] == "\n":
        s = s[:-1]
    return s


def log_record_to_bson_document(record: logging.LogRecord) -> RawBSONDocument:
    document = {
        "timestamp": datetime.datetime.fromtimestamp(record.created),
        "level": record.levelno,
        "levelName": record.levelname,
        "thread": record.thread,
        "threadName": record.threadName,
        "message": record.getMessage(),
        "loggerName": record.name,
        "path": record.pathname,
        "module": record.module,
        "method": record.funcName,
        "lineno": record.lineno,
    }
    if record.exc_info is not None:
        document["exception"] = {
            "message": str(record.exc_info[1]),
            "stackTrace": format_exception(record.exc_info),
        }

    return document


def document_to_json(document: RawBSONDocument) -> str:
    return bson.json_util.dumps(document)


class TftpServerRequestHandler(socketserver.BaseRequestHandler):

    server: ThreadingTCPServer
    request: socket.socket

    def handle(self) -> None:
        while True:
            # SocketHandler sends chunks of [length][data], where [length] is 4-bytes
            chunk = self.request.recv(4)
            if len(chunk) < 4:
                break
            length = struct.unpack(">L", chunk)[0]
            chunk = self.request.recv(length)
            # TODO implement JSON serialization with optional "unsafe" pickle run mode
            data = pickle.loads(chunk)
            record = logging.makeLogRecord(data)
            logger.debug("Data received from %s:%d:: %s", *self.client_address, record)
            self.server.log_db.insert_one(log_record_to_bson_document(record))


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def __init__(
        self,
        log_db: pymongo.collection.Collection,
        listen_addr: str = "0.0.0.0",
        listen_port: int = 18001,
    ) -> None:
        self.log_db = log_db
        super().__init__((listen_addr, listen_port), TftpServerRequestHandler)
        listen_addr_, listen_port_ = self.socket.getsockname()
        logger.info("Serving on %s:%d", listen_addr_, listen_port_)
