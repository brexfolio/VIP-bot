"""
⚠️ DEPRECATED — apps.cbe.com.et:100 (ይህ ፋይል ይጠቀምበት የነበረው endpoint) ጭራሽ
ደርሶበታል/ቆሟል፣ እናም CBE ጭራሽ ባዶ FT number+account digit ብቻ ተሰጥቶ ደረሰኝ URL
የመገንባት አገልግሎት አልነበረውም/የለውም (ያ ራሱ ስህተት ግምት ነበር)።

CBE ደረሰኝ ማረጋገጫ ሙሉ ለሙሉ ወደ `receipt_checker.verify_cbe_payment()` ተዛውሯል፣
እሱም ተጠቃሚው ከላከው SMS/screenshot/QR ውስጥ የተገኘውን **እውነተኛ** CBE ደረሰኝ ሊንክ
(mbreciept.cbe.com.et/... ወይም ሌላ *.cbe.com.et ሊንክ) Playwright headless
browser ተጠቅሞ ራንደር አድርጎ ያነባል (ልክ እንደ paste-to-verify / awet_online_equib
cbe-verifier አካሄድ) — ከዚህ በታች ያሉት ፈንክሽኖች ተጠርተው ከተጠቀሙ ግልፅ ስህተት ብቻ
ይመልሳሉ፣ ጸጥ ብለው በሞተ endpoint ላይ አይሞክሩም/አያሳስቱም።
"""


def extract_cbe_receipt_info(url):
    raise RuntimeError(
        "extract_cbe_receipt_info() ተነስቷል — apps.cbe.com.et:100 PDF አካሄድ "
        "ጭራሽ ቆሟል። ከ receipt_checker.py 'await verify_cbe_payment(user_input, "
        "expected_amount)' ተጠቀም (ወይም ራንደር-ብቻ ለሚያስፈልግህ "
        "receipt_checker._fetch_and_parse_cbe(url, timeout_ms))።"
    )


def extract_cbe_receipt_info_from_ft(ft_number: str, account_last8_or_full: str):
    raise RuntimeError(
        "extract_cbe_receipt_info_from_ft() ተነስቷል — CBE ባዶ FT number+account "
        "digit ብቻ ተሰጥቶ ደረሰኝ URL የመገንባት አገልግሎት የለውም (ያ ግምት ራሱ ስህተት ነበር)። "
        "ራንደር ለማድረግ ተጠቃሚው ከላከው ጽሁፍ/QR/screenshot ውስጥ የተገኘ እውነተኛ ደረሰኝ "
        "ሊንክ ያስፈልጋል — receipt_checker.verify_cbe_payment() ይመልከቱ።"
    )
