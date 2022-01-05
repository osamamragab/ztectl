import os
import sys
import csv
import re
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver, WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support.expected_conditions import presence_of_element_located


DEV_MODE = os.getenv("DEV_MODE") == "1"
ZTE_DOMAIN = os.getenv("ZTE_DOMAIN", "http://192.168.1.1")
ZTE_USERNAME = os.getenv("ZTE_USERNAME", "admin")
ZTE_PASSWORD = os.getenv("ZTE_PASSWORD", "password")
ZTE_MACS_FILE = os.getenv("ZTE_MACS_FILE", "macs.csv")


def panic(msg: str):
    print("error:", msg, file=sys.stderr)
    sys.exit(1)


def checkmac(mac: str) -> bool:
    return bool(
        re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac.lower())
    )


def allowmacaddr(driver: WebDriver, addr: str):
    for i, a in enumerate(addr.split(":")):
        driver.find_element((By.ID, f"mac{i+1}")).send_keys(a)
        driver.find_element((By.ID, "add")).click()


def hasmacaddr(driver: WebDriver, addr: str) -> WebElement | None:
    table: WebElement | None = driver.find_element((By.ID, "MAC_table"))
    if not table:
        return None
    macs: list[WebElement] = table.find_elements(
        (By.CSS_SELECTOR, "input[id*='MACAddress']")
    )
    if not macs:
        return None
    for m in macs:
        if m.get_attribute("value") == addr:
            return m
    return None


def blockmacaddr(driver: WebDriver, addr: str):
    e: WebElement | None = hasmacaddr(driver, addr)
    if not e:
        return
    eid: str = e.get_attribute("id")
    if not eid.startswith("Line_"):
        panic("wtf")
    driver.find_element((By.ID, f"Btn_Delete{eid[5]}")).click()


if ZTE_PASSWORD == "":
    panic("password is required")


def main():
    if len(sys.argv) > 2:
        macmode = sys.argv[1].strip().lower()
        macaddr = sys.argv[2].strip().lower()
        if macmode not in ("add", "allow", "rm", "remove", "block", "toggle"):
            panic(f"invalid mode {sys.argv[1]}")
    else:
        panic(f"usage: {sys.argv[0]} <mode> <macaddr>")

    if not checkmac(macaddr):
        if ZTE_MACS_FILE != "" and os.path.exists(ZTE_MACS_FILE):
            with open(ZTE_MACS_FILE) as file:
                reader = csv.reader(file, delimiter=",")
                for row in reader:
                    if len(row) != 2:  # skip invalid rows
                        continue
                    if not checkmac(row[1]):
                        print(
                            f"warning: invalid mac for {row[0]} ({row[1]})",
                            file=sys.stderr,
                        )
                        continue
                    if macaddr == row[0].lower():
                        macaddr = row[1].lower()
                        break
        else:
            panic("the given mac address is not valid")

    opts = webdriver.FirefoxOptions()
    opts.headless = not DEV_MODE

    with webdriver.Firefox(options=opts, service_log_path="/dev/null") as driver:
        driver.get(ZTE_DOMAIN)
        driver.switch_to.frame("mainFrame")

        wait = WebDriverWait(driver, 10)
        wait.until(presence_of_element_located((By.ID, "mmNet"))).click()
        wait.until(presence_of_element_located((By.ID, "smWLAN"))).click()
        wait.until(presence_of_element_located((By.ID, "ssmMacFilter"))).click()

        Select(
            wait.until(presence_of_element_located((By.ID, "Frm_Mode")))
        ).select_by_value("Allow")

        if macmode in ("add", "allow"):
            allowmacaddr(driver, macaddr)
        elif macmode in ("rm", "remove", "block"):
            blockmacaddr(driver, macaddr)
        elif macmode == "toggle":
            if hasmacaddr(driver, macaddr):
                blockmacaddr(driver, macaddr)
            else:
                allowmacaddr(driver, macaddr)


if __name__ == "__main__":
    main()
