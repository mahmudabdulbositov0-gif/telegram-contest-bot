





import asyncio
import json
import os
import random
import re

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 7018749665

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    ChatJoinRequest,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    CallbackQuery,
)


# =========================================================
# SOZLAMALAR
# =========================================================




# =========================================================
# FAYLLAR
# =========================================================

CHANNELS_FILE = "channels.json"
USERS_FILE = "users.json"
REQUESTS_FILE = "join_requests.json"
ADMINS_FILE = "admins.json"
WINNER_FILE = "winner.json"
RANDOM_FILE = "random_status.json"


# =========================================================
# BOT
# =========================================================

session = AiohttpSession()

bot = Bot(
    token=BOT_TOKEN,
    session=session
)

dp = Dispatcher()


# =========================================================
# JSON
# =========================================================

def save_json(filename, data):

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )


def load_json(filename, default):

    if not os.path.exists(filename):

        save_json(
            filename,
            default
        )

        return default

    try:

        with open(
            filename,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return default


# =========================================================
# USERS
# =========================================================

def load_users():

    data = load_json(
        USERS_FILE,
        {}
    )

    if isinstance(data, list):

        result = {}

        for item in data:

            try:

                user_id = int(item)

            except:

                continue

            result[str(user_id)] = {

                "id": user_id,

                "first_name": "",

                "username": "",

                "completed_channels": []

            }

        save_json(
            USERS_FILE,
            result
        )

        return result

    if not isinstance(data, dict):

        return {}

    return data


def save_users(data):

    save_json(
        USERS_FILE,
        data
    )


def add_user(user):

    users = load_users()

    key = str(
        user.id
    )

    if key not in users:

        users[key] = {

            "id": user.id,

            "first_name": user.first_name or "",

            "username": user.username or "",

            "completed_channels": []

        }

    else:

        users[key]["first_name"] = (
            user.first_name or ""
        )

        users[key]["username"] = (
            user.username or ""
        )

        if "completed_channels" not in users[key]:

            users[key]["completed_channels"] = []

    save_users(
        users
    )


# =========================================================
# ADMINS
# =========================================================

def load_admins():

    data = load_json(
        ADMINS_FILE,
        []
    )

    if not isinstance(data, list):

        return []

    result = []

    for item in data:

        try:

            result.append(
                int(item)
            )

        except:

            pass

    return result


def save_admins(data):

    save_json(
        ADMINS_FILE,
        data
    )


def is_admin(user_id):

    return (
        user_id == ADMIN_ID
        or user_id in load_admins()
    )


# =========================================================
# CHANNELS
# =========================================================

def load_channels():

    data = load_json(
        CHANNELS_FILE,
        []
    )

    if not isinstance(data, list):

        return []

    result = []

    for item in data:

        if not isinstance(item, dict):

            continue

        item_type = item.get("type")

        if item_type == "channel":

            try:

                channel_id = int(
                    item.get("id")
                )

            except:

                continue

            result.append({

                "type": "channel",

                "id": channel_id,

                "name": item.get(
                    "name",
                    "Kanal"
                ),

                "link": item.get(
                    "link",
                    ""
                )

            })

        elif item_type == "bot":

            result.append({

                "type": "bot",

                "name": item.get(
                    "name",
                    "Bot"
                ),

                "username": item.get(
                    "username",
                    ""
                ),

                "link": item.get(
                    "link",
                    ""
                )

            })

    return result


def save_channels(data):

    save_json(
        CHANNELS_FILE,
        data
    )


# =========================================================
# JOIN REQUESTS
# =========================================================

def load_requests():

    data = load_json(
        REQUESTS_FILE,
        {}
    )

    if not isinstance(data, dict):

        return {}

    return data


def save_requests(data):

    save_json(
        REQUESTS_FILE,
        data
    )


# =========================================================
# WINNER
# =========================================================

def load_winner():

    data = load_json(
        WINNER_FILE,
        {}
    )

    if not isinstance(data, dict):

        return {}

    return data


def save_winner(data):

    save_json(
        WINNER_FILE,
        data
    )


# =========================================================
# RANDOM
# =========================================================

def get_random_status():

    data = load_json(
        RANDOM_FILE,
        {
            "enabled": False
        }
    )

    if not isinstance(data, dict):

        return False

    return bool(
        data.get(
            "enabled",
            False
        )
    )


def set_random_status(status):

    save_json(
        RANDOM_FILE,
        {
            "enabled": status
        }
    )


# =========================================================
# FSM
# =========================================================

class AdminStates(StatesGroup):

    waiting_channel_id = State()

    waiting_channel_link = State()

    waiting_delete_channel = State()

    waiting_admin = State()

    waiting_delete_admin = State()

    waiting_winner = State()

    waiting_broadcast = State()


# =========================================================
# ADMIN KEYBOARD
# =========================================================

def main_admin_keyboard():

    return ReplyKeyboardMarkup(

        keyboard=[

            [
                KeyboardButton(
                    text="➕ Kanal qo‘shish"
                ),
                KeyboardButton(
                    text="❌ Kanalni o‘chirish"
                )
            ],

            [
                KeyboardButton(
                    text="📋 Kanallar ro‘yxati"
                )
            ],

            [
                KeyboardButton(
                    text="👤 Admin qo‘shish"
                ),
                KeyboardButton(
                    text="🗑 Adminni o‘chirish"
                )
            ],

            [
                KeyboardButton(
                    text="🏆 Yutuq egasi"
                ),
                KeyboardButton(
                    text="🗑 Yutuq egasini o‘chirish"
                )
            ],

            [
                KeyboardButton(
                    text="🟢 Randomni yoqish"
                ),
                KeyboardButton(
                    text="🔴 Randomni o‘chirish"
                )
            ],

            [
                KeyboardButton(
                    text="📨 Xabar yuborish"
                )
            ]

        ],

        resize_keyboard=True
    )


def normal_admin_keyboard():

    return ReplyKeyboardMarkup(

        keyboard=[

            [
                KeyboardButton(
                    text="🎲 Random yutuq egasi"
                )
            ]

        ],

        resize_keyboard=True
    )


# =========================================================
# USER KEYBOARD
# =========================================================

async def get_user_keyboard(user_id):

    items = load_channels()

    users = load_users()

    user_data = users.get(
        str(user_id),
        {}
    )

    completed = set()

    for channel_id in user_data.get(
        "completed_channels",
        []
    ):

        try:

            completed.add(
                int(channel_id)
            )

        except:

            pass

    keyboard = []

    for item in items:

        # =================================================
        # CHANNEL
        # =================================================

        if item.get("type") == "channel":

            try:

                channel_id = int(
                    item.get("id")
                )

            except:

                continue

            if channel_id in completed:

                continue

            name = item.get(
                "name",
                "Kanal"
            )

            link = item.get(
                "link",
                ""
            )

            if link:

                keyboard.append([

                    InlineKeyboardButton(
                        text=f"📢 {name}",
                        url=link
                    )

                ])

        # =================================================
        # BOT
        # =================================================

        elif item.get("type") == "bot":

            name = item.get(
                "name",
                "Bot"
            )

            link = item.get(
                "link",
                ""
            )

            if link:

                keyboard.append([

                    InlineKeyboardButton(
                        text=f"🤖 {name}",
                        url=link
                    )

                ])

    keyboard.append([

        InlineKeyboardButton(
            text="✅ Tekshirish",
            callback_data="check_subscription"
        )

    ])

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )


# =========================================================
# START
# =========================================================

@dp.message(
    CommandStart()
)
async def start_handler(
    message: Message,
    state: FSMContext
):

    await state.clear()

    add_user(
        message.from_user
    )

    user_id = message.from_user.id

    # =====================================================
    # MAIN ADMIN
    # =====================================================

    if user_id == ADMIN_ID:

        await message.answer(

            "👑 Asosiy admin panel",

            reply_markup=main_admin_keyboard()

        )

        return

    # =====================================================
    # ADDED ADMIN
    # =====================================================

    if user_id in load_admins():

        await message.answer(

            "👤 Admin panel",

            reply_markup=normal_admin_keyboard()

        )

        return

    # =====================================================
    # USER
    # =====================================================

    channels = [

        item

        for item in load_channels()

        if item.get("type") == "channel"

    ]

    if not channels:

        await message.answer(

            "🎉 TABRIKLAYMIZ!\n\n"

            "Konkursda qatnashishingiz mumkin."

        )

        return

    await message.answer(

        "🏆 KONKURSDA QATNASHISH UCHUN\n\n"

        "Quyidagi barcha kanallarga obuna bo‘ling.\n\n"

        "Shundan keyin «✅ Tekshirish» "
        "tugmasini bosing.",

        reply_markup=await get_user_keyboard(
            user_id
        )

    )


# =========================================================
# JOIN REQUEST
# =========================================================

@dp.chat_join_request()
async def join_request_handler(
    request: ChatJoinRequest
):

    user_id = request.from_user.id

    channel_id = request.chat.id

    requests = load_requests()

    key = str(
        user_id
    )

    if key not in requests:

        requests[key] = []

    if not isinstance(
        requests[key],
        list
    ):

        requests[key] = []

    if channel_id not in requests[key]:

        requests[key].append(
            channel_id
        )

    save_requests(
        requests
    )


# =========================================================
# CHANNEL CHECK
# =========================================================

async def check_channels_for_user(
    user_id
):

    items = load_channels()

    users = load_users()

    requests = load_requests()

    key = str(
        user_id
    )

    if key not in users:

        users[key] = {

            "id": user_id,

            "first_name": "",

            "username": "",

            "completed_channels": []

        }

    if "completed_channels" not in users[key]:

        users[key]["completed_channels"] = []

    # =====================================================
    # OLDIN BAJARILGAN KANALLAR
    # =====================================================

    completed = set()

    for channel_id in users[key][
        "completed_channels"
    ]:

        try:

            completed.add(
                int(channel_id)
            )

        except:

            pass

    # =====================================================
    # JOIN REQUEST
    # =====================================================

    user_requests = requests.get(
        key,
        []
    )

    if not isinstance(
        user_requests,
        list
    ):

        user_requests = []

    request_channels = set()

    for channel_id in user_requests:

        try:

            request_channels.add(
                int(channel_id)
            )

        except:

            pass

    # =====================================================
    # HAR BIR CHANNEL
    # =====================================================

    for item in items:

        if item.get(
            "type"
        ) != "channel":

            continue

        try:

            channel_id = int(
                item.get("id")
            )

        except:

            continue

        if channel_id in completed:

            continue

        passed = False

        # =================================================
        # JOIN REQUEST
        # =================================================

        if channel_id in request_channels:

            passed = True

        # =================================================
        # REAL MEMBERSHIP
        # =================================================

        if not passed:

            try:

                member = await bot.get_chat_member(

                    chat_id=channel_id,

                    user_id=user_id

                )

                status = member.status

                if status in [

                    "member",
                    "administrator",
                    "creator"

                ]:

                    passed = True

                elif (

                    status == "restricted"

                    and getattr(
                        member,
                        "is_member",
                        False
                    )

                ):

                    passed = True

            except Exception:

                passed = False

        if passed:

            completed.add(
                channel_id
            )

    # =====================================================
    # SAQLASH
    # =====================================================

    users[key][
        "completed_channels"
    ] = list(
        completed
    )

    save_users(
        users
    )

    # =====================================================
    # QOLGAN KANALLAR
    # =====================================================

    remaining = []

    for item in items:

        if item.get(
            "type"
        ) != "channel":

            continue

        try:

            channel_id = int(
                item.get("id")
            )

        except:

            continue

        if channel_id not in completed:

            remaining.append(
                item
            )

    return len(
        remaining
    ) == 0


# =========================================================
# CHECK BUTTON
# =========================================================

@dp.callback_query(
    lambda callback:
    callback.data == "check_subscription"
)
async def check_subscription(
    callback: CallbackQuery
):

    user_id = callback.from_user.id

    all_done = await check_channels_for_user(
        user_id
    )

    if all_done:

        await callback.answer(
            "🎉 Barcha shartlar bajarildi!",
            show_alert=True
        )

        try:

            await callback.message.edit_text(

                "🎉 TABRIKLAYMIZ!\n\n"

                "Siz konkursda qatnashish uchun "
                "barcha shartlarni bajardingiz. ✅\n\n"

                "Omad tilaymiz! 🏆"

            )

        except:

            pass

        return

    await callback.answer(
        "✅ Bajarilgan kanallar olib tashlandi!",
        show_alert=True
    )

    try:

        await callback.message.edit_reply_markup(

            reply_markup=await get_user_keyboard(
                user_id
            )

        )

    except:

        pass


# =========================================================
# ➕ KANAL QO'SHISH
# =========================================================

@dp.message(
    lambda message:
    message.text == "➕ Kanal qo‘shish"
    and message.from_user.id == ADMIN_ID
)
async def add_channel_start(
    message: Message,
    state: FSMContext
):

    await state.clear()

    await state.set_state(
        AdminStates.waiting_channel_id
    )

    await message.answer(

        "➕ KANAL YOKI BOT QO‘SHISH\n\n"

        "📢 Kanal uchun kanal ID yuboring:\n"
        "-1001234567890\n\n"

        "🤖 Bot uchun link yuboring:\n"
        "https://t.me/MyBot"

    )


# =========================================================
# CHANNEL ID / BOT LINK
# =========================================================

@dp.message(
    AdminStates.waiting_channel_id
)
async def channel_id_process(
    message: Message,
    state: FSMContext
):

    text = (
        message.text or ""
    ).strip()

    # Agar boshqa admin tugmasi bosilsa
    if text in [

        "➕ Kanal qo‘shish",
        "❌ Kanalni o‘chirish",
        "📋 Kanallar ro‘yxati",
        "👤 Admin qo‘shish",
        "🗑 Adminni o‘chirish",
        "🏆 Yutuq egasi",
        "🗑 Yutuq egasini o‘chirish",
        "🟢 Randomni yoqish",
        "🔴 Randomni o‘chirish",
        "📨 Xabar yuborish"

    ]:

        await state.clear()

        await message.answer(
            "⚙️ Oldingi amal bekor qilindi.\n"
            "Endi tanlagan tugmangizni qaytadan bosing.",
            reply_markup=main_admin_keyboard()
        )

        return

    # =====================================================
    # BOT
    # =====================================================

    bot_match = re.match(

        r"^(?:https?://)?t\.me/"
        r"([A-Za-z0-9_]+)$",

        text

    )

    if bot_match:

        username = bot_match.group(
            1
        )

        link = (
            f"https://t.me/{username}"
        )

        items = load_channels()

        for item in items:

            if (

                item.get("type") == "bot"

                and item.get("link") == link

            ):

                await message.answer(
                    "❌ Bu bot allaqachon qo‘shilgan."
                )

                await state.clear()

                return

        items.append({

            "type": "bot",

            "name": f"@{username}",

            "username": username,

            "link": link

        })

        save_channels(
            items
        )

        await state.clear()

        await message.answer(

            "✅ BOT QO‘SHILDI!\n\n"

            f"🤖 @{username}\n"

            f"🔗 {link}\n\n"

            "ℹ️ Bot tekshirilmaydi.",

            reply_markup=main_admin_keyboard()

        )

        return

    # =====================================================
    # CHANNEL ID
    # =====================================================

    try:

        channel_id = int(
            text
        )

    except:

        await message.answer(

            "❌ Noto‘g‘ri Telegram ID.\n\n"

            "Kanal ID yuboring.\n"
            "Masalan:\n"
            "-1001234567890"

        )

        return

    # =====================================================
    # GET CHAT
    # =====================================================

    try:

        chat = await bot.get_chat(
            channel_id
        )

        channel_name = (
            chat.title
            or "Kanal"
        )

        # =================================================
        # PUBLIC
        # =================================================

        if chat.username:

            link = (
                f"https://t.me/"
                f"{chat.username}"
            )

            items = load_channels()

            for item in items:

                if item.get(
                    "type"
                ) != "channel":

                    continue

                try:

                    old_id = int(
                        item.get("id")
                    )

                except:

                    continue

                if old_id == channel_id:

                    await message.answer(
                        "❌ Bu kanal allaqachon qo‘shilgan."
                    )

                    await state.clear()

                    return

            items.append({

                "type": "channel",

                "id": channel_id,

                "name": channel_name,

                "link": link

            })

            save_channels(
                items
            )

            await state.clear()

            await message.answer(

                "✅ PUBLIC KANAL QO‘SHILDI!\n\n"

                f"📢 {channel_name}\n"

                f"🆔 {channel_id}\n"

                f"🔗 {link}",

                reply_markup=main_admin_keyboard()

            )

            return

        # =================================================
        # PRIVATE
        # =================================================

        await state.update_data(

            channel_id=channel_id,

            channel_name=channel_name

        )

        await state.set_state(
            AdminStates.waiting_channel_link
        )

        await message.answer(

            "🔒 PRIVATE KANAL ANIQLANDI!\n\n"

            f"📢 {channel_name}\n"

            f"🆔 {channel_id}\n\n"

            "Join Request invite linkini yuboring.\n\n"

            "Misol:\n"
            "https://t.me/+AbCdEf123456"

        )

    except Exception:

        await message.answer(

            "❌ Kanal topilmadi.\n\n"

            "Bot kanalga admin qilinganini "
            "tekshiring."

        )


# =========================================================
# PRIVATE CHANNEL LINK
# =========================================================

@dp.message(
    AdminStates.waiting_channel_link
)
async def private_channel_link_process(
    message: Message,
    state: FSMContext
):

    text = (
        message.text or ""
    ).strip()

    # Boshqa admin tugmasi
    if text in [

        "➕ Kanal qo‘shish",
        "❌ Kanalni o‘chirish",
        "📋 Kanallar ro‘yxati",
        "👤 Admin qo‘shish",
        "🗑 Adminni o‘chirish",
        "🏆 Yutuq egasi",
        "🗑 Yutuq egasini o‘chirish",
        "🟢 Randomni yoqish",
        "🔴 Randomni o‘chirish",
        "📨 Xabar yuborish"

    ]:

        await state.clear()

        await message.answer(
            "⚙️ Oldingi amal bekor qilindi.",
            reply_markup=main_admin_keyboard()
        )

        return

    if not re.match(

        r"^https://t\.me/\+[A-Za-z0-9_-]+$",

        text

    ):

        await message.answer(

            "❌ Join Request link noto‘g‘ri.\n\n"

            "Misol:\n"
            "https://t.me/+AbCdEf123456"

        )

        return

    data = await state.get_data()

    channel_id = data.get(
        "channel_id"
    )

    channel_name = data.get(
        "channel_name",
        "Kanal"
    )

    items = load_channels()

    for item in items:

        if item.get(
            "type"
        ) != "channel":

            continue

        try:

            old_id = int(
                item.get("id")
            )

        except:

            continue

        if old_id == int(
            channel_id
        ):

            await message.answer(
                "❌ Bu kanal allaqachon qo‘shilgan."
            )

            await state.clear()

            return

    items.append({

        "type": "channel",

        "id": int(channel_id),

        "name": channel_name,

        "link": text

    })

    save_channels(
        items
    )

    await state.clear()

    await message.answer(

        "✅ PRIVATE KANAL QO‘SHILDI!\n\n"

        f"📢 {channel_name}\n"

        f"🆔 {channel_id}\n"

        f"🔗 {text}",

        reply_markup=main_admin_keyboard()

    )


# =========================================================
# ❌ KANAL O'CHIRISH
# =========================================================

@dp.message(
    lambda message:
    message.text == "❌ Kanalni o‘chirish"
    and message.from_user.id == ADMIN_ID
)
async def delete_channel_start(
    message: Message,
    state: FSMContext
):

    await state.clear()

    items = load_channels()

    if not items:

        await message.answer(
            "📭 Kanal yoki bot yo‘q."
        )

        return

    text = (
        "❌ KANAL / BOT O‘CHIRISH\n\n"
    )

    for index, item in enumerate(
        items,
        1
    ):

        if item.get(
            "type"
        ) == "channel":

            text += (

                f"{index}. 📢 {item.get('name')}\n"
                f"ID: {item.get('id')}\n\n"

            )

        else:

            text += (

                f"{index}. 🤖 {item.get('name')}\n"
                f"Link: {item.get('link')}\n\n"

            )

    await state.set_state(
        AdminStates.waiting_delete_channel
    )

    await message.answer(
        text
    )


# =========================================================
# DELETE CHANNEL
# =========================================================

@dp.message(
    AdminStates.waiting_delete_channel
)
async def delete_channel_process(
    message: Message,
    state: FSMContext
):

    text = (
        message.text or ""
    ).strip()

    # Boshqa admin tugmasi
    if text in [

        "➕ Kanal qo‘shish",
        "❌ Kanalni o‘chirish",
        "📋 Kanallar ro‘yxati",
        "👤 Admin qo‘shish",
        "🗑 Adminni o‘chirish",
        "🏆 Yutuq egasi",
        "🗑 Yutuq egasini o‘chirish",
        "🟢 Randomni yoqish",
        "🔴 Randomni o‘chirish",
        "📨 Xabar yuborish"

    ]:

        await state.clear()

        await message.answer(
            "⚙️ Oldingi amal bekor qilindi.",
            reply_markup=main_admin_keyboard()
        )

        return

    items = load_channels()

    new_items = []

    deleted = None

    for item in items:

        if item.get(
            "type"
        ) == "channel":

            try:

                if int(text) == int(
                    item.get("id")
                ):

                    deleted = item

                    continue

            except:

                pass

        elif item.get(
            "type"
        ) == "bot":

            username = item.get(
                "username",
                ""
            )

            link = item.get(
                "link",
                ""
            )

            if (

                text == username
                or text == f"@{username}"
                or text == link

            ):

                deleted = item

                continue

        new_items.append(
            item
        )

    if deleted is None:

        await message.answer(
            "❌ Kanal yoki bot topilmadi."
        )

        await state.clear()

        return

    save_channels(
        new_items
    )

    await state.clear()

    await message.answer(

        "✅ O‘CHIRILDI!\n\n"

        f"{deleted.get('name')}",

        reply_markup=main_admin_keyboard()

    )


# =========================================================
# 📋 RO'YXAT
# =========================================================

@dp.message(
    lambda message:
    message.text == "📋 Kanallar ro‘yxati"
    and message.from_user.id == ADMIN_ID
)
async def channels_list(
    message: Message,
    state: FSMContext
):

    await state.clear()

    items = load_channels()

    if not items:

        await message.answer(
            "📭 Kanal yoki bot yo‘q."
        )

        return

    text = (
        "📋 KANALLAR / BOTLAR\n\n"
    )

    for index, item in enumerate(
        items,
        1
    ):

        if item.get(
            "type"
        ) == "channel":

            text += (

                f"{index}. 📢 KANAL\n"
                f"Nom: {item.get('name')}\n"
                f"ID: {item.get('id')}\n"
                f"Link: {item.get('link') or 'Yo‘q'}\n\n"

            )

        else:

            text += (

                f"{index}. 🤖 BOT\n"
                f"Nom: {item.get('name')}\n"
                f"Link: {item.get('link')}\n\n"

            )

    await message.answer(
        text
    )


# =========================================================
# 👤 ADMIN QO'SHISH
# =========================================================

@dp.message(
    lambda message:
    message.text == "👤 Admin qo‘shish"
    and message.from_user.id == ADMIN_ID
)
async def add_admin_start(
    message: Message,
    state: FSMContext
):

    await state.clear()

    await state.set_state(
        AdminStates.waiting_admin
    )

    await message.answer(
        "👤 Admin Telegram ID yuboring:"
    )


# =========================================================
# ADD ADMIN PROCESS
# =========================================================

@dp.message(
    AdminStates.waiting_admin
)
async def add_admin_process(
    message: Message,
    state: FSMContext
):

    text = (
        message.text or ""
    ).strip()

    # =====================================================
    # BOSHQA ADMIN TUGMASI BOSILSA
    # =====================================================

    if text in [

        "➕ Kanal qo‘shish",
        "❌ Kanalni o‘chirish",
        "📋 Kanallar ro‘yxati",
        "👤 Admin qo‘shish",
        "🗑 Adminni o‘chirish",
        "🏆 Yutuq egasi",
        "🗑 Yutuq egasini o‘chirish",
        "🟢 Randomni yoqish",
        "🔴 Randomni o‘chirish",
        "📨 Xabar yuborish"

    ]:

        await state.clear()

        await message.answer(
            "⚙️ Oldingi amal bekor qilindi.",
            reply_markup=main_admin_keyboard()
        )

        return

    try:

        user_id = int(
            text
        )

    except:

        await message.answer(

            "❌ Noto‘g‘ri Telegram ID.\n\n"

            "Masalan:\n"
            "123456789"

        )

        return

    if user_id == ADMIN_ID:

        await message.answer(
            "❌ Bu asosiy admin."
        )

        await state.clear()

        return

    admins = load_admins()

    if user_id in admins:

        await message.answer(
            "❌ Bu user allaqachon admin."
        )

        await state.clear()

        return

    admins.append(
        user_id
    )

    save_admins(
        admins
    )

    await state.clear()

    await message.answer(

        "✅ ADMIN QO‘SHILDI!\n\n"

        f"🆔 {user_id}",

        reply_markup=main_admin_keyboard()

    )


# =========================================================
# 🗑 ADMIN O'CHIRISH
# =========================================================

@dp.message(
    lambda message:
    message.text == "🗑 Adminni o‘chirish"
    and message.from_user.id == ADMIN_ID
)
async def delete_admin_start(
    message: Message,
    state: FSMContext
):

    await state.clear()

    admins = load_admins()

    if not admins:

        await message.answer(
            "📭 Adminlar yo‘q."
        )

        return

    text = (
        "🗑 ADMIN O‘CHIRISH\n\n"
    )

    for admin_id in admins:

        text += (
            f"👤 {admin_id}\n"
        )

    text += (
        "\nAdmin ID yuboring."
    )

    await state.set_state(
        AdminStates.waiting_delete_admin
    )

    await message.answer(
        text
    )


# =========================================================
# DELETE ADMIN PROCESS
# =========================================================

@dp.message(
    AdminStates.waiting_delete_admin
)
async def delete_admin_process(
    message: Message,
    state: FSMContext
):

    text = (
        message.text or ""
    ).strip()

    if text in [

        "➕ Kanal qo‘shish",
        "❌ Kanalni o‘chirish",
        "📋 Kanallar ro‘yxati",
        "👤 Admin qo‘shish",
        "🗑 Adminni o‘chirish",
        "🏆 Yutuq egasi",
        "🗑 Yutuq egasini o‘chirish",
        "🟢 Randomni yoqish",
        "🔴 Randomni o‘chirish",
        "📨 Xabar yuborish"

    ]:

        await state.clear()

        await message.answer(
            "⚙️ Oldingi amal bekor qilindi.",
            reply_markup=main_admin_keyboard()
        )

        return

    try:

        user_id = int(
            text
        )

    except:

        await message.answer(
            "❌ Noto‘g‘ri Telegram ID."
        )

        return

    admins = load_admins()

    if user_id not in admins:

        await message.answer(
            "❌ Bu admin topilmadi."
        )

        await state.clear()

        return

    admins.remove(
        user_id
    )

    save_admins(
        admins
    )

    await state.clear()

    await message.answer(

        "✅ ADMIN O‘CHIRILDI!",

        reply_markup=main_admin_keyboard()

    )


# =========================================================
# 🏆 YUTUQ EGASI
# =========================================================

@dp.message(
    lambda message:
    message.text == "🏆 Yutuq egasi"
    and message.from_user.id == ADMIN_ID
)
async def winner_start(
    message: Message,
    state: FSMContext
):

    await state.clear()

    await state.set_state(
        AdminStates.waiting_winner
    )

    await message.answer(
        "🏆 Yutuq egasi Telegram ID yuboring:"
    )


# =========================================================
# WINNER PROCESS
# =========================================================

@dp.message(
    AdminStates.waiting_winner
)
async def winner_process(
    message: Message,
    state: FSMContext
):

    text = (
        message.text or ""
    ).strip()

    if text in [

        "➕ Kanal qo‘shish",
        "❌ Kanalni o‘chirish",
        "📋 Kanallar ro‘yxati",
        "👤 Admin qo‘shish",
        "🗑 Adminni o‘chirish",
        "🏆 Yutuq egasi",
        "🗑 Yutuq egasini o‘chirish",
        "🟢 Randomni yoqish",
        "🔴 Randomni o‘chirish",
        "📨 Xabar yuborish"

    ]:

        await state.clear()

        await message.answer(
            "⚙️ Oldingi amal bekor qilindi.",
            reply_markup=main_admin_keyboard()
        )

        return

    try:

        user_id = int(
            text
        )

    except:

        await message.answer(
            "❌ Noto‘g‘ri Telegram ID."
        )

        return

    save_winner({

        "user_id": user_id

    })

    await state.clear()

    await message.answer(

        "🏆 YUTUQ EGASI BELGILANDI!\n\n"

        f"🆔 {user_id}",

        reply_markup=main_admin_keyboard()

    )


# =========================================================
# 🗑 WINNER DELETE
# =========================================================

@dp.message(
    lambda message:
    message.text == "🗑 Yutuq egasini o‘chirish"
    and message.from_user.id == ADMIN_ID
)
async def delete_winner(
    message: Message,
    state: FSMContext
):

    await state.clear()

    save_winner({})

    await message.answer(

        "✅ Yutuq egasi o‘chirildi.",

        reply_markup=main_admin_keyboard()

    )


# =========================================================
# RANDOM ON
# =========================================================

@dp.message(
    lambda message:
    message.text == "🟢 Randomni yoqish"
    and message.from_user.id == ADMIN_ID
)
async def random_on(
    message: Message,
    state: FSMContext
):

    await state.clear()

    set_random_status(
        True
    )

    await message.answer(

        "🟢 RANDOM YOQILDI!",

        reply_markup=main_admin_keyboard()

    )


# =========================================================
# RANDOM OFF
# =========================================================

@dp.message(
    lambda message:
    message.text == "🔴 Randomni o‘chirish"
    and message.from_user.id == ADMIN_ID
)
async def random_off(
    message: Message,
    state: FSMContext
):

    await state.clear()

    set_random_status(
        False
    )

    await message.answer(

        "🔴 RANDOM O‘CHIRILDI!",

        reply_markup=main_admin_keyboard()

    )


# =========================================================
# RANDOM WINNER
# =========================================================

async def get_random_winner():

    users = load_users()

    admins = load_admins()

    channels = load_channels()

    mandatory_channels = []

    for item in channels:

        if item.get(
            "type"
        ) != "channel":

            continue

        try:

            mandatory_channels.append(
                int(
                    item.get("id")
                )
            )

        except:

            pass

    candidates = []

    for user_key, user_data in users.items():

        try:

            user_id = int(
                user_key
            )

        except:

            continue

        if user_id == ADMIN_ID:

            continue

        if user_id in admins:

            continue

        completed = set()

        for channel_id in user_data.get(
            "completed_channels",
            []
        ):

            try:

                completed.add(
                    int(channel_id)
                )

            except:

                pass

        if all(
            channel_id in completed
            for channel_id in mandatory_channels
        ):

            candidates.append(
                user_id
            )

    if not candidates:

        return None

    return random.choice(
        candidates
    )


# =========================================================
# 🎲 RANDOM WINNER
# =========================================================

@dp.message(
    lambda message:
    message.text == "🎲 Random yutuq egasi"
    and is_admin(message.from_user.id)
)
async def random_winner_handler(
    message: Message,
    state: FSMContext
):

    await state.clear()

    countdown = await message.answer(
        "9"
    )

    for number in range(
        8,
        0,
        -1
    ):

        await asyncio.sleep(
            1
        )

        try:

            await countdown.edit_text(
                str(number)
            )

        except:

            pass

    await asyncio.sleep(
        1
    )

    try:

        await countdown.delete()

    except:

        pass

    # =====================================================
    # RANDOM
    # =====================================================

    if get_random_status():

        winner_id = await get_random_winner()

        if winner_id is None:

            await message.answer(

                "❌ Barcha shartlarni "
                "bajargan user topilmadi."

            )

            return

    # =====================================================
    # MANUAL
    # =====================================================

    else:

        winner = load_winner()

        winner_id = winner.get(
            "user_id"
        )

        if not winner_id:

            await message.answer(
                "❌ Yutuq egasi belgilanmagan."
            )

            return

        try:

            winner_id = int(
                winner_id
            )

        except:

            await message.answer(
                "❌ Winner ID noto‘g‘ri."
            )

            return

    users = load_users()

    user_data = users.get(
        str(winner_id),
        {}
    )

    first_name = user_data.get(
        "first_name",
        "Noma’lum"
    )

    username = user_data.get(
        "username",
        ""
    )

    username_text = ""

    if username:

        username_text = (
            f"\nUsername: @{username}"
        )

    await message.answer(

        "🏆 YUTUQ EGASI!\n\n"

        f"👤 {first_name}\n"

        f"🆔 {winner_id}"

        f"{username_text}\n\n"

        "🎉 Tabriklaymiz!"

    )


# =========================================================
# 📨 BROADCAST
# =========================================================

@dp.message(
    lambda message:
    message.text == "📨 Xabar yuborish"
    and message.from_user.id == ADMIN_ID
)
async def broadcast_start(
    message: Message,
    state: FSMContext
):

    await state.clear()

    await state.set_state(
        AdminStates.waiting_broadcast
    )

    await message.answer(

        "📨 XABAR YUBORISH\n\n"

        "Yubormoqchi bo‘lgan xabaringizni "
        "shu yerga yuboring."

    )


# =========================================================
# BROADCAST PROCESS
# =========================================================

@dp.message(
    AdminStates.waiting_broadcast
)
async def broadcast_process(
    message: Message,
    state: FSMContext
):

    text = (
        message.text or ""
    ).strip()

    if text in [

        "➕ Kanal qo‘shish",
        "❌ Kanalni o‘chirish",
        "📋 Kanallar ro‘yxati",
        "👤 Admin qo‘shish",
        "🗑 Adminni o‘chirish",
        "🏆 Yutuq egasi",
        "🗑 Yutuq egasini o‘chirish",
        "🟢 Randomni yoqish",
        "🔴 Randomni o‘chirish",
        "📨 Xabar yuborish"

    ]:

        await state.clear()

        await message.answer(
            "⚙️ Xabar yuborish bekor qilindi.",
            reply_markup=main_admin_keyboard()
        )

        return

    users = load_users()

    total = len(
        users
    )

    if total == 0:

        await message.answer(
            "📭 Userlar yo‘q."
        )

        await state.clear()

        return

    status_message = await message.answer(

        "📨 Xabar yuborilmoqda...\n\n"

        f"👥 Jami: {total}"

    )

    success = 0

    failed = 0

    for user_key in users.keys():

        try:

            user_id = int(
                user_key
            )

            await message.copy_to(
                chat_id=user_id
            )

            success += 1

        except:

            failed += 1

        await asyncio.sleep(
            0.05
        )

    try:

        await status_message.edit_text(

            "✅ XABAR YUBORILDI!\n\n"

            f"👥 Jami: {total}\n"

            f"✅ Yetkazildi: {success}\n"

            f"❌ Xatolik: {failed}"

        )

    except:

        await message.answer(

            "✅ XABAR YUBORILDI!\n\n"

            f"👥 Jami: {total}\n"

            f"✅ Yetkazildi: {success}\n"

            f"❌ Xatolik: {failed}"

        )

    await state.clear()


# =========================================================
# ODDIY ADMIN / USER MESSAGE
# =========================================================

@dp.message()
async def unknown_message(
    message: Message
):

    user_id = message.from_user.id

    if user_id == ADMIN_ID:

        await message.answer(

            "⚙️ Admin paneldan kerakli "
            "tugmani tanlang.",

            reply_markup=main_admin_keyboard()

        )

        return

    if user_id in load_admins():

        await message.answer(

            "⚙️ Kerakli tugmani tanlang.",

            reply_markup=normal_admin_keyboard()

        )


# =========================================================
# MAIN
# =========================================================

async def main():

    print(
        "BOT ISHGA TUSHDI"
    )

    await dp.start_polling(

        bot,

        allowed_updates=dp.resolve_used_update_types()

    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        pass
