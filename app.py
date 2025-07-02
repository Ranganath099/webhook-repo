from flask import Flask, request, jsonify, render_template, redirect,url_for
from pymongo import MongoClient
from datetime import datetime
import uuid
import requests

app = Flask(__name__)

# MongoDB Atlas connection
client = MongoClient("mongodb+srv://sriranganathbesta:Ranga6300@cluster0.0uukzja.mongodb.net/")
db = client["webhook_db"]
collection = db["events"]


@app.route('/events')
def get_events():
    docs = collection.find().sort('timestamp', -1).limit(10)
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

@app.route('/')
def index():
    docs = collection.find().sort('timestamp', -1).limit(10)
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

@app.route('/webhook', methods=['POST'])
def webhook():
    event_type = request.headers.get('X-GitHub-Event')
    data = request.json
    timestamp = datetime.utcnow().strftime('%#d %B %Y - %#I:%M %p UTC')
    request_id = str(uuid.uuid4())
    author = data.get('sender', {}).get('login', 'Unknown')

    if event_type == 'push':
        to_branch = data.get('ref', '').split('/')[-1]
        action = 'PUSH'
        from_branch = ''
    elif event_type == 'pull_request':
        pr = data.get('pull_request', {})
        from_branch = pr.get('head', {}).get('ref')
        to_branch = pr.get('base', {}).get('ref')
        if data.get('action') == 'opened':
            action = 'PULL_REQUEST'
        elif data.get('action') == 'closed' and pr.get('merged'):
            action = 'MERGE'
        else:
            return jsonify({'status': 'ignored'}), 200
    else:
        return jsonify({'status': 'ignored'}), 200

    collection.insert_one({
        'request_id': request_id,
        'author': author,
        'action': action,
        'from_branch': from_branch,
        'to_branch': to_branch,
        'timestamp': timestamp
    })

    return jsonify({'status': 'success'}), 200

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
                "sender": {
                    "login": author
                }
            }
            headers = {"X-GitHub-Event": "push"}

        elif event_type == 'pull_request':
            data = {
                "action": "opened",
                "pull_request": {
                    "head": {"ref": from_branch},
                    "base": {"ref": to_branch}
                },
                "sender": {
                    "login": author
                }
            }
            headers = {"X-GitHub-Event": "pull_request"}

        elif event_type == 'merge':
            data = {
                "action": "closed",
                "pull_request": {
                    "head": {"ref": from_branch},
                    "base": {"ref": to_branch},
                    "merged": True
                },
                "sender": {
                    "login": author
                }
            }
            headers = {"X-GitHub-Event": "pull_request"}

        else:
            return "Invalid event", 400

        # Send POST to webhook endpoint
        requests.post(
            'http://127.0.0.1:5000/webhook',
            json=data,
            headers={**headers, "Content-Type": "application/json"}
        )

        # ✅ Redirect to the homepage after success
        return redirect(url_for('index'))

    return render_template('trigger.html')



if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
