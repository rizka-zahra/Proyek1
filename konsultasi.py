from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import mysql.connector
import datetime

app = Flask(__name__)
CORS(app)

# Konfigurasi API Gemini
genai.configure(api_key="AIzaSyC4TXs1Hb1qCxExZqEiOYTNetH39vzZWI8")
model = genai.GenerativeModel('gemini-1.5-flash')

# Fungsi koneksi ke MySQL
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",          # ganti sesuai user MySQL
        password="",          # isi kalau pakai password
        database="stuntfree"  # nama database kamu
    )

# Halaman utama
@app.route('/')
def index():
    return "Flask backend running."

# Endpoint untuk chat
@app.route('/api/chat', methods=['POST'])
def chat():
    user_message = request.json['message']
    id_pengguna = 1  # bisa disesuaikan dengan user login misalnya

    local_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
    formatted_time = local_time.strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db_connection()
    c = conn.cursor()

    # Simpan pesan user
    c.execute("""
        INSERT INTO riwayat_chat (id_pengguna, sender, pesan, waktu)
        VALUES (%s, %s, %s, %s)
    """, (id_pengguna, 'user', user_message, formatted_time))
    conn.commit()

    # Dapatkan respons dari Gemini
    response = model.generate_content(user_message)
    ai_response = response.candidates[0].content.parts[0].text

    # Simpan respons AI
    c.execute("""
        INSERT INTO riwayat_chat (id_pengguna, sender, pesan, waktu)
        VALUES (%s, %s, %s, %s)
    """, (id_pengguna, 'ai', ai_response, formatted_time))
    conn.commit()

    c.close()
    conn.close()

    return jsonify({'ai_response': ai_response})

# Endpoint untuk riwayat
@app.route('/api/history_grouped', methods=['GET'])
def get_history_grouped():
    from_date = request.args.get('date')

    conn = get_db_connection()
    c = conn.cursor(dictionary=True)

    base_query = """
        SELECT sender, pesan AS content, waktu AS timestamp, DATE(waktu) AS date_only
        FROM riwayat_chat
    """

    if from_date:
        query = base_query + " WHERE DATE(waktu) = %s ORDER BY waktu ASC"
        c.execute(query, (from_date,))
    else:
        query = base_query + " ORDER BY waktu ASC"
        c.execute(query)

    rows = c.fetchall()
    conn.close()

    grouped = {}
    for row in rows:
        date_key = row['date_only']
        if date_key not in grouped:
            grouped[date_key] = []
        grouped[date_key].append({
            'sender': row['sender'],
            'content': row['content'],
            'timestamp': row['timestamp']
        })

    return jsonify(grouped)

# Endpoint hapus riwayat
@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    date_to_delete = request.args.get('date')

    conn = get_db_connection()
    c = conn.cursor()

    if date_to_delete:
        c.execute("DELETE FROM riwayat_chat WHERE DATE(waktu) = %s", (date_to_delete,))
        message = f"Riwayat chat tanggal {date_to_delete} berhasil dihapus."
    else:
        c.execute("DELETE FROM riwayat_chat")
        message = "Seluruh riwayat chat berhasil dihapus."

    conn.commit()
    c.close()
    conn.close()

    return jsonify({"message": message})


if __name__ == '__main__':
    app.run(debug=True)
