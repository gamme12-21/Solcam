import logging
import uuid
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import os
import json

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '7922484259:AAH21mVqLF0OAeughkVXXrJ3_zOzuyJICys')
ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '1751803948,6392794694').split(',')]
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', '@G_king123f')
BTC_WALLET = os.getenv('BTC_WALLET', '8yt1x4XqPJqgdS95M8nrDpczkzyoYr4oGL8NDjEqXASj')

# Global data storage
teachers = []
bookings = []
pending_payments = {}
user_states = {}
teacher_edit_states = {}
referrals = {}  # Store referral data
user_profiles = {}  # Store enhanced user profiles
referral_rewards = {}  # Store referral rewards

# Referral system configuration
REFERRAL_REWARD = 5  # $5 reward for each referral
REFERRAL_BONUS = 10  # $10 bonus for referee

# Teacher management conversation states
TEACHER_EDIT_STATES = {
    'WAITING_FOR_FIELD': 'waiting_for_field',
    'WAITING_FOR_VALUE': 'waiting_for_value',
    'WAITING_FOR_NEW_TEACHER': 'waiting_for_new_teacher'
}

# Initialize sample teacher data
def initialize_teachers():
    global teachers
    teachers = [
        {
            'id': 1,
            'name': 'Sarah Johnson',
            'age': 28,
            'subjects': ['Mathematics', 'Physics'],
            'price': 25,
            'photo': 'https://images.unsplash.com/photo-1494790108755-2616c78746d5?w=400&h=400&fit=crop&crop=face',
            'available': True,
            'bio': 'Expert mathematician with 5+ years teaching experience. Specializes in making complex concepts simple and engaging.',
            'education': 'MSc Mathematics, Stanford University',
            'experience': '2+ years of webcam worker',
            'rating': 4.9,
            'why_choose': 'i love working on webcam i can make you happy.'
        },
        {
            'id': 2,
            'name': 'Emma Williams',
            'age': 25,
            'subjects': ['English', 'Literature'],
            'price': 30,
            'photo': 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=400&h=400&fit=crop&crop=face',
            'available': True,
            'bio': 'Passionate English teacher with creative teaching methods. Makes learning fun and interactive.',
            'education': 'BA English Literature, Oxford University',
            'experience': '3+ years of webcam worker',
            'rating': 4.8,
            'why_choose': 'Creative and engaging approach to make complex topics simple.'
        },
        {
            'id': 3,
            'name': 'Lisa Chen',
            'age': 29,
            'subjects': ['Chemistry', 'Biology'],
            'price': 28,
            'photo': 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=400&h=400&fit=crop&crop=face',
            'available': False,
            'bio': 'Science enthusiast with years of research experience. Excellent at explaining complex scientific concepts.',
            'education': 'PhD Chemistry, MIT',
            'experience': '4+ years of webcam worker',
            'rating': 4.9,
            'why_choose': 'Research background brings real-world applications to learning.'
        },
        {
            'id': 4,
            'name': 'Maria Rodriguez',
            'age': 26,
            'subjects': ['Spanish', 'French'],
            'price': 22,
            'photo': 'https://images.unsplash.com/photo-1489424731084-a5d8b219a5bb?w=400&h=400&fit=crop&crop=face',
            'available': True,
            'bio': 'Native Spanish speaker with fluency in multiple languages. Cultural insights included.',
            'education': 'MA Linguistics, Universidad Complutense',
            'experience': '2+ years of webcam worker',
            'rating': 4.7,
            'why_choose': 'Native speaker with cultural context and immersive learning.'
        },
        {
            'id': 5,
            'name': 'Sophie Taylor',
            'age': 24,
            'subjects': ['Art', 'Music'],
            'price': 26,
            'photo': 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400&h=400&fit=crop&crop=face',
            'available': True,
            'bio': 'Creative artist and musician. Specializes in developing artistic skills and musical talent.',
            'education': 'BFA Fine Arts, Royal College of Art',
            'experience': '1+ years of webcam worker',
            'rating': 4.8,
            'why_choose': 'Combines technical skills with creative inspiration.'
        }
    ]

def is_admin(user_id):
    return user_id in ADMIN_IDS

def create_inline_keyboard(buttons):
    """Create better inline keyboard with improved spacing and design"""
    return InlineKeyboardMarkup(buttons)

def generate_referral_code(user_id):
    """Generate unique referral code for user"""
    return f"SOL{user_id}CAM"

def get_user_profile(user_id):
    """Get or create user profile"""
    if user_id not in user_profiles:
        user_profiles[user_id] = {
            'referral_code': generate_referral_code(user_id),
            'referred_by': None,
            'referrals_made': 0,
            'total_earnings': 0,
            'bookings_count': 0,
            'join_date': datetime.now().strftime('%Y-%m-%d'),
            'status': 'Bronze',  # Bronze, Silver, Gold, Platinum
            'profile_complete': False
        }
    return user_profiles[user_id]

def update_user_status(user_id):
    """Update user status based on activity"""
    profile = get_user_profile(user_id)
    bookings = profile['bookings_count']
    
    if bookings >= 20:
        profile['status'] = 'Platinum'
    elif bookings >= 10:
        profile['status'] = 'Gold'
    elif bookings >= 5:
        profile['status'] = 'Silver'
    else:
        profile['status'] = 'Bronze'

def process_referral(referrer_id, referee_id):
    """Process referral reward"""
    referrer_profile = get_user_profile(referrer_id)
    referee_profile = get_user_profile(referee_id)
    
    if referee_profile['referred_by'] is None:
        referee_profile['referred_by'] = referrer_id
        referrer_profile['referrals_made'] += 1
        referrer_profile['total_earnings'] += REFERRAL_REWARD
        
        # Store referral reward
        if referrer_id not in referral_rewards:
            referral_rewards[referrer_id] = 0
        referral_rewards[referrer_id] += REFERRAL_REWARD
        
        return True
    return False

# Start command with referral handling
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id

    # Handle referral code
    referrer_id = None
    if context.args:
        try:
            referrer_id = int(context.args[0])
            if referrer_id != user_id:  # Can't refer yourself
                success = process_referral(referrer_id, user_id)
                if success:
                    await context.bot.send_message(
                        referrer_id,
                        f"🎉 Congratulations! You earned ${REFERRAL_REWARD} from a referral!\n"
                        f"Your new referral has joined SOLCAM!"
                    )

        except ValueError:
            pass

    # Store user information
    user_states[user_id] = {
        'username': user.username or "No username set",
        'full_name': user.full_name or "Unknown User",
        'chat_id': chat_id
    }

    # Get user profile
    profile = get_user_profile(user_id)
    status_emoji = {'Bronze': '🥉', 'Silver': '🥈', 'Gold': '🥇', 'Platinum': '💎'}
    
    welcome_message = f"""💋 Welcome to SOLCAM! 💋

Hello {user.first_name}! 👋 {status_emoji.get(profile['status'], '🥉')}

I'm your personal beautiful girls booking assistant. Here's what I can help you with:

🔥 **Your Status**: {profile['status']} Member
💰 **Earnings**: ${profile['total_earnings']} from referrals
📅 **Member Since**: {profile['join_date']}

🌟 **For You**:
• 💃 Browse amazing beautiful cam girls
• 👤 View detailed profiles  
• 📅 Book sessions easily
• 💳 Secure Solana payments
• 🎁 Earn with referrals

Ready to start your adventure? Choose an option below!

💬 **Need Support?** Contact us: {ADMIN_USERNAME}"""

    keyboard = [
        [
            InlineKeyboardButton("💃 Browse Models", callback_data='check_teachers'),
            InlineKeyboardButton("👤 My Profile", callback_data='user_profile')
        ],
        [
            InlineKeyboardButton("🎁 Referral System", callback_data='referral_system'),
            InlineKeyboardButton("ℹ️ How It Works", callback_data='how_it_works')
        ],
        [
            InlineKeyboardButton("💬 Contact Support", callback_data='contact_support')
        ]
    ]

    # Add admin panel button only for admins
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton("🔧 Admin Panel", callback_data='admin')])

    reply_markup = create_inline_keyboard(keyboard)
    await context.bot.send_message(chat_id, welcome_message, reply_markup=reply_markup)

# User profile display
async def show_user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id

    profile = get_user_profile(user_id)
    status_emoji = {'Bronze': '🥉', 'Silver': '🥈', 'Gold': '🥇', 'Platinum': '💎'}
    
    profile_message = f"""👤 **YOUR PROFILE** 👤
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏷️ **Basic Info**:
• Name: {user.full_name or user.first_name}
• Username: @{user.username or 'Not set'}
• Status: {status_emoji.get(profile['status'], '🥉')} {profile['status']} Member
• Member Since: {profile['join_date']}

📊 **Your Statistics**:
• 📅 Total Bookings: {profile['bookings_count']}
• 👥 Referrals Made: {profile['referrals_made']}
• 💰 Total Earnings: ${profile['total_earnings']}
• 🎁 Pending Rewards: ${referral_rewards.get(user_id, 0)}

🔗 **Referral Info**:
• Your Code: `{profile['referral_code']}`
• Referred By: {'Someone special' if profile['referred_by'] else 'Direct signup'}

🎯 **Next Status**: {
    'Silver (5 bookings)' if profile['status'] == 'Bronze' else
    'Gold (10 bookings)' if profile['status'] == 'Silver' else
    'Platinum (20 bookings)' if profile['status'] == 'Gold' else
    'Maximum level reached!'
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Use your referral code to earn rewards! 🎁"""

    keyboard = [
        [
            InlineKeyboardButton("🎁 Share Referral", callback_data='share_referral'),
            InlineKeyboardButton("📊 My Bookings", callback_data='my_bookings')
        ],
        [
            InlineKeyboardButton("💰 Withdraw Earnings", callback_data='withdraw_earnings'),
            InlineKeyboardButton("🔙 Back to Main", callback_data='back_to_main')
        ]
    ]

    reply_markup = create_inline_keyboard(keyboard)
    await context.bot.send_message(chat_id, profile_message, reply_markup=reply_markup, parse_mode='Markdown')

# Referral system display
async def show_referral_system(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id

    profile = get_user_profile(user_id)
    
    referral_message = f"""🎁 **REFERRAL SYSTEM** 🎁
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 **Earn Money by Referring Friends!**

🔥 **How it works**:
1. Share your referral code with friends
2. They sign up using your code
3. You earn ${REFERRAL_REWARD} per referral
4. They get ${REFERRAL_BONUS} bonus credit!

📊 **Your Performance**:
• 🔗 Your Code: `{profile['referral_code']}`
• 👥 Referrals Made: {profile['referrals_made']}
• 💵 Total Earned: ${profile['total_earnings']}
• 🎁 Pending: ${referral_rewards.get(user_id, 0)}

🚀 **Share Your Code**:
Send this message to friends:
"Join SOLCAM with my referral code and get ${REFERRAL_BONUS} bonus! 
Use /start {user_id} or click: https://t.me/{context.bot.username}?start={user_id}"

🏆 **Referral Rewards**:
• 🥉 Bronze: ${REFERRAL_REWARD} per referral
• 🥈 Silver: ${REFERRAL_REWARD + 2} per referral
• 🥇 Gold: ${REFERRAL_REWARD + 5} per referral  
• 💎 Platinum: ${REFERRAL_REWARD + 10} per referral

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Start earning today! 💸"""

    keyboard = [
        [
            InlineKeyboardButton("📤 Share Code", callback_data='share_referral_code'),
            InlineKeyboardButton("📊 Referral Stats", callback_data='referral_stats')
        ],
        [
            InlineKeyboardButton("💰 Withdraw", callback_data='withdraw_earnings'),
            InlineKeyboardButton("🔙 Back", callback_data='back_to_main')
        ]
    ]

    reply_markup = create_inline_keyboard(keyboard)
    await context.bot.send_message(chat_id, referral_message, reply_markup=reply_markup, parse_mode='Markdown')

# Admin panel
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id

    if not is_admin(user.id):
        await context.bot.send_message(chat_id, '❌ Access denied. Admin only.')
        return

    total_users = len(user_profiles)
    total_referrals = sum(profile['referrals_made'] for profile in user_profiles.values())
    total_earnings = sum(profile['total_earnings'] for profile in user_profiles.values())

    admin_message = f"""🔧 **ADMIN CONTROL PANEL** 🔧
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👋 Welcome, Admin {user.first_name}!

📊 **System Statistics**:
• 👥 Total Users: {total_users}
• 💃 Models: {len(teachers)}
• 📅 Bookings: {len(bookings)}
• 💰 Pending Payments: {len(pending_payments)}
• 🎁 Total Referrals: {total_referrals}
• 💸 Total Earnings: ${total_earnings}

🛠️ **Admin Tools**:
Choose an action below:"""

    keyboard = [
        [
            InlineKeyboardButton("💃 Manage Models", callback_data='manage_teachers'),
            InlineKeyboardButton("📋 View Bookings", callback_data='view_bookings')
        ],
        [
            InlineKeyboardButton("💰 Pending Payments", callback_data='view_payments'),
            InlineKeyboardButton("➕ Add New Model", callback_data='add_teacher')
        ],
        [
            InlineKeyboardButton("👥 User Analytics", callback_data='user_analytics'),
            InlineKeyboardButton("🎁 Referral System", callback_data='admin_referrals')
        ],
        [
            InlineKeyboardButton("🔙 Back to Main", callback_data='back_to_main')
        ]
    ]

    reply_markup = create_inline_keyboard(keyboard)
    await context.bot.send_message(chat_id, admin_message, reply_markup=reply_markup, parse_mode='Markdown')

# Show available teachers
async def show_available_teachers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id

    message = """💃 **AVAILABLE MODELS** 💃
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Choose your perfect model from our exclusive collection:

🔥 **All models are verified and ready for private sessions**
✨ **Premium quality guaranteed**
🎯 **Secure payments with Solana**

Select a model to view her full profile:"""

    keyboard = []
    for teacher in teachers:
        status_emoji = "✅" if teacher['available'] else "❌"
        button_text = f"{status_emoji} {teacher['name']} - ${teacher['price']}/hr"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"teacher_{teacher['id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Main", callback_data='back_to_main')])

    reply_markup = create_inline_keyboard(keyboard)
    await context.bot.send_message(chat_id, message, reply_markup=reply_markup, parse_mode='Markdown')

# Show detailed teacher profile
async def show_teacher_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, teacher_id: int) -> None:
    chat_id = update.effective_chat.id

    teacher = next((t for t in teachers if t['id'] == teacher_id), None)

    if not teacher:
        await context.bot.send_message(chat_id, '❌ Model not found.')
        return

    profile_text = f"""🌟 {teacher['name']} - Full Profile 🌟
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💃 PERSONAL INFO:
🎂 Age: {teacher['age']} years
🔥 Specializes in: {', '.join(teacher['subjects'])}
⭐ Rating: {teacher.get('rating', 'N/A')}/5.0

😈 Interested:
{teacher.get('education', 'Not specified')}

💄 EXPERIENCE:
{teacher.get('experience', 'Not specified')}

📝 ABOUT {teacher['name'].split()[0]}:
{teacher.get('bio', 'Professional with this field.')}

🎯 WHY CHOOSE {teacher['name'].split()[0]}:
{teacher.get('why_choose', 'loyalty and trust also beauty.')}

💸 PRICING:
Rate: ${teacher['price']} /hour
⭐ Status: {'✅ Available Now' if teacher['available'] else '❌ Currently Unavailable'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💋 Want her? Tap below to book your private moment!"""

    keyboard = [
        [InlineKeyboardButton("💋 Book Me Now 💋", callback_data=f"book_teacher_{teacher['id']}")],
        [InlineKeyboardButton("← Back to All Models", callback_data='check_teachers')]
    ]
    reply_markup = create_inline_keyboard(keyboard)

    try:
        if teacher.get('photo'):
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=teacher['photo'],
                caption=profile_text,
                reply_markup=reply_markup
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=profile_text,
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Error sending teacher profile for {teacher['name']}: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=profile_text,
            reply_markup=reply_markup
        )

# Handle teacher booking
async def handle_book_teacher(update: Update, context: ContextTypes.DEFAULT_TYPE, teacher_id: int) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id

    teacher = next((t for t in teachers if t['id'] == teacher_id), None)
    if not teacher:
        await context.bot.send_message(chat_id, '❌ Model not found.')
        return

    if not teacher['available']:
        await context.bot.send_message(chat_id, '❌ This Model is currently unavailable.')
        return

    # Get user info
    user_info = user_states.get(user_id, {})
    student_username = user_info.get('username', 'No username set')
    student_full_name = user_info.get('full_name', 'Unknown User')

    # Create booking
    booking_id = str(uuid.uuid4())[:8]
    booking = {
        'id': booking_id,
        'student_id': user_id,
        'student_username': student_username,
        'student_name': student_full_name,
        'teacher_id': teacher_id,
        'teacher_name': teacher['name'],
        'price': teacher['price'],
        'status': 'pending_payment',
        'created_at': datetime.now()
    }

    bookings.append(booking)
    pending_payments[booking_id] = booking
    
    # Update user profile booking count
    profile = get_user_profile(user_id)
    profile['bookings_count'] += 1
    update_user_status(user_id)

    # Send payment instructions to student
    payment_message = f"""💰 PAYMENT INSTRUCTIONS 💰
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💋 Booking Details:
• Model: {teacher['name']}
• Rate: ${teacher['price']} /hour
• Booking ID: {booking_id}

💳 Payment Method: Solana (SOL)
• Wallet Address: `{BTC_WALLET}`
• Amount: ${teacher['price']}

📝 Instructions:
1. Send ${teacher['price']} SOL to the address above
2. Take a screenshot of the transaction
3. Send the screenshot to this chat
4. Wait for admin verification

⚡ After payment confirmation:
• {teacher['name']} will contact you within 5 minutes
• You'll receive her contact information
• Session details will be shared

💡 Note: Payment verification usually takes 2-5 minutes

Need help? Contact: {ADMIN_USERNAME}"""

    keyboard = [
        [InlineKeyboardButton("📷 Upload Payment Screenshot", callback_data=f"upload_payment_{booking_id}")],
        [InlineKeyboardButton("❌ Cancel Booking", callback_data=f"cancel_booking_{booking_id}")],
        [InlineKeyboardButton("🔙 Back to Models", callback_data='check_teachers')]
    ]

    reply_markup = create_inline_keyboard(keyboard)
    await context.bot.send_message(chat_id, payment_message, reply_markup=reply_markup, parse_mode='Markdown')

    # Notify admin about new booking
    admin_notification = f"""🔔 NEW BOOKING ALERT 🔔

👤 Student: {student_full_name} (@{student_username})
💃 Model: {teacher['name']}
💰 Amount: ${teacher['price']}
🆔 Booking ID: {booking_id}
📅 Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Status: Waiting for payment"""

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, admin_notification)
        except Exception as e:
            logger.error(f"Failed to send admin notification to {admin_id}: {e}")

# Callback query handler
async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    chat_id = update.effective_chat.id
    callback_data = query.data

    try:
        if callback_data == 'check_teachers':
            await show_available_teachers(update, context)

        elif callback_data == 'admin':
            await admin(update, context)

        elif callback_data == 'user_profile':
            await show_user_profile(update, context)

        elif callback_data == 'referral_system':
            await show_referral_system(update, context)

        elif callback_data == 'how_it_works':
            how_it_works_message = """ℹ️ **HOW IT WORKS** ℹ️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **Simple 4-Step Process**:

1️⃣ **Browse Models**
   • Check our available girls
   • Choose your favorite girl
   • View her profile

2️⃣ **Select & Book**
   • Choose your beauty
   • Review pricing and availability
   • Confirm your booking

3️⃣ **Secure Payment**
   • Pay with Solana (secure & private)
   • Send payment screenshot
   • Wait for admin verification

4️⃣ **Get Live with Your Lady**
   • Lady contacts you within 5 minutes
   • Schedule your first session
   • Enjoy our services!

💡 **Why Choose Us?**
• Loyalty and trust
• Professional models
• Easy booking process
• Fast payment verification
• Secure Solana payments for privacy
• 24/7 admin support for any issues

Ready to get started? Click "Browse Models" below! 🚀"""

            keyboard = [
                [InlineKeyboardButton("💃 Browse Models", callback_data='check_teachers')],
                [InlineKeyboardButton("🔙 Back to Main", callback_data='back_to_main')]
            ]
            reply_markup = create_inline_keyboard(keyboard)
            await context.bot.send_message(chat_id, how_it_works_message, reply_markup=reply_markup, parse_mode='Markdown')

        elif callback_data == 'back_to_main':
            await start(update, context)

        elif callback_data == 'contact_support':
            support_message = f"""💬 **CONTACT SUPPORT** 💬
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤝 **Need Help?**
We're here to assist you 24/7!

📞 **Support Contact:**
{ADMIN_USERNAME}

💡 **What we can help with:**
• Booking assistance
• Payment verification issues
• Technical support
• Account questions
• General inquiries

⚡ **Response Time:**
We typically respond within 5 minutes during business hours.

Don't hesitate to reach out - we're happy to help! 😊"""

            keyboard = [
                [InlineKeyboardButton("📱 Message Support", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")],
                [InlineKeyboardButton("🔙 Back to Main", callback_data='back_to_main')]
            ]
            reply_markup = create_inline_keyboard(keyboard)
            await context.bot.send_message(chat_id, support_message, reply_markup=reply_markup, parse_mode='Markdown')

        elif callback_data == 'share_referral':
            await show_referral_system(update, context)

        elif callback_data == 'my_bookings':
            await show_user_profile(update, context)

        elif callback_data == 'withdraw_earnings':
            user_id = user.id
            profile = get_user_profile(user_id)
            if profile['total_earnings'] > 0:
                withdraw_message = f"""💰 **WITHDRAW EARNINGS** 💰
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 **Your Current Earnings**: ${profile['total_earnings']}

💳 **Payment Details:**
• Wallet Address: {BTC_WALLET}
• Amount: ${profile['total_earnings']}
• Currency: Solana (SOL)

📝 **Next Steps:**
1. Send the exact amount of ${profile['total_earnings']} to the wallet address above.
2. Take a screenshot of the transaction.
3. Send the screenshot to this chat.
4. Wait for admin confirmation.

⏰ After payment verification, your earnings will be added to your account.

💡 **Note:** Withdrawals are processed manually by the admin.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
                await context.bot.send_message(chat_id, withdraw_message, parse_mode='Markdown')
            else:
                await context.bot.send_message(chat_id, "You don't have any earnings to withdraw yet!")

        elif callback_data == 'share_referral_code':
            user_id = user.id
            profile = get_user_profile(user_id)
            referral_link = f"https://t.me/{context.bot.username}?start={user_id}"
            share_message = f"""📤 **SHARE YOUR REFERRAL CODE** 📤
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎁 **Your Referral Code:** `{profile['referral_code']}`

🚀 **Share this link with your friends to earn rewards!**

{referral_link}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Start earning today! 💸"""
            await context.bot.send_message(chat_id, share_message, parse_mode='Markdown')

        elif callback_data == 'referral_stats':
            user_id = user.id
            profile = get_user_profile(user_id)
            referred_by_display = f"@{user_profiles.get(profile['referred_by'], {}).get('username', 'Direct signup')}" if profile['referred_by'] else "Direct signup"

            referral_stats_message = f"""📊 **REFERRAL STATS** 📊
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 **Your Referral Code:** `{profile['referral_code']}`
👥 **Referred By:** {referred_by_display}
👥 **Referrals Made:** {profile['referrals_made']}
💰 **Total Earnings from Referrals:** ${profile['total_earnings']}
🎁 **Pending Rewards:** ${referral_rewards.get(user_id, 0)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Start earning today! 💸"""
            await context.bot.send_message(chat_id, referral_stats_message, parse_mode='Markdown')

        elif callback_data == 'user_analytics':
            if not is_admin(user.id):
                await context.bot.send_message(chat_id, '❌ Access denied. Admin only.')
                return
            
            total_users = len(user_profiles)
            bronze_users = sum(1 for p in user_profiles.values() if p['status'] == 'Bronze')
            silver_users = sum(1 for p in user_profiles.values() if p['status'] == 'Silver')
            gold_users = sum(1 for p in user_profiles.values() if p['status'] == 'Gold')
            platinum_users = sum(1 for p in user_profiles.values() if p['status'] == 'Platinum')
            
            analytics_message = f"""📊 **USER ANALYTICS** 📊
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👥 **Total Users:** {total_users}

🏆 **User Status Breakdown:**
• 🥉 Bronze: {bronze_users} users
• 🥈 Silver: {silver_users} users  
• 🥇 Gold: {gold_users} users
• 💎 Platinum: {platinum_users} users

📈 **Engagement Stats:**
• Total Bookings: {len(bookings)}
• Total Referrals: {sum(p['referrals_made'] for p in user_profiles.values())}
• Total Earnings: ${sum(p['total_earnings'] for p in user_profiles.values())}
• Average Bookings per User: {len(bookings) / max(total_users, 1):.1f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
            
            keyboard = [
                [InlineKeyboardButton("🔙 Back to Admin", callback_data='admin')]
            ]
            reply_markup = create_inline_keyboard(keyboard)
            await context.bot.send_message(chat_id, analytics_message, reply_markup=reply_markup, parse_mode='Markdown')

        elif callback_data == 'admin_referrals':
            if not is_admin(user.id):
                await context.bot.send_message(chat_id, '❌ Access denied. Admin only.')
                return
            
            total_referrals = sum(profile['referrals_made'] for profile in user_profiles.values())
            total_rewards = sum(referral_rewards.values())
            
            admin_referrals_message = f"""🎁 **ADMIN REFERRAL OVERVIEW** 🎁
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **System Statistics:**
• Total Referrals: {total_referrals}
• Total Rewards Paid: ${total_rewards}
• Active Referrers: {len([p for p in user_profiles.values() if p['referrals_made'] > 0])}

💰 **Reward Settings:**
• Referral Reward: ${REFERRAL_REWARD}
• Referee Bonus: ${REFERRAL_BONUS}

📈 **Top Referrers:**"""
            
            # Get top referrers
            top_referrers = sorted(user_profiles.items(), key=lambda x: x[1]['referrals_made'], reverse=True)[:5]
            for i, (user_id, profile) in enumerate(top_referrers, 1):
                if profile['referrals_made'] > 0:
                    admin_referrals_message += f"\n{i}. User {user_id}: {profile['referrals_made']} referrals (${profile['total_earnings']})"
            
            admin_referrals_message += "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            
            keyboard = [
                [InlineKeyboardButton("🔙 Back to Admin", callback_data='admin')]
            ]
            reply_markup = create_inline_keyboard(keyboard)
            await context.bot.send_message(chat_id, admin_referrals_message, reply_markup=reply_markup, parse_mode='Markdown')

        elif callback_data.startswith('book_teacher_'):
            teacher_id = int(callback_data.split('_')[2])
            await handle_book_teacher(update, context, teacher_id)

        elif callback_data.startswith('teacher_'):
            teacher_id = int(callback_data.split('_')[1])
            await show_teacher_profile(update, context, teacher_id)

        else:
            await context.bot.send_message(
                chat_id,
                '❌ Unknown command. Please use the menu buttons.'
            )

    except Exception as e:
        logger.error(f"Error in callback query handler: {e}")
        await context.bot.send_message(
            chat_id,
            '❌ An error occurred. Please try again or contact support.'
        )

# Handle text messages
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    text = update.message.text

    # Check if user is in any editing state
    if user.id in teacher_edit_states:
        await handle_teacher_editing(update, context, text)
        return

    # Default response for unrecognized text
    await context.bot.send_message(
        chat_id,
        '❌ I didn\'t understand that. Please use the menu buttons or type /start to begin.'
    )

# Handle photo uploads
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id

    await context.bot.send_message(
        chat_id,
        '📷 Photo received! If this is a payment screenshot, please contact admin for verification.'
    )

# Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Exception while handling an update: {context.error}")

def main() -> None:
    """Start the bot."""
    # Initialize teachers
    initialize_teachers()

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CallbackQueryHandler(callback_query_handler))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_error_handler(error_handler)

    # Start the bot
    logger.info("Starting SOLCAM bot with enhanced features...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()