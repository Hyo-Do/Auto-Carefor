import datetime
import json
import logging
import time
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from secret.env_key import ID, ORG_CD, PW

CRAWLING_EXCEPTION = (
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)


def logging_init(print_format="%(levelname)s: %(message)s"):
    """
    로깅 환경 초기화하는 함수

    Args:
        print_format (str, optional): 로그 출력형식. Defaults to "%(levelname)s: %(message)s".
    """
    logging.basicConfig(
        format="%(levelname)s: %(message)s",
        level=logging.INFO,
        filename="output.log",
        encoding="utf-8",
    )
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logging.getLogger().addHandler(console)


class CrawlCarefor:
    page_url = "https://www.carefor.co.kr/login.php"
    login_xpath = '//*[@id="login_outline"]/div[1]/div/form/ul'
    table_xpath = '//*[@id="care_service_list_table"]/tbody'
    info_xpath = '//*[@id="care_service_tbl"]/tbody'
    delay_default_sec = 1
    back_cnt = 155

    def __init__(self) -> None:
        logging_init()
        _options = ChromeOptions()
        _options.add_argument("--headless=new")
        self.driver: webdriver = webdriver.Chrome(options=_options)
        self.driver.get(self.page_url)
        self.actions = ActionChains(self.driver)
        self.date = None
        self.res = {}

    def delay(self, delay_val: 1) -> None:
        time.sleep(self.delay_default_sec * delay_val)

    def find_xpath(self, xpath: str):
        return self.driver.find_element(By.XPATH, xpath)

    def click_xpath(self, xpath: str, passable: bool = False) -> None:
        try:
            self.find_xpath(xpath).click()
        except CRAWLING_EXCEPTION:
            try:
                self.delay(1)
                self.find_xpath(xpath).click()
            except CRAWLING_EXCEPTION:
                if passable:
                    return
                self.delay(2)
                self.find_xpath(xpath).click()

    def _login(self) -> None:
        self.find_xpath(self.login_xpath + "/li[1]/input").send_keys(ORG_CD)
        self.find_xpath(self.login_xpath + "/li[2]/input").send_keys(ID)
        self.find_xpath(self.login_xpath + "/li[3]/input").send_keys(PW)
        self.find_xpath(self.login_xpath + "/li[4]/input").click()
        logging.info(f"로그인 성공 (ID: {ID})")

        # 공지 팝업이 존재하면 각각 닫기
        # self.click_xpath('//*[@id="layerModal"]/div/div[6]/span[2]', passable=True)
        # self.click_xpath(
        #     '//*[@id="layerModal"]/section/section/section[3]/div', passable=True
        # )

    def _go_target_page(self) -> None:
        self.delay(1)
        self.click_xpath('//*[@id="left_area"]/div[4]/ul/li[3]')
        self.delay(0.5)
        self.click_xpath(
            '//*[@id="left_sub3"]/div[2]/table/tbody/tr[2]/td/div/ul/li[1]'
        )

    def _go_last_week(self, cur=0, tot=0) -> None:
        self.click_xpath('//*[@id="r_padding"]/div[5]/div/div[1]/div/div[1]/span[1]')
        logging.info(">> 지난주로 이동" + (f" ({cur}/{tot})" if tot else ""))

    def _back_to_target_week(self) -> None:
        if self.back_cnt == 0:
            return
        self.delay(2)
        for i in range(self.back_cnt):
            self.delay(0.3)
            self._go_last_week(i + 1, self.back_cnt)

    def _get_date(self) -> None:
        self.delay(2)
        date_txt = self.find_xpath(self.info_xpath + "/tr[1]/th[2]/span[1]").text
        self.date = datetime.datetime(*map(int, date_txt.split(".")))
        self.res["date"] = [
            (self.date + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(6)
        ]
        logging.info(
            f"1) 날짜 수집 성공 ({self.res['date'][0]} ~ {self.res['date'][-1]})"
        )

    def _get_people_data(self) -> None:
        self.delay(2)
        people_li = self.driver.find_elements(By.XPATH, self.table_xpath + "/tr")
        logging.info(f"2) 수급자 목록 수집 성공 (총 {len(people_li)-1} 명)")
        _last_msg = ["" for _ in range(5)]
        for people_i in range(1, len(people_li)):
            people_xpath = f"{self.table_xpath}/tr[{people_i}]/td[3]"
            people_name = self.find_xpath(people_xpath).text

            self._click_people_name(people_xpath)
            _msg_li = self._get_daily_message()
            if all(_last_msg[i] == _msg_li[i] for i in range(2)):
                self.delay(1)
                self._click_people_name(people_xpath)
                _msg_li = self._get_daily_message()
            
            _last_msg = _msg_li.copy()
            self.res[people_name] = _msg_li
            logging.info(
                f"- 기재내역 수집 성공 (성함: {people_name}, 수집한 일자: {len(_msg_li)} 일) ({people_i}/{len(people_li)-1})"
            )

    def _click_people_name(self, people_xpath):
        self.actions.move_to_element(self.find_xpath(people_xpath)).perform()
        self.delay(0.2)
        self.click_xpath(people_xpath)
        WebDriverWait(self.driver, 10).until_not(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="loading_div"]'))
        )
        self.delay(0.5)

    def _get_daily_message(self):
        msg_li = []
        day_li = self.driver.find_elements(By.XPATH, self.info_xpath + "/tr[1]/th[7]")
        for day_i in range(1, 7):
            if day_i == 6 and len(day_li) == 0: continue
            try:
                msg = self.find_xpath(f"{self.info_xpath}/tr[1]/th[{day_i+1}]/div/div")
                msg_li.append("*" * 10 + msg.text)
            except NoSuchElementException:
                try:
                    msg = self.find_xpath(f"{self.info_xpath}/tr[17]/td[{day_i}]/textarea")
                    msg_li.append(msg.text)
                except CRAWLING_EXCEPTION:
                    self.delay(1)
                    day_li = self.driver.find_elements(By.XPATH, self.info_xpath + "/tr[1]/th[7]")
                    except_msg = self.driver.find_elements(By.XPATH, f"{self.info_xpath}/tr[1]/th[{day_i+1}]/div/div")
                    if len(except_msg) > 0 or (day_i == 6 and len(day_li) == 0):
                        msg_li.append("*" * 10 + "(기타 조회 실패)")
                        logging.info(f"[!] 조회 실패 ({self.res['date'][day_i]})")
                        continue
                    
                    msg = self.find_xpath(f"{self.info_xpath}/tr[17]/td[{day_i}]/textarea")
                    msg_li.append(msg.text)
        return msg_li

    def _export_file(self) -> None:
        with open(
            f"output_{self.date.strftime('%Y%m%d')}.json", "wt", encoding="utf8"
        ) as f:
            json.dump(self.res, f, ensure_ascii=False)
            logging.info(
                f"3) 파일 저장 완료 (파일명: output_{self.date.strftime('%Y%m%d')}.json)"
            )

    def run(self) -> None:
        self._login()
        self._go_target_page()
        self._back_to_target_week()
        for _ in range(300):
            self._get_date()
            self._get_people_data()
            self._export_file()
            self._go_last_week()

        self.driver.quit()


if __name__ == "__main__":
    crawler = CrawlCarefor()
    crawler.run()
