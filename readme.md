# Domain Expiry Checker Bot

A Telegram bot that helps you track domain expiration dates and sends notifications when domains are nearing expiry. The bot monitors your domains and alerts you 30 days before they expire, helping you avoid domain loss due to forgotten renewals.

You can run this bot on any server that has a public IP address.

And also you can use my bot: https://t.me/domainops_bot

## Features

- Add and manage multiple domains
- Check expiration dates manually or automatically 
- Get notifications 30 days before domain expiry
- View list of tracked domains
- Remove domains from tracking
- Logging of all bot interactions
- Daily automated checks for expiring domains

## Prerequisites

- Python 3.8 or higher
- SQLite3
- A Telegram Bot Token (get it from [@BotFather](https://t.me/botfather))

## Installation

1. Clone this repository to /usr/local/domainops:

```bash
cd /usr/local
git clone https://github.com/drfaustxx/domainops.git
cd domainops
```

2. Install required packages:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```
3. Create and configure the environment file, and set your bot token:

```bash
cp .env.example .env
nano .env
```

4. Set up your cron job to run the bot daily:

```bash
chmod +x check_expiry.py
crontab -e

0 9 * * * /usr/bin/python3 /usr/local/domainops/check_expiry.py
```

5. Run the bot as a service:

```bash
sudo cp domainops.service /etc/systemd/system/
sudo systemctl enable domainops
sudo systemctl start domainops
```
6. Logs can be viewed with:

```bash
journalctl -u domainops
```