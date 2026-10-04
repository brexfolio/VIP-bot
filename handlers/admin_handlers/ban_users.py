import aiosqlite
from aiogram import Router, F, types
from utils.emoji import e
import config

ban_users_router = Router()


@ban_users_router.message(F.text == "🚫 Ban Users List")
async def get_banned_list(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        return
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT user_id, full_name, expiry_date FROM users "
            "WHERE is_vip=0 AND expiry_date IS NOT NULL ORDER BY expiry_date DESC LIMIT 100"
        ) as cur:
            rows = [dict(r) for r in await cur.fetchall()]

    if not rows:
        await message.answer(f"{e('warning')} ጊዜ ያለቀባቸው ተጠቃሚዎች አልተገኙም።", parse_mode="HTML")
        return

    header = f"{e('shield')} <b>Expired Users</b>\n\n<pre>{'No':<3} {'ስም':<14} {'ያለቀ':<10}\n{'─'*30}\n"
    body = ""
    for idx, r in enumerate(rows, 1):
        name    = "".join(c if ord(c) < 128 else "?" for c in (r.get("full_name") or ""))[:12]
        expired = (r.get("expiry_date") or "")[:10]
        body   += f"{idx:<3} {name:<14} {expired:<10}\n"

    await message.answer(header + body + "</pre>", parse_mode="HTML")
