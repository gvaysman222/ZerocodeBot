import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import threading
import time

# Токен твоего бота
TOKEN = '7094168945:AAHlxpfbPeG-OIs2Q1SQGfpKwFEq60X0RgQ'
bot = telebot.TeleBot(TOKEN)

# Настройки Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('cobalt-ship-421207-f6982a7c5358.json', scope)
client = gspread.authorize(creds)

# Открываем таблицу по ID и выбираем лист "ВОПРОС ОТВЕТ"
sheet = client.open_by_key('1IlLgVK3wzfeVS7xSd32eLUNYwe3R2AVaih-6pdCPmD0').worksheet('ВОПРОС-ОТВЕТ')

def find_row_by_message_link(message_link):
    try:
        cell = sheet.find(message_link)
        return cell.row if cell else None
    except:
        return None
def get_curator(chat_id):
    curators = []
    try:
        # Получаем список администраторов чата
        admins = bot.get_chat_administrators(chat_id)
        # Фильтруем администраторов по должности "Куратор"
        curators = [admin.user.username for admin in admins if admin.custom_title == 'Куратор' and admin.user.username]
    except Exception as e:
        print(f"Ошибка при получении данных администратора: {e}")
    return ', '.join(curators) if curators else 'Куратор не найден'

@bot.message_handler(func=lambda message: message.text.startswith('#вопроскуратору'))
def handle_question(message):
    question_text = message.text[len('#вопроскуратору'):].strip()
    timestamp = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    chat_title = message.chat.title if message.chat.type in ['group', 'supergroup'] else 'Private Chat'
    curator_username = get_curator(message.chat.id)
    message_link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.message_id}"
    asker_username = message.from_user.username or message.from_user.first_name  # Используем username или имя, если username отсутствует
    # Добавляем все данные в таблицу
    sheet.append_row([chat_title, question_text, curator_username, timestamp, message_link, asker_username], value_input_option='USER_ENTERED')
    bot.reply_to(message, f'Вопрос "{question_text}" добавлен в таблицу.')


@bot.message_handler(func=lambda message: message.reply_to_message and message.text.startswith('#ответ'))
def handle_answer(message):
    date_answer = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    if message.from_user.username in get_curator(message.chat.id):
        answer_text = message.text[len('#ответ'):].strip()
        # Строим ссылку на сообщение, на которое был дан ответ
        reply_message_link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.reply_to_message.message_id}"
        row = find_row_by_message_link(reply_message_link)
        if row:
            sheet.update_cell(row, 8, answer_text)  # Столбец F - это 6-й столбец
            bot.reply_to(message, f'Ответ "{answer_text}" записан в строку {row} столбца F.')
        else:
            bot.reply_to(message, 'Соответствующий вопрос не найден в таблице.')
        sheet.update_cell(row, 7, date_answer)
    else:
        bot.reply_to(message, 'У вас нет прав для ответа на вопросы.')


bot.polling()

