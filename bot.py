from subprocess import Popen, PIPE
from multiprocessing import Process
import psutil
import telegram
from telegram.ext import CommandHandler, Updater, MessageHandler, Filters
import os


def authenticate_decorator(func):
    def wrapper(update, context):
        if update.effective_chat.id == admin_id:
            func(update, context)

    return wrapper


def status():
    for line in proc.stdout:
        bot.send_message(chat_id=admin_id, text=line.decode('utf-8'))


@authenticate_decorator
def start_server(update, context):
    global proc
    proc = Popen('java -Xmx{}M -Xms1024M -jar server.jar nogui'.format(int(os.environ.get('MAX_MEMORY'))),
                 shell=True, stdin=PIPE, stdout=PIPE)
    global status_process
    status_process.start()


@authenticate_decorator
def stop_server(update, context):
    global proc
    proc.stdin.write(b'/stop\n')
    proc.stdin.close()
    proc.stdout.close()
    global status_process
    status_process.join()
    proc = None


@authenticate_decorator
def custom_command(update, context):
    global proc
    proc.stdin.write((update.message.text + '\n').encode('utf-8'))
    proc.stdin.flush()


@authenticate_decorator
def server_load_info(update, context):
    load_res_string = 'INFO\nCPU load {} %\nMemory used {} %'.format(psutil.cpu_percent(interval=0.1),
                                                                     psutil.virtual_memory().percent)

    context.bot.send_message(chat_id=update.effective_chat.id, text=load_res_string)


proc = None
status_process = Process(target=status)
my_token = os.environ.get('API_KEY')
admin_id = int(os.environ.get('ADMIN_ID'))
# api key and admin id in environmental variable
bot = telegram.Bot(token=my_token)
updater = Updater(token=my_token, use_context=True)
dispatcher = updater.dispatcher

start_server_handler = CommandHandler('server_start', start_server)
dispatcher.add_handler(start_server_handler)
server_stop_handler = CommandHandler('server_stop', stop_server)
dispatcher.add_handler(server_stop_handler)
stop_handler = CommandHandler('stop', stop_server)
server_load_info_handler = CommandHandler('server_load_info', server_load_info)
dispatcher.add_handler(server_load_info_handler)
users_command_handler = MessageHandler(Filters.command, custom_command)
dispatcher.add_handler(users_command_handler)
updater.start_polling()
