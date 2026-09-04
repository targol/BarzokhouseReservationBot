// handlers/callback_query.js - مدیریت کلیک روی دکمه‌های شیشه‌ای در تلگرام سرورلس
import {
  BOT_TOKEN,
  ADMIN_CHAT_ID,
  WELCOME_MESSAGE,
  ADDRESS_TEXT,
  LOCATION_LATITUDE,
  LOCATION_LONGITUDE,
  CONTACT_TEXT,
  SOCIAL_TEXT,
  PAYMENT_URL,
  HOUSE_RULES_TEXT,
  ROOMS,
  FOODS
} from "../config.js";
import {
  mainMenuKeyboard,
  backToMainKeyboard,
  socialLinksKeyboard,
  roomsListKeyboard,
  roomDetailKeyboard,
  bookingRoomsSelectionKeyboard,
  ageCountersKeyboard,
  bookingFinalConfirmKeyboard,
  foodMenuKeyboard,
  foodSelectionKeyboard,
  foodPortionsKeyboard,
  foodNotesKeyboard,
  foodConfirmKeyboard
} from "../keyboards.js";
import {
  toPersianDigits,
  formatPrice
} from "../utils.js";
import { getSession, setSession, clearSession } from "../db.js";

async function answerCallback(ctx, queryId, text = "", showAlert = false) {
  if (ctx && ctx.api && typeof ctx.api.answerCallbackQuery === "function") {
    return await ctx.api.answerCallbackQuery(queryId, { text, show_alert: showAlert });
  }
  const token = (ctx && ctx.env && ctx.env.BOT_TOKEN) || BOT_TOKEN;
  if (!token) return;
  await fetch(`https://api.telegram.org/bot${token}/answerCallbackQuery`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      callback_query_id: queryId,
      text,
      show_alert: showAlert
    })
  });
}

async function editMessage(ctx, chatId, messageId, text, options = {}) {
  if (ctx && ctx.api && typeof ctx.api.editMessageText === "function") {
    return await ctx.api.editMessageText(chatId, messageId, text, { parse_mode: "HTML", ...options });
  }
  const token = (ctx && ctx.env && ctx.env.BOT_TOKEN) || BOT_TOKEN;
  if (!token) return;
  const res = await fetch(`https://api.telegram.org/bot${token}/editMessageText`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      message_id: messageId,
      text,
      parse_mode: "HTML",
      ...options
    })
  });
  return await res.json();
}

async function sendMessage(ctx, chatId, text, options = {}) {
  if (ctx && ctx.api && typeof ctx.api.sendMessage === "function") {
    return await ctx.api.sendMessage(chatId, text, { parse_mode: "HTML", ...options });
  }
  const token = (ctx && ctx.env && ctx.env.BOT_TOKEN) || BOT_TOKEN;
  if (!token) return;
  const res = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text,
      parse_mode: "HTML",
      ...options
    })
  });
  return await res.json();
}

async function sendLocation(ctx, chatId, lat, lon) {
  if (ctx && ctx.api && typeof ctx.api.sendLocation === "function") {
    return await ctx.api.sendLocation(chatId, lat, lon);
  }
  const token = (ctx && ctx.env && ctx.env.BOT_TOKEN) || BOT_TOKEN;
  if (!token) return;
  await fetch(`https://api.telegram.org/bot${token}/sendLocation`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      latitude: lat,
      longitude: lon
    })
  });
}

export default async function handleCallbackQuery(payload, ctx) {
  const query = payload?.callback_query || payload;
  if (!query) return;

  const data = query.data;
  const queryId = query.id;
  const chatId = query.message?.chat?.id;
  const messageId = query.message?.message_id;
  const userId = query.from?.id;

  if (!chatId || !userId) return;

  // ۱. نادیده‌گرفتن کلیک‌های خنثی
  if (data === "ignore") {
    return await answerCallback(ctx, queryId);
  }

  // ۲. بازگشت به منوی اصلی
  if (data === "back_main") {
    await answerCallback(ctx, queryId);
    await clearSession(ctx, userId);
    return await editMessage(ctx, chatId, messageId, WELCOME_MESSAGE, {
      reply_markup: mainMenuKeyboard()
    });
  }

  // ۳. اتاق‌ها و لیست آن‌ها
  if (data === "menu_rooms") {
    await answerCallback(ctx, queryId);
    return await editMessage(
      ctx,
      chatId,
      messageId,
      "🛏 <b>اتاق‌های اقامتگاه بومگردی خانه برزک</b>\n\nبرای مشاهده مشخصات هر اتاق روی نام آن بزنید یا مستقیماً درخواست رزرو را شروع فرمایید 👇",
      { reply_markup: roomsListKeyboard() }
    );
  }

  // نمایش جزئیات اتاق
  if (data.startsWith("room_")) {
    const roomKey = data.replace("room_", "");
    const room = ROOMS[roomKey];
    if (!room) {
      return await answerCallback(ctx, queryId, "اتاق یافت نشد", true);
    }
    await answerCallback(ctx, queryId);
    const text = `🏡 <b>${room.title}</b>\n\n${room.description}\n\n💰 <b>نرخ:</b> ${room.price}`;
    return await editMessage(ctx, chatId, messageId, text, {
      reply_markup: roomDetailKeyboard(roomKey)
    });
  }

  // ۴. منوی غذا
  if (data === "menu_food") {
    await answerCallback(ctx, queryId);
    return await editMessage(
      ctx,
      chatId,
      messageId,
      "🍽 <b>منوی غذاهای محلی اقامتگاه خانه برزک</b>\n\nغذاها با مواد اولیه تازه و سنتی برزک طبخ می‌شوند. برای مشاهده قیمت یا سفارش خوراک از گزینه‌های زیر استفاده کنید 👇",
      { reply_markup: foodMenuKeyboard() }
    );
  }

  if (data.startsWith("finfo_")) {
    const foodKey = data.replace("finfo_", "");
    const food = FOODS[foodKey];
    if (!food) return await answerCallback(ctx, queryId, "غذا یافت نشد", true);
    await answerCallback(ctx, queryId);
    const mealsText = (food.available_meals || []).map((m) => m === "lunch" ? "ناهار" : "شام").join(" و ");
    const text = `🍲 <b>${food.title}</b>\n\n${food.description}\n\n💰 <b>قیمت:</b> ${food.price}\n☀️ <b>وعده‌های سرو:</b> ${mealsText}`;
    return await editMessage(ctx, chatId, messageId, text, {
      reply_markup: {
        inline_keyboard: [
          [{ text: "🍲 شروع ثبت سفارش این غذا", callback_data: "food_order_start" }],
          [{ text: "⬅️ بازگشت به منوی غذا", callback_data: "menu_food" }]
        ]
      }
    });
  }

  // ۵. بخش‌های عمومی
  if (data === "menu_rules") {
    await answerCallback(ctx, queryId);
    return await editMessage(ctx, chatId, messageId, HOUSE_RULES_TEXT, {
      reply_markup: backToMainKeyboard()
    });
  }

  if (data === "menu_address") {
    await answerCallback(ctx, queryId);
    await editMessage(ctx, chatId, messageId, ADDRESS_TEXT, {
      reply_markup: backToMainKeyboard()
    });
    return await sendLocation(ctx, chatId, LOCATION_LATITUDE, LOCATION_LONGITUDE);
  }

  if (data === "menu_contact") {
    await answerCallback(ctx, queryId);
    return await editMessage(ctx, chatId, messageId, CONTACT_TEXT, {
      reply_markup: backToMainKeyboard()
    });
  }

  if (data === "menu_social") {
    await answerCallback(ctx, queryId);
    return await editMessage(ctx, chatId, messageId, SOCIAL_TEXT, {
      reply_markup: socialLinksKeyboard()
    });
  }

  if (data === "menu_payment") {
    await answerCallback(ctx, queryId);
    const payText = `💳 <b>پرداخت آنلاین اقامتگاه خانه برزک:</b>\n\nجهت واریز بیعانه یا تسویه حساب، می‌توانید از درگاه امن زیر استفاده فرمایید:\n<a href="${PAYMENT_URL}">ورود به درگاه پرداخت آنلاین</a>\n\nپس از واریز، عکس رسید را در همین گفتگو ارسال نمایید.`;
    return await editMessage(ctx, chatId, messageId, payText, {
      reply_markup: backToMainKeyboard()
    });
  }

  if (data === "menu_review") {
    await answerCallback(ctx, queryId);
    const reviewText = `⭐ <b>ثبت تجربه و نظرات شما</b>\n\nنظر و تجربه شما در خانه برزک برای ما بسیار ارزشمند است.\nلطفاً نظرات یا پیشنهادات خود را در قالب پیام متنی یا صوتی ارسال فرمایید تا جهت بهبود کیفیت خدمات ثبت گردد 🌿`;
    return await editMessage(ctx, chatId, messageId, reviewText, {
      reply_markup: backToMainKeyboard()
    });
  }

  // ۶. شروع جریان رزرو
  if (data === "book_start_direct" || data.startsWith("book_")) {
    await answerCallback(ctx, queryId);
    const preSelected = data.startsWith("book_") && data !== "book_start_direct" && !data.includes("cancel") && !data.includes("confirm")
      ? [data.replace("book_", "")]
      : [];

    await setSession(ctx, userId, "BOOKING_ASK_NAME", {
      selectedRooms: preSelected,
      adults: 1,
      kids5to12: 0,
      kidsUnder5: 0
    });

    return await sendMessage(
      ctx,
      chatId,
      "✨ <b>فرآیند رزرو اقامتگاه خانه برزک</b>\n\nلطفاً <b>نام و نام خانوادگی</b> مهمان اصلی را وارد فرمایید:"
    );
  }

  // انتخاب اتاق‌ها با چک‌باکس
  if (data.startsWith("selroom_")) {
    const action = data.replace("selroom_", "");
    const session = await getSession(ctx, userId);
    const sData = session.data || {};
    sData.selectedRooms = sData.selectedRooms || [];

    if (action === "done") {
      if (sData.selectedRooms.length === 0) {
        return await answerCallback(ctx, queryId, "لطفاً حداقل یک اتاق را انتخاب کنید", true);
      }
      await answerCallback(ctx, queryId);
      await setSession(ctx, userId, "BOOKING_AGE_COUNTERS", sData);
      return await editMessage(
        ctx,
        chatId,
        messageId,
        "👥 <b>تعداد نفرات و تفکیک رده‌های سنی:</b>\n\n" +
        "• بزرگسال: هزینه کامل\n" +
        "• کودک ۵ تا ۱۲ سال: <b>نیم‌بها (۵۰٪ تخفیف)</b>\n" +
        "• کودک زیر ۵ سال: <b>رایگان</b>\n\n" +
        "با دکمه‌های ➕ و ➖ تعداد هر رده را مشخص فرمایید 👇",
        { reply_markup: ageCountersKeyboard(sData.adults || 1, sData.kids5to12 || 0, sData.kidsUnder5 || 0) }
      );
    }

    // تغییر وضعیت انتخاب اتاق
    if (sData.selectedRooms.includes(action)) {
      sData.selectedRooms = sData.selectedRooms.filter((k) => k !== action);
    } else {
      sData.selectedRooms.push(action);
    }
    await setSession(ctx, userId, "BOOKING_SELECT_ROOMS", sData);
    await answerCallback(ctx, queryId);
    return await editMessage(
      ctx,
      chatId,
      messageId,
      "🛏 <b>انتخاب اتاق‌ها (تک یا چند اتاقه):</b>\n\nشما می‌توانید یک یا چند اتاق را با لمس گزینه‌ها علامت بزنید و سپس دکمه تأیید را لمس نمایید 👇",
      { reply_markup: bookingRoomsSelectionKeyboard(sData.selectedRooms) }
    );
  }

  // تغییر شمارنده‌های سن
  if (data.startsWith("guest_")) {
    const session = await getSession(ctx, userId);
    const sData = session.data || {};
    sData.adults = sData.adults || 1;
    sData.kids5to12 = sData.kids5to12 || 0;
    sData.kidsUnder5 = sData.kidsUnder5 || 0;

    if (data === "guest_adult_inc") sData.adults += 1;
    if (data === "guest_adult_dec" && sData.adults > 1) sData.adults -= 1;
    if (data === "guest_kid12_inc") sData.kids5to12 += 1;
    if (data === "guest_kid12_dec" && sData.kids5to12 > 0) sData.kids5to12 -= 1;
    if (data === "guest_kid5_inc") sData.kidsUnder5 += 1;
    if (data === "guest_kid5_dec" && sData.kidsUnder5 > 0) sData.kidsUnder5 -= 1;

    await setSession(ctx, userId, "BOOKING_AGE_COUNTERS", sData);
    await answerCallback(ctx, queryId);
    return await editMessage(
      ctx,
      chatId,
      messageId,
      "👥 <b>تعداد نفرات و تفکیک رده‌های سنی:</b>\n\n" +
      "• بزرگسال: هزینه کامل\n" +
      "• کودک ۵ تا ۱۲ سال: <b>نیم‌بها (۵۰٪ تخفیف)</b>\n" +
      "• کودک زیر ۵ سال: <b>رایگان</b>\n\n" +
      "با دکمه‌های ➕ و ➖ تعداد هر رده را مشخص فرمایید 👇",
      { reply_markup: ageCountersKeyboard(sData.adults, sData.kids5to12, sData.kidsUnder5) }
    );
  }

  if (data === "guests_confirmed") {
    await answerCallback(ctx, queryId);
    const session = await getSession(ctx, userId);
    await setSession(ctx, userId, "BOOKING_ASK_NOTES", session.data || {});
    return await sendMessage(
      ctx,
      chatId,
      "📝 <b>ملاحظات و درخواست‌های خاص:</b>\n\n" +
      "آیا نکته‌ای مانند ساعت ورود حدودی، افراد سالمند یا با نیازهای ویژه حرکتی، رژیم غذایی خاص یا همراه داشتن وسایل خاص دارید؟\n\n" +
      "لطفاً در پیام بنویسید (یا عدد ۰ یا کلمه «ندارم» را ارسال کنید):"
    );
  }

  if (data === "book_confirm_final") {
    await answerCallback(ctx, queryId, "درخواست رزرو ثبت شد!", false);
    const session = await getSession(ctx, userId);
    const sData = session.data || {};

    const roomTitles = (sData.selectedRooms || []).map((k) => ROOMS[k]?.title || k);
    const adminMessage = `🔔 <b>درخواست رزرو جدید اقامتگاه:</b>\n\n` +
      `👤 مهمان: <b>${sData.guestName}</b>\n` +
      `📞 تلفن: <code>${sData.phone}</code>\n` +
      `🆔 شناسه تلگرام: <code>${userId}</code>\n` +
      `📅 تاریخ ورود: <b>${sData.checkinWeekday} ${toPersianDigits(sData.checkinDate)}</b>\n` +
      `🌙 مدت: <b>${toPersianDigits(sData.duration)} شب</b>\n` +
      `🛏 اتاق‌ها: <b>${roomTitles.join(" + ")}</b>\n` +
      `👥 ترکیب نفرات: ${toPersianDigits(sData.adults || 1)} بزرگسال | ${toPersianDigits(sData.kids5to12 || 0)} کودک ۵-۱۲ | ${toPersianDigits(sData.kidsUnder5 || 0)} زیر ۵ سال\n` +
      `📝 ملاحظات: <i>${sData.notes || "ندارد"}</i>\n` +
      `💰 مبلغ کل: <b>${formatPrice(sData.totalAmount)}</b>`;

    const token = (ctx && ctx.env && ctx.env.BOT_TOKEN) || BOT_TOKEN;
    if (token && ADMIN_CHAT_ID) {
      await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: ADMIN_CHAT_ID,
          text: adminMessage,
          parse_mode: "HTML"
        })
      });
    }

    await clearSession(ctx, userId);

    const guestWelcome = `🏡 <b>درخواست رزرو شما با موفقیت ثبت شد!</b>\n\n` +
      `از اینکه اقامتگاه بومگردی «خانه برزک» را برای اقامت و خلق لحظات خاطره‌انگیز خود انتخاب کردید، صمیمانه سپاسگزاریم. ما باور داریم روح این خانه با حضور گرم شما زنده است 🌿\n\n` +
      `مدیریت اقامتگاه پس از بررسی تقویم، حداکثر ظرف ۱ ساعت جهت نهایی‌سازی و هماهنگی با شماره <code>${sData.phone}</code> تماس خواهد گرفت.\n\n` +
      `به امید دیدار شما در خانه برزک ✨`;

    return await editMessage(ctx, chatId, messageId, guestWelcome, {
      reply_markup: backToMainKeyboard()
    });
  }

  if (data === "book_cancel" || data === "food_cancel_order") {
    await answerCallback(ctx, queryId, "لغو شد");
    await clearSession(ctx, userId);
    return await editMessage(
      ctx,
      chatId,
      messageId,
      "❌ عملیات لغو شد.\nبرای دسترسی به سایر بخش‌ها از منوی زیر استفاده کنید:",
      { reply_markup: mainMenuKeyboard() }
    );
  }

  // ۷. جریان سفارش غذا
  if (data === "food_order_start") {
    await answerCallback(ctx, queryId);
    await setSession(ctx, userId, "FOOD_ASK_GUEST_NAME", {});
    return await sendMessage(
      ctx,
      chatId,
      "🍽 <b>ثبت سفارش غذای خانه برزک</b>\n\nلطفاً <b>نام و نام خانوادگی</b> مهمان را وارد فرمایید:"
    );
  }

  if (data === "meal_lunch" || data === "meal_dinner") {
    await answerCallback(ctx, queryId);
    const mealType = data === "meal_lunch" ? "lunch" : "dinner";
    const session = await getSession(ctx, userId);
    const sData = session.data || {};
    sData.mealType = mealType;
    sData.selectedFoods = sData.selectedFoods || [];
    await setSession(ctx, userId, "FOOD_SELECT_ITEMS", sData);

    return await editMessage(
      ctx,
      chatId,
      messageId,
      `🍴 <b>انتخاب غذاهای وعده ${mealType === "lunch" ? "ناهار" : "شام"}:</b>\n` +
      `<i>(امکان انتخاب حداکثر ۲ نوع غذا برای هر وعده وجود دارد)</i> 👇`,
      { reply_markup: foodSelectionKeyboard(mealType, sData.selectedFoods) }
    );
  }

  if (data.startsWith("fsel_")) {
    const foodKey = data.replace("fsel_", "");
    const session = await getSession(ctx, userId);
    const sData = session.data || {};
    sData.selectedFoods = sData.selectedFoods || [];

    if (sData.selectedFoods.includes(foodKey)) {
      sData.selectedFoods = sData.selectedFoods.filter((k) => k !== foodKey);
    } else {
      if (sData.selectedFoods.length >= 2) {
        return await answerCallback(ctx, queryId, "در هر سفارش حداکثر ۲ نوع غذا قابل انتخاب است", true);
      }
      sData.selectedFoods.push(foodKey);
    }

    await setSession(ctx, userId, "FOOD_SELECT_ITEMS", sData);
    await answerCallback(ctx, queryId);
    return await editMessage(
      ctx,
      chatId,
      messageId,
      `🍴 <b>انتخاب غذاهای وعده ${sData.mealType === "lunch" ? "ناهار" : "شام"}:</b>\n` +
      `<i>(امکان انتخاب حداکثر ۲ نوع غذا برای هر وعده وجود دارد)</i> 👇`,
      { reply_markup: foodSelectionKeyboard(sData.mealType, sData.selectedFoods) }
    );
  }

  if (data === "food_finalize") {
    const session = await getSession(ctx, userId);
    const sData = session.data || {};
    if (!sData.selectedFoods || sData.selectedFoods.length === 0) {
      return await answerCallback(ctx, queryId, "لطفاً حداقل یک غذا را انتخاب کنید", true);
    }
    await answerCallback(ctx, queryId);

    // شروع تعیین پرس برای غذاها
    sData.portions = sData.portions || {};
    const firstFoodKey = sData.selectedFoods[0];
    sData.currentFoodKey = firstFoodKey;
    await setSession(ctx, userId, "FOOD_ASK_PORTIONS", sData);

    const foodObj = FOODS[firstFoodKey];
    return await editMessage(
      ctx,
      chatId,
      messageId,
      `🍲 چند پرس از <b>«${foodObj?.title}»</b> میل دارید؟ 👇`,
      { reply_markup: foodPortionsKeyboard() }
    );
  }

  if (data.startsWith("fportion_")) {
    const val = data.replace("fportion_", "");
    const session = await getSession(ctx, userId);
    const sData = session.data || {};
    sData.portions = sData.portions || {};

    if (val === "custom") {
      await answerCallback(ctx, queryId);
      await setSession(ctx, userId, "FOOD_ASK_PORTION_CUSTOM", sData);
      return await sendMessage(ctx, chatId, "لطفاً تعداد پرس مد نظرتان را به صورت عدد ارسال فرمایید:");
    }

    const count = parseInt(val, 10) || 1;
    if (sData.currentFoodKey) {
      sData.portions[sData.currentFoodKey] = count;
    }

    // آیا غذای بعدی برای تعیین پرس وجود دارد؟
    const foods = sData.selectedFoods || [];
    const currentIndex = foods.indexOf(sData.currentFoodKey);
    if (currentIndex >= 0 && currentIndex + 1 < foods.length) {
      const nextFoodKey = foods[currentIndex + 1];
      sData.currentFoodKey = nextFoodKey;
      await setSession(ctx, userId, "FOOD_ASK_PORTIONS", sData);
      await answerCallback(ctx, queryId);
      const foodObj = FOODS[nextFoodKey];
      return await editMessage(
        ctx,
        chatId,
        messageId,
        `🍲 چند پرس از <b>«${foodObj?.title}»</b> میل دارید؟ 👇`,
        { reply_markup: foodPortionsKeyboard() }
      );
    }

    // همه غذاها پرس خوردند، رفتن به یادداشت
    await setSession(ctx, userId, "FOOD_ASK_NOTES", sData);
    await answerCallback(ctx, queryId);
    return await editMessage(
      ctx,
      chatId,
      messageId,
      "📝 آیا یادداشت یا نکته خاصی در مورد پخت غذاها (مثلاً کم‌نمک، بدون فلفل، یا زمان سرو) دارید؟\nدر پیام بنویسید یا دکمه «رد شدن» را لمس کنید 👇",
      { reply_markup: foodNotesKeyboard() }
    );
  }

  if (data === "food_skip_notes") {
    await answerCallback(ctx, queryId);
    const session = await getSession(ctx, userId);
    const sData = session.data || {};
    sData.notes = "بدون یادداشت";

    let invoice = `🍲 <b>پیش‌فاکتور سفارش غذا:</b>\n` +
      `👤 مهمان: <b>${sData.guestName}</b>\n` +
      `📞 شماره تماس: <code>${sData.phone}</code>\n` +
      `🛏 اتاق / رزرو: <b>${sData.roomName}</b>\n` +
      `📅 تاریخ: <b>${sData.mealWeekday} ${toPersianDigits(sData.mealDate)}</b>\n` +
      `☀️ وعده: <b>${sData.mealType === "lunch" ? "ناهار" : "شام"}</b>\n\n` +
      `🍴 <b>اقلام انتخابی:</b>\n`;

    let total = 0;
    const portions = sData.portions || {};
    for (const [key, count] of Object.entries(portions)) {
      const food = FOODS[key];
      if (food) {
        const itemTotal = (food.price_num || 300000) * count;
        total += itemTotal;
        invoice += ` • ${food.title} × ${toPersianDigits(count)} پرس = ${formatPrice(itemTotal)}\n`;
      }
    }

    invoice += `\n💰 <b>مجموع قابل پرداخت:</b> <b>${formatPrice(total)}</b>\n\nآیا سفارش غذا را تأیید می‌فرمایید؟`;
    sData.totalAmount = total;
    await setSession(ctx, userId, "FOOD_CONFIRM_AWAIT", sData);

    return await editMessage(ctx, chatId, messageId, invoice, {
      reply_markup: foodConfirmKeyboard()
    });
  }

  if (data === "food_confirm_final") {
    await answerCallback(ctx, queryId, "سفارش غذا ثبت شد!", false);
    const session = await getSession(ctx, userId);
    const sData = session.data || {};

    let orderList = "";
    const portions = sData.portions || {};
    for (const [key, count] of Object.entries(portions)) {
      const food = FOODS[key];
      if (food) {
        orderList += ` • ${food.title} × ${toPersianDigits(count)} پرس\n`;
      }
    }

    const adminMessage = `🍲 <b>سفارش غذای جدید ثبت شد:</b>\n\n` +
      `👤 مهمان: <b>${sData.guestName}</b>\n` +
      `📞 تلفن: <code>${sData.phone}</code>\n` +
      `🛏 اتاق: <b>${sData.roomName}</b>\n` +
      `📅 تاریخ سرو: <b>${sData.mealWeekday} ${toPersianDigits(sData.mealDate)}</b>\n` +
      `☀️ وعده: <b>${sData.mealType === "lunch" ? "ناهار" : "شام"}</b>\n` +
      `🍴 اقلام:\n${orderList}` +
      `📝 یادداشت پخت: <i>${sData.notes || "ندارد"}</i>\n` +
      `💰 مبلغ کل: <b>${formatPrice(sData.totalAmount)}</b>`;

    const token = (ctx && ctx.env && ctx.env.BOT_TOKEN) || BOT_TOKEN;
    if (token && ADMIN_CHAT_ID) {
      await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: ADMIN_CHAT_ID,
          text: adminMessage,
          parse_mode: "HTML"
        })
      });
    }

    await clearSession(ctx, userId);

    const guestConfirmation = `🍲 <b>سفارش غذای شما با موفقیت ثبت شد!</b>\n\n` +
      `مطبخ اقامتگاه خانه برزک با افتخار در تدارک میزبانی از شما خواهد بود. وعده ${sData.mealType === "lunch" ? "ناهار" : "شام"} شما در تاریخ ${toPersianDigits(sData.mealDate)} با عشق آماده خواهد شد.\n\nنوش جان و اقامتتان سرشار از آرامش 🌿`;

    return await editMessage(ctx, chatId, messageId, guestConfirmation, {
      reply_markup: backToMainKeyboard()
    });
  }

  return await answerCallback(ctx, queryId);
}
