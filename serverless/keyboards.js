// keyboards.js - تعریف کیبوردهای شیشه‌ای تعاملی ربات سرورلس
import { ROOMS, FOODS, PAYMENT_URL } from "./config.js";
import { toPersianDigits, formatPrice } from "./utils.js";

export function mainMenuKeyboard() {
  return {
    inline_keyboard: [
      [{ text: "🛏 اتاق‌ها و رزرو اقامت", callback_data: "menu_rooms" }],
      [{ text: "🍽 منوی غذا و سفارش خوراک", callback_data: "menu_food" }],
      [{ text: "📜 اطلاعاتی درباره اقامتگاه", callback_data: "menu_rules" }],
      [{ text: "📍 آدرس و لوکیشن", callback_data: "menu_address" }],
      [{ text: "📞 تماس با ما", callback_data: "menu_contact" }],
      [{ text: "🌐 سایت و شبکه‌های اجتماعی", callback_data: "menu_social" }],
      [{ text: "💳 پرداخت آنلاین", callback_data: "menu_payment" }],
      [{ text: "⭐ ثبت تجربه شما", callback_data: "menu_review" }]
    ]
  };
}

export function backToMainKeyboard() {
  return {
    inline_keyboard: [
      [{ text: "⬅️ بازگشت به منوی اصلی", callback_data: "back_main" }]
    ]
  };
}

export function socialLinksKeyboard() {
  return {
    inline_keyboard: [
      [
        { text: "🌐 وب‌سایت", url: "https://barzokhouse.com" },
        { text: "✈️ تلگرام", url: "https://t.me/barzokhouselodge" },
        { text: "📸 اینستاگرام", url: "https://instagram.com/barzokhouse" }
      ],
      [{ text: "⬅️ بازگشت به منوی اصلی", callback_data: "back_main" }]
    ]
  };
}

export function roomsListKeyboard() {
  const rows = [];
  for (const [key, room] of Object.entries(ROOMS)) {
    rows.push([{ text: room.title, callback_data: `room_${key}` }]);
  }
  rows.push([{ text: "✨ رزرو اقامتگاه (تک یا چند اتاقه)", callback_data: "book_start_direct" }]);
  rows.push([{ text: "⬅️ بازگشت به منوی اصلی", callback_data: "back_main" }]);
  return { inline_keyboard: rows };
}

export function roomDetailKeyboard(roomKey) {
  return {
    inline_keyboard: [
      [{ text: "✅ درخواست رزرو این اتاق", callback_data: `book_${roomKey}` }],
      [{ text: "⬅️ بازگشت به لیست اتاق‌ها", callback_data: "menu_rooms" }]
    ]
  };
}

export function bookingRoomsSelectionKeyboard(selectedKeys = []) {
  const rows = [];
  for (const [key, room] of Object.entries(ROOMS)) {
    const isSelected = selectedKeys.includes(key);
    const mark = isSelected ? "✅ " : "⬜ ";
    const priceText = formatPrice(room.price_per_person).replace(" تومان", "");
    rows.push([{
      text: `${mark}${room.title} (${priceText})`,
      callback_data: `selroom_${key}`
    }]);
  }

  if (selectedKeys.length > 0) {
    rows.push([{
      text: `➡️ تأیید و رفتن به مرحله بعد (${toPersianDigits(selectedKeys.length)} اتاق)`,
      callback_data: "selroom_done"
    }]);
  }

  rows.push([{ text: "❌ انصراف از رزرو", callback_data: "book_cancel" }]);
  return { inline_keyboard: rows };
}

export function ageCountersKeyboard(adults = 1, kids5to12 = 0, kidsUnder5 = 0) {
  return {
    inline_keyboard: [
      [
        { text: "➖", callback_data: "guest_adult_dec" },
        { text: `بزرگسال: ${toPersianDigits(adults)} نفر`, callback_data: "ignore" },
        { text: "➕", callback_data: "guest_adult_inc" }
      ],
      [
        { text: "➖", callback_data: "guest_kid12_dec" },
        { text: `کودک ۵ تا ۱۲ سال (نیم‌بها): ${toPersianDigits(kids5to12)} نفر`, callback_data: "ignore" },
        { text: "➕", callback_data: "guest_kid12_inc" }
      ],
      [
        { text: "➖", callback_data: "guest_kid5_dec" },
        { text: `کودک زیر ۵ سال (رایگان): ${toPersianDigits(kidsUnder5)} نفر`, callback_data: "ignore" },
        { text: "➕", callback_data: "guest_kid5_inc" }
      ],
      [
        { text: "✅ تأیید تعداد نفرات و ادامه ➡️", callback_data: "guests_confirmed" }
      ],
      [
        { text: "❌ انصراف", callback_data: "book_cancel" }
      ]
    ]
  };
}

export function bookingFinalConfirmKeyboard() {
  return {
    inline_keyboard: [
      [{ text: "✅ تأیید و ارسال درخواست نهایی", callback_data: "book_confirm_final" }],
      [{ text: "✏️ ویرایش توضیحات یا یادداشت", callback_data: "book_edit_notes" }],
      [{ text: "❌ انصراف از رزرو", callback_data: "book_cancel" }]
    ]
  };
}

export function foodMenuKeyboard() {
  const rows = [];
  for (const [key, food] of Object.entries(FOODS)) {
    rows.push([{ text: `${food.title} - ${food.price}`, callback_data: `finfo_${key}` }]);
  }
  rows.push([{ text: "🍲 ثبت سفارش غذا (ناهار / شام)", callback_data: "food_order_start" }]);
  rows.push([{ text: "⬅️ بازگشت به منوی اصلی", callback_data: "back_main" }]);
  return { inline_keyboard: rows };
}

export function foodMealSelectionKeyboard() {
  return {
    inline_keyboard: [
      [
        { text: "☀️ وعده ناهار", callback_data: "meal_lunch" },
        { text: "🌙 وعده شام", callback_data: "meal_dinner" }
      ],
      [{ text: "❌ انصراف از سفارش", callback_data: "food_cancel_order" }]
    ]
  };
}

export function foodSelectionKeyboard(mealType, selectedKeys = []) {
  const rows = [];
  for (const [key, food] of Object.entries(FOODS)) {
    if (food.available_meals && !food.available_meals.includes(mealType)) {
      continue;
    }
    const isSelected = selectedKeys.includes(key);
    const mark = isSelected ? "✅ " : "⬜ ";
    rows.push([{
      text: `${mark}${food.title} (${food.price})`,
      callback_data: `fsel_${key}`
    }]);
  }

  if (selectedKeys.length > 0) {
    rows.push([{
      text: `➡️ مرحله بعد: تعیین تعداد پرس (${toPersianDigits(selectedKeys.length)} غذا)`,
      callback_data: "food_finalize"
    }]);
  }

  rows.push([{ text: "❌ انصراف از سفارش", callback_data: "food_cancel_order" }]);
  return { inline_keyboard: rows };
}

export function foodPortionsKeyboard(currentCount = 1) {
  return {
    inline_keyboard: [
      [
        { text: "۱ پرس", callback_data: "fportion_1" },
        { text: "۲ پرس", callback_data: "fportion_2" },
        { text: "۳ پرس", callback_data: "fportion_3" }
      ],
      [
        { text: "۴ پرس", callback_data: "fportion_4" },
        { text: "۵ پرس", callback_data: "fportion_5" },
        { text: "۶ پرس", callback_data: "fportion_6" }
      ],
      [
        { text: "تعداد دیگر (ارسال عدد در پیام)", callback_data: "fportion_custom" }
      ],
      [
        { text: "❌ انصراف", callback_data: "food_cancel_order" }
      ]
    ]
  };
}

export function foodNotesKeyboard() {
  return {
    inline_keyboard: [
      [{ text: "⏩ رد شدن و بدون یادداشت", callback_data: "food_skip_notes" }],
      [{ text: "⬅️ بازگشت و اصلاح غذاها", callback_data: "food_back_to_items" }],
      [{ text: "❌ انصراف از سفارش", callback_data: "food_cancel_order" }]
    ]
  };
}

export function foodConfirmKeyboard() {
  return {
    inline_keyboard: [
      [{ text: "✅ تأیید و ثبت نهایی سفارش غذا", callback_data: "food_confirm_final" }],
      [{ text: "❌ انصراف", callback_data: "food_cancel_order" }]
    ]
  };
}
