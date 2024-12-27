
import logging
import sqlite3
import os
import telebot
from telebot import types
from datetime import datetime, timedelta
import random
import string
# ============================
# Configuration Section
# ============================

# IMPORTANT: For security reasons, **never share your bot token publicly**.
# The token below is an example. Replace it with your actual bot token.
BOT_TOKEN = "7226809374:AAEXd8c3ulo6HB6n8TcPYgyIp300EeoJsW4"  # Replace with your Bot Token
ADMIN_IDS = "1105522303,6943911086,155618958,6319243149".split(",")  # Replace with actual admin Telegram user IDs
ADMIN_IDS = [int(admin_id.strip()) for admin_id in ADMIN_IDS]
CHANNEL_USERNAME = "sut_tribune"  # Without @


SUPER_ADMIN_ID = 6943911086



# ============================
# Logging Configuration
# ============================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================
# Database Setup
# ============================

# Connect to SQLite database (it will be created if it doesn't exist)
conn = sqlite3.connect("messages.db", check_same_thread=False)
cursor = conn.cursor()

# Create messages table if it doesn't exist
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message TEXT,
        status TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        channel_message_id INTEGER,
        parent_message_id INTEGER
    )
    """
)
conn.commit()

# Create users table to store user details and random names
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        random_name TEXT,
        last_name_reset DATETIME,
        role TEXT DEFAULT 'user'
    )
    """
)
conn.commit()

# Create replies table to manage reply states (optional for better persistence)
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS replies (
        user_id INTEGER PRIMARY KEY,
        target_message_id INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
)
conn.commit()

# ============================
# Initialize Bot
# ============================

bot = telebot.TeleBot(BOT_TOKEN)

# ============================
# Helper Functions
# ============================

def is_super_admin(user_id: int) -> bool:
    """
    Checks if a user ID is the super admin.
    """
    return user_id == SUPER_ADMIN_ID

@bot.message_handler(commands=['help'])
def handle_help(message):
    """
    Handles the /help command. Provides information about how to use the bot for users.
    """
    help_text = (
        "📌 <b>راهنمای ربات ناشناس:</b>\n\n"
        "👤 <b>ارسال پیام:</b>\n"
        "فقط کافی است نگرانی، دغدغه یا پیام خود را به صورت متن ارسال کنید.\n"
        "پیام شما پس از بررسی توسط مدیران تایید یا رد خواهد شد.\n\n"
        "🔄 <b>درخواست نام جدید:</b>\n"
        "می‌توانید هر ۱۴ روز یکبار نام تصادفی جدید درخواست کنید تا هویت شما ناشناس باقی بماند.\n"
        "📌 دستور: <code>/newname</code>\n\n"
        "💬 <b>پاسخ به پیام‌های کانال:</b>\n"
        "در کانال ما، زیر هر پیام تایید شده یک دکمه‌ی <b>پاسخ (💬)</b> قرار دارد.\n"
        "با کلیک بر روی این دکمه، می‌توانید به آن پیام پاسخ دهید.\n"
        "پاسخ شما نیز پس از بررسی توسط مدیران تایید یا رد خواهد شد.\n\n"
        "ℹ️ <b>دستورهای دیگر:</b>\n"
        "📌 <code>/start</code> - شروع تعامل با ربات و دریافت پیام خوش‌آمدگویی.\n"
        "📌 <code>/help</code> - نمایش راهنمای استفاده از ربات.\n"
    )
    bot.send_message(chat_id=message.chat.id, text=help_text, parse_mode='HTML')

def is_admin(user_id: int) -> bool:
    """
    Checks if a user ID is in the list of admin IDs or has 'admin' or 'super_admin' role.
    """
    if user_id in ADMIN_IDS:
        return True
    # Check role from users table
    cursor.execute("SELECT role FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    if result and result[0] in ['admin', 'super_admin']:
        return True
    return False

def generate_random_name() -> str:
    """
    Generates a unique random name for a user with positive adjectives.
    """
    adjectives = [
        "هوشمند", "شاداب", "خلاق", "مهربان", "شجاع",
        "دلنشین", "پرانرژی", "بااستعداد", "دانشمند",
        "پویان", "متحرک", "پرشور", "باورمند", "منظم"
    ]
    
    nouns = [
        "رعد", "سحر", "برق", "نور", "شهاب",
        "بهمن", "آذر", "شهرزاد", "سوزان",
        "لیلا", "فناوری", "فیزیک", "کوانتوم",
        "ترمودینامیک", "الکترون", "فرمول",
        "مدار", "ذره", "انرژی", "نظریه",
        "پروتون", "نیوترون", "فوتون", "مغناطیس",
        "گرانش", "تابش"
    ]
    
    while True:
        adjective = random.choice(adjectives)
        noun = random.choice(nouns)
        number = ''.join(random.choices(string.digits, k=2))
        random_name = f"{noun} {adjective}{number}"
        # Ensure the random name is unique
        cursor.execute("SELECT random_name FROM users WHERE random_name=?", (random_name,))
        if not cursor.fetchone():
            return random_name

def get_user_details(message) -> dict:
    """
    Extracts user details from the message.
    """
    user = message.from_user
    return {
        "user_id": user.id,
        "username": user.username if user.username else "",
        "first_name": user.first_name if user.first_name else "",
        "last_name": user.last_name if user.last_name else ""
    }

def get_user_random_name(user_id: int) -> str:
    """
    Retrieves the user's random name. If not exists, creates one.
    """
    cursor.execute("SELECT random_name FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        random_name = generate_random_name()
        cursor.execute(
            "INSERT INTO users (user_id, random_name, last_name_reset, role) VALUES (?, ?, ?, ?)",
            (user_id, random_name, datetime.now(), 'user')
        )
        conn.commit()
        return random_name

def can_reset_name(user_id: int) -> bool:
    """
    Checks if the user can reset their random name (every 14 days).
    """
    cursor.execute("SELECT last_name_reset FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    if result:
        last_reset = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
        if datetime.now() - last_reset >= timedelta(days=14):
            return True
    return False

def reset_user_random_name(user_id: int) -> str:
    """
    Resets the user's random name if 14 days have passed since the last reset.
    """
    if can_reset_name(user_id):
        new_random_name = generate_random_name()
        cursor.execute(
            "UPDATE users SET random_name=?, last_name_reset=? WHERE user_id=?",
            (new_random_name, datetime.now(), user_id)
        )
        conn.commit()
        return new_random_name
    else:
        return ""

def send_admin_notification(message_id: int, user_random_name: str, user_details: dict, message_text: str, parent_message_id: int = None):
    """
    Sends a notification to all admins about a new message with inline keyboard.
    """
    inline_kb = types.InlineKeyboardMarkup()
    approve_btn = types.InlineKeyboardButton(text="✅ تأیید", callback_data=f"approve:{message_id}")
    reject_btn = types.InlineKeyboardButton(text="❌ رد", callback_data=f"reject:{message_id}")
    inline_kb.add(approve_btn, reject_btn)
    
    if parent_message_id:
        admin_message = (
            f"🆕 <b>پاسخ جدید دریافت شد</b>\n\n"
            f"<b>شناسه پاسخ:</b> <code>{message_id}</code>\n"
            f"<b>شناسه پیام اصلی:</b> <code>{parent_message_id}</code>\n"
            f"<b>نام تصادفی کاربر:</b> {user_random_name}\n"
            f"<b>جزئیات کاربر:</b>\n"
            f"• <b>نام:</b> {user_details['first_name']} {user_details['last_name']}\n"
            f"• <b>نام کاربری:</b> @{user_details['username']}\n"
            f"<b>پاسخ:</b> {message_text}"
        )
    else:
        admin_message = (
            f"🆕 <b>پیام جدید دریافت شد</b>\n\n"
            f"<b>شناسه پیام:</b> <code>{message_id}</code>\n"
            f"<b>نام تصادفی کاربر:</b> {user_random_name}\n"
            f"<b>جزئیات کاربر:</b>\n"
            f"• <b>نام:</b> {user_details['first_name']} {user_details['last_name']}\n"
            f"• <b>نام کاربری:</b> @{user_details['username']}\n"
            f"<b>پیام:</b> {message_text}"
        )
    
    for admin_id in ADMIN_IDS:
        try:
            bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                parse_mode='HTML',
                reply_markup=inline_kb
            )
        except Exception as e:
            logger.error(f"Error sending message to admin {admin_id}: {e}")

def send_approval_notification(admin_id: int, message_id: int):
    """
    Optionally notify the approving admin about the approval.
    """
    notification = f"✅ پیام شماره <code>{message_id}</code> تایید و به کانال ارسال شد."
    try:
        bot.send_message(
            chat_id=admin_id,
            text=notification,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error notifying admin {admin_id} about approval: {e}")

def send_rejection_notification(admin_id: int, message_id: int):
    """
    Optionally notify the rejecting admin about the rejection.
    """
    notification = f"❌ پیام شماره <code>{message_id}</code> رد شد."
    try:
        bot.send_message(
            chat_id=admin_id,
            text=notification,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error notifying admin {admin_id} about rejection: {e}")

def add_admin(admin_id: int):
    """
    Adds an admin by updating the user's role to 'admin'.
    """
    cursor.execute("UPDATE users SET role='admin' WHERE user_id=?", (admin_id,))
    if cursor.rowcount == 0:
        # User not in the database, add them as admin
        cursor.execute(
            "INSERT INTO users (user_id, role) VALUES (?, ?)",
            (admin_id, 'admin')
        )
    conn.commit()

def remove_admin(admin_id: int):
    """
    Removes an admin by updating the user's role to 'user'.
    """
    cursor.execute("UPDATE users SET role='user' WHERE user_id=?", (admin_id,))
    conn.commit()

# ============================
# Command Handlers
# ============================

@bot.message_handler(commands=['start'])
def handle_start(message):
    """
    Handles the /start command. Sends a welcome message to the user.
    """
    welcome_text = (
        "سلام! به ربات ناشناس ما خوش آمدید.\n"
        "شما می‌توانید نگرانی‌ها و دغدغه‌های خود را به صورت ناشناس با ما در میان بگذارید.\n\n"
        "برای ارسال پیام، کافی است متن خود را ارسال کنید.\n"
        "همچنین می‌توانید نام تصادفی خود را مشاهده یا درخواست کنید.\n\n"
        "دستورهای مفید:\n"
        "/newname - درخواست نام جدید (هر ۱۴ روز یکبار)\n"
        "/help - نمایش راهنما"
    )
    bot.send_message(chat_id=message.chat.id, text=welcome_text)

 
@bot.message_handler(commands=['newname'])
def handle_newname(message):
    """
    Handles the /newname command. Allows users to request a new random name every 14 days.
    """
    user_id = message.from_user.id
    if can_reset_name(user_id):
        new_name = reset_user_random_name(user_id)
        if new_name:
            cursor.execute("SELECT username, first_name, last_name FROM users WHERE user_id=?", (user_id,))
            result = cursor.fetchone()
            if result:
                username = result[0] if result[0] else ""
                first_name = result[1] if result[1] else ""
                last_name = result[2] if result[2] else ""
                # Update user details if necessary
                cursor.execute(
                    "UPDATE users SET username=?, first_name=?, last_name=? WHERE user_id=?",
                    (username, first_name, last_name, user_id)
                )
                conn.commit()
            bot.reply_to(message, f"✅ نام شما با موفقیت به <b>{new_name}</b> تغییر یافت.", parse_mode='HTML')
        else:
            bot.reply_to(message, "❌ مشکلی در تغییر نام پیش آمد. لطفاً دوباره تلاش کنید.")
    else:
        cursor.execute("SELECT last_name_reset FROM users WHERE user_id=?", (user_id,))
        result = cursor.fetchone()
        if result:
            last_reset = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
            next_reset = last_reset + timedelta(days=14)
            remaining = next_reset - datetime.now()
            if remaining.total_seconds() > 0:
                days = remaining.days
                hours = remaining.seconds // 3600
                minutes = (remaining.seconds % 3600) // 60
                bot.reply_to(message, f"❌ شما هنوز نمی‌توانید نام جدید درخواست کنید.\nلطفاً بعد از {days} روز، {hours} ساعت و {minutes} دقیقه دوباره تلاش کنید.")
            else:
                bot.reply_to(message, "❌ مشکلی در تغییر نام پیش آمد. لطفاً دوباره تلاش کنید.")
        else:
            bot.reply_to(message, "❌ مشکلی در یافتن اطلاعات شما پیش آمد.")

@bot.message_handler(commands=['addadmin'])
def handle_addadmin(message):
    """
    Handles the /addadmin command. Super admin can add an admin by specifying the user's Telegram ID.
    Usage: /addadmin <user_id>
    """
    user_id = message.from_user.id
    if not is_super_admin(user_id):
        bot.reply_to(message, "❌ شما اجازه استفاده از این دستور را ندارید.")
        return

    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            bot.reply_to(message, "❌ لطفاً دستور را به صورت /addadmin <user_id> وارد کنید.")
            return
        new_admin_id = int(parts[1])
        add_admin(new_admin_id)
        bot.reply_to(message, f"✅ کاربر با شناسه {new_admin_id} به مدیر اضافه شد.")
    except ValueError:
        bot.reply_to(message, "❌ شناسه کاربر نامعتبر است.")

@bot.message_handler(commands=['removeadmin'])
def handle_removeadmin(message):
    """
    Handles the /removeadmin command. Super admin can remove an admin by specifying the user's Telegram ID.
    Usage: /removeadmin <user_id>
    """
    user_id = message.from_user.id
    if not is_super_admin(user_id):
        bot.reply_to(message, "❌ شما اجازه استفاده از این دستور را ندارید.")
        return

    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            bot.reply_to(message, "❌ لطفاً دستور را به صورت /removeadmin <user_id> وارد کنید.")
            return
        remove_admin_id = int(parts[1])
        remove_admin(remove_admin_id)
        bot.reply_to(message, f"✅ کاربر با شناسه {remove_admin_id} از مدیران حذف شد.")
    except ValueError:
        bot.reply_to(message, "❌ شناسه کاربر نامعتبر است.")

@bot.message_handler(commands=['superadmin'])
def handle_superadmin(message):
    """
    Handles the /superadmin command. Super admin can add another super admin.
    Usage: /superadmin <user_id>
    """
    user_id = message.from_user.id
    if not is_super_admin(user_id):
        bot.reply_to(message, "❌ شما اجازه استفاده از این دستور را ندارید.")
        return

    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            bot.reply_to(message, "❌ لطفاً دستور را به صورت /superadmin <user_id> وارد کنید.")
            return
        new_super_admin_id = int(parts[1])
        cursor.execute("UPDATE users SET role='super_admin' WHERE user_id=?", (new_super_admin_id,))
        if cursor.rowcount == 0:
            # User not in the database, add them as super_admin
            cursor.execute(
                "INSERT INTO users (user_id, role) VALUES (?, ?)",
                (new_super_admin_id, 'super_admin')
            )
        conn.commit()
        bot.reply_to(message, f"✅ کاربر با شناسه {new_super_admin_id} به سوپرادمین اضافه شد.")
    except ValueError:
        bot.reply_to(message, "❌ شناسه کاربر نامعتبر است.")

@bot.message_handler(commands=['remove_superadmin'])
def handle_remove_superadmin(message):
    """
    Handles the /remove_superadmin command. Super admin can remove another super admin by specifying the user's Telegram ID.
    Usage: /remove_superadmin <user_id>
    """
    user_id = message.from_user.id
    if not is_super_admin(user_id):
        bot.reply_to(message, "❌ شما اجازه استفاده از این دستور را ندارید.")
        return

    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            bot.reply_to(message, "❌ لطفاً دستور را به صورت /remove_superadmin <user_id> وارد کنید.")
            return
        remove_super_admin_id = int(parts[1])
        cursor.execute("UPDATE users SET role='user' WHERE user_id=?", (remove_super_admin_id,))
        conn.commit()
        bot.reply_to(message, f"✅ کاربر با شناسه {remove_super_admin_id} از سوپرادمین‌ها حذف شد.")
    except ValueError:
        bot.reply_to(message, "❌ شناسه کاربر نامعتبر است.")

@bot.message_handler(commands=['listadmins'])
def handle_listadmins(message):
    """
    Handles the /listadmins command. Lists all current admins and super admins.
    """
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.reply_to(message, "❌ شما اجازه دسترسی به این دستور را ندارید.")
        return

    cursor.execute("SELECT user_id, role FROM users WHERE role IN ('admin', 'super_admin')")
    admins = cursor.fetchall()
    if not admins:
        bot.reply_to(message, "✅ هیچ مدیری وجود ندارد.")
        return

    admin_text = "👥 <b>لیست مدیران:</b>\n\n"
    for admin in admins:
        admin_id, role = admin
        role_display = "سوپرادمین" if role == 'super_admin' else "مدیر"
        admin_text += f"• <code>{admin_id}</code> - {role_display}\n"
    
    bot.send_message(chat_id=message.chat.id, text=admin_text, parse_mode='HTML')

# ============================
# Callback Query Handler
# ============================

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve:") or call.data.startswith("reject:") or call.data.startswith("reply:"))
def callback_inline(call):
    """
    Handles all callback queries from inline keyboards.
    """
    if call.message:
        try:
            data = call.data.split(":")
            action = data[0]
            if len(data) < 2:
                bot.answer_callback_query(call.id, "❌ داده نامعتبر.", show_alert=True)
                return
            message_id = int(data[1])
            
            user_id = call.from_user.id

            if action in ["approve", "reject"]:
                if not is_admin(user_id):
                    bot.answer_callback_query(call.id, "❌ شما اجازه دسترسی به این دکمه را ندارید.", show_alert=True)
                    return

                # Handle approve or reject
                cursor.execute("SELECT user_id, message, status, parent_message_id FROM messages WHERE id=?", (message_id,))
                result = cursor.fetchone()

                if not result:
                    bot.answer_callback_query(call.id, "❌ پیام مورد نظر یافت نشد.", show_alert=True)
                    return

                target_user_id, message_text, status, parent_message_id = result

                if status != "pending":
                    bot.answer_callback_query(call.id, "❌ این پیام قبلاً بررسی شده است.", show_alert=True)
                    return

                if action == "approve":
                    # Fetch user's random name
                    cursor.execute("SELECT random_name FROM users WHERE user_id=?", (target_user_id,))
                    user_result = cursor.fetchone()
                    if user_result:
                        user_random_name = user_result[0]
                    else:
                        user_random_name = "کاربر ناشناس"

                    # Prepare the message to send to channel
                    channel_message = f"<b>{user_random_name}</b> :\n\n{message_text}"

                    try:
                        if parent_message_id:
                            # Fetch the channel_message_id of the parent message
                            cursor.execute("SELECT channel_message_id FROM messages WHERE id=?", (parent_message_id,))
                            parent_result = cursor.fetchone()
                            if parent_result and parent_result[0]:
                                reply_to_id = parent_result[0]
                            else:
                                reply_to_id = None
                        else:
                            reply_to_id = None

                        sent_message = bot.send_message(
                            chat_id=f"@{CHANNEL_USERNAME}",
                            text=channel_message,
                            parse_mode='HTML',
                            reply_to_message_id=reply_to_id
                        )
                        channel_message_id = sent_message.message_id
                        # Update the message with channel_message_id
                        cursor.execute("UPDATE messages SET status='approved', channel_message_id=? WHERE id=?", (channel_message_id, message_id))
                        conn.commit()
                    except Exception as e:
                        logger.error(f"Error sending message to channel: {e}")
                        bot.answer_callback_query(call.id, "❌ مشکلی در ارسال پیام به کانال پیش آمد.", show_alert=True)
                        return

                    # Add 'Reply' button to the channel message
                    reply_btn = types.InlineKeyboardButton(text="💬 پاسخ", callback_data=f"reply:{message_id}")
                    inline_kb = types.InlineKeyboardMarkup().add(reply_btn)
                    try:
                        bot.edit_message_reply_markup(chat_id=f"@{CHANNEL_USERNAME}", message_id=channel_message_id, reply_markup=inline_kb)
                    except Exception as e:
                        logger.error(f"Error adding reply button to channel message: {e}")

                    # Notify the approving admin
                    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
                    bot.send_message(call.message.chat.id, f"✅ پیام شماره <code>{message_id}</code> تایید و به کانال ارسال شد.", parse_mode='HTML')

                    # Notify other admins about the approval
                    approval_notification = f"✅ پیام شماره <code>{message_id}</code> توسط @{call.from_user.username} تایید و به کانال ارسال شد."
                    for admin_id in ADMIN_IDS:
                        if admin_id != user_id:
                            try:
                                bot.send_message(
                                    chat_id=admin_id,
                                    text=approval_notification,
                                    parse_mode='HTML'
                                )
                            except Exception as e:
                                logger.error(f"Error notifying admin {admin_id} about approval: {e}")

                    # Notify the original user
                    try:
                        bot.send_message(
                            chat_id=target_user_id,
                            text="پیام شما تایید شد و در کانال منتشر گردید."
                        )
                    except Exception as e:
                        logger.error(f"Error notifying user {target_user_id}: {e}")

                elif action == "reject":
                    # Update message status to 'rejected'
                    cursor.execute("UPDATE messages SET status='rejected' WHERE id=?", (message_id,))
                    conn.commit()

                    # Notify the rejecting admin
                    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
                    bot.send_message(call.message.chat.id, f"❌ پیام شماره <code>{message_id}</code> رد شد.", parse_mode='HTML')

                    # Notify other admins about the rejection
                    rejection_notification = f"❌ پیام شماره <code>{message_id}</code> توسط @{call.from_user.username} رد شد."
                    for admin_id in ADMIN_IDS:
                        if admin_id != user_id:
                            try:
                                bot.send_message(
                                    chat_id=admin_id,
                                    text=rejection_notification,
                                    parse_mode='HTML'
                                )
                            except Exception as e:
                                logger.error(f"Error notifying admin {admin_id} about rejection: {e}")

                    # Notify the original user
                    try:
                        bot.send_message(
                            chat_id=target_user_id,
                            text="متاسفانه پیام شما به دلیل نقض قوانین منتشر نمی‌شود."
                        )
                    except Exception as e:
                        logger.error(f"Error notifying user {target_user_id}: {e}")

            elif action == "reply":
                # Handle reply action
                message_id = int(data[1])
                # Fetch target user_id from messages table
                cursor.execute("SELECT user_id FROM messages WHERE id=?", (message_id,))
                result = cursor.fetchone()
                if not result:
                    bot.answer_callback_query(call.id, "❌ پیام مورد نظر یافت نشد.", show_alert=True)
                    return
                target_user_id = result[0]
                # Record that this user is replying to target_message_id in replies table
                cursor.execute(
                    "INSERT OR REPLACE INTO replies (user_id, target_message_id, timestamp) VALUES (?, ?, ?)",
                    (user_id, message_id, datetime.now())
                )
                conn.commit()
                # Prompt the user to send their reply
                bot.answer_callback_query(call.id, "✍️در بات لطفاً پاسخ خود را ارسال کنید.", show_alert=True)
                bot.send_message(call.from_user.id, "✍️ پاسخ خود را اینجا ارسال کنید:")

            else:
                bot.answer_callback_query(call.id, "❌ عملیات نامعتبر.", show_alert=True)
        except Exception as e:
            logger.error(f"Error handling callback: {e}")
            bot.answer_callback_query(call.id, "❌ خطایی رخ داد.", show_alert=True)

# ============================
# Message Handler
# ============================

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_all_messages(message):
    """
    Handles incoming text messages from users. Stores the message and notifies the admins.
    Also handles replies from users to other users.
    """
    user_id = message.chat.id
    if is_admin(user_id):
        # Optionally, admins can interact with the bot normally
        return

    # Check if user is in reply mode
    cursor.execute("SELECT target_message_id FROM replies WHERE user_id=?", (user_id,))
    reply_entry = cursor.fetchone()
    if reply_entry:
        parent_message_id = reply_entry[0]
        reply_text = message.text.strip()
        if reply_text:
            # Insert the reply message into the database with parent_message_id
            cursor.execute(
                "INSERT INTO messages (user_id, message, status, parent_message_id) VALUES (?, ?, ?, ?)",
                (user_id, reply_text, "pending", parent_message_id)
            )
            conn.commit()
            reply_message_id = cursor.lastrowid

            # Get user details
            user_details = get_user_details(message)

            # Get or create user's random name
            cursor.execute("SELECT random_name FROM users WHERE user_id=?", (user_id,))
            result = cursor.fetchone()
            if result:
                user_random_name = result[0]
                # Update user details in the database
                cursor.execute(
                    "UPDATE users SET username=?, first_name=?, last_name=? WHERE user_id=?",
                    (user_details['username'], user_details['first_name'], user_details['last_name'], user_id)
                )
            else:
                # Create a new user entry with random name and details
                user_random_name = generate_random_name()
                cursor.execute(
                    "INSERT INTO users (user_id, username, first_name, last_name, random_name, last_name_reset, role) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        user_id,
                        user_details['username'],
                        user_details['first_name'],
                        user_details['last_name'],
                        user_random_name,
                        datetime.now(),
                        'user'
                    )
                )
            conn.commit()

            # Remove the reply entry as it's being processed
            cursor.execute("DELETE FROM replies WHERE user_id=?", (user_id,))
            conn.commit()

            # Notify all admins with inline keyboard, including parent_message_id
            send_admin_notification(reply_message_id, user_random_name, user_details, reply_text, parent_message_id=parent_message_id)

            # Inform the user that their reply is under review
            user_reply = "✉️ پاسخ شما دریافت شد و در حال بررسی است. اگر پاسخ شما تایید شود، در کانال منتشر خواهد شد."
            bot.send_message(chat_id=user_id, text=user_reply)
        else:
            bot.send_message(user_id, "❌ پیام خالی قابل قبول نیست.")
        return

    message_text = message.text.strip()
    if not message_text:
        bot.reply_to(message, "❌ پیام خالی قابل قبول نیست.")
        return

    # Get user details
    user_details = get_user_details(message)

    # Get or create user's random name
    cursor.execute("SELECT random_name FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    if result:
        user_random_name = result[0]
        # Update user details in the database
        cursor.execute(
            "UPDATE users SET username=?, first_name=?, last_name=? WHERE user_id=?",
            (user_details['username'], user_details['first_name'], user_details['last_name'], user_id)
        )
    else:
        # Create a new user entry with random name and details
        user_random_name = generate_random_name()
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name, last_name, random_name, last_name_reset, role) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                user_details['username'],
                user_details['first_name'],
                user_details['last_name'],
                user_random_name,
                datetime.now(),
                'user'
            )
        )
    conn.commit()

    # Insert message into database with status 'pending'
    cursor.execute(
        "INSERT INTO messages (user_id, message, status) VALUES (?, ?, ?)",
        (user_id, message_text, "pending")
    )
    conn.commit()

    # Get the message ID
    message_id = cursor.lastrowid

    # Notify all admins with inline keyboard
    send_admin_notification(message_id, user_random_name, user_details, message_text)

    # Inform the user that their message is under review
    user_reply = "✉️ پیام شما دریافت شد و در حال بررسی است. اگر پیام شما تایید شود، در کانال منتشر خواهد شد."
    bot.send_message(chat_id=user_id, text=user_reply)

# ============================
# Start the Bot
# ============================

def main():
    """
    Starts the bot and begins polling.
    """
    logger.info("🔄 Bot is running...")
    try:
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"Bot polling failed: {e}")

if __name__ == "__main__":
    main()
