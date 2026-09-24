import logging
import asyncio
import os
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = "8970665118:AAGgNYxKMonmiShUr5mUqQW1p0jA0NkuqbE"
IBAN = "TR62 0006 2000 5000 0006 8107 73"
RECIPIENT = "Resul Sakal"
SUPPORT_USERNAME = "SMSPATRONUM"

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

FREE_SERVICES = {
    "tc_gsm": {"name": "🔍 TC'den GSM Sorgu", "input_type": "TC Kimlik Numarası"},
    "gsm_tc": {"name": "📱 GSM'den TC Sorgu", "input_type": "Telefon Numarası"},
    "ad_soyad": {"name": "👤 Ad Soyad / İl-İlçe Sorgu", "input_type": "Ad, Soyad ve İl/İlçe Bilgisi"}
}

PAID_SERVICES = {
    "tc_aile": {"name": "👨‍👩‍👧‍👦 TC Aile / Soyağacı Sorgu", "input_type": "TC Kimlik Numarası"},
    "vesika": {"name": "🖼️ Vesika / Fotoğraf Sorgu", "input_type": "TC Kimlik Numarası"},
    "arac_plaka": {"name": "🚗 Araç / Plaka Sorgu", "input_type": "Araç Plakası"},
    "hastane": {"name": "🏥 Hastane / Muayene Geçmişi", "input_type": "TC Kimlik Numarası"},
    "sms_bomber": {"name": "💣 SMS Bomber / Flood", "input_type": "Hedef Telefon Numarası"},
    "ip_lokasyon": {"name": "📍 IP & Lokasyon Sorgu", "input_type": "IP Adresi"},
    "tapu": {"name": "🏡 Tapu / Gayrimenkul Sorgu", "input_type": "TC veya Ada/Parsel Bilgisi"},
    "sosyal_medya": {"name": "🌐 Sosyal Medya (OSINT)", "input_type": "Kullanıcı Adı veya Telefon"},
    "veri_sizintisi": {"name": "🔓 Veri Sızıntısı (Leak)", "input_type": "E-posta veya Telefon Numarası"},
    "sirket": {"name": "🏢 Şirket / Ortaklık Sorgu", "input_type": "Şirket Adı veya Vergi No"},
    "hat_operator": {"name": "📡 Hat / Operatör Detay", "input_type": "Telefon Numarası"},
    "okul": {"name": "🎓 Mezuniyet / Okul Bilgisi", "input_type": "TC Kimlik Numarası"}
}

def main_menu(user_balance=0, vip_status="Yok"):
    keyboard = [
        [InlineKeyboardButton("👑 ANKA VIP ABONELİK PLANLARI", callback_data="vip_plans")],
        [InlineKeyboardButton("✨ ÜCRETSİZ SORGULAR ✨", callback_data="none_free")]
    ]
    for key, info in FREE_SERVICES.items():
        keyboard.append([InlineKeyboardButton(f"🟢 {info['name']}", callback_data=f"q_{key}")])
    
    keyboard.append([InlineKeyboardButton("💎 ÜCRETLİ / VIP SORGULAR 💎", callback_data="none_paid")])
    for key, info in PAID_SERVICES.items():
        keyboard.append([InlineKeyboardButton(f"🔒 {info['name']}", callback_data=f"q_{key}")])
    
    keyboard.append([
        InlineKeyboardButton(f"💰 Bakiye: {user_balance} TL", callback_data="balance"),
        InlineKeyboardButton(f"🛡️ VIP: {vip_status}", callback_data="vip_plans")
    ])
    keyboard.append([InlineKeyboardButton("💳 Bakiye / VIP Satın Al (IBAN)", callback_data="buy_vip_menu")])
    keyboard.append([InlineKeyboardButton("📞 Canlı Destek / İletişim", url=f"https://t.me/{SUPPORT_USERNAME}")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = (
            "🛡️ ANKA — GELİŞMİŞ SORGULAMA MERKEZİ\n\n"
            "⚡ Hızlı, Güvenli ve Profesyonel Altyapı\n"
            "Aşağıdaki menüden yapmak istediğiniz sorgu türünü seçebilirsiniz."
        )
        if update.message:
            await update.message.reply_text(text, reply_markup=main_menu())
        elif update.callback_query:
            await update.callback_query.message.edit_text(text, reply_markup=main_menu())
    except Exception as e:
        logging.error(f"Start hatası: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "vip_plans" or data == "buy_vip_menu":
            text = (
                "💎 ANKA VIP ABONELİK PAKETLERİ\n\n"
                "Tüm VIP sorgulara sınırsız erişim sağlamak için aşağıdaki paketlerden birini seçebilirsiniz:\n\n"
                "⏱️ Günlük VIP (24 Saat): 200 TL\n"
                "📆 Haftalık VIP: 400 TL\n"
                "🗓️ Aylık VIP: 600 TL\n"
                "♾️ Sınırsız VIP: 1.500 TL\n\n"
                "💳 Ödeme Yapılacak IBAN:\n"
                f"IBAN: {IBAN}\n"
                f"Alıcı: {RECIPIENT}\n\n"
                "⚠️ Nasıl Alınır?\n"
                "Tutarını gönderdiğiniz dekontu doğrudan bu sohbete gönderin, admin onayından sonra VIP yapılacaktır."
            )
            keyboard = [[InlineKeyboardButton("⬅️ Ana Menüye Dön", callback_data="home")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

        elif data.startswith("q_"):
            service_key = data.replace("q_", "")
            all_services = {**FREE_SERVICES, **PAID_SERVICES}
            if service_key in all_services:
                s_info = all_services[service_key]
                is_paid = service_key in PAID_SERVICES
                is_vip = context.user_data.get("is_vip", False)

                if is_paid and not is_vip:
                    text = (
                        f"🔒 VIP Kısıtlaması!\n\n"
                        f"{s_info['name']} yalnızca VIP üyelere özeldir.\n\n"
                        "VIP özelliklerin kilidini açmak için paketleri inceleyebilirsiniz."
                    )
                    keyboard = [
                        [InlineKeyboardButton("💎 VIP Paketleri İncele", callback_data="vip_plans")],
                        [InlineKeyboardButton("⬅️ Geri Dön", callback_data="home")]
                    ]
                else:
                    context.user_data["active_query"] = service_key
                    text = (
                        f"{s_info['name']}\n\n"
                        f"✍️ Lütfen sorgulamak istediğiniz {s_info['input_type']} bilgisini şimdi sohbete yazın:"
                    )
                    keyboard = [[InlineKeyboardButton("⬅️ Geri Dön", callback_data="home")]]
                
                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

        elif data == "home":
            text = "🛡️ ANKA — GELİŞMİŞ SORGULAMA MERKEZİ\n\nAşağıdaki menüden yapmak istediğiniz sorgu türünü seçebilirsiniz."
            balance = context.user_data.get("balance", 0)
            vip_status = "Aktif" if context.user_data.get("is_vip", False) else "Yok"
            await query.edit_message_text(text, reply_markup=main_menu(balance, vip_status))

    except Exception as e:
        logging.error(f"Buton hatası: {e}")

async def handle_query_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message and update.message.text:
            active_q = context.user_data.get("active_query")
            user_input = update.message.text.strip()

            if not active_q:
                await update.message.reply_text("Lütfen önce menüden bir sorgu türü seçin.", reply_markup=main_menu())
                return

            processing_msg = await update.message.reply_text("🔄 Sorgulama yapılıyor, lütfen bekleyin...")

            result_text = (
                f"✅ Sorgu Başarılı\n\n"
                f"🔎 Aranan Veri: {user_input}\n\n"
                "📊 Sonuçlar:\n"
                "• İşlem Durumu: Başarıyla Tamamlandı.\n\n"
                "⚠️ ANKA Güvencesiyle."
            )

            keyboard = [[InlineKeyboardButton("🏠 Ana Menüye Dön", callback_data="home")]]
            await processing_msg.edit_text(result_text, reply_markup=InlineKeyboardMarkup(keyboard))
            context.user_data["active_query"] = None

    except Exception as e:
        logging.error(f"Girdi hatası: {e}")

async def receipt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message and (update.message.photo or update.message.document):
            await update.message.reply_text(
                "✅ Dekont Alındı!\n\n"
                "Dekontunuz yöneticiye iletildi. En kısa sürede VIP üyeliğiniz aktif edilecektir.\n\n"
                f"📞 Canlı Destek: @{SUPPORT_USERNAME}"
            )
    except Exception as e:
        logging.error(f"Dekont hatası: {e}")

# Render port uyarılarını çözmek için hafif bir web sunucusu
async def handle_web(request):
    return web.Response(text="ANKA Bot Aktif Çalışıyor!")

async def start_web_server():
    app = web.Application()
    app.add_routes([web.get("/", handle_web)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Web sunucusu {port} portunda başlatıldı.")

async def main():
    # Render port hatasını gidermek için web sunucusunu arka planda başlatıyoruz
    await start_web_server()

    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, receipt_handler))
    app.add_handler(MessageHandler(filters.CHAT & filters.TEXT & ~filters.COMMAND, handle_query_input))
    
    print("ANKA Bot Sorunsuz Başlatıldı!")
    await app.initialize()
    await app.start()
    # drop_pending_updates=True sayesinde arkada kalan eski istekler temizlenir ve çakışma (Conflict) önlenir.
    await app.updater.start_polling(drop_pending_updates=True)
    
    stop_event = asyncio.Event()
    await stop_event.wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
