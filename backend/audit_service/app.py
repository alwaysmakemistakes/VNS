from flask import Flask, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics
from models import get_db_connection, create_audit_table
from datetime import datetime
import requests
import json


app = Flask(__name__)
metrics = PrometheusMetrics(app)
AUDIT_SERVICE_URL = "http://audit_service:5000/audit/event"

create_audit_table()

@app.route("/audit/event", methods=["POST"])
def create_event():
    data = request.get_json()

    entity_type = data["entity_type"]
    entity_id = data["entity_id"]
    event_type = data["event_type"]
    payload = data["payload"]

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO audit_events (timestamp, entity_type, entity_id, event_type, payload)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (datetime.utcnow(), entity_type, entity_id, event_type, json.dumps(payload))
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Event recorded"}), 201

@app.route("/audit/events", methods=["GET"])
def get_events():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM audit_events ORDER BY timestamp DESC LIMIT 50;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    events = []
    for row in rows:
        events.append({
            "id": row[0],
            "timestamp": row[1].isoformat(),
            "entity_type": row[2],
            "entity_id": row[3],
            "event_type": row[4],
            "payload": row[5],
        })

    return jsonify(events)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
