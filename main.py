import os
import json
import telebot
from telebot import types
from settings import TOKEN

bot = telebot.TeleBot(TOKEN)
data_dct = dict()

def load_json(folder_name, file_name):
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
    filename = os.path.join(folder_name, file_name)
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            json.dump(dict(), f, ensure_ascii=True)
    with open(filename, encoding="utf-8") as f:
        load_dct = json.load(f)
    return load_dct

def save_json(folder_name, file_name, save_dct):
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
    filename = os.path.join(folder_name, file_name)
    with open(filename, "w") as f:
        json.dump(save_dct, f, ensure_ascii=False, indent=4)

def logging(message, *args, **kwargs):
    fnc = kwargs.get('fnc', '')
    call = kwargs.get('call', '')
    if not os.path.exists('cache'):
        os.mkdir('cache')
    with open('cache/user.log', '+a') as f:
        f.write(f'{message.date};{message.id};{message.from_user.id};{fnc};{message.text};{call}\n')

def register(user_id, key, value):
    user_json = load_json('cache', 'user.json')
    user_json.setdefault(str(user_id), dict())
    user_json[str(user_id)][key] = value
    save_json('cache', 'user.json', user_json)

def get_user(user_id):
    user_json = load_json('cache', 'user.json')
    return user_json.get(str(user_id))

@bot.message_handler(content_types=['text'])
def start(message):
    logging(message, fnc='start')
    if message.text == '/reg':
        bot.send_message(message.from_user.id, "Как тебя зовут?")
        bot.register_next_step_handler(message, get_name)
    else:
        bot.send_message(message.from_user.id, 'Напиши /reg')

def get_name(message):
    logging(message, fnc='get_name', name=message.text)
    register(message.from_user.id, 'name', message.text)

    bot.send_message(message.from_user.id, 'Какая у тебя фамилия?')
    bot.register_next_step_handler(message, get_surname)

def get_surname(message):
    logging(message, fnc='get_surname', surname=message.text)
    register(message.from_user.id, 'surname', message.text)

    bot.send_message(message.from_user.id, 'Сколько тебе лет?')
    bot.register_next_step_handler(message, get_age)

def get_age(message):
    logging(message, fnc='get_surname', surname=message.text)
    register(message.from_user.id, 'age', message.text)
    user_dct = get_user(message.from_user.id)
    age = user_dct['age']
    name = user_dct['name']
    surname = user_dct['surname']

    kb = types.InlineKeyboardMarkup()
    k_yes = types.InlineKeyboardButton(text='да', callback_data= 'yes')
    kb.add(k_yes)
    k_no = types.InlineKeyboardButton(text='нет', callback_data='no')
    kb.add(k_no)
    msg = f'Тебе {age} лет. Тебя зовут {name} {surname}'
    bot.send_message(message.from_user.id, msg, reply_markup=kb)

@bot.callback_query_handler(func = lambda call: True)
def callback_worker(call):
    logging(call.message, fnc='callback_worker', call=call.data)
    if call.data == 'yes':
        bot.send_message(call.message.chat.id, 'Хорошо, приятно познакомиться!')
    elif call.data == 'no':
        bot.send_message(call.message.chat.id, 'Странно, напишите: /reg')

if __name__ == "__main__":
    bot.polling(none_stop=True, interval=0)