<h1 align="center">📊 Sibotan Ai - Smart Bot for Trading Analysis</h1>

<p align="center">
  <img src="https://img.shields.io/github/license/naoya-souta/sibotan-ai?style=for-the-badge" />
  <img src="https://img.shields.io/github/stars/naoya-souta/sibotan-ai?style=for-the-badge" />
  <img src="https://img.shields.io/github/forks/naoya-souta/sibotan-ai?style=for-the-badge" />
  <img src="https://img.shields.io/github/issues/naoya-souta/sibotan-ai?style=for-the-badge" />
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" />
</p>

---

## 🎯 Tentang Proyek Ini

**Sibotan Ai** adalah bot trading berbasis terminal yang memanfaatkan kekuatan _AI (OpenAI GPT-4)_ dan analisa teknikal dari _TradingView_.
Dirancang untuk memberikan analisis pasar yang akurat, cepat, dan interaktif langsung dari terminal kamu.

---

## ⚙️ Fitur Utama

- 📈 Analisa teknikal otomatis berbasis GPT-4
- 🔍 Dukungan multi-pair: Crypto, Forex, Gold
- 🧠 Rekomendasi BUY / SELL berdasarkan TA dan AI
- 💹 SL & TP otomatis berdasarkan rasio Risk:Reward
- 🎛️ User input dinamis dan fleksibel
- 🖥️ Terminal interface dengan tampilan elegan dan responsive
- 📂 Opsional menyimpan hasil analisa ke file

---


## 💾 Instalasi

### 1. Clone repo ini
```bash
git clone https://github.com/naoya-souta/sibotan-ai.git
cd sibotan-ai
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Konfigurasi kredensial
Jalankan perintah berikut untuk memasukkan akun TradingView Anda (tanpa API key OpenAI):
```bash
python main.py --configure
```
Perintah di atas akan menanyakan `TV_USER` dan `TV_PASS` lalu menyimpannya ke file `credentials.json`.

Saat menjalankan bot, login AI menggunakan `OPENAI_OAUTH_TOKEN` (OAuth access token OpenAI), bukan API key.

---

## 🚀 Cara Menjalankan
```bash
python main.py
```
Gunakan opsi `--configure` kapan saja jika ingin mengganti akun TradingView yang tersimpan.

---

## 🧪 Contoh Output

```bash
📈 Analisa: BTCUSDT [1H]
📊 Sinyal         : BUY
📥 Entry (OPEN)   : 62700.00
🔴 Stop Loss (SL) : 62300.00
🟢 Take Profit(TP): 63500.00
```

---

## 🤝 Kontribusi

Pull request sangat diterima! Untuk perubahan besar, buka issue terlebih dahulu agar kita bisa diskusi.

---

## 🧠 Powered By

- [OpenAI GPT-4](https://openai.com)
- [TradingView TA](https://github.com/brian-the-dev/python-tradingview-ta)
- [tvDatafeed](https://github.com/rongardF/tvdatafeed)

---

## 🐍 Dibuat dengan Python dan ❤️ oleh [naoya_souta](https://github.com/naoya-souta)

## 🔥 Keunggulan Tambahan

- ⏱️ Eksekusi cepat dengan output rapi & berwarna
- 💬 Penjelasan analisa yang mendalam & mudah dimengerti
- 📊 Support SL/TP otomatis dengan perhitungan akurat sesuai RR ratio
- 🧩 Mudah dikembangkan untuk integrasi Telegram Bot atau GUI
- 🛠️ Struktur modular memudahkan debugging dan peningkatan fitur

## 🧠 Contoh Output

```
📈 Analisa: BTCUSDT [4H]
🕒 Waktu Analisa : 2025-06-12 08:00:00
📊 Sinyal         : BUY
📥 Entry (OPEN)   : 67000
🔴 Stop Loss (SL) : 66500
🟢 Take Profit(TP): 68000

📌 Alasan:
Harga berada di area demand kuat, didukung pola bullish engulfing dan RSI naik dari oversold. MA dan MACD menunjukkan konfirmasi arah naik.
```

---

## 🌐 Roadmap (yang akan datang)

- ☁️ Export hasil analisa ke file (.txt/.csv) **(selesai)**
- 🤖 Integrasi Telegram Bot untuk sinyal otomatis
- 🌐 Dashboard Web Live untuk rekap sinyal harian
- 📈 Fitur Chart Visualization (candlestick rendering CLI)

---

## 💡 Tips

- Gunakan terminal ukuran lebar agar banner tampil maksimal.
- Cek kembali TP/SL sesuai preferensi pribadi dan kondisi volatilitas.
- Bisa digabungkan dengan backtesting strategy untuk hasil optimal.

---

## 🙋 FAQ

**Q:** Kenapa datanya kadang tidak tersedia?  
**A:** Bisa jadi pair/timeframe tidak didukung oleh datafeed. Ganti exchange atau timeframe.

**Q:** Bisa jalan di HP Android?  
**A:** Bisa pakai Termux atau Pydroid 3 dengan sedikit penyesuaian dependency.

---
