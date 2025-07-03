from flask import Flask, request, jsonify, render_template, redirect, url_for
from pymongo import MongoClient
from datetime import datetime
import uuid
import requests
import os
import sys
from dotenv import load_dotenv
from dateutil import parser  # for ISO timestamp parsing

load_dotenv()

app = Flask(__name__)

# MongoDB Atlas connection
MONGO_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGO_URI)
db = client["webhook_db"]
collection = db["events"]

# Home route: Show last 10 events in HTML
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

# JSON endpoint for frontend polling
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

# GitHub Webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    print("Webhook triggered!", file=sys.stderr)
    event_type = request.headers.get('X-GitHub-Event')
    data = request.json
    author = data.get('sender', {}).get('login', 'Unknown')

    if event_type == 'push':
        request_id = data.get('after', str(uuid.uuid4()))
        to_branch = data.get('ref', '').split('/')[-1]
        action = 'PUSH'
        from_branch = ''
        raw_time = data.get('head_commit', {}).get('timestamp')

    elif event_type == 'pull_request':
        pr = data.get('pull_request', {})
        request_id = str(pr.get('id', uuid.uuid4()))
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

    # Format timestamp
    if raw_time:
        dt_obj = parser.isoparse(raw_time)
        formatted_time = dt_obj.strftime('%-d %B %Y - %-I:%M %p UTC')
    else:
        dt_obj = datetime.utcnow()
        formatted_time = dt_obj.strftime('%-d %B %Y - %-I:%M %p UTC')

    collection.insert_one({
        'request_id': request_id,
        'author': author,
        'action': action,
        'from_branch': from_branch,
        'to_branch': to_branch,
        'timestamp': formatted_time,
        'timestamp_raw': dt_obj  # used for accurate sorting
    })

    return jsonify({'status': 'success'}), 200

# Trigger manually (for testing)
@app.route('/trigger', methods=['GET', 'POST'])
def trigger_webhook():
    if request.method == 'POST':
        event_type = request.form['event_type']
        author = request.form['author']
        to_branch = request.form['to_branch']
        from_branch = request.form.get('from_branch', '')

        if event_type == 'push':
            data = {
                "ref": f"refs/heads/{to_branch}",
                "head_commit": {"timestamp": datetime.utcnow().isoformat()},
                "sender": {"login": author}
            }
            headers = {"X-GitHub-Event": "push"}

        elif event_type == 'pull_request':
            data = {
                "action": "opened",
                "pull_request": {
                    "id": str(uuid.uuid4()),
                    "head": {"ref": from_branch},
                    "base": {"ref": to_branch},
                    "created_at": datetime.utcnow().isoformat()
                },
                "sender": {"login": author}
            }
            headers = {"X-GitHub-Event": "pull_request"}

        elif event_type == 'merge':
            data = {
                "action": "closed",
                "pull_request": {
                    "id": str(uuid.uuid4()),
                    "head": {"ref": from_branch},
                    "base": {"ref": to_branch},
                    "merged": True,
                    "merged_at": datetime.utcnow().isoformat()
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

# Run app
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
