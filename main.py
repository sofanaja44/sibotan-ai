from tradingview_ta import TA_Handler, Interval, Exchange
from tvDatafeed import TvDatafeed, Interval as TvInterval
from credentials import load_credentials, save_credentials
import argparse
from openai import OpenAI
import pandas as pd
import sys
import contextlib
import os
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from colorama import init, Fore, Style
from pyfiglet import Figlet
import shutil
import hashlib
import json
from urllib import parse, request, error


# Inisialisasi colorama
init(autoreset=True)

# Parse CLI arguments
parser = argparse.ArgumentParser(description="Sibotan Ai")
parser.add_argument('--configure', action='store_true', help='Set or update saved credentials and exit')
args = parser.parse_args()

if args.configure:
    creds = load_credentials()
    creds['TV_USER'] = input('TV_USER: ').strip()
    creds['TV_PASS'] = input('TV_PASS: ').strip()
    save_credentials(creds)
    print('Credentials saved.')
    sys.exit(0)

import config
TV_USER = config.TV_USER
TV_PASS = config.TV_PASS

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

# Setup Codex OAuth token (tanpa API key)
AI_MODEL = "codex-5.3"
creds = load_credentials()

OAUTH_AUTHORIZE_URL = "https://auth.openai.com/oauth/authorize"
OAUTH_TOKEN_URL = "https://auth.openai.com/oauth/token"


def build_oauth_authorize_url(client_id, redirect_uri, state='sibotan-ai-login'):
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'openid offline_access',
        'state': state,
    }
    return f"{OAUTH_AUTHORIZE_URL}?{parse.urlencode(params)}"


def parse_authorization_code(raw_input):
    value = (raw_input or '').strip()
    if not value:
        return ''

    if '://' in value and 'code=' in value:
        parsed = parse.urlparse(value)
        query = parse.parse_qs(parsed.query)
        return query.get('code', [''])[0]

    return value


def oauth_token_request(payload):
    encoded_data = parse.urlencode(payload).encode('utf-8')
    req = request.Request(
        OAUTH_TOKEN_URL,
        data=encoded_data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST',
    )
    with request.urlopen(req, timeout=20) as response:
        body = response.read().decode('utf-8')
        return json.loads(body)


def exchange_authorization_code(client_id, client_secret, code, redirect_uri):
    payload = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'redirect_uri': redirect_uri,
    }
    return oauth_token_request(payload)


def refresh_oauth_token(client_id, client_secret, refresh_token):
    payload = {
        'grant_type': 'refresh_token',
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
    }
    return oauth_token_request(payload)


def save_oauth_tokens(credentials, token_response):
    access_token = token_response.get('access_token')
    refresh_token = token_response.get('refresh_token')
    expires_in = token_response.get('expires_in')

    if access_token:
        credentials['CODEX_OAUTH_TOKEN'] = access_token

    if refresh_token:
        credentials['OPENAI_REFRESH_TOKEN'] = refresh_token

    if isinstance(expires_in, (int, float)):
        expires_at = datetime.now() + timedelta(seconds=int(expires_in))
        credentials['OPENAI_OAUTH_EXPIRES_AT'] = expires_at.isoformat()

    save_credentials(credentials)


def get_saved_oauth_token(credentials):
    token = credentials.get('CODEX_OAUTH_TOKEN') or credentials.get('OPENAI_OAUTH_TOKEN')
    expires_at = credentials.get('OPENAI_OAUTH_EXPIRES_AT')

    if not token:
        return ''

    if not expires_at:
        return token

    try:
        if datetime.now() < datetime.fromisoformat(expires_at):
            return token
    except ValueError:
        return token

    return ''


CODEX_OAUTH_TOKEN = os.getenv('CODEX_OAUTH_TOKEN') or os.getenv('CODEX_TOKEN') or get_saved_oauth_token(creds)

if not CODEX_OAUTH_TOKEN:
    oauth_client_id = os.getenv('OPENAI_OAUTH_CLIENT_ID') or creds.get('OPENAI_OAUTH_CLIENT_ID')
    oauth_client_secret = os.getenv('OPENAI_OAUTH_CLIENT_SECRET') or creds.get('OPENAI_OAUTH_CLIENT_SECRET')
    oauth_redirect_uri = os.getenv('OPENAI_OAUTH_REDIRECT_URI') or creds.get('OPENAI_OAUTH_REDIRECT_URI')
    oauth_refresh_token = os.getenv('OPENAI_REFRESH_TOKEN') or creds.get('OPENAI_REFRESH_TOKEN')

    if oauth_client_id and oauth_client_secret and oauth_refresh_token:
        try:
            refreshed = refresh_oauth_token(oauth_client_id, oauth_client_secret, oauth_refresh_token)
            save_oauth_tokens(creds, refreshed)
            CODEX_OAUTH_TOKEN = refreshed.get('access_token', '')
            if CODEX_OAUTH_TOKEN:
                print('✅ OAuth token berhasil diperbarui otomatis via refresh token.')
        except (error.HTTPError, error.URLError, json.JSONDecodeError):
            pass

    if not CODEX_OAUTH_TOKEN and oauth_client_id and oauth_client_secret and oauth_redirect_uri:
        auth_url = build_oauth_authorize_url(oauth_client_id, oauth_redirect_uri)
        print('\n🔐 Login OAuth OpenAI diperlukan untuk melanjutkan.')
        print('1) Buka URL berikut di browser, login, lalu izinkan akses aplikasi:')
        print(auth_url)
        raw_code = input('2) Paste authorization code (atau URL redirect penuh): ').strip()
        authorization_code = parse_authorization_code(raw_code)

        if authorization_code:
            try:
                token_response = exchange_authorization_code(
                    oauth_client_id,
                    oauth_client_secret,
                    authorization_code,
                    oauth_redirect_uri,
                )
                save_oauth_tokens(creds, token_response)
                CODEX_OAUTH_TOKEN = token_response.get('access_token', '')
                if CODEX_OAUTH_TOKEN:
                    print('✅ OAuth login berhasil. Access token sudah tersimpan.')
            except error.HTTPError as http_error:
                detail = http_error.read().decode('utf-8', errors='ignore')
                print(f'❌ OAuth token exchange gagal: {detail or http_error.reason}')
            except (error.URLError, json.JSONDecodeError) as exc:
                print(f'❌ OAuth token exchange gagal: {exc}')

if not CODEX_OAUTH_TOKEN:
    CODEX_OAUTH_TOKEN = input('CODEX_OAUTH_TOKEN (OAuth access token): ').strip()
    if CODEX_OAUTH_TOKEN:
        creds['CODEX_OAUTH_TOKEN'] = CODEX_OAUTH_TOKEN
        save_credentials(creds)

if not CODEX_OAUTH_TOKEN:
    print('❌ CODEX_OAUTH_TOKEN belum diisi. Silakan login Codex/OpenAI dan masukkan OAuth token Anda.')
    sys.exit(1)

client = OpenAI(api_key=CODEX_OAUTH_TOKEN)

# Redam output login
with open(os.devnull, 'w') as fnull:
    with contextlib.redirect_stdout(fnull), contextlib.redirect_stderr(fnull):
        try:
            tv = TvDatafeed(username=TV_USER, password=TV_PASS)
        except Exception:
            # Fallback to anonymous connection if credentials fail
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

# Cache configuration
CACHE_DIR = os.path.join(os.path.dirname(__file__), '.cache')
CACHE_EXPIRY_MINUTES = 5  # Cache expires after 5 minutes

def get_cache_key(symbol, timeframe, rr_ratio):
    """Generate a unique cache key for the analysis."""
    key_string = f"{symbol}_{timeframe}_{rr_ratio}"
    return hashlib.md5(key_string.encode()).hexdigest()

def load_from_cache(cache_key):
    """Load analysis result from cache if not expired."""
    if not os.path.exists(CACHE_DIR):
        return None

    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    if not os.path.exists(cache_file):
        return None

    try:
        with open(cache_file, 'r') as f:
            cached_data = json.load(f)

        # Check if cache is expired
        cached_time = datetime.fromisoformat(cached_data['timestamp'])
        if datetime.now() - cached_time > timedelta(minutes=CACHE_EXPIRY_MINUTES):
            # Cache expired, remove it
            os.remove(cache_file)
            return None

        return cached_data['result']
    except (json.JSONDecodeError, KeyError, ValueError):
        return None

def save_to_cache(cache_key, result_data):
    """Save analysis result to cache."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    cached_data = {
        'timestamp': datetime.now().isoformat(),
        'result': result_data
    }

    try:
        with open(cache_file, 'w') as f:
            json.dump(cached_data, f, indent=2)
    except IOError:
        pass  # Silently fail if cache write fails

def extract_rr_ratio(text):
    """Extract risk-reward ratio from string format like '1:2'."""
    try:
        r, rr = map(int, text.strip().split(':'))
        return r, rr
    except (ValueError, AttributeError):
        return None

def calculate_tp(open_price_str, sl_price_str, signal):
    """Calculate take profit based on risk-reward ratio."""
    try:
        # Validate inputs
        if not open_price_str or not sl_price_str or not signal:
            return "?"

        open_f = Decimal(open_price_str.replace(',', ''))
        sl_f = Decimal(sl_price_str.replace(',', ''))
        risk = abs(open_f - sl_f)

        # Avoid division by zero
        if risk == 0:
            return "?"

        reward = risk * (Decimal(reward_ratio) / Decimal(risk_ratio))
        tp_f = open_f + reward if signal.upper() == "BUY" else open_f - reward
        decimal_places = abs(open_price_str[::-1].find('.')) if '.' in open_price_str else 0
        quantize_str = '1.' + '0' * decimal_places if decimal_places > 0 else '1'
        tp_ai = tp_f.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
        return str(tp_ai)
    except (ValueError, TypeError, ArithmeticError) as e:
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

    # Check cache first
    cache_key = get_cache_key(symbol, timeframe, rr_input)
    cached_result = load_from_cache(cache_key)

    if cached_result:
        print(Fore.YELLOW + "\n💾 Menggunakan hasil dari cache (< 5 menit yang lalu)...")
        print("\n" + "═"*50)
        print(Fore.YELLOW + f"📈 Analisa: {cached_result['symbol']} [{cached_result['timeframe']}]")
        print("═"*50)
        print(f"🕒 Waktu Analisa : {cached_result['timestamp']}")
        print(Fore.CYAN + f"📊 Sinyal         : {cached_result['sinyal']}")
        print(Fore.GREEN + f"📥 Entry (OPEN)   : {cached_result['open']}")
        print(Fore.RED + f"🔴 Stop Loss (SL) : {cached_result['sl']}")
        print(Fore.GREEN + f"🟢 Take Profit(TP): {cached_result['tp']}")
        print("\n📌 Alasan:")
        print(Fore.WHITE + cached_result['alasan'])
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
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )

        jawaban = (response.choices[0].message.content or '').strip()
        if not jawaban or "SINYAL:" not in jawaban:
            raise ValueError("AI tidak memberikan jawaban yang valid atau lengkap.")

        lines = jawaban.splitlines()
        sinyal_ai = next((l.replace("SINYAL:", "").strip() for l in lines if "SINYAL:" in l), "N/A")

        # Parse OPEN price with more robust handling
        open_line = next((l for l in lines if "OPEN:" in l), "OPEN: N/A")
        # AI sometimes uses en/em dashes; normalize them before splitting
        open_clean = open_line.replace("OPEN:", "").replace("—", "-").replace("–", "-").replace("―", "-")
        open_parts = open_clean.split('-', 1)
        open_price = open_parts[0].strip() if len(open_parts) > 0 else "N/A"
        alasan_open = open_parts[1].strip() if len(open_parts) > 1 else ""

        # Parse SL price
        sl_line = next((l for l in lines if "SL:" in l), "SL: N/A")
        sl_clean = sl_line.replace("SL:", "").replace("—", "-").replace("–", "-").replace("―", "-")
        sl_parts = sl_clean.split('-', 1)
        sl_price = sl_parts[0].strip() if len(sl_parts) > 0 else "N/A"

        alasan_index = next((i for i, l in enumerate(lines) if "Alasan" in l or "RISK" in l), None)
        alasan_bawah = "\n".join(lines[alasan_index + 1:]).strip() if alasan_index is not None else ""
        alasan_full = f"{alasan_open}\n\n{alasan_bawah}".strip()

        tp_price = calculate_tp(open_price, sl_price, sinyal_ai)

        # Save to cache
        analysis_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cache_data = {
            'symbol': symbol,
            'timeframe': timeframe.upper(),
            'timestamp': analysis_timestamp,
            'sinyal': sinyal_ai,
            'open': open_price if open_price else 'N/A',
            'sl': sl_price if sl_price else 'N/A',
            'tp': tp_price if tp_price else '?',
            'alasan': alasan_full if alasan_full else "AI tidak memberikan alasan lengkap."
        }
        save_to_cache(cache_key, cache_data)

        print("\r" + " " * 80 + "\r", end="")

        print("\n" + "═"*50)
        print(Fore.YELLOW + f"📈 Analisa: {symbol} [{timeframe.upper()}]")
        print("═"*50)
        print(f"🕒 Waktu Analisa : {analysis_timestamp}")
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
        print("📢 Coba gunakan pair/timeframe lain, atau ulangi login OAuth Codex Anda.")
