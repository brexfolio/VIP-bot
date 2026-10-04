"""
ethiobank_receipts/text_extract.py — Tag-independent label:value ጽሁፍ ማውጫ

BOA እና Awash ገጾች ሁለቱም JS-rendered ናቸው፣ እና የ HTML DOM structure (table ወይም
div/flex) ወደፊት ሊቀየር ስለሚችል በ tag ላይ ጥገኛ ከመሆን ይልቅ driver.page render
ካደረገ በኋላ ያለውን ንፁህ ጽሁፍ (body text) ላይ label-based regex እንጠቀማለን - ይሄ
ከ DOM structure ለውጥ የበለጠ ደህንነቱ የተጠበቀ ነው።
"""
import re

LABEL_PATTERNS_BOA = {
    "Source Account": re.compile(r"Source\s*Account\s*\n?\s*([\d*]{4,})", re.IGNORECASE),
    "Source Account Name": re.compile(r"Source\s*Account\s*Name\s*\n?\s*([A-Za-z .]+)", re.IGNORECASE),
    "Receiver's Account": re.compile(r"Receiver'?s?\s*Account\s*\n?\s*([\d*]{4,})", re.IGNORECASE),
    "Receiver's Name": re.compile(r"Receiver'?s?\s*Name\s*\n?\s*([A-Za-z .]+)", re.IGNORECASE),
    "Transferred Amount": re.compile(r"Transferred\s*[Aa]mount\s*\n?\s*(?:ETB)?\s*([\d,.]+)", re.IGNORECASE),
    "Transaction Type": re.compile(r"Transaction\s*Type\s*\n?\s*([A-Za-z ]+)", re.IGNORECASE),
    "Transaction Date": re.compile(r"Transaction\s*Date\s*\n?\s*([\d/:\s]+)", re.IGNORECASE),
    "Transaction Reference": re.compile(r"Transaction\s*Reference\s*\n?\s*([A-Za-z0-9]{6,})", re.IGNORECASE),
    "Narrative": re.compile(r"Narrative\s*\n?\s*(.+)", re.IGNORECASE),
}

LABEL_PATTERNS_AWASH = {
    "Beneficiary name": re.compile(r"(?:Beneficiary|Receiver)\s*[Nn]ame\s*\n?\s*[:\-]?\s*([A-Za-z .]+)", re.IGNORECASE),
    "Beneficiary Account": re.compile(r"(?:Beneficiary|Receiver)\s*Account\s*\n?\s*[:\-]?\s*([\d*/A-Za-z]{4,})", re.IGNORECASE),
    "Sender Name": re.compile(r"Sender\s*[Nn]ame\s*\n?\s*[:\-]?\s*([A-Za-z .]+)", re.IGNORECASE),
    "Sender Account": re.compile(r"Sender\s*Account\s*\n?\s*[:\-]?\s*([\d*/A-Za-z]{4,})", re.IGNORECASE),
    "Amount": re.compile(r"\bAmount\s*\n?\s*[:\-]?\s*([\d,.]+)\s*ETB", re.IGNORECASE),
    "Transaction Time": re.compile(r"Transaction\s*(?:Time|Date)\s*\n?\s*[:\-]?\s*([\d/:\-\s]+)", re.IGNORECASE),
    "Transaction Type": re.compile(r"Transaction\s*Type\s*\n?\s*[:\-]?\s*([A-Za-z ]+)", re.IGNORECASE),
    "Transaction ID": re.compile(r"Transaction\s*ID\s*\n?\s*[:>\-]?\s*([\d]{6,})", re.IGNORECASE),
    "Reason": re.compile(r"Reason\s*\n?\s*[:\-]?\s*([A-Za-z .]+)", re.IGNORECASE),
}


def parse_labeled_text(body_text: str, patterns: dict) -> dict:
    """body_text ውስጥ (ምንም HTML tag ግድ ሳይል) ከ patterns ጋር የሚዛመዱትን label:value ጥንዶች ያወጣል።"""
    data = {}
    for key, pattern in patterns.items():
        m = pattern.search(body_text)
        if m:
            data[key] = m.group(1).strip()
    return data
