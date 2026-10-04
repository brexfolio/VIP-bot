from aiogram import Router, F, types
from utils.emoji import e

info_router = Router()


@info_router.callback_query(F.data == "vip_info")
async def show_vip_info(callback: types.CallbackQuery):
    text = (
        f"{e('smile')} <b>ስለ VIP ቻናሎቻችን ዝርዝር መረጃ</b>\n\n"
        f"{e('green_check')} በአንድ ክፍያ 49 ቻናሎችን ይቀላቀላሉ\n"
        f"{e('green_check')} ፊልሞቹ ጥራት ያላቸው፣ በየቀኑ ይለቀቃሉ\n"
        f"{e('warning')} ጊዜዎ ሊያልቅ 1 ቀን ሲቀር ቦቱ ያስጠነቅቃል\n"
        f"{e('trash')} ጊዜዎ ሲያልቅ ከቻናሎቹ ይወጣሉ\n\n"
        f"{e('arrow_right')} ለማስጠናቀቅ /start ብለው ክፍያ ይፈጽሙ።"
    )
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()
