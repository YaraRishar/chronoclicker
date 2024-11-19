from selenium.webdriver import Keys
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.select import Select

import cage_utils
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
                 is_headless: bool = False,
                 driver_path: str = "",
                 max_waiting_time: int = 3,
                 monitor_chat_while_waiting: bool = False,
                 turn_off_timer: bool = False,
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
        self.turn_off_timer = turn_off_timer
        self.notify_about = notify_about
        self.notification_url = notification_url

        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")  # windows....
        options.add_argument("--remote-debugging-port=9222")
        # options.add_argument("--auto-open-devtools-for-tabs")
        options.add_argument("user-data-dir=selenium")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        if is_headless:
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

        element: WebElement = self.locate_element("//div[@id='block_mess']")
        message = element.text
        if not element:
            return 1
        match_seconds = re.search(r"(\d*) мин (\d*) с", message)
        if not match_seconds:
            match_seconds = re.search(r"(\d*) с", message)
            seconds = int(match_seconds[1])
        else:
            seconds = int(match_seconds[1]) * 60 + int(match_seconds[2])
        return seconds

    def get_parameter(self, param_name) -> float | int:
        """ Проверить параметр param_name, вернуть его значение в процентах """

        element = self.locate_element(f"//div[@id='{param_name}']/div[@class='bar']/div[@class='bar-data']")
        if not element:
            return -1
        percents = re.search(r": (\d*)%", element.text)
        return percents[1]

    def check_skill(self, skill_name_server, skill_name) -> str:
        """ Проверить уровень и дробь навыка """

        self.mouse_over(xpath=f"//div[@id='{skill_name_server}']", hover_for=random.uniform(0.1, 0.2))
        skill_name = skill_name[0].upper() + skill_name[1:]
        xpath = f"//div[@class='tooltip-inner' and contains(text(), '{skill_name}')]"
        tooltip_elem = self.locate_element(xpath=xpath)
        text = tooltip_elem.text if tooltip_elem else ""
        level_elem = self.locate_element(f"//div[@id='{skill_name_server}']/div[3]", do_wait=False)
        if not level_elem:
            return ""
        self.mouse_over(xpath=f"//div[@id='{skill_name_server}']", hover_for=0.01)
        return text + ", уровень " + level_elem.text

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

    def play_sound(self, sound_url="https://abstract-class-shed.github.io/cwshed/chat_mention.mp3"):
        """ Воспроизвести звук """

        self.switch_to.new_window("tab")
        self.get(sound_url)
        time.sleep(2)
        cw3 = self.window_handles[0]
        self.close()
        self.switch_to.window(cw3)

    def is_action_active(self) -> bool:
        """ Проверка на выполнение действия """

        element = self.locate_element(xpath="//a[@id='cancel']", do_wait=False)
        return element is not None

    def move_to_location(self, location_name: str, show_availables=False) -> bool:
        """ Общая функция для перехода на локацию """

        if self.is_held():
            self.quit()

        if self.is_action_active():
            seconds = self.check_time()
            clicker_utils.print_timer(console_string="Действие уже совершается!", seconds=seconds,
                                      turn_off_timer=self.turn_off_timer)
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
                                      seconds=seconds, turn_off_timer=self.turn_off_timer)
            self.click(xpath="//a[@id='cancel']")
            time.sleep(random.uniform(1, 3))
            return has_moved
        seconds = self.check_time() + random.uniform(self.short_break_duration[0],
                                                     self.short_break_duration[1])
        clicker_utils.print_timer(console_string=f"Совершён переход в локацию {location_name}", seconds=seconds,
                                  turn_off_timer=self.turn_off_timer)
        if show_availables:
            print(f"Доступные локации: {', '.join(self.get_available_locations())}")
        else:
            self.trigger_long_break(self.long_break_chance, self.long_break_duration)

        return has_moved

    def get_available_actions(self, action_dict) -> list:
        """ Получить список доступных в данный момент действий """

        elements = self.locate_elements(xpath="//div[@id='akten']/a[@class='dey has-tooltip']")
        actions_list = []
        for element in elements:
            for key, value in action_dict.items():
                if int(element.get_attribute("data-id")) == value:
                    actions_list.append(key)
                    break
        return actions_list

    def get_available_locations(self) -> list:
        """ Получить список переходов на локации """

        elements = self.locate_elements(xpath="//span[@class='move_name']")
        location_list = []
        for element in elements:
            try:
                location_list.append(element.get_attribute(name="innerText"))
            except StaleElementReferenceException:
                print("\t\tencountered stale element, retrying getloc call...")
                time.sleep(1)
                self.get_available_locations()

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
        for element in cages_with_items:
            style_str = element.get_attribute("style")
            items_ids.append(re.findall(pattern=r"things\/(\d*)", string=style_str))

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

    def bury_item(self, item_img_id: str, level: int):
        self.click(xpath=f"//div[@class='itemInMouth']/img[@src='things/{item_img_id}.png']", offset_range=(10, 10))
        time.sleep(random.uniform(0.3, 0.6))
        if level != 1:
            slider = self.locate_element(xpath="//div[@id='layer']/"
                                               "span[@class='ui-slider-handle ui-state-default ui-corner-all']")
            self.click(given_element=slider)
            while level != 1:
                time.sleep(random.uniform(0.1, 0.5))
                slider.send_keys(Keys.ARROW_RIGHT)
                level -= 1
        self.click(xpath="//a[text()='Закопать']")
        seconds = self.check_time() + random.uniform(self.short_break_duration[0], self.short_break_duration[1])
        hist_list = self.get_hist_list()
        clicker_utils.print_timer(console_string=f"{hist_list[-1].lstrip()}",
                                  seconds=seconds, turn_off_timer=self.turn_off_timer)

    def get_hist_list(self) -> list:
        hist_list = self.locate_element("//span[@id='ist']").text.split(".")[:-1]
        return hist_list

    def trigger_long_break(self, long_break_chance: float, long_break_duration: list):
        """ Включение долгого перерыва после действия/перехода """

        if random.random() < long_break_chance:
            seconds = random.uniform(long_break_duration[0], long_break_duration[1])
            clicker_utils.print_timer(console_string="Начался долгий перерыв",
                                      seconds=seconds, turn_off_timer=self.turn_off_timer)

    def has_moves(self) -> bool:
        available_locations = self.get_available_locations()
        return available_locations is None

    def is_held(self) -> bool:
        cw3_message_element = self.locate_element(xpath="/html/body/div[1]/table/tbody/tr[2]/td/div[@id='block_mess']")
        if not cw3_message_element:
            return False
        cw3_message = cw3_message_element.text
        if " держит вас во рту" in cw3_message:
            cat_name = cw3_message.split(" держит вас во рту")[0]
            href = self.get_cat_link(cat_name)
            print(f"ВАС ПОДНЯЛ ИГРОК ПО ИМЕНИ {cat_name}! Ссылка на профиль: {href}")
            self.play_sound()
            return True
        return False

    def get_cat_link(self, cat_name) -> str:
        """ Получить ссылку на кота по его имени (в Игровой) """
        cat_element = self.locate_element(xpath=f"//span[@class='cat_tooltip']/u/a[text()='{cat_name}']")
        if not cat_element:
            return "N/A"
        href = "catwar.net" + cat_element.get_attribute("href")
        return href

    def get_current_location(self) -> str:
        """ Получить название локации, на которой находится игрок """
        current_location = "[ Загружается… ]"
        while current_location == "[ Загружается… ]":
            location_element = self.locate_element("/html/body/div[1]/table/tbody/tr[7]/td/"
                                                   "table/tbody/tr/td[2]/div/div/span")
            current_location = location_element.text
            time.sleep(0.5)
        return current_location

    def get_inv_items(self) -> list:
        """ Получить список id изображений всех предметов в инвентаре """

        inv_elements = self.locate_elements(xpath="//div[@class='itemInMouth']/img")
        inv_ids = []
        for element in inv_elements:
            style_str = element.get_attribute("src")
            inv_ids.append(int(re.findall(pattern=r"things\/(\d*)", string=style_str)[0]))
        return inv_ids

    def get_cages_list(self) -> list[cage_utils.Cage]:
        """ Получить список элементов всех клеток на поле """

        cages_list = [cage_utils.Cage(self, row, column) for column in range(1, 11) for row in range(1, 7)]
        return cages_list

    def get_move_coords(self, loc_name) -> tuple:
        cages = self.get_cages_list()
        for cage in cages:
            move_name = cage.get_move_name()
            if move_name == loc_name:
                return cage.row, cage.column
        return -1, -1

    def find_cat_on_loc(self, names_to_find) -> tuple:
        """ Найти кота на текущей локации по имени или ID """

        cages_list = self.get_cages_list()
        for cage in cages_list:
            cat_name = cage.get_cat_name()
            cat_id = cage.get_cat_id()
            location = self.get_current_location()
            if cat_name in names_to_find:
                return cat_name, location, cage.row, cage.column
            elif cat_id in names_to_find:
                return cat_id, location, cage.row, cage.column
        return False, False, False, False

    def get_weight(self):
        pass
