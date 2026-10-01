import asyncio
import json
import os
import random
import re

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

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Asosiy admin Telegram ID
ADMIN_ID = 7018749665


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
# JSON FUNKSIYALAR
# =========================================================

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )


def load_json(filename, default):
    if not os.path.exists(filename):
        save_json(filename, default)
        return default

    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception:
        return default


# =========================================================
# USERS
# =========================================================

def load_users():
    data = load_json(USERS_FILE, {})

    if isinstance(data, list):
        result = {}

        for user in data:
            if not isinstance(user, dict):
                continue

            user_id = user.get("id")

            if user_id is None:
                continue

            result[str(user_id)] = user

        save_json(USERS_FILE, result)
        return result

    if not isinstance(data, dict):
        return {}

    return data


def save_users(data):
    save_json(USERS_FILE, data)


def add_user(user):
    users = load_users()

    user_id = str(user.id)

    if user_id not in users:
        users[user_id] = {
            "id": user.id,
            "first_name": user.first_name or "",
            "username": user.username or "",
            "completed_channels": []
        }

    else:
        users[user_id]["first_name"] = user.first_name or ""
        users[user_id]["username"] = user.username or ""

        if "completed_channels" not in users[user_id]:
            users[user_id]["completed_channels"] = []

    save_users(users)


# =========================================================
# ADMINS
# =========================================================

def load_admins():
    data = load_json(ADMINS_FILE, [])

    if not isinstance(data, list):
        return []

    result = []

    for item in data:
        try:
            result.append(int(item))
        except Exception:
            pass

    return result


def save_admins(data):
    save_json(ADMINS_FILE, data)


def is_admin(user_id):
    if user_id == ADMIN_ID:
        return True

    return user_id in load_admins()


# =========================================================
# CHANNELS
# =========================================================

def load_channels():
    data = load_json(CHANNELS_FILE, [])

    if not isinstance(data, list):
        return []

    return data


def save_channels(data):
    save_json(CHANNELS_FILE, data)


# =========================================================
# JOIN REQUESTS
# =========================================================

def load_requests():
    data = load_json(REQUESTS_FILE, {})

    if not isinstance(data, dict):
        return {}

    return data


def save_requests(data):
    save_json(REQUESTS_FILE, data)


# =========================================================
# WINNER
# =========================================================

def load_winner():
    data = load_json(WINNER_FILE, {})

    if not isinstance(data, dict):
        return {}

    return data


def save_winner(data):
    save_json(WINNER_FILE, data)


# =========================================================
# RANDOM
# =========================================================

def load_random_status():
    data = load_json(
        RANDOM_FILE,
        {"enabled": False}
    )

    if not isinstance(data, dict):
        return {"enabled": False}

    return data


def save_random_status(data):
    save_json(RANDOM_FILE, data)


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
                KeyboardButton(text="➕ Kanal qo‘shish"),
                KeyboardButton(text="❌ Kanalni o‘chirish")
            ],
            [
                KeyboardButton(text="📋 Kanallar ro‘yxati")
            ],
            [
                KeyboardButton(text="👤 Admin qo‘shish"),
                KeyboardButton(text="🗑 Adminni o‘chirish")
            ],
            [
                KeyboardButton(text="🏆 Yutuq egasi"),
                KeyboardButton(text="🗑 Yutuq egasini o‘chirish")
            ],
            [
                KeyboardButton(text="🟢 Randomni yoqish"),
                KeyboardButton(text="🔴 Randomni o‘chirish")
            ],
            [
                KeyboardButton(text="📨 Xabar yuborish")
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
            ],
            [
                KeyboardButton(
                    text="👥 Qatnashuvchilar"
                )
            ]
        ],
        resize_keyboard=True
    )


# =========================================================
# USER KEYBOARD
# =========================================================

def get_user_keyboard(user_id):

    channels = load_channels()

    users = load_users()

    user = users.get(str(user_id), {})

    completed_channels = user.get(
        "completed_channels",
        []
    )

    buttons = []

    for item in channels:

        item_type = item.get("type")

        if item_type == "channel":

            try:
                channel_id = int(item.get("id"))
            except Exception:
                continue

            if channel_id in completed_channels:
                continue

            name = item.get(
                "name",
                "Kanal"
            )

            link = item.get(
                "link",
                ""
            )

            if not link:
                continue

            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"📢 {name}",
                        url=link
                    )
                ]
            )

        elif item_type == "bot":

            name = item.get(
                "name",
                "Bot"
            )

            link = item.get(
                "link",
                ""
            )

            if not link:
                continue

            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"🤖 {name}",
                        url=link
                    )
                ]
            )

    buttons.append(
        [
            InlineKeyboardButton(
                text="✅ Tekshirish",
                callback_data="check_channels"
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


# =========================================================
# CHANNEL CHECK
# =========================================================

async def check_channels_for_user(user_id):

    channels = load_channels()

    users = load_users()

    requests = load_requests()

    mandatory_channels = []

    for item in channels:

        if item.get("type") != "channel":
            continue

        try:
            channel_id = int(item.get("id"))
        except Exception:
            continue

        mandatory_channels.append(channel_id)

    if not mandatory_channels:

        return True

    key = str(user_id)

    requested_channels = requests.get(
        key,
        []
    )

    if not isinstance(
        requested_channels,
        list
    ):
        requested_channels = []

    requested_set = set()

    for channel_id in requested_channels:

        try:
            requested_set.add(
                int(channel_id)
            )
        except Exception:
            pass

    completed_channels = []

    for channel_id in mandatory_channels:

        passed = channel_id in requested_set

        if not passed:

            try:

                member = await bot.get_chat_member(
                    chat_id=channel_id,
                    user_id=user_id
                )

                if member.status in [
                    "member",
                    "administrator",
                    "creator"
                ]:
                    passed = True

                elif (
                    member.status == "restricted"
                    and getattr(
                        member,
                        "is_member",
                        False
                    )
                ):
                    passed = True

            except Exception:
                pass

        if passed:

            completed_channels.append(
                channel_id
            )

    if key not in users:

        users[key] = {
            "id": user_id,
            "first_name": "",
            "username": "",
            "completed_channels": []
        }

    users[key]["completed_channels"] = (
        completed_channels
    )

    save_users(users)

    return len(
        completed_channels
    ) == len(
        mandatory_channels
    )


# =========================================================
# /START
# =========================================================

@dp.message(CommandStart())
async def start_handler(
    message: Message,
    state: FSMContext
):

    await state.clear()

    add_user(
        message.from_user
    )

    user_id = message.from_user.id

    if user_id == ADMIN_ID:

        await message.answer(
            "👑 <b>ASOSIY ADMIN PANEL</b>",
            parse_mode="HTML",
            reply_markup=main_admin_keyboard()
        )

        return

    if user_id in load_admins():

        await message.answer(
            "🛡 <b>ADMIN PANEL</b>",
            parse_mode="HTML",
            reply_markup=normal_admin_keyboard()
        )

        return

    await message.answer(
        "🎁 <b>KONKURSDA QATNASHISH UCHUN</b>\n\n"
        "Quyidagi kanallarga qo‘shiling yoki Join Request yuboring.\n\n"
        "So‘ng <b>✅ Tekshirish</b> tugmasini bosing.",
        parse_mode="HTML",
        reply_markup=get_user_keyboard(user_id)
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

    key = str(user_id)

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

    save_requests(requests)

    add_user(
        request.from_user
    )


# =========================================================
# CHECK BUTTON
# =========================================================

@dp.callback_query(
    lambda callback:
    callback.data == "check_channels"
)
async def check_button_handler(
    callback: CallbackQuery
):

    user_id = callback.from_user.id

    result = await check_channels_for_user(
        user_id
    )

    if result:

        await callback.message.edit_text(
            "🎉 <b>TABRIKLAYMIZ!</b>\n\n"
            "Siz barcha shartlarni bajardingiz.\n"
            "Endi konkursda qatnashyapsiz! 🔥",
            parse_mode="HTML"
        )

    else:

        await callback.answer(
            "❌ Hali barcha kanallarga qo‘shilmagansiz.",
            show_alert=True
        )

        try:
            await callback.message.edit_reply_markup(
                reply_markup=get_user_keyboard(
                    user_id
                )
            )
        except Exception:
            pass

    await callback.answer()


# =========================================================
# ➕ KANAL QO‘SHISH
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
        "➕ <b>KANAL YOKI BOT QO‘SHISH</b>\n\n"

        "📢 <b>Kanal uchun</b> kanal ID yuboring:\n"
        "<code>-1001234567890</code>\n\n"

        "🤖 <b>Bot uchun</b> link yuboring:\n"
        "<code>https://t.me/MyBot</code>",
        parse_mode="HTML"
    )


# =========================================================
# KANAL ID / BOT LINK
# =========================================================

@dp.message(
    AdminStates.waiting_channel_id
)
async def channel_id_process(
    message: Message,
    state: FSMContext
):

    text = (message.text or "").strip()

    stop_buttons = [
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
    ]

    if text in stop_buttons:

        await state.clear()

        await message.answer(
            "❌ Amal bekor qilindi.",
            reply_markup=main_admin_keyboard()
        )

        return

    # -----------------------------------------------------
    # BOT
    # -----------------------------------------------------

    bot_match = re.match(
        r"^(?:https?://)?t\.me/([A-Za-z0-9_]+)$",
        text
    )

    if bot_match:

        username = bot_match.group(1)

        items = load_channels()

        for item in items:

            if (
                item.get("type") == "bot"
                and item.get("username", "").lower()
                == username.lower()
            ):

                await state.clear()

                await message.answer(
                    "❌ Bu bot allaqachon ro‘yxatda mavjud.",
                    reply_markup=main_admin_keyboard()
                )

                return

        items.append(
            {
                "type": "bot",
                "name": f"@{username}",
                "username": username,
                "link": f"https://t.me/{username}"
            }
        )

        save_channels(items)

        await state.clear()

        await message.answer(
            "✅ <b>BOT QO‘SHILDI!</b>\n\n"
            f"🤖 @{username}",
            parse_mode="HTML",
            reply_markup=main_admin_keyboard()
        )

        return

    # -----------------------------------------------------
    # CHANNEL ID
    # -----------------------------------------------------

    try:

        channel_id = int(text)

    except Exception:

        await message.answer(
            "❌ Noto‘g‘ri format.\n\n"
            "Kanal ID misol:\n"
            "<code>-1001234567890</code>\n\n"
            "Yoki bot linki:\n"
            "<code>https://t.me/MyBot</code>",
            parse_mode="HTML"
        )

        return

    try:

        chat = await bot.get_chat(
            channel_id
        )

        channel_name = (
            chat.title
            or "Kanal"
        )

        # -------------------------------------------------
        # DUPLICATE
        # -------------------------------------------------

        items = load_channels()

        for item in items:

            if item.get("type") != "channel":
                continue

            try:
                old_id = int(
                    item.get("id")
                )
            except Exception:
                continue

            if old_id == channel_id:

                await state.clear()

                await message.answer(
                    "❌ Bu kanal allaqachon "
                    "kanallar ro‘yxatida mavjud.",
                    reply_markup=main_admin_keyboard()
                )

                return

        # -------------------------------------------------
        # PUBLIC CHANNEL
        # -------------------------------------------------

        if chat.username:

            link = (
                f"https://t.me/{chat.username}"
            )

            items.append(
                {
                    "type": "channel",
                    "id": channel_id,
                    "name": channel_name,
                    "link": link
                }
            )

            save_channels(items)

            await state.clear()

            await message.answer(
                "✅ <b>PUBLIC KANAL QO‘SHILDI!</b>\n\n"
                f"📢 {channel_name}\n"
                f"🆔 <code>{channel_id}</code>\n"
                f"🔗 {link}",
                parse_mode="HTML",
                reply_markup=main_admin_keyboard()
            )

            return

        # -------------------------------------------------
        # PRIVATE CHANNEL
        # -------------------------------------------------

        await state.update_data(
            channel_id=channel_id,
            channel_name=channel_name
        )

        await state.set_state(
            AdminStates.waiting_channel_link
        )

        await message.answer(
            "🔒 <b>PRIVATE KANAL ANIQLANDI!</b>\n\n"
            f"📢 {channel_name}\n"
            f"🆔 <code>{channel_id}</code>\n\n"
            "Endi shu kanalning <b>Join Request invite link</b>ini yuboring.\n\n"
            "Masalan:\n"
            "<code>https://t.me/+AbCdEf123456</code>",
            parse_mode="HTML"
        )

    except Exception as e:

        print(
            f"CHANNEL GET ERROR: {e}"
        )

        await message.answer(
            "❌ Kanal topilmadi.\n\n"
            "Tekshiring:\n"
            "1. Kanal ID to‘g‘ri ekanini\n"
            "2. Bot kanalga admin qilib qo‘shilganini\n"
            "3. Botda kanalni boshqarish huquqi borligini"
        )


# =========================================================
# 🔒 PRIVATE CHANNEL LINK
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
    ).strip().rstrip("/")

    # Join Request invite link
    if not re.match(
        r"^https?://t\.me/\+[A-Za-z0-9_-]+$",
        text
    ):

        await message.answer(
            "❌ <b>Join Request link noto‘g‘ri.</b>\n\n"
            "Private kanalning Join Request linkini yuboring.\n\n"
            "Masalan:\n"
            "<code>https://t.me/+AbCdEf123456</code>",
            parse_mode="HTML"
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

    if not channel_id:

        await state.clear()

        await message.answer(
            "❌ Kanal ma'lumotlari topilmadi.\n"
            "Kanalni qaytadan qo‘shing.",
            reply_markup=main_admin_keyboard()
        )

        return

    items = load_channels()

    # -----------------------------------------------------
    # DUPLICATE
    # -----------------------------------------------------

    for item in items:

        if item.get("type") != "channel":
            continue

        try:
            old_id = int(
                item.get("id")
            )
        except Exception:
            continue

        if old_id == int(channel_id):

            await state.clear()

            await message.answer(
                "❌ Bu kanal allaqachon "
                "kanallar ro‘yxatida mavjud.",
                reply_markup=main_admin_keyboard()
            )

            return

    # -----------------------------------------------------
    # SAVE PRIVATE CHANNEL
    # -----------------------------------------------------

    items.append(
        {
            "type": "channel",
            "id": int(channel_id),
            "name": channel_name,
            "link": text
        }
    )

    save_channels(items)

    await state.clear()

    await message.answer(
        "✅ <b>PRIVATE KANAL QO‘SHILDI!</b>\n\n"
        f"📢 {channel_name}\n"
        f"🆔 <code>{channel_id}</code>\n"
        f"🔗 {text}\n\n"
        "📋 Kanal ro‘yxatiga muvaffaqiyatli qo‘shildi.",
        parse_mode="HTML",
        reply_markup=main_admin_keyboard()
    )


# =========================================================
# 📋 KANALLAR RO‘YXATI
# =========================================================

@dp.message(
    lambda message:
    message.text == "📋 Kanallar ro‘yxati"
    and message.from_user.id == ADMIN_ID
)
async def channels_list_handler(
    message: Message,
    state: FSMContext
):

    await state.clear()

    channels = load_channels()

    if not channels:

        await message.answer(
            "📭 Hozircha kanallar yoki botlar yo‘q.",
            reply_markup=main_admin_keyboard()
        )

        return

    text = "📋 <b>KANALLAR RO‘YXATI</b>\n\n"

    for index, item in enumerate(
        channels,
        start=1
    ):

        item_type = item.get(
            "type"
        )

        if item_type == "channel":

            name = item.get(
                "name",
                "Kanal"
            )

            channel_id = item.get(
                "id",
                ""
            )

            link = item.get(
                "link",
                ""
            )

            text += (
                f"{index}. 📢 <b>{name}</b>\n"
                f"🆔 <code>{channel_id}</code>\n"
                f"🔗 {link}\n\n"
            )

        elif item_type == "bot":

            name = item.get(
                "name",
                "Bot"
            )

            link = item.get(
                "link",
                ""
            )

            text += (
                f"{index}. 🤖 <b>{name}</b>\n"
                f"🔗 {link}\n\n"
            )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=main_admin_keyboard()
    )


# =========================================================
# ❌ KANAL O‘CHIRISH
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

    channels = load_channels()

    if not channels:

        await message.answer(
            "📭 O‘chirish uchun kanal yo‘q.",
            reply_markup=main_admin_keyboard()
        )

        return

    text = (
        "❌ <b>KANAL O‘CHIRISH</b>\n\n"
        "O‘chirmoqchi bo‘lgan kanalning ID raqamini yuboring.\n\n"
    )

    for item in channels:

        if item.get("type") != "channel":
            continue

        text += (
            f"📢 {item.get('name', 'Kanal')}\n"
            f"🆔 <code>{item.get('id')}</code>\n\n"
        )

    await state.set_state(
        AdminStates.waiting_delete_channel
    )

    await message.answer(
        text,
        parse_mode="HTML"
    )


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

    try:

        channel_id = int(text)

    except Exception:

        await message.answer(
            "❌ Kanal ID raqamini to‘g‘ri yuboring."
        )

        return

    channels = load_channels()

    new_channels = []

    found = False

    for item in channels:

        if item.get("type") != "channel":

            new_channels.append(item)

            continue

        try:
            item_id = int(
                item.get("id")
            )
        except Exception:

            new_channels.append(item)

            continue

        if item_id == channel_id:

            found = True

        else:

            new_channels.append(item)

    if not found:

        await message.answer(
            "❌ Bu kanal topilmadi."
        )

        return

    save_channels(
        new_channels
    )

    await state.clear()

    await message.answer(
        "✅ Kanal o‘chirildi.",
        reply_markup=main_admin_keyboard()
    )


# =========================================================
# 👤 ADMIN QO‘SHISH
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
        "👤 Yangi adminning Telegram ID raqamini yuboring.\n\n"
        "Masalan:\n"
        "<code>123456789</code>",
        parse_mode="HTML"
    )


@dp.message(
    AdminStates.waiting_admin
)
async def add_admin_process(
    message: Message,
    state: FSMContext
):

    try:

        user_id = int(
            (message.text or "").strip()
        )

    except Exception:

        await message.answer(
            "❌ ID noto‘g‘ri."
        )

        return

    admins = load_admins()

    if user_id == ADMIN_ID:

        await state.clear()

        await message.answer(
            "❌ Bu asosiy adminning ID raqami.",
            reply_markup=main_admin_keyboard()
        )

        return

    if user_id in admins:

        await state.clear()

        await message.answer(
            "❌ Bu foydalanuvchi allaqachon admin.",
            reply_markup=main_admin_keyboard()
        )

        return

    admins.append(
        user_id
    )

    save_admins(
        admins
    )

    await state.clear()

    await message.answer(
        "✅ Admin qo‘shildi.",
        reply_markup=main_admin_keyboard()
    )


# =========================================================
# 🗑 ADMIN O‘CHIRISH
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
            "📭 Hozircha qo‘shimcha adminlar yo‘q.",
            reply_markup=main_admin_keyboard()
        )

        return

    text = (
        "🗑 <b>ADMIN O‘CHIRISH</b>\n\n"
    )

    for admin_id in admins:

        text += (
            f"👤 <code>{admin_id}</code>\n"
        )

    text += (
        "\nO‘chirmoqchi bo‘lgan admin ID raqamini yuboring."
    )

    await state.set_state(
        AdminStates.waiting_delete_admin
    )

    await message.answer(
        text,
        parse_mode="HTML"
    )


@dp.message(
    AdminStates.waiting_delete_admin
)
async def delete_admin_process(
    message: Message,
    state: FSMContext
):

    try:

        user_id = int(
            (message.text or "").strip()
        )

    except Exception:

        await message.answer(
            "❌ ID noto‘g‘ri."
        )

        return

    admins = load_admins()

    if user_id not in admins:

        await message.answer(
            "❌ Bu admin topilmadi."
        )

        return

    admins.remove(
        user_id
    )

    save_admins(
        admins
    )

    await state.clear()

    await message.answer(
        "✅ Admin o‘chirildi.",
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
        "🏆 Yutuq egasining Telegram ID raqamini yuboring.\n\n"
        "Masalan:\n"
        "<code>123456789</code>",
        parse_mode="HTML"
    )


@dp.message(
    AdminStates.waiting_winner
)
async def winner_process(
    message: Message,
    state: FSMContext
):

    try:

        user_id = int(
            (message.text or "").strip()
        )

    except Exception:

        await message.answer(
            "❌ ID noto‘g‘ri."
        )

        return

    save_winner(
        {
            "user_id": user_id
        }
    )

    await state.clear()

    await message.answer(
        "🏆 Yutuq egasi saqlandi.",
        reply_markup=main_admin_keyboard()
    )


# =========================================================
# 🗑 YUTUQ EGASINI O‘CHIRISH
# =========================================================

@dp.message(
    lambda message:
    message.text == "🗑 Yutuq egasini o‘chirish"
    and message.from_user.id == ADMIN_ID
)
async def delete_winner_handler(
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
# 🟢 RANDOM YOQISH
# =========================================================

@dp.message(
    lambda message:
    message.text == "🟢 Randomni yoqish"
    and message.from_user.id == ADMIN_ID
)
async def random_on_handler(
    message: Message,
    state: FSMContext
):

    await state.clear()

    save_random_status(
        {
            "enabled": True
        }
    )

    await message.answer(
        "🟢 Random yutuq egasi rejimi yoqildi.",
        reply_markup=main_admin_keyboard()
    )


# =========================================================
# 🔴 RANDOM O‘CHIRISH
# =========================================================

@dp.message(
    lambda message:
    message.text == "🔴 Randomni o‘chirish"
    and message.from_user.id == ADMIN_ID
)
async def random_off_handler(
    message: Message,
    state: FSMContext
):

    await state.clear()

    save_random_status(
        {
            "enabled": False
        }
    )

    await message.answer(
        "🔴 Random yutuq egasi rejimi o‘chirildi.",
        reply_markup=main_admin_keyboard()
    )


# =========================================================
# 👥 QATNASHUVCHILAR
# =========================================================

@dp.message(
    lambda message:
    message.text == "👥 Qatnashuvchilar"
    and is_admin(message.from_user.id)
)
async def participants_handler(
    message: Message,
    state: FSMContext
):

    await state.clear()

    channels = load_channels()

    requests = load_requests()

    mandatory_channels = []

    for item in channels:

        if item.get("type") != "channel":
            continue

        try:

            channel_id = int(
                item.get("id")
            )

            mandatory_channels.append(
                channel_id
            )

        except Exception:
            pass

    if not mandatory_channels:

        await message.answer(
            "📭 Hozircha majburiy kanallar yo‘q."
        )

        return

    admins = set(
        load_admins()
    )

    participant_count = 0

    for user_id, user_channels in requests.items():

        if not isinstance(
            user_channels,
            list
        ):
            continue

        user_channel_ids = set()

        for channel_id in user_channels:

            try:

                user_channel_ids.add(
                    int(channel_id)
                )

            except Exception:
                pass

        if all(
            channel_id in user_channel_ids
            for channel_id in mandatory_channels
        ):

            try:

                uid = int(
                    user_id
                )

            except Exception:
                continue

            if uid == ADMIN_ID:
                continue

            if uid in admins:
                continue

            participant_count += 1

    await message.answer(
        "👥 <b>QATNASHUVCHILAR</b>\n\n"
        f"🎯 Jami: <b>{participant_count} ta</b>",
        parse_mode="HTML"
    )


# =========================================================
# 🎲 RANDOM YUTUQ EGASI
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

    channels = load_channels()

    users = load_users()

    mandatory_channels = []

    for item in channels:

        if item.get("type") != "channel":
            continue

        try:

            mandatory_channels.append(
                int(item.get("id"))
            )

        except Exception:
            pass

    if not mandatory_channels:

        await message.answer(
            "📭 Hozircha majburiy kanallar yo‘q."
        )

        return

    candidates = []

    for user_id, user in users.items():

        if not isinstance(
            user,
            dict
        ):
            continue

        try:

            uid = int(
                user.get(
                    "id",
                    user_id
                )
            )

        except Exception:

            continue

        if uid == ADMIN_ID:
            continue

        if uid in load_admins():
            continue

        completed = user.get(
            "completed_channels",
            []
        )

        try:

            completed_set = set(
                int(x)
                for x in completed
            )

        except Exception:

            completed_set = set()

        if all(
            channel_id in completed_set
            for channel_id in mandatory_channels
        ):

            candidates.append(
                user
            )

    if not candidates:

        await message.answer(
            "❌ Hozircha barcha shartlarni bajargan "
            "qatnashuvchi yo‘q."
        )

        return

    # COUNTDOWN

    countdown_message = await message.answer(
        "🎲 <b>G‘OLIB ANIQLANMOQDA...</b>\n\n"
        "9",
        parse_mode="HTML"
    )

    for number in range(8, 0, -1):

        await asyncio.sleep(1)

        try:

            await countdown_message.edit_text(
                "🎲 <b>G‘OLIB ANIQLANMOQDA...</b>\n\n"
                f"{number}",
                parse_mode="HTML"
            )

        except Exception:
            pass

    winner = random.choice(
        candidates
    )

    winner_id = winner.get(
        "id"
    )

    first_name = winner.get(
        "first_name",
        ""
    )

    username = winner.get(
        "username",
        ""
    )

    if username:

        winner_text = (
            f"@{username}"
        )

    elif first_name:

        winner_text = first_name

    else:

        winner_text = (
            str(winner_id)
        )

    await countdown_message.edit_text(
        "🎉 <b>G‘OLIB ANIQLANDI!</b>\n\n"
        f"🏆 {winner_text}\n\n"
        f"🆔 <code>{winner_id}</code>",
        parse_mode="HTML"
    )

    save_winner(
        {
            "user_id": winner_id,
            "first_name": first_name,
            "username": username
        }
    )


# =========================================================
# 📨 XABAR YUBORISH
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
        "📨 Yubormoqchi bo‘lgan xabaringizni yuboring.\n\n"
        "Matn, rasm yoki boshqa xabar yuborishingiz mumkin."
    )


@dp.message(
    AdminStates.waiting_broadcast
)
async def broadcast_process(
    message: Message,
    state: FSMContext
):

    users = load_users()

    success = 0

    failed = 0

    for user_id in users.keys():

        try:

            await message.copy_to(
                chat_id=int(user_id)
            )

            success += 1

            await asyncio.sleep(
                0.05
            )

        except Exception:

            failed += 1

    await state.clear()

    await message.answer(
        "📨 <b>XABAR YUBORILDI</b>\n\n"
        f"✅ Yetib bordi: <b>{success}</b>\n"
        f"❌ Xatolik: <b>{failed}</b>",
        parse_mode="HTML",
        reply_markup=main_admin_keyboard()
    )


# =========================================================
# NOTOG‘RI XABAR
# =========================================================

@dp.message()
async def unknown_message_handler(
    message: Message
):

    user_id = message.from_user.id

    if user_id == ADMIN_ID:

        await message.answer(
            "❗ Menyudan kerakli tugmani tanlang.",
            reply_markup=main_admin_keyboard()
        )

    elif user_id in load_admins():

        await message.answer(
            "❗ Menyudan kerakli tugmani tanlang.",
            reply_markup=normal_admin_keyboard()
        )


# =========================================================
# MAIN
# =========================================================

async def main():

    print(
        "BOT ISHGA TUSHDI"
    )

    while True:

        try:

            await dp.start_polling(
                bot,
                allowed_updates=dp.resolve_used_update_types()
            )

        except Exception as e:

            print(
                f"BOT XATOLIK BILAN TO'XTADI: {e}"
            )

            print(
                "5 soniyadan keyin qayta ishga tushadi..."
            )

            await asyncio.sleep(5)


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )
