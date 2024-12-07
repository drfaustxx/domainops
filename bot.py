import telebot
import sqlite3
import whois
from datetime import datetime
import re
from dotenv import load_dotenv
import os
# Load environment variables
load_dotenv()

# Initialize bot with your token
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))

# Database initialization
def init_db():
    conn = sqlite3.connect('domains.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS domains
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  domain TEXT NOT NULL,
                  user_id INTEGER NOT NULL,
                  expiry_date TEXT,
                  whois_info TEXT,
                  is_deleted INTEGER DEFAULT 0,
                  last_checked TIMESTAMP)''')
    
    # Add new message_logs table
    c.execute('''CREATE TABLE IF NOT EXISTS message_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  message_text TEXT NOT NULL,
                  command TEXT,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# Helper function to validate domain
def is_valid_domain(domain):
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))

# Add this helper function to log messages
def log_message(message):
    conn = sqlite3.connect('domains.db')
    try:
        command = message.text.split()[0] if message.text.startswith('/') else None
        c = conn.cursor()
        c.execute("""INSERT INTO message_logs (user_id, message_text, command) 
                    VALUES (?, ?, ?)""",
                 (message.from_user.id, message.text, command))
        conn.commit()
    finally:
        conn.close()

# Command handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    log_message(message)
    bot.reply_to(message, "Welcome! Use /help to see available commands.")

@bot.message_handler(commands=['help'])
def send_help(message):
    log_message(message)
    help_text = """
Available commands:
/add <domain> - Add a new domain
/list - List all your active domains
/delete <domain> - Mark a domain as deleted
/check <domain> - Check WHOIS info for a domain
/checkall - Check WHOIS info for all your domains
    """
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['add'])
def add_domain(message):
    log_message(message)
    conn = sqlite3.connect('domains.db')
    try:
        domain = message.text.split()[1].lower()
        if not is_valid_domain(domain):
            bot.reply_to(message, "Invalid domain format!")
            return
        
        c = conn.cursor()
        c.execute("SELECT * FROM domains WHERE domain=? AND user_id=? AND is_deleted=0", 
                 (domain, message.from_user.id))
        if c.fetchone():
            bot.reply_to(message, "Domain already exists!")
            return
            
        c.execute("INSERT INTO domains (domain, user_id) VALUES (?, ?)",
                 (domain, message.from_user.id))
        conn.commit()
        bot.reply_to(message, f"Domain {domain} added successfully!")
    except IndexError:
        bot.reply_to(message, "Please provide a domain! Usage: /add domain.com")
    except Exception as e:
        bot.reply_to(message, f"Error occurred: {str(e)}")
    finally:
        conn.close()

@bot.message_handler(commands=['list'])
def list_domains(message):
    log_message(message)
    conn = sqlite3.connect('domains.db')
    c = conn.cursor()
    c.execute("SELECT domain, expiry_date FROM domains WHERE user_id=? AND is_deleted=0", 
             (message.from_user.id,))
    domains = c.fetchall()
    conn.close()
    
    if not domains:
        bot.reply_to(message, "You haven't added any domains yet!")
        return
        
    response = "Your domains:\n"
    for domain, expiry in domains:
        expiry_info = f" (Expires: {expiry})" if expiry else ""
        response += f"• {domain}{expiry_info}\n"
    bot.reply_to(message, response)

@bot.message_handler(commands=['delete'])
def delete_domain(message):
    log_message(message)
    conn = sqlite3.connect('domains.db')
    try:
        domain = message.text.split()[1].lower()
        c = conn.cursor()
        c.execute("UPDATE domains SET is_deleted=1 WHERE domain=? AND user_id=?", 
                 (domain, message.from_user.id))
        conn.commit()
        if c.rowcount > 0:
            bot.reply_to(message, f"Domain {domain} is no longer in your list!")
        else:
            bot.reply_to(message, f"Domain {domain} not found!")
    except IndexError:
        bot.reply_to(message, "Please provide a domain! Usage: /delete domain.com")
    finally:
        conn.close()

@bot.message_handler(commands=['check', 'checkall'])
def check_domains(message):
    log_message(message)
    conn = sqlite3.connect('domains.db')
    c = conn.cursor()
    
    if message.text.startswith('/check '):
        domain = message.text.split()[1].lower()
        domains = [(domain,)]
        c.execute("SELECT domain FROM domains WHERE domain=? AND user_id=? AND is_deleted=0",
                 (domain, message.from_user.id))
        if not c.fetchone():
            bot.reply_to(message, "Domain not found in your list!")
            conn.close()
            return
    else:  # /checkall
        c.execute("SELECT domain FROM domains WHERE user_id=? AND is_deleted=0",
                 (message.from_user.id,))
        domains = c.fetchall()
        if not domains:
            bot.reply_to(message, "No domains to check!")
            conn.close()
            return
    
    bot.reply_to(message, "Checking domain(s)... This might take a moment.")
    
    for domain, in domains:
        try:
            w = whois.whois(domain)
            expiry_date = w.expiration_date
            if isinstance(expiry_date, list):
                expiry_date = expiry_date[0]
            expiry_str = expiry_date.strftime('%Y-%m-%d') if expiry_date else 'Unknown'
            
            c.execute("""UPDATE domains 
                        SET expiry_date=?, whois_info=?, last_checked=? 
                        WHERE domain=? AND user_id=?""",
                     (expiry_str, str(w), datetime.now(), domain, message.from_user.id))
            conn.commit()
            
            bot.reply_to(message, f"Domain: {domain}\nExpiry Date: {expiry_str}")
        except Exception as e:
            bot.reply_to(message, f"Error checking {domain}: {str(e)}")
    
    conn.close()

# Start the bot
bot.polling()
