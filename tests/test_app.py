from app import create_app
import sqlite3
from werkzeug.security import generate_password_hash

def test_workflow(tmp_path):
    path=str(tmp_path/'test.db'); app=create_app({'TESTING':True,'DATABASE':path}); c=app.test_client()
    def post(url,**data):
        c.get('/')
        with c.session_transaction() as s: data['csrf']=s['csrf']
        return c.post(url,data=data)
    assert post('/register',name='Student',email='student@example.com',password='password123',cgpa='8.5').status_code==302
    assert post('/login',email='student@example.com',password='password123').status_code==302
    assert post('/jobs',company='X',title='Engineer',minimum='7',deadline='2099-01-01').status_code==403
    with sqlite3.connect(path) as db:
        db.execute('INSERT INTO jobs(company,title,minimum,deadline) VALUES(?,?,?,?)',('Example','Engineer',7,'2099-01-01'))
    assert post('/apply/1').status_code==302
    assert post('/apply/1').status_code==302
    with sqlite3.connect(path) as db: assert db.execute('SELECT count(*) FROM applications').fetchone()[0]==1
    assert b'Applied' in c.get('/').data
