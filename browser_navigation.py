from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.select import Select

import clicker_utils
from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (NoSuchElementException,
                                        MoveTargetOutOfBoundsException,
                                        StaleElementReferenceException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.chrome.service import Service
import time
import random
import re
import datetime


class DriverWrapper(WebDriver):
    """ Обёртка для драйвера WebDriver из модуля selenium. """

    def __init__(self,
                 long_break_chance=0.05,
                 long_break_duration=(10, 200),
                 short_break_duration=(1, 5),
                 critical_sleep_pixels=20,
                 is_headless: str = "False",
                 driver_path: str = "",
                 max_waiting_time: int = 3,
                 monitor_chat_while_waiting: bool = False,
                 notify_about: [str] = "",
                 notification_url: str = ""):

        self.long_break_chance = long_break_chance
        self.long_break_duration = long_break_duration
        self.short_break_duration = short_break_duration
        self.critical_sleep_pixels = critical_sleep_pixels
        self.is_headless = is_headless
        self.driver_path = driver_path
        self.max_waiting_time = max_waiting_time
        self.monitor_chat_while_waiting = monitor_chat_while_waiting
        self.notify_about = notify_about
        self.notification_url = notification_url

        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")  # windows....
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("user-data-dir=selenium")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        if is_headless == "True":
            options.add_argument("--headless")
            print("Запуск в фоновом режиме... Может занять некоторое время.")
        else:
            print("Вебдрайвер запускается, может занять некоторое время...")

        if driver_path:
            service = Service(driver_path)
            super().__init__(options=options, service=service)
            print(f"Вебдрайвер запущен, путь {driver_path}")
        else:
            super().__init__(options=options)
            print("Вебдрайвер запущен.")

        stealth(self,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True)

        self.implicitly_wait(max_waiting_time)

    def locate_element(self, xpath: str, do_wait=True) -> WebElement | None:
        """ Найти элемент на странице по xpath. """

        try:
            if not do_wait:
                self.implicitly_wait(0)
            element = self.find_element(By.XPATH, xpath)
            if not do_wait:
                self.implicitly_wait(self.max_waiting_time)
            return element
        except NoSuchElementException:
            if self.is_cw3_disabled():
                self.refresh()
                self.locate_element(xpath)
            else:
                return None

    def locate_elements(self, xpath: str, do_wait=True) -> list[WebElement] | None:
        """ Найти элемент на странице по xpath. """

        try:
            if not do_wait:
                self.implicitly_wait(0)
            elements = self.find_elements(By.XPATH, xpath)
            if not do_wait:
                self.implicitly_wait(self.max_waiting_time)
            return elements
        except NoSuchElementException:
            if self.is_cw3_disabled():
                self.refresh()
                self.locate_elements(xpath)
            else:
                return None

    def is_cw3_disabled(self) -> bool:
        """ Проверка на активность Игровой """

        try:
            cw3_disabled_element = self.find_element(By.XPATH, "//body[text()='Вы открыли новую вкладку с Игровой, "
                                                               "поэтому старая (эта) больше не работает.']")
            if cw3_disabled_element:
                return True
        except NoSuchElementException:
            return False

    def remove_cursor(self):
        action_builder = ActionBuilder(self)
        action_builder.pointer_action.move_to_location(1, 8)
        action_builder.perform()

    def click(self, xpath="xpath", offset_range=(0, 0), given_element=None) -> bool:
        """ Клик по элементу element с оффсетом offset_range.
        Возвращает True, если был совершён клик по элементу. """

        if xpath != "xpath" and not given_element:
            element = self.locate_element(xpath)
        elif given_element:
            element = given_element
        else:
            return False

        if not element or not element.is_displayed():
            return False

        random_offset = (random.randint(-offset_range[0], offset_range[0]),
                         random.randint(-offset_range[1], offset_range[1]))
        try:
            action_chain = ActionChains(self)
            action_chain.scroll_to_element(element).perform()
            action_chain.move_to_element_with_offset(to_element=element,
                                                     xoffset=random_offset[0],
                                                     yoffset=random_offset[1]
                                                     ).perform()
            action_chain.click_and_hold().perform()
            time.sleep(random.uniform(0, 0.1))
            action_chain.release().perform()
            self.remove_cursor()
        except MoveTargetOutOfBoundsException:
            print("MoveTargetOutOfBoundsException raised for reasons unknown to man :<")
            print("random offset =", random_offset)
            return False
        return True

    def mouse_over(self, xpath: str, hover_for=0.1) -> bool:
        """ Передвинуть курсор к элементу по xpath """

        element = self.locate_element(xpath)
        if not element or not element.is_displayed():
            return False
        action_chain = ActionChains(self)
        action_chain.scroll_to_element(element).perform()
        action_chain.move_to_element(element).perform()
        time.sleep(hover_for)
        return True

    def check_time(self) -> int:
        """ Проверить, сколько времени осталось до окончания действия.
        Если никакое действие в данный момент не выполняется, возвращает 1. """

        element: WebElement = self.locate_element("//span[@id='sek']")
        if not element:
            return 1
        match_seconds = re.match(r"(\d*) мин (\d*) с", element.text)
        if not match_seconds:
            match_seconds = re.match(r"(\d*) с", element.text)
            seconds = int(match_seconds[1])
        else:
            seconds = int(match_seconds[1]) * 60 + int(match_seconds[2])
        return seconds

    def check_parameter(self, param_name) -> float | int:
        """ Проверить параметр param_name, вернуть его значение в процентах """

        element = self.locate_element(f"//span[@id='{param_name}']/*/*/*/descendant::*")
        if not element:
            return -1
        pixels = float(element.get_attribute("style").split("px")[0].split("width: ")[1])
        percents = round(pixels / 150 * 100, 2)
        if percents == int(percents):
            return int(percents)
        return percents

    def check_skill(self, skill_name) -> str:
        """ Проверить уровень и дробь навыка """

        tooltip_elem = self.locate_element("//div[@id='tiptip_content']")
        level_elem = self.locate_element(f"//table[@id='{skill_name}_table']", do_wait=False)
        if not level_elem:
            return ""
        self.mouse_over(xpath=f"//span[@id='{skill_name}']/*/*/*/descendant::*")
        if not tooltip_elem.text:
            self.mouse_over(xpath=f"//span[@id='{skill_name}']/*/*/*/descendant::*", hover_for=0.01)
        if skill_name in tooltip_elem.text:
            return tooltip_elem.text + ", уровень " + level_elem.text
        return tooltip_elem.text + ", уровень " + level_elem.text

    def get_last_cw3_message(self) -> tuple:
        """ Получить последнее сообщение в чате Игровой и имя написавшего """

        try:
            last_message = self.locate_element(xpath="//*[@id='chat_msg']/span[1]/table/tbody/tr/td[1]/span/span").text
            name_from = self.locate_element(xpath="//*[@id='chat_msg']/span[1]/table/tbody/tr/td[1]/span/b").text
        except AttributeError:
            return '', ''
        return last_message, name_from

    def monitor_cw3_chat(self, monitor_for: float):
        """ Выводить последние сообщения в чате Игровой, пока не истечёт время end_time """

        end_time = time.time() + monitor_for
        temp_message = ('', '')
        while time.time() <= end_time:
            time.sleep(1)
            message_bundle = self.get_last_cw3_message()
            if message_bundle == temp_message:
                continue
            else:
                message_time = datetime.datetime.now()
                print(f"Чат |\t{message_bundle[0]} - {message_bundle[1]} | {message_time.strftime('%H:%M:%S')}")
                for name in self.notify_about:
                    if name in message_bundle[0]:
                        self.play_sound()
            temp_message = message_bundle

    def play_sound(self, sound_url=""):
        self.switch_to.new_window("tab")
        self.get(sound_url)
        time.sleep(2)
        cw3 = self.window_handles[0]
        self.switch_to.window(cw3)

    def is_action_active(self) -> bool:
        """ Проверка на выволнение действия """

        element = self.locate_element(xpath="//a[@id='cancel']", do_wait=False)
        if element:
            return True
        return False

    def move_to_location(self, location_name: str, show_availibles=True) -> bool:
        """ Техническая функция для перехода на локацию. """

        if self.is_action_active():
            seconds = self.check_time()
            clicker_utils.print_timer(console_string="Действие уже совершается!", seconds=seconds)
            return False
        elements = self.locate_elements(f"//span[text()='{location_name.replace(" (о)", "")}' "
                                        f"and @class='move_name']/preceding-sibling::*")
        if not elements:
            return False
        random_element = random.sample(elements, 1)[0]
        has_moved = self.click(given_element=random_element,
                               offset_range=(40, 70))
        if " (о)" in location_name:
            seconds = random.uniform(0.5, 3)
            clicker_utils.print_timer(console_string=f"Совершён переход с отменой в локацию {location_name}",
                                      seconds=seconds)
            self.click(xpath="//a[@id='cancel']")
            time.sleep(random.uniform(1, 3))
            return has_moved
        seconds = self.check_time() + random.uniform(self.short_break_duration[0],
                                                     self.short_break_duration[1])
        clicker_utils.print_timer(console_string=f"Совершён переход в локацию {location_name}", seconds=seconds)
        if show_availibles:
            print(f"Доступные локации: {', '.join(self.get_availible_locations())}")
        else:
            clicker_utils.trigger_long_break(self.long_break_chance, self.long_break_duration)

        return has_moved

    def get_availible_actions(self, action_dict) -> list:
        """ Получить список доступных в данный момент действий """

        elements_self = self.locate_elements(xpath="//div[@id='akten']/a[@class='dey']")
        elements_others = self.locate_elements(xpath="//div[@id='dein']/a[@class='dey']")
        elements = elements_self + elements_others
        actions_list = []
        for element in elements:
            for key, value in action_dict.items():
                if int(element.get_attribute("data-id")) == value:
                    actions_list.append(key)
                    break
        return actions_list

    def get_availible_locations(self) -> list:
        """ Получить список переходов на локации """

        elements = self.locate_elements(xpath="//span[@class='move_name']")
        location_list = []
        for element in elements:
            try:
                location_list.append(element.get_attribute(name="innerText"))
            except StaleElementReferenceException:
                print("\t\tencountered stale element, retrying getloc call...")
                time.sleep(1)
                self.get_availible_locations()

        return location_list

    def get_cats_list(self) -> list:
        cats_list = []
        elements = self.locate_elements(xpath="//span[@class='cat_tooltip']/u/a")
        for element in elements:
            cats_list.append(element.get_attribute(name="innerText"))
        return cats_list

    def get_last_message(self) -> str:
        """ Получить последнее отправленное сообщение из текущей вкладки чата (не в игровой!) """

        last_message = self.locate_element(xpath="//div[@class='mess_div']/div[@class='parsed']").text
        while not bool(last_message):
            self.refresh()
            time.sleep(2)
            last_message = self.get_last_message()

        return last_message

    def type_in_chat(self, text: str, entry_xpath: str):
        """ Написать сообщение в чат (занимает реалистичное количество времени на набор текста) """

        text = [i for i in text]
        chatbox: WebElement = self.locate_element(entry_xpath)
        for i in range(len(text)):
            chatbox.send_keys(text[i])
            if text[i - 1] == text[i]:
                time.sleep(random.uniform(0, 0.1))
                continue
            time.sleep(random.uniform(0.05, 0.5))
        if len(text) < 5:
            time.sleep(random.uniform(1, 3))

    def rabbit_game(self, lower_bound=-9999999999, upper_bound=9999999999) -> bool:
        """ Игра в числа """

        last_message = ""
        while "это" not in last_message:
            time.sleep(random.uniform(0.8, 1.5))
            guess = (upper_bound + lower_bound) // 2

            self.type_in_chat(text=f"/number {guess}", entry_xpath="//div[@id='mess']")
            self.click(xpath="//input[@id='mess_submit']")

            time.sleep(random.uniform(1.5, 3))
            last_message = self.get_last_message()

            if "Меньше" in last_message:
                # guess = 50, (0, 100), < 50 -> (0, 49)
                if guess - 1 in range(lower_bound, upper_bound + 1):
                    upper_bound = guess - 1
                else:
                    upper_bound = lower_bound
            elif "Больше" in last_message:
                # guess = 50, (0, 100), > 50 -> (51, 100)
                if guess + 1 in range(lower_bound + 1, upper_bound):
                    lower_bound = guess + 1
                else:
                    lower_bound = upper_bound
            elif "это" in last_message:
                print("+4 кроля!")
                return True
            else:
                print(f"Произошла ошибка при парсинге сообщения с текстом {last_message}")
                return False

            print(last_message.split(", ")[0])
            print(f"({lower_bound}, {upper_bound}), difference = {upper_bound - lower_bound}")

    def get_field_items(self) -> list:
        cages_with_items = self.locate_elements(xpath="//div[@style!='' and @class='cage_items']", do_wait=False)
        items_ids = []

        if not cages_with_items:
            return []
        print("Предметы на поле:")
        for element in cages_with_items:
            style_str = element.get_attribute("style")
            items_ids.append(re.findall(pattern=r"things\/(\d*)", string=style_str))
            print(f"Ссылка на изображение предмета: https://catwar.su/cw3/things/{items_ids[-1]}.png\n")

        return items_ids

    def print_cats(self):
        """ Вывести список игроков на одной локации с вами """

        cages = []
        for row in range(1, 7):
            for column in range(1, 11):
                element = self.locate_element(xpath=f"//table[@id='cages']/tbody/tr[{row}]/td[{column}]/div "
                                                    f"//span[@class='cat_tooltip']/u/a", do_wait=False)
                if element:
                    cages.append([row, column])

        cats_list = self.get_cats_list()
        if len(cats_list) == 1:
            print("Других котов на локации нет.")
            return
        print("Коты на локации:")
        temp_row = cages[0][0]
        for i in range(len(cats_list)):
            print(f"{cats_list[i]} ({cages[i][0]}x{cages[i][1]})", end=", ")
            try:
                if cages[i + 1][0] != temp_row:
                    temp_row = cages[i + 1][0]
                    print()
            except IndexError:
                print()

    def is_cat_in_action(self, cat_name: str) -> bool:
        """ Проверка кота на действие (потереться носом о нос и отменить действие)
         result = True -> кот занят действием """

        selector = self.locate_element(xpath="//*[@id='mit']")
        dropdown_object = Select(selector)

        options_list = selector.find_elements(By.XPATH, "//option")
        names_list = [i.text for i in options_list]
        if cat_name in names_list:
            dropdown_object.select_by_visible_text(cat_name)
            time.sleep(0.5)
            self.click(xpath="//*[@id='mitok']")
            time.sleep(0.5)
            self.click(xpath="//img[@src='actions/9.png']")
            time.sleep(random.uniform(1, 2))
            result = self.click(xpath="//a[@id='cancel']")
            return result
