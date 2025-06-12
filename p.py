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

# Inisialisasi colorama
init(autoreset=True)

# Banner ASCII - Sibotan Ai
figlet = Figlet(font='slant')
banner_text = figlet.renderText('Sibotan Ai')
colored_banner = (
    Fore.GREEN + banner_text +
    Fore.CYAN + "╔════════════════════════════════════════════════════╗\n" +
    "║     Smart Interactive Bot for Trading Analysis     ║\n" +
    "╠════════════════════════════════════════════════════╣\n" +
    "║ 📌 Steps:                                           \n" +
    "║   ① User Input   ② AI Analysis   ③ SL/TP Setup     \n" +
    "║   ④ Output Result ⑤ Export (future feature)        \n" +
    "╠════════════════════════════════════════════════════╣\n" +
    "║ Built by: " + Fore.YELLOW + "naoya_souta" + Fore.CYAN + "                                  ║\n" +
    "╚════════════════════════════════════════════════════╝\n"
)
print(colored_banner)

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

# Fungsi parsing RRR dari input
def extract_rr_ratio(text):
    try:
        r, rr = map(int, text.strip().split(':'))
        return r, rr
    except:
        return None

# Input user
symbol = input("Masukkan pair (contoh: BTCUSDT, XAUUSD, EURUSD): ").upper()
timeframe = input("Masukkan timeframe (1m / 5m / 15m / 30m / 1h / 4h / 1d): ").lower()
rr_input = input("Masukkan risk-reward ratio (contoh: 1:2, 1:3, 2:5): ")

rr_values = extract_rr_ratio(rr_input)
if not rr_values:
    print("⛔ Format RRR salah. Gunakan format seperti 1:2.")
    exit()
risk_ratio, reward_ratio = rr_values

if timeframe not in interval_mapping_tv:
    print("⛔ Timeframe tidak valid.")
    exit()

# Tentukan exchange
if symbol == 'XAUUSD':
    exchange = 'OANDA'
    screener = 'forex'
elif symbol.endswith('USD') and not symbol.startswith('USDT'):
    exchange = 'OANDA'
    screener = 'forex'
else:
    exchange = 'BINANCE'
    screener = 'crypto'

# Ambil data candle
try:
    df = tv.get_hist(symbol=symbol, exchange=exchange, interval=interval_mapping_tv[timeframe], n_bars=150)
    if df is None or df.empty:
        print("⛔ Data candle tidak tersedia.")
        exit()
except Exception as e:
    print(f"⛔ Gagal ambil data: {e}")
    exit()

# Ambil sinyal TA
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
        print(f"[⛔] Tidak ada peluang open posisi di {symbol} {timeframe.upper()}.")
        exit()
except Exception as e:
    print(f"⛔ Gagal ambil sinyal teknikal: {e}")
    exit()

# Status loading
print("\n🤖 Bot sedang menganalisis, mohon tunggu...", end="")
sys.stdout.flush()

# Prompt AI
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

# Fungsi hitung TP pakai Decimal
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

# Kirim ke OpenAI
try:
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    jawaban = response.choices[0].message.content.strip()
    lines = jawaban.splitlines()
    sinyal_ai = next((l.replace("SINYAL:", "").strip() for l in lines if "SINYAL:" in l), "N/A")

    open_line = next((l for l in lines if "OPEN:" in l), "OPEN: N/A")
    open_price, alasan_open = (open_line.replace("OPEN:", "").split('-', 1) + [""] )[:2]
    open_price = open_price.strip()
    alasan_open = alasan_open.strip()

    sl_line = next((l for l in lines if "SL:" in l), "SL: N/A")
    sl_price, _ = (sl_line.replace("SL:", "").split('-', 1) + [""] )[:2]
    sl_price = sl_price.strip()

    alasan_index = next((i for i, l in enumerate(lines) if "Alasan" in l), None)
    alasan_bawah = "\n".join(lines[alasan_index + 1:]).strip() if alasan_index else ""
    alasan_full = f"{alasan_open}\n\n{alasan_bawah}".strip()

    tp_price = calculate_tp(open_price, sl_price, sinyal_ai)

    # Bersihkan loading
    print("\r" + " " * 80 + "\r", end="")

    # Output final
    print("\n" + "═"*50)
    print(Fore.YELLOW + f"📈 Analisa: {symbol} [{timeframe.upper()}]")
    print("═"*50)
    print(f"🕒 Waktu Analisa : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(Fore.CYAN + f"📊 Sinyal         : {sinyal_ai}")
    print(Fore.GREEN + f"📥 Entry (OPEN)   : {open_price}")
    print(Fore.RED + f"🔴 Stop Loss (SL) : {sl_price}")
    print(Fore.GREEN + f"🟢 Take Profit(TP): {tp_price}")
    print("\n📌 Alasan:")
    print(Fore.WHITE + alasan_full)

except Exception as e:
    print(f"\n⚠️ Gagal proses hasil AI: {e}")
