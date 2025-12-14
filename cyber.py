import csv
import os
import re
import sys
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


# ---------- SETTINGS ----------
HEADLESS = True          # Set False if you want to SEE the browser
WAIT_SECONDS = 6         # Basic wait for page to load
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/120.0.0.0 Safari/537.36")
# -----------------------------


def ensure_dirs():
    os.makedirs("screenshots", exist_ok=True)
    os.makedirs("data", exist_ok=True)


def load_products(csv_path="products.csv"):
    products = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("name") or "").strip()
            url = (row.get("url") or "").strip()
            target = (row.get("target_price") or "").strip()

            if not url:
                continue

            target_price = None
            if target:
                try:
                    target_price = float(target)
                except ValueError:
                    target_price = None

            products.append({"name": name or "Unnamed", "url": url, "target_price": target_price})
    return products


def make_driver():
    options = Options()
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument(f"--user-agent={USER_AGENT}")
    options.add_argument("--window-size=1400,900")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def clean_price(text: str):
    """
    Extract float from text like "$1,299.99" or "1.299,99 €"
    This is best-effort; Amazon varies by country/locale.
    """
    if not text:
        return None

    # keep digits, comma, dot
    t = re.sub(r"[^\d,\.]", "", text).strip()
    if not t:
        return None

    # Strategy:
    # - If both ',' and '.' exist: assume thousand separators; decide by last separator.
    # - If only ',' exists: treat ',' as decimal if it looks like decimals.
    # - Else '.' decimal.
    if "," in t and "." in t:
        # decimal separator likely the last one
        if t.rfind(",") > t.rfind("."):
            # comma decimal -> remove dots (thousands)
            t = t.replace(".", "").replace(",", ".")
        else:
            # dot decimal -> remove commas (thousands)
            t = t.replace(",", "")
    elif "," in t and "." not in t:
        # could be decimal or thousands. If exactly 2 digits after last comma => decimal
        parts = t.split(",")
        if len(parts[-1]) == 2:
            t = t.replace(",", ".")
        else:
            t = t.replace(",", "")
    else:
        # only dots or only digits
        # remove thousands separators like 1.299.999 -> keep last dot as decimal only if 2 digits after it
        if t.count(".") >= 2:
            parts = t.split(".")
            if len(parts[-1]) == 2:
                t = "".join(parts[:-1]) + "." + parts[-1]
            else:
                t = t.replace(".", "")

    try:
        return float(t)
    except ValueError:
        return None


def try_get_text(driver, by, selector):
    try:
        el = driver.find_element(by, selector)
        return el.text.strip()
    except Exception:
        return ""


def get_amazon_title_and_price(driver):
    # Title
    title = try_get_text(driver, By.ID, "productTitle")

    # Price can appear in different places
    candidates = [
        (By.CSS_SELECTOR, "span.a-price > span.a-offscreen"),  # common
        (By.ID, "priceblock_ourprice"),
        (By.ID, "priceblock_dealprice"),
        (By.ID, "priceblock_saleprice"),
        (By.CSS_SELECTOR, "#corePriceDisplay_desktop_feature_div span.a-price span.a-offscreen"),
    ]

    price_text = ""
    for by, sel in candidates:
        txt = try_get_text(driver, by, sel)
        if txt:
            price_text = txt
            break

    price = clean_price(price_text)

    return title, price, price_text


def save_history(row, out_csv="data/price_history.csv"):
    file_exists = os.path.exists(out_csv)
    with open(out_csv, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["timestamp", "name", "url", "title", "price", "raw_price_text", "target_price", "status"]
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main():
    ensure_dirs()

    if not os.path.exists("products.csv"):
        print("ERROR: products.csv not found. Create it first.")
        sys.exit(1)

    products = load_products("products.csv")
    if not products:
        print("ERROR: No products found in products.csv")
        sys.exit(1)

    driver = make_driver()

    try:
        for idx, p in enumerate(products, start=1):
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "_", p["name"])[:60]
            screenshot_path = f"screenshots/{idx:02d}_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

            print(f"\n[{idx}/{len(products)}] Opening: {p['url']}")
            driver.get(p["url"])
            time.sleep(WAIT_SECONDS)

            # Save screenshot no matter what (useful for your report)
            driver.save_screenshot(screenshot_path)
            print(f"  Screenshot saved: {screenshot_path}")

            title, price, raw_price_text = get_amazon_title_and_price(driver)
            print(f"  Title: {title[:80]}{'...' if len(title) > 80 else ''}")
            print(f"  Raw price: {raw_price_text}")
            print(f"  Parsed price: {price}")

            status = "OK"
            if price is None:
                status = "PRICE_NOT_FOUND (possible CAPTCHA/blocked or different layout)"
            elif p["target_price"] is not None and price <= p["target_price"]:
                status = f"TARGET_REACHED (<= {p['target_price']})"

            save_history({
                "timestamp": ts,
                "name": p["name"],
                "url": p["url"],
                "title": title,
                "price": price if price is not None else "",
                "raw_price_text": raw_price_text,
                "target_price": p["target_price"] if p["target_price"] is not None else "",
                "status": status
            })

            print(f"  Status: {status}")

    finally:
        driver.quit()
        print("\nDone. Check data/price_history.csv and screenshots/ folder.")


if __name__ == "__main__":
    main()
