# webhook-repo
📘 README.md – Webhook Receiver (Flask + MongoDB)
🚀 Webhook Receiver – TechStaX Developer Assessment
This repository is part of the TechStaX Developer Assessment task. It acts as a webhook receiver for GitHub events like Push, Pull Request, and Merge, and stores these events in MongoDB Atlas.

The UI fetches the latest webhook events from MongoDB every 15 seconds, and displays them in a clean and minimal format.

📦 Tech Stack
Flask (Python)

MongoDB Atlas (Cloud Database)

HTML + Bootstrap (Minimal UI)

Gunicorn (For production deployment on Render)

Render.com (Deployment platform)

🧠 Problem Statement Summary
You are required to:

Receive GitHub Webhooks for:

Push

Pull Request (opened)

Pull Request (merged) ← Bonus Points

Store events in MongoDB using a specific schema.

Build a UI that polls events every 15 seconds and displays messages like:

🔔 UI Output Format
Push:
"Travis" pushed to "staging" on 1st April 2021 - 9:30 PM UTC

Pull Request:
"Travis" submitted a pull request from "staging" to "master" on 1st April 2021 - 9:00 AM UTC

Merge:
"Travis" merged branch "dev" to "master" on 2nd April 2021 - 12:00 PM UTC

📁 MongoDB Schema
Field	Type	Description
_id	ObjectId	Default MongoDB ID
request_id	String	UUID for the webhook request
author	String	GitHub username who triggered the event
action	String	One of "PUSH", "PULL_REQUEST", "MERGE"
from_branch	String	Source branch (for PR and merge)
to_branch	String	Target branch
timestamp	String	Formatted string (e.g. 1st April 2021 - 9:30 PM UTC)
timestamp_raw	DateTime	Raw UTC datetime used for sorting

🛠️ Setup Instructions
🔑 Prerequisites
Python 3.8+

MongoDB Atlas cluster

A .env file with:

env
Copy
Edit
MONGODB_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/webhook_db
🚀 Local Development
Clone this repo:

bash
Copy
Edit
git clone https://github.com/<your-username>/webhook-repo.git
cd webhook-repo
Create a virtual environment & activate it:

bash
Copy
Edit
python -m venv venv
source venv/bin/activate     # On Windows: venv\Scripts\activate
Install dependencies:

bash
Copy
Edit
pip install -r requirements.txt
Run the Flask app:

bash
Copy
Edit
flask run
🌍 Deployment (Render)
Create a new Web Service on Render.

Use:

Build Command: pip install -r requirements.txt

Start Command: gunicorn app:app

Add your MONGODB_URI in environment variables.

🔗 API Endpoints
Method	Route	Description
GET	/	Shows latest 10 events in HTML format
GET	/events	Returns last 10 events in JSON format
POST	/webhook	GitHub Webhook receiver
GET/POST	/trigger	Manual UI for triggering test events

✅ Testing Locally (Without GitHub)
Visit:

bash
Copy
Edit
http://localhost:5000/trigger
Submit a simulated push, pull_request, or merge event manually.

📄 Related Repos
✅ action-repo — Repo to simulate GitHub Actions (must be public).

✅ webhook-repo — This repo (webhook listener + UI).

🧠 Notes
Time is converted to UTC using datetime or dateutil.parser from the GitHub webhook payload.

You can only show 10 most recent records for UI simplicity.

Frontend updates every 15 seconds using polling (no AJAX/JS framework).

👨‍💻 Author
Ranganath B
