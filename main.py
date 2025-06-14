from tradingview_ta import TA_Handler, Interval, Exchange
from tvDatafeed import TvDatafeed, Interval as TvInterval
from config import OPENAI_API_KEY, TV_USER, TV_PASS
import openai
import pandas as pd
import sys
import contextlib
import os
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from colorama import init, Fore, Style
from pyfiglet import Figlet
import shutil


# Inisialisasi colorama
init(autoreset=True)

# Banner Responsive
def tampilkan_banner():
    terminal_width = shutil.get_terminal_size().columns
    figlet = Figlet(font='slant')
    banner_text = figlet.renderText('Sibotan Ai')
    banner_lines = banner_text.splitlines()

    for line in banner_lines:
        print(Fore.GREEN + line.center(terminal_width))

    print(Fore.CYAN + "=" * terminal_width)
    
    steps_text = [
        "Smart Interactive Bot for Trading Analysis",
        "① User Input   ② AI Analysis   ③ SL/TP Setup",
        "④ Output Result ⑤ Export (future feature)"
    ]
    for text in steps_text:
        print(Fore.CYAN + text.center(terminal_width))

    print(Fore.CYAN + "=" * terminal_width)
    print(Fore.YELLOW + "Build with ❤ by naoya_souta".center(terminal_width))
    print(Fore.CYAN + "=" * terminal_width + "\n")

# Tampilkan banner di awal

# Setup API
openai.api_key = OPENAI_API_KEY

# Redam output login
with open(os.devnull, 'w') as fnull:
    with contextlib.redirect_stdout(fnull), contextlib.redirect_stderr(fnull):
        try:
            tv = TvDatafeed(username=TV_USER, password=TV_PASS)
        except:
            tv = TvDatafeed()

# Mapping timeframe
interval_mapping_ta = {
    '1m': Interval.INTERVAL_1_MINUTE,
    '5m': Interval.INTERVAL_5_MINUTES,
    '15m': Interval.INTERVAL_15_MINUTES,
    '30m': Interval.INTERVAL_30_MINUTES,
    '1h': Interval.INTERVAL_1_HOUR,
    '4h': Interval.INTERVAL_4_HOURS,
    '1d': Interval.INTERVAL_1_DAY,
}
interval_mapping_tv = {
    '1m': TvInterval.in_1_minute,
    '5m': TvInterval.in_5_minute,
    '15m': TvInterval.in_15_minute,
    '30m': TvInterval.in_30_minute,
    '1h': TvInterval.in_1_hour,
    '4h': TvInterval.in_4_hour,
    '1d': TvInterval.in_daily,
}

def extract_rr_ratio(text):
    try:
        r, rr = map(int, text.strip().split(':'))
        return r, rr
    except:
        return None

def calculate_tp(open_price_str, sl_price_str, signal):
    try:
        open_f = Decimal(open_price_str.replace(',', ''))
        sl_f = Decimal(sl_price_str.replace(',', ''))
        risk = abs(open_f - sl_f)
        reward = risk * (Decimal(reward_ratio) / Decimal(risk_ratio))
        tp_f = open_f + reward if signal.upper() == "BUY" else open_f - reward
        decimal_places = abs(open_price_str[::-1].find('.')) if '.' in open_price_str else 0
        quantize_str = '1.' + '0' * decimal_places if decimal_places > 0 else '1'
        tp_ai = tp_f.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
        return str(tp_ai)
    except:
        return "?"

# Start program
if __name__ == '__main__':
    tampilkan_banner()

    symbol = input("Masukkan pair (contoh: BTCUSDT, XAUUSD, EURUSD): ").upper()
    timeframe = input("Masukkan timeframe (1m / 5m / 15m / 30m / 1h / 4h / 1d): ").lower()
    rr_input = input("Masukkan risk-reward ratio (contoh: 1:2, 1:3, 2:5): ")

    rr_values = extract_rr_ratio(rr_input)
    if not rr_values:
        print("\u26d4 Format RRR salah. Gunakan format seperti 1:2.")
        exit()
    risk_ratio, reward_ratio = rr_values

    if timeframe not in interval_mapping_tv:
        print("\u26d4 Timeframe tidak valid.")
        exit()

    if symbol == 'XAUUSD':
        exchange = 'OANDA'
        screener = 'forex'
    elif symbol.endswith('USD') and not symbol.startswith('USDT'):
        exchange = 'OANDA'
        screener = 'forex'
    else:
        exchange = 'BINANCE'
        screener = 'crypto'

    try:
        df = tv.get_hist(symbol=symbol, exchange=exchange, interval=interval_mapping_tv[timeframe], n_bars=150)
        if df is None or df.empty:
            print("\u26d4 Data candle tidak tersedia.")
            exit()
    except Exception as e:
        print(f"\u26d4 Gagal ambil data: {e}")
        exit()

    try:
        handler = TA_Handler(
            symbol=symbol,
            screener=screener,
            exchange=exchange,
            interval=interval_mapping_ta[timeframe]
        )
        hasil = handler.get_analysis()
        sinyal = hasil.summary['RECOMMENDATION']
        if sinyal == "NEUTRAL":
            print(f"[\u26d4] Tidak ada peluang open posisi di {symbol} {timeframe.upper()}.")
            exit()
    except Exception as e:
        print(f"\u26d4 Gagal ambil sinyal teknikal: {e}")
        exit()

    print("\n🤖 Bot sedang menganalisis, mohon tunggu...", end="")
    sys.stdout.flush()

   # ... [kode sebelumnya tidak berubah] ...

    prompt = f"""
Lakukan analisa teknikal profesional terhadap pasangan {symbol} pada timeframe {timeframe.upper()}.

### Data Harga Terkini:
- Open: {df['open'].iloc[-1]}
- High: {df['high'].iloc[-1]}
- Low: {df['low'].iloc[-1]}
- Close: {df['close'].iloc[-1]}
- Volume: {df['volume'].iloc[-1]}
- Sinyal Awal: {sinyal}

### Format Jawaban:
SINYAL: BUY / SELL / WAIT  
OPEN: [harga entry] — Jelaskan alasan masuk posisi  
SL: [level stop loss] — Jelaskan kenapa level ini dipilih  
TP: [level take profit] — Hitung otomatis dengan RISK:REWARD = {risk_ratio}:{reward_ratio}  
RISK MANAGEMENT: Jelaskan strategi risk per trade yang ideal

Detailkan analisa berdasarkan:
- Pola candlestick signifikan (jika ada): engulfing, pin bar, hammer, dll
- Support/resistance & trendline
- Zona demand/supply (jika terlihat jelas)
- Indikator teknikal: RSI, MACD, MA, volume
- Konfirmasi candle lanjutan
-Jawaban harus meyakinkan, dan disampaikan seolah-olah dari analis profesional kepada trader lain. Jika tidak ada sinyal valid untuk entry, jelaskan alasannya secara objektif dan hindari memaksakan posisi.
""".strip()

    # ✅ try ini HARUS sejajar dengan prompt, bukan masuk ke dalam string prompt
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )

        jawaban = response.choices[0].message.content.strip()
        if not jawaban or "SINYAL:" not in jawaban:
            raise ValueError("AI tidak memberikan jawaban yang valid atau lengkap.")

        lines = jawaban.splitlines()
        sinyal_ai = next((l.replace("SINYAL:", "").strip() for l in lines if "SINYAL:" in l), "N/A")

        open_line = next((l for l in lines if "OPEN:" in l), "OPEN: N/A")
        # AI sometimes uses en/em dashes; normalize them before splitting
        open_clean = open_line.replace("OPEN:", "").replace("—", "-").replace("–", "-")
        open_price, alasan_open = (open_clean.split('-', 1) + ["" ])[:2]
        open_price = open_price.strip()
        alasan_open = alasan_open.strip()

        sl_line = next((l for l in lines if "SL:" in l), "SL: N/A")
        sl_clean = sl_line.replace("SL:", "").replace("—", "-").replace("–", "-")
        sl_price, _ = (sl_clean.split('-', 1) + [""])[:2]
        sl_price = sl_price.strip()

        alasan_index = next((i for i, l in enumerate(lines) if "Alasan" in l or "RISK" in l), None)
        alasan_bawah = "\n".join(lines[alasan_index + 1:]).strip() if alasan_index is not None else ""
        alasan_full = f"{alasan_open}\n\n{alasan_bawah}".strip()

        tp_price = calculate_tp(open_price, sl_price, sinyal_ai)

        print("\r" + " " * 80 + "\r", end="")

        print("\n" + "═"*50)
        print(Fore.YELLOW + f"📈 Analisa: {symbol} [{timeframe.upper()}]")
        print("═"*50)
        print(f"🕒 Waktu Analisa : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(Fore.CYAN + f"📊 Sinyal         : {sinyal_ai}")
        print(Fore.GREEN + f"📥 Entry (OPEN)   : {open_price if open_price else 'N/A'}")
        print(Fore.RED + f"🔴 Stop Loss (SL) : {sl_price if sl_price else 'N/A'}")
        print(Fore.GREEN + f"🟢 Take Profit(TP): {tp_price if tp_price else '?'}")
        print("\n📌 Alasan:")
        print(Fore.WHITE + (alasan_full if alasan_full else "AI tidak memberikan alasan lengkap."))

        hasil_text = (
            f"Analisa: {symbol} [{timeframe.upper()}]\n"
            f"Waktu Analisa : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Sinyal         : {sinyal_ai}\n"
            f"Entry (OPEN)   : {open_price if open_price else 'N/A'}\n"
            f"Stop Loss (SL) : {sl_price if sl_price else 'N/A'}\n"
            f"Take Profit(TP): {tp_price if tp_price else '?'}\n\n"
            f"Alasan:\n{alasan_full if alasan_full else 'AI tidak memberikan alasan lengkap.'}\n"
        )

        if input("Simpan hasil ke file? (y/n): ").lower() == 'y':
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"hasil_{symbol}_{timeframe}_{timestamp}.txt"
            with open(filename, 'w') as file:
                file.write(hasil_text)
            print(f"✅ Hasil disimpan di {filename}")
        

    except Exception as e:
        print("\n❌ Tidak bisa menganalisa setup entry saat ini.")
        print(f"📉 Alasan: {str(e)}")
        print("📢 Coba gunakan pair atau timeframe lain, atau periksa koneksi API.")
