# Placement Portal
Campus recruitment web application built with Flask, SQLite, HTML and CSS.

## Run locally
Open this folder in VS Code. Run `python -m pip install -r requirements.txt`, then `python app.py`. Open http://127.0.0.1:5000 and register a student account.

## Create a placement officer account
In a separate terminal in the same folder, run `python -m flask --app app:create_app create-admin`. Enter an email and a password of at least eight characters. Log in as that account to post opportunities and update application status. Register a separate student account to apply. CGPA and deadlines are checked on the server; duplicate applications are prevented.

## Testing
Run `python -m pytest -q`. GitHub Actions runs the tests on pushes and pull requests. The Dockerfile is for local demonstration, not a hardened production deployment.

## GitHub
Create an empty repository and run `git init`, `git add .`, `git commit -m "Initial commit"`, `git branch -M main`, `git remote add origin YOUR_REPOSITORY_URL`, `git push -u origin main`. Do not upload local databases or secrets. For persistent sessions set SECRET_KEY as an environment variable. The example environment file is informational; it is not automatically loaded.

## Limitations
Student CGPA is self-reported; institutional verification, resume uploads, interview scheduling and email notifications are future enhancements.
