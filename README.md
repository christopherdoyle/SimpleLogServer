# Simple Log Server

Basic implementation of a server that responds to Python logging SocketHandler,
stores the records in MongoDB, and displays the results in a web browser.
Created for personal use during development, not production.

Records are sent to the browser with websockets so that we can send live
updates easily --- this is done by watching the MongoDB change log for inserts.
The updates are not synchronized properly and assumptions are made here.

## Requirements

* MongoDB on localhost with a replica set (single instance works fine)
* Python 3.~
* Pymongo, gevent, gevent-websocket

## Usage

```commandline
python -m simplelogserver
```

## TODO

* Show full record info on click
* Sort the records inplace in JavaScript
* Pagination --- requires changes to program structure
* Filters
