import os

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TV_USER = os.getenv('TV_USER')
TV_PASS = os.getenv('TV_PASS')

required = {
    'OPENAI_API_KEY': OPENAI_API_KEY,
    'TV_USER': TV_USER,
    'TV_PASS': TV_PASS,
}
missing = [name for name, value in required.items() if not value]
if missing:
    missing_vars = ', '.join(missing)
    raise EnvironmentError(f"Missing required environment variable(s): {missing_vars}")

