# 📧 IMAP Mail Bulk Archiver

> **Bulk-download every email from any IMAP mailbox as `.eml` files + CSV index.**
> Read-only · Resume-capable · Zero dependencies · 15+ providers supported.

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.10+-blue.svg">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green.svg">
  <img alt="No Dependencies" src="https://img.shields.io/badge/dependencies-none-brightgreen.svg">
  <img alt="Platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg">
</p>

---

## 🎯 Why This Tool

Manually saving 1000 emails as `.eml` files? That's a full week of clicking.

This script does it in **20 minutes** — with **resume capability**, **CSV index**, and **read-only IMAP** (never marks your emails as read).

### Perfect for

- 🧑‍💼 **Employees backing up work emails** before leaving a company
- 🏢 **Compliance / Legal archiving** (3-5 years of correspondence)
- 🔄 **Mailbox migration** (Gmail → Outlook · 163 → Gmail)
- 📊 **Data analysis** — convert emails to Excel for search / stats
- ⚖️ **Legal evidence** — timestamped `.eml` files admissible in most jurisdictions
- 🚚 **Cross-border e-commerce** — archiving FedEx / UPS case emails

---

## ⚡ Quick Start

```bash
# 1. Clone
git clone https://github.com/<your-username>/imap-mail-bulk-archiver.git
cd imap-mail-bulk-archiver

# 2. Configure (create .env from README example below)

# 3. Run
python src/main.py                    # Download INBOX
python src/main.py --all              # Download all folders
python src/main.py --list             # Just list folders
python src/main.py --resume           # Resume after network break
```

### `.env` Example

```env
MAIL_PROVIDER=qq
MAIL_USER=you@qq.com
MAIL_PASSWORD=your_authorization_code
```

---

## 🌐 Supported Providers (15+)

| Provider | Note |
|---|---|
| Gmail | Requires App Password (2FA) |
| Outlook / Hotmail / Office 365 | Standard password or App Password |
| Yahoo Mail | Requires App Password |
| iCloud | Requires App Password from appleid.apple.com |
| QQ Mail (China) | Requires Authorization Code (not login password) |
| 163 / 126 / yeah (NetEase) | Requires Authorization Code |
| Aliyun Mail | Standard password |
| Foxmail | Uses QQ Mail infrastructure |
| Tencent Business Mail | For companies |
| Yandex Mail | Standard password |
| Zoho Mail | Standard password |
| Sina / Sohu | Standard password |
| Hostinger Mail | Standard password |
| **Custom IMAP** | Add to `providers.json`, no code change |

---

## ✨ Features

- ✅ **Read-only IMAP** — never marks emails as read or modifies server state
- ✅ **Resume-capable** — re-run skips already-downloaded UIDs (extracted from filenames)
- ✅ **Batch FETCH** — 100 messages per batch, configurable via `--batch`
- ✅ **Standard `.eml` format** — opens in Outlook / Thunderbird / Apple Mail / Foxmail
- ✅ **CSV index** — `_index.csv` with `uid,date,from,subject,size,filename` for Excel analysis
- ✅ **Non-overwriting output** — auto-increment `26.9.22 → 26.9.22_2 → 26.9.22_3`
- ✅ **Zero dependencies** — pure Python stdlib (no `pip install` needed)

---

## 📖 Usage

### Command-line Options

```
--provider   Preset name (gmail/qq/163/outlook/...) — see providers.json
--host       Custom IMAP server (overrides --provider)
--port       Port (default 993)
--user       Email address
--password   Password / App password / Authorization code
--folder     Folder to download (default: INBOX)
--all        Download all folders
--list       Just list folders, don't download
--out        Custom output directory
--resume     Continue in today's latest output directory
--batch      FETCH batch size (default: 100)
```

### Real-World Examples

```bash
# List all mailbox folders
python src/main.py --provider gmail --user me@gmail.com --password $APP_PW --list

# Download only Sent folder from Outlook
python src/main.py --provider outlook --folder "Sent Items" \
    --user me@outlook.com --password $PW

# Resume interrupted download (network died mid-way)
python src/main.py --resume

# Download 500,000 emails from a corporate mailbox (slow-batch mode)
python src/main.py --all --batch 50
```

### Output Structure

```
输出/
└── 26.9.22/                             # today's date (YY.M.D)
    └── INBOX/
        ├── 12345__Order Confirmation.eml
        ├── 12346__Shipment Notice.eml
        ├── ...
        └── _index.csv                   # uid, date, from, subject, size, filename
```

---

## 🔐 Password / Authorization Notes

Every provider handles auth differently. **This is where 90% of users get stuck** — here's the cheat sheet:

| Provider | Password Type | How to Get |
|---|---|---|
| **Gmail** | App Password (2FA required) | Google Account → Security → App Passwords |
| **Outlook** | Standard or App Password | Microsoft Account → Security |
| **iCloud** | App-Specific Password | appleid.apple.com → Sign-in → App-Specific Passwords |
| **QQ Mail** | Authorization Code (NOT login pw) | mail.qq.com Settings → IMAP/SMTP → Get Code |
| **163 / 126** | Authorization Code | mail.163.com Settings → POP3/SMTP/IMAP |
| **Yahoo** | App Password | account.yahoo.com Security |

---

## 🛠️ Custom Providers

Add to `src/providers.json`:

```json
"my_company": {
    "host": "imap.mycompany.com",
    "port": 993,
    "ssl": true,
    "note": "My company self-hosted mail"
}
```

Then use: `python src/main.py --provider my_company`

---

## ⚠️ Legal & Ethical Use

- 🟢 **Only for mailboxes you own** or have explicit authorization to access
- 🔴 **NOT for scraping others' mailboxes** — that's illegal in most jurisdictions
- 🟡 IMAP `readonly=True` means server logs won't show read-status changes, but **login events are still logged**

---

## 🚀 Pro Version (Coming Soon)

The Pro version adds features many teams need:

| Feature | Open Source | Pro |
|---|---|---|
| Bulk `.eml` download | ✅ | ✅ |
| Resume + Batch | ✅ | ✅ |
| CSV index | ✅ | ✅ |
| 15+ providers | ✅ | ✅ |
| **GUI (double-click launcher)** | ❌ | ✅ |
| **Attachment extraction** — auto-save all attachments as files | ❌ | ✅ |
| **`.eml` → Excel parser** — turn emails into structured `.xlsx` for analysis | ❌ | ✅ |
| **Scheduled auto-backup** — cron / Windows Task Scheduler ready | ❌ | ✅ |
| **AES encryption + zip archive** — HIPAA/GDPR-friendly | ❌ | ✅ |
| **Priority email support (30 days)** | ❌ | ✅ |

**Pricing**:
- 💰 **Personal** — $49 (one-time, single user)
- 💰 **Business** — $99 (5 seats)
- 💰 **Extended** — $199 (GUI + Attachment + Scheduled)

📩 **Get Pro**:[Gumroad Link](#) (updating)
📩 **Custom / Enterprise**:[Contact via GitHub Issues](../../issues)

---

## 🤝 Contributing

Contributions welcome! Especially:

- 📮 Adding more IMAP provider presets to `providers.json`
- 🌍 Translations of this README (currently EN + ZH)
- 🐛 Bug reports with reproducible steps
- 📝 Documentation improvements

Please open an issue before large PRs to discuss the approach.

---

## 📜 License

MIT License — see [LICENSE](./LICENSE) file.

You are free to use, modify, and distribute this software.
**Attribution appreciated but not required.**

---

## 💬 About the Author

Built by a **3PL data engineer** who processes 100,000+ FedEx / UPS emails per year.

If this tool saves you a week of clicking, consider:

- ⭐ **Starring this repo**(helps others find it)
- 🐦 **Sharing on Twitter / LinkedIn**
- 💰 **Buying the Pro version**(supports open source)
- 🐛 **Contributing a provider preset**

---

## 🔗 Related Projects (by same author)

- 🚚 **FedEx Bill Toolkit** — 4-in-1 bundle for cross-border sellers(coming to GitHub)
- 📊 **Cross-border 3PL Automation** — Excel / CSV / API tools for warehouses
- 🎯 **awesome-cross-border-3pl-tools** — curated list of tools we use daily

Follow [@your-username](../../) for updates.

---

<p align="center">
  <sub>Built with ❤️ for the cross-border e-commerce community.</sub>
</p>
