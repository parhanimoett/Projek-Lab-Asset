from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
import database as db
import csv
from io import StringIO

app = Flask(__name__)
app.secret_key = "kunci_rahasia_lab_asset_aman"
db.init_db()

@app.route('/')
def home():
    # Fungsi untuk halaman utama (root). 
    # Mengarahkan user ke dashboard jika sudah login, atau ke halaman login jika belum.
    if 'username' in session: return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login')
def login():
    # Fungsi untuk menampilkan halaman form login.
    # Jika user mengakses halaman ini tapi sudah login, akan langsung dilempar ke dashboard.
    if 'username' in session: return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login_auth', methods=['POST'])
def login_auth():
    # Fungsi untuk memvalidasi input dari form login.
    # Mengecek username dan password ke database. Jika cocok, buat sesi (session). 
    # Jika salah, kembalikan pesan error (flash) dan minta login ulang.
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
    # Fungsi untuk keluar dari aplikasi (logout).
    # Menghapus seluruh data sesi pengguna dan mengembalikannya ke halaman login.
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    # Fungsi untuk menampilkan halaman utama aplikasi (dashboard).
    # Jika ada pengiriman data form (POST), fungsi ini akan melakukan pencarian barang.
    # Jika tidak (GET), akan menampilkan seluruh data barang dan statistik aset.
    if 'username' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        assets = db.search_assets(request.form['kategori_cari'], request.form['kata_kunci'])
    else:
        assets = db.get_all_assets()
    stats = db.get_laporan_data() 
    return render_template('dashboard.html', role=session['role'], assets=assets, stats=stats)

@app.route('/tambah', methods=['GET', 'POST'])
def tambah():
    # Fungsi untuk menambahkan data aset baru.
    # Hanya bisa diakses oleh user dengan role 'admin'.
    if 'username' not in session: return redirect(url_for('login'))
    if 'role' not in session or session['role'] != 'admin': return "Akses Ditolak."
    
    if request.method == 'POST':
        nama_barang = request.form['nama_barang']
        kategori = request.form['kategori']
        jumlah_total = int(request.form['jumlah_total'])
        kondisi_baik = int(request.form['kondisi_baik'])
        kondisi_rusak = int(request.form['kondisi_rusak'])
        lokasi = request.form['lokasi']

        # Validasi: Memastikan user tidak menginputkan angka minus
        if jumlah_total < 0 or kondisi_baik < 0 or kondisi_rusak < 0:
            flash('Gagal: Jumlah barang dan kondisi tidak boleh minus!')
            return render_template('form_asset.html', action="Tambah", asset=request.form)
        
        # Validasi: Memastikan logika jumlah masuk akal (Baik + Rusak = Total)
        if (kondisi_baik + kondisi_rusak) != jumlah_total:
            flash('Gagal: Jumlah kondisi baik dan rusak harus sama dengan Total Barang!')
            return render_template('form_asset.html', action="Tambah", asset=request.form)

        # Jika lolos validasi, masukkan data ke dalam database
        conn = db.get_db_connection()
        conn.execute('INSERT INTO assets (nama_barang, kategori, jumlah_total, kondisi_baik, kondisi_rusak, lokasi) VALUES (?, ?, ?, ?, ?, ?)',
                     (nama_barang, kategori, jumlah_total, kondisi_baik, kondisi_rusak, lokasi))
        conn.commit()
        return redirect(url_for('dashboard'))
        
    return render_template('form_asset.html', action="Tambah", asset=None)

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    # Fungsi untuk memperbarui (edit) data aset yang sudah ada berdasarkan ID-nya.
    if 'username' not in session: return redirect(url_for('login'))
    conn = db.get_db_connection()
    
    if request.method == 'POST':
        jumlah_total = int(request.form['jumlah_total'])
        kondisi_baik = int(request.form['kondisi_baik'])
        kondisi_rusak = int(request.form['kondisi_rusak'])
        lokasi = request.form['lokasi']

        # Validasi: Memastikan nilai tidak minus
        if jumlah_total < 0 or kondisi_baik < 0 or kondisi_rusak < 0:
            flash('Gagal: Jumlah barang dan kondisi tidak boleh minus!')
            asset_temp = request.form.to_dict()
            asset_temp['id'] = id
            return render_template('form_asset.html', action="Update", asset=asset_temp)
        
        # Validasi: Memastikan penjumlahan baik dan rusak sama dengan total barang
        if (kondisi_baik + kondisi_rusak) != jumlah_total:
            flash('Gagal: Jumlah kondisi baik dan rusak harus sama dengan Total Barang!')
            asset_temp = request.form.to_dict()
            asset_temp['id'] = id
            return render_template('form_asset.html', action="Update", asset=asset_temp)

        # Update data ke database jika lolos validasi
        conn.execute('UPDATE assets SET jumlah_total=?, kondisi_baik=?, kondisi_rusak=?, lokasi=? WHERE id=?', 
                     (jumlah_total, kondisi_baik, kondisi_rusak, lokasi, id))
        conn.commit()
        return redirect(url_for('dashboard'))
        
    # Mengambil data aset saat ini untuk ditampilkan di form edit sebelum diubah
    asset = conn.execute('SELECT * FROM assets WHERE id = ?', (id,)).fetchone()
    return render_template('form_asset.html', action="Update", asset=asset)

@app.route('/hapus/<int:id>')
def hapus(id):
    # Fungsi khusus admin untuk menghapus data aset dari database berdasarkan ID.
    if 'username' not in session: return redirect(url_for('login'))
    if 'role' not in session or session['role'] != 'admin': return "Akses Ditolak."
    conn = db.get_db_connection()
    conn.execute('DELETE FROM assets WHERE id = ?', (id,))
    conn.commit()
    return redirect(url_for('dashboard'))

@app.route('/laporan')
def laporan():
    # Fungsi untuk mengambil data ringkasan laporan dari database 
    # dan menampilkannya di halaman khusus laporan.
    if 'username' not in session: return redirect(url_for('login'))
    data_laporan = db.get_laporan_data()
    return render_template('laporan.html', data=data_laporan)

@app.route('/export_csv')
def export_csv():
    # Fungsi untuk mengunduh (download) seluruh data aset dalam format file CSV.
    # Menggunakan StringIO untuk membuat file teks dalam memori agar bisa diunduh oleh user.
    if 'username' not in session: return redirect(url_for('login'))
    assets = db.get_all_assets()
    si = StringIO()
    cw = csv.writer(si)
    
    # Menulis header (baris pertama) untuk file CSV
    cw.writerow(['ID', 'Nama Barang', 'Kategori', 'Jumlah Total', 'Kondisi Baik', 'Kondisi Rusak', 'Lokasi'])
    
    # Melakukan perulangan untuk menulis setiap baris data aset
    for a in assets:
        cw.writerow([a['id'], a['nama_barang'], a['kategori'], a['jumlah_total'], a['kondisi_baik'], a['kondisi_rusak'], a['lokasi']])
    
    # Membungkus hasilnya menjadi format respon untuk didownload
    output = Response(si.getvalue(), mimetype='text/csv')
    output.headers["Content-Disposition"] = "attachment; filename=laporan_aset.csv"
    return output

if __name__ == '__main__':
    app.run(debug=True)