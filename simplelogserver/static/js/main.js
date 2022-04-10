"use strict";


class Record {
    constructor({
        timestamp,
        levelName,
        message,
        ...rest
    }={}) {
        this.timestamp = timestamp;
        this.level = levelName;
        this.message = message;
        this.data = rest;
    }
}


class RecordTable {
    constructor(renderCallback) {
        this.renderCallback = renderCallback;
        this.rendered = false;
        this.lengthLimit = 30;
        this.length = 0;

        this.columns = ["Level", "Message", "Timestamp"];
        this.table = document.createElement("table");
        this.table.classList.add("records");
        this.thead = document.createElement("thead");
        this.tbody = document.createElement("tbody");

        const colgroup = document.createElement("colgroup");
        const tr = document.createElement("tr");
        this.columns.forEach(name => {
            const col = document.createElement("col");
            col.setAttribute("class", name);
            colgroup.append(col);

            const th = document.createElement("th");
            th.innerText = name;
            tr.append(th);
        });

        this.thead.append(tr);
        this.table.append(colgroup);
        this.table.append(this.thead);
        this.table.append(this.tbody);
    }

    addRecord(record) {
        const el = document.createElement("tr");
        el.classList.add("record");
        el.classList.add(`record__${record.level.toLowerCase()}`);
        el.innerHTML = `
<td>${record.level}</td>
<td>${record.message}</td>
<td>${record.timestamp}</td>`;
        this.length += 1;
        if (this.length > this.lengthLimit) {
            this.removeLastRecord();
        }
        this.tbody.prepend(el);
        this.render();
    }

    removeLastRecord() {
        this.tbody.lastChild.remove();
        this.length -= 1;
    }

    render() {
        if (this.rendered === false) {
            this.renderCallback(this.table);
            this.rendered = true;
        }
    }
}


document.addEventListener("DOMContentLoaded", () => {
    const socket = new WebSocket("ws://localhost:8080/websocket"),
        recordTable = new RecordTable(
            (el) => {
                document.querySelector("#main").append(el);
            }
        );

    socket.onmessage = (event) => {
        const message = JSON.parse(event.data);

        if (message.type === "record") {
            const data = message.data;
            data["timestamp"] = data["timestamp"]["$date"];
            recordTable.addRecord(new Record(data));
        } else if (message.type === "state") {
            const data = message.data;
            if (data === "end") {
                /* client has received all the initial data,
                now we ask for updates instead */
                socket.send(JSON.stringify({type: "update"}));
            }
        }
    }

    socket.onopen = () => {
        socket.send(JSON.stringify({type: "bulk", n: recordTable.lengthLimit}));
    }
}, false);
