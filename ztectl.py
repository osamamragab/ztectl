import os
import sys
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support.expected_conditions import presence_of_element_located


DEV_MODE = os.getenv("DEV_MODE", "0") == "1"
ZTE_DOMAIN = os.getenv("ZTE_DOMAIN", "http://192.168.1.1")
ZTE_USERNAME = os.getenv("ZTE_USERNAME", "admin")
ZTE_PASSWORD = os.getenv("ZTE_PASSWORD", "")
ZTE_MACS_FILE = os.getenv("ZTE_MACS_FILE", "macs.csv")


def panic(msg: str):
    print("error:", msg, file=sys.stderr)
    sys.exit(1)


if ZTE_PASSWORD == "":
    panic("password is required")


macaddr = sys.argv[1] if len(sys.argv) > 1 else ""
if macaddr == "":
    panic("mac address is required")
elif len(macaddr) != 12:
    if ZTE_MACS_FILE != "" and os.path.exists(ZTE_MACS_FILE):
        with open(ZTE_MACS_FILE) as file:
            reader = csv.reader(file, delimiter=",")
            for row in reader:
                if row[0] == macaddr:
                    macaddr = row[1]
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
    ).select_by_value("Ban")

    for i, m in enumerate(macaddr.split(":")):
        driver.find_element_by_id("mac" + str(i + 1)).send_keys(m)

    driver.find_element_by_id("add").click()
