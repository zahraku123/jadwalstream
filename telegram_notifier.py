"""
Telegram Notification Module
Sends notifications to Telegram for schedule events
"""

import requests
import json
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configuration file
CONFIG_FILE = 'telegram_config.json'

def load_config():
    """Load Telegram configuration from file"""
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

def save_config(config):
    """Save Telegram configuration to file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def is_enabled():
    """Check if Telegram notifications are enabled"""
    config = load_config()
    enabled = config.get('enabled', False)
    has_token = bool(config.get('bot_token', '').strip())
    has_chat_id = bool(config.get('chat_id', '').strip())
    return enabled and has_token and has_chat_id

def send_message(message, parse_mode='HTML'):
    """
    Send a message to Telegram
    
    Args:
        message (str): Message to send
        parse_mode (str): Parse mode (HTML or Markdown)
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not is_enabled():
        logging.warning("[TELEGRAM] Notifications are disabled or not configured")
        return False
    
    config = load_config()
    bot_token = config['bot_token']
    chat_id = config['chat_id']
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': parse_mode
    }
    
    try:
        logging.info(f"[TELEGRAM] Sending message to chat_id: {chat_id}")
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logging.info("[TELEGRAM] Message sent successfully")
            return True
        else:
            logging.error(f"[TELEGRAM] Failed to send message. Status: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        logging.error(f"[TELEGRAM] Error sending message: {e}", exc_info=True)
        return False

def notify_schedule_created(title, scheduled_time, broadcast_link):
    """
    Notify when a schedule is successfully created
    
    Args:
        title (str): Schedule title
        scheduled_time (str): Scheduled start time
        broadcast_link (str): YouTube studio link
    """
    logging.info(f"[TELEGRAM] Preparing schedule created notification for: {title}")
    message = f"""
🎬 <b>Schedule Created Successfully!</b>

📺 <b>Title:</b> {title}
🕐 <b>Scheduled Time:</b> {scheduled_time}
🔗 <b>Link:</b> <a href="{broadcast_link}">Open in YouTube Studio</a>

✅ Your stream is ready to go live!
"""
    result = send_message(message.strip())
    logging.info(f"[TELEGRAM] Notification result: {result}")
    return result

def notify_stream_starting(title, scheduled_time, broadcast_link):
    """
    Notify when a stream is about to start
    
    Args:
        title (str): Stream title
        scheduled_time (str): Scheduled start time
        broadcast_link (str): YouTube studio link
    """
    message = f"""
🚀 <b>Stream Starting Now!</b>

📺 <b>Title:</b> {title}
🕐 <b>Time:</b> {scheduled_time}
🔗 <b>Link:</b> <a href="{broadcast_link}">Open Stream</a>

🎥 Your livestream is going live!
"""
    return send_message(message.strip())

def notify_stream_ended(title, duration=None):
    """
    Notify when a stream has ended
    
    Args:
        title (str): Stream title
        duration (str, optional): Stream duration
    """
    duration_text = f"\n⏱ <b>Duration:</b> {duration}" if duration else ""
    
    message = f"""
🛑 <b>Stream Ended</b>

📺 <b>Title:</b> {title}{duration_text}

✅ Stream completed successfully!
"""
    return send_message(message.strip())

def notify_schedule_error(title, error_message):
    """
    Notify when there's an error creating a schedule
    
    Args:
        title (str): Schedule title
        error_message (str): Error message
    """
    message = f"""
❌ <b>Schedule Creation Failed</b>

📺 <b>Title:</b> {title}
⚠️ <b>Error:</b> {error_message}

Please check the application logs for details.
"""
    return send_message(message.strip())

def notify_daily_summary(total_schedules, successful, failed):
    """
    Send daily summary of schedules
    
    Args:
        total_schedules (int): Total schedules processed
        successful (int): Successful schedules
        failed (int): Failed schedules
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
    return send_message(message.strip())

def test_connection():
    """
    Test Telegram bot connection
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if not is_enabled():
        return False, "Telegram notifications are not configured or disabled"
    
    config = load_config()
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
            if send_message(test_msg.strip()):
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
    success, message = test_connection()
    print(f"Result: {message}")
