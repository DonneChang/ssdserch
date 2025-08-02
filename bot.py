import asyncio
import json, os
from pathlib import Path
from libs.log import logger
from libs.toml import read
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from libs.crawler import fetch_torrents
from apscheduler.schedulers.asyncio import AsyncIOScheduler

config = read("config/config.toml")
chat_id = config["BOT"].get("chat_id")
BOT_TOKEN = config["BOT"]["BOT_TOKEN"]


SENT_IDS_FILE = Path("logs/sent_titles.json")
SENT_IDS_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_sent_ids():
    if os.path.exists(SENT_IDS_FILE):
        try:
            with open(SENT_IDS_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception as e:
            print(f"加载 sent_ids.json 失败：{e}")
    return set()

def save_sent_ids(ids):
    try:
        with open(SENT_IDS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(ids), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存 sent_ids.json 失败：{e}")

sent_ids = load_sent_ids()


# 指令处理器：/start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("欢迎使用种子推送Bot，发送 /search 查看最新推荐种子。")

# 指令处理器：/search
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("正在查找，请稍候...")
    results = await fetch_torrents()
    new_results = [r for r in results if r[0] not in sent_ids]  # r[0] 是 torrent_id

    if new_results:
        for torrent_id, title, link in new_results[:50]:
            await update.message.reply_text(f"{title}\n👉 {link}")
            sent_ids.add(torrent_id)
        save_sent_ids(sent_ids)
    else:
        await update.message.reply_text("暂无新种子。")

# 定时任务函数
async def auto_check(application: Application):
    results = await fetch_torrents()
    new_results = [r for r in results if r[0] not in sent_ids]

    for torrent_id, title, link in new_results:
        try:
            await application.bot.send_message(chat_id=chat_id, text=f"{title}\n👉 {link}")
            sent_ids.add(torrent_id)
        except Exception as e:
            print(f"发送失败：{e}")
    if new_results:
        save_sent_ids(sent_ids)


async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.run(auto_check(app)), trigger="interval", minutes=2)
    scheduler.start()

    print("Bot 已启动，正在监听...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    # 保持程序运行，等待关闭信号
    try:
        await asyncio.Event().wait()
    finally:
        # 优雅关闭
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())