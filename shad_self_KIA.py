import asyncio
import logging
import os
import random
import re
import sys
import time
from datetime import datetime

from aioshad import (
    Client,
    ClientConfig,
    TimeName,
    AioShadError,
    AuthenticationError,
    InvalidSessionError,
)
from aioshad import filters

APP_VERSION = "2.0.0"
DATA_DIR = os.getenv("SHAD_DATA_DIR", "./data")
SESSION_DIR = os.path.join(DATA_DIR, "sessions")
os.makedirs(SESSION_DIR, exist_ok=True)

PREFIX = "/"
TIME_FORMAT = "⏰ {time}"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("selfbot")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

STATE = {
    "my_guid": None,
    "start": time.time(),
    "msgs": 0,
    "commands": 0,
}

GREETINGS = [
    "سلام رفیق! 👋 چه خبر؟",
    "سلام! 🌟 امروز روز خوبیه نه؟",
    "سلام سلام! 😎 خوش اومدی",
    "درود! 🚀 آماده‌ای؟",
    "هی! 👋 چطوری؟",
    "سلام! 💫 چه روزی داری؟",
    "سلام گلم! 🌸 خوبی؟",
    "سلام! 🔥 همیشه پرانرژی",
    "سلام عزیز! ✨ چه خبر تازه؟",
    "سلام! 🌈 امروز چی خبر؟",
]

JOKES = [
    "به یه برنامه‌نویس گفتن برو نون بگیر، گفت: نون.api داری؟",
    "چرا برنامه‌نویس‌ها شب کار می‌کنن؟ چون باگ‌ها شب بیدارن!",
    "دیتابیس به برنامه‌نویس گفت: تو منو نمی‌فهمی، گفت: JOIN بزنیم!",
    "دو تا بایت راه می‌رفتن، یکیشون گفت: من بیت دارم، اون گفت: من هم!",
    "چرا Java کندی؟ چون همیشه یه چیز اضافه داره!",
    "سه تا ریاضی‌دان تو رستوران‌ن، پیش‌غذا رو بین خودشون تقسیم می‌کنن!",
    "برنامه‌نویس به همسرش گفت: امشب میام خونه، گفت: promise دادی یا callback؟",
]

QUOTES = [
    "«تنها راه انجام کار بزرگ، عاشق کارت بودن است.» — استیو جابز",
    "«سخته، ولی ممکنه.» — ناشناس",
    "«اگه رؤیاش رو داری، پس تعقیبش کن.» — انیشتین",
    "«موفقیت نتیجه‌ی تلاش‌های کوچیک روزانه‌ست.» — ناشناس",
    "«بهترین زمان برای شروع، همین حالاست.» — ناشناس",
    "«شکست پلی‌ست به سمت موفقیت، نه دیوار.» — ناشناس",
    "«هر روز یه قدم، سالی ۳۶۵ قدم.» — ناشناس",
]

EIGHT_BALL = [
    "🎱 قطعاً بله",
    "🎱 قطعاً خیر",
    "🎱 شاید... شاید نه",
    "🎱 از من بپرس بعداً",
    "🎱 ستاره‌ها می‌گن بله",
    "🎱 فعلاً نه",
    "🎱 بهش اعتماد نکن",
    "🎱 بدون شک!",
    "🎱 خودت می‌دونی جوابش رو",
    "🎱 نمی‌تونم بگم",
    "🎱 سرنوشت می‌گه آره",
    "🎱 بی‌خیالش شو",
]

LOVE_LINES = [
    "❤️ عشقت ۹۵٪ واقعیه!",
    "❤️ عشقت ۷۰٪ قانع‌کننده‌ست",
    "❤️ عشقت ۱۰۰٪ خالصانه‌ست!",
    "❤️ عشقت ۴۰٪ ولی قشنگه",
    "❤️ عشقت ۸۵٪ واقعیه، ادامه بده!",
    "❤️ عشقت ۶۰٪، قابل قبوله",
    "❤️ عشقت ۹۹٪، فقط یه ذره مونده",
]

SMART_REPLIES = [
    "پیامت دریافت شد، در حال پردازش... 🧠",
    "چیزی که گفتی خیلی عمیقه! 🤔",
    "جدی؟ بگو بیشتر 🌟",
    "آره؟ باور نکردم 😏",
    "اینو باید یه جا یادداشت کنم ✍️",
    "حرفت منطقیه 💭",
    "جالب بود، ادامه بده 🎯",
    "واقعاً؟ 😲",
    "داری جدی میگی؟ 🤨",
    "باحال بود! 🔥",
]

BOOT_MESSAGES = [
    "🔋 بوت در حال راه‌اندازی...",
    "🚀 آماده‌سازی موشک...",
    "🧬 همگام‌سازی با شاد...",
    "📡 اتصال به مرکز فرمان...",
    "🛡️ بررسی امنیت نشست...",
    "⚡ فعال‌سازی قابلیت‌ها...",
]

KNOWN_COMMANDS = {
    f"{PREFIX}start", f"{PREFIX}help", f"{PREFIX}ping",
    f"{PREFIX}info", f"{PREFIX}time", f"{PREFIX}stats",
    f"{PREFIX}echo", f"{PREFIX}joke", f"{PREFIX}quote",
    f"{PREFIX}dice", f"{PREFIX}coin", f"{PREFIX}8ball",
    f"{PREFIX}love", f"{PREFIX}age",
}
KNOWN_COMMANDS_LOWER = {k.lower() for k in KNOWN_COMMANDS}

PHONE = os.getenv("AIOSHAD_PHONE", "").strip()
if not PHONE and sys.stdin.isatty():
    PHONE = input("📱 شماره تلفن (با کد کشور): ").strip()

app = Client(
    phone_number=PHONE,
    session_directory=SESSION_DIR,
    config=ClientConfig(
        timeout=30.0,
        poll_interval=1.5,
        max_requests_per_second=5.0,
        retry_attempts=3,
    ),
)


async def is_self(message):
    if not STATE.get("my_guid"):
        return False
    try:
        author = await message.get_author()
        if author is not None:
            return getattr(author, "guid", None) == STATE["my_guid"]
    except Exception as e:
        log.debug(f"is_self get_author ناموفق: {e}")
    try:
        ag = getattr(message, "author_guid", None)
        if ag is not None:
            return ag == STATE["my_guid"]
    except Exception:
        pass
    return False


@app.on_message(filters.command("start", prefixes=[PREFIX]))
async def cmd_start(message):
    STATE["commands"] += 1
    await message.reply(
        "╭─────────────╮\n"
        "  🤖 **سلف حرفه‌ای**\n"
        "╰─────────────╯\n\n"
        "✨ **دستورات موجود:**\n\n"
        f"`{PREFIX}ping` — سرعت پاسخ\n"
        f"`{PREFIX}info` — اطلاعات اکانت\n"
        f"`{PREFIX}time` — ساعت و تاریخ\n"
        f"`{PREFIX}stats` — آمار سلف\n"
        f"`{PREFIX}echo متن` — تکرار متن\n"
        f"`{PREFIX}joke` — جوک تصادفی\n"
        f"`{PREFIX}quote` — جمله الهام‌بخش\n"
        f"`{PREFIX}dice` — تاس ریختن\n"
        f"`{PREFIX}coin` — شیر یا خط\n"
        f"`{PREFIX}8ball سوال` — جواب غیبی\n"
        f"`{PREFIX}love` — شانس عشق\n"
        f"`{PREFIX}age سال` — سن دقیق\n"
        f"`{PREFIX}help` — راهنما"
    )


@app.on_message(filters.command("help", prefixes=[PREFIX]))
async def cmd_help(message):
    STATE["commands"] += 1
    await message.reply(
        "📖 **راهنمای سلف**\n\n"
        "🎯 **دستورات:**\n"
        f"`{PREFIX}start` `{PREFIX}ping` `{PREFIX}info`\n"
        f"`{PREFIX}time` `{PREFIX}stats` `{PREFIX}echo`\n"
        f"`{PREFIX}joke` `{PREFIX}quote` `{PREFIX}dice`\n"
        f"`{PREFIX}coin` `{PREFIX}8ball` `{PREFIX}love`\n"
        f"`{PREFIX}age` `{PREFIX}help`\n\n"
        "💬 **پاسخ خودکار:**\n"
        "به سلام خودکار جواب می‌دم\n"
        "به پیام خصوصی پاسخ می‌دم\n"
        "به مدیا واکنش نشون می‌دم"
    )


@app.on_message(filters.command("ping", prefixes=[PREFIX]))
async def cmd_ping(message):
    STATE["commands"] += 1
    t0 = time.perf_counter()
    msg = await message.reply("🏓 در حال اندازه‌گیری...")
    ms = (time.perf_counter() - t0) * 1000
    try:
        await msg.edit(
            f"🏓 **Pong!**\n"
            f"⚡ پاسخ: `{ms:.0f}ms`\n"
            f"💚 وضعیت: `فعال`"
        )
    except Exception as e:
        log.warning(f"ping edit ناموفق: {e}")


@app.on_message(filters.command("info", prefixes=[PREFIX]))
async def cmd_info(message):
    STATE["commands"] += 1
    try:
        me = await app.get_me()
        await message.reply(
            "╭──── اطلاعات ────╮\n"
            f"👤 **نام:** {me.name}\n"
            f"🆔 **GUID:** `{me.guid[:20]}...`\n"
            f"📛 **یوزر:** @{me.username or 'ندارد'}\n"
            f"📝 **بیو:** {me.bio or 'خالی'}\n"
            f"✅ **تایید:** {'بله' if getattr(me, 'is_verified', False) else 'خیر'}\n"
            "╰────────────────╯"
        )
    except Exception as e:
        log.warning(f"info ناموفق: {e}")
        await message.reply("❌ خطا در دریافت اطلاعات")


@app.on_message(filters.command("time", prefixes=[PREFIX]))
async def cmd_time(message):
    STATE["commands"] += 1
    now = datetime.now()
    await message.reply(
        f"🕐 **ساعت:** `{now:%H:%M:%S}`\n"
        f"📅 **تاریخ:** `{now:%Y/%m/%d}`\n"
        f"📆 **روز:** `{now:%A}`"
    )


@app.on_message(filters.command("stats", prefixes=[PREFIX]))
async def cmd_stats(message):
    STATE["commands"] += 1
    up = time.time() - STATE["start"]
    h = int(up // 3600)
    m = int((up % 3600) // 60)
    s = int(up % 60)
    await message.reply(
        "📊 **آمار سلف**\n\n"
        f"⏱️ **Uptime:** `{h}h {m}m {s}s`\n"
        f"📨 **پیام‌ها:** `{STATE['msgs']}`\n"
        f"⚙️ **دستورات:** `{STATE['commands']}`\n"
        f"🔗 **اتصال:** `{'فعال' if app.is_connected else 'قطع'}`"
    )


@app.on_message(filters.command("echo", prefixes=[PREFIX]))
async def cmd_echo(message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(f"❌ مثال: `{PREFIX}echo سلام`")
        return
    STATE["commands"] += 1
    await message.reply(f"🔊 {parts[1]}")


@app.on_message(filters.command("joke", prefixes=[PREFIX]))
async def cmd_joke(message):
    STATE["commands"] += 1
    await message.reply(f"😄 {random.choice(JOKES)}")


@app.on_message(filters.command("quote", prefixes=[PREFIX]))
async def cmd_quote(message):
    STATE["commands"] += 1
    await message.reply(f"✨ {random.choice(QUOTES)}")


@app.on_message(filters.command("dice", prefixes=[PREFIX]))
async def cmd_dice(message):
    STATE["commands"] += 1
    n = random.randint(1, 6)
    faces = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
    await message.reply(f"🎲 تاس: {faces[n]} `{n}`")


@app.on_message(filters.command("coin", prefixes=[PREFIX]))
async def cmd_coin(message):
    STATE["commands"] += 1
    result = random.choice(["🪙 **شیر**", "🪙 **خط**"])
    await message.reply(f"{result}")


@app.on_message(filters.regex(rf"^{re.escape(PREFIX)}8ball\s+(.+)$"))
async def cmd_8ball(message):
    STATE["commands"] += 1
    await message.reply(f"🔮 {random.choice(EIGHT_BALL)}")


@app.on_message(filters.command("love", prefixes=[PREFIX]))
async def cmd_love(message):
    STATE["commands"] += 1
    await message.reply(random.choice(LOVE_LINES))


@app.on_message(filters.command("age", prefixes=[PREFIX]))
async def cmd_age(message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.reply(f"❌ مثال: `{PREFIX}age 1370`")
        return
    try:
        year = int(parts[1])
        if year < 1300:
            year += 1300
        now = datetime.now()
        jalali_year = now.year - 621
        if now.month < 3 or (now.month == 3 and now.day < 21):
            jalali_year -= 1
        age = jalali_year - year
        if age < 0:
            await message.reply("❌ سال وارد شده در آینده است")
            return
        days = age * 365
        hours = days * 24
        minutes = hours * 60
        STATE["commands"] += 1
        await message.reply(
            f"🎂 **سن شما:**\n"
            f"📅 `{age}` سال\n"
            f"📆 `{days:,}` روز\n"
            f"⏰ `{hours:,}` ساعت\n"
            f"⏱️ `{minutes:,}` دقیقه"
        )
    except ValueError:
        await message.reply("❌ عدد معتبر وارد کن")


@app.on_message(filters.private & filters.text & ~filters.startswith(PREFIX))
async def on_private(message):
    if await is_self(message):
        return
    STATE["msgs"] += 1
    text = (message.text or "").strip()
    try:
        if "سلام" in text or "salam" in text.lower():
            await message.reply(random.choice(GREETINGS))
        else:
            await message.reply(random.choice(SMART_REPLIES))
    except Exception as e:
        log.warning(f"پاسخ خصوصی ناموفق: {e}")


@app.on_message(filters.group & filters.contains("سلام"))
async def on_group_greeting(message):
    if await is_self(message):
        return
    STATE["msgs"] += 1
    try:
        await message.reply(random.choice(GREETINGS))
    except Exception as e:
        log.warning(f"پاسخ گروهی ناموفق: {e}")


@app.on_message(filters.private & filters.media)
async def on_media(message):
    if await is_self(message):
        return
    STATE["msgs"] += 1
    try:
        await message.reply("📎 فایل دریافت شد! 🎯")
    except Exception as e:
        log.warning(f"پاسخ مدیا ناموفق: {e}")


@app.on_message(filters.edited)
async def on_edited(message):
    if await is_self(message):
        return
    log.info(f"✏️ پیام ویرایش شد: {message.id}")


@app.on_message(
    filters.private
    & filters.startswith(PREFIX)
    & filters.text
)
async def on_unknown_command(message):
    if await is_self(message):
        return
    try:
        text = (message.text or "").strip()
        cmd = text.split()[0] if text else ""
        if cmd.lower() in KNOWN_COMMANDS_LOWER:
            return
        await message.reply(
            f"❓ دستور ناشناخته: `{cmd}`\n"
            f"برای راهنما `{PREFIX}help` را بزن"
        )
    except Exception as e:
        log.warning(f"unknown command handler: {e}")


async def heartbeat():
    log.info(
        f"💓 متصل={app.is_connected} │ "
        f"پیام‌ها={STATE['msgs']} │ "
        f"دستورات={STATE['commands']}"
    )


async def boot_banner():
    for line in BOOT_MESSAGES:
        log.info(line)
        await asyncio.sleep(0.4)
    log.info("✅ بوت با موفقیت راه افتاد")


async def main():
    log.info(f"🚀 شروع سلف v{APP_VERSION}...")
    if not PHONE:
        log.error("❌ AIOSHAD_PHONE تنظیم نشده است")
        return

    try:
        await app.connect()
        log.info("✅ اتصال برقرار شد")
    except AuthenticationError:
        log.error("❌ خطای احراز هویت")
        return
    except InvalidSessionError:
        log.error("❌ Session نامعتبر — پوشه sessions را پاک کن")
        return
    except AioShadError as e:
        log.error(f"❌ خطای aioshad: {e}")
        return
    except Exception as e:
        log.exception(f"💥 خطای غیرمنتظره: {e}")
        return

    try:
        me = await app.get_me()
        STATE["my_guid"] = me.guid
        log.info(f"👤 {me.name} ({me.guid})")
    except Exception as e:
        log.warning(f"⚠️ get_me ناموفق: {e}")

    try:
        await app.presence.start_time_name(
            TimeName(
                format=TIME_FORMAT,
                timezone="Asia/Tehran",
                interval=60,
                preserve_first_name=True,
            )
        )
        log.info("⏰ TimeName فعال — ساعت کنار اسم")
    except Exception as e:
        log.warning(f"⚠️ TimeName ناموفق: {e}")

    await boot_banner()

    try:
        app.scheduler.every(60, heartbeat)
        log.info("⏰ Heartbeat فعال")
    except Exception as e:
        log.warning(f"⚠️ Scheduler ناموفق: {e}")

    log.info("🔄 سلف در حال اجراست... (Ctrl+C برای توقف)")
    try:
        await app.run_until_disconnected()
    except KeyboardInterrupt:
        log.info("🛑 توقف دستی")
    except asyncio.CancelledError:
        log.info("🛑 تسک لغو شد")
    finally:
        try:
            await app.scheduler.cancel_all()
        except Exception as e:
            log.warning(f"⚠️ cancel_all ناموفق: {e}")
        try:
            await app.presence.stop_time_name()
            log.info("⏰ TimeName متوقف شد")
        except Exception as e:
            log.warning(f"⚠️ stop_time_name ناموفق: {e}")
        try:
            await app.stop()
        except Exception as e:
            log.warning(f"⚠️ stop ناموفق: {e}")


if __name__ == "__main__":
    print("╭────────────────────────────────╮")
    print("│  🤖 راه‌اندازی سلف حرفه‌ای aioshad  │")
    print("╰────────────────────────────────╯")
    print()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("👋 خداحافظ")
