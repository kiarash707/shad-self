# 🤖 Shad Self KIA

> یک Self Account حرفه‌ای برای پیام‌رسان شاد، ساخته‌شده با Python و aioshad.

## ✨ امکانات

- 🔐 ورود با شماره تلفن و کد تأیید شاد
- 💾 ذخیره Session برای ورودهای بعدی
- 💬 پاسخ خودکار در پیام خصوصی
- 👥 پاسخ به «سلام» در گروه
- 📎 واکنش به مدیای دریافتی
- ⏰ نمایش ساعت کنار نام با TimeName
- 📊 آمار اجرا و وضعیت اتصال
- 🏓 اندازه‌گیری زمان پاسخ عملیات
- 👤 نمایش اطلاعات حساب
- 🎲 ابزارهای Dice، Coin و 8Ball
- 🎂 محاسبه سن تقریبی
- 💓 Heartbeat و مدیریت خطاهای اتصال
- 🔄 مناسب برای اجرای دائمی روی VPS و Ubuntu

## 🧰 پیش‌نیازها

- Python 3.11+
- کتابخانه aioshad
- اینترنت پایدار
- شماره تلفن ثبت‌شده در شاد

## 📥 نصب

```bash
git clone https://github.com/kiarash707/shad-self.git
cd shad-self
python3 -m pip install -U aioshad
python3 shad_self_KIA.py
```

در ویندوز:

```bash
python shad_self_KIA.py
```

## 🔐 ورود

در اولین اجرا شماره تلفن را با کد کشور وارد کنید.

صحیح:

```text
989123456789
```

اشتباه:

```text
09123456789
```

بعد از دریافت کد تأیید، آن را در Terminal وارد کنید.

## 💾 Session

Session در پوشه sessions/ ذخیره می‌شود.

در اجراهای بعدی، اگر Session معتبر باشد، معمولاً نیازی به ورود مجدد نیست.

**هشدار:** پوشه sessions/ حاوی اطلاعات حساس است و نباید در GitHub عمومی، ZIP عمومی یا اختیار دیگران قرار گیرد.

## 🧩 دستورات

| دستور | عملکرد |
|---|---|
| /start | فهرست دستورات |
| /help | راهنما |
| /ping | زمان پاسخ عملیات |
| /info | اطلاعات حساب |
| /time | ساعت و تاریخ |
| /stats | آمار اجرا |
| /echo متن | تکرار متن |
| /joke | جوک تصادفی |
| /quote | جمله تصادفی |
| /dice | تاس |
| /coin | شیر یا خط |
| /8ball سؤال | پاسخ تصادفی |
| /love | ابزار سرگرمی عشق |
| /age سال | محاسبه سن تقریبی |

### مثال

```text
/ping
/echo سلام
/joke
/8ball آیا موفق می‌شوم؟
/age 1370
```

> نکته: /ping زمان پاسخ عملیات برنامه در شاد را اندازه می‌گیرد و Ping خام اینترنت یا ICMP نیست.

## 💬 پاسخ خودکار

### خصوصی
پیام‌های متنی را پاسخ می‌دهد. پیام‌های شامل «سلام» پاسخ سلام تصادفی دریافت می‌کنند.

### گروه
به پیام‌های شامل «سلام» پاسخ می‌دهد.

### مدیا
در پیام خصوصی هنگام دریافت مدیا، پیام دریافت فایل ارسال می‌شود.

برنامه پیام‌های حساب خودش را تشخیص می‌دهد تا به خودش پاسخ ندهد.

## ⏰ TimeName

بعد از اتصال، ساعت کنار نام نمایش داده می‌شود.

```text
⏰ 13:25
```

منطقه زمانی: Asia/Tehran

## 🖥️ نصب روی Ubuntu / VPS

```bash
apt update
apt install -y git python3 python3-venv

git clone https://github.com/kiarash707/shad-self.git
cd shad-self

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python shad_self_KIA.py
```

اگر سیستم شما sudo می‌خواهد، دستورات apt را با sudo اجرا کنید.

> استفاده از sudo su برای این پروژه الزامی نیست.

## 🔄 اجرای دائمی با systemd

بعد از اینکه برنامه را یک بار دستی اجرا کردید و Session ساخته شد، می‌توانید آن را دائمی کنید.

```bash
nano /etc/systemd/system/shad-self.service
```

```ini
[Unit]
Description=Shad Self KIA
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/root/shad-self
ExecStart=/root/shad-self/.venv/bin/python /root/shad-self/shad_self_KIA.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

> مسیر /root/shad-self را با مسیر واقعی پروژه خودتان جایگزین کنید.

فعال‌سازی:

```bash
systemctl daemon-reload
systemctl enable shad-self
systemctl start shad-self
```

وضعیت:

```bash
systemctl status shad-self
```

لاگ زنده:

```bash
journalctl -u shad-self -f
```

Restart:

```bash
systemctl restart shad-self
```

توقف:

```bash
systemctl stop shad-self
```

## 🌐 هاست

### VPS
مناسب است، به شرط داشتن Python 3.11+، SSH، فضای ذخیره‌سازی دائمی و امکان اجرای Process طولانی‌مدت.

### Shared Hosting
ممکن است Process دائمی Python را متوقف کند؛ قبل از خرید، Long-running Python Process را بررسی کنید.

### Serverless
برای این پروژه مناسب نیست، چون برنامه به اتصال طولانی‌مدت نیاز دارد.

## 🛡️ امنیت

```gitignore
sessions/
.venv/
__pycache__/
*.py[cod]
.env
```

- Session را منتشر نکنید.
- شماره و کد ورود را در اختیار دیگران قرار ندهید.
- چند نمونه همزمان روی یک حساب اجرا نکنید.

## 🧯 رفع خطا

### Session خراب

```bash
rm -rf sessions
```

سپس دوباره اجرا و وارد حساب شوید.

### بررسی Python

```bash
python3 --version
```

### نصب مجدد aioshad

```bash
python3 -m pip install -U aioshad
```

### بررسی شبکه

```bash
ping 1.1.1.1
curl -I https://pypi.org
```

### بررسی systemd

```bash
systemctl status shad-self
journalctl -u shad-self -n 100 --no-pager
```

## 📁 ساختار پروژه

```text
shad-self/
├── shad_self_KIA.py
├── README.md
├── requirements.txt
├── .gitignore
├── .venv/       # محلی
└── sessions/    # محرمانه
```

## 📦 requirements.txt

```text
aioshad==1.0.14
```

## 🔄 به‌روزرسانی

```bash
cd shad-self
git pull
source .venv/bin/activate
python -m pip install -r requirements.txt
```

اگر با systemd اجرا می‌شود:

```bash
systemctl restart shad-self
```

## ⚠️ نکته مهم

این پروژه به حساب واقعی شاد متصل می‌شود. استفاده از آن باید مطابق قوانین و محدودیت‌های سرویس شاد باشد.

---

**Shad Self KIA — Simple, Fast & Self.**

## 🛡️ Operations Dashboard

The project includes a production-oriented FastAPI dashboard at `/`.

Railway runtime configuration:

- `AIOSHAD_PHONE` — Shad account phone number. Required for the bot to authenticate.
- `DASHBOARD_TOKEN` — required secret for dashboard operations.
- `SHAD_DATA_DIR` — persistent data directory; defaults to `./data`.
- Railway volume should be mounted at `/app/data`.

Endpoints:

- `/health` — public liveness check
- `/ready` — runtime readiness
- `/api/status` — authenticated runtime status
- `/api/backup` — authenticated backup creation
- `/api/backups` — authenticated backup inventory
- `/api/restore` — authenticated validated restore
- `/api/restart` — authenticated bot restart

Backups contain runtime/session state only. Environment secrets are never included. Restore validates ZIP integrity, manifest, file count, uncompressed size, path traversal, symlinks, and SHA-256 checksums before replacing session state.

For Railway, the service start command is:

```bash
uvicorn dashboard:app --host 0.0.0.0 --port $PORT
```

The dashboard is intentionally locked until `DASHBOARD_TOKEN` is configured.
