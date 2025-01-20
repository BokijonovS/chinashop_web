from socket import fromfd
from traceback import format_exc

import telebot
from telebot.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo


# Replace 'YOUR_BOT_TOKEN' with your actual bot token from BotFather
BOT_TOKEN = '7642750809:AAGia4vhE-SE_024OcrbVBi6EKPA4yvcFU8'
bot = telebot.TeleBot(BOT_TOKEN)


import sqlite3
import os

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

def get_user(username):
    try:
        # Connect to the database
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../db.sqlite3')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute the SQL query to fetch the user
        cursor.execute("SELECT id, username, email, first_name, last_name FROM auth_user WHERE username = ?;", (username,))
        user = cursor.fetchone()

        # Close the connection
        conn.close()

        # Return a dictionary if the user exists
        if user:
            return {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "first_name": user[3],
                "last_name": user[4],
            }
        else:
            return None  # User not found
    except Exception as e:
        return {"error": str(e)}


def create_user(username, email=None, password=None, first_name=None, last_name=None):
    try:
        # Connect to the database
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../db.sqlite3')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Insert the user into the database
        cursor.execute("""
            INSERT INTO auth_user (username, email, password, first_name, last_name, is_active, is_staff, is_superuser, date_joined)
            VALUES (?, ?, ?, ?, ?, 1, 0, 0, datetime('now'));
        """, (
            username,
            email or "",  # Convert None to ""
            password or "",  # Convert None to ""
            first_name or "",  # Convert None to ""
            last_name or ""  # Convert None to ""
        ))

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

        return {"status": "success", "message": f"User '{username}' created successfully."}
    except sqlite3.IntegrityError as e:
        return {"status": "error", "message": "Username already exists."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def update_user(username, field, new_value):
    try:
        # Define the list of fields allowed to be updated
        allowed_fields = ["email", "password", "first_name", "last_name", "is_active", "is_staff", "is_superuser"]

        if field not in allowed_fields:
            return {"status": "error", "message": f"Field '{field}' cannot be updated."}

        # Connect to the database
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../db.sqlite3')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute the SQL update query
        query = f"UPDATE auth_user SET {field} = ? WHERE username = ?;"
        cursor.execute(query, (new_value, username))

        # Check if any row was affected
        if cursor.rowcount == 0:
            conn.close()
            return {"status": "error", "message": f"No user found with username '{username}'."}

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

        return {"status": "success",
                "message": f"User '{username}' updated successfully. Field '{field}' set to '{new_value}'."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_user(user_id):
    user = get_user(username=user_id)
    if user['username'] and user['first_name'] and user['last_name'] and user['email']:
        return True
    else:
        return False

letters = "abcdefghijklmnopqrstuvwxyz '`"


def name_checker(name):
    name1 = str(name)
    for i in name1:
        if i.lower() not in letters:
            return False
    if name1.istitle() and len(name1) >= 4:
        return True
    else:
        return False



@bot.message_handler(commands=['start'])
def start(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    try:
        create_user(username=user_id)
    except:
        pass
    registered = check_user(user_id)
    if registered:
        user = get_user(user_id)
        bot.send_message(chat_id, "Assalomu alekum botga hush kelibsiz!", reply_markup=menu_buttons(user['username']))
    else:
        bot.send_message(chat_id, "Ro'yxatdan o'ting", reply_markup=register_button())



USER_DATA = {}


@bot.message_handler(func=lambda message: message.text == "Ro'yxatdan o'tish")
def register(message: Message):
    chat_id = message.chat.id
    from_user_id = message.from_user.id
    USER_DATA[from_user_id] = {}
    msg = bot.send_message(chat_id, "Ismingizni kiriting", reply_markup=ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, get_name)


def get_name(message: Message):
    chat_id = message.chat.id
    name1 = message.text
    from_user_id = message.from_user.id

    # Validate the name
    if name_checker(name1):
        # Store the valid name in USER_DATA
        USER_DATA[from_user_id]["name"] = name1
        msg = bot.send_message(chat_id, "Telefon raqamni yuborish tugmasini bosing!", reply_markup=phone_button())
        bot.register_next_step_handler(msg, get_phone_number)
    else:
        # Prompt user to enter a valid name again
        msg = bot.send_message(chat_id, "Ismingizni bosh harfini katta bilan lotin harflarida kiriting")
        bot.register_next_step_handler(msg, get_name)
        return


def get_phone_number(message: Message):
    chat_id = message.chat.id
    from_user_id = message.from_user.id
    if message.text and message.text == "Ortga◀️":
        msg = bot.send_message(chat_id, "Ismingizni kiriting", reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, get_name)
        return

    # Handle phone number
    phone_number = None
    if message.contact:
        phone_number = message.contact.phone_number
    else:
        msg = bot.send_message(chat_id, "Telefon raqamni yuborish tugmasini bosing!", reply_markup=phone_button())
        bot.register_next_step_handler(msg, get_phone_number)
        return

    # Store the phone number in USER_DATA
    USER_DATA[from_user_id]["phone_number"] = phone_number
    msg = bot.send_message(chat_id, "Iltimos, qo'shimcha telefon raqamni kiriting (faqat matn shaklida)", reply_markup=back_button())
    bot.register_next_step_handler(msg, get_secondary_number)


def get_secondary_number(message: Message):
    chat_id = message.chat.id
    from_user_id = message.from_user.id
    secondary_number = message.text

    # Validate secondary number
    if secondary_number == "Ortga◀️":
        msg = bot.send_message(chat_id, "Telefon raqamni yuborish tugmasini bosing!", reply_markup=phone_button())
        bot.register_next_step_handler(msg, get_phone_number)
        return
    elif secondary_number.startswith('+998') and len(secondary_number) == 13 and secondary_number[1:].isdigit():
        USER_DATA[from_user_id]["secondary_number"] = secondary_number

        # Save user data in the database
        try:
            user = get_user(from_user_id)
        except:
            bot.send_message(chat_id, "Foydalanuvchi topilmadi! /start qaytadan bosing")
            return

        # Update and save user information
        update_user(from_user_id, "first_name", USER_DATA[from_user_id]["name"])
        update_user(from_user_id, "last_name", USER_DATA[from_user_id]["phone_number"])
        update_user(from_user_id, "email", USER_DATA[from_user_id]["secondary_number"])


        # Clean up user data
        del USER_DATA[from_user_id]
        user = get_user(from_user_id)

        # Confirm registration
        bot.send_message(chat_id, "Ro'yxatdan o'tdingiz",
                         reply_markup=menu_buttons(user['username']))
    else:
        msg = bot.send_message(chat_id, "Iltimos, qo'shimcha telefon raqamni to'g'ri kiriting (format: +998XXXXXXXXX)",
                               reply_markup=back_button())
        bot.register_next_step_handler(msg, get_secondary_number)
        return


@bot.message_handler(func=lambda message: message.text == "Bosh menyu")
def menu(message: Message):
    chat_id = message.chat.id
    user_tg_id = message.from_user.id
    bot.send_message(chat_id, "Bosh menyuga qaytdingiz", reply_markup=menu_buttons(telegram_id=user_tg_id))


@bot.message_handler(func=lambda message: message.text == "Sozlamalar ⚙️")
def settings(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    user = get_user(user_id)
    text = f"Ismingiz: {user['first_name']}\nTelefon raqamingiz: {user['last_name']}\nQo'shimcha raqamingiz: {user['email']}"
    msg = bot.send_message(chat_id, text, reply_markup=settings_buttons())
    bot.register_next_step_handler(msg, handle_setting)


def handle_setting(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if message.text == "Ortga◀️":
        bot.send_message(chat_id, "Bosh menyuga qaytdingiz", reply_markup=menu_buttons(user_id))
        return
    elif message.text == "Ismni o'zgartirish 🖊":
        msg = bot.send_message(chat_id, "Ismni kiriting", reply_markup=back_button())
        bot.register_next_step_handler(msg, change_user, "name")

    elif message.text == "Qo'shimcha raqamni o'zgartirish ☎️":
        msg = bot.send_message(chat_id, "Raqamni kiriting.\nShablon: +998XXXXXXXXX", reply_markup=back_button())
        bot.register_next_step_handler(msg, change_user, "phone_number2")

    else:
        msg = bot.send_message(chat_id, "Pastdagi tugmalardan birini tanlang!", reply_markup=settings_buttons())
        bot.register_next_step_handler(msg, handle_setting)


def change_user(message: Message, field):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.text == "Ortga◀️":
        msg = bot.send_message(chat_id, "O'zgartirmoqchi bo'gan maydonni tanlang.", reply_markup=settings_buttons())
        bot.register_next_step_handler(msg, handle_setting)
        return
    elif field == "name":
        if name_checker(message.text):
            update_user(user_id, "first_name", message.text)
            bot.send_message(chat_id, "Yangi ism saqlandi!", reply_markup=settings_buttons())
            user = get_user(user_id)
            text = f"Ismingiz: {user['first_name']}\nTelefon raqamingiz: {user['last_name']}\nQo'shimcha raqamingiz: {user['email']}"
            msg = bot.send_message(chat_id, text, reply_markup=settings_buttons())
            bot.register_next_step_handler(msg, handle_setting)
        else:
            msg = bot.send_message(chat_id, "Ismingizni bosh harfini katta bilan lotin harflarida kiriting",
                                   reply_markup=back_button())
            bot.register_next_step_handler(msg, change_user, "name")
            return
    elif field == "phone_number2":
        if message.text.startswith('+998') and len(message.text) == 13 and message.text[1:].isdigit():
            change_user(user_id, 'email', message.text)
            bot.send_message(chat_id, "Yangi raqam saqlandi!", reply_markup=settings_buttons())
            user = get_user(user_id)
            text = f"Ismingiz: {user['first_name']}\nTelefon raqamingiz: {user['last_name']}\nQo'shimcha raqamingiz: {user['email']}"
            msg = bot.send_message(chat_id, text, reply_markup=settings_buttons())
            bot.register_next_step_handler(msg, handle_setting)
        else:
            msg = bot.send_message(chat_id, "Iltimos, qo'shimcha telefon raqamni to'g'ri kiriting (format: +998XXXXXXXXX)",
                                   reply_markup=back_button())
            bot.register_next_step_handler(msg, change_user, "phone_number")
            return




# Start the bot's polling loop
if __name__ == "__main__":
    bot.polling(none_stop=True)
