// handlers/message.js - پردازش پیام‌های متنی، دستورات و رسانه‌ها در تلگرام سرورلس
import {
  BOT_TOKEN,
  ADMIN_CHAT_ID,
  WELCOME_MESSAGE,
  ROOMS,
  FOODS
} from "../config.js";
import {
  mainMenuKeyboard,
  bookingRoomsSelectionKeyboard,
  bookingFinalConfirmKeyboard,
  foodMealSelectionKeyboard,
  foodNotesKeyboard,
  foodConfirmKeyboard
} from "../keyboards.js";
import {
  toEnglishDigits,
  toPersianDigits,
  formatPrice,
  parseJalaliDate
} from "../utils.js";
import { getSession, setSession, clearSession } from "../db.js";

async function sendMessage(ctx, chatId, text, options = {}) {
  if (ctx && ctx.api && typeof ctx.api.sendMessage === "function") {
    return await ctx.api.sendMessage(chatId, text, { parse_mode: "HTML", ...options });
  }
  const token = (ctx && ctx.env && ctx.env.BOT_TOKEN) || BOT_TOKEN;
  if (!token) throw new Error("BOT_TOKEN is missing");
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

export default async function handleMessage(payload, ctx) {
  const msg = payload?.message || payload;
  if (!msg) return;

  const chatId = msg.chat?.id;
  const userId = msg.from?.id;
  const text = msg.text?.trim();

  if (!chatId || !userId) return;

  // ۱. دستور شروع /start
  if (text === "/start") {
    await clearSession(ctx, userId);
    return await sendMessage(ctx, chatId, WELCOME_MESSAGE, {
      reply_markup: mainMenuKeyboard()
    });
  }

  // ۲. دستور انصراف /cancel
  if (text === "/cancel") {
    await clearSession(ctx, userId);
    return await sendMessage(
      ctx,
      chatId,
      "❌ عملیات جاری لغو شد.\nبرای دسترسی به بخش‌های مختلف از منوی زیر استفاده کنید:",
      { reply_markup: mainMenuKeyboard() }
    );
  }

  // ۳. دستور مستقیم سفارش غذا /food
  if (text === "/food") {
    await setSession(ctx, userId, "FOOD_ASK_GUEST_NAME", {});
    return await sendMessage(
      ctx,
      chatId,
      "🍽 <b>سفارش غذای اقامتگاه خانه برزک</b>\n\nلطفاً نام و نام خانوادگی مهمان اصلی را وارد فرمایید:"
    );
  }

  // ۴. دریافت فیش واریزی (عکس)
  if (msg.photo && msg.photo.length > 0) {
    const largestPhoto = msg.photo[msg.photo.length - 1];
    const caption = `💳 <b>رسید واریز ارسال‌شده از مهمان:</b>\n👤 نام کاربری: @${msg.from.username || "ندارد"}\n🆔 شناسه: <code>${userId}</code>\n📝 نام: ${msg.from.first_name || ""} ${msg.from.last_name || ""}`;
    
    // ارسال به ادمین
    const token = (ctx && ctx.env && ctx.env.BOT_TOKEN) || BOT_TOKEN;
    if (token && ADMIN_CHAT_ID) {
      await fetch(`https://api.telegram.org/bot${token}/sendPhoto`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: ADMIN_CHAT_ID,
          photo: largestPhoto.file_id,
          caption,
          parse_mode: "HTML"
        })
      });
    }

    return await sendMessage(
      ctx,
      chatId,
      "✅ رسید واریزی شما با موفقیت دریافت شد و برای مدیریت اقامتگاه ارسال گردید.\nپس از بررسی، نتیجه به اطلاع شما خواهد رسید.\nسپاس از همراهی شما 🌿",
      { reply_markup: mainMenuKeyboard() }
    );
  }

  // ۵. بررسی وضعیت مکالمه و سناریوها
  const session = await getSession(ctx, userId);
  const state = session.state;
  const data = session.data || {};

  if (!state) {
    // پیام عمومی خارج از مکالمه
    return await sendMessage(
      ctx,
      chatId,
      "برای راهنمایی و استفاده از خدمات خانه برزک لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
      { reply_markup: mainMenuKeyboard() }
    );
  }

  // --- مراحل رزرو اقامتگاه ---
  if (state === "BOOKING_ASK_NAME") {
    data.guestName = text;
    await setSession(ctx, userId, "BOOKING_ASK_PHONE", data);
    return await sendMessage(
      ctx,
      chatId,
      `متشکرم ${text} عزیز 🌿\n\nلطفاً <b>شماره تماس همراه</b> خود را وارد فرمایید (جهت ارسال پیامک و هماهنگی نهایی):`
    );
  }

  if (state === "BOOKING_ASK_PHONE") {
    data.phone = toEnglishDigits(text);
    await setSession(ctx, userId, "BOOKING_ASK_CHECKIN", data);
    return await sendMessage(
      ctx,
      chatId,
      "📅 لطفاً <b>تاریخ ورود</b> خود را به‌صورت شمسی وارد فرمایید:\n(مثال: ۱۴۰۴/۰۶/۱۵ یا 1404/6/15)"
    );
  }

  if (state === "BOOKING_ASK_CHECKIN") {
    const parsed = parseJalaliDate(text);
    if (!parsed) {
      return await sendMessage(
        ctx,
        chatId,
        "⚠️ تاریخ وارد شده نامعتبر است.\nلطفاً تاریخ را به صورت سال/ماه/روز وارد کنید (مثال: <b>۱۴۰۴/۰۶/۱۵</b>):"
      );
    }
    data.checkinDate = parsed.formatted;
    data.checkinWeekday = parsed.weekday;
    await setSession(ctx, userId, "BOOKING_ASK_DURATION", data);
    return await sendMessage(
      ctx,
      chatId,
      `تاریخ ورود شما: <b>${parsed.weekday} ${toPersianDigits(parsed.formatted)}</b> ثبت شد.\n\nچند شب اقامت خواهید داشت؟ (لطفاً فقط یک عدد وارد فرمایید، مثلاً: ۱ یا ۲):`
    );
  }

  if (state === "BOOKING_ASK_DURATION") {
    const nights = parseInt(toEnglishDigits(text), 10);
    if (isNaN(nights) || nights < 1) {
      return await sendMessage(
        ctx,
        chatId,
        "⚠️ لطفاً تعداد شب را به صورت عدد بزرگتر از صفر وارد فرمایید (مثال: ۱ یا ۲):"
      );
    }
    data.duration = nights;
    data.selectedRooms = data.selectedRooms || [];
    await setSession(ctx, userId, "BOOKING_SELECT_ROOMS", data);
    return await sendMessage(
      ctx,
      chatId,
      "🛏 <b>انتخاب اتاق‌ها (تک یا چند اتاقه):</b>\n\nشما می‌توانید یک یا چند اتاق را با لمس گزینه‌ها علامت بزنید و سپس دکمه تأیید را لمس نمایید 👇",
      { reply_markup: bookingRoomsSelectionKeyboard(data.selectedRooms) }
    );
  }

  if (state === "BOOKING_ASK_NOTES") {
    data.notes = text;
    await setSession(ctx, userId, "BOOKING_CONFIRM_AWAIT", data);

    // محاسبه قیمت کل
    let perNightBase = 0;
    const roomTitles = (data.selectedRooms || []).map((k) => ROOMS[k]?.title || k);
    for (const k of data.selectedRooms || []) {
      perNightBase += ROOMS[k]?.price_per_person || 1300000;
    }

    const adults = data.adults || 1;
    const kids12 = data.kids5to12 || 0;
    const kids5 = data.kidsUnder5 || 0;
    const nights = data.duration || 1;

    const basePerPerson = (data.selectedRooms && data.selectedRooms.length > 0)
      ? Math.round(perNightBase / data.selectedRooms.length)
      : 1300000;

    const adultTotal = adults * basePerPerson * nights;
    const kid12Total = Math.round(kids12 * basePerPerson * 0.5 * nights);
    const totalAmount = adultTotal + kid12Total;

    data.totalAmount = totalAmount;
    await setSession(ctx, userId, "BOOKING_CONFIRM_AWAIT", data);

    const invoiceText = `📋 <b>پیش‌فاکتور و خلاصه درخواست رزرو:</b>\n` +
      `👤 مهمان: <b>${data.guestName}</b>\n` +
      `📞 شماره تماس: <code>${data.phone}</code>\n` +
      `📅 تاریخ ورود: <b>${data.checkinWeekday} ${toPersianDigits(data.checkinDate)}</b>\n` +
      `🌙 مدت اقامت: <b>${toPersianDigits(nights)} شب</b>\n` +
      `🛏 اتاق‌های انتخابی: <b>${roomTitles.join(" + ")}</b>\n` +
      `👥 تفکیک مهمانان:\n` +
      `  • بزرگسال: ${toPersianDigits(adults)} نفر\n` +
      `  • کودک ۵ تا ۱۲ سال (نیم‌بها): ${toPersianDigits(kids12)} نفر\n` +
      `  • کودک زیر ۵ سال (رایگان): ${toPersianDigits(kids5)} نفر\n` +
      `📝 ملاحظات خاص: <i>${data.notes || "ندارد"}</i>\n\n` +
      `💰 <b>مبلغ کل قابل پرداخت:</b> <b>${formatPrice(totalAmount)}</b>\n\n` +
      `آیا اطلاعات بالا را تأیید می‌فرمایید؟`;

    return await sendMessage(ctx, chatId, invoiceText, {
      reply_markup: bookingFinalConfirmKeyboard()
    });
  }

  // --- مراحل سفارش غذا ---
  if (state === "FOOD_ASK_GUEST_NAME") {
    data.guestName = text;
    await setSession(ctx, userId, "FOOD_ASK_PHONE", data);
    return await sendMessage(
      ctx,
      chatId,
      `متشکرم ${text} عزیز 🌿\n\nلطفاً <b>شماره تماس همراه</b> خود را وارد فرمایید:`
    );
  }

  if (state === "FOOD_ASK_PHONE") {
    data.phone = toEnglishDigits(text);
    await setSession(ctx, userId, "FOOD_ASK_ROOM", data);
    return await sendMessage(
      ctx,
      chatId,
      "🛏 لطفاً نام اتاقی که در آن اقامت دارید یا نام ثبت‌شده در رزرو را وارد فرمایید (مثال: اتاق شاتوت):"
    );
  }

  if (state === "FOOD_ASK_ROOM") {
    data.roomName = text;
    await setSession(ctx, userId, "FOOD_ASK_DATE", data);
    return await sendMessage(
      ctx,
      chatId,
      "📅 تاریخ سرو غذا را به‌صورت شمسی وارد فرمایید (مثال: <b>۱۴۰۴/۰۶/۱۵</b>):"
    );
  }

  if (state === "FOOD_ASK_DATE") {
    const parsed = parseJalaliDate(text);
    if (!parsed) {
      return await sendMessage(
        ctx,
        chatId,
        "⚠️ تاریخ وارد شده نامعتبر است.\nلطفاً تاریخ را به صورت سال/ماه/روز وارد کنید (مثال: ۱۴۰۴/۰۶/۱۵):"
      );
    }
    data.mealDate = parsed.formatted;
    data.mealWeekday = parsed.weekday;
    await setSession(ctx, userId, "FOOD_ASK_MEAL", data);
    return await sendMessage(
      ctx,
      chatId,
      `تاریخ انتخابی: <b>${parsed.weekday} ${toPersianDigits(parsed.formatted)}</b>\n\nکدام وعده مد نظر شماست؟ 👇`,
      { reply_markup: foodMealSelectionKeyboard() }
    );
  }

  if (state === "FOOD_ASK_PORTION_CUSTOM") {
    const portions = parseInt(toEnglishDigits(text), 10);
    if (isNaN(portions) || portions < 1) {
      return await sendMessage(ctx, chatId, "⚠️ لطفاً یک عدد معتبر بزرگتر از صفر وارد فرمایید:");
    }
    const currentFood = data.currentFoodKey;
    if (currentFood) {
      data.portions = data.portions || {};
      data.portions[currentFood] = portions;
    }
    await setSession(ctx, userId, "FOOD_ASK_NOTES", data);
    return await sendMessage(
      ctx,
      chatId,
      `تعداد ${toPersianDigits(portions)} پرس ثبت شد.\n\nآیا یادداشت، حساسیت غذایی یا ملاحظات خاصی در پخت دارید؟\nدر صورت تمایل بنویسید یا دکمه «رد شدن» را لمس کنید 👇`,
      { reply_markup: foodNotesKeyboard() }
    );
  }

  if (state === "FOOD_ASK_NOTES") {
    data.notes = text;
    await setSession(ctx, userId, "FOOD_CONFIRM_AWAIT", data);

    let invoice = `🍲 <b>پیش‌فاکتور سفارش غذا:</b>\n` +
      `👤 مهمان: <b>${data.guestName}</b>\n` +
      `📞 شماره تماس: <code>${data.phone}</code>\n` +
      `🛏 اتاق / رزرو: <b>${data.roomName}</b>\n` +
      `📅 تاریخ: <b>${data.mealWeekday} ${toPersianDigits(data.mealDate)}</b>\n` +
      `☀️ وعده: <b>${data.mealType === "lunch" ? "ناهار" : "شام"}</b>\n\n` +
      `🍴 <b>اقلام انتخابی:</b>\n`;

    let total = 0;
    const portions = data.portions || {};
    for (const [key, count] of Object.entries(portions)) {
      const food = FOODS[key];
      if (food) {
        const itemTotal = (food.price_num || 300000) * count;
        total += itemTotal;
        invoice += ` • ${food.title} × ${toPersianDigits(count)} پرس = ${formatPrice(itemTotal)}\n`;
      }
    }

    invoice += `\n📝 ملاحظات پخت: <i>${data.notes || "ندارد"}</i>\n\n` +
      `💰 <b>مجموع قابل پرداخت:</b> <b>${formatPrice(total)}</b>\n\n` +
      `آیا سفارش غذا را تأیید می‌فرمایید؟`;

    data.totalAmount = total;
    await setSession(ctx, userId, "FOOD_CONFIRM_AWAIT", data);

    return await sendMessage(ctx, chatId, invoice, {
      reply_markup: foodConfirmKeyboard()
    });
  }

  // در سایر حالت‌ها، منوی اصلی را نمایش بده
  return await sendMessage(
    ctx,
    chatId,
    "برای راهنمایی از منوی زیر استفاده فرمایید:",
    { reply_markup: mainMenuKeyboard() }
  );
}
