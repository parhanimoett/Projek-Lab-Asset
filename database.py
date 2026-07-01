import sqlite3

def get_db_connection():
    # Fungsi ini bertugas untuk membuat dan membuka koneksi ke file database 'lab_asset.db'.
    # sqlite3.Row digunakan agar hasil query (data dari database) bisa dipanggil 
    # menggunakan nama kolomnya seperti dictionary, contoh: row['nama_barang'].
    conn = sqlite3.connect('lab_asset.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Fungsi ini dijalankan saat aplikasi pertama kali dimulai untuk menyiapkan database.
    # Mengecek dan membuat tabel 'users' dan 'assets' jika belum ada di dalam database.
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT, role TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS assets (id INTEGER PRIMARY KEY AUTOINCREMENT, nama_barang TEXT, kategori TEXT, jumlah_total INTEGER, kondisi_baik INTEGER, kondisi_rusak INTEGER, lokasi TEXT)''')
    
    # Mengecek apakah tabel 'users' masih kosong. Jika kosong, fungsi ini akan 
    # otomatis membuat dua akun bawaan (default) yaitu 'admin' dan 'asisten'.
    cur = conn.cursor()
    cur.execute('SELECT * FROM users')
    if not cur.fetchall():
        conn.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')")
        conn.execute("INSERT INTO users (username, password, role) VALUES ('asisten', 'asisten123', 'asisten')")
        conn.commit()
    conn.close()

def get_all_assets():
    # Fungsi ini mengambil (menampilkan) seluruh data barang yang ada di dalam tabel 'assets'.
    conn = get_db_connection()
    assets = conn.execute('SELECT * FROM assets').fetchall()
    conn.close()
    return assets

def search_assets(kategori_cari, kata_kunci):
    # Fungsi ini digunakan untuk fitur pencarian barang pada halaman dashboard.
    # Pencarian disesuaikan dengan pilihan kategori ('lokasi' atau nama barang)
    # Tanda '%' pada query LIKE berfungsi agar pencarian bisa menemukan kecocokan kata secara parsial.
    conn = get_db_connection()
    if kategori_cari == 'lokasi':
        query = "SELECT * FROM assets WHERE lokasi LIKE ?"
    else:
        query = "SELECT * FROM assets WHERE nama_barang LIKE ?"
    
    assets = conn.execute(query, ('%' + kata_kunci + '%',)).fetchall()
    conn.close()
    return assets

def get_laporan_data():
    # Fungsi ini mengambil semua data barang, kemudian menghitung statistik totalnya.
    # Statistik yang dihitung meliputi total seluruh barang, total kondisi baik, 
    # total kondisi rusak, dan persentase kerusakan barang.
    assets = get_all_assets()
    total_semua = 0; total_baik = 0; total_rusak = 0
    
    # Melakukan perulangan untuk menjumlahkan semua angka dari setiap barang
    for row in assets:
        total_semua += row['jumlah_total']
        total_baik += row['kondisi_baik']
        total_rusak += row['kondisi_rusak']
        
    # Menghitung persentase barang rusak (mencegah error pembagian dengan nol jika data kosong)
    persentase_rusak = (total_rusak / total_semua * 100) if total_semua > 0 else 0
    
    # Mengembalikan hasil perhitungan dalam bentuk dictionary
    return {'total': total_semua, 'baik': total_baik, 'rusak': total_rusak, 'persentase': round(persentase_rusak, 2)}