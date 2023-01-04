import time
import os
import re
import codecs
from typing import List
from random import randint
from EmikoRobot.modules.helper_funcs.chat_status import user_admin
from EmikoRobot.modules.disable import DisableAbleCommandHandler
from EmikoRobot import (
    dispatcher,
    WALL_API,
)
import requests as r
import wikipedia
from requests import get, post
from telegram import (
    Chat,
    ChatAction,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
    Message,
    MessageEntity,
    TelegramError,
)
from telegram.error import BadRequest
from telegram.ext.dispatcher import run_async
from telegram.ext import CallbackContext, Filters, CommandHandler
from EmikoRobot import StartTime
from EmikoRobot.modules.helper_funcs.chat_status import sudo_plus
from EmikoRobot.modules.helper_funcs.alternate import send_action, typing_action

MARKDOWN_HELP = f"""
Penurunan harga adalah alat pemformatan yang sangat kuat yang didukung oleh telegram. {dispatcher.bot.first_name} memiliki beberapa penyempurnaan, untuk memastikan bahwa \
pesan yang disimpan diurai dengan benar, dan untuk memungkinkan Anda membuat tombol.

❂ <code>_italic_</code>: membungkus teks dengan '_' akan menghasilkan teks miring
❂ <code>*bold*</code>: membungkus teks dengan '*' akan menghasilkan teks tebal
❂ <code>`code`</code>: membungkus teks dengan ''`' akan menghasilkan teks monospace, juga dikenal sebagai 'kode'
❂ <code>[sometext](someURL)</code>: ini akan membuat tautan - pesan hanya akan menampilkan <code>sometext</code>, \
dan mengetuknya akan membuka halaman di <code>someURL</code>.
<b>Contoh:</b><code>[test](example.com)</code>

❂ <code>[buttontext](buttonurl:someURL)</code>: ini adalah peningkatan khusus untuk memungkinkan pengguna memiliki telegram \
tombol di penurunan harga mereka. <code>buttontext</code> akan menjadi apa yang ditampilkan pada tombol, dan <code>someurl</code> \
akan menjadi url yang dibuka.
<b>Contoh:</b> <code>[Ini adalah tombol](buttonurl:example.com)</code>

Jika Anda ingin beberapa tombol pada baris yang sama, gunakan :sama, seperti:
<code>[satu](buttonurl://example.com)
[dua](buttonurl://google.com:sama)</code>
Ini akan membuat dua tombol pada satu baris, bukan satu tombol per baris.

Ingatlah bahwa pesan Anda <b>HARUS</b> berisi beberapa teks selain hanya sebuah tombol!
"""


@user_admin
def echo(update: Update, context: CallbackContext):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message

    if message.reply_to_message:
        message.reply_to_message.reply_text(
            args[1], parse_mode="MARKDOWN", disable_web_page_preview=True
        )
    else:
        message.reply_text(
            args[1], quote=False, parse_mode="MARKDOWN", disable_web_page_preview=True
        )
    message.delete()


def markdown_help_sender(update: Update):
    update.effective_message.reply_text(MARKDOWN_HELP, parse_mode=ParseMode.HTML)
    update.effective_message.reply_text(
        "Try forwarding the following message to me, and you'll see, and Use #test!"
    )
    update.effective_message.reply_text(
        "/save test This is a markdown test. _italics_, *bold*, code, "
        "[URL](example.com) [button](buttonurl:github.com) "
        "[button2](buttonurl://google.com:same)"
    )


def markdown_help(update: Update, context: CallbackContext):
    if update.effective_chat.type != "private":
        update.effective_message.reply_text(
            "Contact me in pm",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Markdown help",
                            url=f"t.me/{context.bot.username}?start=markdownhelp",
                        )
                    ]
                ]
            ),
        )
        return
    markdown_help_sender(update)


def wiki(update: Update, context: CallbackContext):
    kueri = re.split(pattern="wiki", string=update.effective_message.text)
    wikipedia.set_lang("en")
    if len(str(kueri[1])) == 0:
        update.effective_message.reply_text("Enter keywords!")
    else:
        try:
            pertama = update.effective_message.reply_text("🔄 Loading...")
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="🔧 More Info...",
                            url=wikipedia.page(kueri).url,
                        )
                    ]
                ]
            )
            context.bot.editMessageText(
                chat_id=update.effective_chat.id,
                message_id=pertama.message_id,
                text=wikipedia.summary(kueri, sentences=10),
                reply_markup=keyboard,
            )
        except wikipedia.PageError as e:
            update.effective_message.reply_text(f"⚠ Error: {e}")
        except BadRequest as et:
            update.effective_message.reply_text(f"⚠ Error: {et}")
        except wikipedia.exceptions.DisambiguationError as eet:
            update.effective_message.reply_text(
                f"⚠ Error\n There are too many query! Express it more!\nPossible query result:\n{eet}"
            )


@send_action(ChatAction.UPLOAD_PHOTO)
def wall(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    msg = update.effective_message
    msg_id = update.effective_message.message_id
    args = context.args
    query = " ".join(args)
    if not query:
        msg.reply_text("Please enter a query!")
        return
    caption = query
    term = query.replace(" ", "%20")
    json_rep = r.get(
        f"https://wall.alphacoders.com/api2.0/get.php?auth={WALL_API}&method=search&term={term}"
    ).json()
    if not json_rep.get("success"):
        msg.reply_text("An error occurred!")

    else:
        wallpapers = json_rep.get("wallpapers")
        if not wallpapers:
            msg.reply_text("No results found! Refine your search.")
            return
        index = randint(0, len(wallpapers) - 1)  # Choose random index
        wallpaper = wallpapers[index]
        wallpaper = wallpaper.get("url_image")
        wallpaper = wallpaper.replace("\\", "")
        context.bot.send_photo(
            chat_id,
            photo=wallpaper,
            caption="Preview",
            reply_to_message_id=msg_id,
            timeout=60,
        )
        context.bot.send_document(
            chat_id,
            document=wallpaper,
            filename="wallpaper",
            caption=caption,
            reply_to_message_id=msg_id,
            timeout=60,
        )


__help__ = """
*Perintah yang tersedia:*

❂ /markdownhelp*:* ringkasan singkat tentang cara kerja penurunan harga di telegram - hanya dapat dipanggil dalam obrolan pribadi
❂ /paste*:* Menyimpan konten yang dibalas ke `nekobin.com` dan membalas dengan url
❂ /bereaksi*:* Bereaksi dengan reaksi acak
❂ /ud <word>*:* Ketikkan kata atau ekspresi yang ingin dicari gunakan
❂ /react*:* Melakukan pencarian gambar terbalik dari media yang dibalas.
❂ /wiki <query>*:* wikipedia permintaan Anda
❂ /wall <query>*:* dapatkan wallpaper dari wall.alphacoders.com
❂ /cash*:* pengonversi mata uang
  Contoh:
  `/tunai 1 USD INR`
       _ATAU_
  `/uang tunai 1 usd masuk`
  Keluaran: `1,0 USD = 75,505 INR`

*Modul Musik:*
❂ /video atau /vsong (permintaan): unduh video dari youtube
❂ /music atau /song (query): unduh lagu dari server yt. (BERBASIS API)
❂ /lyrics (nama lagu): Plugin ini mencari lirik lagu dengan nama lagu.
"""

ECHO_HANDLER = DisableAbleCommandHandler(
    "echo", echo, filters=Filters.chat_type.groups, run_async=True
)
MD_HELP_HANDLER = CommandHandler("markdownhelp", markdown_help, run_async=True)
WIKI_HANDLER = DisableAbleCommandHandler("wiki", wiki, run_async=True)
WALLPAPER_HANDLER = DisableAbleCommandHandler("wall", wall, run_async=True)

dispatcher.add_handler(ECHO_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)
dispatcher.add_handler(WIKI_HANDLER)
dispatcher.add_handler(WALLPAPER_HANDLER)

__mod_name__ = "Extras"
__command_list__ = ["id", "echo", "wiki", "wall"]
__handlers__ = [
    ECHO_HANDLER,
    MD_HELP_HANDLER,
    WIKI_HANDLER,
    WALLPAPER_HANDLER,
]
