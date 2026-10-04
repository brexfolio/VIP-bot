import aiosqlite
from aiogram import Router, F, types
from utils.emoji import e
import config

payment_info_router = Router()


@payment_info_router.message(F.text == "💰 Payment Info")
async def show_payment_info(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        return

    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM payments ORDER BY id ASC") as cur:
            payments = [dict(r) for r in await cur.fetchall()]
        async with db.execute("SELECT COALESCE(SUM(amount), 0) FROM payments") as cur:
            total = float((await cur.fetchone())[0])

    if not payments:
        await message.answer(f"{e('bell')} እስካሁን ምንም ክፍያ አልተመዘገበም።", parse_mode="HTML")
        return

    title = f"{e('msg_amount')} <b>PaymentInfo</b>\n\n"

    header = (
        f"All Paid Amount: {total:.1f} Birr\n\n"
        "| No | Name     | Phone      | TID         | amount |\n"
        "|----|----------|------------|-------------|--------|\n"
    )

    rows = ""
    for i, p in enumerate(payments, 1):
        name  = "".join(c if ord(c) < 128 else "?" for c in (p.get("payer_name") or "N/A"))[:8]
        phone = (p.get("phone") or "N/A")[-10:]
        tid   = (p.get("transaction_id") or "N/A")[:11]
        amt   = f"{p.get('amount', 0):.1f}"
        rows += f"| {i:<2} | {name:<8} | {phone:<10} | {tid:<11} | {amt:<6} |\n"

    full = title + f"<pre>{header}{rows}</pre>"

    if len(full) <= 4096:
        await message.answer(full, parse_mode="HTML")
    else:
        await message.answer(title + f"<pre>{header}</pre>", parse_mode="HTML")
        chunk = ""
        for line in rows.splitlines(keepends=True):
            if len(chunk) + len(line) > 3800:
                await message.answer(f"<pre>{chunk}</pre>", parse_mode="HTML")
                chunk = ""
            chunk += line
        if chunk:
            await message.answer(f"<pre>{chunk}</pre>", parse_mode="HTML")
