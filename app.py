import os, sqlite3, secrets
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash

def create_app(config=None):
    app=Flask(__name__)
    app.config.update(SECRET_KEY=os.getenv('SECRET_KEY') or secrets.token_hex(32), DATABASE=os.getenv('DATABASE','placement.db'))
    if config: app.config.update(config)
    def db():
        c=sqlite3.connect(app.config['DATABASE']); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON'); return c
    with db() as c: c.executescript(Path(__file__).with_name('database').joinpath('schema.sql').read_text())
    @app.before_request
    def csrf():
        if 'csrf' not in session: session['csrf']=secrets.token_hex(24)
        if request.method=='POST' and request.form.get('csrf')!=session['csrf']: abort(400)
    @app.route('/register',methods=['GET','POST'])
    def register():
        if request.method=='POST':
            try:
                cgpa=float(request.form['cgpa']); name=request.form['name'].strip(); email=request.form['email'].strip().lower(); password=request.form['password']
                if not 0<=cgpa<=10 or not name or '@' not in email or len(password)<8: raise ValueError()
                with db() as c: c.execute('INSERT INTO users(name,email,password,cgpa) VALUES(?,?,?,?)',(name,email,generate_password_hash(password),cgpa))
                return redirect(url_for('login'))
            except (ValueError,sqlite3.IntegrityError): flash('Invalid details or email already registered. Use at least 8 password characters.')
        return render_template('auth.html',register=True)
    @app.route('/login',methods=['GET','POST'])
    def login():
        if request.method=='POST':
            with db() as c: u=c.execute('SELECT * FROM users WHERE email=?',(request.form['email'].strip().lower(),)).fetchone()
            if u and check_password_hash(u['password'],request.form['password']):
                session.clear(); session.update(uid=u['id'],role=u['role']); return redirect(url_for('dashboard'))
            flash('Invalid email or password.')
        return render_template('auth.html',register=False)
    @app.post('/logout')
    def logout(): session.clear(); return redirect(url_for('login'))
    @app.route('/')
    def dashboard():
        if not session.get('uid'): return redirect(url_for('login'))
        with db() as c:
            u=c.execute('SELECT * FROM users WHERE id=?',(session['uid'],)).fetchone()
            if not u: session.clear(); return redirect(url_for('login'))
            jobs=c.execute('SELECT * FROM jobs ORDER BY id DESC').fetchall()
            apps=c.execute('SELECT a.*,j.company,j.title,u.name FROM applications a JOIN jobs j ON j.id=a.job_id JOIN users u ON u.id=a.user_id WHERE (?=\'admin\' OR a.user_id=?) ORDER BY a.id DESC',(u['role'],u['id'])).fetchall()
        return render_template('dashboard.html',u=u,jobs=jobs,apps=apps)
    @app.post('/jobs')
    def jobs():
        if session.get('role')!='admin': abort(403)
        try:
            company=request.form['company'].strip(); title=request.form['title'].strip(); minimum=float(request.form['minimum']); deadline=request.form['deadline']
            from datetime import date
            date.fromisoformat(deadline)
            if not company or not title or not 0<=minimum<=10: raise ValueError()
            with db() as c: c.execute('INSERT INTO jobs(company,title,minimum,deadline) VALUES(?,?,?,?)',(company,title,minimum,deadline))
        except ValueError: flash('Invalid job details.')
        return redirect(url_for('dashboard'))
    @app.post('/apply/<int:job_id>')
    def apply(job_id):
        if session.get('role')!='student': abort(403)
        from datetime import date
        with db() as c:
            u=c.execute('SELECT * FROM users WHERE id=?',(session['uid'],)).fetchone(); j=c.execute('SELECT * FROM jobs WHERE id=?',(job_id,)).fetchone()
            if not j: abort(404)
            if u['cgpa']<j['minimum'] or j['deadline']<date.today().isoformat(): flash('Not eligible or deadline expired.')
            else:
                c.execute('INSERT OR IGNORE INTO applications(user_id,job_id) VALUES(?,?)',(u['id'],job_id)); flash('Application recorded.')
        return redirect(url_for('dashboard'))
    @app.post('/status/<int:aid>')
    def status(aid):
        if session.get('role')!='admin': abort(403)
        value=request.form['status']
        if value not in ('Applied','Shortlisted','Interview','Selected','Rejected'): abort(400)
        with db() as c: c.execute('UPDATE applications SET status=? WHERE id=?',(value,aid))
        return redirect(url_for('dashboard'))
    @app.cli.command('create-admin')
    def admin():
        import click
        email=click.prompt('Admin email').strip().lower(); password=click.prompt('Password',hide_input=True,confirmation_prompt=True)
        if len(password)<8: raise click.ClickException('Use at least 8 characters')
        with db() as c: c.execute('INSERT INTO users(name,email,password,cgpa,role) VALUES(?,?,?,?,?)',('Placement Officer',email,generate_password_hash(password),0,'admin'))
        click.echo('Admin created')
    return app

if __name__=='__main__': create_app().run()
