import sqlite3
import telebot
from datetime import datetime, timedelta
import sys
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(
    filename='domain_checker.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize bot with your token (use the same token as in main.py)
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))

def check_expiring_domains():
    conn = sqlite3.connect('domains.db')
    c = conn.cursor()
    
    # Get current date and date 30 days from now
    today = datetime.now()
    thirty_days_later = today + timedelta(days=30)
    
    try:
        # Get all active domains that expire within the next 30 days
        c.execute("""
            SELECT domain, user_id, expiry_date 
            FROM domains 
            WHERE is_deleted = 0 
            AND expiry_date IS NOT NULL
            AND date(expiry_date) BETWEEN date(?) AND date(?)
        """, (today.strftime('%Y-%m-%d'), thirty_days_later.strftime('%Y-%m-%d')))
        
        expiring_domains = c.fetchall()
        
        # Group domains by user
        user_domains = {}
        for domain, user_id, expiry_date in expiring_domains:
            if user_id not in user_domains:
                user_domains[user_id] = []
            days_until_expiry = (datetime.strptime(expiry_date, '%Y-%m-%d') - today).days
            user_domains[user_id].append((domain, expiry_date, days_until_expiry))
        
        # Send notifications to users
        for user_id, domains in user_domains.items():
            message = "⚠️ Domain Expiration Alert ⚠️\n\n"
            message += "The following domains are expiring soon:\n\n"
            
            for domain, expiry_date, days in domains:
                message += f"🔸 {domain}\n"
                message += f"   Expires: {expiry_date} ({days} days remaining)\n\n"
            
            message += "Please make sure to renew these domains if needed."
            
            try:
                bot.send_message(user_id, message)
                logging.info(f"Notification sent to user {user_id} for {len(domains)} domains")
            except Exception as e:
                logging.error(f"Failed to send notification to user {user_id}: {str(e)}")
        
        logging.info(f"Expiry check completed. Processed {len(expiring_domains)} expiring domains")
        
    except Exception as e:
        logging.error(f"Error during expiry check: {str(e)}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    logging.info("Starting domain expiry check script")
    check_expiring_domains()
    logging.info("Domain expiry check script completed")