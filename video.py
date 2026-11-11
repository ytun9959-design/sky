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

# ==================== 🚨 Cookie စာသားများ (ဒီနေရာမှာ ထည့်ထားပါတယ်) ====================
COOKIE_CONTENT = """# Netscape HTTP Cookie File
# Generated for yt-dlp

.google.com	TRUE	/verify	TRUE	1810186771	SNID	ANBxh3hwC0Vski-aucdeaDIpfACib7zn1coQNFsdPLQkA1L6nC0ItfKdeP7nP4jCsJO_Kb4CpBDxYtXYY6yEPwYvpsko2FDAi_g
.mozilla.org	TRUE	/	FALSE	1828935563	_ga_B9CY1C9VBC	GS2.1.s1794375394$o1$g1$t1794375563$j58$l0$h0
.mozilla.org	TRUE	/	FALSE	1828935418	_ga	GA1.1.1077350213.1794375394
.google.com	TRUE	/	TRUE	1810186771	NID	CosDCAESvQIBM9Agl5jpeVHNUWfrgZk630Z90Z7YG-h17essjzqVFW6WupDmCnzmZlakeu1ySOKwleJXDaStvUYS0j8RWv6yNFXkhpxusb0gs7joFlwx-H_paxcOrgSwM3o3EvglgA2HvqzEBWEI_u9ciHQhDFo_VjAMk07_7nbkseYiRDLcAefZ6nhSD0DNdAF2IZ1T_Kh9998c4oi8FpwEEq-VtJrv7rd_NYLwPeWGll_lTIct0_Mhn2AJckNFHjQp2I9Y1VzMNRBp1e8QDDAlQuTTc95_F91-MhhFUznyS0MKi8F6MFWdYO8w30kfMrWBfxWmMvDChjRn5OimMmsZja-VQUSalJ5xxcuPtN0Or9_PtusuXm0gnqs76JWYT61Fiy5v36FyIlFs0ejfHJAbQOf8d7QhdXbtGr_idHNjPPuX5ygBMkUBcEpCz_x0WRpQRPRHzEQ1VsqcKsrO5M_mDm9cgi84J5AfSA6BWl4NoHu6kKNbgSmoU9gx4R2P3ccfeRweJnsiSNQj7Qk
.google.com	TRUE	/	TRUE	1794376007	__Secure-STRP	ABNhA6jkbZip1ViamdFxoA_FdSmr4V1bQKi0XeTgk1b-V83VwIrIyWaSrRBZIHnaazkid6lvdHLyG3q1c_DbDeXRceBLs1ZpJS1P
.google.com	TRUE	/	FALSE	1809927621	SEARCH_SAMESITE	CgQIoKIB
.google.com	TRUE	/	TRUE	1809927573	AEC	Aaa9EJqb-zveNASbkjje-QWUteDsIjrJ3sURLMGBuYRAeMLrff3ves-f9Q
www.google.com	FALSE	/	FALSE	1794376313	DV	k5mWCnQPmzEVcNh6fbLcG-h27-WRHBo
accounts.google.com	FALSE	/	TRUE	1828935615	__Host-GAPS	1:82kh4TaxeSTkJOBicMlfndwSeES871Cmed9kDNyJcXiHNzAm1Lo_pY5Xkzh71UYs0KLjGalGNBGfRuUOyCTT3CxaVlQrAQ:yelqi8unfPT1cPB7
accounts.google.com	FALSE	/	TRUE	1796967593	OTZ	8867860_30_30__30_
.google.com	TRUE	/	FALSE	1828935615	SID	g.a000Egnm4Cl-lwtJgTEO6eBA8ywo-xuqUsHk2TfaQyHm_kkbIdevtAoVzULWnIc8HrFzHIQY1wACgYKAQMSARMSFQHGX2MiNjGd5FTR4agUYBkx5ToffhoVAUF8yKpY6VLwoyyPg-iQNT-Gdsab0076
.google.com	TRUE	/	TRUE	1828935615	__Secure-1PSID	g.a000Egnm4Cl-lwtJgTEO6eBA8ywo-xuqUsHk2TfaQyHm_kkbIdevW30sAM1c0i0AR9B0WFxBHgACgYKAVYSARMSFQHGX2MiVPcS3q0nbGZYQEdbHh0pcxoVAUF8yKrMIJfaBDbgzMQadQ4pAAdz0076
.google.com	TRUE	/	TRUE	1828935615	__Secure-3PSID	g.a000Egnm4Cl-lwtJgTEO6eBA8ywo-xuqUsHk2TfaQyHm_kkbIdev2KBLp3CKadtoJj2FyvGroAACgYKAUMSARMSFQHGX2Mi2i5c9xQVVo3dXGX92nxKJBoVAUF8yKp7ejMDnHdEUOEI5kRBM6hw0076
accounts.google.com	FALSE	/	TRUE	1828935621	LSID	s.youtube:g.a000Egnm4GNo95NkJDKjVjm4Ok2Q-CWo-fEAjVZAvcE5t-vvWuxZUORIu4uCHBXt-HFJh36YlAACgYKAc0SARMSFQHGX2MisoACAvbb1TVk-v4UjThijRoVAUF8yKqIvRiTjDeNblZlLKITpzlR0076
accounts.google.com	FALSE	/	TRUE	1828935621	__Host-1PLSID	s.youtube:g.a000Egnm4GNo95NkJDKjVjm4Ok2Q-CWo-fEAjVZAvcE5t-vvWuxZaHrmsyLd8qTMaCXhrU23yAACgYKAdoSARMSFQHGX2MiEYqmWV5tHNo-bcqxDRl6FBoVAUF8yKqx_5EFT0r08nqfmFSTm1mK0076
accounts.google.com	FALSE	/	TRUE	1828935621	__Host-3PLSID	s.youtube:g.a000Egnm4GNo95NkJDKjVjm4Ok2Q-CWo-fEAjVZAvcE5t-vvWuxZUQwyl-FQWrZM7a4Z8TGHvAACgYKATgSARMSFQHGX2MirLCvg9wExlpLgtP-t8dQdhoVAUF8yKoSVVjonKPLZOnFs6o31Fml0076
.google.com	TRUE	/	FALSE	1828935615	HSID	AnctyZHpoNeEJnwtG
.google.com	TRUE	/	TRUE	1828935615	SSID	AiY3DLuAxu0ysakS8
.google.com	TRUE	/	FALSE	1828935615	APISID	ZQ-nBH4RG7fx4LEl/AmdCv89Ix-ERTonZc
.google.com	TRUE	/	TRUE	1828935615	SAPISID	2EdiERSP5X5l0uym/Ahc8eamhQeoF1JgbW
.google.com	TRUE	/	TRUE	1828935615	__Secure-1PAPISID	2EdiERSP5X5l0uym/Ahc8eamhQeoF1JgbW
.google.com	TRUE	/	TRUE	1828935615	__Secure-3PAPISID	2EdiERSP5X5l0uym/Ahc8eamhQeoF1JgbW
accounts.google.com	FALSE	/	TRUE	1828935616	ACCOUNT_CHOOSER	AFx_qI5MkE6yRGe5DK0JLBoB9btGxNeMpP3I-FpQKh_9s3WpPbmYKAQzrvkfWJmsmrdcJjyGHD5bFGSpV9dUcnANMQY5pFGI2VcmOZysWXjqvYSSPjmvbOeVvVe7lb36vfKvzEIxxfGi
accounts.google.com	FALSE	/	TRUE	1828935615	SMSV	ADHTe-DSwHsPQTAiuNChGvEczRvKZfIfKzZ110NGOKqFtZwfgHnzw7Dnggc5QwtxaU3TRDWGqbPtrm4M22-nBGDiduEK9-DVcMvYBpdeQJ1U7Hqy9Tty7c4
.google.com	TRUE	/	FALSE	1825911720	SIDCC	APD_SKEULGGeT_yNksLNSdiYfxCjYQA2pp__Mad8sc93ZSvOB9q73wN2O60rBx0SUZo99Iq0zg
.google.com	TRUE	/	TRUE	1825911720	__Secure-1PSIDCC	APD_SKEZtykMaTZrkP2m-d3nMd5ij8W7UcL5Q4mMefm454F8N1t6W5voBmw7VOeAqhNcgxNm
.google.com	TRUE	/	TRUE	1825911720	__Secure-3PSIDCC	APD_SKHt1k0jSGRE5EsQvCFTK-mn3XCc9EnCJfAmGXUyV4lX7XwWgiRWTRup9x9hLUAbmlDQ
gds.google.com	FALSE	/	TRUE	1796967619	OTZ	8867860_30_30__30_
.youtube.com	TRUE	/	TRUE	1825911753	__Secure-1PSIDTS	sidts-CjUBnJZzal9i1f_kpxXGaN_Qw2Sa4Q3GaoMiVdVOQ3YiEtuT0d8qQql5YyrwWkBfIHKwDVIP6xAA
.youtube.com	TRUE	/	TRUE	1825911753	__Secure-3PSIDTS	sidts-CjUBnJZzal9i1f_kpxXGaN_Qw2Sa4Q3GaoMiVdVOQ3YiEtuT0d8qQql5YyrwWkBfIHKwDVIP6xAA
.youtube.com	TRUE	/	FALSE	1828935621	HSID	A3XZRTu4Qp0yGSDjZ
.youtube.com	TRUE	/	TRUE	1828935621	SSID	Auic74DNzoRPKiU5L
.youtube.com	TRUE	/	FALSE	1828935621	APISID	ZQ-nBH4RG7fx4LEl/AmdCv89Ix-ERTonZc
.youtube.com	TRUE	/	TRUE	1828935621	SAPISID	2EdiERSP5X5l0uym/Ahc8eamhQeoF1JgbW
.youtube.com	TRUE	/	TRUE	1828935621	__Secure-1PAPISID	2EdiERSP5X5l0uym/Ahc8eamhQeoF1JgbW
.youtube.com	TRUE	/	TRUE	1828935621	__Secure-3PAPISID	2EdiERSP5X5l0uym/Ahc8eamhQeoF1JgbW
.youtube.com	TRUE	/	FALSE	1828935621	SID	g.a000Egnm4Cl-lwtJgTEO6eBA8ywo-xuqUsHk2TfaQyHm_kkbIdevtAoVzULWnIc8HrFzHIQY1wACgYKAQMSARMSFQHGX2MiNjGd5FTR4agUYBkx5ToffhoVAUF8yKpY6VLwoyyPg-iQNT-Gdsab0076
.youtube.com	TRUE	/	TRUE	1828935621	__Secure-1PSID	g.a000Egnm4Cl-lwtJgTEO6eBA8ywo-xuqUsHk2TfaQyHm_kkbIdevW30sAM1c0i0AR9B0WFxBHgACgYKAVYSARMSFQHGX2MiVPcS3q0nbGZYQEdbHh0pcxoVAUF8yKrMIJfaBDbgzMQadQ4pAAdz0076
.youtube.com	TRUE	/	TRUE	1828935621	__Secure-3PSID	g.a000Egnm4Cl-lwtJgTEO6eBA8ywo-xuqUsHk2TfaQyHm_kkbIdev2KBLp3CKadtoJj2FyvGroAACgYKAUMSARMSFQHGX2Mi2i5c9xQVVo3dXGX92nxKJBoVAUF8yKp7ejMDnHdEUOEI5kRBM6hw0076
.youtube.com	TRUE	/	TRUE	1809927740	__Secure-YNID	CtoBCAUSjAEBDB6PDOT_Sedn9thNvINDCv2_ZcadDUGXYMnHreWkcU9vpORrmL4EEYyvqZsZK-EThPjb_4xOEFkdZqwWKP_oA9Cap27GMR_HS4qE7eYF4wLeCMIgxlwJAfVqv5enAPYCt2wGxsdrJIEpMxEGVI1WQIQmVgB64z62ALfX98mVpphk-n0Dw2vzLinslSgFMkUBHFj1au8Cfkt5MEhFt_LreeHdIoBYooQYrRnRWEbjJoJ6S12dAfeD2Gz5JSWnqhrzhY1MWLZoQNZE9gYh99EAUF0Hxg0
.youtube.com	TRUE	/	FALSE	1825911753	SIDCC	APD_SKFvBsaR48V-_Z8OlZRXtbprGtyKHL-nChbFaLkjwDpbxtLkRDAHuiSNQe5-d2H6Fba3
.youtube.com	TRUE	/	TRUE	1825911753	__Secure-1PSIDCC	APD_SKFCR5PpuJqHfTa48yJPaVzczek3jWfynfY2WHtrSPaLWNG-F6k1weC2mChILINBHx7yOw
.youtube.com	TRUE	/	TRUE	1825911753	__Secure-3PSIDCC	APD_SKGMwd5FFm7RAZoFVGrqQkNgwBjr68QB2TNYPZGTIrblDmyRU72gkUiaTWFjB7_tVSLj
.youtube.com	TRUE	/	TRUE	0	YSC	pk1prS8T7E0
.youtube.com	TRUE	/	TRUE	1809927749	VISITOR_INFO1_LIVE	q5pXlvGVGc8
.youtube.com	TRUE	/	TRUE	1809927749	VISITOR_PRIVACY_METADATA	CgJNTRIEGgAgCw%3D%3D
.youtube.com	TRUE	/	TRUE	1828935749	PREF	f4=4000000&tz=Asia.Yangon
.youtube.com	TRUE	/	TRUE	1828935748	LOGIN_INFO	AFmmF2swRgIhAN4KHpBKnhZzMnOKdWgsDLp9tCAiyqeqWAER1Dpf60g4AiEAnriTTQBND5dOgWPPgmEFOd2m_T9ayiEe2GIU4BJPLbg:QUQ3MjNmeVVOaVBJQlFEZHJrNkRiQkRiYzFqbHBPMUZHdmdfSDFoZnMxZUZXN05sZktVSnpkNXhobXJyVlJDb01CMFFEaGkwR00yUzN2dlZWVkdGM3QxWTdyR2ZyT2gxZU9FS19wdFd3azN1X1pvUXlIMF95MEtoMnYyU1c4S0IwSnBValBvay1xMV9FS0ptekhmemNzTlhxc1BLSF9vaTVn"""

# 🚨 Cookie ဖိုင်ကို အလိုအလျောက် ဆောက်ပေးမည့် Function
def create_cookie_file():
    try:
        with open("cookies.txt", "w", encoding="utf-8") as f:
            f.write(COOKIE_CONTENT)
        print("✅ cookies.txt ဖိုင် ဆောက်ပြီးပါပြီ။")
    except Exception as e:
        print(f"⚠️ Cookie ဖိုင် ဆောက်မရပါ: {e}")

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
                    cmd = ["yt-dlp", "--cookies", "cookies.txt", "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", "--merge-output-format", "mp4", "--no-warnings", "-o", out_template, url]
                else:
                    cmd = ["yt-dlp", "--cookies", "cookies.txt", "-x", "--audio-format", "mp3", "--no-warnings", "-o", out_template, url]
            
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
                    text=f"❌ ဒေါင်းလုဒ် မအောင်မြင်ပါ။\n\nError: {err}"
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
    # 🚨 Bot မစတင်ခင် Cookie ဖိုင်ကို အရင်ဆောက်မယ်
    create_cookie_file()

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
