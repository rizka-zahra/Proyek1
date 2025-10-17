import google.generativeai as genai

# Masukkan kunci API Gemini kamu
genai.configure(api_key="AIzaSyC4TXs1Hb1qCxExZqEiOYTNetH39vzZWI8")

# Gunakan model yang tersedia dan stabil
model = genai.GenerativeModel('gemini-2.5-flash')

# Kirim prompt kamu
response = model.generate_content("Explain how AI works in a few words")

print(response.text)