# Telegram_admin_bot

Simple script para controlar un bot de telegram que administre tu canal de suscriptores.

Es común que la gente tenga canales privados de telegram donde cobra una suscripción y pone contenido exclusivo para sus suscriptores, Aunque hay otras plataformas similares, muchos prefieren canales de telegram, pero muchos deben estar montanteando las suscripciones manualmente, así que se me ocurrió hacer este script para que un bot administre estas suscripciones. aunque quizá le pude haber puesto un mejor nombre.

Lo primero que se necesita es una cuenta en telegram y crear credenciales para acceder a la API de Telegram. Se puede obtener más información en https://core.telegram.org/api/obtaining_api_id

También hay que crear un bot, para esto, debemos escribirle al padre de los bots en Telegram, osea a @BotFather. Mas información en https://core.telegram.org/bots/tutorial

una vez que se tienen las credenciales, es decir, el api_id, el api_hash y el bot tokken (No hay que compartir estas claves ya que cualquiera que las tenga puede acceder y controlar a tu bot y cuenta y app de Telegram) ya podemos empezar a pensar que queremos que haga el bot.

## Concepto

Ok, la idea es simple. Tenemos un canal de Telegram y queremos gestionar quien entra y sale del canal. Hay tres formas de agregar a alguien a un canal:
* Añadirlos directamente desde la configuración del canal de Telegram
* Añadirlos mediante un enlace estático
* Añadirlos mediante un enlace dinámico

No me quiero meter con la form en la que cada quien añade gente a sus canales, puede ser que sean conocidos, gente random en internet, o que se yo, asi que el bot no va a agregar gente, . Despues puedo hacer otro script que se dedique a eso, pero por el momento, sigamosle dejando ese trabajo al dueño del canal.

Lo que sí quiero ahorrarle es el tener que estar acordándose cuando se le acaba la suscripción a cada quien. Para esto, necesitamos una base de datos donde se guarden los miembros del canal y el tiempo de sus suscripción. Usare un archivo csv para esto, que será datos.csv. El archivo que encuentran en github tiene datos generados aleatoriamente, solo para fines demostrativos, en la practica, se tendrán que usar los datos de un canal de verdad.

Lo que necesitamos que haga el bot es que revise todos los días si es que a alguien se le venció la suscripción y si es el caso, lo expulsa del canal. Voy a añadir las siguientes funcionalidades extra:
* El bot puede proporcionar una lista de miembros del canal en el chat de Telegram
* El bot puede obtener el ID de usuario de los miembros (más sobre esto despues)
* El bot puede renovar la suscripción de los usuarios.

Ademas, vamos a añadir una uncion para notificar a los usuarios que su suscripcion está proxima a vencer.

Ya con la idea de que queremos hacer, podemos empezar a configurar nuestro bot

# The setup

Primero que nada, necesitamos instalar una libreria que nos permita interactuar con la API de Telegram. Utilizaré la libretia de Telethon para python: https://docs.telethon.dev/en/stable/index.html#

crearemos un espacio virtual de python para no generar ningún conflicto con librerías que tengamos en el sistema u otros proyectos. En este espacio virtual podemos instalar telethon mediante pip.
Va a ser necesario gestionar una base de datos, en este caso, el archivo csv. asi que usaré la libreria de pandas. Al principio crei que usar pandas para esto era como matar moscas a cañonazos, pero despues pensé que es posible que alguien tenga millones de suscriptores, en este caso, pandas suena como la opción ideal. Tambien debemos instalar pandas en nuestro espacio virtual.

Para que el bot pueda interactuar con nuestro canal, debemos agregarlo como administrador al canal y necesitamos el id del canal. ¿Como obtenemos esto? primero vamos a iniciar sesion en Telegram con nuestras credenciales para poder interactuar con la API, para esto, seguimos el script que viene en la documentacion de tehethon. Este script es login_user.py. Este script genera un archivo con extension .session, que es el que va a guardar la informacion de inicio de sesion, para que no tengamos que estar poniendo codigos cada que corramos el script del bot. no debe renombrarse ni cambiarse de ubicacion.

Ahora sí, para obtener el id del canal, suponiendo que somos miembros de nuestro propio canal, podemos correr el script canal_id.py para obtener el ide de nuestro canal en pantalla, de aqui podemos guardarlo en algun otro lugar. Tambien podriamos implementar este script al principio del bot si queremos automatizar aun más el proceso, pero yo lo dejé aparte.

Si el canal ya está hecho, debemos crear la base de datos de los usuarios ya existentes. Aqui sí se tendra que poner a mano las fechas de finalizacion de las suscripciones que ya se tienen, pero a partir de aqui, para los demas miembros que se unan será un poco más facil administrarlos on ayuda del bot. Para crear la base de datos hice el script create_db.py. Notese que las columnas de la base de datos incluyen el id del usuario (identiicador unico de telegram), la fecha en la que se unio el miembro al canal, los meses que se unió, la fecha de finalización y una llamada "Anuncio" que va a contener 0 o 1 y servira como un flag para saver si ya se le notificó a ese usuario que su suscripcion está por terminar.

ya con los archivos de sesión, la base de datos creada y acceso al canal mediante el bot, podemos empezar a escribir el código


# The code

importamos las paqueterias que se van a utilizar

```
from telethon import TelegramClient, events
import pandas as pd
from datetime import date, datetime, timedelta
import asyncio
import logging
import re
```

La paqueteria asyncio se utiliza para controlar elementos del loop ya que telethon es una libreria asincronica. logging se utiliza para crear un registro de los eventos importantes del bot como cuando se elimina a algun miembro.


La primera parte del código es iniciar el cliente de Telegram para poder comunicarnos con la API. Se incian tranto el bot como la cuenta del usuario. Este ultimo para poder mandar avisos ya que un bot no puede iniciar conversaciones con usuarios (por politicas de telegram)

```
api_id = 12345
api_hash = 'your_hash'
bottoken = 'your_tokken'

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bottoken)
client_myid = TelegramClient('anon', api_id, api_hash)
```
Defino una variable c_loop como un evento de asyncio que será utilizada despues para controlar el loop.

```
c_loop = asyncio.Event()

```

la funcion principal main() debe ser definida como asincronica

```
async def main():
```

dentro de la funcion main() empezamos por definir el canal y el usuario que enviara los mensajes de aviso mediante su ID. tambien arrancamos el log con la primera linea

```
    logging.basicConfig(filename='eventlog.log', encoding='utf-8', level=logging.INFO, format='%(asctime)s %(message)s')
    logging.basicConfig()
    myid = await client.get_entity(178289)
    canal = await client.get_entity(00000)
```

El primer comando que vamos a definir es el de renovacion. En esta funcion el usuario envía un comando al bot junto con un ID y el numero de meses que se renovará la suscripcion al usuario. El codigo primero guarda el mensaje recibido con el comando y lo separa en tres partes. despues, que hace es crear un dataframe con pandas, editarlo con los tipos de dato adecuados para la columna de "Usuario" y "Final". Antes de trabajar con el comando ingresado necesitamos verificar que tiene un formato adecuado, de esto nos encargamos con varias funciones if anidadas. Una vez que sabemos que el comando está bien, comparamos el ID dado con la base de datos para encontrar cual registro hay que actualizar, lo actualizamos con el comando dfr.at. Avisamos al que envió el comando que el usuario se renovó y finalmente editamos el archivo csv para guardar los cambios y borramos el dataframe para ahorrar memoria.

```
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

```
para renovar a un usuario hay que enviar al bot una cadena de texto como la siguiente:

/renovar 1893632894 3

donde la primera palabra /renovar le dice al bot que queremos renovar a un miembro, el segundo numero es el ID del miembro a renovar y el tercero es el numero de meses que se va a renovar.


Para renovar necesitamos conocer el ID, asi que ponemos otro comando para obtener los id. En esta funcion, lo que se hace es guardar el texto del comando enviado, despues squitar el comando "/id" del resto del texto. Posteriormente se itera sobre todos los miembros del canal, cuando se encuentra uno que contiene la cadena de texto del comando enviado (menos "id") se envia un mensaje con el nombre del usuario y despues otro con su ID, esto lo va a hacer para todos los usuarios que encuentre que contengan la cadena de texto enviada, asi que funciona como una busqueda.

Los sirven para poder mostrar más informacion del miembro como su apellido y nombre de usuario. No todos los usuarios de telegram tienen estos campos, asi que debemos verificar si los tienen o no para poder escribirlos en el mensaje, si no tienen, esa variable es None.

```
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

```

El comando a mandar tiene la forma 

\id nombre


La tercer función que añadí es una opcio para obtener la lista de miembros del canal. Ahora que lo pienso, esta lista puede ser muy larga y el bot te va a enviar quizá cientos o miles de mensajes, asi que hay que usar esta opcion con cuidado. el comandop es /lista

```
    async def lista(event_lista):
        await event_lista.reply('Esta es la lista de miembros')
        async for miembro_l in client.iter_participants(canal):
            await client.send_message(myid, miembro_l.first_name)
```

Finalmente, deje un comando para probar si el bot está en linea. implemente te contesta con una frase cuando recibe el comando /prueba

```
    async def prueba(event_prueba):
        await client.send_message(myid, 'la prueba se ejecutó con exito')
```

Todas estas funciones estan bien, pero hasta el momento no le hemos dicho al bot cuando activarlas, para esto debemos añadir los handlers al cliente de telegram usando regex para indicar como deben ser las entradas de texto para iniciar las funciones

```
    client.add_event_handler(prueba, events.NewMessage(pattern='/prueba'))  
    client.add_event_handler(renovar, events.NewMessage(pattern=re.compile(r'^/renovar'), from_users = myid))
    client.add_event_handler(lista, events.NewMessage(pattern='/lista', from_users = myid))    
    client.add_event_handler(miembroid, events.NewMessage(pattern=re.compile(r'^/id'), from_users = myid))  

```

Elegí iniciar los handlers así en lugar de usar el adorno @ para el cliente de telegram por que más adelante vamos a necesitar quitar los handlers y volverlos a activar para evitar conflictos con la base de datos.

Ahora empieza el loop de la funcion main. Este loop es el que va a revisar periodicamente si algun miembro debe eliminarse o si uno nuevo a entrado al canal. Quiero ahorrar en CPU y evitar que comandos se envien cuando se esta sobre escribiendo la base de datos con estos nuevos registros, asi que este loop se va a correr cada dos horas, por eso empezamos con la funcion wait de asyncio y quitamos los handlers de los comandos definidos antes. tambien ponemos el evento c_loop como no iniciado.

```
        await asyncio.sleep(7200)

        client.remove_event_handler(renovar)
        client.remove_event_handler(lista)
        client.remove_event_handler(miembroid)
        client.remove_event_handler(prueba)

        c_loop.clear()
```

Empezamos cargando la base de datos en memoria con un dataframe. Como se va a iterar sobre este dataframe no quiero editarlo dentro de las iteraciones, asi que lo copio definiendo un segundo dataframe que será el que se va a editar.

```
        df = pd.read_csv("datos.csv")
        df['Usuario'] = df['Usuario'].astype('str')
        df['Usuario'] = pd.to_numeric(df['Usuario'])
        df['Final'] = df['Final'].astype('str')
        df['Final'] = pd.to_datetime(df['Final'], format = "%Y-%m-%d")
        df['Anuncio'] = df['Anuncio'].astype('str')
        df['Anuncio'] = pd.to_numeric(df['Anuncio'])
        dfd = df
```

Primero converti los datos de tipo object a tipo string y despues a sus respectivos tipos adecuados como numeric y datetime. esto por que tuve problemas convirtiendolos directamente a numeic y datetime.


Inicia la iteracion sobre los miembros registrados en la base de datos y obtenemos las entidades (los usuarios de telegram) de nuestra base de datos

```
        for usuario in df['Usuario']:        
            i = df[df.Usuario == usuario].index.item()
            kick = await client.get_entity(usuario)
```

Comprobamos si a alguien ya se le passo la fecha y si es así, lo sacamos el canaly actualizamos el dataframe para quitar ese registro

```
            if df.loc[i, 'Final'] < datetime.now():
                await client.kick_participant(canal, kick)
                dfd = dfd.drop([i])
                logging.info(str(kick.first_name) + ' fue expulsado. ID: ' + str(kick.id))
                await client.send_message(myid, 'La suscripción de '+ kick.first_name + ' terminó')
```
Despues, revisamos si alguien está proximo a vencerse, en este caso puse tres dias, pero se puede cambiar al tiempo deseado. Cuando el programa detecta que le faltan tres dias a un miembro, le manda un aviso desde la cuenta del usuario (no desde el bot), asi que debemos inicializar el cliente del usuario. Despues, modifica su entrada en "Anuncio" de 0 a 1, para saber que ese usuario ya fue notificado y que no le vuelva a notificar (para esto era esa columna). Finalmente actualizamos la base de datos.


```
            if df.loc[i, 'Final'] < datetime.now() + timedelta(days = 3) and df.loc[i, 'Anuncio'] == 0:
                dfd.at[i, 'Anuncio'] = 1
                
                await client_myid.start()
                await client_myid.send_message(kick, 'Tu suscripcion a termina en 3 dias')
                await client_myid.disconnect()

                await client.send_message(myid, 'La suscripción de '+ kick.first_name + ' termina en 3 dias')
                logging.info(str(kick.first_name) + 'fue avisado. ID: ' +  str(kick.id))
        df = dfd
        df.to_csv("datos.csv", index=False)
```

La siguiente parte del loop va a revisar si hay nuevos miembros añadidos, es decir, miembors que se hayan unido al canal pero que no los tengamos en la base de datos

```
        async for miembro in client.iter_participants(canal):
            c_loop.clear()
            if miembro.id not in df['Usuario'].values :
                nuevo = miembro
                await client.send_message(myid, nuevo.first_name + ' se ha unido al canal. ¿Por cuántos meses?')
                logging.info('Se detectó a ' + str(nuevo.first_name) + ' como nuevo miembro. ID: ' + str(nuevo.id))
```

Si se detecta un nuevo usuario, el bot le envía un mensaje al administrador diciendole que un nuevo miembro se añadio al canal y pregunta por cuantos meses. En este punto, se inicia un nuevo handler, está vez sí con el adorno @, este handler va a estar a la espera de que el aministrador envíe un número indicando por cuantos meses se unió este miembro, como los demas handlers están deshabilitados, este es el unico handler activo, lo que significa que el boto no recibira ningun comando hasta que el administrador especifique cuantos meses se unió este miembro.

```
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
```
Notese tambien la ultima linea de este código, contiene la funcion `c_loop.wait()`. Esto pausa el loop hasta que la variable c_loop cambie a puesta, lo que se hace con la funcion `c_loop.set()`. Esto quiere decir que el loop queda pausado hasta que el administrador envíe el numero de meses del nuevo registro. Hice esto para que la base de datos no se este sobreescribiendo en paralelo y gener conflictos o perdidas de información.

Una vez que el administrador envío el numero de meses se reanuda el loop. Al final del loop, volvemos a activar los handlers de los comandos

```
        client.add_event_handler(prueba, events.NewMessage(pattern='/prueba'))  
        client.add_event_handler(renovar, events.NewMessage(pattern=re.compile(r'^/renovar'), from_users = myid))
        client.add_event_handler(lista, events.NewMessage(pattern='/lista', from_users = myid))    
        client.add_event_handler(miembroid, events.NewMessage(pattern=re.compile(r'^/id'), from_users = myid))  
```

Finalmente añadimos el task asincronico de la funcion main() y pedimos que el bot corra hasta que se desconecte. Como no hay ninguna linea que obligue la desconeccion, el bot correra para siempre.

```
with client:
    client.loop.create_task(main())
    client.run_until_disconnected()
```

# Funcionamiento

Se pueden agregar miembros al canal de cualquier manera, este bot va a escanear cada dos horas si hay nuevos miembros o si hay que expulsar otros. Los posibles comandos son
* /renovar numero_id numero_meses
  Renueva al miembro del canal con id numero_id por la cantidad de meses numero_meses   
* /id 'nombre'
  Busca los miembros cuyos nombres contengan 'nombre' y envía un mensaje al administrador con los nombres que encontró y sus id. S no se especifica nombre se envíaran los id de todos los miembros del canal.
* /lista
  Envía una lista con los miembros del canal
* /prueba
  envía un mensaje simple, sirve para saber si el bot está en linea

El script debe correr en una computadora que siempre este prendida y tenga python 3. Lo he provado con las versiones 3.10 y 3.11. Esta maquina puede ser un servidro o alguna computadora que siempre tengan prendida, como una raspberry pi.  el archivo eventlog.log ira guardando un registro de las acciones que se toman para tenerlo como referencia.

  
