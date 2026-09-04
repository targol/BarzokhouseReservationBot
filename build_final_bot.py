# -*- coding: utf-8 -*-
with open("github_bot.py", "r", encoding="utf-8") as f:
    text = f.read()

header1 = "# ---------------------------------------------------------------------------\n# وضعیت‌های مکالمه‌ی رزرو"
header2 = "# ---------------------------------------------------------------------------\n# کیبوردهای کمکی"
header3 = "# ---------------------------------------------------------------------------\n# دستور /start"
header4 = "# ---------------------------------------------------------------------------\n# مدیریت دکمه‌های منوی اصلی (غیر از رزرو)"
header5 = "# ---------------------------------------------------------------------------\n# مکالمه‌ی رزرو"
header6 = "# ---------------------------------------------------------------------------\n# راه‌اندازی ربات"

p1 = text.find(header1)
p2 = text.find(header2)
p3 = text.find(header3)
p4 = text.find(header4)
p5 = text.find(header5)
p6 = text.find(header6)

part0 = text[:p1]
# Between p1 and p2: states, to_english_digits, calendar, parse_checkin_date
part1 = text[p1:p2]
# Helpers
part2 = text[p2:p3]
# Start & basics
part3 = text[p3:p4]
# Menu router
part4 = text[p4:p5]
# Booking conversation
part5 = text[p5:p6]
# Main & runner
part6 = text[p6:]

# 1. Update states in part1
food_states = """
# ---------------------------------------------------------------------------
# وضعیت‌های مکالمه‌ی سفارش غذا (ناهار / شام)
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
"""

# Modify build_calendar_keyboard signature to accept prefix
old_cal_def = "def build_calendar_keyboard(year: int, month: int) -> InlineKeyboardMarkup:"
new_cal_def = "def build_calendar_keyboard(year: int, month: int, prefix: str = 'cal_day_') -> InlineKeyboardMarkup:"

part1_mod = part1.replace(old_cal_def, new_cal_def)
part1_mod = part1_mod.replace('f"cal_nav_{prev_year}_{prev_month}"', 'f"{nav_prefix}{prev_year}_{prev_month}"')
part1_mod = part1_mod.replace('f"cal_nav_{next_year}_{next_month}"', 'f"{nav_prefix}{next_year}_{next_month}"')
part1_mod = part1_mod.replace('f"cal_day_{year}_{month}_{day}"', 'f"{prefix}{year}_{month}_{day}"')

# Add nav_prefix definition in build_calendar_keyboard
part1_mod = part1_mod.replace(
    '    # هدر: ماه/سال + دکمه‌های قبلی و بعدی',
    '    nav_prefix = "cal_nav_" if prefix == "cal_day_" else "fcal_nav_"\n    # هدر: ماه/سال + دکمه‌های قبلی و بعدی'
)

# Add parse_jalali_date_details
jalali_helper = """
def parse_jalali_date_details(raw_text: str):
    \"\"\"پارس تاریخ شمسی و بازگرداندن jdatetime.date جهت استخراج روز هفته\"\"\"
    text = to_english_digits(raw_text.strip())
    parts = text.replace("-", "/").split("/")
    if len(parts) != 3:
        return None
    try:
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        return jdatetime.date(y, m, d)
    except Exception:
        return None
"""

part1_final = part1_mod + food_states + jalali_helper

# 2. Update helpers in part2
old_main_menu = """def main_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("🛏 اتاق‌ها", callback_data="menu_rooms")],
        [InlineKeyboardButton("🍽 منوی غذا", callback_data="menu_food")],
        [InlineKeyboardButton("📜 اطلاعاتی درباره اقامتگاه", callback_data="menu_rules")],
        [InlineKeyboardButton("📍 آدرس", callback_data="menu_address")],
        [InlineKeyboardButton("📞 تماس با ما", callback_data="menu_contact")],
        [InlineKeyboardButton("🌐 شبکه‌های اجتماعی", callback_data="menu_social")],
        [InlineKeyboardButton("💳 پرداخت", callback_data="menu_payment")],
        [InlineKeyboardButton("⭐ ثبت تجریه شما", callback_data="menu_review")],
    ]
    return InlineKeyboardMarkup(buttons)"""

new_main_menu = """def main_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("🛏 اتاق‌ها و رزرو اقامت", callback_data="menu_rooms")],
        [InlineKeyboardButton("🍽 منوی غذا و سفارش خوراک", callback_data="menu_food")],
        [InlineKeyboardButton("📜 اطلاعاتی درباره اقامتگاه", callback_data="menu_rules")],
        [InlineKeyboardButton("📍 آدرس و لوکیشن", callback_data="menu_address")],
        [InlineKeyboardButton("📞 تماس با ما", callback_data="menu_contact")],
        [InlineKeyboardButton("🌐 شبکه‌های اجتماعی", callback_data="menu_social")],
        [InlineKeyboardButton("💳 پرداخت آنلاین", callback_data="menu_payment")],
        [InlineKeyboardButton("⭐ ثبت تجربه شما", callback_data="menu_review")],
    ]
    return InlineKeyboardMarkup(buttons)"""

food_helpers = """
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
"""

part2_final = part2.replace(old_main_menu, new_main_menu) + food_helpers

# 3. In part3 (basics), add cmd_food
cmd_food_code = """
async def cmd_food(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        config.FOOD_MENU_TEXT,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=food_menu_keyboard(),
    )
"""
part3_final = part3 + cmd_food_code

# 4. In part4 (menu_router), update menu_food handler
old_menu_food = """    if data == "menu_food":
        food_keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🍽 مشاهده منوی غذا", url=config.FOOD_MENU_URL)],
                [InlineKeyboardButton("⬅️ بازگشت به منو", callback_data="back_main")],
            ]
        )
        await query.edit_message_text(
            config.FOOD_MENU_TEXT,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=food_keyboard,
        )
        return"""

new_menu_food = """    if data == "menu_food":
        await query.edit_message_text(
            config.FOOD_MENU_TEXT,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=food_menu_keyboard(),
        )
        return

    if data == "food_list_details":
        foods = getattr(config, "FOODS", {})
        text_lines = ["🍽 <b>لیست خوراک‌ها و غذاهای محلی خانه برزک:</b>\\n"]
        for key, food in foods.items():
            meal_names = [config.MEALS[m]["title"] for m in food.get("available_meals", []) if m in config.MEALS]
            meals_str = " و ".join(meal_names) if meal_names else "ناهار و شام"
            text_lines.append(
                f"▫️ <b>{food['title']}</b>\\n"
                f"   💵 قیمت: {food['price']}\\n"
                f"   🕒 وعده‌های ارائه: {meals_str}\\n"
                f"   📝 {food['description']}\\n"
            )
        text_lines.append("برای ثبت درخواست وعده ناهار یا شام بر روی دکمه زیر بزنید 👇")
        full_text = "\\n".join(text_lines)
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
            f"🍲 <b>{food['title']}</b>\\n\\n"
            f"💵 <b>قیمت:</b> {food['price']}\\n"
            f"🕒 <b>قابل سفارش برای:</b> {meals_str}\\n\\n"
            f"📖 <b>توضیحات:</b>\\n{food['description']}"
        )
        item_keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🍲 ثبت درخواست غذا", callback_data="food_order_start")],
                [InlineKeyboardButton("⬅️ بازگشت به لیست غذاها", callback_data="food_list_details")],
            ]
        )
        await query.edit_message_text(item_text, parse_mode="HTML", reply_markup=item_keyboard)
        return"""

part4_final = part4.replace(old_menu_food, new_menu_food)

# 5. In part5 (booking conv), enhance with weekday display and add the entire food conversation handlers
food_conv_handlers = """
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
        "🍲 <b>ثبت درخواست وعده غذایی در خانه برزک</b>\\n\\n"
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
        f"سپاس جناب/سرکار {name} عزیز.\\n"
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
        "ممنون! این غذا برای چه اتاقی در خانه برزک سرو شود؟\\n"
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
        "📅 این سفارش برای <b>کدام روز هفته و چه تاریخی</b> از اقامت شماست؟\\n\\n"
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
        f"🕒 وعده انتخاب‌شده: <b>{meal_title}</b>\\n\\n"
        f"🍲 <b>انتخاب غذاها:</b>\\n"
        f"هر مهمان می‌تواند حداکثر <b>{max_selections} نوع غذا</b> برای این وعده انتخاب کند.\\n"
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
        f"🍲 غذای انتخابی: <b>{food['title']}</b>\\n"
        f"💵 قیمت هر پرس: {food['price']}\\n\\n"
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
        f"🕒 وعده: <b>{meal_title}</b> | حداکثر <b>{max_selections} نوع غذا</b>\\n\\n"
        + "\\n".join(summary_lines)
        + "\\n\\nبرای افزودن/ویرایش غذاها کلیک کنید یا در صورت اتمام، دکمه تایید نهایی را بزنید 👇"
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
    items_formatted = "\\n".join(items_text_list) if items_text_list else "موردی انتخاب نشده"
    user = message.from_user if is_query else message.from_user

    admin_text = (
        "🍽🔔 <b>درخواست سفارش غذای جدید</b>\\n\\n"
        f"👤 <b>مهمان:</b> {name}\\n"
        f"📞 <b>شماره تماس:</b> {phone}\\n"
        f"🛏 <b>اتاق:</b> {room}\\n"
        f"📅 <b>روز و تاریخ سرو:</b> {weekday} {date}\\n"
        f"🕒 <b>وعده:</b> {meal}\\n\\n"
        f"📋 <b>جزئیات سفارش غذا:</b>\\n{items_formatted}\\n\\n"
        f"🆔 <b>آیدی تلگرام:</b> @{user.username if user and user.username else 'ندارد'}"
    )
    try:
        await context.bot.send_message(
            chat_id=config.ADMIN_CHAT_ID, text=admin_text, parse_mode="HTML"
        )
    except Exception as exc:
        logger.error("ارسال سفارش غذا به مدیر با خطا مواجه شد: %s", exc)

    confirm_text = (
        "✅ <b>درخواست غذای شما با موفقیت ثبت شد!</b>\\n\\n"
        f"👤 به نام: {name}\\n"
        f"🛏 اتاق: {room}\\n"
        f"📅 روز و تاریخ: {weekday} {date}\\n"
        f"🕒 وعده: {meal}\\n"
        f"📋 خوراک‌ها:\\n{items_formatted}\\n\\n"
        "سفارش شما برای آشپزخانه اقامتگاه ارسال شد و در زمان مقرر تدارک دیده خواهد شد. نوش جان! 🌿\\n\\n"
        "برای بازگشت به منوی اصلی /start را بزنید."
    )
    await message.reply_text(
        confirm_text,
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data.clear()
"""

part5_final = part5 + food_conv_handlers

# 6. In part6 (post_init & main), register /food command and food_conv
part6_mod = part6.replace(
    'BotCommand("contact", "📞 تماس با ما"),',
    'BotCommand("food", "🍽 منوی غذا و سفارش خوراک"),\n            BotCommand("contact", "📞 تماس با ما"),'
)

food_conv_registration = """
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
"""

part6_mod = part6_mod.replace(
    'application.add_handler(booking_conv)',
    food_conv_registration + '\n    application.add_handler(booking_conv)\n    application.add_handler(food_conv)\n    application.add_handler(CommandHandler("food", cmd_food))'
)

full_bot = part0 + part1_final + part2_final + part3_final + part4_final + part5_final + part6_mod

with open("repo_files/bot.py", "w", encoding="utf-8") as f:
    f.write(full_bot)

print("Generated bot.py length:", len(full_bot))
