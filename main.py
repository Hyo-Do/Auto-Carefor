import datetime
import json
import time
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains


from secret.env_key import ID, ORG_CD, PW


def click_element(driver: webdriver, xpath: str, on_fail=None):
    try:
        driver.find_element(By.XPATH, xpath).click()
        time.sleep(0.6)
    except NoSuchElementException:
        pass


def init_driver() -> webdriver:
    _options = ChromeOptions()
    # _options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=_options)
    driver.get("https://www.carefor.co.kr/login.php")
    return driver


def login_process(driver: webdriver):
    login_xpath = '//*[@id="login_outline"]/div[1]/div/form/ul'
    driver.find_element(By.XPATH, login_xpath + "/li[1]/input").send_keys(ORG_CD)
    driver.find_element(By.XPATH, login_xpath + "/li[2]/input").send_keys(ID)
    driver.find_element(By.XPATH, login_xpath + "/li[3]/input").send_keys(PW)
    driver.find_element(By.XPATH, login_xpath + "/li[4]/input").click()


def check_alert_process(driver: webdriver):
    click_element(driver, '//*[@id="layerModal"]/div/div[6]/span[2]')
    click_element(driver, '//*[@id="layerModal"]/section/section/section[3]/div')


def go_section_3_1_process(driver: webdriver):
    click_element(driver, '//*[@id="left_area"]/div[4]/ul/li[3]')
    click_element(
        driver, '//*[@id="left_sub3"]/div[2]/table/tbody/tr[2]/td/div/ul/li[1]'
    )


if __name__ == "__main__":
    _delay = 0.8
    _driver: webdriver = init_driver()
    _actions = ActionChains(_driver)
    login_process(_driver)
    check_alert_process(_driver)
    go_section_3_1_process(_driver)

    table_xpath = '//*[@id="care_service_list_table"]/tbody'
    info_xpath = '//*[@id="care_service_tbl"]/tbody'
    people_li = _driver.find_elements(By.XPATH, table_xpath + "/tr")

    res = {}
    time.sleep(_delay)
    date_txt = _driver.find_element(By.XPATH, f"{info_xpath}/tr[1]/th[2]/span[1]").text
    date = datetime.datetime(*map(int, date_txt.split(".")))
    res['date'] = [(date + datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6)]

    for i, people in enumerate(people_li[:-1]):
        name_xpath = f"{table_xpath}/tr[{i+1}]/td[3]"
        target_ele = _driver.find_element(By.XPATH, name_xpath)
        nm = target_ele.text
        _actions.move_to_element(target_ele).perform()
        target_ele.click()
        time.sleep(_delay)

        msg_li = []
        for i in range(1, 7):
            try:
                ele = _driver.find_element(By.XPATH, f"{info_xpath}/tr[1]/th[{i+1}]/div/div")
                msg_li.append("*"*8 + ele.text)
            except NoSuchElementException:
                if i == 6 and len(_driver.find_elements(By.XPATH, f"{info_xpath}/tr[1]/th[7]")) == 0:
                    continue
                txt = _driver.find_element(By.XPATH, f"{info_xpath}/tr[17]/td[{i}]/textarea").text
                msg_li.append(txt)
        res[nm] = msg_li
    
    with open("output.json", "wt", encoding="utf8") as f:
        json.dump(res, f, ensure_ascii=False)

    _driver.quit()
