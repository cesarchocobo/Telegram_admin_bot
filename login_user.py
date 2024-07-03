from telethon import TelegramClient

# Use your own values from my.telegram.org
api_id = 12345
api_hash = '0123456789abcdef0123456789abcdef'

# The first parameter is the .session file name (absolute paths allowed)
with TelegramClient('anon', api_id, api_hash) as client:
    client.loop.run_until_complete(client.send_message('me', 'Hola yo'))
