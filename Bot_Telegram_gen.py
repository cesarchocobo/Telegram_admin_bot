from telethon import TelegramClient, Button, events
from telethon import events
import pandas as pd
from datetime import date, datetime, timedelta
import asyncio
import logging
import re

api_id = 12345
api_hash = 'your_hash'
bottoken = 'your_tokken'

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bottoken)
client_myid = TelegramClient('anon', api_id, api_hash)

c_loop = asyncio.Event()



async def main():


    logging.basicConfig(filename='eventlog.log', encoding='utf-8', level=logging.INFO, format='%(asctime)s %(message)s')
    logging.basicConfig()
    myid = await client.get_entity(178289)
    canal = await client.get_entity(00000)
    

    async def renovar(event_reno):
        texto_reno = event_reno.raw_text
        lista_txt = texto_reno.split()
        dfr = pd.read_csv("datos.csv")
        dfr['Usuario'] = dfr['Usuario'].astype('str')
        dfr['Usuario'] = pd.to_numeric(dfr['Usuario'])
        dfr['Final'] = dfr['Final'].astype('str')
        dfr['Final'] = pd.to_datetime(dfr['Final'], format = "%Y-%m-%d")
        if len(lista_txt) != 3:
            await event_reno.reply('Formato no valido. Vuelve a intentarlo')
        else:
            try:
                usuarioid = int(lista_txt[1])
            except ValueError:
                    await event_reno.reply('ID no valido')
            else:
                try:
                    usuario_mes = int(lista_txt[2])
                except ValueError:
                    await event_reno.reply('meses no validos. introduce un número')
                else:
                    if usuarioid not in dfr['Usuario'].values:
                        await event_reno.reply('Usuario no encontrado. Verifica el ID o intenta más tarde')
                    else:
                        usuario_user = await client.get_entity(usuarioid)
                        j = dfr[dfr.Usuario == usuarioid].index.item()
                        dfr.at[j, 'Final'] = dfr.loc[j, 'Final']+ timedelta(days = 30*usuario_mes)
                        dfr.to_csv("datos.csv", index=False)
                        await event_reno.reply('Se renovó a '+ usuario_user.first_name + ' por ' + str(usuario_mes) + ' meses')
        
        dfr = ''



    async def miembroid(event_id):
        texto_id = event_id.raw_text
        lista_id = texto_id.partition('/id ')
        await event_id.reply('Encontré estos id:')
        async for miembro_id in client.iter_participants(canal):
            if miembro_id.last_name is None:
                last = ''
            else:
                last = miembro_id.last_name
            
            if miembro_id.username is None:
                username = ''
            else:
                username = miembro_id.username
            if lista_id[2] in miembro_id.first_name:
                await client.send_message(myid, miembro_id.first_name + ' ' + last + ' usuario: ' + username)
                await client.send_message(myid, str(miembro_id.id))

    async def lista(event_lista):
        await event_lista.reply('Esta es la lista de miembros')
        async for miembro_l in client.iter_participants(canal):
            await client.send_message(myid, miembro_l.first_name)

    async def prueba(event_prueba):
        await client.send_message(myid, 'la prueba se ejecutó con exito')
    
    

    client.add_event_handler(prueba, events.NewMessage(pattern='/prueba'))  
    client.add_event_handler(renovar, events.NewMessage(pattern=re.compile(r'^/renovar'), from_users = myid))
    client.add_event_handler(lista, events.NewMessage(pattern='/lista', from_users = myid))    
    client.add_event_handler(miembroid, events.NewMessage(pattern=re.compile(r'^/id'), from_users = myid))  

    while True:
        await asyncio.sleep(7200)

        client.remove_event_handler(renovar)
        client.remove_event_handler(lista)
        client.remove_event_handler(miembroid)
        client.remove_event_handler(prueba)

        c_loop.clear()
        #Inicializando
        df = pd.read_csv("datos.csv")
        df['Usuario'] = df['Usuario'].astype('str')
        df['Usuario'] = pd.to_numeric(df['Usuario'])
        df['Final'] = df['Final'].astype('str')
        df['Final'] = pd.to_datetime(df['Final'], format = "%Y-%m-%d")
        df['Anuncio'] = df['Anuncio'].astype('str')
        df['Anuncio'] = pd.to_numeric(df['Anuncio'])
        dfd = df

######################################################################
        for usuario in df['Usuario']:        
            i = df[df.Usuario == usuario].index.item()
            kick = await client.get_entity(usuario)
############################# kick ##############        
            if df.loc[i, 'Final'] < datetime.now():
                await client.kick_participant(canal, kick)
                dfd = dfd.drop([i])
                logging.info(str(kick.first_name) + ' fue expulsado. ID: ' + str(kick.id))
                await client.send_message(myid, 'La suscripción de '+ kick.first_name + ' terminó')
######################## Anuncio #########
            if df.loc[i, 'Final'] < datetime.now() + timedelta(days = 3) and df.loc[i, 'Anuncio'] == 0:
                dfd.at[i, 'Anuncio'] = 1
                
                await client_myid.start()
                await client_myid.send_message(kick, 'Tu suscripcion a termina en 3 dias')
                await client_myid.disconnect()

                await client.send_message(myid, 'La suscripción de '+ kick.first_name + ' termina en 3 dias')
                logging.info(str(kick.first_name) + 'fue avisado. ID: ' +  str(kick.id))
        df = dfd
        df.to_csv("datos.csv", index=False)

       



        async for miembro in client.iter_participants(canal):
            c_loop.clear()
            if miembro.id not in df['Usuario'].values :
                nuevo = miembro
                await client.send_message(myid, nuevo.first_name + ' se ha unido al canal. ¿Por cuántos meses?')
                logging.info('Se detectó a ' + str(nuevo.first_name) + ' como nuevo miembro. ID: ' + str(nuevo.id))

                @client.on(events.NewMessage())
                async def nuevo_ing(event):
                    
                    try:
                        mes = int(event.raw_text)
                    except ValueError:
                        await event.reply('Por favor, introduce un número')
                    else:
                        registro = {'Usuario': [nuevo.id], 'Nombre' : [nuevo.first_name], 'Telefono' : [nuevo.phone], 'Inicio': [date.today()], 'Meses' : [mes], 'Final' : [date.today() + timedelta(days = 30*mes)], 'Anuncio' : [0]}
                        df2 = pd.DataFrame(registro)                    
                        df2.to_csv('datos.csv', mode='a', index=False, header=False)
                        logging.info('Se agregó con exito a ' + nuevo.first_name + ' por una duracion de ' + str(mes) + ' meses. ID: ' + str(nuevo.id))
                        await event.reply('Se agregó a ' + nuevo.first_name + ' por ' + event.raw_text + ' meses')
                        client.remove_event_handler(nuevo_ing)
                        c_loop.set()

                await c_loop.wait()

        client.add_event_handler(prueba, events.NewMessage(pattern='/prueba'))  
        client.add_event_handler(renovar, events.NewMessage(pattern=re.compile(r'^/renovar'), from_users = myid))
        client.add_event_handler(lista, events.NewMessage(pattern='/lista', from_users = myid))    
        client.add_event_handler(miembroid, events.NewMessage(pattern=re.compile(r'^/id'), from_users = myid))  




with client:
    client.loop.create_task(main())
    client.run_until_disconnected()