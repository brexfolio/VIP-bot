import io
import logging
import re

import pdfplumber
import pytesseract
from PIL import Image

import config

# Windows ላይ Tesseract-OCR ጫነህ ከሆነ፣ .env ውስጥ TESSERACT_CMD ካስቀመጥክ ይጠቀማል
if getattr(config, "TESSERACT_CMD", None):
    pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD


def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    """ከፎቶ/ስክሪንሾት ጽሁፍ በ OCR ያወጣል"""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(image, lang="eng")
    except Exception as e:
        logging.error(f"[OCR] ምስል ማንበብ አልተቻለም: {e}")
        return ""


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """ከ PDF ደረሰኝ ጽሁፍ ያወጣል"""
    try:
        parts = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                parts.append(page.extract_text() or "")
        return "\n".join(parts)
    except Exception as e:
        logging.error(f"[OCR] PDF ማንበብ አልተቻለም: {e}")
        return ""


# ==========================================================================
# ከ OCR/PDF ጽሁፍ ውስጥ የትራንዛክሽን ማጣቀሻ (reference) ቁጥር/ሙሉ ሊንክ ማውጫ
# ==========================================================================
_TELE_CONTEXT_RE = re.compile(
    r'transaction\s*(?:number|id)?\s*(?:is)?\s*[:\-]?\s*([A-Z0-9]{8,14})',
    re.IGNORECASE,
)
_TELE_GENERIC_RE = re.compile(r'\b([A-Z0-9]{9,13})\b')

# ⚠️ ከዚህ ቀደም BOA (Abyssinia) ደግሞ CBE's FT-number regex ይጠቀም ነበር -
# ግን BOA ደረሰኞች "FT..." reference አይጠቀሙም (cs.bankofabyssinia.com/slip/?trx=...
# የተለየ ቅርጽ ነው)፣ ስለዚህ ይህ ስህተት ነበር (የBOA ስክሪንሾቶች ላይ reference ፈጽሞ አይገኝም ነበር)።
_AWASH_URL_RE = re.compile(r'https?://(?:www\.)?awashpay\.awashbank\.com(?::\d+)?/\S+', re.IGNORECASE)
_BOA_URL_RE = re.compile(r'https?://(?:cs\.)?bankofabyssinia\.com/slip/\?trx=\S+', re.IGNORECASE)

# "Transaction ID" ላይ OCR ብዙ ጊዜ ኖይዝ ያስገባል (ለምሳሌ '26061 305) 816394' ለ '260613051816394')፣
# ስለዚህ ከ label በኋላ ያለውን ሙሉ መስመር (ቁጥር+ስፔስ+ስርዓተ-ነጥብ ጭምር) ወስደን ከዚያ ዲጂት ብቻ እናጣራለን።
_AWASH_ID_LABEL_RE = re.compile(r'Transaction\s*ID\s*[:>\-]?\s*([\d\s()]{8,40})', re.IGNORECASE)
_AWASH_GENERIC_RE = re.compile(r'\b(\d{10,20})\b')

# BOA ደረሰኞች ላይ ትክክለኛው label "Transaction Reference" ነው (ከዚህ በፊት የነበረው loose
# regex '(?:transaction|reference)...' የ‘Reference’ የሚለውን label ቃል ራሱን እንደ ኮድ ይይዘው ነበር -
# ለምሳሌ 'Transaction Reference FT26183KJH8T' ላይ 'Reference' ራሱን ይይዝ ነበር)።
_BOA_LABEL_RE = re.compile(r'Transaction\s*Reference\s*[:\-]?\s*([A-Za-z0-9]{6,})', re.IGNORECASE)
_BOA_FT_FALLBACK_RE = re.compile(r'\bFT[A-Z0-9]{6,}\b', re.IGNORECASE)
_LABEL_WORDS = {"reference", "number", "no", "id", "transaction", "transactionid"}


def extract_reference(text: str, method: str):
    """ከ OCR/PDF ጽሁፍ ውስጥ በክፍያ ዘዴ (bank) መሰረት ትክክለኛውን ማጣቀሻ ቁጥር (ወይም ካገኘ ሙሉ
    ሊንክ) ያገኛል። ካላገኘ None ይመልሳል (ተጠቃሚው በእጅ እንዲተይብ ይጠየቃል)።

    CBE ላይ ራሱን የቻለ (የበለጠ ጠንካራ) extract_cbe_tid() ፈንክሽን ይጠቀሙ
    (receipt_checker.py ውስጥ - TID ወይም እውነተኛ ደረሰኝ ሊንክ ይመልሳል) — ይህ ፈንክሽን ለ
    telebirr/awash/boa ብቻ ነው የሚያገለግለው።
    """
    if not text:
        return None

    if method == "telebirr":
        m = _TELE_CONTEXT_RE.search(text)
        if m:
            return m.group(1).upper()
        for tok in _TELE_GENERIC_RE.findall(text):
            tok = tok.upper()
            if tok.startswith("FT") or tok.isdigit() or tok.isalpha():
                continue
            return tok
        return None

    if method == "awash":
        # 1) ሙሉ ደረሰኝ ሊንክ በምስሉ/PDF ውስጥ ከታየ በቀጥታ እንጠቀማለን (reference ከመገመት ይልቅ
        #    ይበልጥ አስተማማኝ ነው)።
        m = _AWASH_URL_RE.search(text)
        if m:
            return m.group(0)
        # 2) "Transaction ID" label ተከትሎ ያለውን ኖይዚ ቁጥር አጽድተን እንወስዳለን
        m = _AWASH_ID_LABEL_RE.search(text)
        if m:
            digits = re.sub(r"\D", "", m.group(1))
            if len(digits) >= 8:
                return digits
        # 3) የመጨረሻ አማራጭ: ጽሁፉ ውስጥ ያለ ማንኛውም 10-20 ዲጂት ቁጥር (ስልክ/ፋክስ ቁጥሮች ላይ
        #    እንዳይሳሳት 'transaction id' label ከሌለ ብቻ እንደ የመጨረሻ አማራጭ ነው የሚያገለግለው)
        m = _AWASH_GENERIC_RE.search(text)
        return m.group(1) if m else None

    if method == "boa":
        m = _BOA_URL_RE.search(text)
        if m:
            return m.group(0)
        # "Transaction Reference" label ብቻ በትክክል እንፈልጋለን (loose label word
        # ('Reference' ራሱ) እንዳይያዝ)
        m = _BOA_LABEL_RE.search(text)
        if m and m.group(1).lower() not in _LABEL_WORDS:
            return m.group(1).upper()
        # fallback: BOA ደረሰኞችም አንዳንዴ FT-style ኮድ ይጠቀማሉ (CBE ዓይነት)
        m = _BOA_FT_FALLBACK_RE.search(text)
        return m.group(0).upper() if m else None

    return None


def extract_reference_from_image_bytes(image_bytes: bytes, method: str):
    """ስክሪንሾት ተቀብሎ ማጣቀሻ ያገኛል፡ CBE ላይ QR code በቅድሚያ ይሞክራል (ብዙ ጊዜ ከOCR ይልቅ
    ይበልጥ ትክክለኛ ውጤት ይሰጣል)፣ ካልተሳካ ወይም ለሌላ payment method OCR ይጠቀማል።"""
    if method == "cbe":
        from receipt_checker import extract_cbe_tid_from_image
        return extract_cbe_tid_from_image(image_bytes)

    text = extract_text_from_image_bytes(image_bytes)
    return extract_reference(text, method)


def extract_reference_from_pdf_bytes(pdf_bytes: bytes, method: str):
    """PDF ደረሰኝ ተቀብሎ ማጣቀሻ ያገኛል።"""
    if method == "cbe":
        from receipt_checker import extract_cbe_tid_from_pdf
        return extract_cbe_tid_from_pdf(pdf_bytes)

    text = extract_text_from_pdf_bytes(pdf_bytes)
    return extract_reference(text, method)


def build_boa_url(reference: str) -> str:
    """reference ቀድሞውኑ ሙሉ ሊንክ ከሆነ (extract_reference URL መልሶ ከሆነ) እንደዛው
    ይመልሳል፤ አለበለዚያ ብቻ ከ trx ID ሊንክ ይገነባል።"""
    if reference and reference.strip().lower().startswith("http"):
        return reference.strip()
    return f"https://cs.bankofabyssinia.com/slip/?trx={reference}"


def build_awash_url(reference: str) -> str:
    if reference and reference.strip().lower().startswith("http"):
        return reference.strip()
    return f"https://awashpay.awashbank.com:8225/-{reference}"
