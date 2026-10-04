"""
utils/qr_decode.py — QR Code decoder (cv2 primary, pyzbar fallback)

ከ awet_online_equib ፕሮጀክት የተወሰደ (ተመሳሳይ አካሄድ)። ብዙ የክፍያ ደረሰኞች
(በተለይ CBE 'thank you' ገጽ) ውስጥ QR code አለ - ብዙ ጊዜ ከ OCR ይልቅ
የበለጠ ትክክለኛ ውጤት ይሰጣል፣ ስለዚህ ስክሪንሾት ስንፈትሽ መጀመሪያ ይህን እንሞክራለን።
"""
from PIL import Image


def decode_qr_from_bytes(image_bytes: bytes) -> str | None:
    """ከ image bytes QR code ያነባል። cv2 ካለ ይጠቀማል፣ ካልሆነ pyzbar fallback።"""
    import io

    # ── Try cv2 (most reliable) ─────────────────────────────
    try:
        import cv2
        import numpy as np
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_cv is not None:
            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector.detectAndDecode(img_cv)
            if data:
                return data
            # Try with upscaled image for small QR codes
            h, w = img_cv.shape[:2]
            if max(h, w) < 800:
                big = cv2.resize(img_cv, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
                data, _, _ = detector.detectAndDecode(big)
                if data:
                    return data
    except ImportError:
        pass
    except Exception:
        pass

    # ── Try pyzbar if installed ──────────────────────────────
    try:
        from pyzbar.pyzbar import decode as pyzbar_decode
        pil_img = Image.open(io.BytesIO(image_bytes))
        decoded = pyzbar_decode(pil_img)
        if decoded:
            return decoded[0].data.decode("utf-8")
    except Exception:
        pass

    return None
