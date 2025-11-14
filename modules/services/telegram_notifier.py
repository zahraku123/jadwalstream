"""
Telegram Notification Module - Per-User Support
Sends notifications to Telegram for schedule events
Now supports per-user bot configuration!
"""

import requests
import json
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configuration file (fallback for legacy)
CONFIG_FILE = 'telegram_config.json'

def get_db_connection():
    """Get database connection"""
    import sqlite3
    conn = sqlite3.connect('jadwalstream.db')
    conn.row_factory = sqlite3.Row
    return conn

def load_config(user_id=None):
    """
    Load Telegram configuration for specific user or global
    
    Args:
        user_id (int, optional): User ID for per-user config
    
    Returns:
        dict: Configuration with bot_token, chat_id, enabled
    """
    # Per-user configuration from database
    if user_id:
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT telegram_bot_token, telegram_chat_id, telegram_enabled 
                    FROM users WHERE id = ?
                ''', (user_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'bot_token': row['telegram_bot_token'] or '',
                        'chat_id': row['telegram_chat_id'] or '',
                        'enabled': bool(row['telegram_enabled'])
                    }
        except Exception as e:
            logging.error(f"[TELEGRAM] Error loading config for user {user_id}: {e}")
    
    # Fallback to global configuration file (legacy)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    
    return {
        'enabled': False,
        'bot_token': '',
        'chat_id': ''
    }

def save_config(config, user_id=None):
    """
    Save Telegram configuration for specific user or global
    
    Args:
        config (dict): Configuration to save
        user_id (int, optional): User ID for per-user config
    """
    # Per-user configuration to database
    if user_id:
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET telegram_bot_token = ?,
                        telegram_chat_id = ?,
                        telegram_enabled = ?
                    WHERE id = ?
                ''', (
                    config.get('bot_token', ''),
                    config.get('chat_id', ''),
                    1 if config.get('enabled') else 0,
                    user_id
                ))
                conn.commit()
                logging.info(f"[TELEGRAM] Config saved for user {user_id}")
                return True
        except Exception as e:
            logging.error(f"[TELEGRAM] Error saving config for user {user_id}: {e}")
            return False
    
    # Fallback to global config file (legacy)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    return True

def is_enabled(user_id=None):
    """
    Check if Telegram notifications are enabled for user
    
    Args:
        user_id (int, optional): User ID to check
    
    Returns:
        bool: True if enabled and configured
    """
    config = load_config(user_id)
    enabled = config.get('enabled', False)
    has_token = bool(config.get('bot_token', '').strip())
    has_chat_id = bool(config.get('chat_id', '').strip())
    return enabled and has_token and has_chat_id

def send_message(message, parse_mode='HTML', user_id=None):
    """
    Send a message to Telegram
    
    Args:
        message (str): Message to send
        parse_mode (str): Parse mode (HTML or Markdown)
        user_id (int, optional): User ID for per-user bot
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not is_enabled(user_id):
        logging.warning(f"[TELEGRAM] Notifications disabled or not configured for user {user_id}")
        return False
    
    config = load_config(user_id)
    bot_token = config['bot_token']
    chat_id = config['chat_id']
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': parse_mode
    }
    
    try:
        user_info = f" (user_id: {user_id})" if user_id else " (global)"
        logging.info(f"[TELEGRAM] Sending message to chat_id: {chat_id}{user_info}")
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logging.info(f"[TELEGRAM] Message sent successfully{user_info}")
            return True
        else:
            logging.error(f"[TELEGRAM] Failed to send message{user_info}. Status: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        logging.error(f"[TELEGRAM] Error sending message: {e}", exc_info=True)
        return False

def notify_schedule_created(title, scheduled_time, broadcast_link, user_id=None):
    """
    Notify when a schedule is successfully created (Indonesian slang style)
    
    Args:
        title (str): Schedule title
        scheduled_time (str): Scheduled start time
        broadcast_link (str): YouTube studio link
        user_id (int, optional): User ID for notification
    """
    logging.info(f"[TELEGRAM] Preparing schedule created notification for: {title} (user_id: {user_id})")
    message = f"""
🎬 <b>Jadwal Live Udah Jadi Bos!</b> 🔥

📺 <b>Judul:</b> {title}
🕐 <b>Jam Tayang:</b> {scheduled_time}
🔗 <b>Link:</b> <a href="{broadcast_link}">Buka Studio</a>

✅ Siap-siap go live nih! Mantap! 🚀
"""
    result = send_message(message.strip(), user_id=user_id)
    logging.info(f"[TELEGRAM] Notification result: {result}")
    return result

def notify_stream_starting(title, scheduled_time, broadcast_link, user_id=None):
    """
    Notify when a stream is about to start (Indonesian slang style)
    
    Args:
        title (str): Stream title
        scheduled_time (str): Scheduled start time
        broadcast_link (str): YouTube studio link
        user_id (int, optional): User ID for notification
    """
    message = f"""
🚀 <b>Live Mulai Sekarang Bro!</b> 🎬

📺 <b>Judul:</b> {title}
🕐 <b>Jam:</b> {scheduled_time}
🔗 <b>Link:</b> <a href="{broadcast_link}">Langsung Tonton</a>

🎥 Stream udah on air nih, cus! 🔥
"""
    return send_message(message.strip(), user_id=user_id)

def notify_stream_ended(title, duration=None, user_id=None):
    """
    Notify when a stream has ended (Indonesian slang style)
    
    Args:
        title (str): Stream title
        duration (str, optional): Stream duration
        user_id (int, optional): User ID for notification
    """
    duration_text = f"\n⏱ <b>Durasi:</b> {duration}" if duration else ""
    
    message = f"""
🛑 <b>Live Udah Selesai Bos!</b> ✅

📺 <b>Judul:</b> {title}{duration_text}

💯 Stream sukses abis! Keren banget! 🎉
"""
    return send_message(message.strip(), user_id=user_id)

def notify_schedule_error(title, error_message, user_id=None):
    """
    Notify when there's an error creating a schedule (Indonesian slang style)
    
    Args:
        title (str): Schedule title
        error_message (str): Error message
        user_id (int, optional): User ID for notification
    """
    message = f"""
❌ <b>Waduh, Jadwal Gagal Dibuat Nih!</b> 😅

📺 <b>Judul:</b> {title}
⚠️ <b>Masalah:</b> {error_message}

Coba cek log-nya ya bos, ada yang error! 🔧
"""
    return send_message(message.strip(), user_id=user_id)

def notify_upload_success(title, youtube_video_id, scheduled_time, user_id=None):
    """
    Notify when video upload is successful (Indonesian slang style)
    
    Args:
        title (str): Video title
        youtube_video_id (str): YouTube video ID
        scheduled_time (str): Scheduled publish time
        user_id (int, optional): User ID for notification
    """
    video_url = f"https://studio.youtube.com/video/{youtube_video_id}/edit"
    
    message = f"""
🔥 <b>Upload Sukses Bos!</b> 🚀

🎬 <b>Judul:</b> {title}
📹 <b>Video ID:</b> {youtube_video_id}
🕐 <b>Publish:</b> {scheduled_time}
🔗 <b>Link:</b> <a href="{video_url}">Cek di Studio</a>

✨ Mantap jiwa! Video udah siap tayang nih! 🎉
"""
    return send_message(message.strip(), user_id=user_id)

def notify_upload_failed(title, error_message, user_id=None):
    """
    Notify when video upload fails (Indonesian slang style)
    
    Args:
        title (str): Video title
        error_message (str): Error message
        user_id (int, optional): User ID for notification
    """
    message = f"""
❌ <b>Waduh, Upload Gagal Bro!</b> 😅

🎬 <b>Judul:</b> {title}
⚠️ <b>Kenapa:</b> {error_message[:200]}

Coba cek lagi ya bos, mungkin ada yang kurang! 🔧
"""
    return send_message(message.strip(), user_id=user_id)

def notify_daily_summary(total_schedules, successful, failed, user_id=None):
    """
    Send daily summary of schedules
    
    Args:
        total_schedules (int): Total schedules processed
        successful (int): Successful schedules
        failed (int): Failed schedules
        user_id (int, optional): User ID for notification
    """
    message = f"""
📊 <b>Daily Schedule Summary</b>

📅 <b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}

📈 <b>Statistics:</b>
• Total Schedules: {total_schedules}
• Successful: ✅ {successful}
• Failed: ❌ {failed}

Keep up the great work! 🎉
"""
    return send_message(message.strip(), user_id=user_id)

def test_connection(user_id=None):
    """
    Test Telegram bot connection
    
    Args:
        user_id (int, optional): User ID to test
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if not is_enabled(user_id):
        return False, "Telegram notifications are not configured or disabled"
    
    config = load_config(user_id)
    bot_token = config['bot_token']
    
    # Test getMe endpoint
    url = f"https://api.telegram.org/bot{bot_token}/getMe"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if response.status_code == 200 and data.get('ok'):
            bot_name = data['result'].get('username', 'Unknown')
            
            # Send test message
            test_msg = f"""
✅ <b>Telegram Bot Connected!</b>

🤖 <b>Bot:</b> @{bot_name}
🕐 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Your notifications are working correctly!
"""
            if send_message(test_msg.strip(), user_id=user_id):
                return True, f"Successfully connected to bot @{bot_name}"
            else:
                return False, "Failed to send test message. Check chat_id."
        else:
            error = data.get('description', 'Unknown error')
            return False, f"Bot authentication failed: {error}"
    
    except requests.exceptions.Timeout:
        return False, "Connection timeout. Check your internet connection."
    except Exception as e:
        return False, f"Connection error: {str(e)}"

if __name__ == '__main__':
    # Test the module
    print("Testing Telegram notification module...")
    print("\nTesting global config:")
    success, message = test_connection()
    print(f"Result: {message}")
    
    print("\nTesting user_id=1 (admin):")
    success, message = test_connection(user_id=1)
    print(f"Result: {message}")
