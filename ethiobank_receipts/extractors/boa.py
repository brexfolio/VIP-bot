import logging
import os
import tempfile
import time

from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from ethiobank_receipts.selenium_driver import get_chrome_driver, invalidate_driver
from ethiobank_receipts.text_extract import LABEL_PATTERNS_BOA, parse_labeled_text

logger = logging.getLogger(__name__)

# ⚠️ ማረጋገጫ (2026-07): cs.bankofabyssinia.com/slip ገጹ ራሱ ባዶ HTML shell ብቻ ነው
# የሚመልሰው (title ብቻ ያለው) - ትክክለኛው የደረሰኝ ይዘት ሙሉ በሙሉ በ JavaScript (SPA) ነው
# የሚሞላው። ስለዚህ የተወሰነ <table> tag እንደሚኖር መገመት አደገኛ ነው። ይልቁንም ገጹ ላይ
# በተጨባጭ የተጻፈውን ጽሁፍ (ምንም tag ይሁን ምን) እናነብና በ label ስም regex እናወጣለን።

_READY_MARKERS = ("Receiver", "Transaction", "Source Account", "Reference")


def _parse_table(page_source: str) -> dict:
    soup = BeautifulSoup(page_source, "html.parser")
    data = {}
    for row in soup.select("table tr"):
        cells = row.find_all("td")
        if len(cells) == 2:
            key = cells[0].get_text(strip=True).rstrip(":")
            value = cells[1].get_text(strip=True)
            data[key] = value
    return data


def _wait_for_content(driver):
    try:
        WebDriverWait(driver, 20).until(
            lambda d: any(marker in d.find_element(By.TAG_NAME, "body").text for marker in _READY_MARKERS)
        )
    except TimeoutException:
        # ⚠️ DIAGNOSTIC: ገጹ ላይ በትክክል ምን እንደሚታይ (bot-block ገጽ? "transaction not
        # found"? ወይስ ገና እየጫነ ነው?) እናትም - ያለዚህ በጭፍን መገመት ብቻ ነው የምንችለው።
        try:
            title = driver.title
            snippet = driver.find_element(By.TAG_NAME, "body").text[:500]
        except Exception:
            title, snippet = "?", "?"
        shot_path = None
        try:
            shot_path = os.path.join(tempfile.gettempdir(), f"boa_debug_{int(time.time())}.png")
            driver.save_screenshot(shot_path)
        except Exception:
            pass
        logger.warning(
            f"[BOA] page content not confirmed within 20s wait, proceeding anyway. "
            f"page title={title!r} body snippet={snippet!r} screenshot={shot_path}"
        )
        time.sleep(2)


def extract_boa_receipt_data(url, _retry: bool = True):
    try:
        driver = get_chrome_driver()
        driver.get(url)
        _wait_for_content(driver)

        data = _parse_table(driver.page_source)

        if not data or not (data.get("Receiver's Account") or data.get("Receiver's Name")):
            body_text = driver.find_element(By.TAG_NAME, "body").text
            text_data = parse_labeled_text(body_text, LABEL_PATTERNS_BOA)
            for k, v in text_data.items():
                data.setdefault(k, v)

        if not data and _retry:
            logger.warning(f"[BOA] empty parse on first try for {url}, retrying once")
            time.sleep(3)
            body_text = driver.find_element(By.TAG_NAME, "body").text
            data = parse_labeled_text(body_text, LABEL_PATTERNS_BOA) or _parse_table(driver.page_source)

    except WebDriverException as e:
        # ⚠️ FIX: ከዚህ በፊት get_chrome_driver() ከ try block ውጪ ስለነበር (Chrome
        # ማስጀመር ራሱ ቢወድቅ - ለምሳሌ 'session not created: Chrome instance exited'
        # የሚል አልፎ አልፎ የሚያጋጥም ችግር) ወደ ላይ ወጥቶ generic '❌ WebDriver ችግር' መልእክት
        # ብቻ ይሰጥ ነበር። አሁን ይህ ራሱ በራስ-ሰር ድጋሚ ይሞክራል።
        logger.error(f"[BOA] WebDriver error: {e}")
        invalidate_driver()
        if _retry:
            return extract_boa_receipt_data(url, _retry=False)
        raise

    logger.info(f"[BOA] parsed keys for {url}: {list(data.keys())}")

    return {
        "Source Account": data.get("Source Account"),
        "Source Account Name": data.get("Source Account Name"),
        "Receiver's Account": data.get("Receiver's Account"),
        "Receiver's Name": data.get("Receiver's Name"),
        "Transferred Amount": data.get("Transferred amount") or data.get("Transferred Amount"),
        "Service Charge": data.get("Service Charge"),
        "VAT": data.get("VAT (15%)"),
        "Total Amount": data.get("Total Amount"),
        "Transaction Type": data.get("Transaction Type"),
        "Transaction Date": data.get("Transaction Date"),
        "Transaction Reference": data.get("Transaction Reference"),
        "Narrative": data.get("Narrative"),
    }
