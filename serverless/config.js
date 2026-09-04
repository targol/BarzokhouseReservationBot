// config.js - تنظیمات اقامتگاه بومگردی خانه برزک برای ربات سرورلس تلگرام
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function loadJson(filename, fallback) {
  try {
    const filePath = path.join(__dirname, filename);
    if (fs.existsSync(filePath)) {
      const data = JSON.parse(fs.readFileSync(filePath, "utf-8"));
      if (data && typeof data === "object") return data;
    }
  } catch (e) {
    console.warn(`Could not load ${filename}:`, e.message);
  }
  return fallback;
}

export const BOT_TOKEN = process.env.BOT_TOKEN || "";
export const ADMIN_CHAT_ID = process.env.ADMIN_CHAT_ID ? Number(process.env.ADMIN_CHAT_ID) : -1004485664573;

export const ROOMS = loadJson("rooms.json", {
  shatoot: {
    title: "اتاق شاتوت",
    description: "مناسب برای ۲ نفر.\nدر خانه جدید، امکانات: تخت دونفره، پنکه، بخاری گازی، سرویس بهداشتی ایرانی و حمام اختصاصی داخل اتاق.",
    price: "۱,۳۰۰,۰۰۰ تومان / اقامت و صبحانه هر نفرشب",
    price_per_person: 1300000,
    photo: "rooms_photos/shatoot.webp"
  },
  ghali: {
    title: "اتاق قالی",
    description: "مناسب برای ۳ نفر.\nدر خانه جدید، امکانات: یک تخت دونفره و یک تخت یک نفره، پنکه، بخاری گازی، سرویس بهداشتی فرنگی و حمام اختصاصی داخل اتاق.",
    price: "۱,۳۰۰,۰۰۰ تومان / اقامت و صبحانه هر نفرشب",
    price_per_person: 1300000,
    photo: "rooms_photos/ghali.webp"
  },
  abi: {
    title: "اتاق آبی",
    description: "مناسب برای ۲ نفر.\nدر خانه قدیم، دارای امکانات: رختخواب، پنکه، بخاری گازی، سرویس بهداشتی ایرانی و حمام اختصاصی داخل اتاق.",
    price: "۱,۳۰۰,۰۰۰ تومان / اقامت و صبحانه هر نفرشب",
    price_per_person: 1300000,
    photo: "rooms_photos/abi.webp"
  },
  sara: {
    title: "اتاق سرا",
    description: "بزرگ‌ترین اتاق مجموعه، مناسب خانواده‌ها تا ۱۰ نفر.\nدر خانه قدیم، دارای امکانات: یک تخت دو نفر، یک تخت یک نفره و رختخواب، پنکه، بخاری گازی و برقی، سرویس بهداشتی فرنگی و حمام اختصاصی داخل اتاق.",
    price: "۱,۳۰۰,۰۰۰ تومان / اقامت و صبحانه هر نفرشب",
    price_per_person: 1300000,
    photo: "rooms_photos/sara.webp"
  },
  balakhooneh: {
    title: "اتاق بالاخونه",
    description: "اتاقی در طبقه بالا با چشم‌انداز باغ و کوه، مناسب برای ۳ نفر.\nدر خانه قدیم، دارای امکانات: یک تخت دو نفر، یک تخت یک نفره و رختخواب، دارای پنکه، بخاری گازی، سرویس بهداشتی و حمام اختصاصی ندارد.",
    price: "۱,۲۰۰,۰۰۰ تومان / اقامت و صبحانه هر نفرشب",
    price_per_person: 1200000,
    photo: "rooms_photos/balakhooneh.webp"
  }
});

export const FOODS = loadJson("foods.json", {
  gheimeh_rizegi: {
    title: "خورش قیمه ریزه برزک",
    description: "غذای اصیل و سنتی برزک با گوشت چرخ‌کرده تازه، آرد نخودچی، سبزیجات معطر کوهستانی و رب گوجه همراه با برنج اعلای ایرانی.",
    price: "۳۸۰,۰۰۰ تومان",
    price_num: 380000,
    available_meals: ["lunch", "dinner"]
  },
  kashk_bademjan: {
    title: "کشک بادمجان محلی",
    description: "بادمجان کبابی تازه با گردوی خردشده باغ‌های برزک، نعناع‌داغ، سیرداغ و کشک اعلا همراه با نان محلی برزک.",
    price: "۲۹۰,۰۰۰ تومان",
    price_num: 290000,
    available_meals: ["lunch", "dinner"]
  },
  kaljoosh: {
    title: "کالجوش سنتی برزک",
    description: "غذای گرم و مقوی محلی با کشک سنتی، گردوی فراوان باغ‌های برزک، پیازداغ و نعناع تازه.",
    price: "۲۶۰,۰۰۰ تومان",
    price_num: 260000,
    available_meals: ["lunch", "dinner"]
  },
  dizi: {
    title: "دیزی سنتی هیزمی",
    description: "گوشت گوسفندی تازه، نخود و لوبیا، دنبه، گوجه و سیب‌زمینی همراه با نان سنتی، پیاز و ترشی خانگی.",
    price: "۴۵۰,۰۰۰ تومان",
    price_num: 450000,
    available_meals: ["lunch"]
  },
  zereshk_polo: {
    title: "زرشک‌پلو با مرغ زعفرانی",
    description: "خوراک ران مرغ سس‌پز زعفرانی با برنج ممتاز ایرانی، زرشک تازه و خلال پسته و بادام.",
    price: "۳۵۰,۰۰۰ تومان",
    price_num: 350000,
    available_meals: ["lunch", "dinner"]
  }
});

export const WELCOME_MESSAGE = `🏡 به اقامتگاه بومگردی «خانه برزک» خوش آمدید!

ما باور داریم که هر خانه‌ای که انسان در آن نباشد، بی‌روح است. خانه برزک خانه‌ای قدیمی است که زمانی با وجود آدم‌ها و خانواده‌ها، زندگی در آن جریان داشت. امروز خانه برزک با حضور مهمان‌هایش زنده است و هر روز روح جدیدی در آن دمیده می‌شود.

از منوی زیر می‌توانید اطلاعات بیشتری ببینید یا اتاق مورد نظر خود را رزرو کنید 👇`;

export const ADDRESS_TEXT = `📍 آدرس:
در ۴۵ کیلومتری کاشان، برزک، خانه (روحانی) برزک

برای مشاهده روی نقشه، لوکیشن زیر رو ببین 👇`;

export const LOCATION_LATITUDE = 33.78286576513508;
export const LOCATION_LONGITUDE = 51.22924918495417;

export const CONTACT_TEXT = `📞 تماس با ما:
09334868840
09125472055`;

export const SOCIAL_TEXT = `🌐 سایت و شبکه‌های اجتماعی:

🌐 barzokhouse.com
✈️ @barzokhouselodge
📸 instagram.com/barzokhouse`;

export const WEBSITE_URL = "https://barzokhouse.com";
export const TELEGRAM_URL = "https://t.me/barzokhouselodge";
export const INSTAGRAM_URL = "https://instagram.com/barzokhouse";
export const PAYMENT_URL = "https://packpay.ir/barzokhouse";

export const HOUSE_RULES_TEXT = `🙏 سلام
از اینکه خانه برزک را برای اقامت خود انتخاب کرده‌اید، خوشحالیم و مشتاق دیدار شما هستیم.

برای اینکه اقامت راحت‌تر و لذت‌بخش‌تری داشته باشید، لطفاً پیش از سفر نگاهی به موارد زیر بیندازید؛ مطالعه آن کمتر از ۳ دقیقه زمان می‌برد.

🏡 <b>آشنایی با خانه برزک</b>
اطلاعات اتاق‌ها، امکانات، مسیر دسترسی و سایر اطلاعات موردنیاز را در سایت مشاهده کنید:
<a href="https://barzokhouse.com/%D9%85%D8%B4%D8%A7%D9%87%D8%AF%D9%87-%D8%A7%D8%AA%D8%A7%D9%82-%D9%87%D8%A7">مشاهده مشخصات اتاق‌ها</a>

📋 <b>چند نکته پیش از اقامت</b>
برای اینکه همه مهمانان اقامت آرام و دلپذیری داشته باشند، لطفاً شرایط را مطالعه فرمایید:
<a href="https://barzokhouse.com/%d8%b4%d8%b1%d8%a7%db%8c%d8%b7-%d8%ae%d8%a7%d9%86%d9%87-%d9%88-%d9%88%d8%b1%d9%88%d8%af-%d9%85%d9%87%d9%85%d8%a7%d9%86/">شرایط خانه و ورود مهمان</a>

🌤 <b>آب‌وهوای برزک</b>
<a href="https://www.accuweather.com/en/ir/azaran/208117/weather-forecast/208117?type=place&placename=barzok%20house">مشاهده وضعیت هوا</a>

🌿 <b>سفر سبز به خانه برزک</b>
<a href="https://barzokhouse.com/green-eco-lodge/">اصول سفر سازگار با طبیعت</a>

اگر پیش از سفر سؤال یا ابهامی داشتید، با کمال میل پاسخگوی شما هستیم.
به امید دیدار شما در خانه برزک 🌿`;
