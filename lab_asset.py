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
        nama_barang = request.form['nama_barang']
        kategori = request.form['kategori']
        jumlah_total = int(request.form['jumlah_total'])
        kondisi_baik = int(request.form['kondisi_baik'])
        kondisi_rusak = int(request.form['kondisi_rusak'])
        lokasi = request.form['lokasi']

        # Validasi: Tidak boleh minus
        if jumlah_total < 0 or kondisi_baik < 0 or kondisi_rusak < 0:
            flash('Gagal: Jumlah barang dan kondisi tidak boleh minus!')
            return render_template('form_asset.html', action="Tambah", asset=request.form)
        
        # Validasi: Baik + Rusak harus sama dengan Total
        if (kondisi_baik + kondisi_rusak) != jumlah_total:
            flash('Gagal: Jumlah kondisi baik dan rusak harus sama dengan Total Barang!')
            return render_template('form_asset.html', action="Tambah", asset=request.form)

        conn = db.get_db_connection()
        conn.execute('INSERT INTO assets (nama_barang, kategori, jumlah_total, kondisi_baik, kondisi_rusak, lokasi) VALUES (?, ?, ?, ?, ?, ?)',
                     (nama_barang, kategori, jumlah_total, kondisi_baik, kondisi_rusak, lokasi))
        conn.commit()
        return redirect(url_for('dashboard'))
        
    return render_template('form_asset.html', action="Tambah", asset=None)

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    if 'username' not in session: return redirect(url_for('login'))
    conn = db.get_db_connection()
    
    if request.method == 'POST':
        jumlah_total = int(request.form['jumlah_total'])
        kondisi_baik = int(request.form['kondisi_baik'])
        kondisi_rusak = int(request.form['kondisi_rusak'])
        lokasi = request.form['lokasi']

        # Validasi: Tidak boleh minus
        if jumlah_total < 0 or kondisi_baik < 0 or kondisi_rusak < 0:
            flash('Gagal: Jumlah barang dan kondisi tidak boleh minus!')
            asset_temp = request.form.to_dict()
            asset_temp['id'] = id
            return render_template('form_asset.html', action="Update", asset=asset_temp)
        
        # Validasi: Baik + Rusak harus sama dengan Total
        if (kondisi_baik + kondisi_rusak) != jumlah_total:
            flash('Gagal: Jumlah kondisi baik dan rusak harus sama dengan Total Barang!')
            asset_temp = request.form.to_dict()
            asset_temp['id'] = id
            return render_template('form_asset.html', action="Update", asset=asset_temp)

        conn.execute('UPDATE assets SET jumlah_total=?, kondisi_baik=?, kondisi_rusak=?, lokasi=? WHERE id=?', 
                     (jumlah_total, kondisi_baik, kondisi_rusak, lokasi, id))
        conn.commit()
        return redirect(url_for('dashboard'))
        
    asset = conn.execute('SELECT * FROM assets WHERE id = ?', (id,)).fetchone()
    return render_template('form_asset.html', action="Update", asset=asset)

@app.route('/hapus/<int:id>')
def hapus(id):
    if 'username' not in session: return redirect(url_for('login'))
    if 'role' not in session or session['role'] != 'admin': return "Akses Ditolak."
    conn = db.get_db_connection()
    conn.execute('DELETE FROM assets WHERE id = ?', (id,))
    conn.commit()
    return redirect(url_for('dashboard'))

@app.route('/laporan')
def laporan():
    if 'username' not in session: return redirect(url_for('login'))
    data_laporan = db.get_laporan_data()
    return render_template('laporan.html', data=data_laporan)

@app.route('/export_csv')
def export_csv():
    if 'username' not in session: return redirect(url_for('login'))
    assets = db.get_all_assets()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Nama Barang', 'Kategori', 'Jumlah Total', 'Kondisi Baik', 'Kondisi Rusak', 'Lokasi'])
    for a in assets:
        cw.writerow([a['id'], a['nama_barang'], a['kategori'], a['jumlah_total'], a['kondisi_baik'], a['kondisi_rusak'], a['lokasi']])
    output = Response(si.getvalue(), mimetype='text/csv')
    output.headers["Content-Disposition"] = "attachment; filename=laporan_aset.csv"
    return output

if __name__ == '__main__':
    app.run(debug=True)