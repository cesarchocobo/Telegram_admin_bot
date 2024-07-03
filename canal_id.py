import telethon

api_id = 1234
api_hash = 'my hash'


Canal_id = None

client_user = TelegramClient('anon', api_id, api_hash)

async def main():
	async for chats in tg.client.iter_dialogs():
    		if chats.name == "nombre del canal":
	        	Canal_id = chats.id
	        	break
	
	if Canal_id is None:
	    print("No hay chat")
	else:
	    print("el id es:", Canal_id)
    
with client_user:
    client_user.loop.run_until_complete(main())
