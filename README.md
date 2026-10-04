# mule_vip_bot

## Setup

```
pip install -r requirements.txt
playwright install chromium   # required for CBE receipt verification
```

## CBE payment verification (⚠️ changed)

CBE receipts are now verified by rendering the customer's **actual receipt
link** (`mbreciept.cbe.com.et/...`, found in their SMS or receipt QR code)
with a headless Chromium browser (Playwright) and reading the official page —
not by downloading a PDF from `apps.cbe.com.et:100` (that endpoint is dead)
and not by trusting anything typed/OCR'd/QR-decoded from the customer as
financial fact. Practical implications:

- A bare transaction ID (e.g. `FT2312345678`) typed with no link is no
  longer enough to auto-verify — CBE has no way to open a receipt from a
  bare TID alone. Customers must send either the full confirmation SMS
  (with the link) or a screenshot/PDF with a scannable QR code.
- See `receipt_checker.py` (`verify_cbe_payment`) for the implementation.
