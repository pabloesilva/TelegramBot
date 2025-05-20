import asyncio.selector_events
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
import logging, os, asyncio, aiomqtt, ssl
from telegram.ext import ConversationHandler
import aiomysql
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO

token=os.environ["TB_TOKEN"]
autorizados=[int(x) for x in os.environ["TB_AUTORIZADOS"].split(',')]

logging.basicConfig(format='%(asctime)s - TelegramBot - %(levelname)s - %(message)s', level=logging.INFO)

async def publicar_mensaje(context: ContextTypes.DEFAULT_TYPE, topico: str, mensaje):
    client = context.application.bot_data.get("mqtt_client")
    if not client:
        logging.error("MQTT client no disponible en el contexto.")
        return
    top = "2C955830E8133FDE/" + topico
    await client.publish(top, mensaje)

async def sin_autorizacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("intento de conexión de: " + str(update.message.from_user.id))
    await context.bot.send_message(chat_id=update.effective_chat.id, text="no autorizado")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("se conectó: " + str(update.message.from_user.id))
    if update.message.from_user.first_name:
        nombre=update.message.from_user.first_name
    else:
        nombre=""
    if update.message.from_user.last_name:
        apellido=update.message.from_user.last_name
    else:
        apellido=""
    kb = [["temperatura"],["humedad"],["gráfico temperatura"],["gráfico humedad"]]
    await context.bot.send_message(update.message.chat.id, text="Bienvenido al Bot "+ nombre + " " + apellido,reply_markup=ReplyKeyboardMarkup(kb))
    # await update.message.reply_text("Bienvenido al Bot "+ nombre + " " + apellido) # también funciona

async def acercade(update: Update, context):
    await context.bot.send_message(update.message.chat.id, text="Este bot fue creado para dominar el universo.")

async def rele(update: Update, context:ContextTypes.DEFAULT_TYPE): 
    keyboard = [
            [InlineKeyboardButton("Prender", callback_data="1"),
            InlineKeyboardButton("Apagar", callback_data="0"),
    ],]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Seleccione una opción:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    await query.answer()
    if query.data == "0":
        await publicar_mensaje(context,"rele", 0)
        await query.edit_message_text("Apagando relé...")
    elif query.data == "1":
        await publicar_mensaje(context,"rele", 1)
        await query.edit_message_text("Encendiendo relé...")        
    elif query.data == "2":
        await publicar_mensaje(context,"modo", 0)
        await query.edit_message_text("Modo Manual")
    elif query.data == "3":
        await publicar_mensaje(context,"modo", 1)
        await query.edit_message_text("Modo Automatico")

async def modo(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    keyboard = [[
            InlineKeyboardButton("Manual", callback_data="2"),
            InlineKeyboardButton("Automatico", callback_data="3"),
    ],]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Seleccione un modo:", reply_markup=reply_markup)

# inicia la conversación
async def pedir_periodo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ingresa el valor del período en segundos:")
    return 1

# el usuario responde con el valor
async def recibir_periodo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = int(update.message.text)
        await publicar_mensaje(context,"periodo",valor)
        await update.message.reply_text(f"Período recibido: {valor} segundos.")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Por favor, ingresá un número válido.")
    return 1

# /cancelar permite salir del flujo
async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operación cancelada.")
    return ConversationHandler.END

async def pedir_setpoint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ingresa el valor de referencia de temperatura:")
    return 1

async def recibir_setpoint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = int(update.message.text)
        if (valor < 0) or  (valor > 60):
            await update.message.reply_text("Por favor, ingresá un valor coherente.[0-60°C]")
            return 1    
        else:
            await publicar_mensaje(context,"setpoint",valor)
            await update.message.reply_text(f"Setpoint recibido: {valor}°C.")
            return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Por favor, ingresá un número válido.")
    return 1

async def destello (update: Update, context: ContextTypes.DEFAULT_TYPE):
    await publicar_mensaje(context,"destello",1)
    await context.bot.send_animation(update.message.chat.id, "https://media.tenor.com/B2Y36jtHnKwAAAAM/party-lights-night-life.gif")

async def medicion(update: Update, context):
    logging.info(update.message.text)
    sql = f"SELECT timestamp, {update.message.text} FROM mediciones ORDER BY timestamp DESC LIMIT 1"
    conn = await aiomysql.connect(host=os.environ["MARIADB_SERVER"], port=3306,
                                    user=os.environ["MARIADB_USER"],
                                    password=os.environ["MARIADB_USER_PASS"],
                                    db=os.environ["MARIADB_DB"])
    async with conn.cursor() as cur:
        await cur.execute(sql)
        r = await cur.fetchone()
        if update.message.text == 'temperatura':
            unidad = 'ºC'
        else:
            unidad = '%'
        await context.bot.send_message(update.message.chat.id,
                                    text="La última {} es de {} {},\nregistrada a las {:%H:%M:%S %d/%m/%Y}"
                                    .format(update.message.text, str(r[1]).replace('.',','), unidad, r[0]))
        logging.info("La última {} es de {} {}, medida a las {:%H:%M:%S %d/%m/%Y}".format(update.message.text, r[1], unidad, r[0]))
    conn.close()

async def graficos(update: Update, context):
    logging.info(update.message.text)
    sql = f"SELECT timestamp, {update.message.text.split()[1]} FROM mediciones where id mod 2 = 0 AND timestamp >= NOW() - INTERVAL 1 DAY AND sensor_id LIKE '2C955830E8133FDE' ORDER BY timestamp"
    conn = await aiomysql.connect(host=os.environ["MARIADB_SERVER"], port=3306,
                                    user=os.environ["MARIADB_USER"],
                                    password=os.environ["MARIADB_USER_PASS"],
                                    db=os.environ["MARIADB_DB"])
    async with conn.cursor() as cur:
        await cur.execute(sql)
        filas = await cur.fetchall()

        fig, ax = plt.subplots(figsize=(7, 4))

        fecha, var = zip(*filas)

        ax.plot(fecha, var, color='black', linewidth=2)

        ax.grid(True, which='both', color='gray', alpha=0.7)

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45)

        ax.set_title(update.message.text, fontsize=14, verticalalignment='bottom')
        ax.set_xlabel('Hora', fontsize=12)
        if update.message.text.split()[1] == 'temperatura':
            ax.set_ylabel('Temperatura en °C', fontsize=12)
        else: 
            ax.set_ylabel('Humedad en %', fontsize=12)
        plt.tight_layout()

        buffer = BytesIO()
        fig.tight_layout()
        fig.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=buffer)
        buffer.close()
    conn.close()


async def main():
      

    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    tls_context.verify_mode = ssl.CERT_REQUIRED
    tls_context.check_hostname = True
    tls_context.load_default_certs()
    
    async with aiomqtt.Client(
        os.environ["DOMINIO"],
        username=os.environ["MQTT_USR"],
        password=os.environ["MQTT_PASS"],
        port=int(os.environ["PUERTO_MQTTS"]),
        tls_context=tls_context,
    ) as client:  
        logging.info(autorizados)
        application = Application.builder().token(token).build()
        application.bot_data["mqtt_client"] = client
        application.add_handler(MessageHandler((~filters.User(autorizados)), sin_autorizacion))
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CommandHandler('acercade', acercade))
        application.add_handler(CommandHandler('rele', rele))
        application.add_handler(CallbackQueryHandler(button))
        application.add_handler(CommandHandler('modo', modo))
        conv = ConversationHandler(
                entry_points=[CommandHandler('periodo', pedir_periodo)],
                states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_periodo)],},
                fallbacks=[CommandHandler('cancelar', cancelar)],
        )
        application.add_handler(conv)
        
        conv1 = ConversationHandler(
                entry_points=[CommandHandler('setpoint', pedir_setpoint)],
                states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_setpoint)],},
                fallbacks=[CommandHandler('cancelar', cancelar)],
        )
        application.add_handler(conv1)
        application.add_handler(CommandHandler('destello', destello))
        application.add_handler(MessageHandler(filters.Regex("^(temperatura|humedad)$"), medicion))
        application.add_handler(MessageHandler(filters.Regex("^(gráfico temperatura|gráfico humedad)$"), graficos))
            
        async with application:  # Calls `initialize` and `shutdown`
            await application.start()
            await application.updater.start_polling()
            # Start other asyncio frameworks here
            # Add some logic that keeps the event loop running until you want to shutdown
            while True:
                try:
                    await asyncio.sleep(1)
                except Exception: 
            # Stop the other asyncio frameworks here
                    await application.updater.stop()
                    await application.stop()
    
if __name__ == '__main__':
    asyncio.run(main())
