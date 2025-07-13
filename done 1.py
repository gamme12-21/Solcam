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
    logger.info(f"Initialized {len(teachers)} teachers")

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
            InlineKeyboardButton("� Browse Models", callback_data='check_teachers'),
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
    
    profile_message = f"""� **YOUR PROFILE** �
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
            InlineKeyboardButton("� My Bookings", callback_data='my_bookings')
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
            InlineKeyboardButton("� Withdraw", callback_data='withdraw_earnings'),
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

    if not teachers:
        await context.bot.send_message(chat_id, '❌ No model available at the moment.')
        return

    # Header message
    header_message = """🔥 OUR AMAZING GIRLS 🔥
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Choose your perfect beutiful girls from our curated selection and have fun with your lady 💦  🥵! :"""

    await context.bot.send_message(chat_id, header_message)

    # Send each teacher as individual card
    for teacher in teachers:
        if teacher['available']:
            teacher_card = f"""👙 Name: {teacher['name']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

😘 Age: {teacher['age']} years

😈 Interasted : {', '.join(teacher['subjects'])}

💸 Rate: ${teacher['price']}/hour

⭐ Rating: {teacher.get('rating', 'N/A')}/5.0

👙Why Choose {teacher['name'].split()[0]}:
ccc"{teacher.get('why_choose', 'Professional mom girl.')}"

💡 Experience: {teacher.get('experience', 'Experienced educator')}

✅ Status: Available Now

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

            keyboard = [
                [InlineKeyboardButton("🍑 View Full Profile", callback_data=f"profile_teacher_{teacher['id']}")],
                [InlineKeyboardButton("💃 Book Me😘", callback_data=f"book_teacher_{teacher['id']}")]
            ]
            reply_markup = create_inline_keyboard(keyboard)

            try:
                if teacher.get('photo'):
                    await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=teacher['photo'],
                        caption=teacher_card,
                        reply_markup=reply_markup
                    )
                else:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=teacher_card,
                        reply_markup=reply_markup
                    )
            except Exception as e:
                logger.error(f"Error sending model card for {teacher['name']}: {e}")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=teacher_card,
                    reply_markup=reply_markup
                )

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

😈 Interasted:
{teacher.get('education', 'Not specified')}

💄 EXPERIENCE:
{teacher.get('experience', 'Not specified')}

📝 ABOUT {teacher['name'].split()[0]}:
{teacher.get('bio', 'Professional with this filde.')}

🎯 WHY CHOOSE {teacher['name'].split()[0]}:
{teacher.get('why_choose', 'loyality and trust also beuty.')}

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

    # Get user info
    user_info = user_states.get(user_id, {})
    student_username = user_info.get('username', 'No username set')
    student_full_name = user_info.get('full_name', 'Unknown User')

    teacher = next((t for t in teachers if t['id'] == teacher_id), None)

    if not teacher:
        await context.bot.send_message(chat_id, '❌ Model not found.')
        return

    if not teacher['available']:
        await context.bot.send_message(chat_id, '❌ This Model is currently unavailable.')
        return

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

💳 Payment:
Send ${teacher['price']} worth of Solana to this wallet:

{BTC_WALLET}


📸 Next Steps:
1. Send the payment
2. Take a screenshot of the transaction
3. Send the screenshot to this chat
4. Wait for admin confirmation

⏰ After payment verification, your teacher will contact you within 5 minutes."""
    await context.bot.send_message(chat_id, payment_message)


    # Notify admin about new booking
    username_display = f"@{student_username}" if student_username != "No username set" else "❌ No username set"

    admin_notification = f"""🔔 NEW BOOKING ALERT! 🔔
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 USER INFORMATION:
📝 Name: {student_full_name}
🏷️ Username: {username_display}
🆔 User ID: {user_id}
💬 Chat ID: {chat_id}

💃 MODEL BOOKED:
🌟 {teacher['name']}
💰 Rate: ${teacher['price']}/hour

📊 BOOKING DETAILS:
🆔 Booking ID: {booking_id}
📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
⏳ Status: Waiting for payment

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📞 CONTACT USER:
• Use username: {username_display}
• Or message directly via User ID: {user_id}

⚡ ACTION REQUIRED: Wait for payment screenshot!"""

    keyboard = [
        [InlineKeyboardButton("✅ Confirm Payment", callback_data=f"confirm_payment_{booking_id}")],
        [InlineKeyboardButton("❌ Reject Payment", callback_data=f"reject_payment_{booking_id}")]
    ]
    reply_markup = create_inline_keyboard(keyboard)

    # Send to all admins
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, admin_notification, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Failed to send admin notification to {admin_id}: {e}")

# Handle payment confirmation
async def handle_confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, booking_id: str) -> None:
    user = update.effective_user

    if not is_admin(user.id):
        await context.bot.send_message(update.effective_chat.id, '❌ Access denied. Admin only.')
        return

    booking = pending_payments.get(booking_id)
    if not booking:
        await context.bot.send_message(update.effective_chat.id, '❌ Booking not found.')
        return

    # Update booking status
    booking['status'] = 'confirmed'
    booking['confirmed_at'] = datetime.now()
    booking['confirmed_by'] = user.id

    # Remove from pending payments
    del pending_payments[booking_id]

    # Notify student
    student_message = f"""✅ PAYMENT CONFIRMED! ✅

🎉 Great news! Your booking has been confirmed.

📋 Booking Details:
• Modelr: {booking['teacher_name']}
• Booking ID: {booking_id}
• Status: ✅ Confirmed

📞 Next Steps:
Your love will contact you within 5 minutes to schedule your session.

Thank you for choosing SolCam! 💃 """

    try:
        await context.bot.send_message(booking['student_id'], student_message)
    except Exception as e:
        logger.error(f"Failed to notify student {booking['student_id']}: {e}")

    # Notify admin
    await context.bot.send_message(
        update.effective_chat.id,
        f"✅ Payment confirmed for booking {booking_id}. Student has been notified."
    )

# Handle payment rejection
async def handle_reject_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, booking_id: str) -> None:
    user = update.effective_user

    if not is_admin(user.id):
        await context.bot.send_message(update.effective_chat.id, '❌ Access denied. Admin only.')
        return

    booking = pending_payments.get(booking_id)
    if not booking:
        await context.bot.send_message(update.effective_chat.id, '❌ Booking not found.')
        return

    # Update booking status
    booking['status'] = 'rejected'
    booking['rejected_at'] = datetime.now()
    booking['rejected_by'] = user.id

    # Remove from pending payments
    del pending_payments[booking_id]

    # Notify student
    student_message = f"""❌ Payment Issue ❌

We couldn't verify your payment for booking {booking_id}.

📞 Next Steps:
• Please check your Solana transaction
• Contact our admin: {ADMIN_USERNAME}
• Or try booking again

We're here to help! 🤝"""

    try:
        await context.bot.send_message(booking['student_id'], student_message)
    except Exception as e:
        logger.error(f"Failed to notify student {booking['student_id']}: {e}")

    # Notify admin
    await context.bot.send_message(
        update.effective_chat.id,
        f"❌ Payment rejected for booking {booking_id}. Student has been notified."
    )

# Manage teachers (admin)
async def manage_teachers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id

    if not is_admin(user.id):
        await context.bot.send_message(chat_id, '❌ Access denied. Admin only.')
        return

    if not teachers:
        await context.bot.send_message(chat_id, '❌ No model available.')
        return

    management_message = """💃 MODEL MANAGEMENT 💃
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Select a teacher to edit their profile:"""

    keyboard = []
    for teacher in teachers:
        keyboard.append([InlineKeyboardButton(f"✏️ Edit {teacher['name']}", callback_data=f"edit_teacher_{teacher['id']}")])

    keyboard.append([InlineKeyboardButton("❌ Remove Model", callback_data='remove_teacher_menu')])
    keyboard.append([InlineKeyboardButton("🔙 Back to Admin", callback_data='admin')])

    reply_markup = create_inline_keyboard(keyboard)
    await context.bot.send_message(chat_id, management_message, reply_markup=reply_markup)

# Edit teacher profile
async def edit_teacher(update: Update, context: ContextTypes.DEFAULT_TYPE, teacher_id: int) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id

    if not is_admin(user.id):
        await context.bot.send_message(chat_id, '❌ Access denied. Admin only.')
        return

    teacher = next((t for t in teachers if t['id'] == teacher_id), None)
    if not teacher:
        await context.bot.send_message(chat_id, '❌ model not found.')
        return

    edit_message = f"""✏️ EDIT MODEL PROFILE ✏️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👨‍🏫 Current Profile: {teacher['name']}

Select field to edit:"""

    keyboard = [
        [InlineKeyboardButton("🩷 Name", callback_data=f"edit_field_name_{teacher_id}")],
        [InlineKeyboardButton("😘 Age", callback_data=f"edit_field_age_{teacher_id}")],
        [InlineKeyboardButton("💰 Price", callback_data=f"edit_field_price_{teacher_id}")],
        [InlineKeyboardButton("🥵 Interasted", callback_data=f"edit_field_subjects_{teacher_id}")],
        [InlineKeyboardButton("🎯 Why Choose", callback_data=f"edit_field_why_choose_{teacher_id}")],
        [InlineKeyboardButton("📖 Bio", callback_data=f"edit_field_bio_{teacher_id}")],
        [InlineKeyboardButton("🎓 Education", callback_data=f"edit_field_education_{teacher_id}")],
        [InlineKeyboardButton("😈 Experience", callback_data=f"edit_field_experience_{teacher_id}")],
        [InlineKeyboardButton("⭐ Rating", callback_data=f"edit_field_rating_{teacher_id}")],
        [InlineKeyboardButton("📸 Photo URL", callback_data=f"edit_field_photo_{teacher_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data='manage_teachers')]
    ]

    reply_markup = create_inline_keyboard(keyboard)
    await context.bot.send_message(chat_id, edit_message, reply_markup=reply_markup)

# Show bookings for admin
async def show_bookings_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id

    if not is_admin(user.id):
        await context.bot.send_message(chat_id, '❌ Access denied. Admin only.')
        return

    if not bookings:
        await context.bot.send_message(chat_id, '❌ No bookings yet.')
        return

    bookings_list = '📊 BOOKINGS MANAGEMENT 📊\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n'

    for i, booking in enumerate(bookings, 1):
        username_display = f"@{booking.get('student_username', 'No username')}" if booking.get('student_username') != "No username set" else "❌ No username"

        bookings_list += f"""📋 Booking #{i}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 STUDENT INFO:
📝 Name: {booking.get('student_name', 'Unknown')}
🏷️ Username: {username_display}
🆔 User ID: {booking['student_id']}

💃 MODEL: {booking['teacher_name']}
💰 PRICE: ${booking['price']}
📅 DATE: {booking['created_at'].strftime('%Y-%m-%d %H:%M:%S')}
🔄 STATUS: {booking['status']}

🆔 Booking ID: {booking['id']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

    await context.bot.send_message(chat_id, bookings_list)

# Show pending payments for admin
async def show_pending_payments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id

    if not is_admin(user.id):
        await context.bot.send_message(chat_id, '❌ Access denied. Admin only.')
        return

    if not pending_payments:
        await context.bot.send_message(chat_id, '✅ No pending payments.')
        return

    payments_list = '💰 PENDING PAYMENTS 💰\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n'

    for booking_id, booking in pending_payments.items():
        username_display = f"@{booking.get('student_username', 'No username')}" if booking.get('student_username') != "No username set" else "❌ No username"

        payments_list += f"""💳 Payment #{booking_id}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 USER: {booking.get('student_name', 'Unknown')}
🏷️ USERNAME: {username_display}
💃 MODEL: {booking['teacher_name']}
💰 AMOUNT: ${booking['price']}
📅 DATE: {booking['created_at'].strftime('%Y-%m-%d %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

    keyboard = []
    for booking_id in pending_payments.keys():
        keyboard.append([
            InlineKeyboardButton(f"✅ Confirm {booking_id}", callback_data=f"confirm_payment_{booking_id}"),
            InlineKeyboardButton(f"❌ Reject {booking_id}", callback_data=f"reject_payment_{booking_id}")
        ])

    keyboard.append([InlineKeyboardButton("🔙 Back to Admin", callback_data='admin')])
    reply_markup = create_inline_keyboard(keyboard)

    await context.bot.send_message(chat_id, payments_list, reply_markup=reply_markup)

# Add new teacher
async def add_teacher(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id

    if not is_admin(user.id):
        await context.bot.send_message(chat_id, '❌ Access denied. Admin only.')
        return

    # Set user state for adding teacher
    teacher_edit_states[user.id] = {
        'state': TEACHER_EDIT_STATES['WAITING_FOR_NEW_TEACHER'],
        'step': 'name',
        'teacher_data': {}
    }

    add_message = """➕ ADD NEW MODEL ➕
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Let's add a new model to the system!

📝 Step 1: model Name
Please enter the model's full name:"""

    await context.bot.send_message(chat_id, add_message)

# Remove teacher
async def remove_teacher(update: Update, context: ContextTypes.DEFAULT_TYPE, teacher_id: int) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id

    if not is_admin(user.id):
        await context.bot.send_message(chat_id, '❌ Access denied. Admin only.')
        return

    # Find and remove teacher
    global teachers
    teacher = next((t for t in teachers if t['id'] == teacher_id), None)

    if not teacher:
        await context.bot.send_message(chat_id, '❌ Model not found.')
        return

    teachers = [t for t in teachers if t['id'] != teacher_id]

    await context.bot.send_message(
        chat_id,
        f"✅ Model '{teacher['name']}' has been removed successfully."
    )

# Handle field editing
async def handle_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE, field: str, teacher_id: int) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id

    if not is_admin(user.id):
        await context.bot.send_message(chat_id, '❌ Access denied. Admin only.')
        return

    teacher = next((t for t in teachers if t['id'] == teacher_id), None)
    if not teacher:
        await context.bot.send_message(chat_id, '❌ Model not found.')
        return

    # Set editing state
    teacher_edit_states[user.id] = {
        'state': TEACHER_EDIT_STATES['WAITING_FOR_VALUE'],
        'field': field,
        'teacher_id': teacher_id
    }

    current_value = teacher.get(field, 'Not set')
    if field == 'subjects' and isinstance(current_value, list):
        current_value = ', '.join(current_value)

    field_names = {
        'name': 'Name',
        'age': 'Age',
        'price': 'Price (per hour)',
        'subjects': 'Subjects (comma-separated)',
        'why_choose': 'Why Choose This Teacher',
        'bio': 'Biography',
        'education': 'Education',
        'experience': 'Experience',
        'rating': 'Rating (0-5)',
        'photo': 'Photo URL'
    }

    field_display = field_names.get(field, field.title())

    edit_message = f"""✏️ EDIT {field_display.upper()} ✏️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💃 Model: {teacher['name']}
📝 Field: {field_display}
🔸 Current Value: {current_value}

Please enter the new value:"""

    await context.bot.send_message(chat_id, edit_message)

# Handle teacher editing process
async def handle_teacher_editing(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id

    if not is_admin(user.id):
        await context.bot.send_message(chat_id, '❌ Access denied. Admin only.')
        return

    state_info = teacher_edit_states[user.id]

    if state_info['state'] == TEACHER_EDIT_STATES['WAITING_FOR_VALUE']:
        # Update existing teacher field
        teacher_id = state_info['teacher_id']
        field = state_info['field']

        teacher = next((t for t in teachers if t['id'] == teacher_id), None)
        if not teacher:
            await context.bot.send_message(chat_id, '❌ Model not found.')
            del teacher_edit_states[user.id]
            return

        # Process the value based on field type
        try:
            if field == 'age':
                teacher[field] = int(text)
            elif field == 'price':
                teacher[field] = float(text)
            elif field == 'rating':
                rating = float(text)
                if 0 <= rating <= 5:
                    teacher[field] = rating
                else:
                    await context.bot.send_message(chat_id, '❌ Rating must be between 0 and 5.')
                    return
            elif field == 'subjects':
                teacher[field] = [s.strip() for s in text.split(',')]
            else:
                teacher[field] = text

            await context.bot.send_message(
                chat_id,
                f"✅ Successfully updated {field} for {teacher['name']}!"
            )

        except ValueError:
            await context.bot.send_message(chat_id, '❌ Invalid value format. Please try again.')
            return

        # Clean up state
        del teacher_edit_states[user.id]

    elif state_info['state'] == TEACHER_EDIT_STATES['WAITING_FOR_NEW_TEACHER']:
        # Add new teacher process
        await handle_add_teacher_step(update, context, text)

# Handle adding new teacher step by step
async def handle_add_teacher_step(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id

    state_info = teacher_edit_states[user.id]
    step = state_info['step']
    teacher_data = state_info['teacher_data']

    if step == 'name':
        teacher_data['name'] = text
        state_info['step'] = 'age'
        await context.bot.send_message(
            chat_id,
            f"✅ Name: {text}\n\n📝 Step 2: Age\nEnter the model's age:"
        )

    elif step == 'age':
        try:
            teacher_data['age'] = int(text)
            state_info['step'] = 'subjects'
            await context.bot.send_message(
                chat_id,
                f"✅ Age: {text}\n\n📝 Step 3: Subjects\nEnter subjects (comma-separated):"
            )
        except ValueError:
            await context.bot.send_message(chat_id, '❌ Please enter a valid age number.')

    elif step == 'subjects':
        teacher_data['subjects'] = [s.strip() for s in text.split(',')]
        state_info['step'] = 'price'
        await context.bot.send_message(
            chat_id,
            f"✅ Subjects: {text}\n\n📝 Step 4: Price\nEnter hourly rate ($):"
        )

    elif step == 'price':
        try:
            teacher_data['price'] = float(text)
            state_info['step'] = 'why_choose'
            await context.bot.send_message(
                chat_id,
                f"✅ Price: ${text}/hour\n\n📝 Step 5: Why Choose\nEnter why students should choose this teacher:"
            )
        except ValueError:
            await context.bot.send_message(chat_id, '❌ Please enter a valid price number.')

    elif step == 'why_choose':
        teacher_data['why_choose'] = text
        state_info['step'] = 'bio'
        await context.bot.send_message(
            chat_id,
            f"✅ Why Choose: {text[:50]}...\n\n📝 Step 6: Biography\nEnter teacher's bio:"
        )

    elif step == 'bio':
        teacher_data['bio'] = text
        state_info['step'] = 'education'
        await context.bot.send_message(
            chat_id,
            f"✅ Bio: {text[:50]}...\n\n📝 Step 7: Education\nEnter education background:"
        )

    elif step == 'education':
        teacher_data['education'] = text
        state_info['step'] = 'experience'
        await context.bot.send_message(
            chat_id,
            f"✅ Interested: {text[:50]}...\n\n📝 Step 8: Experience\nEnter teaching experience:"
        )

    elif step == 'experience':
        teacher_data['experience'] = text
        state_info['step'] = 'rating'
        await context.bot.send_message(
            chat_id,
            f"✅ Experience: {text[:50]}...\n\n📝 Step 9: Rating\nEnter rating (0-5):"
        )

    elif step == 'rating':
        try:
            rating = float(text)
            if 0 <= rating <= 5:
                teacher_data['rating'] = rating
                state_info['step'] = 'photo'
                await context.bot.send_message(
                    chat_id,
                    f"✅ Rating: {rating}/5\n\n📝 Step 10: Photo\nEnter photo URL (or skip with 'none'):"
                )
            else:
                await context.bot.send_message(chat_id, '❌ Rating must be between 0 and 5.')
        except ValueError:
            await context.bot.send_message(chat_id, '❌ Please enter a valid rating number.')

    elif step == 'photo':
        if text.lower() != 'none':
            teacher_data['photo'] = text
        else:
            teacher_data['photo'] = None

        # Create new teacher
        new_teacher_id = max([t['id'] for t in teachers]) + 1 if teachers else 1
        teacher_data['id'] = new_teacher_id
        teacher_data['available'] = True

        teachers.append(teacher_data)

        # Send confirmation
        confirmation = f"""✅ MODEL ADDED SUCCESSFULLY! ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👨‍🏫 {teacher_data['name']} has been added to the system!

📋 Summary:
• Age: {teacher_data['age']}
• Subjects: {', '.join(teacher_data['subjects'])}
• Price: ${teacher_data['price']}/hour
• Rating: {teacher_data['rating']}/5
• Status: Available

The model is now available for booking! 🎉"""

        await context.bot.send_message(chat_id, confirmation)

        # Clean up state
        del teacher_edit_states[user.id]

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

        elif callback_data == 'manage_teachers':
            await manage_teachers(update, context)

        elif callback_data == 'view_bookings':
            await show_bookings_admin(update, context)

        elif callback_data == 'view_payments':
            await show_pending_payments(update, context)

        elif callback_data == 'add_teacher':
            await add_teacher(update, context)

        elif callback_data == 'remove_teacher_menu':
            if not is_admin(user.id):
                await context.bot.send_message(chat_id, '❌ Access denied. Admin only.')
                return

            keyboard = [[InlineKeyboardButton(f"❌ Remove {teacher['name']}", callback_data=f"remove_teacher_{teacher['id']}")] for teacher in teachers]
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data='manage_teachers')])
            reply_markup = create_inline_keyboard(keyboard)
            await context.bot.send_message(chat_id, '🗑️ Remove Teachers:', reply_markup=reply_markup)

        elif callback_data == 'how_it_works':
            how_it_works_message = """ℹ️ HOW IT WORKS ℹ️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 Simple 4-Step Process:

1️⃣ Search your girl
   • check our avaliable girls
   • choose your fovorite girl
   • view her profile

2️⃣ Select & Book
   • Choose your beuty
   • Review pricing and availability
   • Confirm your booking

3️⃣ Secure Payment
   • Pay with Solana (secure & private)
   • Send payment screenshot
   • Wait for admin verification

4️⃣ get live with your lady
   • lady contacts you within 5 minutes
   • Schedule your first session
   • then enjoy on our serves!

💡 Why Choose Us?
• loyality and trust
• professional models
• Easy booking process
• Fast payment verification
• Secure Bitcoin payments for privacy
• 24/7 admin support for any issues

Ready to get started? Click "Browse Teachers" below! 🚀"""

            keyboard = [
                [InlineKeyboardButton("💃 Browse Models", callback_data='check_teachers')],
                [InlineKeyboardButton("🔙 Back to Main", callback_data='back_to_main')]
            ]
            reply_markup = create_inline_keyboard(keyboard)
            await context.bot.send_message(chat_id, how_it_works_message, reply_markup=reply_markup)

        elif callback_data == 'back_to_main':
            await start(update, context)

        elif callback_data == 'contact_support':
            support_message = f"""💬 CONTACT SUPPORT 💬
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤝 Need Help?
We're here to assist you 24/7!

📞 Support Contact:
{ADMIN_USERNAME}

💡 What we can help with:
• booking assistance
• Payment verification issues
• Technical support
• Account questions
• General inquiries

⚡ Response Time:
We typically respond within 5 minutes during business hours.

Don't hesitate to reach out - we're happy to help! 😊"""

            keyboard = [
                [InlineKeyboardButton("📱 Message Support", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")],
                [InlineKeyboardButton("🔙 Back to Main", callback_data='back_to_main')]
            ]
            reply_markup = create_inline_keyboard(keyboard)
            await context.bot.send_message(chat_id, support_message, reply_markup=reply_markup)

        elif callback_data == 'user_profile':
            await show_user_profile(update, context)

        elif callback_data == 'referral_system':
            await show_referral_system(update, context)

        elif callback_data.startswith('book_teacher_'):
            teacher_id = int(callback_data.split('_')[2])
            await handle_book_teacher(update, context, teacher_id)

        elif callback_data.startswith('profile_teacher_'):
            teacher_id = int(callback_data.split('_')[2])
            await show_teacher_profile(update, context, teacher_id)

        elif callback_data.startswith('edit_teacher_'):
            teacher_id = int(callback_data.split('_')[2])
            await edit_teacher(update, context, teacher_id)

        elif callback_data.startswith('edit_field_'):
            parts = callback_data.split('_')
            field = parts[2]
            teacher_id = int(parts[3])
            await handle_edit_field(update, context, field, teacher_id)

        elif callback_data.startswith('remove_teacher_'):
            teacher_id = int(callback_data.split('_')[2])
            await remove_teacher(update, context, teacher_id)

        elif callback_data.startswith('confirm_payment_'):
            booking_id = callback_data.split('_')[2]
            await handle_confirm_payment(update, context, booking_id)

        elif callback_data.startswith('reject_payment_'):
            booking_id = callback_data.split('_')[2]
            await handle_reject_payment(update, context, booking_id)

        elif callback_data == 'share_referral':
            await show_referral_system(update, context)

        elif callback_data == 'my_bookings':
            await show_user_profile(update, context) # Assuming bookings are part of user profile

        elif callback_data == 'withdraw_earnings':
            user_id = user.id
            profile = get_user_profile(user_id)
            if profile['total_earnings'] > 0:
                withdraw_message = f"""💰 WITHDRAW EARNINGS 💰
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 Your Current Earnings: ${profile['total_earnings']}

💳 Payment Details:
• Wallet Address: {BTC_WALLET}
• Amount: ${profile['total_earnings']}
• Currency: Solana (Sol)

📝 Next Steps:
1. Send the exact amount of ${profile['total_earnings']} to the wallet address above.
2. Take a screenshot of the transaction.
3. Send the screenshot to this chat.
4. Wait for admin confirmation.

⏰ After payment verification, your earnings will be added to your account.

💡 Note: Withdrawals are processed manually by the admin.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
                await context.bot.send_message(chat_id, withdraw_message)
            else:
                await context.bot.send_message(chat_id, "You don't have any earnings to withdraw yet!")

        elif callback_data == 'share_referral_code':
            user_id = user.id
            profile = get_user_profile(user_id)
            referral_link = f"https://t.me/{context.bot.username}?start={user_id}"
            share_message = f"""📤 SHARE YOUR REFERRAL CODE 📤
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎁 Your Referral Code: `{profile['referral_code']}`

🚀 Share this link with your friends to earn rewards!

{referral_link}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Start earning today! 💸"""
            await context.bot.send_message(chat_id, share_message)

        elif callback_data == 'referral_stats':
             user_id = user.id
             profile = get_user_profile(user_id)
             referred_by_display = f"@{user_profiles.get(profile['referred_by'], {}).get('username', 'Direct signup')}" if profile['referred_by'] else "Direct signup"

             referral_stats_message = f"""📊 REFERRAL STATS 📊
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 Your Referral Code: `{profile['referral_code']}`
👥 Referred By: {referred_by_display}
👥 Referrals Made: {profile['referrals_made']}
💰 Total Earnings from Referrals: ${profile['total_earnings']}
🎁 Pending Rewards: ${referral_rewards.get(user_id, 0)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Start earning today! 💸"""
             await context.bot.send_message(chat_id, referral_stats_message)

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

👥 **Total Users**: {total_users}

🏆 **User Status Breakdown**:
• 🥉 Bronze: {bronze_users} users
• 🥈 Silver: {silver_users} users  
• 🥇 Gold: {gold_users} users
• 💎 Platinum: {platinum_users} users

📈 **Engagement Stats**:
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

📊 **System Statistics**:
• Total Referrals: {total_referrals}
• Total Rewards Paid: ${total_rewards}
• Active Referrers: {len([p for p in user_profiles.values() if p['referrals_made'] > 0])}

💰 **Reward Settings**:
• Referral Reward: ${REFERRAL_REWARD}
• Referee Bonus: ${REFERRAL_BONUS}

📈 **Top Referrers**:"""
             
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

        else:
            await context.bot.send_message(
                chat_id,
                f'🤔 Unknown action: {callback_data}\n\n'
                f'Need help? Contact our admin: {ADMIN_USERNAME}\n\n'
                f'We\'re here to help! 🤝'
            )

    except Exception as e:
        logger.error(f"Error in callback query handler: {e}")
        await context.bot.send_message(
            chat_id,
            "❌ An error occurred. Please try again or contact admin."
        )

# Handle photo uploads
# Handle photo uploads
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    photo = update.message.photo[-1]  # Best quality

    # 🔍 Check if this user has a pending payment
    booking = next((b for b in pending_payments.values() if b['student_id'] == user.id), None)

    if booking:
        await context.bot.send_message(
            chat_id,
            "📸 Payment screenshot received! Our admin will verify it shortly.\n\n"
            "⏰ You'll receive confirmation within 5 minutes."
        )

        student_username = user.username or "No username set"
        student_full_name = user.full_name or "Unknown"
        username_display = f"@{student_username}" if student_username != "No username set" else "❌ No username set"

        admin_message = f"""📸 PAYMENT SCREENSHOT RECEIVED! 📸
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 user INFO:
📝 Name: {student_full_name}
🏷️ Username: {username_display}
🆔 User ID: {user.id}
📋 Booking ID: {booking['id']}
📅 Received: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚡ ACTION NEEDED: Review the screenshot and confirm/reject the payment.
"""

        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(admin_id, admin_message)
                await context.bot.send_photo(
                    chat_id=admin_id,
                    photo=photo.file_id,
                    caption=f"💳 Payment Proof from {student_full_name} ({username_display})"
                )
            except Exception as e:
                logger.error(f"Failed to send screenshot to admin {admin_id}: {e}")

    else:
        # Optional fallback if no pending booking
        await context.bot.send_message(
            chat_id,
            "📸 Photo received. If this is a payment screenshot, it will be reviewed shortly."
        )

# Handle text messages
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    text = update.message.text

    # Check if user is in teacher editing state
    if user.id in teacher_edit_states:
        await handle_teacher_editing(update, context, text)
        return

    # Default response for regular text
    await context.bot.send_message(
        chat_id,
        f"💬 I received your message: \"{text}\"\n\n"
        f"Use the menu buttons to navigate the bot.\n"
        f"Need help? Contact: {ADMIN_USERNAME}"
    )

# Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Update {update} caused error {context.error}")

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
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()