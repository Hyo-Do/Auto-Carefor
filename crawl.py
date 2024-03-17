import datetime
import json
import logging
import time
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException
)
from selenium.webdriver.common.action_chains import ActionChains


from secret.env_key import ID, ORG_CD, PW


def click_element(driver: webdriver, xpath: str, on_fail=None, delay=0.8):
    try:
        driver.find_element(By.XPATH, xpath).click()
        time.sleep(delay)
    except (NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException):
        time.sleep(delay * 2)
        driver.find_element(By.XPATH, xpath).click()
        


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
    logging.info(f"로그인 성공 (ID: {ID})")

    # 공지 팝업이 존재하면 각각 닫기
    click_element(driver, '//*[@id="layerModal"]/div/div[6]/span[2]')
    click_element(driver, '//*[@id="layerModal"]/section/section/section[3]/div')


def go_last_week(driver: webdriver, cur = 0, total = 0):
    click_element(driver, '//*[@id="r_padding"]/div[5]/div/div[1]/div/div[1]/span[1]')
    logging.info(">> 지난주로 이동" + ("" if total == 0 else f" ({cur}/{total})"))


if __name__ == "__main__":
    logging.basicConfig(
        format="%(levelname)s: %(message)s",
        level=logging.INFO,
        filename="output.log",
        encoding="utf-8",
    )
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logging.getLogger().addHandler(console)
    
    _delay = 1
    _driver: webdriver = init_driver()
    _actions = ActionChains(_driver)

    login_process(_driver)
    click_element(_driver, '//*[@id="left_area"]/div[4]/ul/li[3]')
    click_element(_driver, '//*[@id="left_sub3"]/div[2]/table/tbody/tr[2]/td/div/ul/li[1]')
    time.sleep(_delay)

    table_xpath = '//*[@id="care_service_list_table"]/tbody'
    info_xpath = '//*[@id="care_service_tbl"]/tbody'
    
    _back_cnt = 148
    for i in range(_back_cnt):
        go_last_week(_driver, i+1, _back_cnt)

    for week_i in range(50):
        res = {}
        date_txt = _driver.find_element(By.XPATH, f"{info_xpath}/tr[1]/th[2]/span[1]").text
        date = datetime.datetime(*map(int, date_txt.split(".")))
        res["date"] = [(date + datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6)]
        logging.info(f"1) 날짜 수집 성공 ({res['date'][0]} ~ {res['date'][-1]})")

        time.sleep(_delay * 1.5)
        people_li = _driver.find_elements(By.XPATH, table_xpath + "/tr")
        logging.info(f"2) 수급자 목록 수집 성공 (총 {len(people_li)-1} 명)")
        for people_i, people in enumerate(people_li[:-1]):
            people_name = _driver.find_element(By.XPATH, f"{table_xpath}/tr[{people_i+1}]/td[3]")
            _actions.move_to_element(people_name).perform()
            time.sleep(_delay * 0.5)
            try:
                people_name.click()
            except (ElementClickInterceptedException, StaleElementReferenceException):
                time.sleep(_delay)
                print(f"{table_xpath}/tr[{people_i+1}]/td[3]")
                _actions.move_to_element(people_name).perform()
                time.sleep(_delay)
                people_name.click()
            time.sleep(_delay * 1.5)
            msg_li = []
            for day_i in range(1, 7):
                if day_i == 6 and len(_driver.find_elements(By.XPATH, f"{info_xpath}/tr[1]/th[7]")) == 0:
                    continue
                try:
                    ele = _driver.find_element(By.XPATH, f"{info_xpath}/tr[1]/th[{day_i+1}]/div/div")
                    msg_li.append("*" * 8 + ele.text)
                except NoSuchElementException:
                    txt = _driver.find_element(By.XPATH, f"{info_xpath}/tr[17]/td[{day_i}]/textarea").text
                    msg_li.append(txt)
            res[people_name.text] = msg_li
            logging.info(f"- 기재내역 수집 성공 (성함: {people_name.text}, 수집한 일자: {len(msg_li)} 일) ({people_i+1}/{len(people_li)-1})")

        with open(f"output_{date.strftime('%Y%m%d')}.json", "wt", encoding="utf8") as f:
            json.dump(res, f, ensure_ascii=False)
            logging.info(f"3) 파일 저장 완료 (파일명: output_{date.strftime('%Y%m%d')}.json)")
            
        go_last_week(_driver)

    _driver.quit()
