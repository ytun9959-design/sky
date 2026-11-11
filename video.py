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
# သင့် Bot Token နဲ့ အချက်အလက်များကို ဒီမှာ တိုက်ရိုက် ထည့်ထားပါတယ်
BOT_TOKEN = "9200315361:AAHnys_q3LYcRXDvqti4FGxh4Xcq8yK0GKI"
ADMIN_ID = 5617375002
ADMIN_CONTACT = "@Kenobe21"
CHANNEL_LINK = "https://t.me/Skyblue021"
CHANNEL_USERNAME = "@Skyblue021"
BOT_LINK = "https://t.me/SkyBlueFreevpn_bot?start="

# ==================== Settings ====================
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

MAX_CONCURRENT_DOWNLOADS = 3
MAX_FILE_SIZE_MB = 50
MAX_PLAYLIST_ITEMS = 30
FILE_TTL_SECONDS = 3600
YTDLP_TIMEOUT = 900

# ==================== Runtime State ====================
user_links = defaultdict(list)
user_choice = {}
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


async def run_ytdlp(cmd, timeout=YTDLP_TIMEOUT):
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

    keyboard = [
        [InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("👨‍💻 Admin", url=f"https://t.me/{ADMIN_CONTACT.lstrip('@')}")],
    ]
    await update.message.reply_text(
        "👋 မင်္ဂလာပါ!\n\n"
        "📌 အသုံးပြုပုံ -\n"
        "• Video/MP3 link တစ်ခု သို့မဟုတ် အများကြီး ပို့ပါ\n"
        "• Playlist/Channel link လည်း ရပါတယ်\n"
        "• ပြီးရင် Video / MP3 ရွေးပါ\n\n"
        "📊 Commands -\n"
        "/start - စတင်ရန်\n"
        "/status - အခြေအနေ\n"
        "/clear - စာရင်းရှင်း\n"
        "/help - အကူအညီ",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"❓ အကူအညီ\n\n"
        f"1️⃣ YouTube/TikTok link ကို ပို့ပါ\n"
        f"2️⃣ Link အများကြီး (line တစ်ကြောင်းစီ) ပို့နိုင်သည်\n"
        f"3️⃣ Video သို့မဟုတ် MP3 ရွေးပါ\n"
        f"4️⃣ ဒေါင်းလုဒ်ပြီးရင် bot က ပြန်ပို့ပေးမည်\n\n"
        f"⚠️ {MAX_FILE_SIZE_MB}MB အထက်ဖိုင် မပို့နိုင်ပါ။\n\n"
        f"📢 {CHANNEL_LINK}\n👨‍💻 {ADMIN_CONTACT}"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    pending = len(user_links.get(user_id, []))
    active = active_tasks.get(user_id, 0)
    await update.message.reply_text(
        f"📊 အခြေအနေ\n\n"
        f"• စောင့်ဆိုင်းနေသော link: {pending}\n"
        f"• လုပ်ဆောင်နေသော task: {active}"
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_links[user_id].clear()
    user_choice.pop(user_id, None)
    await update.message.reply_text("✅ စာရင်း ရှင်းပြီးပါပြီ။")


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await check_channel_membership(context, user_id):
        await send_join_prompt(update, context)
        return

    text = update.message.text.strip()
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    valid_links = [l for l in lines if l.startswith(("http://", "https://"))]

    if not valid_links:
        await update.message.reply_text("❌ ကျေးဇူးပြု၍ မှန်ကန်သော link ပို့ပါ။")
        return

    user_links[user_id].extend(valid_links)
    total_pending = len(user_links[user_id])

    keyboard = [
        [
            InlineKeyboardButton("🎬 Video", callback_data="video"),
            InlineKeyboardButton("🎵 MP3", callback_data="mp3"),
        ]
    ]
    await update.message.reply_text(
        f"✅ Link {len(valid_links)} ခု လက်ခံပြီး\n"
        f"(စုစုပေါင်း စောင့်ဆိုင်းနေသည်: {total_pending})\n\n"
        f"ဘာကို ဒေါင်းလုဒ်လုပ်မလဲ?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if await check_channel_membership(context, user_id):
        await query.edit_message_text("✅ Join ပြီးပါပြီ။ /start ကို နှိပ်ပါ။")
    else:
        await query.answer("❌ Channel ကို Join မထားသေးပါ။", show_alert=True)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    choice = query.data

    links = user_links.get(user_id, [])
    if not links:
        await query.edit_message_text("❌ Link မတွေ့ပါ။ ပြန်ပို့ပေးပါ။")
        return

    user_choice[user_id] = choice
    user_links[user_id] = []

    await query.edit_message_text(
        f"⏳ Link {len(links)} ခု ဒေါင်းလုဒ် စတင်နေပါပြီ...\n"
        f"(တစ်ပြိုင်နက် {MAX_CONCURRENT_DOWNLOADS} ခု)"
    )

    active_tasks[user_id] = active_tasks.get(user_id, 0) + len(links)

    for idx, link in enumerate(links, 1):
        asyncio.create_task(
            process_single_link(context, user_id, link, choice, idx, len(links))
        )


async def process_single_link(context, user_id, url, choice, idx, total):
    chat_id = user_id
    file_id = str(uuid.uuid4())
    user_dir = os.path.join(DOWNLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    out_template = os.path.join(user_dir, f"{file_id}.%(ext)s")

    async with download_semaphore:
        try:
            if choice == "video":
                cmd = [
                    "yt-dlp",
                    "-f", "bv*+ba/b",
                    "--merge-output-format", "mp4",
                    "--playlist-end", str(MAX_PLAYLIST_ITEMS),
                    "--no-warnings",
                    "-o", out_template,
                    url,
                ]
            else:
                cmd = [
                    "yt-dlp",
                    "-x", "--audio-format", "mp3",
                    "--playlist-end", str(MAX_PLAYLIST_ITEMS),
                    "--no-warnings",
                    "-o", out_template,
                    url,
                ]

            returncode, stdout, stderr = await run_ytdlp(cmd)

            if returncode != 0:
                err = stderr[-300:] if stderr else "Unknown error"
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Link {idx}/{total} မအောင်မြင်ပါ\n{url}\n\n{err}",
                )
                return

            files = [
                os.path.join(user_dir, f)
                for f in os.listdir(user_dir)
                if f.startswith(file_id)
            ]

            if not files:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Link {idx}/{total} ဖိုင် မတွေ့ပါ။",
                )
                return

            for fpath in files:
                size_mb = os.path.getsize(fpath) / (1024 * 1024)
                if size_mb > MAX_FILE_SIZE_MB:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"⚠️ {os.path.basename(fpath)} ({size_mb:.1f}MB) ကို မပို့နိုင်ပါ။",
                    )
                    os.remove(fpath)
                    continue

                try:
                    with open(fpath, "rb") as f:
                        if choice == "video":
                            await context.bot.send_video(
                                chat_id=chat_id, video=f,
                                caption=f"✅ {idx}/{total}",
                            )
                        else:
                            await context.bot.send_audio(
                                chat_id=chat_id, audio=f,
                                caption=f"✅ {idx}/{total}",
                            )
                except Exception as e:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"❌ ပို့မရပါ: {e}",
                    )
                finally:
                    try:
                        os.remove(fpath)
                    except Exception:
                        pass

            await context.bot.send_message(
                chat_id=chat_id,
                text=f"✅ Link {idx}/{total} ပြီးပါပြီ!",
            )

        except Exception as e:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Error (Link {idx}/{total}): {e}",
            )
        finally:
            active_tasks[user_id] = max(0, active_tasks.get(user_id, 1) - 1)
            cleanup_old_files()
            try:
                if os.path.exists(user_dir) and not os.listdir(user_dir):
                    shutil.rmtree(user_dir, ignore_errors=True)
            except Exception:
                pass


# ==================== Admin ====================
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin သာ အသုံးပြုနိုင်သည်။")
        return

    total_pending = sum(len(v) for v in user_links.values())
    total_active = sum(active_tasks.values())

    await update.message.reply_text(
        f"📊 Admin Stats\n\n"
        f"• Verified users: {len(verified_users)}\n"
        f"• Pending links: {total_pending}\n"
        f"• Active tasks: {total_active}",
    )


async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: /broadcast သင့်စာ")
        return

    message = " ".join(context.args)
    success, failed = 0, 0
    for uid in list(verified_users):
        try:
            await context.bot.send_message(chat_id=uid, text=message)
            success += 1
        except Exception:
            failed += 1

    await update.message.reply_text(
        f"📢 Broadcast ပြီးပါပြီ\n✅ အောင်မြင်: {success}\n❌ မအောင်မြင်: {failed}"
    )


# ==================== Main ====================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("broadcast", admin_broadcast))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(video|mp3)$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    print("🚀 Bot စတင်နေပါပြီ...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()