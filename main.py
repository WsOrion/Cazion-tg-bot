import telebot
from telebot import types
import os
import time
import threading
import random
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot.log'
)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = 'ВАШ ТОКЕН СЮДА НАДО ВСТАВИТЬ'

# Файлы для хранения данных
USERS_FILE = 'users.txt'
PROMO_FILE = 'promo.txt'
BETS_FILE = 'bets.txt'

# Создаем необходимые файлы, если их нет
for file in [USERS_FILE, PROMO_FILE, BETS_FILE]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            if file == PROMO_FILE:
                f.write('welcome|50|100\n')  # Пример промокода

bot = telebot.TeleBot(TOKEN)

# Функции для работы с данными
def check_user(user_id):
    try:
        with open(USERS_FILE, 'r') as f:
            for line in f:
                if line.startswith(f"{user_id}|"):
                    return True
        return False
    except Exception as e:
        logger.error(f"Error checking user: {e}")
        return False

def get_user_data(user_id):
    try:
        with open(USERS_FILE, 'r') as f:
            for line in f:
                if line.startswith(f"{user_id}|"):
                    parts = line.strip().split('|')
                    return {
                        'id': parts[0],
                        'phone': parts[1] if len(parts) > 1 else '',
                        'balance': int(parts[2]) if len(parts) > 2 else 0,
                        'status': parts[3] if len(parts) > 3 else 'Игрок'
                    }
        return None
    except Exception as e:
        logger.error(f"Error getting user data: {e}")
        return None

def add_user(user_id, phone=''):
    try:
        with open(USERS_FILE, 'a') as f:
            f.write(f"{user_id}|{phone}|0|Игрок\n")
    except Exception as e:
        logger.error(f"Error adding user: {e}")

def update_user_balance(user_id, amount):
    try:
        lines = []
        with open(USERS_FILE, 'r') as f:
            lines = f.readlines()
        
        with open(USERS_FILE, 'w') as f:
            for line in lines:
                if line.startswith(f"{user_id}|"):
                    parts = line.strip().split('|')
                    new_balance = int(parts[2]) + amount
                    parts[2] = str(new_balance)
                    line = '|'.join(parts) + '\n'
                f.write(line)
    except Exception as e:
        logger.error(f"Error updating balance: {e}")

def set_user_bet(user_id, game_type, amount):
    try:
        lines = []
        if os.path.exists(BETS_FILE):
            with open(BETS_FILE, 'r') as f:
                lines = [line for line in f if not line.startswith(f"{user_id}|")]
        
        with open(BETS_FILE, 'w') as f:
            f.writelines(lines)
            f.write(f"{user_id}|{game_type}|{amount}\n")
    except Exception as e:
        logger.error(f"Error setting bet: {e}")

def get_user_bet(user_id):
    try:
        if not os.path.exists(BETS_FILE):
            return None
            
        with open(BETS_FILE, 'r') as f:
            for line in f:
                if line.startswith(f"{user_id}|"):
                    parts = line.strip().split('|')
                    if len(parts) >= 3:
                        return {
                            'game_type': parts[1],
                            'amount': int(parts[2])
                        }
        return None
    except Exception as e:
        logger.error(f"Error getting bet: {e}")
        return None

def clear_user_bet(user_id):
    try:
        if not os.path.exists(BETS_FILE):
            return
            
        lines = []
        with open(BETS_FILE, 'r') as f:
            lines = [line for line in f if not line.startswith(f"{user_id}|")]
        
        with open(BETS_FILE, 'w') as f:
            f.writelines(lines)
    except Exception as e:
        logger.error(f"Error clearing bet: {e}")

def check_promo_code(promo_code):
    try:
        with open(PROMO_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) == 3:
                    code, reward, activations = parts
                    if code.lower() == promo_code.lower() and int(activations) > 0:
                        return int(reward)
        return None
    except Exception as e:
        logger.error(f"Error checking promo: {e}")
        return None

def update_promo_activations(promo_code):
    try:
        lines = []
        with open(PROMO_FILE, 'r') as f:
            lines = f.readlines()
        
        with open(PROMO_FILE, 'w') as f:
            for line in lines:
                parts = line.strip().split('|')
                if len(parts) == 3:
                    code, reward, activations = parts
                    if code.lower() == promo_code.lower():
                        activations = str(int(activations) - 1)
                        line = f"{code}|{reward}|{activations}\n"
                f.write(line)
    except Exception as e:
        logger.error(f"Error updating promo: {e}")

# Основные команды бота
@bot.message_handler(commands=['start'])
def start(message):
    try:
        user_id = message.from_user.id
        
        if len(message.text.split()) > 1:
            referrer_id = message.text.split()[1]
            if referrer_id.isdigit() and referrer_id != str(user_id):
                update_user_balance(int(referrer_id), 50)
                bot.send_message(int(referrer_id), "🎉 Вы получили 50 руб. за приглашенного друга!")
        
        if check_user(user_id):
            show_main_menu(message.chat.id)
        else:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add(types.KeyboardButton("📱 Отправить номер телефона", request_contact=True))
            bot.send_message(message.chat.id, 
                           "🔒 Для использования бота необходимо подтвердить ваш аккаунт.\n\n"
                           "Нажмите кнопку ниже, чтобы отправить номер телефона:",
                           reply_markup=markup)
    except Exception as e:
        logger.error(f"Error in start: {e}")
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Попробуйте позже.")

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    try:
        user_id = message.from_user.id
        phone = message.contact.phone_number
        
        if not check_user(user_id):
            add_user(user_id, phone)
            bot.send_message(message.chat.id, "✅ Ваш аккаунт успешно подтвержден!", 
                           reply_markup=types.ReplyKeyboardRemove())
            show_main_menu(message.chat.id)
        else:
            bot.send_message(message.chat.id, "⚠️ Ваш аккаунт уже подтвержден!")
    except Exception as e:
        logger.error(f"Error in handle_contact: {e}")
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Попробуйте позже.")

# Меню и игровые функции
def show_main_menu(chat_id, message_id=None):
    try:
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("🎮 Играть", callback_data='play'))
        markup.row(
            types.InlineKeyboardButton("👤 Профиль", callback_data='profile'),
            types.InlineKeyboardButton("🎁 Бонус", callback_data='bonus')
        )
        markup.row(types.InlineKeyboardButton("🛠 Поддержка", callback_data='support'))

        if message_id:
            try:
                bot.delete_message(chat_id, message_id)
            except:
                pass
        
        bot.send_message(chat_id, "🎮 Добро пожаловать в игрового бота!", reply_markup=markup)
    except Exception as e:
        logger.error(f"Error showing main menu: {e}")

def show_game_menu(call):
    try:
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("🎲 Кубик", callback_data='game_dice'),
            types.InlineKeyboardButton("🎰 Слоты", callback_data='game_slots')
        )
        markup.row(
            types.InlineKeyboardButton("⚽ Футбол", callback_data='sport_football'),
            types.InlineKeyboardButton("🏀 Баскетбол", callback_data='sport_basketball')
        )
        markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data='menu'))

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🎲 Выберите игру:",
            reply_markup=markup
        )
    except Exception as e:
        logger.error(f"Error showing game menu: {e}")
        bot.answer_callback_query(call.id, "⚠️ Ошибка при загрузке меню")

def show_game_info(call, game_type):
    try:
        game_info = {
            'game_dice': {'name': '🎲 Кубик', 'win_chance': '40%', 'multiplier': 2, 'emoji': '🎲'},
            'game_slots': {'name': '🎰 Слоты', 'win_chance': '20%', 'multiplier': 5, 'emoji': '🎰'},
            'sport_football': {'name': '⚽ Футбол', 'win_chance': '40%', 'multiplier': 2.5, 'emoji': '⚽'},
            'sport_basketball': {'name': '🏀 Баскетбол', 'win_chance': '50%', 'multiplier': 2, 'emoji': '🏀'}
        }.get(game_type)
        
        if not game_info:
            bot.answer_callback_query(call.id, "⚠️ Игра не найдена!")
            return
        
        user_bet = get_user_bet(call.from_user.id)
        bet_text = f"{user_bet['amount']} руб." if user_bet and user_bet['game_type'] == game_type else "не установлена"
        
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("💰 Выбрать ставку", callback_data=f'set_bet_{game_type}'),
            types.InlineKeyboardButton("▶️ Играть", callback_data=f'play_{game_type}')
        )
        markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data='play'))
        
        message_text = (
            f"🎮 Игра: {game_info['name']}\n"
            f"💵 Ставка: {bet_text}\n"
            f"📊 Шанс на выигрыш: {game_info['win_chance']}\n"
            f"💰 Множитель: x{game_info['multiplier']}\n\n"
            f"Выберите действие:"
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            reply_markup=markup
        )
    except Exception as e:
        logger.error(f"Error showing game info: {e}")
        bot.answer_callback_query(call.id, "⚠️ Ошибка при загрузке игры")

def process_bet(message, game_type):
    try:
        user_id = message.from_user.id
        try:
            amount = int(message.text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            bot.send_message(message.chat.id, "⚠️ Пожалуйста, введите корректную сумму ставки (целое число больше 0)")
            return
        
        user_data = get_user_data(user_id)
        if not user_data:
            bot.send_message(message.chat.id, "❌ Ошибка: пользователь не найден!")
            return
        
        if amount > user_data['balance']:
            bot.send_message(message.chat.id, "❌ Недостаточно средств на балансе!")
            return
        
        set_user_bet(user_id, game_type, amount)
        bot.send_message(message.chat.id, f"✅ Ставка в размере {amount} руб. установлена!")
        show_game_info_by_type(message.chat.id, game_type)
    except Exception as e:
        logger.error(f"Error processing bet: {e}")
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Попробуйте снова.")

def show_game_info_by_type(chat_id, game_type):
    try:
        game_info = {
            'game_dice': {'name': '🎲 Кубик', 'win_chance': '40%', 'multiplier': 2, 'emoji': '🎲'},
            'game_slots': {'name': '🎰 Слоты', 'win_chance': '20%', 'multiplier': 5, 'emoji': '🎰'},
            'sport_football': {'name': '⚽ Футбол', 'win_chance': '40%', 'multiplier': 2.5, 'emoji': '⚽'},
            'sport_basketball': {'name': '🏀 Баскетбол', 'win_chance': '50%', 'multiplier': 2, 'emoji': '🏀'}
        }.get(game_type)
        
        if not game_info:
            return
        
        user_id = chat_id
        user_bet = get_user_bet(user_id)
        bet_text = f"{user_bet['amount']} руб." if user_bet and user_bet['game_type'] == game_type else "не установлена"
        
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("💰 Выбрать ставку", callback_data=f'set_bet_{game_type}'),
            types.InlineKeyboardButton("▶️ Играть", callback_data=f'play_{game_type}')
        )
        markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data='play'))
        
        message_text = (
            f"🎮 Игра: {game_info['name']}\n"
            f"💵 Ставка: {bet_text}\n"
            f"📊 Шанс на выигрыш: {game_info['win_chance']}\n"
            f"💰 Множитель: x{game_info['multiplier']}\n\n"
            f"Выберите действие:"
        )
        
        bot.send_message(chat_id, message_text, reply_markup=markup)
    except Exception as e:
        logger.error(f"Error showing game info by type: {e}")

def play_game(call, game_type):
    try:
        # Удаляем префикс 'play_' из game_type
        game_type = game_type.replace('play_', '')
        
        user_id = call.from_user.id
        user_bet = get_user_bet(user_id)
        
        if not user_bet:
            bot.answer_callback_query(call.id, "❌ Сначала установите ставку!")
            return
            
        if user_bet['game_type'] != game_type:
            bot.answer_callback_query(call.id, "❌ Ставка не соответствует выбранной игре!")
            return
            
        user_data = get_user_data(user_id)
        if not user_data:
            bot.answer_callback_query(call.id, "❌ Пользователь не найден!")
            return
            
        if user_bet['amount'] > user_data['balance']:
            bot.answer_callback_query(call.id, "❌ Недостаточно средств на балансе!")
            return
            
        update_user_balance(user_id, -user_bet['amount'])
        
        game_info = {
            'game_dice': {'name': '🎲 Кубик', 'win_chance': 0.4, 'multiplier': 2, 'emoji': '🎲', 'win_value': 1},
            'game_slots': {'name': '🎰 Слоты', 'win_chance': 0.2, 'multiplier': 5, 'emoji': '🎰', 'win_value': 777},
            'sport_football': {'name': '⚽ Футбол', 'win_chance': 0.4, 'multiplier': 2.5, 'emoji': '⚽', 'win_value': 1},
            'sport_basketball': {'name': '🏀 Баскетбол', 'win_chance': 0.5, 'multiplier': 2, 'emoji': '🏀', 'win_value': 1}
        }.get(game_type)  # Теперь game_type без префикса 'play_'
        
        if not game_info:
            bot.answer_callback_query(call.id, "❌ Игра не найдена!")
            return
            
        # Отправляем анимацию и обрабатываем результат
        msg = bot.send_dice(call.message.chat.id, emoji=game_info['emoji'])
        time.sleep(4)
        
        dice_result = msg.dice.value
        is_win = False
        
        if game_type == 'game_dice' and dice_result == game_info['win_value']:
            is_win = True
        elif game_type == 'game_slots' and dice_result == game_info['win_value']:
            is_win = True
        elif game_type in ['sport_football', 'sport_basketball'] and random.random() < game_info['win_chance']:
            is_win = True
            
        if is_win:
            win_amount = int(user_bet['amount'] * game_info['multiplier'])
            update_user_balance(user_id, win_amount)
            bot.send_message(call.message.chat.id, f"🎉 Поздравляем! Вы выиграли {win_amount} руб.!")
        else:
            bot.send_message(call.message.chat.id, "😢 К сожалению, вы проиграли. Попробуйте еще раз!")
            
        clear_user_bet(user_id)
        
    except Exception as e:
        logger.error(f"Error in play_game: {e}")
        bot.answer_callback_query(call.id, "⚠️ Произошла ошибка. Попробуйте позже.")
            update_user_balance(user_id, user_bet['amount'])
            
 

# Обработчики кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        if call.data == 'profile':
            show_profile(call)
        elif call.data == 'bonus':
            show_bonus(call)
        elif call.data == 'support':
            show_support(call)
        elif call.data == 'menu':
            show_main_menu(call.message.chat.id, call.message.message_id)
        elif call.data == 'play':
            show_game_menu(call)
        elif call.data in ['game_dice', 'game_slots', 'sport_football', 'sport_basketball']:
            show_game_info(call, call.data)
        elif call.data.startswith('set_bet_'):
            game_type = call.data.split('_')[2]
            msg = bot.send_message(call.message.chat.id, "💰 Введите сумму ставки:")
            bot.register_next_step_handler(msg, lambda m: process_bet(m, game_type))
        elif call.data.startswith('play_'):
            game_type = call.data.split('_')[1]
            play_game(call, game_type)
        elif call.data == 'promo':
            msg = bot.send_message(call.message.chat.id, "🎟 Введите промокод:")
            bot.register_next_step_handler(msg, process_promo_code)
        elif call.data == 'deposit':
            show_deposit(call)
        elif call.data == 'withdraw':
            show_withdraw(call)
    except Exception as e:
        logger.error(f"Error in callback handler: {e}")
        bot.answer_callback_query(call.id, "⚠️ Произошла ошибка. Попробуйте позже.")

def process_promo_code(message):
    try:
        user_id = message.from_user.id
        promo_code = message.text.strip()
        
        reward = check_promo_code(promo_code)
        if reward:
            update_user_balance(user_id, reward)
            update_promo_activations(promo_code)
            bot.send_message(message.chat.id, f"🎉 Промокод активирован! Вы получили {reward} руб.")
        else:
            bot.send_message(message.chat.id, "❌ Неверный или уже использованный промокод")
    except Exception as e:
        logger.error(f"Error processing promo: {e}")
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Попробуйте снова.")

def show_profile(call):
    try:
        user_data = get_user_data(call.from_user.id)
        if not user_data:
            bot.answer_callback_query(call.id, "❌ Профиль не найден!")
            return
        
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("💳 Пополнить", callback_data='deposit'),
            types.InlineKeyboardButton("💰 Вывести", callback_data='withdraw')
        )
        markup.row(types.InlineKeyboardButton("🎟 Промокод", callback_data='promo'))
        markup.row(types.InlineKeyboardButton("🔙 Меню", callback_data='menu'))
        
        profile_text = (
            f"✨ Профиль\n"
            f"──────────────\n"
            f"👤 Имя: {call.from_user.first_name}\n"
            f"🆔 ID: {user_data['id']}\n"
            f"📞 Телефон: {user_data['phone']}\n"
            f"──────────────\n"
            f"💵 Баланс: {user_data['balance']} руб.\n\n"
            f"⬇️ Используйте кнопки ниже:"
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=profile_text,
            reply_markup=markup
        )
    except Exception as e:
        logger.error(f"Error showing profile: {e}")
        bot.answer_callback_query(call.id, "⚠️ Ошибка при загрузке профиля")

def show_bonus(call):
    try:
        ref_link = f"https://t.me/{bot.get_me().username}?start={call.from_user.id}"
        
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton(
            "📤 Поделиться", 
       url=f"https://t.me/share/url?url={ref_link}&text=🎉 Присоединяйся к крутому игровому боту!"
        ))
        markup.row(types.InlineKeyboardButton("🔙 Меню", callback_data='menu'))

        message_text = (
            f"🎁 Реферальная программа\n\n"
            f"Приглашайте друзей и получайте бонусы!\n\n"
            f"🔗 Ваша ссылка:\n"
            f"<code>{ref_link}</code>\n\n"
            f"Нажмите на ссылку, чтобы скопировать её"
        )

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            reply_markup=markup,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error showing bonus: {e}")
        bot.answer_callback_query(call.id, "⚠️ Ошибка при загрузке бонусов")

def show_support(call):
    try:
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("💬 Написать в поддержку", url="https://t.me/your_support"))
        markup.row(types.InlineKeyboardButton("🔙 Меню", callback_data='menu'))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🛠 Техническая поддержка\n\nЕсли у вас возникли вопросы или проблемы, "
                 "нажмите кнопку ниже для связи с поддержкой:",
            reply_markup=markup
        )
    except Exception as e:
        logger.error(f"Error showing support: {e}")
        bot.answer_callback_query(call.id, "⚠️ Ошибка при загрузке поддержки")

def show_deposit(call):
    try:
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data='profile'))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="💳 Пополнение баланса\n\n"
                 "Для пополнения баланса свяжитесь с поддержкой: @your_support\n\n"
                 "Укажите ваш ID и сумму пополнения",
            reply_markup=markup
        )
    except Exception as e:
        logger.error(f"Error showing deposit: {e}")
        bot.answer_callback_query(call.id, "⚠️ Ошибка при загрузке пополнения")

def show_withdraw(call):
    try:
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data='profile'))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="💰 Вывод средств\n\n"
                 "Для вывода средств свяжитесь с поддержкой: @your_support\n\n"
                 "Укажите ваш ID, сумму вывода и реквизиты",
            reply_markup=markup
        )
    except Exception as e:
        logger.error(f"Error showing withdraw: {e}")
        bot.answer_callback_query(call.id, "⚠️ Ошибка при загрузке вывода")

# Запуск бота
def polling():
    while True:
        try:
            logger.info("Бот запущен и готов к работе!")
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            logger.error(f"Ошибка: {e}. Перезапуск через 5 секунд...")
            time.sleep(5)

if __name__ == '__main__':
    # Создаем поток для работы бота
    bot_thread = threading.Thread(target=polling)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Главный поток
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
