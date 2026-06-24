import sqlite3

def get_db_connection():
    conn = sqlite3.connect('lab_asset.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT, role TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS assets (id INTEGER PRIMARY KEY AUTOINCREMENT, nama_barang TEXT, kategori TEXT, jumlah_total INTEGER, kondisi_baik INTEGER, kondisi_rusak INTEGER, lokasi TEXT)''')
    
    cur = conn.cursor()
    cur.execute('SELECT * FROM users')
    if not cur.fetchall():
        conn.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')")
        conn.execute("INSERT INTO users (username, password, role) VALUES ('asisten', 'asisten123', 'asisten')")
        conn.commit()
    conn.close()

def get_all_assets():
    conn = get_db_connection()
    assets = conn.execute('SELECT * FROM assets').fetchall()
    conn.close()
    return assets

def search_assets(kategori_cari, kata_kunci):
    conn = get_db_connection()
    if kategori_cari == 'lokasi':
        query = "SELECT * FROM assets WHERE lokasi LIKE ?"
    else:
        query = "SELECT * FROM assets WHERE nama_barang LIKE ?"
    assets = conn.execute(query, ('%' + kata_kunci + '%',)).fetchall()
    conn.close()
    return assets

def get_laporan_data():
    assets = get_all_assets()
    total_semua = 0; total_baik = 0; total_rusak = 0
    
    for row in assets:
        total_semua += row['jumlah_total']
        total_baik += row['kondisi_baik']
        total_rusak += row['kondisi_rusak']
        
    persentase_rusak = (total_rusak / total_semua * 100) if total_semua > 0 else 0
    return {'total': total_semua, 'baik': total_baik, 'rusak': total_rusak, 'persentase': round(persentase_rusak, 2)}