# SolCam Token Bot Setup Guide

## 🚀 Quick Start

### 1. Download Files
- `bot_complete.py` - Main bot script
- `requirements.txt` - Dependencies
- `SETUP_GUIDE.md` - This guide

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Bot
Open `bot_complete.py` and update these lines (around line 16-19):

```python
BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'
ADMIN_IDS = [YOUR_ADMIN_ID_HERE]  # Get from @userinfobot
ADMIN_USERNAME = '@your_username'
BTC_WALLET = 'your_bitcoin_wallet_address'
```

### 4. Get Bot Token
1. Message @BotFather on Telegram
2. Send `/newbot`
3. Follow instructions to create your bot
4. Copy the token to `BOT_TOKEN`

### 5. Get Your Admin ID
1. Message @userinfobot on Telegram
2. Copy your ID number to `ADMIN_IDS`

### 6. Run the Bot
```bash
python bot_complete.py
```

## 🎯 Features Included

### 🪙 SolCam Token System
- Users earn SolCam points for referrals
- 1 SolCam point = 1 hour with cam girl
- Pre-launch token economy for future Solana airdrop

### 🎁 Referral System
- Automatic referral link generation
- 1 point per successful referral
- Real-time notifications

### 👤 Profile System
- Current order tracking
- Booking history
- Points balance
- Referral statistics

### 💳 Dual Payment System
- Bitcoin payments (traditional)
- SolCam points (requires admin approval)
- Smart booking logic

### 🔧 Enhanced Admin Panel
- Manage all bookings
- Approve/reject point transactions
- User statistics
- Token economy overview

## 📱 Bot Commands

### User Commands
- `/start` - Main menu
- `/profile` - View profile
- `/referral` - Referral system

### Admin Commands
- `/admin` - Admin panel

## 🛠️ Customization

### Add Models/Teachers
Use the admin panel to add new cam girls with photos and details.

### Modify Token Economy
Edit these variables in the code:
- `REFERRAL_BONUS` - Points per referral
- `SOLCAM_POINTS_PER_HOUR` - Points needed per hour

### Update Messages
Search for message text in the code and customize as needed.

## 📞 Support
For issues or questions, contact the bot admin or check the Telegram bot logs.

---
**Ready to launch your SolCam token economy!** 🚀