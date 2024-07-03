import telethon

api_id = 1234
api_hash = 'my hash'


Canal_id = 123

client_user = TelegramClient('anon', api_id, api_hash)

async def main():
    async for miembro in client_user.iter_participants(canal):
        registro = {'Usuario' : [miembro.id], 'Nombre': [miembro.first_name], 'Telefono' : [miembro.phone], 'Inicio': ['NaN'], 'Meses': [1], 'Final': ['Nan'], 'Anuncio': [0]}
        df = pd.DataFrame(registro)                    
        df.to_csv('datos.csv', mode='a', index=False, header=False)
    		
with client_user:
    client_user.loop.run_until_complete(main())
