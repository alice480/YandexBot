import vk_api
import vk
import random
import json
import time
import requests

from wikipedia import wikipedia
from spellchecker import SpellChecker
from google_trans_new import google_translator
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

TOKEN = '281010779644da467b65ad912cb94a5b2684cc67e31f29d07fcd01f9e9f2c0fb4167de9d613b5595f85d3'

token = vk.Session(access_token=TOKEN)
api = vk.API(token)

vk_session = vk_api.VkApi(token=TOKEN)

longpoll = VkBotLongPoll(vk_session, '195389413')
vk = vk_session.get_api()

# словарь, в котором будут содержаться данные о каждом пользователе
bot_users = {}

translator = google_translator()
spell = SpellChecker(language='ru')
wikipedia.set_lang('ru')


def get_name(id):
    data = api.users.get(user_id=id, v='5.130')
    user_name = data[0]['first_name'] + ' ' + data[0]['last_name']
    return user_name


# создаём клавиатуру с пользователями сообщества
def members_list(id):
    global bot_users
    users = api.groups.getMembers(group_id='195389413', v='5.130')
    names = dict()
    members = {"inline": True, "buttons": []}
    names['ids'] = []
    names['ids'].append({})
    for elem in users['items']:
        if elem != id:
            name = get_name(elem)
            names['ids'][0][name] = elem
            members["buttons"].append(
                [{"action": {
                    "type": "text",
                    "label": name
                },
                    "color": "primary"
                }])
    members["buttons"].append(
        [{"action": {
            "type": "text",
            "label": "Все получатели выбраны",
        },
            "color": "positive"
        }])
    members["buttons"].append(
        [{"action": {
            "type": "text",
            "label": "Отключить навык",
        },
            "color": "secondary"
        }])
    names['first_message'], names['first_time'] = True, True
    names['sending'], names['receiving'], names['choice'], names['check'] = False, False, False, False
    names['weather'], names['translation'], names['make_translation'], names['wiki'] = False, False, False, False
    names['preachers'] = []
    names['language'] = ''
    if id not in bot_users:
        bot_users[id] = names
    with open('members.json', 'w', encoding="utf-8") as file:
        json.dump(members, file, ensure_ascii=False)
    return names


def greeting():
    if bot_users[id]['first_time']:
        return 'Привет! Я Яндекс.Бот. Моя основная цель - помочь Алисе добрать необходимые баллы, ' \
               'но ещё я умею делать крутые\n(и не очень) штуки, так что выбирай скорей, какая функция тебе нужна'
    else:
        return 'Рад видеть Вас снова!!!'


def mass_mailing(preachers, text, user):
    name_sender = get_name(user)
    for id in preachers:
        vk.messages.send(user_id=id,
                         message='Вам сообщение от ' + name_sender + ':\n' + text,
                         random_id=random.randint(0, 2 ** 64))


def send_message(id, text, *rest):
    if bool(rest):
        vk.messages.send(user_id=id,
                         message=text,
                         keyboard=open(rest[0], "r", encoding="utf-8").read(),
                         random_id=random.randint(0, 2 ** 64))
    else:
        vk.messages.send(user_id=id,
                         message=text,
                         random_id=random.randint(0, 2 ** 64))


LANGUAGES = {'Русский': 'ru', 'Английский': 'en', 'Французский': 'fr',
             'Немецкий': 'de', 'Китайский': 'zh-tw', 'Итальянский': 'it'}
UNDERSTANDABLE = ['Отключить Яндекс.Бота', 'Написать участникам группы', 'Проверить орфографию',
                  'Все получатели выбраны', 'Отключить навык', 'Показать погоду', 'Перевести текст',
                  'Найти в Википедии']
for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        id = event.obj.message['from_id']
        user_name = get_name(id)
        text = event.obj.message['text']
        members_list(id)
        #приветствие пользователя
        if bot_users[id]['first_message']:
            send_message(id, greeting())
            time.sleep(2)
            send_message(id, 'Итак, я могу', "functions.json")
            bot_users[id]['first_message'] = False

        # ответ на нажатие кнопки "Написать участникам группы"
        elif text == 'Написать участникам группы':
            send_message(id, 'Кому будем писать?', "members.json")
            bot_users[id]['sending'] = True

        # узнаём пользователей, которые получат сообщение
        elif bot_users[id]['sending']:
            if text == 'Все получатели выбраны':
                if bool(bot_users[id]['preachers']):
                    bot_users[id]['sending'] = False
                    send_message(id, 'Введите своё сообщение для выбранных пользователей')
                    bot_users[id]['receiving'] = True
                else:
                    send_message(id, 'Сначала выберите пользователей', "members.json")
            elif text == 'Отключить навык':
                send_message(id, 'Тогда воспользуйтесь другими функциями', "functions.json")
                bot_users[id]['preachers'] = []
                bot_users[id]['sending'] = False
            elif text in bot_users[id]['ids'][0]:
                if bot_users[id]['ids'][0][text] not in bot_users[id]['preachers']:
                    bot_users[id]['preachers'].append(bot_users[id]['ids'][0][text])
            else:
                send_message(id, 'Чтобы воспользоваться навыком, выберите имена пользователей', "members.json")

        elif text == 'Отключить навык':
            send_message(id, 'Тогда воспользуйтесь другими функциями', "functions.json")
            bot_users[id]['preachers'] = []

        # запрос на отправку сообщения
        elif bot_users[id]['receiving']:
            bot_users[id]['receiving'] = False
            forwarded_text = event.obj.message['text']
            send_message(id, 'Отправляем?', "approval.json")
            bot_users[id]['choice'] = True

        elif bot_users[id]['choice']:
            bot_users[id]['choice'] = False
            if event.obj.message['text'] == 'Да':
                send_message(id, 'Спасибо, что воспользовались нашими услугами. Ваша почта России ❤\n',
                             "functions.json")
                mass_mailing(bot_users[id]['preachers'], forwarded_text, id)
                bot_users[id]['preachers'] = []
            else:
                send_message(id, 'Ну и зачем я так долго это всё писала, если Вы всё равно не пользуетесь?\n'
                                 'Ладно, что дальше будете делать?', "functions.json")
                bot_users[id]['preachers'] = []

        # запуск функции "погода"
        elif text == 'Показать погоду':
            send_message(id, 'Введите название города')
            bot_users[id]['weather'] = True

        # получаем информацию о погоде через api и выводим результат
        elif bot_users[id]['weather']:
            bot_users[id]['weather'] = False
            try:
                result = requests.get("http://api.openweathermap.org/data/2.5/weather",
                                      params={'q': text, 'units': 'metric', 'lang': 'ru',
                                              'APPID': "8a7d71108d0e46c268938c66a2ef3dc5"}).text
                result = json.loads(result)
                send_message(id, 'Сейчас на улице: {}'.format(result["weather"][0]['description']) +
                             '\nТемпература в данный момент: {}°C'.format(result["main"]['temp']) +
                             '\nОщущается как: {}°C'.format(result["main"]['feels_like']) +
                             '\nМинимальная температура в течение дня: {}°C'.format(result["main"]['temp_min']) +
                             '\nМаксимальная температура в течение дня: {}°C'.format(result["main"]['temp_max']))
                time.sleep(3)
                send_message(id, 'Чем могу ещё помочь?', "functions.json")
            except Exception as err0:
                send_message(id, 'Ошибка "{}"\nПопробуйте ещё раз'.format(err0), "functions.json")

        # запуск функции "Перевести текст"
        elif text == 'Перевести текст':
            bot_users[id]['translation'] = True
            send_message(id, 'На какой язык перевести?')
            send_message(id, 'Выбирайте:', "languages.json")
            time.sleep(5)
            send_message(id, 'Введите текст, который нужно перевести')

        # выбор языка для перевода
        elif bot_users[id]['translation']:
            bot_users[id]['translation'] = False
            bot_users[id]['language'] = text
            bot_users[id]['make_translation'] = True

        # вывод результата или сообщение об ошибке
        elif bot_users[id]['make_translation']:
            bot_users[id]['make_translation'] = False
            try:
                translation = translator.translate(text, lang_tgt=LANGUAGES[bot_users[id]['language']])
                send_message(id, 'Исходный текст: ' + text + '\n\nПереведенный текст: ' + translation)
                time.sleep(5)
                send_message(id, 'Что теперь?', "functions.json")
            except Exception as err1:
                send_message(id, 'Ошибка "{}" Попробуйте ещё раз'.format(err1), "languages.json")

        # запуск функции "Проверить орфографию"
        elif text == 'Проверить орфографию':
            bot_users[id]['check'] = True
            send_message(id, 'Введите текст на проверку')

        # вывод результата
        elif bot_users[id]['check']:
            bot_users[id]['check'] = False
            misspelled = spell.unknown(text.split(' '))
            stroka = ''
            for word in misspelled:
                stroka += 'Возможно, вы имели в виду слово "{}"\nДругие возможные варианты {}\n\n\n'.format(
                    spell.correction(word), spell.candidates(word))
            send_message(id, stroka)
            time.sleep(5)
            send_message(id, 'Буду рад помочь еще чем-нибудь', "functions.json")

        # запуск функции "Найти в Википедии"
        elif text == 'Найти в Википедии':
            bot_users[id]['wiki'] = True
            send_message(id, 'Что нужно узнать?')

        # вывод результата или сообщение об ошибке
        elif bot_users[id]['wiki']:
            bot_users[id]['wiki'] = False
            try:
                send_message(id, str(wikipedia.page(text).content[:1000]))
                time.sleep(5)
                send_message(id, 'Напоминаю, я могу', "functions.json")
            except Exception as err2:
                send_message(id, 'Ошибка "{}" Попробуйте ещё раз'.format(err2), "functions.json")

        # отключение бота и перевод в первоначальное состояние
        elif text == 'Отключить Яндекс.Бота':
            send_message(id, 'Круто пообщались! Зови, если нужна будет помощь')
            send_message(id, 'Для активации бота пришлите любое сообщение')
            bot_users[id]['first_message'], bot_users[id]['first_time'] = True, False
            bot_users[id]['sending'], bot_users[id]['receiving'], = False, False
            bot_users[id]['choice'], bot_users[id]['check'] = False, False,
            bot_users[id]['weather'], bot_users[id]['translation'] = False, False
            bot_users[id]['make_translation'], bot_users[id]['wiki'] = False, False
            bot_users[id]['preachers'] = []
            bot_users[id]['language'] = ''

        #если слово не является командой, бот просит воспользоваться кнопками
        elif text not in UNDERSTANDABLE and text not in bot_users[id]['ids'][0] and bot_users[id]['first_message'] == \
                                                            bot_users[id]['sending'] == bot_users[id]['receiving'] == \
                                                            bot_users[id]['choice'] == bot_users[id]['weather'] == \
                                                            bot_users[id]['translation'] == \
                                                            bot_users[id]['make_translation'] ==\
                                                            bot_users[id]['check'] == bot_users[id]['wiki'] == False:
            send_message(id, 'Лучше пользуйтесь кнопками. Я Вас так лучше понимаю))', "functions.json")