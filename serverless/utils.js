// utils.js - توابع کمکی تبدیل اعداد، فرمت قیمت و محاسبات تقویم شمسی برای ربات سرورلس

export function toEnglishDigits(str) {
  if (!str) return "";
  const persianDigits = ["۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"];
  const arabicDigits = ["٠", "١", "٢", "٣", "٤", "٥", "٦", "٧", "٨", "٩"];
  let res = String(str);
  for (let i = 0; i < 10; i++) {
    res = res.replaceAll(persianDigits[i], String(i)).replaceAll(arabicDigits[i], String(i));
  }
  return res;
}

export function toPersianDigits(num) {
  if (num === null || num === undefined) return "";
  const persianDigits = ["۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"];
  return String(num).replace(/\d/g, (d) => persianDigits[parseInt(d, 10)]);
}

export function formatPrice(amount) {
  if (!amount && amount !== 0) return "۰ تومان";
  const formatted = String(amount).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return `${toPersianDigits(formatted)} تومان`;
}

// الگوریتم تبدیل تاریخ جلالی (شمسی) به میلادی
export function jalaliToGregorian(jy, jm, jd) {
  let gy = (jy <= 979) ? 621 : 1600;
  jy -= (jy <= 979) ? 0 : 979;
  let days = (365 * jy) + ((Math.floor(jy / 33)) * 8) + (Math.floor(((jy % 33) + 3) / 4)) + 78 + jd + ((jm < 7) ? (jm - 1) * 31 : (((jm - 7) * 30) + 186));
  gy += 400 * Math.floor(days / 146097);
  days %= 146097;
  if (days > 36524) {
    gy += 100 * Math.floor(--days / 36524);
    days %= 36524;
    if (days >= 365) days++;
  }
  gy += 4 * Math.floor(days / 1461);
  days %= 1461;
  if (days > 365) {
    gy += Math.floor((days - 1) / 365);
    days = (days - 1) % 365;
  }
  let gd = days + 1;
  const sal_a = [0, 31, ((gy % 4 === 0 && gy % 100 !== 0) || (gy % 400 === 0)) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  let gm;
  for (gm = 0; gm < 13 && gd > sal_a[gm]; gm++) gd -= sal_a[gm];
  return { gy, gm, gd };
}

export const PERSIAN_WEEKDAYS = [
  "یک‌شنبه",
  "دوشنبه",
  "سه‌شنبه",
  "چهارشنبه",
  "پنج‌شنبه",
  "جمعه",
  "شنبه"
];

export function parseJalaliDate(rawText) {
  if (!rawText) return null;
  const text = toEnglishDigits(rawText.trim());
  const parts = text.replace(/-/g, "/").split("/");
  if (parts.length !== 3) return null;
  const y = parseInt(parts[0], 10);
  const m = parseInt(parts[1], 10);
  const d = parseInt(parts[2], 10);
  if (isNaN(y) || isNaN(m) || isNaN(d)) return null;
  if (m < 1 || m > 12 || d < 1 || d > 31) return null;

  try {
    const { gy, gm, gd } = jalaliToGregorian(y, m, d);
    const dateObj = new Date(Date.UTC(gy, gm - 1, gd));
    const weekday = PERSIAN_WEEKDAYS[dateObj.getUTCDay()];
    return {
      year: y,
      month: m,
      day: d,
      weekday,
      formatted: `${y}/${String(m).padStart(2, "0")}/${String(d).padStart(2, "0")}`,
      dateObj
    };
  } catch (err) {
    return null;
  }
}
