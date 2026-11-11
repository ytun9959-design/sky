import os
import uuid
import shutil
import asyncio
import subprocess
import time
from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ==================== Configuration ====================
BOT_TOKEN = "9200315361:AAHnys_q3LYcRXDvqti4FGxh4Xcq8yK0GKI"
ADMIN_ID = 5617375002
ADMIN_CONTACT = "@Kenobe21"
CHANNEL_LINK = "https://t.me/Skyblue021"
CHANNEL_USERNAME = "@Skyblue021"

# ==================== Settings ====================
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

MAX_CONCURRENT_DOWNLOADS = 3
MAX_FILE_SIZE_MB = 50
FILE_TTL_SECONDS = 3600

# ==================== Runtime State ====================
user_links = defaultdict(list)
user_platform = {} 
download_semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
active_tasks = {}
verified_users = set()


# ==================== Helpers ====================
def cleanup_old_files():
    now = time.time()
    for fname in os.listdir(DOWNLOAD_DIR):
        fpath = os.path.join(DOWNLOAD_DIR, fname)
        try:
            if os.path.isfile(fpath) and (now - os.path.getmtime(fpath)) > FILE_TTL_SECONDS:
                os.remove(fpath)
        except Exception:
            pass


async def run_ytdlp(cmd, timeout=900):
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        return process.returncode, stdout.decode(errors="ignore"), stderr.decode(errors="ignore")
    except asyncio.TimeoutError:
        try:
            process.kill()
        except Exception:
            pass
        return -1, "", "Timeout"


async def check_channel_membership(context, user_id):
    if user_id in verified_users:
        return True
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ("member", "administrator", "creator"):
            verified_users.add(user_id)
            return True
    except Exception:
        pass
    return False


async def send_join_prompt(update, context):
    keyboard = [
        [InlineKeyboardButton("📢 Channel Join", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Join ပြီးပါပြီ", callback_data="check_join")],
    ]
    await update.message.reply_text(
        f"⚠️ Bot အသုံးပြုရန် Channel ကို Join ပေးပါ။\n\n📢 {CHANNEL_LINK}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ==================== Handlers ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_channel_membership(context, user_id):
        await send_join_prompt(update, context)
        return

    # 🚨 Menu Button အသစ်များ (Admin ကို အောက်ဆုံးမှာ ထားသည်)
    keyboard = [
        [InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("📥 Downloaded (ဒေါင်းလုဒ်များ)", callback_data="downloaded_list")],
        [InlineKeyboardButton("👨‍💻 Admin", url=f"https://t.me/{ADMIN_CONTACT.lstrip('@')}")],
    ]
    await update.message.reply_text(
        "👋 မင်္ဂလာပါ!\n\n"
        "📌 **Video/MP3 ဒေါင်းလုဒ်လုပ်ရန် လမ်းညွှန်**\n"
        "1️⃣ ဒေါင်းလုဒ်လုပ်ချင်တဲ့ YouTube, TikTok သို့မဟုတ် Facebook link ကို ဒီ chat ထဲပို့ပါ။\n"
        "2️⃣ ပြီးရင် ဘယ် Platform က Link လဲဆိုတာကို ရွေးချယ်ပါ။\n"
        "3️⃣ ပြီးမှ Video (သို့မဟုတ်) MP3 ကို ရွေးချယ်ပါ။\n"
        "4️⃣ နှိပ်လိုက်ရင် Bot က ဒေါင်းလုဒ်ဆွဲပြီး ပြန်ပို့ပေးပါလိမ့်မယ်။",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ **အကူအညီ**\n\n"
        "1. YouTube/TikTok/Facebook link ကို ပို့ပါ\n"
        "2. ဘယ် Platform လဲ ရွေးပါ\n"
        "3. Video / MP3 ရွေးပါ\n"
        "4. Bot က ဒေါင်းလုဒ်ဆွဲပြီး ပြန်ပို့ပေးပါမယ်\n\n"
        f"⚠️ ဖိုင်ဆိုဒ် {MAX_FILE_SIZE_MB}MB အထက်ကို ပို့မရပါ။\n\n"
        f"📢 {CHANNEL_LINK}\n👨‍💻 {ADMIN_CONTACT}",
        parse_mode="Markdown"
    )


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await check_channel_membership(context, user_id):
        await send_join_prompt(update, context)
        return

    text = update.message.text.strip()
    if not text.startswith(("http://", "https://")):
        await update.message.reply_text("❌ ကျေးဇူးပြု၍ မှန်ကန်သော YouTube, TikTok သို့မဟုတ် Facebook link ကို ပို့ပေးပါ။")
        return

    user_links[user_id] = [text]

    keyboard = [
        [InlineKeyboardButton("🔴 YouTube Link", callback_data="platform_youtube")],
        [InlineKeyboardButton("🔵 Facebook Link", callback_data="platform_facebook")],
        [InlineKeyboardButton("⚫ TikTok Link", callback_data="platform_tiktok")],
    ]
    await update.message.reply_text(
        f"✅ Link လက်ခံပြီးပါပြီ။\n\nဒါက ဘယ် Platform က Link လဲ? ရွေးချယ်ပေးပါ -",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if await check_channel_membership(context, user_id):
        await query.edit_message_text("✅ Join ပြီးပါပြီ။ ကျေးဇူးတင်ပါတယ်။ /start ကို နှိပ်ပါ။")
    else:
        await query.answer("❌ Channel ကို Join မထားသေးပါ။", show_alert=True)


# 🚨 Downloaded Button ကို နှိပ်လိုက်ရင် Link ထည့်ခိုင်းမည့် စာသား
async def downloaded_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📥 **ဒေါင်းလုဒ်လုပ်ရန်**\n\n"
        "ကျေးဇူးပြု၍ ဒေါင်းလုဒ်လုပ်ချင်တဲ့ **Link** ကို ဒီ Chat ထဲမှာ ရိုက်ထည့်ပြီး ပို့ပေးပါ။"
    )


async def platform_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    platform = query.data.replace("platform_", "")
    
    user_platform[user_id] = platform

    keyboard = [
        [
            InlineKeyboardButton("🎬 Video ဒေါင်းမယ်", callback_data="choice_video"),
            InlineKeyboardButton("🎵 MP3 ဒေါင်းမယ်", callback_data="choice_mp3"),
        ]
    ]
    
    platform_names = {"youtube": "YouTube", "facebook": "Facebook", "tiktok": "TikTok"}
    await query.edit_message_text(
        f"✅ Platform: **{platform_names.get(platform, platform)}** ကို ရွေးပြီးပါပြီ။\n\nဘာကို ဒေါင်းလုဒ်လုပ်မလဲ?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    choice = query.data.replace("choice_", "")

    links = user_links.get(user_id, [])
    platform = user_platform.get(user_id, "unknown")

    if not links:
        await query.edit_message_text("❌ Link မတွေ့ပါ။ Link တစ်ခု အရင်ပို့ပေးပါ။")
        return

    user_links[user_id] = []
    user_platform.pop(user_id, None)

    await query.edit_message_text("⏳ ဒေါင်းလုဒ် စတင်နေပါပြီ... ခဏစောင့်ပါ။")

    active_tasks[user_id] = active_tasks.get(user_id, 0) + 1
    asyncio.create_task(process_single_link(context, user_id, links[0], choice, platform))


async def process_single_link(context, user_id, url, choice, platform):
    chat_id = user_id
    file_id = str(uuid.uuid4())
    user_dir = os.path.join(DOWNLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    out_template = os.path.join(user_dir, f"{file_id}.%(ext)s")

    async with download_semaphore:
        try:
            if platform == "youtube":
                if choice == "video":
                    cmd = ["yt-dlp", "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", "--merge-output-format", "mp4", "--no-warnings", "-o", out_template, url]
                else:
                    cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "--no-warnings", "-o", out_template, url]
            
            elif platform == "tiktok":
                if choice == "video":
                    cmd = ["yt-dlp", "--impersonate", "chrome", "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", "--merge-output-format", "mp4", "--no-warnings", "-o", out_template, url]
                else:
                    cmd = ["yt-dlp", "--impersonate", "chrome", "-x", "--audio-format", "mp3", "--no-warnings", "-o", out_template, url]
            
            elif platform == "facebook":
                if choice == "video":
                    cmd = ["yt-dlp", "--impersonate", "chrome", "-f", "best", "--no-warnings", "-o", out_template, url]
                else:
                    cmd = ["yt-dlp", "--impersonate", "chrome", "-x", "--audio-format", "mp3", "--no-warnings", "-o", out_template, url]
            
            else:
                if choice == "video":
                    cmd = ["yt-dlp", "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", "--merge-output-format", "mp4", "--no-warnings", "-o", out_template, url]
                else:
                    cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "--no-warnings", "-o", out_template, url]

            returncode, stdout, stderr = await run_ytdlp(cmd)

            if returncode != 0:
                err = stderr[-300:] if stderr else "Unknown error"
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ ဒေါင်းလုဒ် မအောင်မြင်ပါ။\n\nError: {err}\n\n"
                         f"💡 YouTube အတွက် Cookie လိုအပ်နိုင်ပါတယ်။"
                )
                return

            files = [os.path.join(user_dir, f) for f in os.listdir(user_dir) if f.startswith(file_id)]

            if not files:
                await context.bot.send_message(chat_id=chat_id, text="❌ ဖိုင် မတွေ့ပါ။")
                return

            for fpath in files:
                size_mb = os.path.getsize(fpath) / (1024 * 1024)
                if size_mb > MAX_FILE_SIZE_MB:
                    await context.bot.send_message(chat_id=chat_id, text=f"⚠️ ဖိုင်က {size_mb:.1f}MB ရှိလို့ မပို့နိုင်ပါ။")
                    os.remove(fpath)
                    continue

                with open(fpath, "rb") as f:
                    if choice == "video":
                        await context.bot.send_video(chat_id=chat_id, video=f)
                    else:
                        await context.bot.send_audio(chat_id=chat_id, audio=f)

                os.remove(fpath)

            # 🚨 ဒေါင်းလုဒ်ပြီးတာနဲ့ နောက်တစ်ခု ဆက်လုပ်ဖို့ ခလုတ်လေး ပြပေးမယ်
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("📥 နောက်တစ်ခု ထပ်ဒေါင်းမည်", callback_data="downloaded_list")]
            ])
            await context.bot.send_message(chat_id=chat_id, text="✅ ပြီးပါပြီ! နောက်တစ်ခု ဒေါင်းလိုပါက အောက်က ခလုတ်ကို နှိပ်ပါ။", reply_markup=markup)

        except Exception as e:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Error: {e}")
        finally:
            active_tasks[user_id] = max(0, active_tasks.get(user_id, 1) - 1)
            cleanup_old_files()
            try:
                if os.path.exists(user_dir) and not os.listdir(user_dir):
                    shutil.rmtree(user_dir, ignore_errors=True)
            except Exception:
                pass


# ==================== Main ====================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))
    
    app.add_handler(CallbackQueryHandler(platform_handler, pattern="^platform_"))
    app.add_handler(CallbackQueryHandler(choice_handler, pattern="^choice_"))
    app.add_handler(CallbackQueryHandler(downloaded_list, pattern="^downloaded_list$"))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    print("🚀 Bot စတင်နေပါပြီ...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
