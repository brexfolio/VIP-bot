"""
ethiobank_receipts/selenium_driver.py — Shared 'undetected' Chrome driver.

BOA እና Awash ደረሰኝ ገጾች ሁለቱም JavaScript-rendered SPA ሆነው ተገኝተዋል (ራስ-ሰር HTML
ብቻ ባዶ shell ነው የሚመልሱት)፣ ስለዚህ ሁለቱም Selenium ያስፈልጋቸዋል።

⚠️ ማረጋገጫ (2026-07): BOA's ገጽ static shell (header/footer/QR) ቢጫንም ትክክለኛውን
የደረሰኝ ውሂብ ግን ለ automated browser አይሰጥም (bot-detection) - በተለመደ ስልክ/ኮምፒዩተር
browser ግን ሙሉ በሙሉ ይታያል። ይህ ከ **ትኩስ ትራንዛክሽን ጋር በድጋሚ** ተረጋግጧል (ጊዜው ያለፈበት
transaction ችግር አይደለም)። ተራ Selenium stealth flags (navigator.webdriver
override ወዘተ) በቂ ስላልነበሩ፣ ለዚህ ትክክለኛ ስራ በተለየ ሁኔታ የተሰራውን
`undetected-chromedriver` ላይብረሪ እንጠቀማለን (የ chromedriver's ራሱ automation
"ፊርማ"ዎችን ጭምር ስለሚያጠፋ ከ manual stealth flags የበለጠ ጠንካራ ነው)።

ማሳሰቢያ: pip install undetected-chromedriver ያስፈልጋል (requirements.txt ውስጥ
ተጨምሯል)። Chrome browser ራሱ (ማንኛውም የቅርብ ጊዜ ስሪት) በኮምፒዩተር/ሰርቨሩ ላይ መገጠም አለበት
(chromedriver ራሱ undetected-chromedriver በራስ-ሰር ያወርዳል/ያዘጋጃል)።
"""
import logging

logger = logging.getLogger(__name__)

_driver_holder = {"driver": None}

_REALISTIC_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


def _build_driver():
    import undetected_chromedriver as uc

    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"user-agent={_REALISTIC_UA}")

    # ማሳሰቢያ: undetected-chromedriver ብዙ ጊዜ headless=False (real window) ላይ
    # የተሻለ ውጤት ይሰጣል፣ ምክንያቱም አንዳንድ ገጾች headless modeን ራሱ ስለሚያውቁት። ሰርቨር ላይ
    # GUI ከሌለ (Linux headless VPS) ግን virtual display (xvfb) ያስፈልጋል፤ ካልሆነ
    # ከታች ያለውን headless=True ማድረግ ያስፈልጋል (ግን ማወቂያውን የማለፍ እድሉ ይቀንሳል)።
    driver = uc.Chrome(options=options, headless=False, use_subprocess=True)
    driver.set_page_load_timeout(30)
    return driver


def get_chrome_driver():
    """driver ንቁ መሆኑን አረጋግጦ ይመልሳል፣ ካልሆነ (crashed/stale) አዲስ ይገነባል።"""
    driver = _driver_holder["driver"]
    if driver is not None:
        try:
            _ = driver.title
            return driver
        except Exception:
            logger.warning("shared chrome driver stale/crashed - rebuilding")
            try:
                driver.quit()
            except Exception:
                pass
            _driver_holder["driver"] = None

    driver = _build_driver()
    _driver_holder["driver"] = driver
    return driver


def invalidate_driver():
    """driver ላይ WebDriverException ካጋጠመ ይህን ጠርተህ ቀጣዩ ጥሪ አዲስ driver እንዲገነባ አድርግ።"""
    driver = _driver_holder["driver"]
    if driver is not None:
        try:
            driver.quit()
        except Exception:
            pass
    _driver_holder["driver"] = None
