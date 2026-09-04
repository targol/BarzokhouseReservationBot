# -*- coding: utf-8 -*-
"""
Script to create the updated bot.py with full food order conversation support
"""

updated_bot_code = '''# -*- coding: utf-8 -*-
"""
ربات رزرو و سفارش غذای اقامتگاه بومگردی «خانه برزک»
--------------------------------------------------
اجرا:
    python bot.py
قبل از اجرا حتما فایل config.py رو با اطلاعات واقعی خودت پر کن.
"""

import logging
import os
import jdatetime
from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# وضعیت‌های مکالمه‌ی رزرو اتاق
# ---------------------------------------------------------------------------
ASK_NAME, ASK_PHONE, ASK_CHECKIN, ASK_NIGHTS, ASK_GUESTS = range(5)

# ---------------------------------------------------------------------------
# وضعیت‌های مکالمه‌ی سفارش غذا
# ---------------------------------------------------------------------------
(
    FOOD_ASK_GUEST_NAME,
    FOOD_ASK_PHONE,
    FOOD_ASK_ROOM,
    FOOD_ASK_DAY,
    FOOD_ASK_MEAL,
    FOOD_SELECT_ITEM,
    FOOD_ASK_PORTIONS,
) = range(5, 12)

PERSIAN_WEEKDAYS = ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
WEEKDAY_LABELS_FA = ["ش", "ی", "د", "س", "چ", "پ", "ج"]  # شنبه تا جمعه


def to_english_digits(text: str) -> str:
    """تبدیل ارقام فارسی/عربی به انگلیسی، برای اعتبارسنجی راحت‌تر عدد."""
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    arabic_digits = "٠١٢٣٤٥٦٧٨٩"
    translation = {}
    for i, ch in enumerate(persian_digits):
        translation[ch] = str(i)
    for i, ch in enumerate(arabic_digits):
        translation[ch] = str(i)
    return "".join(translation.get(ch, ch) for ch in text)


def jalali_days_in_month(year: int, month: int) -> int:
    if month <= 6:
        return 31
    elif month <= 11:
        return 30
    else:
        return 30 if jdatetime.date(year, 1, 1).isleap() else 29


def build_calendar_keyboard(year: int, month: int, prefix: str = "cal_day_") -> InlineKeyboardMarkup:
    today = jdatetime.date.today()
    rows = []

    # هدر: ماه/سال + دکمه‌های قبلی و بعدی
    prev_month, prev_year = (month - 1, year) if month > 1 else (12, year - 1)
    next_month, next_year = (month + 1, year) if month < 12 else (1, year + 1)

    # اگه ماه قبلی کاملاً در گذشته باشه، دکمه‌ی قبلی غیرفعال (خالی) میشه
    nav_prefix = "cal_nav_" if prefix == "cal_day_" else "fcal_nav_"
    if (year, month) <= (today.year, today.month):
        prev_button = InlineKeyboardButton(" ", callback_data="ignore")
    else:
        prev_button = InlineKeyboardButton("⬅️", callback_data=f"{nav_prefix}{prev_year}_{prev_month}")

    month_label = f"{jdatetime.date.j_months_fa[month - 1]} {year}"
    rows.append(
        [
            prev_button,
            InlineKeyboardButton(month_label, callback_data="ignore"),
            InlineKeyboardButton("➡️", callback_data=f"{nav_prefix}{next_year}_{next_month}"),
        ]
    )

    # هدر روزهای هفته
    rows.append([InlineKeyboardButton(d, callback_data="ignore") for d in WEEKDAY_LABELS_FA])

    first_weekday = jdatetime.date(year, month, 1).weekday()  # 0=شنبه
    days_in_month = jalali_days_in_month(year, month)

    day_buttons = [InlineKeyboardButton(" ", callback_data="ignore")] * first_weekday

    for day in range(1, days_in_month + 1):
        this_date = jdatetime.date(year, month, day)
        if this_date < today:
            day_buttons.append(InlineKeyboardButton(" ", callback_data="ignore"))
        else:
            label = f"•{day}" if this_date == today else str(day)
            day_buttons.append(
                InlineKeyboardButton(label, callback_data=f"{prefix}{year}_{month}_{day}")
            )

    # تقسیم روزها به ردیف‌های ۷تایی
    for i in range(0, len(day_buttons), 7):
        row = day_buttons[i : i + 7]
        while len(row) < 7:
            row.append(InlineKeyboardButton(" ", callback_data="ignore"))
        rows.append(row)

    return InlineKeyboardMarkup(rows)


def parse_checkin_date(raw_text: str):
    """
    تاریخ ورودی کاربر رو پارس می‌کنه (شمسی یا میلادی، با / یا - جدا شده)
    و در صورت معتبر بودن، تاریخ میلادی امروز رو برمی‌گردونه (برای مقایسه).
    اگه فرمت یا تاریخ نامعتبر بود، None برمی‌گردونه.
    """
    text = to_english_digits(raw_text.strip())
    parts = text.replace("-", "/").split("/")
    if len(parts) != 3:
        return None
    try:
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return None

    try:
        if year > 1700:
            # تاریخ میلادی
            import datetime
            return datetime.date(year, month, day)
        else:
            # تاریخ شمسی
            jdate = jdatetime.date(year, month, day)
            return jdate.togregorian()
    except ValueError:
        return None


def parse_jalali_date_details(raw_text: str):
    """
    تاریخ شمسی رو پارس می‌کنه و آبجکت jdatetime.date رو برمی‌گردونه.
    """
    text = to_english_digits(raw_text.strip())
    parts = text.replace("-", "/").split("/")
    if len(parts) != 3:
        return None
    try:
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        return jdatetime.date(year, month, day)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# کیبوردهای کمکی منوی اصلی و بخش‌ها
# ---------------------------------------------------------------------------
def main_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("🛏 اتاق‌ها و رزرو", callback_data="menu_rooms")],
        [InlineKeyboardButton("🍽 منوی غذا و سفارش خوراک", callback_data="menu_food")],
        [InlineKeyboardButton("📜 اطلاعاتی درباره اقامتگاه", callback_data="menu_rules")],
        [InlineKeyboardButton("📍 آدرس و موقعیت", callback_data="menu_address")],
        [InlineKeyboardButton("📞 تماس با ما", callback_data="menu_contact")],
        [InlineKeyboardButton("🌐 شبکه‌های اجتماعی", callback_data="menu_social")],
        [InlineKeyboardButton("💳 پرداخت آنلاین", callback_data="menu_payment")],
        [InlineKeyboardButton("⭐ ثبت تجربه شما", callback_data="menu_review")],
    ]
    return InlineKeyboardMarkup(buttons)


def back_to_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ بازگشت به منو", callback_data="back_main")]]
    )


def rooms_list_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for key, room in config.ROOMS.items():
        buttons.append(
            [InlineKeyboardButton(room["title"], callback_data=f"room_{key}")]
        )
    buttons.append([InlineKeyboardButton("⬅️ بازگشت به منو", callback_data="back_main")])
    return InlineKeyboardMarkup(buttons)


def room_detail_keyboard(room_key: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("✅ درخواست رزرو این اتاق", callback_data=f"book_{room_key}")],
        [InlineKeyboardButton("⬅️ بازگشت به لیست اتاق‌ها", callback_data="menu_rooms")],
    ]
    return InlineKeyboardMarkup(buttons)


def food_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("🍲 ثبت درخواست غذا (ناهار / شام)", callback_data="food_order_start")],
        [InlineKeyboardButton("📋 مشاهده لیست خوراک‌ها و قیمت", callback_data="food_list_details")],
        [InlineKeyboardButton("🌐 دستور پخت غذاها در وبسایت", url=config.FOOD_MENU_URL)],
        [InlineKeyboardButton("⬅️ بازگشت به منو", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(buttons)


def food_items_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for key, food in getattr(config, "FOODS", {}).items():
        buttons.append([InlineKeyboardButton(f"{food['title']} - {food['price']}", callback_data=f"fooditem_{key}")])
    buttons.append([InlineKeyboardButton("🍲 ثبت درخواست غذا", callback_data="food_order_start")])
    buttons.append([InlineKeyboardButton("⬅️ بازگشت به منوی غذا", callback_data="menu_food")])
    return InlineKeyboardMarkup(buttons)


def phone_request_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📱 ارسال شماره تماس من", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


# ---------------------------------------------------------------------------
# دستور /start و دستورات پایه
# ---------------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        config.WELCOME_MESSAGE, reply_markup=main_menu_keyboard()
    )


async def cmd_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(config.ADDRESS_TEXT)
    await context.bot.send_location(
        chat_id=update.effective_chat.id,
        latitude=config.LOCATION_LATITUDE,
        longitude=config.LOCATION_LONGITUDE,
    )


async def cmd_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(config.CONTACT_TEXT)


async def cmd_food(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        config.FOOD_MENU_TEXT,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=food_menu_keyboard(),
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "درخواست شما لغو شد. هر وقت مایل بودید می‌توانید مجدداً از /start شروع کنید.",
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_outside_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "در حال حاضر هیچ فرآیند رزرو یا درخواستی فعال نیست که لغو شود.\n"
        "برای شروع، /start را ارسال کنید."
    )


async def receive_payment_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """دریافت عکس فیش پرداخت و فوروارد برای مدیریت"""
    user = update.effective_user
    try:
        await context.bot.forward_message(
            chat_id=config.ADMIN_CHAT_ID,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
        )
        await context.bot.send_message(
            chat_id=config.ADMIN_CHAT_ID,
            text=(
                "☝️ فیش پرداخت بالا از طرف:\n"
                f"👤 {user.full_name}\n"
                f"🆔 آیدی تلگرام: @{user.username if user.username else 'ندارد'}"
            ),
        )
    except Exception as exc:
        logger.error("ارسال فیش پرداخت به مدیر با خطا مواجه شد: %s", exc)
        await update.message.reply_text(
            "متاسفانه در ارسال فیش پرداخت مشکلی پیش اومد. لطفاً دوباره امتحان کنید یا از "
            "طریق «تماس با ما» با ما در ارتباط باشید."
        )
        return

    await update.message.reply_text(
        "✅ فیش پرداخت شما دریافت و برای مدیریت اقامتگاه ارسال شد. ممنون از پرداختتون 🙏"
    )


# ---------------------------------------------------------------------------
# روتر دکمه‌های شیشه‌ای منوهای اصلی
# ---------------------------------------------------------------------------
async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_main":
        if query.message.photo:
            try:
                await query.message.delete()
            except Exception:
                pass
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=config.WELCOME_MESSAGE,
                reply_markup=main_menu_keyboard(),
            )
        else:
            await query.edit_message_text(
                config.WELCOME_MESSAGE, reply_markup=main_menu_keyboard()
            )
        return

    if data == "menu_address":
        await query.edit_message_text(
            config.ADDRESS_TEXT, reply_markup=back_to_main_keyboard()
        )
        await context.bot.send_location(
            chat_id=query.message.chat_id,
            latitude=config.LOCATION_LATITUDE,
            longitude=config.LOCATION_LONGITUDE,
        )
        return

    if data == "menu_contact":
        await query.edit_message_text(
            config.CONTACT_TEXT, reply_markup=back_to_main_keyboard()
        )
        return

    if data == "menu_social":
        await query.edit_message_text(
            config.SOCIAL_TEXT, reply_markup=back_to_main_keyboard()
        )
        return

    if data == "menu_payment":
        payment_keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("💳 پرداخت آنلاین", url=config.PAYMENT_URL)],
                [InlineKeyboardButton("⬅️ بازگشت به منو", callback_data="back_main")],
            ]
        )
        await query.edit_message_text(
            "💳 برای پرداخت هزینه‌ رزرو یا پیش پرداخت، روی دکمه‌ زیر بزنید تا به درگاه پرداخت منتقل بشید.\n\n"
            "بعد از پرداخت، می‌تونید عکس رسید پرداخت رو همینجا برای ما ارسال کنید؛ به‌صورت خودکار "
            "برای مدیریت اقامتگاه فرستاده میشه. 📎",
            reply_markup=payment_keyboard,
        )
        return

    if data == "menu_food":
        await query.edit_message_text(
            config.FOOD_MENU_TEXT,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=food_menu_keyboard(),
        )
        return

    if data == "food_list_details":
        foods = getattr(config, "FOODS", {})
        text_lines = ["🍽 <b>لیست خوراک‌ها و غذاهای اقامتگاه خانه برزک:</b>\n"]
        for key, food in foods.items():
            meal_names = [config.MEALS[m]["title"] for m in food.get("available_meals", []) if m in config.MEALS]
            meals_str = " و ".join(meal_names) if meal_names else "ناهار و شام"
            text_lines.append(
                f"▫️ <b>{food['title']}</b>\n"
                f"   💵 قیمت: {food['price']}\n"
                f"   🕒 وعده‌های ارائه: {meals_str}\n"
                f"   📝 {food['description']}\n"
            )
        text_lines.append("برای ثبت درخواست وعده ناهار یا شام بر روی دکمه زیر بزنید 👇")
        full_text = "\n".join(text_lines)
        await query.edit_message_text(
            full_text,
            parse_mode="HTML",
            reply_markup=food_items_keyboard(),
        )
        return

    if data.startswith("fooditem_"):
        food_key = data.replace("fooditem_", "")
        food = getattr(config, "FOODS", {}).get(food_key)
        if not food:
            await query.edit_message_text("غذا پیدا نشد.", reply_markup=food_menu_keyboard())
            return
        meal_names = [config.MEALS[m]["title"] for m in food.get("available_meals", []) if m in config.MEALS]
        meals_str = " و ".join(meal_names) if meal_names else "ناهار و شام"
        item_text = (
            f"🍲 <b>{food['title']}</b>\n\n"
            f"💵 <b>قیمت:</b> {food['price']}\n"
            f"🕒 <b>قابل سفارش برای:</b> {meals_str}\n\n"
            f"📖 <b>توضیحات:</b>\n{food['description']}"
        )
        item_keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🍲 ثبت درخواست غذا", callback_data="food_order_start")],
                [InlineKeyboardButton("⬅️ بازگشت به لیست غذاها", callback_data="food_list_details")],
            ]
        )
        await query.edit_message_text(item_text, parse_mode="HTML", reply_markup=item_keyboard)
        return

    if data == "menu_rules":
        try:
            await query.message.delete()
        except Exception:
            pass

        rules_keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏡 آشنایی با خانه برزک", url=config.HOUSE_RULES_SITE_URL)],
                [InlineKeyboardButton("📋 نکات پیش از اقامت", url=config.HOUSE_RULES_TIPS_URL)],
            ]
        )
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=config.HOUSE_RULES_TEXT,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=rules_keyboard,
        )

        weather_keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🌤 مشاهده آب‌وهوا", url=config.WEATHER_URL)]]
        )
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=config.WEATHER_TEXT,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=weather_keyboard,
        )

        green_trip_keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🌿 مشاهده در سایت", url=config.GREEN_TRIP_URL)],
                [InlineKeyboardButton("⬅️ بازگشت به منو", callback_data="back_main")],
            ]
        )
        green_photo_path = config.GREEN_TRIP_PHOTO
        if green_photo_path and os.path.exists(green_photo_path):
            with open(green_photo_path, "rb") as photo_file:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=photo_file,
                    caption=config.GREEN_TRIP_TEXT,
                    parse_mode="HTML",
                    reply_markup=green_trip_keyboard,
                )
        else:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=config.GREEN_TRIP_TEXT,
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=green_trip_keyboard,
            )
        return

    if data == "menu_review":
        review_keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📍 ثبت نظر در Google Maps", url=config.REVIEW_GOOGLE_MAPS_URL)],
                [InlineKeyboardButton("✈️ ثبت نظر در TripAdvisor", url=config.REVIEW_TRIPADVISOR_URL)],
                [InlineKeyboardButton("⬅️ بازگشت به منو", callback_data="back_main")],
            ]
        )
        await query.edit_message_text(
            config.REVIEW_TEXT,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=review_keyboard,
        )
        return

    if data == "menu_rooms":
        rooms_text = "🛏 لیست اتاق‌های اقامتگاه:\nیکی از اتاق‌ها رو برای دیدن جزئیات انتخاب کن 👇"
        if query.message.photo:
            try:
                await query.message.delete()
            except Exception:
                pass
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=rooms_text,
                reply_markup=rooms_list_keyboard(),
            )
        else:
            await query.edit_message_text(rooms_text, reply_markup=rooms_list_keyboard())
        return

    if data.startswith("room_"):
        room_key = data.replace("room_", "")
        room = config.ROOMS.get(room_key)
        if not room:
            await query.edit_message_text("متاسفانه این اتاق پیدا نشد.")
            return

        caption = f"🛏 {room['title']}\n\n{room['description']}\n\n💰 {room['price']}"
        photo_path = room.get("photo")

        try:
            await query.message.delete()
        except Exception:
            pass

        if photo_path and os.path.exists(photo_path):
            with open(photo_path, "rb") as photo_file:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=photo_file,
                    caption=caption,
                    reply_markup=room_detail_keyboard(room_key),
                )
        else:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=caption,
                reply_markup=room_detail_keyboard(room_key),
            )
        return


# ---------------------------------------------------------------------------
# مکالمه‌ی رزرو اتاق
# ---------------------------------------------------------------------------
async def book_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    room_key = query.data.replace("book_", "")
    room = config.ROOMS.get(room_key)
    if not room:
        await query.message.reply_text("متاسفانه این اتاق پیدا نشد.")
        return ConversationHandler.END

    context.user_data["booking_room_key"] = room_key
    context.user_data["booking_room_title"] = room["title"]
    context.user_data["booking_room_price"] = room["price"]

    await query.message.reply_text(
        f"برای رزرو «{room['title']}» ({room['price']}) ابتدا لطفاً نام و نام خانوادگی خودتون رو وارد کنید:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ASK_NAME


async def book_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    if len(name) < 3:
        await update.message.reply_text("لطفاً یک نام معتبر وارد کنید:")
        return ASK_NAME
    context.user_data["booking_name"] = name
    await update.message.reply_text(
        "سپاس! حالا لطفاً شماره تماس خودتون رو وارد کنید یا با دکمه زیر ارسال کنید:",
        reply_markup=phone_request_keyboard(),
    )
    return ASK_PHONE


async def book_get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text.strip()

    if len(phone) < 10:
        await update.message.reply_text("لطفاً یک شماره تماس معتبر وارد کنید:")
        return ASK_PHONE

    context.user_data["booking_phone"] = phone
    today = jdatetime.date.today()
    await update.message.reply_text(
        "ممنون! حالا لطفاً تاریخ ورود رو از تقویم زیر انتخاب کنید 👇\n"
        "(یا می‌تونید تایپ هم کنید، مثلاً ۱۴۰۵/۰۵/۱۰)",
        reply_markup=ReplyKeyboardRemove(),
    )
    await update.message.reply_text(
        "📅 انتخاب تاریخ ورود:",
        reply_markup=build_calendar_keyboard(today.year, today.month, prefix="cal_day_"),
    )
    return ASK_CHECKIN


async def calendar_ignore(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()


async def calendar_navigate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    _, _, year_str, month_str = query.data.split("_")
    year, month = int(year_str), int(month_str)
    await query.edit_message_reply_markup(reply_markup=build_calendar_keyboard(year, month, prefix="cal_day_"))
    return ASK_CHECKIN


async def calendar_select_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    _, _, year_str, month_str, day_str = query.data.split("_")
    year, month, day = int(year_str), int(month_str), int(day_str)
    jdate = jdatetime.date(year, month, day)
    weekday_name = PERSIAN_WEEKDAYS[jdate.weekday()]
    checkin_text = f"{year}/{month:02d}/{day:02d} ({weekday_name})"
    context.user_data["booking_checkin"] = checkin_text

    await query.edit_message_text(f"📅 تاریخ ورود انتخاب‌شده: {checkin_text}")
    await query.message.reply_text("تعداد شب‌های اقامت رو وارد کنید (مثلاً 2):")
    return ASK_NIGHTS


async def book_get_checkin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    checkin_date_raw = update.message.text.strip()
    parsed_date = parse_checkin_date(checkin_date_raw)

    if parsed_date is None:
        await update.message.reply_text(
            "فرمت تاریخ نامعتبره. لطفاً به این شکل وارد کنید (مثلاً ۱۴۰۵/۰۵/۱۰):"
        )
        return ASK_CHECKIN

    today = jdatetime.date.today().togregorian()
    if parsed_date < today:
        await update.message.reply_text(
            "تاریخ ورود نمی‌تونه قبل از امروز باشه. لطفاً یک تاریخ درست وارد کنید (مثلاً ۱۴۰۵/۰۵/۱۰):"
        )
        return ASK_CHECKIN

    j_date = parse_jalali_date_details(checkin_date_raw)
    if j_date:
        weekday_name = PERSIAN_WEEKDAYS[j_date.weekday()]
        checkin_display = f"{checkin_date_raw} ({weekday_name})"
    else:
        checkin_display = checkin_date_raw

    context.user_data["booking_checkin"] = checkin_display
    await update.message.reply_text("تعداد شب‌های اقامت رو وارد کنید (مثلاً 2):")
    return ASK_NIGHTS


async def book_get_nights(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    nights_raw = to_english_digits(update.message.text.strip())
    if not nights_raw.isdigit() or int(nights_raw) < 1:
        await update.message.reply_text("لطفاً تعداد شب رو به‌صورت عدد وارد کنید (مثلاً 2):")
        return ASK_NIGHTS

    context.user_data["booking_nights"] = nights_raw
    await update.message.reply_text("تعداد نفرات رو وارد کنید (مثلاً 2):")
    return ASK_GUESTS


async def book_get_guests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    guests_raw = to_english_digits(update.message.text.strip())
    if not guests_raw.isdigit() or int(guests_raw) < 1:
        await update.message.reply_text("لطفاً تعداد نفرات رو به‌صورت عدد وارد کنید (مثلاً 2):")
        return ASK_GUESTS

    context.user_data["booking_guests"] = guests_raw
    await finalize_booking(update, context)
    return ConversationHandler.END


async def finalize_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    room_title = context.user_data.get("booking_room_title")
    room_price = context.user_data.get("booking_room_price")
    name = context.user_data.get("booking_name")
    phone = context.user_data.get("booking_phone")
    checkin = context.user_data.get("booking_checkin")
    nights = context.user_data.get("booking_nights")
    guests = context.user_data.get("booking_guests")

    admin_text = (
        "⭕🔔 <b>درخواست رزرو اتاق جدید</b>\n\n"
        f"🛏 <b>اتاق:</b> {room_title}\n"
        f"💰 <b>نرخ:</b> {room_price}\n"
        f"👤 <b>نام مهمان:</b> {name}\n"
        f"📅 <b>تاریخ ورود:</b> {checkin}\n"
        f"🌙 <b>تعداد شب:</b> {nights}\n"
        f"👥 <b>تعداد نفرات:</b> {guests}\n"
        f"📞 <b>شماره تماس:</b> {phone}\n"
        f"🆔 <b>آیدی تلگرام:</b> @{user.username if user.username else 'ندارد'}"
    )

    try:
        await context.bot.send_message(
            chat_id=config.ADMIN_CHAT_ID, text=admin_text, parse_mode="HTML"
        )
    except Exception as exc:
        logger.error("ارسال پیام به مدیر با خطا مواجه شد: %s", exc)

    await update.message.reply_text(
        "✅ درخواست رزرو شما با موفقیت ثبت و برای مدیریت اقامتگاه ارسال شد.\n"
        "به‌زودی برای هماهنگی نهایی و تایید رزرو با شما تماس گرفته می‌شود.\n\n"
        "💡 <i>در صورتی که مایل به سفارش ناهار یا شام محلی برای روزهای اقامت خود هستید، می‌توانید از بخش «منوی غذا» درخواست خود را ثبت کنید.</i>\n\n"
        f"{config.CONTACT_TEXT}\n\n"
        f"{config.ADDRESS_TEXT}",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )
    await context.bot.send_location(
        chat_id=update.effective_chat.id,
        latitude=config.LOCATION_LATITUDE,
        longitude=config.LOCATION_LONGITUDE,
    )
    await update.message.reply_text("برای بازگشت به منوی اصلی /start رو بزنید.")
    context.user_data.clear()


# ---------------------------------------------------------------------------
# مکالمه‌ی سفارش غذا (ناهار / شام با تاریخ و روز هفته و حداکثر ۲ نوع غذا)
# ---------------------------------------------------------------------------
def build_food_selection_keyboard(selected_meal: str, selected_foods: dict) -> InlineKeyboardMarkup:
    """ساخت کیبورد انتخاب غذا بر اساس وعده انتخابی و رعایت سقف ۲ نوع غذا"""
    foods = getattr(config, "FOODS", {})
    max_selections = getattr(config, "MAX_FOOD_SELECTIONS", 2)
    buttons = []

    for food_key, food in foods.items():
        allowed_meals = food.get("available_meals", ["lunch", "dinner"])
        if selected_meal in allowed_meals:
            if food_key in selected_foods:
                portions = selected_foods[food_key]["portions"]
                label = f"✅ {food['title']} ({portions} پرس) - {food['price']}"
            else:
                label = f"▫️ {food['title']} - {food['price']}"
            buttons.append([InlineKeyboardButton(label, callback_data=f"fsel_{food_key}")])

    action_row = []
    if len(selected_foods) > 0:
        action_row.append(InlineKeyboardButton("✅ تایید و ثبت نهایی سفارش", callback_data="food_finalize"))
    action_row.append(InlineKeyboardButton("❌ انصراف", callback_data="food_cancel_order"))
    buttons.append(action_row)

    return InlineKeyboardMarkup(buttons)


async def food_order_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # آماده‌سازی دیتای سفارش در user_data
    context.user_data["food_order"] = {
        "items": {},  # { food_key: { "title": str, "price": str, "portions": int } }
    }

    await query.message.reply_text(
        "🍲 <b>ثبت درخواست وعده غذایی در خانه برزک</b>\n\n"
        "لطفاً ابتدا نام و نام خانوادگی خود را وارد نمایید:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )
    return FOOD_ASK_GUEST_NAME


async def food_get_guest_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    if len(name) < 3:
        await update.message.reply_text("لطفاً یک نام معتبر وارد کنید:")
        return FOOD_ASK_GUEST_NAME

    context.user_data["food_order"]["name"] = name
    await update.message.reply_text(
        f"سپاس جناب/سرکار {name} عزیز.\n"
        "لطفاً شماره تماس خود را وارد کنید یا با دکمه زیر ارسال نمایید:",
        reply_markup=phone_request_keyboard(),
    )
    return FOOD_ASK_PHONE


async def food_get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text.strip()

    if len(phone) < 10:
        await update.message.reply_text("لطفاً یک شماره تماس معتبر وارد کنید:")
        return FOOD_ASK_PHONE

    context.user_data["food_order"]["phone"] = phone

    # کیبورد انتخاب اتاق رزرو شده (برای سهولت کار اقامتگاه)
    room_buttons = []
    for key, room in config.ROOMS.items():
        room_buttons.append([InlineKeyboardButton(f"اتاق {room['title']}", callback_data=f"foodroom_{key}")])
    room_buttons.append([InlineKeyboardButton("مهمان بدون اقامت / سایر", callback_data="foodroom_other")])

    await update.message.reply_text(
        "ممنون! این غذا برای چه اتاقی در خانه برزک سرو شود؟\n"
        "(لطفاً اتاق رزرو شده خود را انتخاب کنید یا گزینه سایر را بزنید):",
        reply_markup=InlineKeyboardMarkup(room_buttons),
    )
    return FOOD_ASK_ROOM


async def food_select_room(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "foodroom_other":
        room_title = "مهمان آزاد / اقامت در سایر بخش‌ها"
    else:
        room_key = data.replace("foodroom_", "")
        room = config.ROOMS.get(room_key)
        room_title = room["title"] if room else "مشخص نشده"

    context.user_data["food_order"]["room_title"] = room_title
    today = jdatetime.date.today()

    await query.edit_message_text(f"🛏 اتاق انتخابی: {room_title}")
    await query.message.reply_text(
        "📅 این سفارش برای <b>کدام روز هفته و چه تاریخی</b> از اقامت شماست؟\n\n"
        "لطفاً تاریخ مورد نظر را از تقویم زیر انتخاب کنید (یا مثلاً ۱۴۰۵/۰۵/۱۰ تایپ کنید) 👇",
        parse_mode="HTML",
        reply_markup=build_calendar_keyboard(today.year, today.month, prefix="fcal_day_"),
    )
    return FOOD_ASK_DAY


async def food_calendar_navigate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    _, _, year_str, month_str = query.data.split("_")
    year, month = int(year_str), int(month_str)
    await query.edit_message_reply_markup(
        reply_markup=build_calendar_keyboard(year, month, prefix="fcal_day_")
    )
    return FOOD_ASK_DAY


async def food_calendar_select_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    _, _, year_str, month_str, day_str = query.data.split("_")
    year, month, day = int(year_str), int(month_str), int(day_str)

    jdate = jdatetime.date(year, month, day)
    weekday_name = PERSIAN_WEEKDAYS[jdate.weekday()]
    date_display = f"{year}/{month:02d}/{day:02d}"

    context.user_data["food_order"]["date"] = date_display
    context.user_data["food_order"]["weekday"] = weekday_name

    await query.edit_message_text(f"📅 تاریخ و روز انتخابی: {weekday_name} {date_display}")
    return await ask_meal_selection(query.message, context)


async def food_get_day_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    date_raw = update.message.text.strip()
    parsed_date = parse_checkin_date(date_raw)

    if parsed_date is None:
        await update.message.reply_text(
            "فرمت تاریخ نامعتبر است. لطفاً تاریخ شمسی را به صورت مثلاً ۱۴۰۵/۰۵/۱۰ وارد کنید:"
        )
        return FOOD_ASK_DAY

    today = jdatetime.date.today().togregorian()
    if parsed_date < today:
        await update.message.reply_text(
            "تاریخ سفارش نمی‌تواند در گذشته باشد. لطفاً تاریخ معتبر وارد کنید:"
        )
        return FOOD_ASK_DAY

    j_date = parse_jalali_date_details(date_raw)
    if j_date:
        weekday_name = PERSIAN_WEEKDAYS[j_date.weekday()]
        date_display = f"{j_date.year}/{j_date.month:02d}/{j_date.day:02d}"
    else:
        weekday_name = "مشخص‌شده"
        date_display = date_raw

    context.user_data["food_order"]["date"] = date_display
    context.user_data["food_order"]["weekday"] = weekday_name

    await update.message.reply_text(f"📅 تاریخ و روز انتخابی: {weekday_name} {date_display}")
    return await ask_meal_selection(update.message, context)


async def ask_meal_selection(message, context: ContextTypes.DEFAULT_TYPE) -> int:
    meals = getattr(config, "MEALS", {"lunch": {"title": "ناهار", "emoji": "☀️"}, "dinner": {"title": "شام", "emoji": "🌙"}})
    buttons = []
    for key, meal_info in meals.items():
        buttons.append([InlineKeyboardButton(f"{meal_info['emoji']} {meal_info['title']}", callback_data=f"meal_{key}")])
    buttons.append([InlineKeyboardButton("❌ انصراف", callback_data="food_cancel_order")])

    await message.reply_text(
        "🍽 لطفاً وعده غذایی مورد نظر را مشخص کنید:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return FOOD_ASK_MEAL


async def food_select_meal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "food_cancel_order":
        await query.edit_message_text("درخواست سفارش غذا لغو شد. برای بازگشت /start را بزنید.")
        context.user_data.clear()
        return ConversationHandler.END

    meal_key = data.replace("meal_", "")
    meals = getattr(config, "MEALS", {})
    meal_title = meals.get(meal_key, {}).get("title", meal_key)

    context.user_data["food_order"]["meal_key"] = meal_key
    context.user_data["food_order"]["meal_title"] = meal_title

    selected_items = context.user_data["food_order"]["items"]
    max_selections = getattr(config, "MAX_FOOD_SELECTIONS", 2)

    await query.edit_message_text(
        f"🕒 وعده انتخاب‌شده: <b>{meal_title}</b>\n\n"
        f"🍲 <b>انتخاب غذاها:</b>\n"
        f"هر مهمان می‌تواند حداکثر <b>{max_selections} نوع غذا</b> برای این وعده انتخاب کند.\n"
        "برای انتخاب یا تغییر تعداد هر غذا، روی دکمه مربوطه بزنید 👇",
        parse_mode="HTML",
        reply_markup=build_food_selection_keyboard(meal_key, selected_items),
    )
    return FOOD_SELECT_ITEM


async def food_item_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "food_cancel_order":
        await query.edit_message_text("درخواست سفارش غذا لغو شد.")
        context.user_data.clear()
        return ConversationHandler.END

    if data == "food_finalize":
        await query.edit_message_text("⏳ در حال ثبت و ارسال سفارش شما...")
        await finalize_food_order(query.message, context, is_query=True)
        return ConversationHandler.END

    food_key = data.replace("fsel_", "")
    foods = getattr(config, "FOODS", {})
    food = foods.get(food_key)
    if not food:
        await query.edit_message_text("این غذا یافت نشد.")
        return FOOD_SELECT_ITEM

    selected_items = context.user_data["food_order"]["items"]
    max_selections = getattr(config, "MAX_FOOD_SELECTIONS", 2)

    # اگر از قبل انتخاب نشده بود و سقف ۲ نوع پر بود
    if food_key not in selected_items and len(selected_items) >= max_selections:
        await query.answer(f"⚠️ شما حداکثر مجاز به انتخاب {max_selections} نوع غذا هستید.", show_alert=True)
        return FOOD_SELECT_ITEM

    context.user_data["current_editing_food"] = food_key

    # گزینه‌های تعداد پرس (۱ تا ۶ پرس یا امکان تایپ)
    portion_buttons = [
        [
            InlineKeyboardButton("۱ پرس", callback_data="portion_1"),
            InlineKeyboardButton("۲ پرس", callback_data="portion_2"),
            InlineKeyboardButton("۳ پرس", callback_data="portion_3"),
        ],
        [
            InlineKeyboardButton("۴ پرس", callback_data="portion_4"),
            InlineKeyboardButton("۵ پرس", callback_data="portion_5"),
            InlineKeyboardButton("۶ پرس", callback_data="portion_6"),
        ],
    ]
    if food_key in selected_items:
        portion_buttons.append([InlineKeyboardButton("🗑 حذف این غذا از سفارش", callback_data="portion_0")])
    portion_buttons.append([InlineKeyboardButton("⬅️ بازگشت به لیست غذاها", callback_data="portion_back")])

    await query.edit_message_text(
        f"🍲 غذای انتخابی: <b>{food['title']}</b>\n"
        f"💵 قیمت هر پرس: {food['price']}\n\n"
        "تعداد پرس مورد نظر را از دکمه‌های زیر انتخاب کنید (یا عدد دلخواه را تایپ کنید):",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(portion_buttons),
    )
    return FOOD_ASK_PORTIONS


async def food_portion_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data

    food_key = context.user_data.get("current_editing_food")
    food = getattr(config, "FOODS", {}).get(food_key)

    if data == "portion_back":
        return await show_food_selection_screen(query.message, context, edit_query=query)

    if data == "portion_0":
        # حذف غذا
        if food_key in context.user_data["food_order"]["items"]:
            del context.user_data["food_order"]["items"][food_key]
        return await show_food_selection_screen(query.message, context, edit_query=query)

    count_str = data.replace("portion_", "")
    portions = int(count_str)

    if food:
        context.user_data["food_order"]["items"][food_key] = {
            "title": food["title"],
            "price": food["price"],
            "portions": portions,
        }

    return await show_food_selection_screen(query.message, context, edit_query=query)


async def food_portion_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    raw_count = to_english_digits(update.message.text.strip())
    if not raw_count.isdigit() or int(raw_count) < 1:
        await update.message.reply_text("لطفاً تعداد پرس را به صورت عدد معتبر (مثلاً ۲) وارد کنید:")
        return FOOD_ASK_PORTIONS

    portions = int(raw_count)
    food_key = context.user_data.get("current_editing_food")
    food = getattr(config, "FOODS", {}).get(food_key)

    if food and food_key:
        context.user_data["food_order"]["items"][food_key] = {
            "title": food["title"],
            "price": food["price"],
            "portions": portions,
        }

    return await show_food_selection_screen(update.message, context, edit_query=None)


async def show_food_selection_screen(message, context: ContextTypes.DEFAULT_TYPE, edit_query=None) -> int:
    meal_key = context.user_data["food_order"]["meal_key"]
    meal_title = context.user_data["food_order"]["meal_title"]
    selected_items = context.user_data["food_order"]["items"]
    max_selections = getattr(config, "MAX_FOOD_SELECTIONS", 2)

    summary_lines = []
    if selected_items:
        summary_lines.append("📋 <b>غذاهای انتخاب‌شده تاکنون:</b>")
        for k, v in selected_items.items():
            summary_lines.append(f"• {v['title']}: <b>{v['portions']} پرس</b> ({v['price']})")
    else:
        summary_lines.append("<i>هنوز غذایی انتخاب نشده است.</i>")

    text = (
        f"🕒 وعده: <b>{meal_title}</b> | حداکثر <b>{max_selections} نوع غذا</b>\n\n"
        + "\n".join(summary_lines)
        + "\n\nبرای افزودن/ویرایش غذاها کلیک کنید یا در صورت اتمام، دکمه تایید نهایی را بزنید 👇"
    )

    markup = build_food_selection_keyboard(meal_key, selected_items)
    if edit_query:
        await edit_query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await message.reply_text(text, parse_mode="HTML", reply_markup=markup)

    return FOOD_SELECT_ITEM


async def finalize_food_order(message, context: ContextTypes.DEFAULT_TYPE, is_query: bool = False) -> None:
    order = context.user_data.get("food_order", {})
    name = order.get("name", "نامشخص")
    phone = order.get("phone", "نامشخص")
    room = order.get("room_title", "نامشخص")
    date = order.get("date", "نامشخص")
    weekday = order.get("weekday", "نامشخص")
    meal = order.get("meal_title", "نامشخص")
    items = order.get("items", {})

    items_text_list = []
    for k, v in items.items():
        items_text_list.append(f"  🍲 {v['title']}: <b>{v['portions']} پرس</b> ({v['price']})")
    items_formatted = "\n".join(items_text_list) if items_text_list else "موردی انتخاب نشده"

    user = message.from_user if is_query else message.from_user

    # پیام اطلاع‌رسانی برای مدیر اقامتگاه
    admin_text = (
        "🍽🔔 <b>درخواست سفارش غذای جدید</b>\n\n"
        f"👤 <b>مهمان:</b> {name}\n"
        f"📞 <b>شماره تماس:</b> {phone}\n"
        f"🛏 <b>اتاق:</b> {room}\n"
        f"📅 <b>روز و تاریخ سرو:</b> {weekday} {date}\n"
        f"🕒 <b>وعده:</b> {meal}\n\n"
        f"📋 <b>جزئیات سفارش غذا:</b>\n{items_formatted}\n\n"
        f"🆔 <b>آیدی تلگرام:</b> @{user.username if user and user.username else 'ندارد'}"
    )

    try:
        await context.bot.send_message(
            chat_id=config.ADMIN_CHAT_ID, text=admin_text, parse_mode="HTML"
        )
    except Exception as exc:
        logger.error("ارسال سفارش غذا به مدیر با خطا مواجه شد: %s", exc)

    confirm_text = (
        "✅ <b>درخواست غذای شما با موفقیت ثبت شد!</b>\n\n"
        f"👤 به نام: {name}\n"
        f"🛏 اتاق: {room}\n"
        f"📅 روز و تاریخ: {weekday} {date}\n"
        f"🕒 وعده: {meal}\n"
        f"📋 خوراک‌ها:\n{items_formatted}\n\n"
        "سفارش شما برای آشپزخانه اقامتگاه ارسال شد و در زمان مقرر تدارک دیده خواهد شد. نوش جان! 🌿\n\n"
        "برای بازگشت به منوی اصلی /start را بزنید."
    )

    await message.reply_text(
        confirm_text,
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data.clear()


# ---------------------------------------------------------------------------
# راه‌اندازی ربات
# ---------------------------------------------------------------------------
async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(
        [
            BotCommand("start", "🏡 نمایش منوی اصلی"),
            BotCommand("food", "🍽 منوی غذا و سفارش خوراک"),
            BotCommand("address", "📍 آدرس اقامتگاه"),
            BotCommand("contact", "📞 تماس با ما"),
            BotCommand("cancel", "❌ لغو درخواست در حال انجام"),
        ]
    )

    await application.bot.set_my_description(
        "🏡 به ربات رزرواسیون و سفارش غذای اقامتگاه بومگردی «خانه برزک» خوش آمدید!\n\n"
        "با این ربات می‌توانید اتاق‌های اقامتگاه را مشاهده کنید، درخواست رزرو دهید، منوی غذاهای محلی را ببینید و برای روزهای اقامت خود وعده ناهار یا شام سفارش دهید.\n\n"
        "برای شروع دکمه Start را لمس کنید 👇"
    )

    await application.bot.set_my_short_description(
        "ربات رزرو و سفارش غذای خانه برزک 🏡🍽"
    )


def main() -> None:
    token = os.environ.get("BOT_TOKEN", config.BOT_TOKEN)
    if token == "-1004485664573":
        raise SystemExit(
            "لطفاً ابتدا توکن ربات رو وارد کنید (در config.py یا متغیر محیطی BOT_TOKEN)."
        )

    application = Application.builder().token(token).post_init(post_init).build()

    # مکالمه رزرو اتاق
    booking_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(book_start, pattern=r"^book_")],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, book_get_name)],
            ASK_PHONE: [
                MessageHandler(
                    (filters.TEXT & ~filters.COMMAND) | filters.CONTACT, book_get_phone
                )
            ],
            ASK_CHECKIN: [
                CallbackQueryHandler(calendar_navigate, pattern=r"^cal_nav_"),
                CallbackQueryHandler(calendar_select_day, pattern=r"^cal_day_"),
                CallbackQueryHandler(calendar_ignore, pattern=r"^ignore$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, book_get_checkin),
            ],
            ASK_NIGHTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, book_get_nights)],
            ASK_GUESTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, book_get_guests)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # مکالمه سفارش غذا
    food_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(food_order_start, pattern=r"^food_order_start$"),
        ],
        states={
            FOOD_ASK_GUEST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, food_get_guest_name)],
            FOOD_ASK_PHONE: [
                MessageHandler((filters.TEXT & ~filters.COMMAND) | filters.CONTACT, food_get_phone)
            ],
            FOOD_ASK_ROOM: [
                CallbackQueryHandler(food_select_room, pattern=r"^foodroom_"),
            ],
            FOOD_ASK_DAY: [
                CallbackQueryHandler(food_calendar_navigate, pattern=r"^fcal_nav_"),
                CallbackQueryHandler(food_calendar_select_day, pattern=r"^fcal_day_"),
                CallbackQueryHandler(calendar_ignore, pattern=r"^ignore$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, food_get_day_text),
            ],
            FOOD_ASK_MEAL: [
                CallbackQueryHandler(food_select_meal, pattern=r"^(meal_|food_cancel_order)"),
            ],
            FOOD_SELECT_ITEM: [
                CallbackQueryHandler(food_item_toggle, pattern=r"^(fsel_|food_finalize|food_cancel_order)"),
            ],
            FOOD_ASK_PORTIONS: [
                CallbackQueryHandler(food_portion_callback, pattern=r"^portion_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, food_portion_text),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(food_item_toggle, pattern=r"^food_cancel_order$"),
        ],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("address", cmd_address))
    application.add_handler(CommandHandler("contact", cmd_contact))
    application.add_handler(CommandHandler("food", cmd_food))

    application.add_handler(booking_conv)
    application.add_handler(food_conv)

    application.add_handler(CallbackQueryHandler(menu_router))
    application.add_handler(CommandHandler("cancel", cancel_outside_conversation))
    application.add_handler(
        MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, receive_payment_receipt)
    )

    webhook_url = os.environ.get("WEBHOOK_URL") or os.environ.get("RENDER_EXTERNAL_URL")
    if webhook_url:
        port = int(os.environ.get("PORT", "10000"))
        url_path = token
        logger.info("ربات در حالت webhook روی پورت %s اجرا میشه...", port)
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=url_path,
            webhook_url=f"{webhook_url.rstrip('/')}/{url_path}",
        )
    else:
        logger.info("ربات در حالت polling (اجرای لوکال) در حال اجراست...")
        application.run_polling()


if __name__ == "__main__":
    main()
'''

with open("repo_files/bot.py", "w", encoding="utf-8") as f:
    f.write(updated_bot_code)

print("Updated repo_files/bot.py successfully")
