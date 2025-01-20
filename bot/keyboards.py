from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo


def register_button():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = KeyboardButton("Ro'yxatdan o'tish")
    markup.add(btn1)
    return markup


def phone_button():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn1 = KeyboardButton("Telefon raqamni yuborish ☎️", request_contact=True)
    btn2 = KeyboardButton("Ortga◀️")
    markup.add(btn1, btn2)
    return markup


def menu_buttons(telegram_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    web_app_url = f"https://darkslied.pythonanywhere.com/api/login/?tg-id={telegram_id}"
    btn1 = KeyboardButton(
        text="Do'konni ochish 🛍",
        web_app=WebAppInfo(url=web_app_url)  # Add WebAppInfo for the button
    )
    btn2 = KeyboardButton("Sozlamalar ⚙️")
    markup.add(btn1, btn2)
    return markup


def settings_buttons():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn1 = KeyboardButton("Ismni o'zgartirish 🖊")
    btn2 = KeyboardButton("Qo'shimcha raqamni o'zgartirish ☎️")
    btn3 = KeyboardButton("Ortga◀️")
    markup.add(btn1, btn2, btn3)
    return markup


def back_button():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    btn = KeyboardButton("Ortga◀️")
    markup.add(btn)
    return markup
