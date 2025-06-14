import os
from credentials import load_credentials, save_credentials

_creds = load_credentials()

OPENAI_API_KEY = _creds.get('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY')
TV_USER = _creds.get('TV_USER') or os.getenv('TV_USER')
TV_PASS = _creds.get('TV_PASS') or os.getenv('TV_PASS')

required = {
    'OPENAI_API_KEY': OPENAI_API_KEY,
    'TV_USER': TV_USER,
    'TV_PASS': TV_PASS,
}

missing = [name for name, value in required.items() if not value]
if missing:
    for name in missing:
        required[name] = input(f'Enter {name}: ').strip()
    save_credentials(required)

OPENAI_API_KEY = required['OPENAI_API_KEY']
TV_USER = required['TV_USER']
TV_PASS = required['TV_PASS']
