# -*- coding: utf-8 -*-
"""
ربات رزرو اقامتگاه بومگردی «خانه برزک»
----------------------------------------
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
# وضعیت‌های مکالمه‌ی رزرو (پشتیبانی از رزرو چند اتاقه، تفکیک سنی و یادداشت‌های مهمان)
# ---------------------------------------------------------------------------
(
    ASK_NAME,
    ASK_PHONE,
    ASK_CHECKIN,
    ASK_NIGHTS,
    ASK_ROOM_SELECT,
    ASK_ROOM_ADULTS,
    ASK_ROOM_CHILDREN_5_12,
    ASK_ROOM_CHILDREN_UNDER_5,
    ASK_ROOM_MORE_OR_CONFIRM,
    ASK_SPECIAL_NOTES,
) = range(10)


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


def to_persian_digits(num_or_str) -> str:
    """تبدیل اعداد انگلیسی به ارقام فارسی."""
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    s = str(num_or_str)
    return "".join(persian_digits[int(ch)] if ch.isdigit() else ch for ch in s)


def format_toman(amount: int) -> str:
    """فرمت‌بندی مبلغ به تومان با جداکننده سه‌رقمی و اعداد فارسی."""
    formatted = f"{int(amount):,}".replace(",", "،")
    return f"{to_persian_digits(formatted)} تومان"


WEEKDAY_LABELS_FA = ["ش", "ی", "د", "س", "چ", "پ", "ج"]  # شنبه تا جمعه


def jalali_days_in_month(year: int, month: int) -> int:
    if month <= 6:
        return 31
    elif month <= 11:
        return 30
    else:
        return 30 if jdatetime.date(year, 1, 1).isleap() else 29


def build_calendar_keyboard(year: int, month: int, prefix: str = 'cal_day_') -> InlineKeyboardMarkup:
    today = jdatetime.date.today()
    rows = []

    nav_prefix = "cal_nav_" if prefix == "cal_day_" else "fcal_nav_"
    # هدر: ماه/سال + دکمه‌های قبلی و بعدی
    prev_month, prev_year = (month - 1, year) if month > 1 else (12, year - 1)
    next_month, next_year = (month + 1, year) if month < 12 else (1, year + 1)

    # اگه ماه قبلی کاملاً در گذشته باشه، دکمه‌ی قبلی غیرفعال (خالی) میشه
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


# ---------------------------------------------------------------------------
# وضعیت‌های مکالمه‌ی سفارش غذا (ناهار / شام و یادداشت‌های مهمان)
# ---------------------------------------------------------------------------
(
    FOOD_ASK_GUEST_NAME,
    FOOD_ASK_PHONE,
    FOOD_ASK_ROOM,
    FOOD_ASK_DAY,
    FOOD_ASK_MEAL,
    FOOD_SELECT_ITEM,
    FOOD_ASK_PORTIONS,
    FOOD_ASK_NOTES,
) = range(20, 28)

PERSIAN_WEEKDAYS = ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]

def parse_jalali_date_details(raw_text: str):
    """پارس تاریخ شمسی و بازگرداندن jdatetime.date جهت استخراج روز هفته"""
    text = to_english_digits(raw_text.strip())
    parts = text.replace("-", "/").split("/")
    if len(parts) != 3:
        return None
    try:
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        return jdatetime.date(y, m, d)
    except Exception:
        return None
# ---------------------------------------------------------------------------
# کیبوردهای کمکی
# ---------------------------------------------------------------------------
def main_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("🛏 اتاق‌ها و رزرو اقامت", callback_data="menu_rooms")],
        [InlineKeyboardButton("🍽 منوی غذا و سفارش خوراک", callback_data="menu_food")],
        [InlineKeyboardButton("📜 اطلاعاتی درباره اقامتگاه", callback_data="menu_rules")],
        [InlineKeyboardButton("📍 آدرس و لوکیشن", callback_data="menu_address")],
        [InlineKeyboardButton("📞 تماس با ما", callback_data="menu_contact")],
        [InlineKeyboardButton("🌐 سایت و شبکه‌های اجتماعی", callback_data="menu_social")],
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
    buttons.append([InlineKeyboardButton("✨ رزرو اقامتگاه (تک یا چند اتاقه)", callback_data="book_start_direct")])
    buttons.append([InlineKeyboardButton("⬅️ بازگشت به منو", callback_data="back_main")])
    return InlineKeyboardMarkup(buttons)


def room_detail_keyboard(room_key: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("✅ درخواست رزرو این اتاق", callback_data=f"book_{room_key}")],
        [InlineKeyboardButton("⬅️ بازگشت به لیست اتاق‌ها", callback_data="menu_rooms")],
    ]
    return InlineKeyboardMarkup(buttons)


def booking_rooms_selection_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for key, room in config.ROOMS.items():
        price_display = room.get("price", "").split("/")[0].strip()
        buttons.append(
            [InlineKeyboardButton(f"🛏 {room['title']} ({price_display})", callback_data=f"bselectroom_{key}")]
        )
    buttons.append([InlineKeyboardButton("❌ لغو رزرو", callback_data="b_cancel_booking")])
    return InlineKeyboardMarkup(buttons)


def adults_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("۱ نفر بزرگسال", callback_data="badults_1"),
            InlineKeyboardButton("۲ نفر بزرگسال", callback_data="badults_2"),
        ],
        [
            InlineKeyboardButton("۳ نفر بزرگسال", callback_data="badults_3"),
            InlineKeyboardButton("۴ نفر بزرگسال", callback_data="badults_4"),
        ],
        [
            InlineKeyboardButton("۵ نفر بزرگسال", callback_data="badults_5"),
            InlineKeyboardButton("۶ نفر بزرگسال", callback_data="badults_6"),
        ],
        [InlineKeyboardButton("❌ انصراف و لغو", callback_data="b_cancel_booking")],
    ])


def children_5_12_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("۰ (بدون کودک)", callback_data="bchild512_0"),
            InlineKeyboardButton("۱ کودک (نیم‌بها)", callback_data="bchild512_1"),
        ],
        [
            InlineKeyboardButton("۲ کودک (نیم‌بها)", callback_data="bchild512_2"),
            InlineKeyboardButton("۳ کودک (نیم‌بها)", callback_data="bchild512_3"),
        ],
        [InlineKeyboardButton("❌ انصراف و لغو", callback_data="b_cancel_booking")],
    ])


def children_under_5_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("۰ (بدون کودک)", callback_data="bchildu5_0"),
            InlineKeyboardButton("۱ کودک (رایگان)", callback_data="bchildu5_1"),
        ],
        [
            InlineKeyboardButton("۲ کودک (رایگان)", callback_data="bchildu5_2"),
            InlineKeyboardButton("۳ کودک (رایگان)", callback_data="bchildu5_3"),
        ],
        [InlineKeyboardButton("❌ انصراف و لغو", callback_data="b_cancel_booking")],
    ])


def phone_request_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📱 ارسال شماره تماس من", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )



def food_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("🍲 ثبت درخواست غذا (ناهار / شام)", callback_data="food_order_start")],
        [InlineKeyboardButton("📋 مشاهده لیست غذاها و قیمت", callback_data="food_list_details")],
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

def build_food_selection_keyboard(selected_meal: str, selected_foods: dict) -> InlineKeyboardMarkup:
    foods = getattr(config, "FOODS", {})
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
        action_row.append(InlineKeyboardButton("✅ تایید و ثبت سفارش", callback_data="food_finalize"))
    action_row.append(InlineKeyboardButton("❌ انصراف", callback_data="food_cancel_order"))
    buttons.append(action_row)
    return InlineKeyboardMarkup(buttons)
# ---------------------------------------------------------------------------
# دستور /start
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


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "درخواست رزرو لغو شد. هر وقت خواستی می‌تونی دوباره از /start شروع کنی.",
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_outside_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # این هندلر وقتی اجرا میشه که کاربر /cancel رو بزنه ولی هیچ فرآیند رزروی فعال نباشه
    await update.message.reply_text(
        "در حال حاضر هیچ درخواست رزرویی در جریان نیست که لغو بشه.\n"
        "برای شروع، /start رو بزنید."
    )


async def receive_payment_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """کاربر می‌تونه هر زمان (حتی خارج از فرآیند رزرو) عکس فیش پرداخت رو بفرسته.
    این عکس مستقیم برای گروه/چت مدیریت فوروارد میشه."""
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



async def cmd_food(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        config.FOOD_MENU_TEXT,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=food_menu_keyboard(),
    )
# ---------------------------------------------------------------------------
# مدیریت دکمه‌های منوی اصلی (غیر از رزرو)
# ---------------------------------------------------------------------------
async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_main":
        # اگه پیام فعلی عکس داشته باشه (مثل پیام بخش «سفر سبز»)، نمیشه با
        # edit_message_text ویرایشش کرد؛ پس پیام قبلی رو حذف و پیام جدید می‌فرستیم.
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
        social_keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🌐 وب‌سایت", url=getattr(config, "WEBSITE_URL", "https://barzokhouse.com")),
                    InlineKeyboardButton("✈️ تلگرام", url=getattr(config, "TELEGRAM_URL", "https://t.me/barzokhouselodge")),
                    InlineKeyboardButton("📸 اینستاگرام", url=getattr(config, "INSTAGRAM_URL", "https://instagram.com/barzokhouse")),
                ],
                [InlineKeyboardButton("⬅️ بازگشت به منو", callback_data="back_main")],
            ]
        )
        await query.edit_message_text(
            config.SOCIAL_TEXT, reply_markup=social_keyboard
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
        text_lines = ["🍽 <b>لیست خوراک‌ها و غذاهای محلی خانه برزک:</b>\n"]
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
        # این بخش چند پیام جداگانه می‌فرسته (متن + متن + عکس)، پس پیام قبلی رو حذف می‌کنیم
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
        # اگه از پیام جزئیات یه اتاق (که عکس داره) اومده باشیم، نمیشه با
        # edit_message_text ویرایشش کرد؛ پس پیام قبلی رو حذف و پیام جدید می‌فرستیم.
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

        # پیام قبلی (لیست اتاق‌ها) رو حذف می‌کنیم و عکس اتاق رو با کپشن می‌فرستیم
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
            # اگر عکس پیدا نشد فقط متن ارسال میشه
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=caption,
                reply_markup=room_detail_keyboard(room_key),
            )
        return


# ---------------------------------------------------------------------------
# مکالمه‌ی رزرو (پشتیبانی از چندین اتاق، تفکیک رده‌های سنی و برآورد هزینه)
# ---------------------------------------------------------------------------
async def book_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    room_key = query.data.replace("book_", "")
    
    context.user_data["booking"] = {
        "rooms": [],
        "current_room_key": room_key if room_key in config.ROOMS else None,
        "name": "",
        "phone": "",
        "checkin": "",
        "nights": 1,
    }

    if room_key in config.ROOMS:
        room = config.ROOMS[room_key]
        intro = f"شما در حال رزرو «{room['title']}» هستید.\n(در ادامه می‌توانید در صورت نیاز اتاق‌های دیگری نیز اضافه نمایید)"
    else:
        intro = "در این بخش می‌توانید یک یا چند اتاق برای اقامت در خانه برزک رزرو فرمایید."

    await query.message.reply_text(
        f"🏡 <b>درخواست رزرو اقامتگاه خانه برزک</b>\n\n"
        f"{intro}\n\n"
        "لطفاً ابتدا نام و نام خانوادگی خود را وارد کنید:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ASK_NAME


async def book_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    if len(name) < 3:
        await update.message.reply_text("لطفاً یک نام و نام خانوادگی معتبر وارد فرمایید:")
        return ASK_NAME

    if "booking" not in context.user_data:
        context.user_data["booking"] = {"rooms": [], "current_room_key": None}
    context.user_data["booking"]["name"] = name

    await update.message.reply_text(
        "سپاس! حالا لطفاً شماره تماس خود را ارسال کرده یا تایپ کنید:",
        reply_markup=phone_request_keyboard(),
    )
    return ASK_PHONE


async def book_get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text.strip()

    if len(phone) < 10:
        await update.message.reply_text("لطفاً یک شماره تماس معتبر (حداقل ۱۰ رقم) وارد نمایید:")
        return ASK_PHONE

    if "booking" not in context.user_data:
        context.user_data["booking"] = {"rooms": [], "current_room_key": None}
    context.user_data["booking"]["phone"] = phone
    today = jdatetime.date.today()
    await update.message.reply_text(
        "ممنون! حالا لطفاً تاریخ ورود را از تقویم زیر انتخاب کنید 👇\n"
        "(یا می‌توانید به فرمت شمسی تایپ نمایید، مثلاً ۱۴۰۵/۰۵/۱۰):",
        reply_markup=ReplyKeyboardRemove(),
    )
    await update.message.reply_text(
        "📅 انتخاب تاریخ ورود:",
        reply_markup=build_calendar_keyboard(today.year, today.month),
    )
    return ASK_CHECKIN


async def calendar_ignore(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # فقط برای دکمه‌های غیرفعال/تزئینی تقویم (بدون هیچ اکشنی)
    await update.callback_query.answer()


async def calendar_navigate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    _, _, year_str, month_str = query.data.split("_")
    year, month = int(year_str), int(month_str)
    await query.edit_message_reply_markup(reply_markup=build_calendar_keyboard(year, month))
    return ASK_CHECKIN


async def calendar_select_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    _, _, year_str, month_str, day_str = query.data.split("_")
    year, month, day = int(year_str), int(month_str), int(day_str)

    checkin_text = f"{year}/{month:02d}/{day:02d}"
    if "booking" not in context.user_data:
        context.user_data["booking"] = {"rooms": [], "current_room_key": None}
    context.user_data["booking"]["checkin"] = checkin_text

    await query.edit_message_text(f"📅 تاریخ ورود انتخاب‌شده: {to_persian_digits(checkin_text)}")
    await query.message.reply_text("🌙 تعداد شب‌های اقامت را وارد نمایید (مثلاً 1 یا 2):")
    return ASK_NIGHTS


async def book_get_checkin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    checkin_date_raw = update.message.text.strip()
    parsed_date = parse_checkin_date(checkin_date_raw)

    if parsed_date is None:
        await update.message.reply_text(
            "فرمت تاریخ نامعتبر است. لطفاً به این شکل وارد کنید (مثلاً ۱۴۰۵/۰۵/۱۰):"
        )
        return ASK_CHECKIN

    today = jdatetime.date.today().togregorian()
    if parsed_date < today:
        await update.message.reply_text(
            "تاریخ ورود نمی‌تواند قبل از امروز باشد. لطفاً یک تاریخ درست وارد کنید (مثلاً ۱۴۰۵/۰۵/۱۰):"
        )
        return ASK_CHECKIN

    if "booking" not in context.user_data:
        context.user_data["booking"] = {"rooms": [], "current_room_key": None}
    context.user_data["booking"]["checkin"] = checkin_date_raw
    await update.message.reply_text("🌙 تعداد شب‌های اقامت را وارد نمایید (مثلاً 1 یا 2):")
    return ASK_NIGHTS


async def ask_room_adults_prompt(target_message, context: ContextTypes.DEFAULT_TYPE, room_key: str) -> int:
    room = config.ROOMS.get(room_key)
    if not room:
        await target_message.reply_text(
            "لطفاً اتاق مورد نظر خود را برای رزرو انتخاب نمایید:",
            reply_markup=booking_rooms_selection_keyboard(),
        )
        return ASK_ROOM_SELECT

    text = (
        f"🛏 <b>تنظیم نفرات برای {room['title']}</b>\n"
        f"💰 <i>نرخ: {room['price']}</i>\n\n"
        f"لطفاً تعداد نفرات <b>بزرگسال (۱۲ سال به بالا)</b> را برای این اتاق مشخص کنید:\n"
        f"(می‌توانید از گزینه‌های زیر انتخاب کنید یا عدد را تایپ فرمایید)"
    )
    await target_message.reply_text(text, parse_mode="HTML", reply_markup=adults_keyboard())
    return ASK_ROOM_ADULTS


async def book_get_nights(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    nights_raw = to_english_digits(update.message.text.strip())
    if not nights_raw.isdigit() or int(nights_raw) < 1:
        await update.message.reply_text("لطفاً تعداد شب را به‌صورت عدد معتبر وارد فرمایید (مثلاً 1 یا 2):")
        return ASK_NIGHTS

    booking = context.user_data.get("booking", {})
    booking["nights"] = int(nights_raw)
    current_room = booking.get("current_room_key")

    if current_room and current_room in config.ROOMS:
        return await ask_room_adults_prompt(update.message, context, current_room)
    else:
        await update.message.reply_text(
            "🛏 لطفاً اتاق مورد نظر خود را برای رزرو انتخاب فرمایید:\n"
            "<i>(در مراحل بعد می‌توانید اتاق‌های دیگری نیز به این درخواست اضافه کنید)</i>",
            parse_mode="HTML",
            reply_markup=booking_rooms_selection_keyboard(),
        )
        return ASK_ROOM_SELECT


async def book_select_room(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    room_key = query.data.replace("bselectroom_", "")
    
    if "booking" not in context.user_data:
        context.user_data["booking"] = {"rooms": [], "nights": 1}
    context.user_data["booking"]["current_room_key"] = room_key
    return await ask_room_adults_prompt(query.message, context, room_key)


async def process_adults_count(target_message, context: ContextTypes.DEFAULT_TYPE, adults_count: int) -> int:
    booking = context.user_data.get("booking", {})
    room_key = booking.get("current_room_key")
    room_title = config.ROOMS.get(room_key, {}).get("title", "این اتاق")
    
    context.user_data["current_adults"] = adults_count

    text = (
        f"👶 <b>تعداد کودکان بین ۵ تا ۱۲ سال برای «{room_title}»</b>:\n\n"
        f"💡 <b>قوانین اقامتگاه:</b> هزینه اقامت کودکان ۵ تا ۱۲ سال به‌صورت <b>نیم‌بها (۵۰٪)</b> محاسبه می‌شود.\n\n"
        f"لطفاً تعداد کودکان ۵ تا ۱۲ سال این اتاق را مشخص کنید:"
    )
    await target_message.reply_text(text, parse_mode="HTML", reply_markup=children_5_12_keyboard())
    return ASK_ROOM_CHILDREN_5_12


async def book_adults_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    count_str = query.data.replace("badults_", "")
    return await process_adults_count(query.message, context, int(count_str))


async def book_get_adults_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    val_str = to_english_digits(update.message.text.strip())
    if not val_str.isdigit() or int(val_str) < 1:
        await update.message.reply_text("لطفاً حداقل ۱ نفر بزرگسال برای این اتاق وارد نمایید (مثلاً 2):")
        return ASK_ROOM_ADULTS
    return await process_adults_count(update.message, context, int(val_str))


async def process_children_5_12_count(target_message, context: ContextTypes.DEFAULT_TYPE, count: int) -> int:
    booking = context.user_data.get("booking", {})
    room_key = booking.get("current_room_key")
    room_title = config.ROOMS.get(room_key, {}).get("title", "این اتاق")
    
    context.user_data["current_children_5_12"] = count

    text = (
        f"🍼 <b>تعداد کودکان زیر ۵ سال برای «{room_title}»</b>:\n\n"
        f"💡 <b>قوانین اقامتگاه:</b> اقامت کودکان زیر ۵ سال <b>کاملاً رایگان (۰٪)</b> است.\n\n"
        f"لطفاً تعداد کودکان زیر ۵ سال این اتاق را مشخص کنید:"
    )
    await target_message.reply_text(text, parse_mode="HTML", reply_markup=children_under_5_keyboard())
    return ASK_ROOM_CHILDREN_UNDER_5


async def book_child_5_12_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    count_str = query.data.replace("bchild512_", "")
    return await process_children_5_12_count(query.message, context, int(count_str))


async def book_get_child_5_12_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    val_str = to_english_digits(update.message.text.strip())
    if not val_str.isdigit() or int(val_str) < 0:
        await update.message.reply_text("لطفاً تعداد کودکان ۵ تا ۱۲ سال را به‌صورت عدد وارد فرمایید (مثلاً 0 یا 1):")
        return ASK_ROOM_CHILDREN_5_12
    return await process_children_5_12_count(update.message, context, int(val_str))


async def process_children_under_5_count(target_message, context: ContextTypes.DEFAULT_TYPE, count: int) -> int:
    booking = context.user_data.get("booking", {})
    nights = int(booking.get("nights", 1))
    room_key = booking.get("current_room_key")
    room = config.ROOMS.get(room_key, {})
    price_per_person = room.get("price_per_person", 1300000)
    
    adults = context.user_data.get("current_adults", 1)
    c_5_12 = context.user_data.get("current_children_5_12", 0)
    c_u5 = count

    # محاسبه هزینه این اتاق
    # بزرگسال: شب * بزرگسال * قیمت نفرشب
    # کودک ۵-۱۲: شب * کودک * (۵۰٪ قیمت نفرشب)
    # کودک زیر ۵: رایگان
    cost_adults = nights * adults * price_per_person
    cost_5_12 = nights * c_5_12 * int(price_per_person * getattr(config, "CHILD_5_12_DISCOUNT_FACTOR", 0.5))
    cost_u5 = 0
    room_cost = cost_adults + cost_5_12

    booking["rooms"].append({
        "room_key": room_key,
        "title": room.get("title", "اتاق"),
        "price_per_person": price_per_person,
        "adults": adults,
        "children_5_12": c_5_12,
        "children_under_5": c_u5,
        "room_cost": room_cost,
    })
    booking["current_room_key"] = None

    count_rooms = len(booking["rooms"])
    text = (
        f"✅ <b>{room.get('title')}</b> به لیست اقامت شما افزوده شد.\n\n"
        f"📊 <b>مشخصات ثبت‌شده این اتاق:</b>\n"
        f"• بزرگسال: {to_persian_digits(adults)} نفر\n"
        + (f"• کودک ۵ تا ۱۲ سال: {to_persian_digits(c_5_12)} نفر (نیم‌بها)\n" if c_5_12 > 0 else "")
        + (f"• کودک زیر ۵ سال: {to_persian_digits(c_u5)} نفر (رایگان)\n" if c_u5 > 0 else "")
        + f"• برآورد هزینه این اتاق ({to_persian_digits(nights)} شب): <b>{format_toman(room_cost)}</b>\n\n"
        f"تاکنون <b>{to_persian_digits(count_rooms)} اتاق</b> در درخواست رزرو شما قرار دارد.\n\n"
        "آیا مایل به <b>افزودن اتاق دیگری</b> هستید، یا می‌خواهید <b>خلاصه و برآورد اولیه کل هزینه</b> را مشاهده نمایید؟"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ افزودن یک اتاق دیگر", callback_data="b_add_room")],
        [InlineKeyboardButton("📋 مشاهده خلاصه رزرو و فاکتور نهایی", callback_data="b_view_summary")],
        [InlineKeyboardButton("❌ انصراف از رزرو", callback_data="b_cancel_booking")],
    ])
    await target_message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)
    return ASK_ROOM_MORE_OR_CONFIRM


async def book_child_u5_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    count_str = query.data.replace("bchildu5_", "")
    return await process_children_under_5_count(query.message, context, int(count_str))


async def book_get_child_u5_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    val_str = to_english_digits(update.message.text.strip())
    if not val_str.isdigit() or int(val_str) < 0:
        await update.message.reply_text("لطفاً تعداد کودکان زیر ۵ سال را به‌صورت عدد وارد فرمایید (مثلاً 0 یا 1):")
        return ASK_ROOM_CHILDREN_UNDER_5
    return await process_children_under_5_count(update.message, context, int(val_str))


async def book_add_room_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    text = (
        "🛏 <b>انتخاب اتاق جدید</b>:\n"
        "لطفاً اتاق مورد نظر خود را برای اضافه شدن به لیست رزرو انتخاب فرمایید:"
    )
    await query.message.reply_text(text, parse_mode="HTML", reply_markup=booking_rooms_selection_keyboard())
    return ASK_ROOM_SELECT


def build_booking_summary_text(booking: dict) -> tuple[str, int]:
    rooms = booking.get("rooms", [])
    nights = booking.get("nights", 1)
    notes = booking.get("notes", "").strip()
    total_cost = sum(r["room_cost"] for r in rooms)
    total_adults = sum(r["adults"] for r in rooms)
    total_5_12 = sum(r["children_5_12"] for r in rooms)
    total_u5 = sum(r["children_under_5"] for r in rooms)

    rooms_text = ""
    for idx, r in enumerate(rooms, 1):
        rooms_text += f"\n{to_persian_digits(idx)}. <b>{r['title']}</b>\n"
        rooms_text += f"   • بزرگسال: {to_persian_digits(r['adults'])} نفر\n"
        if r["children_5_12"] > 0:
            rooms_text += f"   • کودک ۵ تا ۱۲ سال: {to_persian_digits(r['children_5_12'])} نفر (نیم‌بها)\n"
        if r["children_under_5"] > 0:
            rooms_text += f"   • کودک زیر ۵ سال: {to_persian_digits(r['children_under_5'])} نفر (رایگان)\n"
        rooms_text += f"   • برآورد هزینه این اتاق: {format_toman(r['room_cost'])}\n"

    notes_section = f"\n📝 <b>توضیحات و ملاحظات ثبت‌شده:</b>\n{notes}\n" if notes else "\n📝 <b>توضیحات و ملاحظات خاص:</b> <i>ثبت نشده (می‌توانید با دکمه زیر بنویسید)</i>\n"

    summary_text = (
        "📋 <b>پیش‌فاکتور و خلاصه درخواست رزرو اقامتگاه خانه برزک</b>\n\n"
        f"👤 <b>نام مهمان:</b> {booking.get('name')}\n"
        f"📞 <b>شماره تماس:</b> {booking.get('phone')}\n"
        f"📅 <b>تاریخ ورود:</b> {to_persian_digits(booking.get('checkin'))}\n"
        f"🌙 <b>مدت اقامت:</b> {to_persian_digits(nights)} شب\n"
        f"👥 <b>مجموع نفرات:</b> {to_persian_digits(total_adults)} بزرگسال"
        + (f" + {to_persian_digits(total_5_12)} کودک ۵-۱۲ سال" if total_5_12 > 0 else "")
        + (f" + {to_persian_digits(total_u5)} کودک زیر ۵ سال" if total_u5 > 0 else "")
        + f"\n\n<b>🛏 جزئیات اتاق‌ها ({to_persian_digits(len(rooms))} اتاق):</b>"
        f"{rooms_text}\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        f"💰 <b>مجموع برآورد اولیه هزینه: {format_toman(total_cost)}</b>\n"
        "<i>(شامل اقامت و صبحانه محلی برزک برای کل شب‌ها)</i>\n"
        + notes_section +
        "\n✨ <b>قوانین محاسبه هزینه:</b>\n"
        "• هزینه کودکان بین ۵ تا ۱۲ سال <b>نیم‌بها</b> محاسبه شده است.\n"
        "• اقامت کودکان زیر ۵ سال <b>رایگان</b> می‌باشد.\n\n"
        "در صورت تایید، دکمه «تایید نهایی و ارسال به مدیر» را فشار دهید."
    )
    return summary_text, total_cost


async def book_show_summary_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    booking = context.user_data.get("booking", {})
    if not booking.get("rooms"):
        await query.message.reply_text("هیچ اتاقی انتخاب نشده است. لطفاً حداقل یک اتاق انتخاب نمایید:")
        return ASK_ROOM_SELECT

    summary_text, _ = build_booking_summary_text(booking)
    has_notes = bool(booking.get("notes", "").strip())
    notes_button_text = "✏️ ویرایش توضیحات و ملاحظات" if has_notes else "📝 نوشتن توضیحات یا ملاحظه خاص (غذایی، دسترسی و...)"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تایید نهایی و ارسال به مدیر", callback_data="b_confirm_final")],
        [InlineKeyboardButton(notes_button_text, callback_data="b_add_notes")],
        [InlineKeyboardButton("➕ افزودن یک اتاق دیگر", callback_data="b_add_room")],
        [InlineKeyboardButton("❌ انصراف و لغو رزرو", callback_data="b_cancel_booking")],
    ])
    await query.message.reply_text(summary_text, parse_mode="HTML", reply_markup=keyboard)
    return ASK_ROOM_MORE_OR_CONFIRM


async def book_ask_notes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    booking = context.user_data.get("booking", {})
    current_notes = booking.get("notes", "").strip()
    text = (
        "📝 <b>توضیحات و ملاحظات خاص اقامت در خانه برزک</b>\n\n"
        "اگر <b>ملاحظه غذایی خاص</b> (مانند گیاه‌خواری، رژیم کم‌نمک یا دیابت، حساسیت به مواد غذایی)، "
        "نکته‌ای در رابطه با <b>دسترس‌پذیری</b> (سالمند، نوزاد، عدم امکان بالا رفتن از پله، نیاز به طبقه همکف) "
        "یا هر نکته و درخواستی دارید، لطفاً همینجا پیام داده و ارسال کنید:\n\n"
        + (f"<i>(توضیحات فعلی ثبت‌شده: {current_notes})</i>\n\n" if current_notes else "")
        + "یا در صورت عدم نیاز به توضیحات، دکمه زیر را فشار دهید 👇"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("بدون توضیحات اضافی ⏭", callback_data="b_skip_notes")],
        [InlineKeyboardButton("⬅️ بازگشت به پیش‌فاکتور", callback_data="b_view_summary")],
    ])
    await query.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)
    return ASK_SPECIAL_NOTES


async def book_get_notes_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    notes = update.message.text.strip()
    booking = context.user_data.get("booking", {})
    booking["notes"] = notes
    await update.message.reply_text("✅ توضیحات و ملاحظات شما با موفقیت ثبت شد.")
    summary_text, _ = build_booking_summary_text(booking)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تایید نهایی و ارسال به مدیر", callback_data="b_confirm_final")],
        [InlineKeyboardButton("✏️ ویرایش مجدد توضیحات", callback_data="b_add_notes")],
        [InlineKeyboardButton("➕ افزودن یک اتاق دیگر", callback_data="b_add_room")],
        [InlineKeyboardButton("❌ انصراف و لغو رزرو", callback_data="b_cancel_booking")],
    ])
    await update.message.reply_text(summary_text, parse_mode="HTML", reply_markup=keyboard)
    return ASK_ROOM_MORE_OR_CONFIRM


async def book_skip_notes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    booking = context.user_data.get("booking", {})
    if "notes" not in booking:
        booking["notes"] = ""
    summary_text, _ = build_booking_summary_text(booking)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تایید نهایی و ارسال به مدیر", callback_data="b_confirm_final")],
        [InlineKeyboardButton("📝 نوشتن توضیحات یا ملاحظه خاص", callback_data="b_add_notes")],
        [InlineKeyboardButton("➕ افزودن یک اتاق دیگر", callback_data="b_add_room")],
        [InlineKeyboardButton("❌ انصراف و لغو رزرو", callback_data="b_cancel_booking")],
    ])
    await query.message.reply_text(summary_text, parse_mode="HTML", reply_markup=keyboard)
    return ASK_ROOM_MORE_OR_CONFIRM


async def book_skip_notes_finalize_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    booking = context.user_data.get("booking", {})
    booking["notes"] = ""
    await finalize_booking(update, context)
    return ConversationHandler.END


async def book_confirm_final_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    booking = context.user_data.get("booking", {})
    # اگر هنوز در مورد توضیحات سوال پرسیده نشده، به مهمان اطلاع می‌دهیم:
    if "notes" not in booking:
        text = (
            "📝 <b>آیا مایلید توضیحات یا ملاحظه خاصی به اقامتگاه بگویید؟</b>\n\n"
            "قبل از ارسال نهایی، اگر <b>ملاحظه غذایی خاص</b> (حساسیت، رژیم غذایی)، "
            "نکته‌ای در خصوص <b>دسترس‌پذیری</b> (سالمند، نوزاد، عدم امکان بالا رفتن از پله) "
            "یا هر نکته مهمی هست که مایلید به اقامتگاه اطلاع دهید، می‌توانید بنویسید.\n\n"
            "در غیر این صورت، با زدن دکمه «ارسال نهایی بدون توضیحات»، رزرو بلافاصله ثبت می‌شود 👇"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 ارسال نهایی بدون توضیحات اضافی", callback_data="b_skip_notes_finalize")],
            [InlineKeyboardButton("✍️ یادداشت دارم (تایپ می‌کنم)", callback_data="b_add_notes")],
            [InlineKeyboardButton("⬅️ بازگشت به خلاصه رزرو", callback_data="b_view_summary")],
        ])
        await query.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)
        return ASK_SPECIAL_NOTES

    await finalize_booking(update, context)
    return ConversationHandler.END


async def book_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "❌ فرآیند رزرو لغو شد.\nبرای شروع مجدد یا مشاهده بخش‌های دیگر، /start را ارسال کنید.",
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def finalize_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    booking = context.user_data.get("booking", {})
    rooms = booking.get("rooms", [])
    nights = booking.get("nights", 1)
    notes = booking.get("notes", "").strip()

    summary_text, total_cost = build_booking_summary_text(booking)

    # پیام برای مدیر اقامتگاه
    admin_text = (
        "⭕🔔 <b>درخواست رزرو جدید اقامتگاه</b>\n\n"
        f"👤 <b>نام مهمان:</b> {booking.get('name')}\n"
        f"📞 <b>شماره تماس:</b> {booking.get('phone')}\n"
        f"📅 <b>تاریخ ورود:</b> {to_persian_digits(booking.get('checkin'))}\n"
        f"🌙 <b>مدت اقامت:</b> {to_persian_digits(nights)} شب\n"
        f"🆔 <b>آیدی تلگرام:</b> @{user.username if user.username else 'ندارد'}\n\n"
        f"🛏 <b>اتاق‌های درخواستی ({to_persian_digits(len(rooms))} اتاق):</b>\n"
    )
    for idx, r in enumerate(rooms, 1):
        admin_text += (
            f"{to_persian_digits(idx)}. <b>{r['title']}</b>: {to_persian_digits(r['adults'])} بزرگسال"
            + (f" | {to_persian_digits(r['children_5_12'])} کودک ۵-۱۲" if r["children_5_12"] > 0 else "")
            + (f" | {to_persian_digits(r['children_under_5'])} کودک زیر ۵" if r["children_under_5"] > 0 else "")
            + f" | برآورد: {format_toman(r['room_cost'])}\n"
        )
    admin_text += (
        "➖➖➖➖➖➖➖➖➖➖\n"
        f"💰 <b>برآورد کل هزینه: {format_toman(total_cost)}</b>\n"
        f"📝 <b>توضیحات و ملاحظات مهمان:</b>\n{notes if notes else 'ندارد'}\n"
    )

    try:
        await context.bot.send_message(
            chat_id=config.ADMIN_CHAT_ID, text=admin_text, parse_mode="HTML"
        )
    except Exception as exc:
        logger.error("ارسال پیام به مدیر با خطا مواجه شد: %s", exc)

    chat_id = update.effective_chat.id
    confirmation_text = (
        "🏡 <b>درخواست رزرو شما با موفقیت ثبت شد!</b>\n\n"
        "🌿 <b>خانواده اقامتگاه بوم‌گردی خانه برزک، با تمام وجود و از صمیم قلب منتظر دیدارتون تو خونهٔ خودتون هست!</b>\n"
        "امیدواریم روزهایی سرشار از آرامش، عطر گلاب، چای آتشی و خنده‌های به‌یادماندنی در کوچه باغ‌های باصفای برزک در کنار هم داشته باشیم. "
        "دلتون شاد و قدمتون پیشاپیش به روی چشم 🌸☕️\n\n"
        f"💰 <b>برآورد اولیه کل هزینه:</b> {format_toman(total_cost)}\n"
        + (f"📝 <b>ملاحظات ثبت‌شده شما:</b> {notes}\n\n" if notes else "\n")
        + "📞 به‌زودی جهت هماهنگی نهایی، ارسال پیش‌پرداخت و تایید قطعی اقامت با شما تماس گرفته خواهد شد.\n\n"
        f"{config.CONTACT_TEXT}\n\n"
        f"{config.ADDRESS_TEXT}"
    )
    await context.bot.send_message(
        chat_id=chat_id,
        text=confirmation_text,
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )
    await context.bot.send_location(
        chat_id=chat_id,
        latitude=config.LOCATION_LATITUDE,
        longitude=config.LOCATION_LONGITUDE,
    )
    await context.bot.send_message(
        chat_id=chat_id,
        text="برای بازگشت به منوی اصلی /start را بزنید."
    )
    context.user_data.clear()



# ---------------------------------------------------------------------------
# توابع مکالمه‌ی سفارش غذا
# ---------------------------------------------------------------------------
async def food_order_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["food_order"] = {
        "items": {},
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
        selected_items = context.user_data["food_order"]["items"]
        if not selected_items:
            await query.answer("لطفاً حداقل یک غذا انتخاب نمایید.", show_alert=True)
            return FOOD_SELECT_ITEM
        text = (
            "📝 <b>توضیحات و ملاحظات سفارش غذا</b>\n\n"
            "قبل از ارسال نهایی، اگر <b>ملاحظه غذایی خاصی</b> دارید (مانند حساسیت غذایی، رژیم کم‌نمک یا دیابت، بدون چربی، میزان تندی، ساعت دقیق سرو یا هر نکته مهمی برای مطبخ)، "
            "می‌توانید همینجا تایپ و ارسال کنید:\n\n"
            "یا در صورتی که نکته خاصی ندارید، دکمه «ثبت نهایی بدون توضیحات» را بزنید 👇"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 ثبت نهایی بدون توضیحات اضافی", callback_data="food_skip_notes")],
            [InlineKeyboardButton("⬅️ بازگشت و ویرایش غذاها", callback_data="food_back_to_items")],
        ])
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)
        return FOOD_ASK_NOTES
    food_key = data.replace("fsel_", "")
    foods = getattr(config, "FOODS", {})
    food = foods.get(food_key)
    if not food:
        await query.edit_message_text("این غذا یافت نشد.")
        return FOOD_SELECT_ITEM
    selected_items = context.user_data["food_order"]["items"]
    max_selections = getattr(config, "MAX_FOOD_SELECTIONS", 2)
    if food_key not in selected_items and len(selected_items) >= max_selections:
        await query.answer(f"⚠️ شما حداکثر مجاز به انتخاب {max_selections} نوع غذا هستید.", show_alert=True)
        return FOOD_SELECT_ITEM
    context.user_data["current_editing_food"] = food_key
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

async def food_skip_notes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    order = context.user_data.get("food_order", {})
    order["notes"] = ""
    await query.edit_message_text("⏳ در حال ثبت و ارسال سفارش غذای شما...")
    await finalize_food_order(query.message, context, is_query=True)
    return ConversationHandler.END


async def food_back_to_items_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await show_food_selection_screen(query.message, context, edit_query=query)


async def food_get_notes_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    order = context.user_data.get("food_order", {})
    order["notes"] = update.message.text.strip()
    await update.message.reply_text("✅ توضیحات و ملاحظات سفارش غذای شما ثبت شد.")
    await finalize_food_order(update.message, context, is_query=False)
    return ConversationHandler.END


async def finalize_food_order(message, context: ContextTypes.DEFAULT_TYPE, is_query: bool = False) -> None:
    order = context.user_data.get("food_order", {})
    name = order.get("name", "نامشخص")
    phone = order.get("phone", "نامشخص")
    room = order.get("room_title", "نامشخص")
    date = order.get("date", "نامشخص")
    weekday = order.get("weekday", "نامشخص")
    meal = order.get("meal_title", "نامشخص")
    notes = order.get("notes", "").strip()
    items = order.get("items", {})
    items_text_list = []
    for k, v in items.items():
        items_text_list.append(f"  🍲 {v['title']}: <b>{v['portions']} پرس</b> ({v['price']})")
    items_formatted = "\n".join(items_text_list) if items_text_list else "موردی انتخاب نشده"
    user = message.from_user if is_query else message.from_user

    admin_text = (
        "🍽🔔 <b>درخواست سفارش غذای جدید</b>\n\n"
        f"👤 <b>مهمان:</b> {name}\n"
        f"📞 <b>شماره تماس:</b> {phone}\n"
        f"🛏 <b>اتاق:</b> {room}\n"
        f"📅 <b>روز و تاریخ سرو:</b> {weekday} {date}\n"
        f"🕒 <b>وعده:</b> {meal}\n\n"
        f"📋 <b>جزئیات سفارش غذا:</b>\n{items_formatted}\n\n"
        f"📝 <b>توضیحات و ملاحظات سفارش:</b>\n{notes if notes else 'ندارد'}\n\n"
        f"🆔 <b>آیدی تلگرام:</b> @{user.username if user and user.username else 'ندارد'}"
    )
    try:
        await context.bot.send_message(
            chat_id=config.ADMIN_CHAT_ID, text=admin_text, parse_mode="HTML"
        )
    except Exception as exc:
        logger.error("ارسال سفارش غذا به مدیر با خطا مواجه شد: %s", exc)

    confirm_text = (
        "🍲 <b>درخواست سفارش غذای شما با مهر و موفقیت ثبت شد!</b>\n\n"
        "🌿 <b>خانواده اقامتگاه خانه برزک، با عطر و بوی غذاهای دست‌پخت سنتی، بی‌صبرانه منتظر دیدارتون تو خونهٔ خودتون هست!</b>\n"
        "امیدواریم طعم اصیل و نوستالژیک این خوراک‌ها براتون ماندگار بشه و دلتون شاد باشه 🌸\n\n"
        f"👤 به نام: {name}\n"
        f"🛏 اتاق: {room}\n"
        f"📅 روز و تاریخ: {weekday} {date}\n"
        f"🕒 وعده: {meal}\n"
        f"📋 خوراک‌ها:\n{items_formatted}\n"
        + (f"📝 <b>ملاحظات ثبت‌شده:</b> {notes}\n\n" if notes else "\n")
        + "سفارش شما برای مطبخ خانه برزک ارسال شد و در زمان مقرر با تازه‌ترین مواد محلی آماده سرو خواهد بود. نوش جان! 🍃\n\n"
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
    # ثبت دستورات ربات؛ همین کار باعث میشه دکمه‌ی آبی «منو» کنار جعبه‌ی تایپ
    # توی تلگرام فعال بشه و با زدنش، لیست دستورات (مثل /start) نشون داده بشه.
    await application.bot.set_my_commands(
        [
            BotCommand("start", "🏡 نمایش منوی اصلی"),
            BotCommand("address", "📍 آدرس اقامتگاه"),
            BotCommand("food", "🍽 منوی غذا و سفارش خوراک"),
            BotCommand("contact", "📞 تماس با ما"),
            BotCommand("cancel", "❌ لغو درخواست رزرو در حال انجام"),
        ]
    )

    # توضیح بات: همین متن قبل از اینکه کاربر /start رو بزنه (توی صفحه‌ی خالی چت)
    # به‌صورت خودکار توسط خود تلگرام نمایش داده میشه.
    await application.bot.set_my_description(
        "🏡 به ربات رزرو اقامتگاه بومگردی «خانه برزک» خوش اومدید!\n\n"
        "با این ربات می‌تونید اتاق‌های اقامتگاه رو ببینید، اطلاعات آدرس، تماس و قوانین "
        "اقامت رو بگیرید و درخواست رزرو ثبت کنید.\n\n"
        "برای شروع، دکمه‌ی Start رو بزنید 👇"
    )
    await application.bot.set_my_short_description(
        "ربات رزرو اقامتگاه بومگردی خانه برزک 🏡"
    )


def main() -> None:
    token = os.environ.get("BOT_TOKEN", config.BOT_TOKEN)
    if token == "-1004485664573":
        raise SystemExit(
            "لطفاً ابتدا توکن ربات رو وارد کنید (در config.py یا متغیر محیطی BOT_TOKEN)."
        )

    application = Application.builder().token(token).post_init(post_init).build()

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
            ASK_ROOM_SELECT: [
                CallbackQueryHandler(book_select_room, pattern=r"^bselectroom_"),
                CallbackQueryHandler(book_cancel_callback, pattern=r"^b_cancel_booking$"),
            ],
            ASK_ROOM_ADULTS: [
                CallbackQueryHandler(book_adults_callback, pattern=r"^badults_"),
                CallbackQueryHandler(book_cancel_callback, pattern=r"^b_cancel_booking$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, book_get_adults_text),
            ],
            ASK_ROOM_CHILDREN_5_12: [
                CallbackQueryHandler(book_child_5_12_callback, pattern=r"^bchild512_"),
                CallbackQueryHandler(book_cancel_callback, pattern=r"^b_cancel_booking$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, book_get_child_5_12_text),
            ],
            ASK_ROOM_CHILDREN_UNDER_5: [
                CallbackQueryHandler(book_child_u5_callback, pattern=r"^bchildu5_"),
                CallbackQueryHandler(book_cancel_callback, pattern=r"^b_cancel_booking$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, book_get_child_u5_text),
            ],
            ASK_ROOM_MORE_OR_CONFIRM: [
                CallbackQueryHandler(book_add_room_prompt, pattern=r"^b_add_room$"),
                CallbackQueryHandler(book_select_room, pattern=r"^bselectroom_"),
                CallbackQueryHandler(book_show_summary_callback, pattern=r"^b_view_summary$"),
                CallbackQueryHandler(book_ask_notes_callback, pattern=r"^b_add_notes$"),
                CallbackQueryHandler(book_confirm_final_callback, pattern=r"^b_confirm_final$"),
                CallbackQueryHandler(book_cancel_callback, pattern=r"^b_cancel_booking$"),
            ],
            ASK_SPECIAL_NOTES: [
                CallbackQueryHandler(book_skip_notes_finalize_callback, pattern=r"^b_skip_notes_finalize$"),
                CallbackQueryHandler(book_skip_notes_callback, pattern=r"^b_skip_notes$"),
                CallbackQueryHandler(book_ask_notes_callback, pattern=r"^b_add_notes$"),
                CallbackQueryHandler(book_show_summary_callback, pattern=r"^b_view_summary$"),
                CallbackQueryHandler(book_cancel_callback, pattern=r"^b_cancel_booking$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, book_get_notes_text),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(book_cancel_callback, pattern=r"^b_cancel_booking$"),
        ],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("address", cmd_address))
    application.add_handler(CommandHandler("contact", cmd_contact))
    
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
            FOOD_ASK_NOTES: [
                CallbackQueryHandler(food_skip_notes_callback, pattern=r"^food_skip_notes$"),
                CallbackQueryHandler(food_back_to_items_callback, pattern=r"^food_back_to_items$"),
                CallbackQueryHandler(food_item_toggle, pattern=r"^food_cancel_order$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, food_get_notes_text),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(food_item_toggle, pattern=r"^food_cancel_order$"),
        ],
    )

    application.add_handler(booking_conv)
    application.add_handler(food_conv)
    application.add_handler(CommandHandler("food", cmd_food))
    application.add_handler(CallbackQueryHandler(menu_router))
    application.add_handler(CommandHandler("cancel", cancel_outside_conversation))
    application.add_handler(
        MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, receive_payment_receipt)
    )

    # اگر متغیر محیطی WEBHOOK_URL تنظیم شده باشه (مثلا موقع دیپلوی روی Render)
    # ربات با webhook اجرا میشه، در غیر این صورت با polling (مناسب اجرای لوکال روی سیستم خودت)
    webhook_url = os.environ.get("WEBHOOK_URL") or os.environ.get("RENDER_EXTERNAL_URL")
    if webhook_url:
        port = int(os.environ.get("PORT", "10000"))
        url_path = token  # مسیر مخفی وبهوک؛ حدس زدنش سخته چون خود توکنه
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
