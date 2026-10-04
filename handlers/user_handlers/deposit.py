from aiogram import Router, F, types
from aiogram.types import (InlineKeyboardMarkup, InlineKeyboardButton,
                            ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import config
from database import get_user_phone, update_user_phone
from utils.emoji import e, e_id

deposit_router = Router()

# Back/Cancel emoji IDs (ከፎቶ)
BACK_ID   = "5967446600652430309"   # ◀️ Back
CANCEL_ID = "5974083768233760323"   # 🔴 Cancel


class PaymentState(StatesGroup):
    waiting_for_payment_method = State()
    waiting_for_tid            = State()
    waiting_for_phone          = State()


# ── helpers ───────────────────────────────────────────────────────────────────
def back_cancel_row(back_cb: str) -> list:
    """Back + Cancel ያለው row."""
    return [
        InlineKeyboardButton(
            text="Back",
            callback_data=back_cb,
            icon_custom_emoji_id=BACK_ID,
        ),
        InlineKeyboardButton(
            text="Cancel Order",
            callback_data="cancel_order",
            icon_custom_emoji_id=CANCEL_ID,
        ),
    ]


# ── Cancel (ማናቸውም ቦታ) ────────────────────────────────────────────────────────
@deposit_router.callback_query(F.data == "cancel_order")
async def cancel_order(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    # ወደ start message ተመለስ
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="VIP ቻናሉን ለመቀላቀል",
            callback_data="buy_vip",
            icon_custom_emoji_id=e_id("vip_door"),
        )]
    ])
    await callback.message.edit_text(
        f'ሰላም {callback.from_user.full_name} {e("wave")}\n\n'
        f'ወደ <b>Wonde {e("smile")}</b> ቦት እንኳን ደህና መጡ።\n\n'
        f'ሁሉንም የቪአይፒ ቻናሎች ለመቀላቀል ከታች ያለውን በተን ይጫኑ።',
        reply_markup=kb,
        parse_mode="HTML",
    )
    await callback.answer()


# ── Step 1: buy_vip → Deposit / Info ─────────────────────────────────────────
@deposit_router.callback_query(F.data == "buy_vip")
async def start_deposit(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Deposit",
            callback_data="make_deposit",
            icon_custom_emoji_id=e_id("wallet"),
        )],
        [InlineKeyboardButton(
            text="ስለ VIP ቻናሎቻችን ለማወቅ",
            callback_data="vip_info",
            icon_custom_emoji_id=e_id("smile"),
        )],
        [InlineKeyboardButton(
            text="Cancel Order",
            callback_data="cancel_order",
            icon_custom_emoji_id=CANCEL_ID,
        )],
    ])
    await callback.message.edit_text(
        f"{e('down_arrow')} የሚፈልጉትን ይምረጡ:",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await callback.answer()


# ── Step 2: Packages ──────────────────────────────────────────────────────────
@deposit_router.callback_query(F.data == "make_deposit")
async def select_package(callback: types.CallbackQuery):
    pkg_buttons = [
        [InlineKeyboardButton(
            text=v["label"],
            callback_data=f"pkg_{k}",
            icon_custom_emoji_id=config.PKG_CHECK_EMOJI_ID,
        )]
        for k, v in config.PACKAGES.items()
    ]
    pkg_buttons.append(back_cancel_row("buy_vip"))

    await callback.message.edit_text(
        f"{e('dollar')} ከታች ከተዘረዘሩት ጥቅሎች የሚፈልጉትን ይምረጡ",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=pkg_buttons),
        parse_mode="HTML",
    )
    await callback.answer()


# ── Step 3: ጥቅል ሲመረጥ → Payment method ──────────────────────────────────────
@deposit_router.callback_query(F.data.startswith("pkg_"))
async def handle_package_selection(callback: types.CallbackQuery, state: FSMContext):
    package_key = callback.data.replace("pkg_", "")
    user_id     = callback.from_user.id
    await state.update_data(selected_package=package_key)

    user_phone = await get_user_phone(user_id)

    if user_phone:
        await show_payment_method(callback.message, state)
    else:
        # ስልክ ቁጥር ስለሌለ — phone keyboard ብቻ (edit አይደለም)
        phone_kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📲 ስልክ ቁጥሬን ላክ", request_contact=True)]],
            resize_keyboard=True, one_time_keyboard=True,
        )
        await callback.message.answer(
            "ለማረጋገጫ እንዲረዳን ስልክ ቁጥርዎን ይላኩ።",
            reply_markup=phone_kb,
        )
        await state.set_state(PaymentState.waiting_for_phone)
    await callback.answer()


# ── ስልክ ሲቀበል ─────────────────────────────────────────────────────────────────
@deposit_router.message(PaymentState.waiting_for_phone, F.contact)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    await update_user_phone(message.from_user.id, phone)
    await message.answer("✅ ስልክዎ ተመዝግቧል!", reply_markup=ReplyKeyboardRemove())
    # ሰሌዳ (dummy message) ፈጥሮ payment method ያሳያል
    msg = await message.answer("...")
    await show_payment_method(msg, state)


# ── Step 4: Payment method ────────────────────────────────────────────────────
async def show_payment_method(message: types.Message, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Telebirr",
            callback_data="pay_telebirr",
            icon_custom_emoji_id=e_id("telebirr"),
        )],
        [InlineKeyboardButton(
            text="CBE Birr",
            callback_data="pay_cbe",
            icon_custom_emoji_id=e_id("cbe"),
        )],
        [InlineKeyboardButton(
            text="Bank of Abyssinia",
            callback_data="pay_boa",
            icon_custom_emoji_id=e_id("abyssinia"),
        )],
        [InlineKeyboardButton(
            text="Awash Bank",
            callback_data="pay_awash",
        )],
        back_cancel_row("make_deposit"),
    ])
    await message.edit_text(
        f"{e('wallet')} የክፍያ ዘዴ ይምረጡ:",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await state.set_state(PaymentState.waiting_for_payment_method)


_METHOD_MAP = {
    "pay_telebirr": "telebirr",
    "pay_cbe":      "cbe",
    "pay_boa":      "boa",
    "pay_awash":    "awash",
}

# Back to payment method (package ሲመረጥ ቀደም ሲል ስለሆነ state ያስፈልጋል)
@deposit_router.callback_query(F.data == "back_to_method")
async def back_to_method(callback: types.CallbackQuery, state: FSMContext):
    await show_payment_method(callback.message, state)
    await callback.answer()


@deposit_router.callback_query(
    PaymentState.waiting_for_payment_method,
    F.data.in_(list(_METHOD_MAP.keys()))
)
async def handle_payment_method(callback: types.CallbackQuery, state: FSMContext):
    method = _METHOD_MAP[callback.data]
    await state.update_data(payment_method=method)
    package_key = (await state.get_data()).get("selected_package")
    await show_payment_details(callback.message, state, package_key, method)
    await callback.answer()


# ── Step 5: Payment details ───────────────────────────────────────────────────
async def show_payment_details(message: types.Message, state: FSMContext,
                                package_key: str, method: str):
    pkg   = config.PACKAGES[package_key]
    price = pkg["price"]

    if method == "cbe":
        header = f"{e('cbe')} <b>CBE Birr</b>"
        acct   = f"Account: <code>{config.CBE_ACCOUNT}</code>"
        tip    = (f"{e('paid_check')} ከከፈሉ በኋላ CBE app ደረሰኝ ሊንክ ወይም screenshot ይላኩ\n"
                  f"ምሳሌ: <code>https://mbreciept.cbe.com.et/v2-AbCdXyz</code>")
        back_cb = "pay_cbe"
    elif method == "boa":
        header  = f"{e('abyssinia')} <b>Bank of Abyssinia</b>"
        acct    = f"Account: <code>{config.ABYSSINIA_ACCOUNT}</code>"
        tip     = (f"{e('paid_check')} ከከፈሉ በኋላ ደረሰኝ ሊንክ ወይም screenshot ይላኩ\n"
                   f"ምሳሌ: <code>https://cs.bankofabyssinia.com/slip/?trx=...</code>")
        back_cb = "pay_boa"
    elif method == "awash":
        header  = "🏦 <b>Awash Bank</b>"
        acct    = f"Account: <code>{config.AWASH_ACCOUNT}</code>"
        tip     = (f"{e('paid_check')} ከከፈሉ በኋላ ደረሰኝ ሊንክ ወይም screenshot ይላኩ\n"
                   f"ምሳሌ: <code>https://awashpay.awashbank.com:8225/...</code>")
        back_cb = "pay_awash"
    else:
        header  = f"{e('telebirr')} <b>Telebirr</b>"
        acct    = f"ቁጥር: <code>{config.TELEBIRR_NUMBER}</code>"
        tip     = (f"{e('paid_check')} ከከፈሉ በኋላ TID ቁጥሩን ወይም screenshot ለቦቱ ይላኩ\n"
                   f"ምሳሌ TID: <code>CD68C1BD7V</code>")
        back_cb = "pay_telebirr"

    text = (
        f"{header}\n\n"
        f"{acct}\n"
        f"ስም ➡️ <b>{config.ACCOUNT_NAME}</b>\n\n"
        f"{e('dollar')} ሊከፍሉ ያለው: <b>{price} ብር</b>\n\n"
        f"{tip}\n\n"
        f"{e('bell')} ለተጨማሪ መረጃ ➡️ {config.SUPPORT_CONTACT} ያናግሩን።"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="I have paid ✅",
            callback_data="confirm_payment",
            icon_custom_emoji_id=e_id("paid_check"),
        )],
        back_cancel_row("back_to_method"),
    ])
    await message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await state.set_state(PaymentState.waiting_for_payment_method)


# ── Step 6: Confirm → TID input ──────────────────────────────────────────────
@deposit_router.callback_query(F.data == "confirm_payment")
async def confirm_payment(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("selected_package"):
        await callback.answer("⚠️ ጥቅል ይምረጡ!", show_alert=True)
        return

    method = data.get("payment_method", "telebirr")
    prompts = {
        "cbe":   (f"{e('cbe')} CBE ደረሰኝ ሊንክ ወይም screenshot ይላኩ:\n"
                  "<code>https://mbreciept.cbe.com.et/v2-...</code>"),
        "boa":   (f"{e('abyssinia')} Abyssinia ደረሰኝ ሊንክ ወይም screenshot ይላኩ:\n"
                  "<code>https://cs.bankofabyssinia.com/slip/?trx=...</code>"),
        "awash": ("🏦 Awash ደረሰኝ ሊንክ ወይም screenshot ይላኩ:\n"
                  "<code>https://awashpay.awashbank.com:8225/...</code>"),
    }
    prompt = prompts.get(
        method,
        f"{e('telebirr')} Telebirr TID ቁጥሩን ወይም screenshot ይላኩ:\n"
        "ምሳሌ: <code>CD68C1BD7V</code>"
    )
    # edit ሆኖ ይቀይርና back button ያለው prompt ያሳያል
    kb = InlineKeyboardMarkup(inline_keyboard=[
        back_cancel_row("back_to_method"),
    ])
    await callback.message.edit_text(
        prompt,
        reply_markup=kb,
        parse_mode="HTML",
    )
    await state.set_state(PaymentState.waiting_for_tid)
    await callback.answer()
