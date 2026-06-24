from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
import database as db
import csv
from io import StringIO

app = Flask(__name__)
app.secret_key = "kunci_rahasia_lab_asset_aman"
db.init_db()

@app.route('/')
def home():
    if 'username' in session: return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login')
def login():
    if 'username' in session: return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login_auth', methods=['POST'])
def login_auth():
    username = request.form['username']
    password = request.form['password']
    conn = db.get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
    conn.close()
    if user:
        session['username'] = user['username']
        session['role'] = user['role']
        return redirect(url_for('dashboard'))
    else:
        flash('Username atau Password salah!')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)