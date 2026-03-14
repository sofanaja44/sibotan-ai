import os
from credentials import load_credentials, save_credentials

_creds = load_credentials()

OPENAI_API_KEY = _creds.get('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY')
OPENAI_OAUTH_TOKEN = _creds.get('OPENAI_OAUTH_TOKEN') or os.getenv('OPENAI_OAUTH_TOKEN')
OPENAI_AUTH_MODE = (_creds.get('OPENAI_AUTH_MODE') or os.getenv('OPENAI_AUTH_MODE') or '').strip().lower()
TV_USER = _creds.get('TV_USER') or os.getenv('TV_USER')
TV_PASS = _creds.get('TV_PASS') or os.getenv('TV_PASS')

if OPENAI_AUTH_MODE not in {'', 'api_key', 'oauth'}:
    OPENAI_AUTH_MODE = ''

if OPENAI_AUTH_MODE == 'oauth':
    OPENAI_TOKEN = OPENAI_OAUTH_TOKEN
elif OPENAI_AUTH_MODE == 'api_key':
    OPENAI_TOKEN = OPENAI_API_KEY
else:
    OPENAI_TOKEN = OPENAI_OAUTH_TOKEN or OPENAI_API_KEY
    OPENAI_AUTH_MODE = 'oauth' if OPENAI_OAUTH_TOKEN else 'api_key'

required = {
    'OPENAI_TOKEN': OPENAI_TOKEN,
    'TV_USER': TV_USER,
    'TV_PASS': TV_PASS,
}

missing = [name for name, value in required.items() if not value]
if missing:
    for name in missing:
        if name == 'OPENAI_TOKEN':
            auth_mode_input = input('Choose OpenAI auth mode (api_key/oauth) [oauth]: ').strip().lower()
            auth_mode = auth_mode_input if auth_mode_input in {'api_key', 'oauth'} else 'oauth'
            token_prompt = 'Enter OPENAI_OAUTH_TOKEN: ' if auth_mode == 'oauth' else 'Enter OPENAI_API_KEY: '
            token_value = input(token_prompt).strip()
            required['OPENAI_TOKEN'] = token_value
            _creds['OPENAI_AUTH_MODE'] = auth_mode
            if auth_mode == 'oauth':
                _creds['OPENAI_OAUTH_TOKEN'] = token_value
            else:
                _creds['OPENAI_API_KEY'] = token_value
            continue

        required[name] = input(f'Enter {name}: ').strip()
        _creds[name] = required[name]

    if 'OPENAI_AUTH_MODE' not in _creds:
        _creds['OPENAI_AUTH_MODE'] = OPENAI_AUTH_MODE

    if _creds.get('OPENAI_AUTH_MODE') == 'oauth' and 'OPENAI_OAUTH_TOKEN' not in _creds:
        _creds['OPENAI_OAUTH_TOKEN'] = required['OPENAI_TOKEN']
    elif _creds.get('OPENAI_AUTH_MODE') == 'api_key' and 'OPENAI_API_KEY' not in _creds:
        _creds['OPENAI_API_KEY'] = required['OPENAI_TOKEN']

    _creds['TV_USER'] = required['TV_USER']
    _creds['TV_PASS'] = required['TV_PASS']
    save_credentials(_creds)

OPENAI_API_KEY = _creds.get('OPENAI_API_KEY')
OPENAI_OAUTH_TOKEN = _creds.get('OPENAI_OAUTH_TOKEN')
OPENAI_AUTH_MODE = _creds.get('OPENAI_AUTH_MODE', OPENAI_AUTH_MODE)
OPENAI_TOKEN = required['OPENAI_TOKEN']
TV_USER = required['TV_USER']
TV_PASS = required['TV_PASS']
