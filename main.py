import telebot
from telebot import types

from settings import TOKEN

bot = telebot.TeleBot(TOKEN)

name = ''
surname = ''
age = 0

@bot.message_handler(content_types=['text'])
def start(message):
    if message.text == '/reg':
        bot.send_message(message.from_user.id, "Как тебя зовут?")
        bot.register_next_step_handler(message, get_name)
    else:
        bot.send_message(message.from_user.id, 'Напиши /reg')

def get_name(message):
    global name
    name = message.text
    bot.send_message(message.from_user.id, 'Какая у тебя фамилия?')
    bot.register_next_step_handler(message, get_surname)

def get_surname(message):
    global surname
    surname = message.text
    bot.send_message(message.from_user.id, 'Сколько тебе лет?')
    bot.register_next_step_handler(message, get_age)

def get_age(message):
    global age
    age = str(message.text)
    kb = types.InlineKeyboardMarkup()
    k_yes = types.InlineKeyboardButton(text='да', callback_data= 'yes')
    kb.add(k_yes)
    k_no = types.InlineKeyboardButton(text='нет', callback_data='no')
    kb.add(k_no)
    bot.send_message(message.from_user.id, 'Тебе ' + str(age) + ' лет, тебя зовут ' + str(name) + ' ' + str(surname), reply_markup=kb)

@bot.callback_query_handler(func = lambda call: True)
def callback_worker(call):
    global age
    if call.data == 'yes':
        bot.send_message(call.message.chat.id, 'Хорошо, приятно познакомиться!')
    elif call.data == 'no':
        bot.send_message(call.message.chat.id, 'Странно, напишите: /reg')
    age = 0



if __name__ == "__main__":
    bot.polling(none_stop=True, interval=0)