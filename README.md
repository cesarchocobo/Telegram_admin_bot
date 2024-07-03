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

