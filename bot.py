import telebot
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from persiantools.jdatetime import JalaliDate, JalaliDateTime
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import ssl
from pytz import UTC
import random

# Ensure SSL compatibility for the environment
try:
    ssl.create_default_context()
except Exception as e:
    print(f"SSL configuration error: {e}")

# Replace 'YOUR_BOT_TOKEN' with your actual Telegram bot token
token = '7885805773:AAGhCZcByxm09610lu1QB4dtWP9YNLA4m64'
bot = telebot.TeleBot(token)

# Configure requests session with retries to handle network issues
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retries)
session.mount('https://', adapter)
session.mount('http://', adapter)
telebot.apihelper._requests_session = session

# File to store user data
DATA_FILE = 'user_data.json'

# Load user data from file
def load_user_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Save user data to file
def save_user_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(user_data, f)

# Dictionary to store user tasks and progress
user_data = load_user_data()

# Scheduler for daily reminders
scheduler = BackgroundScheduler(timezone=UTC)
scheduler.start()

# Add daily task reminders
@scheduler.scheduled_job('cron', hour=6, minute=0)
def morning_reminder():
    for user_id, data in user_data.items():
        tasks_today = [
            task for task in data.get('tasks', [])
            if datetime.fromisoformat(task['time']).date() == datetime.now(UTC).date()
        ]
        if tasks_today:
            task_list = "\\n".join([
                f"- {task['task']}" for task in tasks_today
            ])
            bot.send_message(user_id, f"☀️ یادآوری صبحگاهی:\\nوظایف امروز شما:\\n{task_list}")

# Add nightly task progress report
@scheduler.scheduled_job('cron', hour=23, minute=59)
def nightly_report():
    for user_id, data in user_data.items():
        tasks_today = [
            task for task in data.get('tasks', [])
            if datetime.fromisoformat(task['time']).date() == datetime.now(UTC).date()
        ]
        if tasks_today:
            progress_list = "\\n".join([
                f"- {task['task']}: {task['progress']}% تکمیل شده" for task in tasks_today
            ])
            bot.send_message(user_id, f"🌙 گزارش شبانه:\\nپیشرفت وظایف امروز:\\n{progress_list}")


# Dictionary to manage user states
user_states = {}

# List of random inspirational quotes or poems
inspirational_texts = [
    "✨ هر روز یک آغاز جدید است. از فرصت‌های تازه لذت ببرید!",
    "🌟 زندگی یک ماجراجویی است، آن را با شور و اشتیاق زندگی کنید!",
    "🚀 هر گام کوچک، شما را به سمت هدفتان نزدیک‌تر می‌کند.",
    "🌱 تلاش امروز شما، فردای روشن‌تر را می‌سازد.",
    "💪 شکست‌ها، پله‌هایی برای موفقیت هستند.",
    "🔥 به توانایی‌هایتان باور داشته باشید و قدم بردارید.",
    "🌟 زندگی فرصتی برای بهبود مستمر است.",
    "🧗‍♂️ هر چالش یک فرصت برای رشد است.",
    "🌈 در هر لحظه زیبایی و پیشرفت وجود دارد، به دنبالش باشید.",
    "🕒 زمان می‌گذرد؛ از هر لحظه استفاده کنید.",
    "✨ تغییر از همین حالا شروع می‌شود.",
    "🚴‍♀️ حرکت کنید، حتی اگر آهسته باشد.",
    "🔑 تمرکز و تعهد، کلید دروازه موفقیت است.",
    "🏆 هر پیروزی، نتیجه تلاش‌های پیوسته است.",
    "🌻 با انگیزه بمانید و به راهتان ادامه دهید.",
    "📚 یادگیری هیچ‌گاه پایان ندارد، به جلو حرکت کنید.",
    "🎯 اهداف شما به اندازه تلاش‌هایتان واقعی هستند.",
    "🛤 مسیر موفقیت با صبر و استمرار ساخته می‌شود.",
    "✈️ پرواز کنید، حتی اگر بال‌هایتان خسته باشند.",
    "🌌 به رویاهایتان نزدیک‌تر شوید، آن‌ها منتظر شما هستند.",
    "🔄 شکست‌ها را به دروس تبدیل کنید و ادامه دهید.",
    "🌎 به یاد داشته باشید، تأثیر شما فراتر از آن چیزی است که فکر می‌کنید.",
    "🏋️‍♀️ تلاش‌هایتان را با عشق و انگیزه ادامه دهید.",
    "🌞 هر روز فرصت جدیدی برای درخشش است.",
    "🌵 در دل سختی‌ها، زیبایی‌های موفقیت نهفته است.",
    "💡 از اشتباهات خود بیاموزید و قوی‌تر شوید.",
    "🕊 آزادی در رسیدن به اهداف، هدیه‌ای از تلاش است.",
     
]

def month_name_to_number(month_name):
    months = {
        'فروردین': 1, 'اردیبهشت': 2, 'خرداد': 3,
        'تیر': 4, 'مرداد': 5, 'شهریور': 6,
        'مهر': 7, 'آبان': 8, 'آذر': 9,
        'دی': 10, 'بهمن': 11, 'اسفند': 12
    }
    return months.get(month_name, 0)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_first_name = message.from_user.first_name
    user_id = str(message.chat.id)

    if user_id not in user_data:
        # Ensure proper right-to-left alignment for non-RTL names
        formatted_name = f"\u202B{user_first_name}"
        random_quote = random.choice(inspirational_texts)
        bot.send_message(
            message.chat.id,
            f"""👋 {formatted_name} عزیز، به ربات مدیریت وظایف خوش آمدید!
{random_quote}

با استفاده از دستورات زیر شروع کنید:
/start - شروع
/add_task - افزودن وظیفه جدید
/view_tasks - مشاهده وظایف
/delete_tasks - حذف وظایف
/update_progress - بروزرسانی پیشرفت
/go_home - بازگشت به منوی اصلی"""
        )
        user_data[user_id] = {'tasks': [], 'welcome_sent': True}  # Initialize user data
        save_user_data()
    else:
        formatted_name = f"\u202B{user_first_name}"
        random_quote = random.choice(inspirational_texts)
        bot.send_message(
            message.chat.id,
            f"""👋 {formatted_name} عزیز، خوش آمدید!
{random_quote}

می‌توانید وظایف جدیدی اضافه کنید یا از دستورات زیر استفاده کنید:
/start - شروع دوباره
/add_task - افزودن وظیفه جدید
/view_tasks - مشاهده وظایف
/delete_tasks - حذف وظایف
/update_progress - بروزرسانی پیشرفت
/go_home - بازگشت به منوی اصلی"""
        )

@bot.message_handler(commands=['add_task'])
def add_task_command(message):
    bot.send_message(message.chat.id, "لطفاً توضیح وظیفه را ارسال کنید.")
    user_states[message.chat.id] = 'add_task'

@bot.message_handler(commands=['view_tasks'])
def view_tasks_command(message):
    view_tasks(message.chat.id)

@bot.message_handler(commands=['delete_tasks'])
def delete_tasks_command(message):
    delete_tasks(message.chat.id)

@bot.message_handler(commands=['update_progress'])
def update_progress_command(message):
    update_progress(message.chat.id)

@bot.message_handler(commands=['go_home'])
def go_home_command(message):
    bot.send_message(message.chat.id, "بازگشت به منوی اصلی.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    state = user_states.get(message.chat.id)
    if state == 'add_task':
        ask_task_time(message)
    elif state == 'save_task':
        save_task(message)
    elif state == 'task_completion':
        handle_task_completion(message)
    elif state == 'delete_task':
        handle_delete_input(message)
    elif state == 'progress_update':
        handle_progress_input(message)
    else:
        bot.send_message(message.chat.id, "لطفاً یک دستور معتبر وارد کنید.")


def ask_task_time(message):
    user_id = str(message.chat.id)
    task = message.text.strip()
    if task:
        if user_id not in user_data:
            user_data[user_id] = {'tasks': []}
        user_data[user_id]['pending_task'] = task
        bot.send_message(user_id, "لطفاً تاریخ و زمان موردنظر خود را وارد کنید (فرمت: روز ماه ساعت:دقیقه یا سال روز ماه ساعت:دقیقه). مثال: 17 دی 14:30 یا 1403 17 دی 14:30")
        user_states[message.chat.id] = 'save_task'
    else:
        bot.send_message(user_id, "توضیحات وظیفه نمی‌تواند خالی باشد. لطفاً دوباره تلاش کنید.")

def save_task(message):
    user_id = str(message.chat.id)
    try:
        parts = message.text.strip().split()
        if len(parts) == 3:
            day = int(parts[0])
            month = month_name_to_number(parts[1])
            time_parts = parts[2].split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            jalali_date = JalaliDate.today()
            if day < jalali_date.day and month == jalali_date.month:
                bot.send_message(user_id, "تاریخ گذشته معتبر نیست. لطفاً یک تاریخ آینده وارد کنید.")
                return
            gregorian_date = JalaliDateTime(jalali_date.year, month, day).to_gregorian()
            task_time = datetime(gregorian_date.year, gregorian_date.month, gregorian_date.day, hour, minute).astimezone(UTC)
        elif len(parts) == 4:
            year = int(parts[0])
            day = int(parts[1])
            month = month_name_to_number(parts[2])
            time_parts = parts[3].split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            gregorian_date = JalaliDateTime(year, month, day).to_gregorian()
            task_time = datetime(gregorian_date.year, gregorian_date.month, gregorian_date.day, hour, minute).astimezone(UTC)
        else:
            bot.send_message(user_id, "فرمت وارد شده نامعتبر است. لطفاً دوباره تلاش کنید.")
            return

        task = user_data[user_id].pop('pending_task', None)
        if task:
            user_data[user_id]['tasks'].append({'task': task, 'time': task_time.isoformat(), 'progress': 0})
            save_user_data()

            # Schedule reminders for the task
            schedule_task_reminders(user_id, task, task_time)

            bot.send_message(user_id, f"وظیفه افزوده شد: {task}")
        else:
            bot.send_message(user_id, "خطایی رخ داد. لطفاً دوباره تلاش کنید.")
    except ValueError:
        bot.send_message(user_id, "لطفاً ورودی معتبری وارد کنید.")

def schedule_task_reminders(user_id, task, task_time):
    eight_hours_before = task_time - timedelta(hours=8)
    one_hour_before = task_time - timedelta(hours=1)
    ten_minutes_before = task_time - timedelta(minutes=10)

    if eight_hours_before > datetime.now(UTC):
        scheduler.add_job(lambda: send_reminder(user_id, task, "8 ساعت مانده"), 'date', run_date=eight_hours_before)
    if one_hour_before > datetime.now(UTC):
        scheduler.add_job(lambda: send_reminder(user_id, task, "1 ساعت مانده"), 'date', run_date=one_hour_before)
    if ten_minutes_before > datetime.now(UTC):
        scheduler.add_job(lambda: send_reminder(user_id, task, "10 دقیقه مانده"), 'date', run_date=ten_minutes_before)

    scheduler.add_job(lambda: send_reminder(user_id, task, "اکنون زمان انجام این وظیفه است!"), 'date', run_date=task_time)

def send_reminder(user_id, task, reminder_time):
    bot.send_message(user_id, f"⏰ یادآوری وظیفه:\nوظیفه: {task}\nزمان: {reminder_time}")

def view_tasks(chat_id):
    user_id = str(chat_id)
    if user_id in user_data and user_data[user_id]['tasks']:
        tasks = user_data[user_id]['tasks']
        task_list = "\n".join([
            f"{i+1}. {t['task']}"
            for i, t in enumerate(tasks)
        ])
        bot.send_message(chat_id, f"وظایف شما:\n{task_list}\nاگر وظیفه‌ای را انجام دادید، شماره آن را همراه با کلمه 'اتمام' ارسال کنید. مثال: 1 اتمام")
        user_states[chat_id] = 'task_completion'
    else:
        bot.send_message(chat_id, "هیچ وظیفه‌ای یافت نشد. برای اضافه کردن وظیفه جدید از دستور /add_task استفاده کنید.")


def handle_task_completion(message):
    user_id = str(message.chat.id)
    try:
        input_parts = message.text.strip().split(maxsplit=1)
        if len(input_parts) == 2 and input_parts[1].strip().lower() == 'اتمام':
            task_index = int(input_parts[0]) - 1
            if user_id in user_data and 0 <= task_index < len(user_data[user_id]['tasks']):
                completed_task = user_data[user_id]['tasks'].pop(task_index)
                save_user_data()
                bot.send_message(message.chat.id, f"وظیفه '{completed_task['task']}' با موفقیت به اتمام رسید و حذف شد.")
            else:
                bot.send_message(message.chat.id, "وظیفه‌ای با این شماره یافت نشد.")
        else:
            bot.send_message(message.chat.id, "فرمت ورودی نادرست است. لطفاً شماره وظیفه را به همراه کلمه 'اتمام' ارسال کنید.")
    except (ValueError, IndexError):
        bot.send_message(message.chat.id, "ورودی نامعتبر است. لطفاً شماره وظیفه را به همراه کلمه 'اتمام' ارسال کنید.")
    view_tasks(message.chat.id)

def delete_tasks(chat_id):
    user_id = str(chat_id)
    if user_id in user_data and user_data[user_id]['tasks']:
        tasks = user_data[user_id]['tasks']
        task_list = "\n".join([
            f"{i+1}. {t['task']}"
            for i, t in enumerate(tasks)
        ])
        task_list += f"\n{len(tasks)+1}. حذف همه وظایف"
        bot.send_message(chat_id, f"وظایف شما:\n{task_list}\nبرای حذف وظیفه، شماره آن را ارسال کنید.")
        user_states[chat_id] = 'delete_task'
    else:
        bot.send_message(chat_id, "هیچ وظیفه‌ای برای حذف وجود ندارد. برای اضافه کردن وظیفه جدید از دستور /add_task استفاده کنید.")

def handle_delete_input(message):
    user_id = str(message.chat.id)
    input_text = message.text.strip()
    try:
        task_index = int(input_text) - 1
        if user_id in user_data:
            if task_index == len(user_data[user_id]['tasks']):
                user_data[user_id]['tasks'] = []
                save_user_data()
                bot.send_message(message.chat.id, "تمام وظایف با موفقیت حذف شدند.")
            elif 0 <= task_index < len(user_data[user_id]['tasks']):
                removed_task = user_data[user_id]['tasks'].pop(task_index)
                save_user_data()
                bot.send_message(message.chat.id, f"وظیفه '{removed_task['task']}' با موفقیت حذف شد.")
            else:
                bot.send_message(message.chat.id, "شماره وارد شده نامعتبر است.")
        else:
            bot.send_message(chat_id, "هیچ وظیفه‌ای برای حذف وجود ندارد. برای اضافه کردن وظیفه جدید از دستور /add_task استفاده کنید.")
    except ValueError:
        bot.send_message(message.chat.id, "لطفاً یک شماره معتبر وارد کنید.")

def update_progress(chat_id):
    user_id = str(chat_id)
    if user_id in user_data and user_data[user_id]['tasks']:
        tasks = user_data[user_id]['tasks']
        task_list = "\n".join([
            f"{i+1}. {t['task']} - پیشرفت: {t['progress']}%"
            for i, t in enumerate(tasks)
        ])
        bot.send_message(chat_id, f"وظایف شما:\n{task_list}\nبرای ثبت پیشرفت، شماره وظیفه و درصد پیشرفت را ارسال کنید.\nمثال: 1 50 (وظیفه 1 با 50% پیشرفت)")
        user_states[chat_id] = 'progress_update'
    else:
        bot.send_message(chat_id, "هیچ وظیفه‌ای برای ثبت پیشرفت وجود ندارد. برای اضافه کردن وظیفه جدید از دستور /add_task استفاده کنید.")

def handle_progress_input(message):
    user_id = str(message.chat.id)
    try:
        input_parts = message.text.strip().split()
        if len(input_parts) == 2:
            task_index = int(input_parts[0]) - 1
            progress = int(input_parts[1])
            if user_id in user_data and 0 <= task_index < len(user_data[user_id]['tasks']) and 0 <= progress <= 100:
                user_data[user_id]['tasks'][task_index]['progress'] = progress
                save_user_data()
                bot.send_message(message.chat.id, f"پیشرفت وظیفه '{user_data[user_id]['tasks'][task_index]['task']}' به {progress}% به‌روزرسانی شد.")
            else:
                bot.send_message(message.chat.id, "ورودی نامعتبر است. لطفاً شماره وظیفه و درصد پیشرفت معتبر وارد کنید.")
        else:
            bot.send_message(message.chat.id, "فرمت ورودی نادرست است. لطفاً دوباره تلاش کنید.")
    except ValueError:
        bot.send_message(message.chat.id, "لطفاً ورودی معتبری وارد کنید.")

if __name__ == '__main__':
    try:
        import logging
        logging.basicConfig(level=logging.INFO)
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        scheduler.shutdown()
