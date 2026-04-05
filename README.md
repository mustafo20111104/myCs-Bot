# Ultimate CS2 Case Bot – 50 Cases, 500 Skins, Real Steam Price

**Eng kuchli CS2 Telegram boti** – 50 xil case, har birida 10 tadan skin, skin qiymatiga mos case narxlari, Steam Market integratsiyasi va tanga xaridi.

## ✨ Xususiyatlar
- **50 xil case** (Oddiy, Noyob, Afsonaviy, Mifologik)
- **500 ta noyob skin** – qiymatlari 30 dan 6000 tangagacha
- **Case narxi** skinlarning o‘rtacha qiymatiga asoslangan (foydali)
- **Steam Market tekshiruvi** – real vaqtda narx va savdo hajmi
- **Tangalarni pulga xarid qilish** (simulyatsiya, real to‘lov ulash mumkin)
- **Kunlik bonus** (100 tanga)
- **Balans tizimi** (SQLite)

## 🚀 O‘rnatish (PythonAnywhere)

1. GitHub’da repository yarating va barcha fayllarni yuklang.
2. PythonAnywhere’da **Web** → **Add web app** → Manual → Python 3.10
3. `mysite` papkasiga fayllarni yuklang.
4. Konsolda: `pip3 install --user -r requirements.txt`
5. `.env` faylga tokeningizni yozing.
6. `app.py` dagi `YOUR_USERNAME` ni o‘zgartiring.
7. WSGI faylini sozlang (yuqoridagi qo‘llanmaga qarang).
8. **Reload** tugmasini bosing.

## 🛒 Haqiqiy to‘lov ulash

`buy_` tugmalari simulyatsiya. Haqiqiy to‘lov uchun:
- Xalqaro: `stripe`
- O‘zbekiston: `click.uz` yoki `payme.uz`

To‘lov muvaffaqiyatli bo‘lganda `update_coins(user_id, user_coins + amount)` chaqiring.

## 📜 Litsenziya

MIT
