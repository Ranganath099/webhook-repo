from flask import Flask, request, jsonify, render_template, redirect, url_for
from pymongo import MongoClient
from datetime import datetime
import uuid
import requests
import os
import sys
from dotenv import load_dotenv
from dateutil import parser  # for parsing GitHub timestamp strings

load_dotenv()

app = Flask(__name__)

# MongoDB Atlas connection
MONGO_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGO_URI)
db = client["webhook_db"]
collection = db["events"]

@app.route('/')
def index():
    docs = collection.find().sort('timestamp_raw', -1).limit(10)
    events = []
    for doc in docs:
        if doc['action'] == 'PUSH':
            msg = f"{doc['author']} pushed to {doc['to_branch']} on {doc['timestamp']}"
        elif doc['action'] == 'PULL_REQUEST':
            msg = f"{doc['author']} submitted a pull request from {doc['from_branch']} to {doc['to_branch']} on {doc['timestamp']}"
        elif doc['action'] == 'MERGE':
            msg = f"{doc['author']} merged branch {doc['from_branch']} to {doc['to_branch']} on {doc['timestamp']}"
        else:
            continue
        events.append(msg)
    return render_template('index.html', events=events)

@app.route('/events')
def get_events():
    docs = collection.find().sort('timestamp_raw', -1).limit(10)
    events = []
    for doc in docs:
        if doc['action'] == 'PUSH':
            msg = f"{doc['author']} pushed to {doc['to_branch']} on {doc['timestamp']}"
        elif doc['action'] == 'PULL_REQUEST':
            msg = f"{doc['author']} submitted a pull request from {doc['from_branch']} to {doc['to_branch']} on {doc['timestamp']}"
        elif doc['action'] == 'MERGE':
            msg = f"{doc['author']} merged branch {doc['from_branch']} to {doc['to_branch']} on {doc['timestamp']}"
        else:
            continue
        events.append(msg)
    return jsonify(events)

# Webhook listener
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    print("Webhook triggered!", file=sys.stderr)

    if request.method == 'GET':
        return "Webhook endpoint is up", 200

    try:
        data = request.get_json(force=True)
    except Exception as e:
        print("Invalid JSON:", e, file=sys.stderr)
        return jsonify({'error': 'Invalid JSON'}), 400

    event_type = request.headers.get('X-GitHub-Event')
    author = data.get('sender', {}).get('login', 'Unknown')
    action = None
    from_branch = ''
    to_branch = ''
    request_id = str(uuid.uuid4())
    raw_time = None

    if event_type == 'push':
        action = 'PUSH'
        to_branch = data.get('ref', '').split('/')[-1]
        raw_time = data.get('head_commit', {}).get('timestamp')

    elif event_type == 'pull_request':
        pr = data.get('pull_request', {})
        from_branch = pr.get('head', {}).get('ref')
        to_branch = pr.get('base', {}).get('ref')

        if data.get('action') == 'opened':
            action = 'PULL_REQUEST'
            raw_time = pr.get('created_at')
        elif data.get('action') == 'closed' and pr.get('merged'):
            action = 'MERGE'
            raw_time = pr.get('merged_at')
        else:
            return jsonify({'status': 'ignored'}), 200
    else:
        return jsonify({'status': 'ignored'}), 200

    # Parse timestamp
    try:
        dt_obj = parser.isoparse(raw_time)
    except Exception:
        dt_obj = datetime.utcnow()

    timestamp = dt_obj.strftime('%-d %B %Y - %-I:%M %p UTC')

    collection.insert_one({
        'request_id': request_id,
        'author': author,
        'action': action,
        'from_branch': from_branch,
        'to_branch': to_branch,
        'timestamp': timestamp,
        'timestamp_raw': dt_obj
    })

    return jsonify({'status': 'success'}), 200

# Manual testing helper
@app.route('/trigger', methods=['GET', 'POST'])
def trigger_webhook():
    if request.method == 'POST':
        event_type = request.form['event_type']
        author = request.form['author']
        to_branch = request.form['to_branch']
        from_branch = request.form.get('from_branch', '')
        now = datetime.utcnow().isoformat()
        unique_id = str(uuid.uuid4())

        if event_type == 'push':
            data = {
                "ref": f"refs/heads/{to_branch}",
                "head_commit": {"timestamp": now},
                "sender": {"login": author}
            }
            headers = {"X-GitHub-Event": "push"}

        elif event_type == 'pull_request':
            data = {
                "action": "opened",
                "pull_request": {
                    "id": unique_id,
                    "head": {"ref": from_branch},
                    "base": {"ref": to_branch},
                    "created_at": now
                },
                "sender": {"login": author}
            }
            headers = {"X-GitHub-Event": "pull_request"}

        elif event_type == 'merge':
            data = {
                "action": "closed",
                "pull_request": {
                    "id": unique_id,
                    "head": {"ref": from_branch},
                    "base": {"ref": to_branch},
                    "merged": True,
                    "merged_at": now
                },
                "sender": {"login": author}
            }
            headers = {"X-GitHub-Event": "pull_request"}

        else:
            return "Invalid event type", 400

        requests.post(
            'https://webhook-repo-nmzl.onrender.com/webhook',
            json=data,
            headers={**headers, "Content-Type": "application/json"}
        )

        return redirect(url_for('index'))

    return render_template('trigger.html')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
