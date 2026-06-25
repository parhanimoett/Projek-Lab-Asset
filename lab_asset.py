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

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        assets = db.search_assets(request.form['kategori_cari'], request.form['kata_kunci'])
    else:
        assets = db.get_all_assets()
    stats = db.get_laporan_data() 
    return render_template('dashboard.html', role=session['role'], assets=assets, stats=stats)

@app.route('/tambah', methods=['GET', 'POST'])
def tambah():
    if 'username' not in session: return redirect(url_for('login'))
    if 'role' not in session or session['role'] != 'admin': return "Akses Ditolak."
    if request.method == 'POST':
        conn = db.get_db_connection()
        conn.execute('INSERT INTO assets (nama_barang, kategori, jumlah_total, kondisi_baik, kondisi_rusak, lokasi) VALUES (?, ?, ?, ?, ?, ?)',
                     (request.form['nama_barang'], request.form['kategori'], int(request.form['jumlah_total']), int(request.form['kondisi_baik']), int(request.form['kondisi_rusak']), request.form['lokasi']))
        conn.commit()
        return redirect(url_for('dashboard'))
    return render_template('form_aset.html', action="Tambah", asset=None)

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    if 'username' not in session: return redirect(url_for('login'))
    conn = db.get_db_connection()
    if request.method == 'POST':
        conn.execute('UPDATE assets SET jumlah_total=?, kondisi_baik=?, kondisi_rusak=?, lokasi=? WHERE id=?', 
                     (int(request.form['jumlah_total']), int(request.form['kondisi_baik']), int(request.form['kondisi_rusak']), request.form['lokasi'], id))
        conn.commit()
        return redirect(url_for('dashboard'))
    asset = conn.execute('SELECT * FROM assets WHERE id = ?', (id,)).fetchone()
    return render_template('form_aset.html', action="Update", asset=asset)

@app.route('/hapus/<int:id>')
def hapus(id):
    if 'username' not in session: return redirect(url_for('login'))
    if 'role' not in session or session['role'] != 'admin': return "Akses Ditolak."
    conn = db.get_db_connection()
    conn.execute('DELETE FROM assets WHERE id = ?', (id,))
    conn.commit()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)