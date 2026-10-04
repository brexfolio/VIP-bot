import logging
import os
import tempfile
import time

import requests
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from ethiobank_receipts.selenium_driver import get_chrome_driver, invalidate_driver
from ethiobank_receipts.text_extract import LABEL_PATTERNS_AWASH, parse_labeled_text

logger = logging.getLogger(__name__)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
})

_KEYS_OF_INTEREST = [
    "Transaction Time", "Transaction Type", "Amount", "Charge", "VAT",
    "Sender Name", "Sender Account", "Beneficiary name", "Beneficiary Account",
    "Beneficiary Bank", "Reason", "Transaction ID",
]

_READY_MARKERS = ("Beneficiary", "Transaction", "Sender", "Amount")


def _parse_rows(soup: BeautifulSoup, selector: str, label_cell: int, value_cell: int, min_cells: int) -> dict:
    data = {}
    for row in soup.select(selector):
        cells = row.find_all("td")
        if len(cells) >= min_cells:
            key = cells[label_cell].get_text(strip=True).rstrip(":")
            value = cells[value_cell].get_text(strip=True)
            if key:
                data[key] = value
    return data


def _try_plain_http(url: str) -> dict:
    """ፈጣን ሙከራ: ገጹ static/server-rendered ከሆነ (ብዙ ጊዜ አይደለም - ኮዱ Selenium-only
    ላይ እንዳይመሰረት ብቻ ነው) ያለ Chrome/Selenium ማግኘት እንችል እንደሆነ እንሞክራለን።"""
    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()
    except Exception as e:
        logger.info(f"[Awash] plain HTTP attempt failed (expected if page is JS-rendered): {e}")
        return {}

    soup = BeautifulSoup(response.content, "html.parser")
    data = _parse_rows(soup, "table.info-table tr", 0, 2, 3)
    if not data:
        data = _parse_rows(soup, "table tr", 0, 1, 2)
    if not data:
        data = _parse_rows(soup, "table tr", 0, 2, 3)
    if not data:
        full_text = soup.get_text("\n", strip=True)
        data = parse_labeled_text(full_text, LABEL_PATTERNS_AWASH)
    return data


def _wait_for_content(driver):
    try:
        WebDriverWait(driver, 20).until(
            lambda d: any(marker in d.find_element(By.TAG_NAME, "body").text for marker in _READY_MARKERS)
        )
    except TimeoutException:
        try:
            title = driver.title
            snippet = driver.find_element(By.TAG_NAME, "body").text[:500]
        except Exception:
            title, snippet = "?", "?"
        shot_path = None
        try:
            shot_path = os.path.join(tempfile.gettempdir(), f"awash_debug_{int(time.time())}.png")
            driver.save_screenshot(shot_path)
        except Exception:
            pass
        logger.warning(
            f"[Awash] page content not confirmed within 20s wait, proceeding anyway. "
            f"page title={title!r} body snippet={snippet!r} screenshot={shot_path}"
        )


def _try_selenium(url: str, _retry: bool = True) -> dict:
    """⚠️ Awash's awashpay.awashbank.com ገጽ (ልክ እንደ BOA) JS-rendered SPA ሆኖ ሊገኝ
    ይችላል - ስለዚህ plain HTTP ውጤት ካላመጣ Chrome (Selenium) ተጠቅመን JS እናስፈጽማለን።"""
    try:
        driver = get_chrome_driver()
        driver.get(url)
        _wait_for_content(driver)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        data = _parse_rows(soup, "table.info-table tr", 0, 2, 3)
        if not data:
            data = _parse_rows(soup, "table tr", 0, 1, 2)
        if not data:
            data = _parse_rows(soup, "table tr", 0, 2, 3)

        if not data or not (data.get("Beneficiary name") or data.get("Beneficiary Account")):
            body_text = driver.find_element(By.TAG_NAME, "body").text
            text_data = parse_labeled_text(body_text, LABEL_PATTERNS_AWASH)
            for k, v in text_data.items():
                data.setdefault(k, v)

        return data
    except WebDriverException as e:
        logger.error(f"[Awash] WebDriver error: {e}")
        invalidate_driver()
        if _retry:
            return _try_selenium(url, _retry=False)
        return {}


def extract_awash_receipt_data(url):
    data = _try_plain_http(url)

    if not data or not (data.get("Beneficiary name") or data.get("Beneficiary Account")):
        logger.info(f"[Awash] plain HTTP returned no usable data for {url}, falling back to Selenium")
        selenium_data = _try_selenium(url)
        for k, v in selenium_data.items():
            data.setdefault(k, v)

    logger.info(f"[Awash] parsed keys for {url}: {list(data.keys())}")

    return {k: data.get(k) for k in _KEYS_OF_INTEREST}
