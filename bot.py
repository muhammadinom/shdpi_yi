import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton, 
    ReplyKeyboardMarkup, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)

import database as db

from aiogram.client.session.aiohttp import AiohttpSession

from aiogram.client.session.aiohttp import AiohttpSession

BOT_TOKEN = "8845868386:AAEtQUdi5jCJJEjswQfgbevQ9OeMLAZCpCU"
ADMIN_ID = 5437507666  # ⚠️ Telegram ID

# PythonAnywhere uchun maxsus proksi
session = AiohttpSession(proxy="http://proxy.server:3128")

bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher()

# Bazani ishga tushirish
db.init_db()

# 1. State (Holatlar) klasslari
class RegistrationForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_faculty = State()
    waiting_for_group = State()
    waiting_for_phone = State()

class CertificateForm(StatesGroup):
    waiting_for_title = State()
    waiting_for_file = State()

class AppealForm(StatesGroup):
    waiting_for_text = State()

# Menyular
def main_menu():
    kb = [
        [KeyboardButton(text="Profil"), KeyboardButton(text="Sertifikatlarim")],
        [KeyboardButton(text="Klublar"), KeyboardButton(text="Rahbariyat")],
        [KeyboardButton(text="✍️ Murojaat qoldirish")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# /start komandasi
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        f"Assalomu alaykum, {message.from_user.first_name}!\n"
        "SHDPI Yoshlar ittifoqi botiga xush kelibsiz.",
        reply_markup=main_menu()
    )

# 2. "👤 Profil" tugmasi bosilganda
@dp.message(F.text == "Profil")
async def profile_handler(message: types.Message, state: FSMContext):
    user_telegram_id = message.from_user.id
    user_data = db.get_user(user_telegram_id)
    
    if not user_data:
        await message.answer(
            "⚠️ <b>Siz hali ro'yxatdan o'tmagansiz!</b>\n\n"
            "Profil yaratish uchun iltimos, to'liq <b>F.I.SH</b> ingizni kiriting:\n"
            "(Masalan: <i>Raxmatov Oybek Odil o'g'li</i>)",
            parse_mode="HTML"
        )
        await state.set_state(RegistrationForm.waiting_for_name)
    else:
        certs = db.get_user_certs(user_telegram_id)
        
        text = (
            "<b>🎓 Talaba Profil Ma'lumotlari:</b>\n\n"
            f"<b>👤 F.I.SH:</b> {user_data['full_name']}\n"
            f"<b>🆔 ID:</b> {user_data['student_id']}\n"
            f"<b>🏛 Fakultet:</b> {user_data['faculty']}\n"
            f"<b>👥 Guruh:</b> {user_data['group']}\n"
            f"<b>📞 Telefon:</b> {user_data['phone']}\n\n"
            "<b>📊 Statistika:</b>\n"
            f"⭐ <b>Reyting ball:</b> {user_data['balls']} ball\n"
            f"📜 <b>Tasdiqlangan sertifikatlar:</b> {len(certs)} ta\n"
        )
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📥 Sertifikat yuklash", callback_data="upload_cert")]
            ]
        )
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

# ----------------- RO'YXATDAN O'TISH BOSQICHLARI -----------------

@dp.message(RegistrationForm.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("🏛 <b>Fakultetingiz nomini kiriting:</b>\n(Masalan: <i>Pedagogika </i>)", parse_mode="HTML")
    await state.set_state(RegistrationForm.waiting_for_faculty)

@dp.message(RegistrationForm.waiting_for_faculty)
async def process_faculty(message: types.Message, state: FSMContext):
    await state.update_data(faculty=message.text)
    await message.answer("👥 <b>Guruhingizni kiriting:</b>\n(Masalan: <i>XT 1-25 guruh</i>)", parse_mode="HTML")
    await state.set_state(RegistrationForm.waiting_for_group)

@dp.message(RegistrationForm.waiting_for_group)
async def process_group(message: types.Message, state: FSMContext):
    await state.update_data(group=message.text)
    
    phone_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        "📱 <b>Telefon raqamingizni kiriting:</b>\n(Tugmani bosing yoki quyidagi formatda yozing: <i>+998901234567</i>)",
        parse_mode="HTML",
        reply_markup=phone_keyboard
    )
    await state.set_state(RegistrationForm.waiting_for_phone)

@dp.message(RegistrationForm.waiting_for_phone, F.contact | F.text)
async def process_phone(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    phone_number = message.contact.phone_number if message.contact else message.text
    
    student_id = f"SHDPI-{db.get_last_student_id()}"
    
    db.add_user(
        user_id=message.from_user.id,
        full_name=user_data['full_name'],
        faculty=user_data['faculty'],
        group_name=user_data['group'],
        phone=phone_number,
        student_id=student_id
    )
    
    await message.answer(
        "🎉 <b>Ro'yxatdan muvaffaqiyatli o'tdingiz!</b>\n'Profil' tugmasini bosib kabinetingizni ko'rishingiz mumkin.",
        parse_mode="HTML",
        reply_markup=main_menu()
    )
    await state.clear()

# ----------------- SERTIFIKAT YUKLASH BOSQICHLARI -----------------

@dp.callback_query(F.data == "upload_cert")
async def start_cert_upload(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📜 Iltimos, sertifikat yoki diplom nomini kiriting:\n(Masalan: <i>Hakaton 1-o'rin diplom</i>)", parse_mode="HTML")
    await state.set_state(CertificateForm.waiting_for_title)
    await call.answer()

@dp.message(CertificateForm.waiting_for_title)
async def process_cert_title(message: types.Message, state: FSMContext):
    await state.update_data(cert_title=message.text)
    await message.answer("📥 Endi sertifikat faylini (rasm yoki PDF formatda) yuboring:")
    await state.set_state(CertificateForm.waiting_for_file)

@dp.message(CertificateForm.waiting_for_file, F.photo | F.document)
async def process_cert_file(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    cert_title = user_data.get("cert_title")
    user_info = db.get_user(message.from_user.id) or {}
    
    file_id = message.photo[-1].file_id if message.photo else message.document.file_id

    await message.answer(
        f"✅ <b>Sertifikat qabul qilindi!</b>\n\n"
        f"📌 <b>Nomi:</b> {cert_title}\n"
        f"⏳ <b>Holati:</b> Kutilmoqda (Admin tasdiqlagach ball qo'shiladi)",
        parse_mode="HTML"
    )

    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash (+15 ball)", callback_data=f"approve_{message.from_user.id}_{cert_title}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{message.from_user.id}_{cert_title}")
            ]
        ]
    )
    
    admin_caption = (
        "📥 <b>YANGI SERTIFIKAT TUSHDI!</b>\n\n"
        f"👤 <b>Talaba:</b> {user_info.get('full_name', 'Noma\'lum')}\n"
        f"🆔 <b>ID:</b> {user_info.get('student_id', 'Noma\'lum')}\n"
        f"🏛 <b>Fakultet:</b> {user_info.get('faculty', 'Noma\'lum')}\n"
        f"📞 <b>Telefon:</b> {user_info.get('phone', 'Noma\'lum')}\n"
        f"📌 <b>Sertifikat nomi:</b> {cert_title}"
    )

    try:
        if message.photo:
            await bot.send_photo(chat_id=ADMIN_ID, photo=file_id, caption=admin_caption, parse_mode="HTML", reply_markup=admin_keyboard)
        else:
            await bot.send_document(chat_id=ADMIN_ID, document=file_id, caption=admin_caption, parse_mode="HTML", reply_markup=admin_keyboard)
    except Exception as e:
        print(f"Admin-ga fayl yuborishda xatolik: {e}")

    await state.clear()

# ----------------- ADMIN PANEL CALLBACK HANDLERLARI -----------------

@dp.callback_query(F.data.startswith("approve_"))
async def approve_certificate(call: types.CallbackQuery):
    _, user_id, cert_title = call.data.split("_", 2)
    user_id = int(user_id)
    
    db.add_certificate(user_id, cert_title)
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"🎉 <b>Xushxabar!</b>\nSiz yuborgan <b>'{cert_title}'</b> sertifikatingiz tasdiqlandi!\n⭐ <b>+15 ball</b> berildi.",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Xabar yuborishda xatolik: {e}")
    
    await call.message.edit_caption(caption=call.message.caption + "\n\n✅ <b>TASDIQLANDI (+15 ball)</b>", parse_mode="HTML")
    await call.answer("Sertifikat tasdiqlandi!")

@dp.callback_query(F.data.startswith("reject_"))
async def reject_certificate(call: types.CallbackQuery):
    _, user_id, cert_title = call.data.split("_", 2)
    user_id = int(user_id)
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"❌ <b>Sertifikat rad etildi:</b>\nSiz yuborgan <b>'{cert_title}'</b> sertifikatingiz mos kelmadi yoki rad qilindi.",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Xabar yuborishda xatolik: {e}")
    
    await call.message.edit_caption(caption=call.message.caption + "\n\n❌ <b>RAD ETILDI</b>", parse_mode="HTML")
    await call.answer("Sertifikat rad etildi!")

# ----------------- MUROJAAT YUBORISH BO'LIMI -----------------

@dp.message(F.text == "✍️ Murojaat qoldirish")
async def start_appeal(message: types.Message, state: FSMContext):
    user_telegram_id = message.from_user.id
    user_info = db.get_user(user_telegram_id)
    
    if not user_info:
        await message.answer(
            "⚠️ <b>Murojaat yuborish uchun avval ro'yxatdan o'tishingiz kerak!</b>\n\n"
            "Iltimos, avval <b>'Profil'</b> tugmasini bosib ro'yxatdan o'ting.",
            parse_mode="HTML"
        )
        return

    await message.answer(
        "✍️ <b>Murojaatingiz, taklif yoki savolingizni matn ko'rinishida yozib yuboring:</b>",
        parse_mode="HTML"
    )
    await state.set_state(AppealForm.waiting_for_text)

@dp.message(AppealForm.waiting_for_text)
async def process_appeal(message: types.Message, state: FSMContext):
    user_info = db.get_user(message.from_user.id) or {}
    appeal_text = message.text

    admin_message = (
        "📩 <b>YANGI MUROJAAT MAVJUD!</b>\n\n"
        f"👤 <b>F.I.SH:</b> {user_info.get('full_name', 'Noma\'lum')}\n"
        f"🆔 <b>ID:</b> {user_info.get('student_id', 'Noma\'lum')}\n"
        f"🏛 <b>Fakultet:</b> {user_info.get('faculty', 'Noma\'lum')}\n"
        f"👥 <b>Guruh:</b> {user_info.get('group', 'Noma\'lum')}\n"
        f"📞 <b>Telefon:</b> {user_info.get('phone', 'Noma\'lum')}\n\n"
        f"📝 <b>Murojaat matni:</b>\n{appeal_text}"
    )

    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_message, parse_mode="HTML")
        await message.answer("✅ <b>Murojaatingiz rahbariyatga yuborildi!</b>\nTez orada aloqaga chiqamiz!", parse_mode="HTML")
    except Exception as e:
        await message.answer("⚠️ Murojaatni yuborishda xatolik yuz berdi. Keyinroq qayta urinib ko'ring.")
        print(f"Murojaat yuborishda xatolik: {e}")

    await state.clear()

# ----------------- BOSHQA TUGMALAR -----------------

@dp.message(F.text == "Klublar")
async def clubs_handler(message: types.Message):
    text = (
        "<b>🏛 SHDPI Yoshlar ittifoqi tomonidan tashkil etilgan Klublar:</b>\n\n"
        "1. 🎭 <b>'Zakovat' Intellektual Klubi</b>\n"
        "2. 💻 <b>'IT & Digital' Klubi</b>\n"
        "3. 🗣 <b>'Debat & Nutq' Klubi</b>\n"
        "4. 🎨 <b>'Ijodkor Yoshlar' Klubi</b>\n"
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "Rahbariyat")
async def leadership_handler(message: types.Message):
    text = (
        "<b>👥 Rahbariyat:</b>\n\n"
        "<b>👔 Prorektor:</b> Ochilov Laziz Siddiqovich\n\n"
        " — Qabul kunlari: Dushanba - Juma (14:00 - 17:00)\n"
        " — Telefon: +998979010100\n\n"
        "<b>👩‍🎓 Yoshlar yetakchisi:</b> Fayzullayeva Dilnura Husan qizi\n\n"
        " — Telefon: +998914540746\n"
        " — Telegram: @Dilnur_Husanovna"
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "Sertifikatlarim")
async def certs_handler(message: types.Message):
    user_id = message.from_user.id
    certs = db.get_user_certs(user_id)
    if certs:
        certs_list = "\n".join([f"• {c}" for c in certs])
        await message.answer(f"<b>📜 Sizning tasdiqlangan sertifikatlaringiz:</b>\n\n{certs_list}", parse_mode="HTML")
    else:
        await message.answer("📜 Sizda hozircha tasdiqlangan sertifikatlar mavjud emas.")

async def main():
    print("Bot SQLite bazasi bilan ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())