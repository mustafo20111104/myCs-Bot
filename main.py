import random
import sqlite3
import re
import requests
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# ================= BAZA =================
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  coins INTEGER DEFAULT 200,
                  last_daily TEXT)''')
    conn.commit()
    conn.close()
init_db()

def get_user(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT coins, last_daily FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"coins": row[0], "last_daily": row[1]}
    else:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (user_id, coins, last_daily) VALUES (?, ?, ?)", (user_id, 200, None))
        conn.commit()
        conn.close()
        return {"coins": 200, "last_daily": None}

def update_coins(user_id, new_coins):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET coins = ? WHERE user_id = ?", (new_coins, user_id))
    conn.commit()
    conn.close()

def update_daily(user_id, date_today):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET last_daily = ? WHERE user_id = ?", (date_today, user_id))
    conn.commit()
    conn.close()

# ================= 50 CASE VA SKINLAR (dinamik yaratish) =================
# Case turlari: oddiy (10), noyob (15), afsonaviy (15), mifologik (10) – jami 50
case_tiers = [
    ("📦 Oddiy", 10, 30, 120),     # (nomi, soni, min_price, max_price)
    ("✨ Noyob", 15, 100, 400),
    ("🔥 Afsonaviy", 15, 300, 1200),
    ("💎 Mifologik", 10, 1000, 6000)
]

# Skin nomlari (real CS2 skinlariga o‘xshash)
skin_names = {
    "common": ["MP9 | Green Plaid", "MAC-10 | Whitefish", "SSG 08 | Abyss", "Galil AR | Sandstorm",
               "FAMAS | Doomkitty", "M4A4 | Evil Daimyo", "AK-47 | Elite Build", "AWP | Capillary",
               "USP-S | Lead Conduit", "Glock-18 | Wraiths"],
    "rare": ["M4A1-S | Atomic Alloy", "AK-47 | Frontside Misty", "AWP | Fever Dream", "Desert Eagle | Code Red",
             "★ Bayonet | Rust Coat", "★ Flip Knife | Tiger Tooth", "★ M9 Bayonet | Night", "AK-47 | Bloodsport",
             "AWP | Oni Taiji", "★ Karambit | Stained"],
    "legendary": ["AK-47 | Fire Serpent", "AWP | Medusa", "★ Butterfly Knife | Fade", "★ Karambit | Doppler",
                  "M4A4 | Howl", "AWP | Dragon Lore", "★ M9 Bayonet | Crimson Web", "★ Karambit | Sapphire",
                  "★ Butterfly Knife | Doppler Ruby", "★ Karambit | Emerald"],
    "mythic": ["★ Karambit | Gamma Doppler", "★ M9 Bayonet | Lore", "AWP | Gungnir", "M4A4 | Poseidon",
               "★ Butterfly Knife | Marble Fade", "★ Karambit | Fade", "★ Talon Knife | Ruby", "AK-47 | Gold Arabesque",
               "★ Skeleton Knife | Slaughter", "★ Karambit | Crimson Web"]
}

# Rasm URL'larini qisqartirib berdim (real Steam CDN bilan almashtirish mumkin)
default_image = "https://steamcdn-a.akamaihd.net/apps/730/icons/econ/default_generated/game_icon_large.vtf"

def generate_cases():
    cases = {}
    case_id = 1
    for tier_name, count, min_price, max_price in case_tiers:
        tier_key = tier_name.split()[1].lower()  # oddiy, noyob, afsonaviy, mifologik
        name_list = skin_names.get(tier_key, skin_names["common"])
        for i in range(count):
            # Case narxi: skinlar o‘rtacha qiymatining 80% (foydalanuvchi foyda olishi mumkin)
            avg_skin_value = (min_price + max_price) // 2
            case_price = int(avg_skin_value * 0.8)
            # Har bir case uchun 10 ta skin yaratish (qiymati min_price dan max_price gacha)
            skins = []
            for j in range(10):
                skin_value = random.randint(min_price, max_price)
                skin_name = random.choice(name_list) + f" {j+1}" if len(name_list) < 10 else name_list[j % len(name_list)]
                skins.append({
                    "name": skin_name,
                    "value": skin_value,
                    "image": default_image  # Haqiqiy rasm URL'ini qo‘shing
                })
            cases[f"case_{case_id}"] = {
                "name": f"{tier_name} Case #{case_id}",
                "price": case_price,
                "skins": skins
            }
            case_id += 1
    return cases

CASES = generate_cases()  # 50 ta case

# ================= STEAM MARKET NARX TEKSHIRISH =================
def get_steam_price(market_hash_name):
    url = "https://steamcommunity.com/market/priceoverview/"
    params = {"country": "US", "currency": 1, "appid": 730, "market_hash_name": market_hash_name}
    try:
        r = requests.get(url, params=params, timeout=8)
        data = r.json()
        if data.get("success"):
            price_str = data["lowest_price"]
            price = float(re.sub(r'[^\d.]', '', price_str))
            volume = data.get("volume", "N/A")
            return price, volume
    except:
        pass
    return None, None

# ================= TUGMALAR (50 case uchun paginatsiya) =================
def main_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💰 Balans", callback_data="balance"),
        InlineKeyboardButton("🎁 Kunlik", callback_data="daily"),
        InlineKeyboardButton("📦 Case ochish", callback_data="case_list_0"),
        InlineKeyboardButton("🛒 Do‘kon", callback_data="shop"),
        InlineKeyboardButton("🔍 Skin narxi", callback_data="price_check"),
        InlineKeyboardButton("❓ Yordam", callback_data="help")
    )
    return kb

def case_list_page(page=0, per_page=10):
    case_items = list(CASES.items())
    total = len(case_items)
    start = page * per_page
    end = min(start + per_page, total)
    kb = InlineKeyboardMarkup(row_width=1)
    for case_id, case in case_items[start:end]:
        kb.add(InlineKeyboardButton(f"{case['name']} ({case['price']} tanga)", callback_data=f"open_{case_id}"))
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ Oldingi", callback_data=f"case_list_{page-1}"))
    if end < total:
        nav_buttons.append(InlineKeyboardButton("Keyingi ▶️", callback_data=f"case_list_{page+1}"))
    if nav_buttons:
        kb.row(*nav_buttons)
    kb.add(InlineKeyboardButton("🔙 Asosiy menyu", callback_data="back_main"))
    return kb

def shop_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("💎 100 tanga - $1", callback_data="buy_100"),
        InlineKeyboardButton("💎 500 tanga - $4.5", callback_data="buy_500"),
        InlineKeyboardButton("💎 1000 tanga - $8", callback_data="buy_1000"),
        InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")
    )
    return kb

# ================= BUYRUQLAR =================
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    get_user(msg.from_user.id)
    await msg.answer(
        "🎮 *ULTIMATE CS2 CASE BOT*\n\n"
        "✅ 50 xil case, har birida 10 tadan skin (jami 500 skin)\n"
        "✅ Case narxi skin qiymatlariga moslashtirilgan\n"
        "✅ Eng qimmat skinlar 6000 tangagacha\n"
        "✅ Steam Marketda istalgan skin narxini tekshirish\n"
        "✅ Tangalarni real pulga xarid qilish\n\n"
        f"💰 Boshlang‘ich balans: 200 tanga",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

@dp.message_handler(commands=['help'])
async def help_cmd(msg: types.Message):
    await msg.answer(
        "📖 *Yordam:*\n\n"
        "• Balans – tangalaringiz\n"
        "• Kunlik – har kuni 100 tanga\n"
        "• Case ochish – 50 xildan birini tanlang\n"
        "• Do‘kon – tangalarni pulga xarid qilish\n"
        "• Skin narxi – Steam Marketda real narx\n\n"
        "Skin narxi uchun botga to‘liq nom yozing (masalan: `AK-47 | Redline (Field-Tested)`)",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

@dp.message_handler()
async def price_check(msg: types.Message):
    skin_name = msg.text.strip()
    if len(skin_name) < 5:
        return
    wait = await msg.reply("🔍 Tekshirilmoqda...", parse_mode="Markdown")
    price, vol = get_steam_price(skin_name)
    if price:
        await bot.edit_message_text(
            f"🎯 *{skin_name}*\n💰 Narxi: `${price:.2f}`\n📊 24s savdo: {vol}",
            chat_id=msg.chat.id, message_id=wait.message_id, parse_mode="Markdown"
        )
    else:
        await bot.edit_message_text(
            f"❌ Topilmadi. To‘liq nom yozing.\nMasalan: `AK-47 | Redline (Field-Tested)`",
            chat_id=msg.chat.id, message_id=wait.message_id, parse_mode="Markdown"
        )

# ================= TUGMALAR =================
@dp.callback_query_handler(lambda c: True)
async def handle_callback(call: types.CallbackQuery):
    uid = call.from_user.id
    user = get_user(uid)
    data = call.data

    if data == "balance":
        await bot.send_message(uid, f"💰 Balans: *{user['coins']}* tanga", parse_mode="Markdown")
        await call.answer()

    elif data == "daily":
        today = datetime.now().date()
        if user['last_daily']:
            last = datetime.strptime(user['last_daily'], "%Y-%m-%d").date()
            if last == today:
                await bot.send_message(uid, "❌ Bugun olgansiz! Ertaga kel.", parse_mode="Markdown")
                await call.answer()
                return
        new = user['coins'] + 100
        update_coins(uid, new)
        update_daily(uid, today.strftime("%Y-%m-%d"))
        await bot.send_message(uid, f"🎉 +100 tanga! Balans: {new} tanga", parse_mode="Markdown")
        await call.answer()

    elif data.startswith("case_list_"):
        page = int(data.split("_")[2])
        await call.message.edit_text("📦 *Case tanlang (sahifalar bo‘yicha):*", reply_markup=case_list_page(page), parse_mode="Markdown")
        await call.answer()

    elif data.startswith("open_"):
        case_id = data.split("_")[1]
        case = CASES.get(case_id)
        if not case:
            await call.answer("Case topilmadi!")
            return
        if user['coins'] < case['price']:
            await bot.send_message(uid, f"❌ Kerak: {case['price']} tanga, sizda {user['coins']} tanga", parse_mode="Markdown")
            await call.answer()
            return
        new_coins = user['coins'] - case['price']
        skin = random.choice(case['skins'])
        new_coins += skin['value']
        update_coins(uid, new_coins)
        caption = (
            f"🎁 *{case['name']} ochildi!*\n\n"
            f"✨ *{skin['name']}*\n"
            f"💰 Qiymati: {skin['value']} tanga\n"
            f"💵 Taxminiy real narx: `${skin['value']/10:.2f}`\n\n"
            f"Yangi balans: {int(new_coins)} tanga"
        )
        try:
            await bot.send_photo(uid, photo=skin['image'], caption=caption, parse_mode="Markdown")
        except:
            await bot.send_message(uid, caption, parse_mode="Markdown")
        await call.answer()

    elif data == "shop":
        await call.message.edit_text("🛒 *Tangalarni xarid qiling:*\n(Payment simulyatsiya)", reply_markup=shop_menu(), parse_mode="Markdown")
        await call.answer()

    elif data.startswith("buy_"):
        amount = int(data.split("_")[1])
        await bot.send_message(
            uid,
            f"💳 *{amount} tanga* xaridi: ${amount/100:.2f}\n\n"
            f"🔹 To‘lovni amalga oshirish uchun quyidagi link orqali to‘lang:\n"
            f"`https://example.com/pay?user={uid}&amount={amount}`\n\n"
            f"⚠️ Bu simulyatsiya. Haqiqiy botda Stripe, Click yoki Payme ulashingiz mumkin.",
            parse_mode="Markdown"
        )
        await call.answer("Xarid havolasi yuborildi.")

    elif data == "price_check":
        await bot.send_message(uid, "🔍 *Skin nomini yozing:*\nMasalan: `AK-47 | Redline (Field-Tested)`", parse_mode="Markdown")
        await call.answer()

    elif data == "help":
        await help_cmd(call.message)
        await call.answer()

    elif data == "back_main":
        await call.message.edit_text("Asosiy menyu:", reply_markup=main_menu(), parse_mode="Markdown")
        await call.answer()

    # Menyuni yangilash (agar kerak bo‘lsa)
    if not data.startswith("case_list_") and data != "back_main" and not data.startswith("open_"):
        await call.message.edit_reply_markup(reply_markup=main_menu())
