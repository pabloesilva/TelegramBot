from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
import logging, os, asyncio
import paho.mqtt.client as mqtt
from telegram.ext import ConversationHandler

token=os.environ["TB_TOKEN"]
autorizados=[int(x) for x in os.environ["TB_AUTORIZADOS"].split(',')]

logging.basicConfig(format='%(asctime)s - TelegramBot - %(levelname)s - %(message)s', level=logging.INFO)

global top, client 
ESPERANDO_SETPOINT=1
ESPERANDO_PERIODO=1

async def publicar_mensaje(topico, mensaje):
    global client
    global top
    top="2C955830E8133FDE/"+topico
    client.publish(top, mensaje)

async def sin_autorizacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("intento de conexión de: " + str(update.message.from_user.id))
    await context.bot.send_message(chat_id=update.effective_chat.id, text="no autorizado")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(update)
    logging.info("se conectó: " + str(update.message.from_user.id))
    if update.message.from_user.first_name:
        nombre=update.message.from_user.first_name
    else:
        nombre=""
    if update.message.from_user.last_name:
        apellido=update.message.from_user.last_name
    else:
        apellido=""
    await context.bot.send_message(update.message.chat.id, text="Bienvenido al Bot "+ nombre + " " + apellido)
    # await update.message.reply_text("Bienvenido al Bot "+ nombre + " " + apellido) # también funciona

async def acercade(update: Update, context):
    await context.bot.send_message(update.message.chat.id, text="Este bot fue creado para dominar el universo.")

async def rele(update: Update, context:ContextTypes.DEFAULT_TYPE): 
    keyboard = [
            [InlineKeyboardButton("Prender", callback_data="0"),
            InlineKeyboardButton("Apagar", callback_data="1"),
    ],]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Seleccione una opción:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    await query.answer()
    if query.data == "0":
        await publicar_mensaje("rele", 0)
        await query.edit_message_text("Apagando relé...")
    elif query.data == "1":
        await publicar_mensaje("rele", 1)
        await query.edit_message_text("Encendiendo relé...")        
    elif query.data == "2":
        await publicar_mensaje("modo", 0)
        await query.edit_message_text("Modo Manual")
    elif query.data == "3":
        await publicar_mensaje("modo", 1)
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
    return ESPERANDO_PERIODO

# el usuario responde con el valor
async def recibir_periodo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = int(update.message.text)
        await publicar_mensaje("periodo",valor)
        await update.message.reply_text(f"Período recibido: {valor} segundos.")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Por favor, ingresá un número válido.")
    return ESPERANDO_PERIODO

# /cancelar permite salir del flujo
async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operación cancelada.")
    return ConversationHandler.END

async def pedir_setpoint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ingresa el valor de referencia de temperatura:")
    return ESPERANDO_SETPOINT

async def recibir_setpoint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = int(update.message.text)
        if (valor < 0) or  (valor > 60):
            await update.message.reply_text("Por favor, ingresá un valor coherente.[0-60°C]")
            return ESPERANDO_SETPOINT    
        else:
            await publicar_mensaje("setpoint",valor)
            await update.message.reply_text(f"Setpoint recibido: {valor}°C.")
            return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Por favor, ingresá un número válido.")
    return ESPERANDO_SETPOINT

async def destello (update: Update, context: ContextTypes.DEFAULT_TYPE):
    await publicar_mensaje("destello",1)
    await context.bot.send_animation(update.message.chat.id, "https://media.tenor.com/B2Y36jtHnKwAAAAM/party-lights-night-life.gif")

def main():
    
    global client
    
    client = mqtt.Client()
    client.username_pw_set(os.environ["MQTT_USR"], os.environ["MQTT_PASS"])
    client.tls_set()
    client.connect(os.environ["DOMINIO"], int(os.environ["PUERTO_MQTTS"]))

    client.publish("topico/ejemplo", "Hola desde el bot")
    
    logging.info(autorizados)
    application = Application.builder().token(token).build()
    application.add_handler(MessageHandler((~filters.User(autorizados)), sin_autorizacion))
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('acercade', acercade))
    application.add_handler(CommandHandler('rele', rele))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler('modo', modo))
    conv = ConversationHandler(
            entry_points=[CommandHandler('periodo', pedir_periodo)],
            states={ESPERANDO_PERIODO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_periodo)],},
            fallbacks=[CommandHandler('cancelar', cancelar)],
    )
    application.add_handler(conv)
    
    conv1 = ConversationHandler(
            entry_points=[CommandHandler('setpoint', pedir_setpoint)],
            states={ESPERANDO_SETPOINT: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_setpoint)],},
            fallbacks=[CommandHandler('cancelar', cancelar)],
    )
    application.add_handler(conv1)
    application.add_handler(CommandHandler('destello', destello))
    
    application.run_polling()
    
if __name__ == '__main__':
    main()
