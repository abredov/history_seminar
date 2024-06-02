import datetime
import settings
import telebot
import random
import utils

bot = telebot.TeleBot(settings.token)


def get_theme_name():
    ww1_dct = utils.read_data("data", "world_war_one.json")
    button_lst = list()
    for key in ww1_dct.keys():
        button_lst.append(key)
    return button_lst


def get_tests_name(theme):
    ww1_dct = utils.read_data("data", "world_war_one.json")[theme]
    button_lst = list()
    for key in ww1_dct.keys():
        button_lst.append(key)
    return button_lst


def get_question(*args):
    """
    если 3 аргумента, то следует найти и задать вопрос
    если аргументов 5, то следует запомнить ответ и найти и задать следующий вопрос
    """
    theme = args[0]
    tests = args[1]
    num = int(args[2])

    resume_dct = dict()
    is_full = False
    question_dct = utils.read_data("data", "world_war_one.json")
    if len(args) == 3:
        question_dct = question_dct[theme][tests][num]
    elif len(args) == 5:
        question_dct = question_dct[theme][tests]
        if num < (len(question_dct) - 1):
            answer = int(args[3])
            weight = int(args[4])
            resume_dct = {
                "theme": theme,
                "tests": tests,
                "num": num,
                "answer": answer,
                "weight": weight,
                "datetime": str(datetime.datetime.now()),
            }
            num = num + 1
            question_dct = question_dct[num]
        else:
            # Вопросы кончились. Сделаем соответствующую запись в профиле пользователя
            questions_count = len(question_dct)
            resume_dct = {
                "questions_count": questions_count,
                "theme": theme,
                "tests": tests,
                "datetime": str(datetime.datetime.now()),
            }
            question_dct = dict()
            is_full = True
    question_dct.update(
        {
            "theme": theme,
            "tests": tests,
            "num": num,
        }
    )
    return question_dct, resume_dct, is_full


def get_full_name(user):
    full_name = " ".join(list(filter(None, [user.first_name, user.last_name])))
    return full_name


def send_rating(user_id):
    rating_dct = utils.read_data("data", "user_score_dct.json")
    rate = rating_dct.get(str(user_id), dict())
    rating_dct = {
        "userscore": rate.get("userscore"),
        "username": rate.get("username"),
        "tests_count": len(rate.get("tests", list())),
    }

    message = ""
    message += f'<b>Ваше имя: </b>{rating_dct["username"]}\n'
    message += f'<b>Набрано баллов: </b>{rating_dct["userscore"]}\n'
    message += f'<b>Пройдено тестов: </b>{rating_dct["tests_count"]}\n'
    message += f"{rate}"
    bot.send_message(user_id, message, parse_mode="html")
    utils.write_data("data", "tmp.json", rate)


@bot.callback_query_handler(func=lambda call: True)
def callback_start(call):
    if call.from_user.is_bot:
        return

    theme_lst = get_theme_name()
    if call.data == "rating":
        send_rating(call.message.chat.id)
    elif call.data == "theme":
        kb = telebot.types.InlineKeyboardMarkup()
        for button in theme_lst:
            kb.add(
                telebot.types.InlineKeyboardButton(text=button, callback_data=button)
            )
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text="Выбери тему",
            reply_markup=kb,
        )

    elif call.data in theme_lst:
        for theme in theme_lst:
            if call.data != theme:
                continue
            quiz_button_lst = get_tests_name(theme)
            num = 0  # Если выбран тест, то начинаем опрос с первого вопроса
            kb = telebot.types.InlineKeyboardMarkup()
            for tests in quiz_button_lst:
                callback_data = f"{theme}|{tests}|{num}"
                kb.add(
                    telebot.types.InlineKeyboardButton(
                        text=tests, callback_data=callback_data
                    )
                )
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                text=theme,
                reply_markup=kb,
            )

    elif call.data.count("|") in [2, 3, 4]:
        question_dct, resume_dct, is_full = get_question(*call.data.split("|"))

        if is_full:
            user_str_id = str(call.message.chat.id)
            user_resume_dct = utils.read_data("data", "user_resume_dct.json")
            questions_lst = [z for z in range(int(resume_dct["questions_count"]) - 1)]
            score = 0
            for ur in user_resume_dct[user_str_id][::-1]:
                if ur["theme"] != resume_dct["theme"]:
                    continue
                if ur["tests"] != resume_dct["tests"]:
                    continue
                if questions_lst:
                    question = questions_lst.pop(questions_lst.index(ur["num"]))
                    score += ur["weight"]

            resume_dct.update({"score": score})

            username = get_full_name(call.message.chat)
            user_score_dct = utils.read_data("data", "user_score_dct.json")
            user_score_dct.setdefault(user_str_id, dict())
            user_score_dct.setdefault(user_str_id, dict()).setdefault("resume", list())
            user_score_dct[user_str_id]["resume"].append(resume_dct)
            user_score_dct[user_str_id]["username"] = username
            user_score_dct[user_str_id]["last_resume"] = str(datetime.datetime.now())
            utils.write_data("data", "user_score_dct.json", user_score_dct)
            send_rating(call.message.chat.id)

            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
            return

        elif resume_dct:
            user_str_id = str(call.message.chat.id)
            user_resume_dct = utils.read_data("data", "user_resume_dct.json")
            user_resume_dct.setdefault(user_str_id, list())
            user_resume_dct[user_str_id].append(resume_dct)
            utils.write_data("data", "user_resume_dct.json", user_resume_dct)

        theme = question_dct["theme"]
        tests = question_dct["tests"]
        num = question_dct["num"]
        question_dct_answers = question_dct["answers"]
        question = question_dct["question"]
        random.shuffle(question_dct_answers)
        kb = telebot.types.InlineKeyboardMarkup()
        for enum, button in enumerate(question_dct_answers):
            callback_data = f'{theme}|{tests}|{num}|{enum}|{button["weight"]}'
            kb.add(
                telebot.types.InlineKeyboardButton(
                    text=button["text"],
                    callback_data=callback_data,
                )
            )
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text=question,
            reply_markup=kb,
        )


@bot.message_handler(content_types=["text"])
def start(message):
    if message.text == "/start":
        kb = telebot.types.InlineKeyboardMarkup()
        k_quiz = telebot.types.InlineKeyboardButton(
            text="Выбор темы", callback_data="theme"
        )
        kb.add(k_quiz)
        k_rating = telebot.types.InlineKeyboardButton(
            text="Посмотреть рейтинг", callback_data="rating"
        )
        kb.add(k_rating)
        bot.send_message(
            message.from_user.id,
            "Привет! Я бот для проверки знаний по Истории. Что выберешь?",
            reply_markup=kb,
        )
    elif message.text == "/rating":
        send_rating(message.from_user.id)


if __name__ == "__main__":
    bot.polling(none_stop=True, interval=0)
