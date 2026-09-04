import React, { useState, useEffect, useRef } from 'react';
import { FoodItem, RoomItem, BookedRoomItem } from './types';
import { INITIAL_FOODS, INITIAL_ROOMS } from './data';
import {
  UtensilsCrossed,
  BedDouble,
  FileCode2,
  Plus,
  Trash2,
  Edit2,
  CheckCircle2,
  Send,
  Calendar,
  Clock,
  User,
  Phone,
  Copy,
  Check,
  Calculator,
  Baby,
  Users,
  Moon,
  Sun,
  Home,
  ShieldCheck,
  Download,
  Upload,
  RotateCcw,
  FileJson,
  Save,
  HardDrive,
  FileText,
  Heart,
  Tag,
  GitBranch,
  ExternalLink,
  FolderArchive,
  Zap,
} from 'lucide-react';

export default function App() {
  // بارگذاری داده‌ها از حافظه مرورگر برای جلوگیری از بازنشانی اطلاعات کاربر
  const [foods, setFoods] = useState<FoodItem[]>(() => {
    try {
      const saved = localStorage.getItem('barzok_custom_foods');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch (e) {
      console.error('Error loading foods from localStorage', e);
    }
    return INITIAL_FOODS;
  });

  const [rooms, setRooms] = useState<RoomItem[]>(() => {
    try {
      const saved = localStorage.getItem('barzok_custom_rooms');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch (e) {
      console.error('Error loading rooms from localStorage', e);
    }
    return INITIAL_ROOMS;
  });

  // ذخیره خودکار هرگونه تغییر در اتاق‌ها و غذاها در حافظه مرورگر (ماندگاری دائمی)
  useEffect(() => {
    try {
      localStorage.setItem('barzok_custom_foods', JSON.stringify(foods));
    } catch (e) {
      console.error('Error saving foods to localStorage', e);
    }
  }, [foods]);

  useEffect(() => {
    try {
      localStorage.setItem('barzok_custom_rooms', JSON.stringify(rooms));
    } catch (e) {
      console.error('Error saving rooms to localStorage', e);
    }
  }, [rooms]);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [activeTab, setActiveTab] = useState<'booking-sim' | 'food-sim' | 'foods' | 'rooms' | 'code' | 'serverless'>('booking-sim');
  const [copied, setCopied] = useState(false);
  const [copiedRelease, setCopiedRelease] = useState(false);
  const [copiedGitCmds, setCopiedGitCmds] = useState(false);
  const [copiedTgCloud, setCopiedTgCloud] = useState(false);
  const [selectedServerlessFile, setSelectedServerlessFile] = useState<'message' | 'callback' | 'config' | 'db' | 'readme'>('readme');
  const [backupNotice, setBackupNotice] = useState<string | null>(null);

  // توابع پشتیبان‌گیری و بارگذاری داده‌ها
  const handleExportBackup = () => {
    const backupData = {
      version: 1,
      exportDate: new Date().toISOString(),
      rooms,
      foods,
    };
    const blob = new Blob([JSON.stringify(backupData, null, 2)], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `barzok_house_backup_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showNotice('فایل پشتیبان کامل با موفقیت دانلود شد.');
  };

  const handleDownloadRoomsJson = () => {
    const roomsDict: Record<string, any> = {};
    rooms.forEach((r) => {
      roomsDict[r.id] = {
        title: r.title,
        description: r.description,
        price: r.price,
        price_per_person: r.pricePerPerson || 1300000,
        photo: r.photo || `rooms_photos/${r.id}.webp`,
      };
    });
    const blob = new Blob([JSON.stringify(roomsDict, null, 2)], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'rooms.json';
    a.click();
    URL.revokeObjectURL(url);
    showNotice('فایل rooms.json مخصوص ربات پایتون دانلود شد.');
  };

  const handleDownloadFoodsJson = () => {
    const foodsDict: Record<string, any> = {};
    foods.forEach((f) => {
      foodsDict[f.id] = {
        title: f.title,
        description: f.description,
        price: f.price,
        available_meals: f.availableMeals,
      };
    });
    const blob = new Blob([JSON.stringify(foodsDict, null, 2)], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'foods.json';
    a.click();
    URL.revokeObjectURL(url);
    showNotice('فایل foods.json مخصوص ربات پایتون دانلود شد.');
  };

  const handleImportBackup = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const parsed = JSON.parse(event.target?.result as string);
        if (parsed.rooms && Array.isArray(parsed.rooms)) {
          setRooms(parsed.rooms);
        }
        if (parsed.foods && Array.isArray(parsed.foods)) {
          setFoods(parsed.foods);
        }
        showNotice('اطلاعات پشتیبان با موفقیت وارد و در حافظه ذخیره شد.');
      } catch (err) {
        alert('خطا در خواندن فایل JSON پشتیبان.');
      }
    };
    reader.readAsText(file);
    e.target.value = '';
  };

  const handleResetToDefaults = () => {
    if (window.confirm('آیا مطمئن هستید که می‌خواهید لیست اتاق‌ها و غذاها را به حالت اولیه بازنشانی کنید؟')) {
      setFoods(INITIAL_FOODS);
      setRooms(INITIAL_ROOMS);
      localStorage.removeItem('barzok_custom_foods');
      localStorage.removeItem('barzok_custom_rooms');
      showNotice('اطلاعات به داده‌های پیش‌فرض بازنشانی شد.');
    }
  };

  const showNotice = (msg: string) => {
    setBackupNotice(msg);
    setTimeout(() => setBackupNotice(null), 3500);
  };

  // شبیه‌ساز رزرو اتاق
  const [bookingGuestName, setBookingGuestName] = useState('علیرضا احمدی');
  const [bookingPhone, setBookingPhone] = useState('09123456789');
  const [bookingCheckin, setBookingCheckin] = useState('۱۴۰۴/۰۲/۱۵');
  const [bookingNights, setBookingNights] = useState<number>(2);
  const [bookedRooms, setBookedRooms] = useState<BookedRoomItem[]>([
    {
      roomId: 'shatoot',
      title: 'اتاق شاتوت',
      pricePerPerson: 1300000,
      adults: 2,
      children5to12: 1,
      childrenUnder5: 1,
    },
    {
      roomId: 'ghali',
      title: 'اتاق قالی',
      pricePerPerson: 1300000,
      adults: 2,
      children5to12: 0,
      childrenUnder5: 0,
    },
  ]);
  const [selectedRoomToAdd, setSelectedRoomToAdd] = useState<string>('abi');
  const [bookingNotes, setBookingNotes] = useState(
    'پدربزرگ همراه ماست و توانایی بالارفتن از پله ندارد؛ ترجیحاً اتاق طبقه همکف باشد. همچنین رژیم غذایی کم‌نمک دارند.'
  );
  const [bookingConfirmed, setBookingConfirmed] = useState(false);

  // شبیه‌ساز سفارش غذا
  const [simGuestName, setSimGuestName] = useState('علیرضا احمدی');
  const [simPhone, setSimPhone] = useState('09123456789');
  const [simRoom, setSimRoom] = useState('اتاق شاتوت');
  const [simWeekday, setSimWeekday] = useState('پنج‌شنبه');
  const [simDate, setSimDate] = useState('۱۴۰۴/۰۲/۱۶');
  const [simMeal, setSimMeal] = useState<'lunch' | 'dinner'>('lunch');
  const [selectedFoodIds, setSelectedFoodIds] = useState<{ [id: string]: number }>({
    gheimeh_rizegi: 2,
    kashk_bademjan: 1,
  });
  const [simFoodNotes, setSimFoodNotes] = useState(
    'قیمه ریزگی کم‌روغن باشد. حساسیت به فلفل تند داریم و ساعت سرو حدود ۱۳:۳۰ تنظیم گردد.'
  );
  const [foodOrderSent, setFoodOrderSent] = useState(false);

  // فرم‌های ویرایش
  const [editingFood, setEditingFood] = useState<FoodItem | null>(null);
  const [editingRoom, setEditingRoom] = useState<RoomItem | null>(null);

  // توابع محاسبات رزرو
  const calcRoomSubtotal = (r: BookedRoomItem) => {
    const adultCost = r.adults * r.pricePerPerson;
    const childCost = r.children5to12 * (r.pricePerPerson * 0.5);
    return bookingNights * (adultCost + childCost);
  };

  const totalBookingCost = bookedRooms.reduce((acc, curr) => acc + calcRoomSubtotal(curr), 0);
  const totalAdults = bookedRooms.reduce((acc, curr) => acc + curr.adults, 0);
  const totalKids512 = bookedRooms.reduce((acc, curr) => acc + curr.children5to12, 0);
  const totalKidsU5 = bookedRooms.reduce((acc, curr) => acc + curr.childrenUnder5, 0);

  const formatPrice = (amount: number) => {
    return amount.toLocaleString('fa-IR') + ' تومان';
  };

  const handleAddRoomToBooking = () => {
    const target = rooms.find((r) => r.id === selectedRoomToAdd);
    if (!target) return;
    setBookedRooms((prev) => [
      ...prev,
      {
        roomId: target.id,
        title: target.title,
        pricePerPerson: target.pricePerPerson || 1300000,
        adults: 2,
        children5to12: 0,
        childrenUnder5: 0,
      },
    ]);
  };

  const handleRemoveRoomFromBooking = (index: number) => {
    setBookedRooms((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpdateGuestCount = (
    index: number,
    field: 'adults' | 'children5to12' | 'childrenUnder5',
    delta: number
  ) => {
    setBookedRooms((prev) => {
      const copy = [...prev];
      const target = { ...copy[index] };
      const current = target[field];
      const minVal = field === 'adults' ? 1 : 0;
      const nextVal = Math.max(minVal, current + delta);
      target[field] = nextVal;
      copy[index] = target;
      return copy;
    });
  };

  // توابع سفارش غذا
  const toggleFoodSelect = (foodId: string) => {
    setSelectedFoodIds((prev) => {
      const next = { ...prev };
      if (next[foodId]) {
        delete next[foodId];
      } else {
        const count = Object.keys(next).length;
        if (count >= 2) {
          alert('در هر سفارش حداکثر مجاز به انتخاب ۲ نوع غذا هستید.');
          return prev;
        }
        next[foodId] = 1;
      }
      return next;
    });
  };

  const updatePortions = (foodId: string, delta: number) => {
    setSelectedFoodIds((prev) => {
      const current = prev[foodId] || 1;
      const nextVal = current + delta;
      if (nextVal <= 0) {
        const copy = { ...prev };
        delete copy[foodId];
        return copy;
      }
      return { ...prev, [foodId]: nextVal };
    });
  };

  const generateConfigPySnippet = () => {
    const foodDictEntries = foods
      .map(
        (f) => `    "${f.id}": {
        "title": "${f.title}",
        "description": "${f.description}",
        "price": "${f.price}",
        "available_meals": [${f.availableMeals.map((m) => `"${m}"`).join(', ')}],
    },`
      )
      .join('\n');

    const roomDictEntries = rooms
      .map(
        (r) => `    "${r.id}": {
        "title": "${r.title}",
        "description": "${r.description}",
        "price": "${r.price}",
        "price_per_person": ${r.pricePerPerson || 1300000},
    },`
      )
      .join('\n');

    return `# ==========================================
# FOODS & ROOMS CONFIG FOR config.py
# ==========================================

MAX_FOOD_SELECTIONS = 2
CHILD_5_12_DISCOUNT_FACTOR = 0.5   # ۵ تا ۱۲ سال نیم‌بها
CHILD_UNDER_5_DISCOUNT_FACTOR = 0.0 # زیر ۵ سال رایگان

ROOMS = {
${roomDictEntries}
}

FOODS = {
${foodDictEntries}
}`;
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(generateConfigPySnippet());
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-stone-50 text-stone-800 font-sans antialiased flex flex-col" dir="rtl">
      {/* Header */}
      <header id="main-header" className="bg-stone-900 text-stone-100 border-b border-stone-800 px-6 py-4 shadow-sm">
        <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-600/20 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <Home className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-bold text-lg text-stone-100 tracking-tight">پنل مدیریت و شبیه‌ساز ربات خانه برزک</h1>
              <p className="text-xs text-stone-400">رزرو چند اتاقه، برآورد هزینه رده‌های سنی، منوی غذا و سفارش ناهار/شام</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav id="top-nav" className="flex items-center gap-1 bg-stone-800/80 p-1 rounded-xl border border-stone-700 overflow-x-auto">
            <button
              id="tab-booking-sim-btn"
              onClick={() => setActiveTab('booking-sim')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5 shrink-0 ${
                activeTab === 'booking-sim' ? 'bg-amber-600 text-white shadow-xs' : 'text-stone-300 hover:text-white'
              }`}
            >
              <BedDouble className="w-3.5 h-3.5" />
              شبیه‌ساز رزرو چند اتاقه
            </button>
            <button
              id="tab-food-sim-btn"
              onClick={() => setActiveTab('food-sim')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5 shrink-0 ${
                activeTab === 'food-sim' ? 'bg-amber-600 text-white shadow-xs' : 'text-stone-300 hover:text-white'
              }`}
            >
              <UtensilsCrossed className="w-3.5 h-3.5" />
              شبیه‌ساز سفارش غذا
            </button>
            <button
              id="tab-foods-btn"
              onClick={() => setActiveTab('foods')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5 shrink-0 ${
                activeTab === 'foods' ? 'bg-amber-600 text-white shadow-xs' : 'text-stone-300 hover:text-white'
              }`}
            >
              منوی غذاها ({foods.length})
            </button>
            <button
              id="tab-rooms-btn"
              onClick={() => setActiveTab('rooms')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5 shrink-0 ${
                activeTab === 'rooms' ? 'bg-amber-600 text-white shadow-xs' : 'text-stone-300 hover:text-white'
              }`}
            >
              اتاق‌ها و نرخ‌ها ({rooms.length})
            </button>
            <button
              id="tab-code-btn"
              onClick={() => setActiveTab('code')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5 shrink-0 ${
                activeTab === 'code' ? 'bg-amber-600 text-white shadow-xs' : 'text-stone-300 hover:text-white'
              }`}
            >
              <FileCode2 className="w-3.5 h-3.5" />
              کدهای config.py
            </button>
            <button
              id="tab-serverless-btn"
              onClick={() => setActiveTab('serverless')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5 shrink-0 ${
                activeTab === 'serverless' ? 'bg-emerald-600 text-white shadow-xs' : 'text-emerald-400 hover:text-white bg-emerald-950/40 border border-emerald-700/50'
              }`}
            >
              <Zap className="w-3.5 h-3.5" />
              نسخه بدون سرور (Serverless)
            </button>
          </nav>
        </div>
      </header>

      {/* Data Protection & Backup Bar */}
      <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-2.5">
        <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-stone-700">
            <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0"></span>
            <span className="font-semibold text-stone-800">ماندگاری داده‌ها:</span>
            <span>تغییرات اتاق‌ها و غذاها در حافظه محلی مرورگر شما ذخیره شده و با ویرایش کد بازنویسی نمی‌شوند.</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleExportBackup}
              className="px-2.5 py-1 rounded-lg bg-white border border-stone-300 text-stone-700 hover:bg-stone-50 font-medium transition flex items-center gap-1.5 shadow-xs"
              title="دانلود فایل نسخه پشتیبان JSON"
            >
              <Download className="w-3.5 h-3.5 text-stone-500" />
              دانلود پشتیبان (JSON)
            </button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleImportBackup}
              accept=".json"
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-2.5 py-1 rounded-lg bg-white border border-stone-300 text-stone-700 hover:bg-stone-50 font-medium transition flex items-center gap-1.5 shadow-xs"
              title="بارگذاری فایل نسخه پشتیبان JSON"
            >
              <Upload className="w-3.5 h-3.5 text-stone-500" />
              بارگذاری پشتیبان
            </button>
            <button
              onClick={handleResetToDefaults}
              className="px-2 py-1 rounded-lg text-stone-400 hover:text-stone-600 hover:bg-stone-200/50 transition flex items-center gap-1"
              title="بازنشانی اطلاعات به مقادیر اولیه"
            >
              <RotateCcw className="w-3 h-3" />
              بازنشانی
            </button>
          </div>
        </div>
      </div>

      {backupNotice && (
        <div className="bg-emerald-600 text-white text-xs px-4 py-2 text-center shadow-md animate-fade-in">
          {backupNotice}
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 max-w-6xl w-full mx-auto p-4 sm:p-6 space-y-6">
        {/* =========================================================
            TAB 1: MULTI-ROOM BOOKING SIMULATOR & COST ESTIMATOR
           ========================================================= */}
        {activeTab === 'booking-sim' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Col: Interactive Booking Form */}
            <div className="lg:col-span-6 space-y-4">
              <div className="bg-white rounded-2xl border border-stone-200 p-5 shadow-xs">
                <div className="flex items-center justify-between pb-3 mb-4 border-b border-stone-100">
                  <div className="flex items-center gap-2">
                    <BedDouble className="w-4 h-4 text-amber-600" />
                    <h2 className="text-sm font-bold text-stone-900">تنظیمات رزرو و انتخاب اتاق‌ها</h2>
                  </div>
                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-medium">
                    پشتیبانی از چند اتاق همزمان
                  </span>
                </div>

                <div className="space-y-3 text-xs">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block font-medium text-stone-700 mb-1">نام مهمان</label>
                      <div className="flex items-center gap-2 border border-stone-300 rounded-xl px-2.5 py-1.5 bg-stone-50">
                        <User className="w-3.5 h-3.5 text-stone-400" />
                        <input
                          type="text"
                          value={bookingGuestName}
                          onChange={(e) => setBookingGuestName(e.target.value)}
                          className="w-full bg-transparent focus:outline-hidden text-xs"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block font-medium text-stone-700 mb-1">شماره تماس</label>
                      <div className="flex items-center gap-2 border border-stone-300 rounded-xl px-2.5 py-1.5 bg-stone-50">
                        <Phone className="w-3.5 h-3.5 text-stone-400" />
                        <input
                          type="text"
                          value={bookingPhone}
                          onChange={(e) => setBookingPhone(e.target.value)}
                          className="w-full bg-transparent focus:outline-hidden text-xs"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block font-medium text-stone-700 mb-1">تاریخ ورود</label>
                      <div className="flex items-center gap-2 border border-stone-300 rounded-xl px-2.5 py-1.5 bg-stone-50">
                        <Calendar className="w-3.5 h-3.5 text-stone-400" />
                        <input
                          type="text"
                          value={bookingCheckin}
                          onChange={(e) => setBookingCheckin(e.target.value)}
                          className="w-full bg-transparent focus:outline-hidden text-xs"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block font-medium text-stone-700 mb-1">مدت اقامت (تعداد شب)</label>
                      <div className="flex items-center gap-2 border border-stone-300 rounded-xl px-2.5 py-1.5 bg-stone-50">
                        <Moon className="w-3.5 h-3.5 text-stone-400" />
                        <input
                          type="number"
                          min={1}
                          max={30}
                          value={bookingNights}
                          onChange={(e) => setBookingNights(Math.max(1, parseInt(e.target.value) || 1))}
                          className="w-full bg-transparent focus:outline-hidden text-xs font-bold text-amber-800"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Rooms in Booking */}
                <div className="mt-5 pt-4 border-t border-stone-100">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-xs font-bold text-stone-900">اتاق‌های انتخاب شده ({bookedRooms.length} اتاق)</label>
                    <span className="text-[11px] text-stone-500">تفکیک رده‌های سنی به ازای هر اتاق</span>
                  </div>

                  <div className="space-y-3">
                    {bookedRooms.map((r, idx) => (
                      <div key={idx} className="p-3.5 rounded-xl border border-stone-200 bg-stone-50/70 space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="w-5 h-5 rounded-full bg-amber-100 text-amber-800 font-bold text-[11px] flex items-center justify-center">
                              {idx + 1}
                            </span>
                            <span className="font-bold text-xs text-stone-900">{r.title}</span>
                            <span className="text-[11px] text-stone-500 font-normal">
                              ({(r.pricePerPerson).toLocaleString('fa-IR')} تومان هر نفرشب)
                            </span>
                          </div>
                          <button
                            onClick={() => handleRemoveRoomFromBooking(idx)}
                            className="p-1 text-stone-400 hover:text-rose-600 hover:bg-rose-50 rounded transition"
                            title="حذف این اتاق"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>

                        {/* Guest Breakdown Selectors */}
                        <div className="grid grid-cols-3 gap-2 text-center text-xs">
                          {/* Adults */}
                          <div className="bg-white p-2 rounded-lg border border-stone-200">
                            <span className="block text-[11px] font-medium text-stone-600 mb-1 flex items-center justify-center gap-1">
                              <Users className="w-3 h-3 text-stone-500" />
                              بزرگسال
                            </span>
                            <div className="flex items-center justify-center gap-2">
                              <button
                                onClick={() => handleUpdateGuestCount(idx, 'adults', -1)}
                                className="w-5 h-5 rounded bg-stone-100 text-stone-700 font-bold hover:bg-stone-200 text-xs"
                              >
                                -
                              </button>
                              <span className="font-bold text-stone-900 w-4">{r.adults}</span>
                              <button
                                onClick={() => handleUpdateGuestCount(idx, 'adults', 1)}
                                className="w-5 h-5 rounded bg-stone-100 text-stone-700 font-bold hover:bg-stone-200 text-xs"
                              >
                                +
                              </button>
                            </div>
                            <span className="block text-[10px] text-stone-400 mt-0.5">تمام بها</span>
                          </div>

                          {/* Children 5-12 */}
                          <div className="bg-amber-50/50 p-2 rounded-lg border border-amber-200">
                            <span className="block text-[11px] font-medium text-amber-900 mb-1 flex items-center justify-center gap-1">
                              <Baby className="w-3 h-3 text-amber-700" />
                              کودک ۵ تا ۱۲
                            </span>
                            <div className="flex items-center justify-center gap-2">
                              <button
                                onClick={() => handleUpdateGuestCount(idx, 'children5to12', -1)}
                                className="w-5 h-5 rounded bg-white text-stone-700 font-bold hover:bg-amber-100 text-xs border border-amber-300"
                              >
                                -
                              </button>
                              <span className="font-bold text-amber-900 w-4">{r.children5to12}</span>
                              <button
                                onClick={() => handleUpdateGuestCount(idx, 'children5to12', 1)}
                                className="w-5 h-5 rounded bg-white text-stone-700 font-bold hover:bg-amber-100 text-xs border border-amber-300"
                              >
                                +
                              </button>
                            </div>
                            <span className="block text-[10px] font-bold text-amber-700 mt-0.5">نیم‌بها (۵۰٪)</span>
                          </div>

                          {/* Children Under 5 */}
                          <div className="bg-emerald-50/50 p-2 rounded-lg border border-emerald-200">
                            <span className="block text-[11px] font-medium text-emerald-900 mb-1 flex items-center justify-center gap-1">
                              <Baby className="w-3 h-3 text-emerald-700" />
                              کودک زیر ۵ سال
                            </span>
                            <div className="flex items-center justify-center gap-2">
                              <button
                                onClick={() => handleUpdateGuestCount(idx, 'childrenUnder5', -1)}
                                className="w-5 h-5 rounded bg-white text-stone-700 font-bold hover:bg-emerald-100 text-xs border border-emerald-300"
                              >
                                -
                              </button>
                              <span className="font-bold text-emerald-900 w-4">{r.childrenUnder5}</span>
                              <button
                                onClick={() => handleUpdateGuestCount(idx, 'childrenUnder5', 1)}
                                className="w-5 h-5 rounded bg-white text-stone-700 font-bold hover:bg-emerald-100 text-xs border border-emerald-300"
                              >
                                +
                              </button>
                            </div>
                            <span className="block text-[10px] font-bold text-emerald-700 mt-0.5">رایگان (۰ تومان)</span>
                          </div>
                        </div>

                        {/* Room Subtotal */}
                        <div className="flex items-center justify-between pt-2 border-t border-stone-200/80 text-[11px]">
                          <span className="text-stone-500">
                            هزینه این اتاق برای {bookingNights} شب:
                          </span>
                          <span className="font-bold text-stone-800">
                            {formatPrice(calcRoomSubtotal(r))}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Add Another Room Button */}
                  <div className="mt-4 flex items-center gap-2">
                    <select
                      value={selectedRoomToAdd}
                      onChange={(e) => setSelectedRoomToAdd(e.target.value)}
                      className="flex-1 px-3 py-2 text-xs rounded-xl border border-stone-300 bg-white focus:outline-hidden focus:border-amber-500"
                    >
                      {rooms.map((rm) => (
                        <option key={rm.id} value={rm.id}>
                          {rm.title} ({rm.price})
                        </option>
                      ))}
                    </select>
                    <button
                      onClick={handleAddRoomToBooking}
                      className="px-3.5 py-2 bg-stone-800 hover:bg-stone-900 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition shrink-0"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      افزودن اتاق دیگر
                    </button>
                  </div>

                  {/* Notes & Special Requests */}
                  <div className="mt-4 pt-3 border-t border-stone-200">
                    <label className="block font-medium text-stone-800 mb-1 text-xs flex items-center justify-between">
                      <span className="flex items-center gap-1.5 font-bold">
                        <FileText className="w-3.5 h-3.5 text-amber-600" />
                        توضیحات و ملاحظات خاص (ملاحظه غذایی، دسترس‌پذیری سالمند/کودک و...)
                      </span>
                      <span className="text-[10px] text-stone-400 font-normal">اختیاری</span>
                    </label>
                    <textarea
                      rows={2}
                      value={bookingNotes}
                      onChange={(e) => setBookingNotes(e.target.value)}
                      placeholder="مثال: ترجیح اتاق همکف، عدم توانایی بالا رفتن از پله برای سالمند، رژیم غذایی کم‌نمک یا گیاهی، تخت اضافه..."
                      className="w-full px-3 py-2 text-xs rounded-xl border border-stone-300 bg-stone-50 focus:bg-white focus:outline-hidden focus:border-amber-500 leading-relaxed"
                    />
                  </div>
                </div>

                <button
                  onClick={() => setBookingConfirmed(true)}
                  className="w-full mt-4 py-2.5 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-semibold shadow-sm transition flex items-center justify-center gap-2 cursor-pointer"
                >
                  <Send className="w-3.5 h-3.5" />
                  ثبت رزرو و صدور پیش‌نمایش تلگرام
                </button>
              </div>

              {/* Rules & Discount Info Card */}
              <div className="p-4 rounded-2xl bg-amber-50/70 border border-amber-200/80 text-xs text-amber-900 space-y-2">
                <div className="flex items-center gap-1.5 font-bold text-amber-950">
                  <ShieldCheck className="w-4 h-4 text-amber-700" />
                  قوانین محاسبه نرخ سنین در ربات خانه برزک:
                </div>
                <ul className="list-disc list-inside space-y-1 text-[11px] text-amber-800 leading-relaxed pr-1">
                  <li><b>بزرگسالان:</b> محاسبه با نرخ کامل مصوب هر نفرشب اقامت به همراه صبحانه محلی.</li>
                  <li><b>کودکان ۵ تا ۱۲ سال:</b> با ضریب تخفیف ۵۰٪ (نیم‌بها) محاسبه می‌گردند.</li>
                  <li><b>کودکان زیر ۵ سال:</b> به صورت کاملاً رایگان (بدون هزینه اقامت) پذیرش می‌شوند.</li>
                  <li><b>امکان رزرو چند اتاق:</b> مهمان می‌تواند در یک درخواست، چندین اتاق مختلف را با تفکیک دقیق سنین مهمانان رزرو نماید.</li>
                </ul>
              </div>
            </div>

            {/* Right Col: Real-time Cost Breakdown & Telegram Message */}
            <div className="lg:col-span-6 space-y-4">
              {/* Cost Calculation Summary Card */}
              <div className="bg-white rounded-2xl border border-stone-200 p-5 shadow-xs space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-stone-100">
                  <h3 className="text-xs font-bold text-stone-900 flex items-center gap-1.5">
                    <Calculator className="w-4 h-4 text-amber-600" />
                    خلاصه برآورد اولیه هزینه اقامت
                  </h3>
                  <span className="text-[11px] text-stone-500 font-medium">
                    مدت اقامت: {bookingNights} شب
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="p-2.5 rounded-xl bg-stone-50 border border-stone-100">
                    <span className="text-[11px] text-stone-500 block">مجموع بزرگسالان</span>
                    <span className="text-sm font-bold text-stone-800">{totalAdults} نفر</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-amber-50/60 border border-amber-100">
                    <span className="text-[11px] text-amber-700 block">کودکان ۵ تا ۱۲ سال</span>
                    <span className="text-sm font-bold text-amber-900">{totalKids512} نفر (نیم‌بها)</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-emerald-50/60 border border-emerald-100">
                    <span className="text-[11px] text-emerald-700 block">کودکان زیر ۵ سال</span>
                    <span className="text-sm font-bold text-emerald-900">{totalKidsU5} نفر (رایگان)</span>
                  </div>
                </div>

                <div className="pt-3 border-t border-stone-100 space-y-2 text-xs">
                  {bookedRooms.map((r, i) => (
                    <div key={i} className="flex items-center justify-between text-stone-600">
                      <span>• {r.title} ({r.adults} بزرگسال، {r.children5to12} کودک ۵-۱۲، {r.childrenUnder5} زیر ۵):</span>
                      <span className="font-semibold text-stone-800">{formatPrice(calcRoomSubtotal(r))}</span>
                    </div>
                  ))}
                </div>

                <div className="p-3.5 rounded-xl bg-stone-900 text-stone-100 flex items-center justify-between">
                  <div>
                    <span className="text-[11px] text-stone-400 block">مبلغ کل برآورد اولیه:</span>
                    <span className="text-sm font-extrabold text-amber-400">
                      {formatPrice(totalBookingCost)}
                    </span>
                  </div>
                  <span className="text-[11px] text-stone-400 border border-stone-700 px-2 py-1 rounded-lg">
                    {bookedRooms.length} اتاق / {bookingNights} شب
                  </span>
                </div>
              </div>

              {/* Telegram Message Preview Sent to Admin */}
              <div className="bg-stone-900 text-stone-100 rounded-2xl p-5 border border-stone-800 shadow-md space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-stone-800">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span className="text-xs font-bold text-stone-200">پیش‌نمایش پیام ارسالی به مدیر تلگرام (ADMIN_CHAT_ID)</span>
                  </div>
                  <span className="text-[11px] text-stone-400">خروجی زنده ربات</span>
                </div>

                <div className="bg-stone-800/90 rounded-xl p-4 border border-stone-700/60 font-mono text-xs leading-relaxed space-y-2 text-stone-200">
                  <p className="text-amber-400 font-bold">🔔 <b>درخواست رزرو جدید اقامتگاه</b></p>
                  <div className="space-y-1 pt-1 border-t border-stone-700 text-[12px]">
                    <p>👤 <b>نام:</b> {bookingGuestName}</p>
                    <p>📞 <b>شماره تماس:</b> {bookingPhone}</p>
                    <p>📅 <b>تاریخ ورود:</b> {bookingCheckin}</p>
                    <p>🌙 <b>مدت اقامت:</b> {bookingNights} شب</p>
                    <p>🛏 <b>تعداد اتاق‌ها:</b> {bookedRooms.length} اتاق</p>
                    <p>👥 <b>مجموع مهمانان:</b> {totalAdults} بزرگسال | {totalKids512} کودک ۵-۱۲ (نیم‌بها) | {totalKidsU5} زیر ۵ سال (رایگان)</p>
                  </div>

                  <div className="pt-2 border-t border-stone-700">
                    <p className="text-amber-300 font-semibold mb-1">📋 اتاق‌های درخواستی و تفکیک نفرات:</p>
                    {bookedRooms.map((r, i) => (
                      <p key={i} className="text-stone-300 pr-2">
                        {i + 1}. <b>{r.title}</b>: {r.adults} بزرگسال، {r.children5to12} کودک ۵-۱۲، {r.childrenUnder5} زیر ۵ سال (برآورد: {formatPrice(calcRoomSubtotal(r))})
                      </p>
                    ))}
                  </div>

                  <div className="pt-2 border-t border-stone-700">
                    <p className="text-emerald-400 font-bold">
                      💰 <b>مبلغ کل برآورد اولیه:</b> {formatPrice(totalBookingCost)}
                    </p>
                  </div>

                  <div className="pt-2 border-t border-stone-700">
                    <p className="text-amber-300 font-semibold mb-1">📝 توضیحات و ملاحظات مهمان:</p>
                    <p className="text-stone-200 pr-2 bg-stone-900/60 p-2 rounded-lg border border-stone-700/50">
                      {bookingNotes.trim() ? bookingNotes : 'ندارد'}
                    </p>
                  </div>

                  <p className="text-stone-400 pt-1 text-[11px]">🆔 آیدی تلگرام: @guest_telegram_id</p>
                </div>

                {/* Warm & Friendly Guest Confirmation Message */}
                <div className="bg-stone-800/80 rounded-xl p-4 border border-amber-600/40 text-xs space-y-2">
                  <div className="flex items-center gap-2 text-amber-300 font-bold pb-2 border-b border-stone-700">
                    <Heart className="w-4 h-4 text-rose-400 fill-rose-400" />
                    <span>پیام گرم و صمیمانه تاییدیه ارسالی به مهمان</span>
                  </div>
                  <div className="space-y-2 text-stone-200 leading-relaxed">
                    <p className="font-bold text-amber-200 text-sm">🏡 درخواست رزرو شما با موفقیت ثبت شد!</p>
                    <p className="text-amber-100 font-semibold bg-amber-950/40 p-2.5 rounded-lg border border-amber-800/40">
                      🌿 <b>خانواده اقامتگاه بوم‌گردی خانه برزک، با تمام وجود و از صمیم قلب منتظر دیدارتون تو خونهٔ خودتون هست!</b>
                    </p>
                    <p className="text-stone-300 text-[11px]">
                      امیدواریم روزهایی سرشار از آرامش، عطر گلاب، چای آتشی و خنده‌های به‌یادماندنی در کوچه باغ‌های باصفای برزک در کنار هم داشته باشیم. دلتون شاد و قدمتون پیشاپیش به روی چشم 🌸☕️
                    </p>
                    {bookingNotes.trim() && (
                      <p className="text-stone-300 text-[11px] pt-1">
                        📝 <b>ملاحظات ثبت‌شده شما:</b> {bookingNotes}
                      </p>
                    )}
                  </div>
                </div>

                {bookingConfirmed && (
                  <div className="p-3 bg-emerald-950/60 border border-emerald-700/50 rounded-xl flex items-center gap-2 text-emerald-300 text-xs">
                    <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
                    <span>خلاصه رزرو و پیام خوش‌آمدگویی با موفقیت ثبت و ارسال شد.</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* =========================================================
            TAB 2: FOOD ORDERING SIMULATOR
           ========================================================= */}
        {activeTab === 'food-sim' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Col: Food Order Form */}
            <div className="lg:col-span-5 space-y-4">
              <div className="bg-white rounded-2xl border border-stone-200 p-5 shadow-xs space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-stone-100">
                  <h2 className="text-sm font-bold text-stone-900 flex items-center gap-2">
                    <UtensilsCrossed className="w-4 h-4 text-amber-600" />
                    شبیه‌ساز سفارش غذا و خوراک
                  </h2>
                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 font-medium">
                    سقف ۲ نوع غذا
                  </span>
                </div>

                <div className="space-y-3 text-xs">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block font-medium text-stone-700 mb-1">نام مهمان</label>
                      <input
                        type="text"
                        value={simGuestName}
                        onChange={(e) => setSimGuestName(e.target.value)}
                        className="w-full px-3 py-2 text-xs rounded-xl border border-stone-300 bg-stone-50 focus:bg-white focus:outline-hidden focus:border-amber-500"
                      />
                    </div>
                    <div>
                      <label className="block font-medium text-stone-700 mb-1">شماره تماس</label>
                      <input
                        type="text"
                        value={simPhone}
                        onChange={(e) => setSimPhone(e.target.value)}
                        className="w-full px-3 py-2 text-xs rounded-xl border border-stone-300 bg-stone-50 focus:bg-white focus:outline-hidden focus:border-amber-500"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block font-medium text-stone-700 mb-1">اتاق اقامت</label>
                      <select
                        value={simRoom}
                        onChange={(e) => setSimRoom(e.target.value)}
                        className="w-full px-3 py-2 text-xs rounded-xl border border-stone-300 bg-stone-50 focus:bg-white focus:outline-hidden focus:border-amber-500"
                      >
                        {rooms.map((r) => (
                          <option key={r.id} value={r.title}>
                            {r.title}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block font-medium text-stone-700 mb-1">وعده غذایی</label>
                      <div className="grid grid-cols-2 gap-1 bg-stone-100 p-1 rounded-xl">
                        <button
                          type="button"
                          onClick={() => setSimMeal('lunch')}
                          className={`py-1 text-xs font-medium rounded-lg transition ${
                            simMeal === 'lunch' ? 'bg-amber-600 text-white shadow-xs' : 'text-stone-600'
                          }`}
                        >
                          ☀️ ناهار
                        </button>
                        <button
                          type="button"
                          onClick={() => setSimMeal('dinner')}
                          className={`py-1 text-xs font-medium rounded-lg transition ${
                            simMeal === 'dinner' ? 'bg-amber-600 text-white shadow-xs' : 'text-stone-600'
                          }`}
                        >
                          🌙 شام
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block font-medium text-stone-700 mb-1">روز هفته اقامت</label>
                      <select
                        value={simWeekday}
                        onChange={(e) => setSimWeekday(e.target.value)}
                        className="w-full px-3 py-2 text-xs rounded-xl border border-stone-300 bg-stone-50 focus:bg-white focus:outline-hidden focus:border-amber-500"
                      >
                        {['شنبه', 'یک‌شنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه'].map((d) => (
                          <option key={d} value={d}>
                            {d}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block font-medium text-stone-700 mb-1">تاریخ سرو غذا</label>
                      <input
                        type="text"
                        value={simDate}
                        onChange={(e) => setSimDate(e.target.value)}
                        className="w-full px-3 py-2 text-xs rounded-xl border border-stone-300 bg-stone-50 focus:bg-white focus:outline-hidden focus:border-amber-500"
                      />
                    </div>
                  </div>

                  {/* Food Selection with Limit 2 */}
                  <div className="pt-2">
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="text-xs font-semibold text-stone-700">
                        انتخاب غذاها برای {simMeal === 'lunch' ? 'ناهار' : 'شام'}
                      </label>
                      <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 font-medium">
                        حداکثر ۲ نوع غذا ({Object.keys(selectedFoodIds).length} / ۲ انتخاب‌شده)
                      </span>
                    </div>

                    <div className="space-y-2 mt-2 max-h-56 overflow-y-auto pr-1">
                      {foods
                        .filter((f) => f.availableMeals.includes(simMeal))
                        .map((food) => {
                          const isSelected = selectedFoodIds[food.id] !== undefined;
                          const portions = selectedFoodIds[food.id] || 0;
                          return (
                            <div
                              key={food.id}
                              className={`p-2.5 rounded-xl border transition flex items-center justify-between gap-3 ${
                                isSelected
                                  ? 'border-amber-500 bg-amber-50/50'
                                  : 'border-stone-200 bg-stone-50 hover:border-stone-300'
                              }`}
                            >
                              <div className="flex-1 cursor-pointer" onClick={() => toggleFoodSelect(food.id)}>
                                <p className="text-xs font-semibold text-stone-800">{food.title}</p>
                                <p className="text-[11px] text-amber-700 font-medium">{food.price}</p>
                              </div>

                              {isSelected ? (
                                <div className="flex items-center gap-1.5 bg-white border border-amber-300 rounded-lg px-1 py-0.5">
                                  <button
                                    onClick={() => updatePortions(food.id, -1)}
                                    className="w-5 h-5 flex items-center justify-center text-xs font-bold text-stone-600 hover:bg-stone-100 rounded"
                                  >
                                    -
                                  </button>
                                  <span className="text-xs font-bold w-6 text-center text-amber-800">{portions} پرس</span>
                                  <button
                                    onClick={() => updatePortions(food.id, 1)}
                                    className="w-5 h-5 flex items-center justify-center text-xs font-bold text-stone-600 hover:bg-stone-100 rounded"
                                  >
                                    +
                                  </button>
                                </div>
                              ) : (
                                <button
                                  onClick={() => toggleFoodSelect(food.id)}
                                  className="px-2.5 py-1 text-xs rounded-lg border border-stone-300 bg-white hover:border-amber-500 hover:text-amber-700 font-medium"
                                >
                                  افزودن
                                </button>
                              )}
                            </div>
                          );
                        })}
                    </div>
                  </div>

                  {/* Food Notes / Special Requests */}
                  <div className="mt-3 pt-3 border-t border-stone-200">
                    <label className="block font-medium text-stone-800 mb-1 text-xs flex items-center justify-between">
                      <span className="flex items-center gap-1.5 font-bold">
                        <FileText className="w-3.5 h-3.5 text-amber-600" />
                        توضیحات و ملاحظات غذا (حساسیت، رژیم خاص، میزان تندی/نمک، ساعت سرو)
                      </span>
                      <span className="text-[10px] text-stone-400 font-normal">اختیاری</span>
                    </label>
                    <textarea
                      rows={2}
                      value={simFoodNotes}
                      onChange={(e) => setSimFoodNotes(e.target.value)}
                      placeholder="مثال: غذای کم‌روغن یا بدون فلفل، حساسیت به گلوتن، ساعت سرو ناهار راس ۱۳:۳۰..."
                      className="w-full px-3 py-2 text-xs rounded-xl border border-stone-300 bg-stone-50 focus:bg-white focus:outline-hidden focus:border-amber-500 leading-relaxed"
                    />
                  </div>

                  <button
                    onClick={() => {
                      if (Object.keys(selectedFoodIds).length === 0) {
                        alert('لطفاً حداقل یک غذا انتخاب کنید.');
                        return;
                      }
                      setFoodOrderSent(true);
                    }}
                    className="w-full mt-2 py-2.5 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-semibold shadow-sm transition flex items-center justify-center gap-2 cursor-pointer"
                  >
                    <Send className="w-3.5 h-3.5" />
                    ارسال سفارش و مشاهده پیام ارسالی به مدیر
                  </button>
                </div>
              </div>
            </div>

            {/* Right Col: Telegram Food Message Preview */}
            <div className="lg:col-span-7 space-y-4">
              <div className="bg-stone-900 text-stone-100 rounded-2xl p-5 border border-stone-800 shadow-md space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-stone-800">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span className="text-xs font-bold text-stone-200">پیش‌نمایش سفارش دریافتی ادمین در تلگرام</span>
                  </div>
                  <span className="text-[11px] text-stone-400">ADMIN_CHAT_ID</span>
                </div>

                <div className="bg-stone-800/90 rounded-xl p-4 border border-stone-700/60 font-mono text-xs leading-relaxed space-y-2 text-stone-200">
                  <p className="text-amber-400 font-bold">🍽🔔 <b>درخواست سفارش غذای جدید</b></p>
                  <div className="space-y-1 pt-1 border-t border-stone-700 text-[13px]">
                    <p>👤 <b>مهمان:</b> {simGuestName}</p>
                    <p>📞 <b>شماره تماس:</b> {simPhone}</p>
                    <p>🛏 <b>اتاق:</b> {simRoom}</p>
                    <p>📅 <b>روز و تاریخ سرو:</b> {simWeekday} {simDate}</p>
                    <p>🕒 <b>وعده:</b> {simMeal === 'lunch' ? 'ناهار ☀️' : 'شام 🌙'}</p>
                  </div>

                  <div className="pt-2 border-t border-stone-700">
                    <p className="text-amber-300 font-semibold mb-1">📋 جزئیات سفارش غذا:</p>
                    {Object.keys(selectedFoodIds).length > 0 ? (
                      Object.entries(selectedFoodIds).map(([id, count]) => {
                        const foodObj = foods.find((f) => f.id === id);
                        return (
                          <p key={id} className="text-stone-300 pr-2">
                            🍲 {foodObj?.title}: <b className="text-amber-400">{count} پرس</b> ({foodObj?.price})
                          </p>
                        );
                      })
                    ) : (
                      <p className="text-stone-500 italic">هنوز غذایی انتخاب نشده است.</p>
                    )}
                  </div>

                  <div className="pt-2 border-t border-stone-700">
                    <p className="text-amber-300 font-semibold mb-1">📝 توضیحات و ملاحظات سفارش:</p>
                    <p className="text-stone-200 pr-2 bg-stone-900/60 p-2 rounded-lg border border-stone-700/50">
                      {simFoodNotes.trim() ? simFoodNotes : 'ندارد'}
                    </p>
                  </div>

                  <p className="text-stone-400 pt-1 text-[11px]">🆔 آیدی تلگرام: @guest_telegram_id</p>
                </div>

                {/* Warm & Friendly Food Order Confirmation Message */}
                <div className="bg-stone-800/80 rounded-xl p-4 border border-amber-600/40 text-xs space-y-2">
                  <div className="flex items-center gap-2 text-amber-300 font-bold pb-2 border-b border-stone-700">
                    <Heart className="w-4 h-4 text-rose-400 fill-rose-400" />
                    <span>پیام صمیمانه تاییدیه سفارش ارسالی به مهمان</span>
                  </div>
                  <div className="space-y-2 text-stone-200 leading-relaxed">
                    <p className="font-bold text-amber-200 text-sm">🍲 درخواست سفارش غذای شما با مهر و موفقیت ثبت شد!</p>
                    <p className="text-amber-100 font-semibold bg-amber-950/40 p-2.5 rounded-lg border border-amber-800/40">
                      🌿 <b>خانواده اقامتگاه خانه برزک، با عطر و بوی غذاهای دست‌پخت سنتی، بی‌صبرانه منتظر دیدارتون تو خونهٔ خودتون هست!</b>
                    </p>
                    <p className="text-stone-300 text-[11px]">
                      امیدواریم طعم اصیل و نوستالژیک این خوراک‌ها براتون ماندگار بشه و دلتون شاد باشه 🌸 سفارش شما برای مطبخ خانه برزک ارسال شد و در زمان مقرر با تازه‌ترین مواد محلی آماده سرو خواهد بود. نوش جان! 🍃
                    </p>
                    {simFoodNotes.trim() && (
                      <p className="text-stone-300 text-[11px] pt-1">
                        📝 <b>ملاحظات ثبت‌شده شما:</b> {simFoodNotes}
                      </p>
                    )}
                  </div>
                </div>

                {foodOrderSent && (
                  <div className="p-3 bg-emerald-950/60 border border-emerald-700/50 rounded-xl flex items-center gap-2 text-emerald-300 text-xs">
                    <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
                    <span>تاییدیه سفارش غذا با موفقیت برای مهمان و آشپزخانه اقامتگاه صادر شد.</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* =========================================================
            TAB 3: MANAGE FOODS
           ========================================================= */}
        {activeTab === 'foods' && (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-4 rounded-2xl border border-stone-200 shadow-xs">
              <div>
                <h2 className="text-sm font-bold text-stone-900">مدیریت لیست غذاها، قیمت‌ها و توضیحات</h2>
                <p className="text-xs text-stone-500">
                  ویرایش نام غذا، قیمت، توضیحات و تعیین وعده‌های سرو مجاز (ناهار یا شام)
                </p>
              </div>
              <button
                onClick={() =>
                  setEditingFood({
                    id: `food_${Date.now()}`,
                    title: 'غذای محلی جدید',
                    description: 'توضیحات و ترکیبات غذای جدید برزک...',
                    price: '۳۰۰,۰۰۰ تومان',
                    availableMeals: ['lunch', 'dinner'],
                  })
                }
                className="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-medium flex items-center gap-1.5 transition"
              >
                <Plus className="w-3.5 h-3.5" />
                افزودن غذای جدید
              </button>
            </div>

            {/* Food Edit Modal */}
            {editingFood && (
              <div className="bg-white border-2 border-amber-500 rounded-2xl p-4 shadow-md space-y-3">
                <div className="flex items-center justify-between border-b pb-2">
                  <h3 className="text-xs font-bold text-stone-800">ویرایش مشخصات غذا</h3>
                  <button onClick={() => setEditingFood(null)} className="text-stone-400 hover:text-stone-600 text-xs">
                    بستن
                  </button>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div>
                    <label className="block text-stone-600 mb-1">عنوان غذا</label>
                    <input
                      type="text"
                      value={editingFood.title}
                      onChange={(e) => setEditingFood({ ...editingFood, title: e.target.value })}
                      className="w-full px-3 py-1.5 rounded-lg border border-stone-300"
                    />
                  </div>
                  <div>
                    <label className="block text-stone-600 mb-1">قیمت هر پرس</label>
                    <input
                      type="text"
                      value={editingFood.price}
                      onChange={(e) => setEditingFood({ ...editingFood, price: e.target.value })}
                      className="w-full px-3 py-1.5 rounded-lg border border-stone-300"
                    />
                  </div>
                  <div className="sm:col-span-2">
                    <label className="block text-stone-600 mb-1">توضیحات و ترکیبات</label>
                    <textarea
                      rows={2}
                      value={editingFood.description}
                      onChange={(e) => setEditingFood({ ...editingFood, description: e.target.value })}
                      className="w-full px-3 py-1.5 rounded-lg border border-stone-300"
                    />
                  </div>
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <button
                    onClick={() => setEditingFood(null)}
                    className="px-3 py-1 text-xs rounded-lg border border-stone-300 bg-white text-stone-600"
                  >
                    انصراف
                  </button>
                  <button
                    onClick={() => {
                      setFoods((prev) => {
                        const idx = prev.findIndex((f) => f.id === editingFood.id);
                        if (idx >= 0) {
                          const copy = [...prev];
                          copy[idx] = editingFood;
                          return copy;
                        }
                        return [...prev, editingFood];
                      });
                      setEditingFood(null);
                    }}
                    className="px-3 py-1 text-xs rounded-lg bg-amber-600 text-white font-medium hover:bg-amber-700"
                  >
                    ذخیره اطلاعات
                  </button>
                </div>
              </div>
            )}

            {/* Food Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {foods.map((food) => (
                <div key={food.id} className="bg-white rounded-2xl border border-stone-200 p-4 shadow-xs flex flex-col justify-between">
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <h3 className="text-sm font-bold text-stone-900">{food.title}</h3>
                      <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-amber-50 text-amber-800 border border-amber-200 shrink-0">
                        {food.price}
                      </span>
                    </div>
                    <p className="text-xs text-stone-600 mb-3 leading-relaxed">{food.description}</p>
                  </div>

                  <div className="pt-3 border-t border-stone-100 flex items-center justify-between">
                    <div className="flex items-center gap-1.5 text-[11px] text-stone-500">
                      {food.availableMeals.map((m) => (
                        <span key={m} className="px-1.5 py-0.5 rounded bg-stone-100 text-stone-700">
                          {m === 'lunch' ? '☀️ ناهار' : '🌙 شام'}
                        </span>
                      ))}
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => setEditingFood(food)}
                        className="p-1.5 text-stone-500 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition"
                        title="ویرایش"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => setFoods(foods.filter((f) => f.id !== food.id))}
                        className="p-1.5 text-stone-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
                        title="حذف"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* =========================================================
            TAB 4: MANAGE ROOMS
           ========================================================= */}
        {activeTab === 'rooms' && (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-4 rounded-2xl border border-stone-200 shadow-xs">
              <div>
                <h2 className="text-sm font-bold text-stone-900">مدیریت لیست اتاق‌ها، قیمت‌ها و توضیحات</h2>
                <p className="text-xs text-stone-500">
                  تغییر عنوان، توضیحات، نرخ عددی هر نفرشب برای محاسبات تخفیف سنین، و متن قیمت
                </p>
              </div>
              <button
                onClick={() =>
                  setEditingRoom({
                    id: `room_${Date.now()}`,
                    title: 'اتاق جدید',
                    description: 'توضیحات، ظرفیت و امکانات اتاق جدید...',
                    price: '۱,۳۰۰,۰۰۰ تومان / اقامت و صبحانه هر نفرشب',
                    pricePerPerson: 1300000,
                  })
                }
                className="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-medium flex items-center gap-1.5 transition"
              >
                <Plus className="w-3.5 h-3.5" />
                افزودن اتاق جدید
              </button>
            </div>

            {/* Room Edit Modal */}
            {editingRoom && (
              <div className="bg-white border-2 border-amber-500 rounded-2xl p-4 shadow-md space-y-3">
                <div className="flex items-center justify-between border-b pb-2">
                  <h3 className="text-xs font-bold text-stone-800">ویرایش مشخصات اتاق</h3>
                  <button onClick={() => setEditingRoom(null)} className="text-stone-400 hover:text-stone-600 text-xs">
                    بستن
                  </button>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div>
                    <label className="block text-stone-600 mb-1">عنوان اتاق</label>
                    <input
                      type="text"
                      value={editingRoom.title}
                      onChange={(e) => setEditingRoom({ ...editingRoom, title: e.target.value })}
                      className="w-full px-3 py-1.5 rounded-lg border border-stone-300"
                    />
                  </div>
                  <div>
                    <label className="block text-stone-600 mb-1">قیمت عددی هر نفرشب (تومان جهت محاسبه)</label>
                    <input
                      type="number"
                      value={editingRoom.pricePerPerson}
                      onChange={(e) => setEditingRoom({ ...editingRoom, pricePerPerson: parseInt(e.target.value) || 0 })}
                      className="w-full px-3 py-1.5 rounded-lg border border-stone-300 font-bold"
                    />
                  </div>
                  <div className="sm:col-span-2">
                    <label className="block text-stone-600 mb-1">متن نمایشی قیمت در ربات</label>
                    <input
                      type="text"
                      value={editingRoom.price}
                      onChange={(e) => setEditingRoom({ ...editingRoom, price: e.target.value })}
                      className="w-full px-3 py-1.5 rounded-lg border border-stone-300"
                    />
                  </div>
                  <div className="sm:col-span-2">
                    <label className="block text-stone-600 mb-1">توضیحات و امکانات</label>
                    <textarea
                      rows={2}
                      value={editingRoom.description}
                      onChange={(e) => setEditingRoom({ ...editingRoom, description: e.target.value })}
                      className="w-full px-3 py-1.5 rounded-lg border border-stone-300"
                    />
                  </div>
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <button
                    onClick={() => setEditingRoom(null)}
                    className="px-3 py-1 text-xs rounded-lg border border-stone-300 bg-white text-stone-600"
                  >
                    انصراف
                  </button>
                  <button
                    onClick={() => {
                      setRooms((prev) => {
                        const idx = prev.findIndex((r) => r.id === editingRoom.id);
                        if (idx >= 0) {
                          const copy = [...prev];
                          copy[idx] = editingRoom;
                          return copy;
                        }
                        return [...prev, editingRoom];
                      });
                      setEditingRoom(null);
                    }}
                    className="px-3 py-1 text-xs rounded-lg bg-amber-600 text-white font-medium hover:bg-amber-700"
                  >
                    ذخیره اطلاعات
                  </button>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {rooms.map((room) => (
                <div key={room.id} className="bg-white rounded-2xl border border-stone-200 p-4 shadow-xs flex flex-col justify-between">
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <h3 className="text-sm font-bold text-stone-900 flex items-center gap-2">
                        <BedDouble className="w-4 h-4 text-amber-700" />
                        {room.title}
                      </h3>
                      <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-stone-100 text-stone-800 shrink-0">
                        {room.price}
                      </span>
                    </div>
                    <p className="text-xs text-stone-600 leading-relaxed mb-3">{room.description}</p>
                  </div>

                  <div className="pt-3 border-t border-stone-100 flex items-center justify-between">
                    <span className="text-[11px] text-amber-800 font-medium">
                      نرخ پایه محاسباتی: {(room.pricePerPerson || 1300000).toLocaleString('fa-IR')} تومان
                    </span>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => setEditingRoom(room)}
                        className="p-1.5 text-stone-500 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition"
                        title="ویرایش"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => setRooms(rooms.filter((r) => r.id !== room.id))}
                        className="p-1.5 text-stone-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
                        title="حذف"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* =========================================================
            TAB 5: PYTHON CODE GENERATOR & SEPARATION OF DATA
           ========================================================= */}
        {activeTab === 'code' && (
          <div className="space-y-6">
            {/* Strategy Explainer Card */}
            <div className="bg-white rounded-2xl border border-stone-200 p-5 shadow-xs space-y-3">
              <div className="flex items-center gap-2 text-stone-900">
                <ShieldCheck className="w-5 h-5 text-emerald-600" />
                <h2 className="text-sm font-bold">معماری جداسازی اطلاعات از کد (عدم بازنویسی تنظیمات شما)</h2>
              </div>
              <p className="text-xs text-stone-600 leading-relaxed">
                برای اینکه با هر بار به‌روزرسانی یا تغییرات در کدهای پایتون (`bot.py`)، مشخصات اتاق‌ها و قیمت غذاهای شما هرگز تغییر نکند یا ریست نشود، ربات طوری تنظیم شده است که ابتدا فایل‌های داده‌های شما (`rooms.json` و `foods.json`) را بررسی کند. در نتیجه با ارتقای کدها، اطلاعات شخصی شما دست‌نخورده باقی می‌ماند.
              </p>
              <div className="flex flex-wrap gap-2 pt-1">
                <button
                  onClick={handleDownloadRoomsJson}
                  className="px-3 py-1.5 rounded-xl bg-amber-50 hover:bg-amber-100 border border-amber-200 text-amber-900 text-xs font-semibold flex items-center gap-1.5 transition"
                >
                  <Download className="w-3.5 h-3.5 text-amber-700" />
                  دانلود فایل rooms.json (برای ربات)
                </button>
                <button
                  onClick={handleDownloadFoodsJson}
                  className="px-3 py-1.5 rounded-xl bg-amber-50 hover:bg-amber-100 border border-amber-200 text-amber-900 text-xs font-semibold flex items-center gap-1.5 transition"
                >
                  <Download className="w-3.5 h-3.5 text-amber-700" />
                  دانلود فایل foods.json (برای ربات)
                </button>
                <button
                  onClick={handleExportBackup}
                  className="px-3 py-1.5 rounded-xl bg-stone-100 hover:bg-stone-200 border border-stone-300 text-stone-700 text-xs font-semibold flex items-center gap-1.5 transition"
                >
                  <Download className="w-3.5 h-3.5 text-stone-600" />
                  دانلود پشتیبان کامل (اتاق‌ها و غذاها)
                </button>
              </div>
            </div>

            {/* GitHub Release & Sync Card */}
            <div className="bg-white rounded-2xl border-2 border-amber-600/30 p-5 shadow-xs space-y-5">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-stone-200 pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-xl bg-amber-600/10 border border-amber-600/20 flex items-center justify-center text-amber-700">
                    <GitBranch className="w-4 h-4" />
                  </div>
                  <div>
                    <h2 className="text-sm font-bold text-stone-900">همگام‌سازی با مخزن گیت‌هاب BarzokhouseTelegramBot</h2>
                    <p className="text-xs text-stone-500">
                      ثبت انتشار (Release) نسخه تولید شده با کلاود به تاریخ امروز و اعمال آخرین تغییرات AI Studio
                    </p>
                  </div>
                </div>
                <a
                  href="https://github.com/targol/BarzokhouseTelegramBot"
                  target="_blank"
                  rel="noreferrer"
                  className="px-3 py-1.5 rounded-xl border border-stone-300 bg-stone-50 hover:bg-stone-100 text-stone-700 text-xs font-semibold flex items-center gap-1.5 transition"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  مشاهده مخزن در GitHub
                </a>
              </div>

              {/* Step 1: GitHub Release */}
              <div className="bg-amber-50/70 border border-amber-200/80 rounded-xl p-4 space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="flex items-center gap-1.5 text-xs font-bold text-amber-950">
                    <Tag className="w-4 h-4 text-amber-700" />
                    مرحله اول: ثبت انتشار (Release) نسخه کلاود در گیت‌هاب (به تاریخ امروز)
                  </span>
                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-200/70 text-amber-900 font-mono font-bold">
                    v1.0-claude-2026-09-04
                  </span>
                </div>

                <div className="bg-white p-3 rounded-lg border border-amber-200 text-xs space-y-2 text-stone-700">
                  <div className="flex items-center justify-between text-[11px] text-stone-500 border-b pb-1.5">
                    <span><b>عنوان انتشار:</b> نسخه اولیه توسعه‌یافته با کلاود (Claude) - 2026-09-04</span>
                    <span><b>تگ:</b> v1.0-claude-2026-09-04</span>
                  </div>
                  <div>
                    <p className="text-stone-500 text-[11px] mb-1">متن توضیحات (Release Notes):</p>
                    <p className="bg-stone-50 p-2 rounded-md font-medium text-stone-800 leading-relaxed">
                      این نسخه با کلاود (Claude) تولید شده است و پس از این، تغییرات، قابلیت‌ها و به‌روزرسانی‌های آینده با Google AI Studio انجام می‌شود.
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2 pt-1">
                  <a
                    href="https://github.com/targol/BarzokhouseTelegramBot/releases/new?tag=v1.0-claude-2026-09-04&title=%D9%86%D8%B3%D8%AE%D9%87%20%D8%A7%D9%88%D9%84%DB%8C%D9%87%20%D8%AA%D9%88%D8%B3%D8%B9%D9%87%E2%80%8C%DB%8C%D8%A7%D9%81%D8%AA%D9%87%20%D8%A8%D8%A7%20%DA%A9%D9%84%D8%A7%D9%88%D8%AF%20(Claude)%20-%202026-09-04&body=%D8%A7%DB%8C%D9%86%20%D9%86%D8%B3%D8%AE%D9%87%20%D8%A8%D8%A7%20%DA%A9%D9%84%D8%A7%D9%88%D8%AF%20(Claude)%20%D8%AA%D9%88%D9%84%DB%8C%D8%AF%20%D8%B4%D8%AF%D9%87%20%D8%A7%D8%B3%D8%AA%20%D9%88%20%D9%BE%D8%B3%20%D8%A7%D8%B2%20%D8%A7%DB%8C%D9%86%D8%8C%20%D8%AA%D8%BA%DB%8C%DB%8C%D8%B1%D8%A7%D8%AA%D8%8C%20%D9%82%D8%A7%D8%A8%D9%84%DB%8C%D8%AA%E2%80%8C%D9%87%D8%A7%20%D9%88%20%D8%A8%D9%87%E2%80%8C%D8%B1%D9%88%D8%B2%D8%B1%D8%B3%D8%A7%D9%86%DB%8C%E2%80%8C%D9%87%D8%A7%DB%8C%20%D8%A2%DB%8C%D9%86%D8%AF%D9%87%20%D8%A8%D8%A7%20Google%20AI%20Studio%20%D8%A7%D9%86%D8%AC%D8%A7%D9%85%20%D9%85%DB%8C%E2%80%8C%D8%B4%D9%88%D8%AF."
                    target="_blank"
                    rel="noreferrer"
                    className="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition shadow-xs"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    باز کردن مستقیم صفحه ساخت Release در گیت‌هاب (آماده با یک کلیک)
                  </a>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(
                        'این نسخه با کلاود (Claude) تولید شده است و پس از این، تغییرات، قابلیت‌ها و به‌روزرسانی‌های آینده با Google AI Studio انجام می‌شود.'
                      );
                      setCopiedRelease(true);
                      setTimeout(() => setCopiedRelease(false), 2000);
                    }}
                    className="px-3 py-1.5 bg-white hover:bg-amber-100/50 border border-amber-300 text-amber-900 rounded-xl text-xs font-medium flex items-center gap-1.5 transition"
                  >
                    {copiedRelease ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    {copiedRelease ? 'متن کپی شد!' : 'کپی متن توضیحات'}
                  </button>
                </div>
              </div>

              {/* Step 2: Apply AI Studio Changes */}
              <div className="bg-stone-50 border border-stone-200 rounded-xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-xs font-bold text-stone-900">
                    <FolderArchive className="w-4 h-4 text-emerald-600" />
                    مرحله دوم: اعمال کدهای جدید روی مخزن گیت‌هاب
                  </span>
                  <span className="text-[11px] text-stone-500">bot.py, config.py, rooms.json, foods.json</span>
                </div>

                <div className="flex flex-wrap gap-2">
                  <a
                    href="/BarzokhouseTelegramBot-aistudio-update.zip"
                    download="BarzokhouseTelegramBot-aistudio-update.zip"
                    className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold flex items-center gap-2 shadow-xs transition"
                  >
                    <Download className="w-4 h-4" />
                    دانلود پکیج کامل کدهای جدید (Zip)
                  </a>
                  <button
                    onClick={() => {
                      const gitScript = `# 1. ثبت تگ انتشار نسخه کلاود در گیت‌هاب
git tag -a v1.0-claude-2026-09-04 -m "این نسخه با کلاود (Claude) تولید شده است و پس از این با AI Studio ادامه می‌یابد"
git push origin v1.0-claude-2026-09-04

# 2. اضافه کردن کدهای جدید و ارسال به گیت‌هاب
git add bot.py config.py rooms.json foods.json AGENTS.md
git commit -m "feat(aistudio): اضافه شدن رزرو چند اتاقه، منوی غذا، تخفیف کودکان، توضیحات خاص، و پیام‌های صمیمانه"
git push origin main`;
                      navigator.clipboard.writeText(gitScript);
                      setCopiedGitCmds(true);
                      setTimeout(() => setCopiedGitCmds(false), 2000);
                    }}
                    className="px-3.5 py-2 bg-stone-200 hover:bg-stone-300 text-stone-800 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition"
                  >
                    {copiedGitCmds ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    {copiedGitCmds ? 'دستورات کپی شد!' : 'کپی دستورات Git برای ترمینال'}
                  </button>
                </div>

                <div className="text-[11px] text-stone-600 space-y-1 pt-1 bg-white p-3 rounded-lg border border-stone-200">
                  <p className="font-semibold text-stone-800">💡 روش خودکار با توکن گیت‌هاب (Personal Access Token):</p>
                  <p>
                    اسکریپت پایتون <code className="text-amber-700 bg-amber-50 px-1 py-0.5 rounded">publish_to_github.py</code> در پروژه آماده شده است. با افزودن <code className="font-mono text-stone-800">GITHUB_TOKEN</code> به Secrets، هم ساخت ریلیز کلاود و هم ارسال خودکار کدهای جدید با یک دستور انجام می‌شود.
                  </p>
                </div>
              </div>
            </div>

            {/* Python Snippet Box */}
            <div className="bg-stone-900 text-stone-100 rounded-2xl border border-stone-800 p-5 shadow-lg space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-sm font-bold text-amber-400">کدهای دیکشنری پایتون در config.py</h2>
                  <p className="text-xs text-stone-400">
                    در صورت تمایل به قرار دادن مستقیم در فایل پایتون، می‌توانید این بخش را در config.py کپی کنید.
                  </p>
                </div>
                <button
                  id="copy-code-btn"
                  onClick={handleCopyCode}
                  className="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition"
                >
                  {copied ? <Check className="w-4 h-4 text-emerald-300" /> : <Copy className="w-4 h-4" />}
                  {copied ? 'کپی شد!' : 'کپی کدهای پایتون'}
                </button>
              </div>

              <pre className="bg-stone-950 p-4 rounded-xl text-xs font-mono text-emerald-400 overflow-x-auto border border-stone-800 max-h-96 leading-relaxed" dir="ltr">
                {generateConfigPySnippet()}
              </pre>
            </div>
          </div>
        )}

        {/* Serverless Bot Tab */}
        {activeTab === 'serverless' && (
          <div className="space-y-6">
            {/* Header Banner */}
            <div className="bg-linear-to-r from-emerald-900 via-stone-900 to-stone-900 text-white rounded-2xl p-6 border border-emerald-700/50 shadow-xl space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-semibold border border-emerald-500/30">
                    <Zap className="w-3.5 h-3.5 text-emerald-400" />
                    Telegram Serverless Architecture (tgcloud)
                  </div>
                  <h1 className="text-xl font-bold text-white">نسخه کامل بدون سرور (Serverless) ربات خانه برزک</h1>
                  <p className="text-xs text-stone-300 max-w-2xl leading-relaxed">
                    این نسخه برای اجرای اختصاصی روی زیرساخت بومی ابری تلگرام بازنویسی شده است. بدون نیاز به سرور مجزا، هاست یا Render، کدهای ربات مستقیماً در کنار هسته تلگرام با حداکثر سرعت اجرا می‌شوند.
                  </p>
                </div>

                <div className="flex flex-wrap gap-2">
                  <a
                    href="https://github.com/targol/BarzokhouseTelegramBot/tree/main/serverless"
                    target="_blank"
                    rel="noreferrer"
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl flex items-center gap-2 shadow-lg transition"
                  >
                    <ExternalLink className="w-4 h-4" />
                    مشاهده پوشه serverless در گیت‌هاب
                  </a>
                </div>
              </div>

              {/* 4 Feature Badges */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2">
                <div className="bg-stone-800/80 border border-emerald-500/20 rounded-xl p-3 space-y-1">
                  <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                    ⚡ پاسخ‌دهی آنی (Zero Cold-Start)
                  </span>
                  <p className="text-[11px] text-stone-300">
                    برخلاف Render که پس از ۱۵ دقیقه به خواب می‌رود، تلگرام سرورلس همواره آماده است و در چند میلی‌ثانیه پاسخ می‌دهد.
                  </p>
                </div>

                <div className="bg-stone-800/80 border border-emerald-500/20 rounded-xl p-3 space-y-1">
                  <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                    💾 دیتابیس بومی SQLite
                  </span>
                  <p className="text-[11px] text-stone-300">
                    ذخیره وضعیت مراحل رزرو چند اتاقه و سفارش غذا مستقیماً در حافظه ابری و امن دیتابیس تلگرام.
                  </p>
                </div>

                <div className="bg-stone-800/80 border border-emerald-500/20 rounded-xl p-3 space-y-1">
                  <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                    🛡️ بدون خطر فیلترینگ سرور
                  </span>
                  <p className="text-[11px] text-stone-300">
                    چون کدها درون شبکه تلگرام اجرا می‌شوند، هیچ سرور واسطی وجود ندارد که مسدود یا قطع شود.
                  </p>
                </div>

                <div className="bg-stone-800/80 border border-emerald-500/20 rounded-xl p-3 space-y-1">
                  <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                    💰 کاملاً رایگان و پایدار
                  </span>
                  <p className="text-[11px] text-stone-300">
                    بدون نیاز به کارت اعتباری بین‌المللی یا تمدید ماهیانه هزینه‌های هاستینگ خارجی.
                  </p>
                </div>
              </div>
            </div>

            {/* Quick Deploy Instructions */}
            <div className="bg-white border border-stone-200 rounded-2xl p-5 shadow-xs space-y-4">
              <h2 className="text-sm font-bold text-stone-900 flex items-center gap-2">
                <Send className="w-4 h-4 text-emerald-600" />
                راهنمای راه‌اندازی سریع در ۲ مرحله
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Step 1 */}
                <div className="border border-stone-200 rounded-xl p-4 bg-stone-50/50 space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-emerald-600 text-white font-bold text-xs flex items-center justify-center">۱</span>
                    <span className="text-xs font-bold text-stone-900">فعال‌سازی در @BotFather</span>
                  </div>
                  <p className="text-xs text-stone-600 leading-relaxed">
                    در تلگرام وارد ربات <b>@BotFather</b> شوید، دستور <code>/mybots</code> را بزنید، ربات خانه برزک را انتخاب کنید، به بخش <b>Bot Settings</b> رفته و گزینه <b>Serverless</b> (یا Cloud Execution) را در حالت <b>Enable</b> قرار دهید تا توکن دیپلوی دریافت شود.
                  </p>
                </div>

                {/* Step 2 */}
                <div className="border border-stone-200 rounded-xl p-4 bg-stone-50/50 space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-emerald-600 text-white font-bold text-xs flex items-center justify-center">۲</span>
                    <span className="text-xs font-bold text-stone-900">دیپلوی با یک خط دستور</span>
                  </div>
                  <p className="text-xs text-stone-600 leading-relaxed">
                    پروژه را با گیت کلون کنید یا کدهای پوشه <code>serverless</code> را بردارید و در خط فرمان دستور زیر را بزنید:
                  </p>
                  <div className="flex items-center justify-between bg-stone-900 text-emerald-400 px-3 py-2 rounded-lg font-mono text-xs">
                    <span>npx tgcloud push</span>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText("cd serverless && npx tgcloud push");
                        setCopiedTgCloud(true);
                        setTimeout(() => setCopiedTgCloud(false), 2000);
                      }}
                      className="text-stone-300 hover:text-white transition flex items-center gap-1 text-[11px]"
                    >
                      {copiedTgCloud ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      {copiedTgCloud ? "کپی شد" : "کپی دستور"}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Code Explorer */}
            <div className="bg-stone-900 text-stone-100 rounded-2xl border border-stone-800 p-5 shadow-lg space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-stone-800 pb-3">
                <div className="flex items-center gap-2">
                  <FileCode2 className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-bold text-stone-200">فایل‌های بازنویسی شده سرورلس در گیت‌هاب:</span>
                </div>

                {/* Sub-file tabs */}
                <div className="flex flex-wrap gap-1 bg-stone-950 p-1 rounded-xl border border-stone-800">
                  <button
                    onClick={() => setSelectedServerlessFile('readme')}
                    className={`px-3 py-1 rounded-lg text-xs transition ${
                      selectedServerlessFile === 'readme' ? 'bg-emerald-600 text-white font-bold' : 'text-stone-400 hover:text-stone-200'
                    }`}
                  >
                    README.md
                  </button>
                  <button
                    onClick={() => setSelectedServerlessFile('message')}
                    className={`px-3 py-1 rounded-lg text-xs transition ${
                      selectedServerlessFile === 'message' ? 'bg-emerald-600 text-white font-bold' : 'text-stone-400 hover:text-stone-200'
                    }`}
                  >
                    handlers/message.js
                  </button>
                  <button
                    onClick={() => setSelectedServerlessFile('callback')}
                    className={`px-3 py-1 rounded-lg text-xs transition ${
                      selectedServerlessFile === 'callback' ? 'bg-emerald-600 text-white font-bold' : 'text-stone-400 hover:text-stone-200'
                    }`}
                  >
                    handlers/callback_query.js
                  </button>
                  <button
                    onClick={() => setSelectedServerlessFile('config')}
                    className={`px-3 py-1 rounded-lg text-xs transition ${
                      selectedServerlessFile === 'config' ? 'bg-emerald-600 text-white font-bold' : 'text-stone-400 hover:text-stone-200'
                    }`}
                  >
                    config.js
                  </button>
                  <button
                    onClick={() => setSelectedServerlessFile('db')}
                    className={`px-3 py-1 rounded-lg text-xs transition ${
                      selectedServerlessFile === 'db' ? 'bg-emerald-600 text-white font-bold' : 'text-stone-400 hover:text-stone-200'
                    }`}
                  >
                    db.js (SQLite)
                  </button>
                </div>
              </div>

              {/* Code viewer container */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-[11px] text-stone-400">
                  <span>مسیر: serverless/{selectedServerlessFile === 'message' ? 'handlers/message.js' : selectedServerlessFile === 'callback' ? 'handlers/callback_query.js' : selectedServerlessFile === 'config' ? 'config.js' : selectedServerlessFile === 'db' ? 'db.js' : 'README.md'}</span>
                  <span className="text-emerald-400 font-mono">JavaScript (ESM)</span>
                </div>

                <pre className="bg-stone-950 p-4 rounded-xl text-xs font-mono text-emerald-400 overflow-x-auto border border-stone-800 max-h-96 leading-relaxed" dir="ltr">
                  {selectedServerlessFile === 'readme' && `# راهنمای اجرای ربات اقامتگاه «خانه برزک» در حالت بدون سرور (Telegram Serverless)

این نسخه به طور کامل بر پایه معماری نوین Telegram Serverless بازنویسی شده است؛ به این معنی که کدهای ربات مستقیماً داخل زیرساخت ابری امن و پرسرعت تلگرام اجرا می‌شوند و به هیچ سرور خارجی (مثل Render، VPS یا هاست‌های پولی) نیازی ندارید.

## دستور دیپلوی:
$ cd serverless
$ npx tgcloud push`}

                  {selectedServerlessFile === 'message' && `// handlers/message.js - پردازش دستورات متنی و سناریوهای رزرو و غذا
import { WELCOME_MESSAGE, ROOMS, FOODS } from "../config.js";
import { mainMenuKeyboard, bookingRoomsSelectionKeyboard } from "../keyboards.js";
import { parseJalaliDate, formatPrice } from "../utils.js";
import { getSession, setSession, clearSession } from "../db.js";

export default async function handleMessage(payload, ctx) {
  const msg = payload?.message || payload;
  const text = msg?.text?.trim();
  // مدیریت دستورات /start, /cancel, /food و پیام‌های متنی مهمانان...
}`}

                  {selectedServerlessFile === 'callback' && `// handlers/callback_query.js - مدیریت کلیک روی دکمه‌های شیشه‌ای
import { mainMenuKeyboard, ageCountersKeyboard, bookingFinalConfirmKeyboard } from "../keyboards.js";
import { getSession, setSession, clearSession } from "../db.js";

export default async function handleCallbackQuery(payload, ctx) {
  const query = payload?.callback_query || payload;
  // مدیریت رزرو چند اتاقه، شمارنده سنین کودکان (نیم‌بها و رایگان)، منوی غذا و ارسال فیش واریزی
}`}

                  {selectedServerlessFile === 'config' && `// config.js - خواندن اطلاعات اتاق‌ها و غذاها از JSON با تضمین پایداری داده
export const ROOMS = loadJson("rooms.json", { ... });
export const FOODS = loadJson("foods.json", { ... });
export const LOCATION_LATITUDE = 33.78286576513508;
export const LOCATION_LONGITUDE = 51.22924918495417;`}

                  {selectedServerlessFile === 'db' && `// db.js - مدیریت سشن‌ها با پشتیبانی کامل از دیتابیس داخلی SQLite تلگرام
export async function initDb(ctx) {
  if (ctx && ctx.db) {
    await ctx.db.exec("CREATE TABLE IF NOT EXISTS user_sessions (user_id TEXT PRIMARY KEY, state TEXT, data TEXT, updated_at INTEGER);");
  }
}`}
                </pre>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
