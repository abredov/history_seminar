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
        if num < (len(question_dct) - 1):
            num = num + 1
            question_dct = question_dct[num]
        else:
            # Вопросы кончились. Сделаем соответствующую запись в профиле пользователя
            questions_count = len(question_dct)
            question_dct = dict()
            question_dct = {
                "questions_count": questions_count,
                "theme": theme,
                "tests": tests,
                "datetime": str(datetime.datetime.now()),
            }

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


def create_rating_msg(collection_dct, resume_lst):
    user_dct = dict()
    for theme in collection_dct:
        for tests in collection_dct[theme]:
            key = f'{theme}_{tests}'
            user_dct.setdefault(key, list())

    for resume in resume_lst:
        key = f'{resume["theme"]}_{resume["tests"]}'
        user_dct.setdefault(key, list())
        user_dct[key].append(resume)

    message2_lst = list()
    for tt in user_dct:
        theme, tests = tt.split('_')
        msg = f'По теме <b>{theme} {tests}</b> сделано попыток: {len(user_dct[tt])}'
        if len(user_dct[tt]) == 1:
            maxx = max(user_dct[tt], key=lambda x: x['score'] / x['questions_count'])
            msg += f'\nМаксимум баллов: {maxx["score"]} из {maxx["questions_count"]}' 
        elif user_dct[tt]:
            maxx = max(user_dct[tt], key=lambda x: x['score'] / x['questions_count'])
            msg += f'\nМаксимум баллов: {maxx["score"]} из {maxx["questions_count"]}' 
            minn = min(user_dct[tt], key=lambda x: x['score'] / x['questions_count'])
            msg += f'\nМинимум баллов: {minn["score"]} из {minn["questions_count"]}' 
        msg += f'\n'
        message2_lst.append(msg)
    message2 = '\n'.join(message2_lst)

    rating_lst = list()
    for tt in user_dct:
        current = 0
        if user_dct[tt]:
            maxx = max(user_dct[tt], key=lambda x: x['score'] / x['questions_count'])
            current = maxx['score'] / maxx['questions_count']
        rating_lst.append(current)
    rating = sum(rating_lst) / len(rating_lst)
    message3 = f'Суммарный рейтинг: {rating:0.2f}'
    return message2, message3, rating


def send_rating(user_id):
    """
    Функция генерирует рейтинг по собранным данным
    1. Последний пройденный тест, сколько набрано очков
    2. Все имеющиеся тесты, сколько по каждому максимум и минимум или вообще нет
    3. Суммарный рейтинг пользователя по всем пройденным тестам с наилучшим результатом
    4. Положение в рейтинге пользователя относительно других
    """

    print('rating')
    rating_dct = utils.read_data("data", "user_score_dct.json")
    resume_lst = rating_dct.get(str(user_id), dict()).get('resume', list())
    rating1 = max(resume_lst, key=lambda x: x['datetime'])
    message1 = '\n'.join([
        f'Последний тест по теме <b>{rating1["theme"]}: {rating1["tests"]}</b>',
        f'Дата прохождения: {rating1["datetime"][:19]}',
        f'Набрано {rating1["score"]} из {rating1["questions_count"]} баллов',
    ])
    bot.send_message(user_id, message1, parse_mode="html")

    collection_dct = utils.read_data("tests", "collection.json")
    message2, message3, _ = create_rating_msg(collection_dct, resume_lst)
    bot.send_message(user_id, message2, parse_mode="html")
    bot.send_message(user_id, message3, parse_mode="html")

    total_lst = list()
    for user_id_rating in rating_dct:
        resume_lst = rating_dct.get(user_id_rating, dict()).get('resume', list())
        _, _, rating = create_rating_msg(collection_dct, resume_lst)
        total_lst.append((user_id_rating, rating))
    total_lst.sort(key=lambda x: x[1], reverse=True)
    total = [x[0] for x in total_lst]
    message4 = f'Ваше место в общем рейтинге: {total.index(str(user_id)) + 1} из {len(total)}'
    bot.send_message(user_id, message4, parse_mode="html")


def send_rating1(user_id):
    user_id = str(user_id)
    user_score = utils.read_data("data", "user_score_dct.json")
    raiting_lst = []
    for user in list(user_score.keys()):
        result_lst = user_score[user]["resume"]
        result_lst = result_lst[::-1]
        repeat_values_lst = []
        score = 0
        for result_dict in result_lst:
            if (result_dict["theme"], result_dict["tests"]) not in repeat_values_lst:
                repeat_values_lst.append((result_dict["theme"], result_dict["tests"]))
                score += result_dict["score"]
        raiting_lst.append((user, user_score[user]["username"], len(repeat_values_lst), score))
    raiting_lst = sorted(raiting_lst, key=lambda x: x[3])
    raiting_lst = raiting_lst[::-1]
    status = 0
    place = len(raiting_lst) + 1
    user_name = ''
    tests_count = 0
    score = 0
    for i in range(len(raiting_lst)):
        if raiting_lst[i][0] == user_id:
            status = 1
            place = i + 1
            user_name = raiting_lst[i][1]
            tests_count = raiting_lst[i][2]
            score = raiting_lst[i][3]
            break
    if status == 0:
        message = ""
        message += f'Набрано баллов: {score}\n'
        message += f'Пройдено тестов: {tests_count}\n'
        message += f'Вы занимаете {place} место из {place}\n'
    else:
        message = ""
        message += f'Ваше имя: {user_name}\n'
        message += f'Набрано баллов: {score}\n'
        message += f'Пройдено тестов: {tests_count}\n'
        message += f'Вы занимаете {place} место из {len(raiting_lst)}\n'
    return message


def send_result(user_id):
    user_score_lst = utils.read_data("data", "user_score_dct.json")
    user_score_lst = user_score_lst[user_id]
    user_score_lst = user_score_lst["resume"]
    last_dict = user_score_lst[-1]
    theme = last_dict['theme']
    count_questions = last_dict["questions_count"]
    tests_lst = utils.read_data("data", "world_war_one.json")[theme]
    tests_lst = list(tests_lst.keys())
    result_dict = dict()
    user_score_lst.reverse()
    for test in tests_lst:
        result_dict[test] = 0
    n = 0
    max_count = len(user_score_lst)
    while tests_lst:
        if n == max_count:
            break
        elif user_score_lst[n]["theme"] == theme and user_score_lst[n]["tests"] in tests_lst:
            result_dict[user_score_lst[n]["tests"]] = user_score_lst[n]["score"]
            tests_lst.remove(user_score_lst[n]["tests"])
        n += 1
    return result_dict, theme, count_questions


def send_mistakes(user_id):
    user_resume_lst = utils.read_data("data", "user_resume_dct.json")
    user_resume_lst = user_resume_lst[user_id]
    user_resume_lst.reverse()
    last_quest = user_resume_lst[0]
    theme = last_quest["theme"]
    test = last_quest["tests"]
    count_questions = last_quest["num"] + 1
    mistakes_dict = dict()
    testing = utils.read_data("data", "world_war_one.json")
    testing = testing[theme]
    testing = testing[test]
    for i in range(count_questions):
        if user_resume_lst[i]["weight"] == 0:
            question = testing[i]["question"]
            answers = testing[i]['answers']
            answer = ''
            for j in range(len(answers)):
                if answers[j]["weight"] == 1:
                    answer = answers[j]["text"]
            mistakes_dict[question] = answer
    return mistakes_dict


@bot.callback_query_handler(func=lambda call: True)
def callback_start(call):
    if call.from_user.is_bot:
        return

    theme_lst = get_theme_name()
    if call.data == "rating":
        message = send_rating(call.message.chat.id)
        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(
            telebot.types.InlineKeyboardButton(
                text='Меню', callback_data='menu'
            )
        )
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text=message,
            reply_markup=kb,
        )
    elif call.data == "theme":
        kb = telebot.types.InlineKeyboardMarkup()
        for button in theme_lst:
            kb.add(
                telebot.types.InlineKeyboardButton(text=button, callback_data=button)
            )
        kb.add(
            telebot.types.InlineKeyboardButton(
                text='Меню', callback_data='menu'
            )
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
            kb.add(
                telebot.types.InlineKeyboardButton(
                    text='Меню', callback_data='menu'
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
            user_resume_dct.setdefault(user_str_id, list())
            user_resume_dct[user_str_id].append(resume_dct)
            utils.write_data("data", "user_resume_dct.json", user_resume_dct)
            user_resume_dct = utils.read_data("data", "user_resume_dct.json")
            questions_lst = [z for z in range(int(question_dct["questions_count"]))]
            score = 0
            removed_value = question_dct.pop('num')
            for ur in user_resume_dct[user_str_id][::-1]:
                if ur["theme"] != question_dct["theme"]:
                    continue
                if ur["tests"] != question_dct["tests"]:
                    continue
                if questions_lst:
                    questions_lst.pop(questions_lst.index(ur["num"]))
                    score += ur["weight"]

            question_dct.update({"score": score})

            username = get_full_name(call.message.chat)
            user_score_dct = utils.read_data("data", "user_score_dct.json")
            user_score_dct.setdefault(user_str_id, dict())
            user_score_dct.setdefault(user_str_id, dict()).setdefault("resume", list())
            user_score_dct[user_str_id]["resume"].append(question_dct)
            user_score_dct[user_str_id]["username"] = username
            user_score_dct[user_str_id]["last_resume"] = str(datetime.datetime.now())
            utils.write_data("data", "user_score_dct.json", user_score_dct)
            '''send_rating(call.message.chat.id)'''

            kb = telebot.types.InlineKeyboardMarkup()
            kb.add(
                telebot.types.InlineKeyboardButton(
                    text='Результат', callback_data='result'
                )
            )
            kb.add(
                telebot.types.InlineKeyboardButton(
                    text='Меню', callback_data='menu'
                )
            )
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                text="Чтобы перейти к результатам нажмите: 'Результат'\n"
                     "Чтобы вернутся на главное меню нажмите: 'Меню'",
                reply_markup=kb,
            )
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
    elif call.data == 'result':
        result_dict, theme, count_questions = send_result(str(call.message.chat.id))
        tests_count = len(result_dict.keys())
        sum_score = 0
        text_of_result = ''
        for key in result_dict.keys():
            sum_score += result_dict[key]
            text_of_result += key + ' - ' + str(result_dict[key] / count_questions * 100) + '%\n'

        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(
            telebot.types.InlineKeyboardButton(
                text='Ошибки', callback_data='mistakes'
            )
        )
        kb.add(
            telebot.types.InlineKeyboardButton(
                text='Меню', callback_data='menu'
            )
        )
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text='Тема освоена на ' + str(round(sum_score / (tests_count * count_questions) * 100)) + '%\n' + text_of_result,
            reply_markup=kb,
        )
    elif call.data == 'mistakes':
        mistakes_dict = send_mistakes(str(call.message.chat.id))
        text_of_mistakes = ''
        if len(mistakes_dict.keys()) == 0:
            text_of_mistakes = 'Поздравляем, вы не допустили ни одну ошибку!!!'
        else:
            n = 1
            for key in mistakes_dict.keys():
                text_of_mistakes += str(n) + '. ' + key + '\n' + mistakes_dict[key] + '\n'
                n += 1
        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(
            telebot.types.InlineKeyboardButton(
                text='Меню', callback_data='menu'
            )
        )
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text='Вам приведены вопросы, в которых вы совершили ошибку, с правильными ответами, \n' +
                 'постарайтесь их запомнить\n' + text_of_mistakes,
            reply_markup=kb,
        )
    elif call.data == 'menu':
        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(
            telebot.types.InlineKeyboardButton(
                text="Выбор темы", callback_data="theme"
            )
        )
        kb.add(
            telebot.types.InlineKeyboardButton(
                text="Посмотреть рейтинг", callback_data="rating"
            )
        )
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text='Меню',
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



if __name__ == "__main__":
    bot.polling(none_stop=True, interval=0)
