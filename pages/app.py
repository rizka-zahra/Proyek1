from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import sqlite3
import datetime

app = Flask(__name__)

# Ganti dengan API key Gemini kamu
genai.configure(api_key="AIzaSyC4TXs1Hb1qCxExZqEiOYTNetH39vzZWI8")

# Fungsi untuk membuat tabel database
def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Inisialisasi model Gemini
model = genai.GenerativeModel('gemini-1.5-flash')

# Endpoint utama untuk menampilkan halaman
@app.route('/')
def index():
    return render_template('konsul.html')

# Endpoint untuk mengirim dan menerima pesan
@app.route('/api/chat', methods=['POST'])
def chat():
    user_message = request.json['message']
    
    # Ambil waktu lokal dan format menjadi string yang mudah dibaca SQLite
    local_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
    formatted_time = local_time.strftime('%Y-%m-%d %H:%M:%S')
    
    # Simpan pesan pengguna ke database
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender, content, timestamp) VALUES (?, ?, ?)", ('user', user_message, formatted_time))
    conn.commit()
    
    # Kirim pesan ke Gemini
    response = model.generate_content(user_message)
    ai_response = response.candidates[0].content.parts[0].text

    # Simpan respons AI ke database
    local_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
    formatted_time = local_time.strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO messages (sender, content, timestamp) VALUES (?, ?, ?)", ('ai', ai_response, formatted_time))
    conn.commit()
    conn.close()
    
    return jsonify({'ai_response': ai_response})

# Endpoint untuk riwayat yang dikelompokkan
@app.route('/api/history_grouped', methods=['GET'])
def get_history_grouped():
    from_date = request.args.get('date')
    print(f"Tanggal yang diterima dari frontend: {from_date}") #Debugging
    
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    
    # Perintah SQL dasar
    base_query = """
        SELECT sender, content, timestamp, 
             strftime('%Y-%m-%d', timestamp) AS date_only
        FROM messages
    """
    
    # Tambahkan filter tanggal jika ada
    if from_date:
        query = base_query + " WHERE date_only = ? ORDER BY timestamp ASC"
        c.execute(query, (from_date,))
    else:
        query = base_query + " ORDER BY timestamp ASC"
        c.execute(query)

    rows = c.fetchall()
    conn.close()

    grouped = {}
    for row in rows:
        sender, content, timestamp, date_only = row
        date_key = date_only
        print(f"Mengelompokkan pesan dengan tanggal: {date_key}")
        
        if date_key not in grouped:
            grouped[date_key] = []
        
        grouped[date_key].append({
            'sender': sender,
            'content': content,
            'timestamp': timestamp
        })
    
    return jsonify(grouped)

# Endpoint untuk menghapus riwayat chat (bisa per tanggal)
@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    date_to_delete = request.args.get('date')
    
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    
    if date_to_delete:
        # Hapus hanya pesan pada tanggal yang dipilih
        c.execute("DELETE FROM messages WHERE strftime('%Y-%m-%d', timestamp) = ?", (date_to_delete,))
        message = f"Riwayat chat pada tanggal {date_to_delete} berhasil dihapus."
    else:
        # Hapus seluruh riwayat jika tidak ada tanggal yang dipilih
        c.execute("DELETE FROM messages")
        message = "Seluruh riwayat chat berhasil dihapus!"
        
    conn.commit()
    conn.close()
    return jsonify({"message": message})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)