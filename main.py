from typing import Final
import json
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import os

TOKEN: Final = "8486624115:AAFXlfNb08meI6UiXIHMWCxSpdgIYd5HLJQ"
BOT_USERNAME: Final = "@Vertical_Aqua_Bot"

# Путь к JSON файлам
JSON_DIR = "json"
CLIENT_DIR = os.path.join(JSON_DIR, "client")
WORKOUT_DIR = os.path.join(JSON_DIR, "workout")
KIDS_DIR = os.path.join(JSON_DIR, "fitnes_kids")

# Маппинг услуг к JSON файлам
SERVICE_MAPPING = {
    "Персональный тренинг": {"file": "gym.json", "key": "gym", "dir": WORKOUT_DIR},
    "Групповые программы": {"file": "workout.json", "key": "workout", "dir": WORKOUT_DIR},
    "Мини-группы": {"file": None, "key": None, "dir": None},  # Нужно будет добавить файл
    "Водные классы": {"file": "swimming_kids.json", "key": "swimming_kids", "dir": WORKOUT_DIR},
    "Детский фитнес": {"file": "function_kids.json", "key": "function_kids", "dir": KIDS_DIR},
    "Тренажерные залы": {"file": "gym.json", "key": "gym", "dir": WORKOUT_DIR},
    "Функциональные тренировки": {"file": "workout.json", "key": "workout", "dir": WORKOUT_DIR},
    "Студии Пилатеса": {"file": "pilates_studio.json", "key": "pilates_studio", "dir": WORKOUT_DIR},
    "Реабилитация": {"file": None, "key": None, "dir": None}  # Нужно будет добавить файл
}

# Хранение данных о клиентах (в реальном проекте лучше использовать БД)
client_data = {}
CLIENT_DATA_FILE = os.path.join(CLIENT_DIR, "verified_clients.json")


def load_json_file(filepath):
    """Загружает JSON файл"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


def load_client_data():
    """Загружает данные о проверенных клиентах из файла"""
    global client_data
    if os.path.exists(CLIENT_DATA_FILE):
        try:
            with open(CLIENT_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Конвертируем ключи обратно в int (JSON сохраняет ключи как строки)
                client_data = {int(k): v for k, v in data.items()}
        except (json.JSONDecodeError, ValueError, FileNotFoundError):
            client_data = {}
    else:
        client_data = {}


def save_client_data():
    """Сохраняет данные о проверенных клиентах в файл"""
    try:
        # Создаем директорию, если её нет
        os.makedirs(CLIENT_DIR, exist_ok=True)
        with open(CLIENT_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(client_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка при сохранении данных клиентов: {e}")


def is_client_verified(user_id):
    """Проверяет, был ли клиент уже проверен"""
    return user_id in client_data and client_data[user_id].get("verified", False)


def check_client_membership(phone_number):
    """Проверяет, является ли клиент членом клуба"""
    # Загружаем данные о клиентах
    client_log_path = os.path.join(CLIENT_DIR, "client_log.json")
    client_reg_path = os.path.join(CLIENT_DIR, "client_reg.json")
    
    # В реальном проекте здесь должна быть проверка по телефону
    # Пока возвращаем True для всех (можно изменить логику)
    return True


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    if not update.message:
        return
    
    user = update.effective_user
    if not user:
        return
    
    user_id = user.id
    user_name = user.first_name or "пользователь"
    
    # Проверяем, был ли пользователь уже проверен
    if is_client_verified(user_id):
        # Пользователь уже проверен, сразу показываем главное меню
        welcome_text = (
            f"С возвращением, {user_name}! 🏋️‍♀️\n\n"
            "Выберите интересующий вас раздел:"
        )
        await update.message.reply_text(welcome_text)
        await show_main_menu(update, context)
        return
    
    # Приветственное сообщение
    welcome_text = (
        f"Добро пожаловать в фитнес-комплекс Вертикаль Аква, {user_name}! 🏋️‍♀️\n\n"
        "Мы рады видеть вас здесь! Наш бот поможет вам узнать о наших услугах, "
        "тренерах и программах тренировок."
    )
    
    await update.message.reply_text(welcome_text)
    
    # Ждем 2 секунды и отправляем сообщение о проверке
    await asyncio.sleep(2)
    
    check_text = (
        "Для продолжения работы необходимо проверить ваше членство в клубе.\n\n"
        "Пожалуйста, отправьте свой контакт для проверки:"
    )
    
    # Создаем кнопку для отправки контакта
    contact_button = KeyboardButton("📱 Отправить контакт", request_contact=True)
    reply_markup = ReplyKeyboardMarkup(
        [[contact_button]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await update.message.reply_text(check_text, reply_markup=reply_markup)


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик получения контакта от пользователя"""
    if not update.message:
        return
    
    user = update.effective_user
    if not user:
        return
    
    contact = update.message.contact
    
    if contact:
        phone_number = contact.phone_number
        user_id = user.id
        
        # Проверяем членство
        is_member = check_client_membership(phone_number)
        
        if is_member:
            # Сохраняем данные клиента
            contact_name = contact.first_name or user.first_name or "Клиент"
            client_data[user_id] = {
                "phone": phone_number,
                "name": contact_name,
                "verified": True
            }
            
            # Сохраняем данные в файл
            save_client_data()
            
            await update.message.reply_text(
                "✅ Отлично! Ваше членство подтверждено.\n\n"
                "Теперь вы можете пользоваться всеми услугами бота.",
                reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True)  # Убираем клавиатуру
            )
            
            # Показываем главное меню
            await show_main_menu(update, context)
        else:
            await update.message.reply_text(
                "❌ К сожалению, мы не нашли вас в базе членов клуба.\n\n"
                "Пожалуйста, обратитесь к администратору для регистрации.",
                reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True)
            )
    else:
        await update.message.reply_text(
            "Пожалуйста, отправьте контакт, используя кнопку ниже."
        )


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает главное меню с кнопкой Фитнес Услуги"""
    text = "Выберите интересующий вас раздел:"
    
    keyboard = [
        [InlineKeyboardButton("🏋️ Фитнес Услуги", callback_data="fitness_services")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query:
        query = update.callback_query
        if query:
            await query.answer()
            await query.edit_message_text(text, reply_markup=reply_markup)


async def show_fitness_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список фитнес услуг"""
    query = update.callback_query
    if not query:
        return
    await query.answer()
    
    text = "🏋️ Выберите интересующую вас услугу:"
    
    services = [
        "Персональный тренинг",
        "Групповые программы",
        "Мини-группы",
        "Водные классы",
        "Детский фитнес",
        "Тренажерные залы",
        "Функциональные тренировки",
        "Студии Пилатеса",
        "Реабилитация"
    ]
    
    # Создаем кнопки для каждой услуги
    keyboard = []
    for service in services:
        keyboard.append([InlineKeyboardButton(service, callback_data=f"service_{service}")])
    
    # Добавляем кнопку "Назад"
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)


async def show_service_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает информацию об услуге"""
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()
    
    service_name = query.data.replace("service_", "")
    
    # Получаем данные об услуге
    service_config = SERVICE_MAPPING.get(service_name)
    
    if not service_config or not service_config["file"]:
        await query.edit_message_text(
            f"📋 {service_name}\n\n"
            "Информация об этой услуге скоро будет добавлена.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Назад к услугам", callback_data="fitness_services")
            ]])
        )
        return
    
    # Загружаем данные из JSON
    service_dir = service_config.get("dir", WORKOUT_DIR)
    file_path = os.path.join(service_dir, service_config["file"])
    
    data = load_json_file(file_path)
    
    if not data or not isinstance(data, dict):
        await query.edit_message_text(
            f"📋 {service_name}\n\n"
            "Информация об этой услуге пока не добавлена. Мы работаем над этим!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Назад к услугам", callback_data="fitness_services")
            ]])
        )
        return
    
    # Формируем текст с информацией об услуге
    service_key = service_config["key"]
    service_info = data.get(service_key, {})
    
    text = f"📋 {service_name}\n\n"
    
    # Добавляем общую информацию
    if "description" in service_info:
        text += f"📝 {service_info['description']}\n\n"
    
    if "ageGroup" in service_info:
        text += f"👥 Возрастная группа: {service_info['ageGroup']}\n"
    
    if "intensity" in service_info:
        text += f"⚡ Интенсивность: {service_info['intensity']}\n"
    
    if "level" in service_info:
        text += f"📊 Уровень: {service_info['level']}\n"
    
    if "goals" in service_info:
        text += f"\n🎯 Цели:\n"
        for goal in service_info['goals']:
            text += f"• {goal}\n"
    
    # Проверяем наличие тренеров
    trainers = service_info.get("trainers", [])
    
    # Создаем клавиатуру
    keyboard = []
    if trainers:
        keyboard.append([InlineKeyboardButton("👨‍🏫 Тренера", callback_data=f"trainers_{service_name}")])
    keyboard.append([InlineKeyboardButton("◀️ Назад к услугам", callback_data="fitness_services")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)


async def show_trainers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список тренеров для услуги"""
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()
    
    service_name = query.data.replace("trainers_", "")
    service_config = SERVICE_MAPPING.get(service_name)
    
    if not service_config or not service_config["file"]:
        await query.edit_message_text(
            "Тренера для этой услуги не найдены.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Назад", callback_data=f"service_{service_name}")
            ]])
        )
        return
    
    # Загружаем данные
    service_dir = service_config.get("dir", WORKOUT_DIR)
    file_path = os.path.join(service_dir, service_config["file"])
    
    data = load_json_file(file_path)
    
    if not data or not isinstance(data, dict):
        await query.edit_message_text(
            "Информация о тренерах пока не добавлена.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Назад", callback_data=f"service_{service_name}")
            ]])
        )
        return
    
    service_key = service_config["key"]
    service_info = data.get(service_key, {})
    trainers = service_info.get("trainers", [])
    
    if not trainers:
        await query.edit_message_text(
            "Тренера для этой услуги не найдены.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Назад", callback_data=f"service_{service_name}")
            ]])
        )
        return
    
    # Формируем список тренеров
    text = f"👨‍🏫 Тренера - {service_name}\n\n"
    
    keyboard = []
    for trainer in trainers:
        trainer_name = trainer.get("name", "Неизвестно")
        trainer_id = trainer.get("id", 0)
        keyboard.append([
            InlineKeyboardButton(
                f"👤 {trainer_name}",
                callback_data=f"trainer_{service_name}_{trainer_id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=f"service_{service_name}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)


async def show_trainer_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает подробную информацию о тренере"""
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()
    
    # Парсим callback_data: trainer_{service_name}_{trainer_id}
    parts = query.data.split("_", 2)
    if len(parts) < 3:
        await query.answer("Ошибка")
        return
    
    service_name = parts[1]
    trainer_id = int(parts[2])
    
    service_config = SERVICE_MAPPING.get(service_name)
    if not service_config or not service_config["file"]:
        await query.answer("Ошибка")
        return
    
    # Загружаем данные
    service_dir = service_config.get("dir", WORKOUT_DIR)
    file_path = os.path.join(service_dir, service_config["file"])
    
    data = load_json_file(file_path)
    if not data or not isinstance(data, dict):
        await query.answer("Ошибка загрузки данных")
        return
    
    service_key = service_config["key"]
    service_info = data.get(service_key, {})
    trainers = service_info.get("trainers", [])
    
    # Находим тренера
    trainer = None
    for t in trainers:
        if t.get("id") == trainer_id:
            trainer = t
            break
    
    if not trainer:
        await query.answer("Тренер не найден")
        return
    
    # Формируем информацию о тренере
    text = f"👤 {trainer.get('name', 'Неизвестно')}\n\n"
    
    if "age" in trainer:
        text += f"🎂 Возраст: {trainer['age']} лет\n"
    
    if "experienceYears" in trainer:
        text += f"⭐ Опыт работы: {trainer['experienceYears']} лет\n"
    
    if "description" in trainer:
        text += f"\n📝 {trainer['description']}\n"
    
    if "specialization" in trainer:
        text += f"\n🎯 Направления:\n"
        for spec in trainer['specialization']:
            text += f"• {spec}\n"
    
    if "achievements" in trainer:
        text += f"\n🏆 Достижения:\n"
        for achievement in trainer['achievements']:
            text += f"• {achievement}\n"
    
    if "rating" in trainer:
        text += f"\n⭐ Рейтинг: {trainer['rating']}/5.0"
        if "reviewsCount" in trainer:
            text += f" ({trainer['reviewsCount']} отзывов)\n"
    
    keyboard = [[InlineKeyboardButton("◀️ Назад к тренерам", callback_data=f"trainers_{service_name}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback запросов"""
    query = update.callback_query
    if not query or not query.data:
        return
    
    if query.data == "fitness_services":
        await show_fitness_services(update, context)
    elif query.data == "back_to_main":
        await show_main_menu(update, context)
    elif query.data.startswith("service_"):
        await show_service_info(update, context)
    elif query.data.startswith("trainers_"):
        await show_trainers(update, context)
    elif query.data.startswith("trainer_"):
        await show_trainer_info(update, context)


def main():
    """Запуск бота"""
    print("Запуск бота...")
    
    # Загружаем данные о проверенных клиентах
    load_client_data()
    print(f"Загружено данных о {len(client_data)} проверенных клиентах")
    
    # Создаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    # Запускаем бота
    print("Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
