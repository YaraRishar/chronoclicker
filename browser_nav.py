from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.select import Select

from cage_utils import Cage
import clicker_utils
from clicker_utils import wait_for, get_text
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
from datetime import datetime


class DriverWrapper(WebDriver):
    """ Обёртка для драйвера WebDriver из модуля selenium. """

    def __init__(self, logger):
        self.logger = logger

        config = clicker_utils.load_json("config.json")
        self.settings, self.alias_dict = config["settings"], config["aliases"]
        gamedata = clicker_utils.load_json("gamedata.json")
        self.action_dict, self.parameters_dict, self.skills_dict = (
            gamedata["actions"], gamedata["parameters"], gamedata["skills"])

        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("user-data-dir=selenium")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])


        if self.settings["my_id"] == "1":
            self.logger.info("[!!!] Параметр my_id в файле config.json не заполнен, поиск пути по клеткам "
                  "и (в будущем) автотренировки не будут работать! "
                  "Введите settings my_id - 1, заменив 1 на ваш ID, "
                  "либо не используйте автокач ПУ в опасных локациях! Кликер ВЫЛЕТИТ и вы УТОНЕТЕ!")

        if self.settings["is_headless"]:
            options.add_argument("--headless=new")
            self.logger.info("Запуск в фоновом режиме... Может занять некоторое время.")
        else:
            self.logger.info("Вебдрайвер запускается, может занять некоторое время...")

        if self.settings["driver_path"]:
            service = Service(self.settings["driver_path"])
            super().__init__(options=options, service=service)
            self.logger.info(f"Вебдрайвер запущен, путь {self.settings["driver_path"]}")
        else:
            super().__init__(options=options)
            self.logger.info("Вебдрайвер запущен... ")
        self.logger.info(f"Версия Chrome: {self.capabilities['browserVersion']}")
        self.command_executor.set_timeout(1000)

        stealth(self,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True)

        self.implicitly_wait(self.settings["max_waiting_time"])

        self.logger.info(f"Игровая загружается, если прошло более минуты - перезапустите кликер.")
        self.get("https://catwar.net/cw3/")
        if self.current_url != "https://catwar.net/cw3/":
            self.logger.info("Для включения кликера вам необходимо залогиниться в варовский аккаунт.\n"
                             "ВНИМАНИЕ: все ваши данные (почта и пароль) "
                             "сохраняются в папке selenium (либо в профилях chrome), "
                             "она создаётся в той же папке, куда вы поместили этот "
                             "скрипт. НЕ ОТПРАВЛЯЙТЕ НИКОМУ папку selenium. \n"
                             "Все команды кликера работают ИЗ ИГРОВОЙ!")
        elif self.current_url == "https://catwar.net/cw3/" and not self.settings["is_headless"]:
            self.logger.info("\t\t[!!!] Кликер может зависнуть, если окно браузера не в фокусе. Чтобы этого избежать, "
                             "пропишите команду settings is_headless - True")

    async def locate_element(self, xpath: str, do_wait=True) -> WebElement | None:
        """ Найти элемент на странице по xpath. """

        # self.logger.info(f"locating {xpath}")
        try:
            if not do_wait:
                self.implicitly_wait(0)
            element = self.find_element(By.XPATH, xpath)
            if not do_wait:
                self.implicitly_wait(self.settings["max_waiting_time"])
            # self.logger.info(f"!found {xpath}")
            return element
        except NoSuchElementException:
            if self.is_cw3_disabled():
                self.refresh()
                await self.locate_element(xpath)
            else:
                # self.logger.info(f"not found {xpath}")
                return None

    async def locate_elements(self, xpath: str,
                        do_wait=True) -> list[WebElement] | None:
        """ Найти элемент на странице по xpath. """

        try:
            if not do_wait:
                self.implicitly_wait(0)
            elements = self.find_elements(By.XPATH, xpath)
            if not do_wait:
                self.implicitly_wait(self.settings["max_waiting_time"])
            return elements
        except NoSuchElementException:
            if self.is_cw3_disabled():
                self.refresh()
                await self.locate_elements(xpath)
            else:
                return None

    def is_cw3_disabled(self) -> bool:
        """ Проверка на активность Игровой """

        try:
            cw3_disabled_element = self.find_element(
                By.XPATH, "//body[contains(text(), 'Вы открыли новую вкладку с Игровой')]")
            return bool(cw3_disabled_element)
        except NoSuchElementException:
            return False

    def remove_cursor(self):
        action_builder = ActionBuilder(self)
        action_builder.pointer_action.move_to_location(1, 8)
        action_builder.perform()

    async def click(self, xpath="xpath", offset_range=(0, 0),
              given_element=None) -> bool:
        """ Клик по элементу element с оффсетом offset_range.
        Возвращает True, если был совершён клик по элементу. """

        if xpath != "xpath" and not given_element:
            element = await self.locate_element(xpath)
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
            await wait_for(0, 0.05)
            action_chain.release().perform()
            self.remove_cursor()
        except MoveTargetOutOfBoundsException:
            return False
        return True

    async def mouse_over(self, xpath: str, hover_for=0.1) -> bool:
        """ Передвинуть курсор к элементу по xpath """

        element = await self.locate_element(xpath)
        if not element or not element.is_displayed():
            return False
        action_chain = ActionChains(self)
        action_chain.scroll_to_element(element).perform()
        action_chain.move_to_element(element).perform()
        await wait_for(hover_for)
        return True

    async def check_time(self) -> int:
        """ Проверить, сколько времени осталось до окончания действия.
        Если никакое действие в данный момент не выполняется, возвращает 1. """

        element: WebElement = await self.locate_element("//div[@id='block_mess']")
        if not element:
            return 1
        message = get_text(element)
        match_seconds = re.search(r"(\d*) мин (\d*) с", message)
        if not match_seconds:
            match_seconds = re.search(r"(\d*) с", message)
            seconds = int(match_seconds[1])
        else:
            seconds = int(match_seconds[1]) * 60 + int(match_seconds[2])
        return seconds

    async def get_action_str(self) -> str:
        element: WebElement = await self.locate_element("//div[@id='block_mess']")
        if not element:
            return "Действие не выполняется."
        return get_text(element)

    async def get_parameter(self, param_name) -> float | int:
        """ Проверить параметр param_name, вернуть его значение в процентах """

        element = await self.locate_element(f"//div[@id='{param_name}']/div[@class='bar']/div[@class='bar-data']")
        if not element:
            return -1
        percents = re.search(r": (\d*)%", element.text)
        return percents[1]

    async def check_skill(self, skill_name_server, skill_name) -> str:
        """ Проверить уровень и дробь навыка """

        await self.mouse_over(xpath=f"//div[@id='{skill_name_server}']", hover_for=random.uniform(0.1, 0.2))
        skill_name = skill_name[0].upper() + skill_name[1:]
        xpath = f"//div[@class='tooltip-inner' and contains(text(), '{skill_name}')]"
        tooltip_elem = await self.locate_element(xpath=xpath)
        text = tooltip_elem.text if tooltip_elem else ""
        level_elem = await self.locate_element(f"//div[@id='{skill_name_server}']/div[3]", do_wait=False)
        if not level_elem:
            return ""
        await self.mouse_over(f"//div[@id='{skill_name_server}']", hover_for=0.01)
        return text + ", уровень " + get_text(level_elem)

    async def get_last_cw3_message(self) -> tuple:
        """ Получить последнее сообщение в чате Игровой и имя написавшего """

        try:
            message_element = await self.locate_element(
                "//*[@id='chat_msg']/span[1]/table/tbody/tr/td[1]/span/span")
            last_message = get_text(message_element)
            name_from_element = await self.locate_element(
                "//*[@id='chat_msg']/span[1]/table/tbody/tr/td[1]/span/b")
            name_from = get_text(name_from_element)
        except AttributeError:
            return "", ""
        return last_message, name_from

    async def monitor_cw3_chat(self, monitor_for: float):
        """ Выводить последние сообщения в чате Игровой, пока не истечёт время end_time """

        end_time = time.time() + monitor_for
        temp_message = ('', '')
        while time.time() <= end_time:
            await wait_for(1)
            message_bundle = await self.get_last_cw3_message()
            if message_bundle == temp_message:
                continue
            message_time = datetime.now()
            self.logger.info(f"Чат |\t{message_bundle[0]} - {message_bundle[1]} | {message_time.strftime('%H:%M:%S')}")
            for name in self.settings["notify_about"]:
                if name in message_bundle[0]:
                    await self.play_sound()
            temp_message = message_bundle

    async def play_sound(self,
                   sound_url="https://abstract-class-shed.github.io/cwshed/chat_mention.mp3"):
        """ Воспроизвести звук """

        self.switch_to.new_window("tab")
        self.get(sound_url)
        await wait_for(2)
        cw3 = self.window_handles[0]
        self.close()
        self.switch_to.window(cw3)

    async def is_action_active(self) -> bool:
        """ Проверка на выполнение действия """

        element = await self.locate_element(xpath="//a[@id='cancel']", do_wait=False)
        return element is not None

    async def get_available_actions(self, action_dict) -> list:
        """ Получить список доступных в данный момент действий """

        elements = await self.locate_elements("//div[@id='akten']/a[@class='dey has-tooltip']")
        actions_list = []
        for element in elements:
            for key, value in action_dict.items():
                if int(element.get_attribute("data-id")) == value:
                    actions_list.append(key)
                    break
        return actions_list

    async def get_available_locations(self) -> list:
        """ Получить список переходов на локации """

        elements = await self.locate_elements(xpath="//span[@class='move_name']")
        location_list = []
        for element in elements:
            try:
                location_list.append(element.get_attribute(name="innerText"))
            except StaleElementReferenceException:
                await wait_for(0.5)
                await self.get_available_locations()

        return location_list

    async def get_cats_list(self) -> list:
        cats_list = []
        elements = await self.locate_elements(xpath="//span[@class='cat_tooltip']/u/a")
        for element in elements:
            cats_list.append(element.get_attribute(name="innerText"))
        return cats_list

    async def get_last_message(self) -> str:
        """ Получить последнее отправленное сообщение из текущей вкладки чата (не в игровой!) """

        last_message_element = await self.locate_element(xpath="//div[@class='mess_div']/div[@class='parsed']")
        last_message = get_text(last_message_element)
        while not bool(last_message):
            self.refresh()
            await wait_for(0.5)
            last_message = self.get_last_message()

        return last_message

    async def type_in_chat(self, text: str, entry_xpath: str):
        """ Написать сообщение в чат (занимает реалистичное количество времени на набор текста) """

        text = [i for i in text]
        chatbox: WebElement = await self.locate_element(entry_xpath)
        for i in range(len(text)):
            chatbox.send_keys(text[i])
            if text[i - 1] == text[i]:
                await wait_for(0, 0.1)
                continue
            await wait_for(0.05, 0.5)
        if len(text) < 5:
            await wait_for(1, 3)

    async def rabbit_game(self, lower_bound=-9999999999, upper_bound=9999999999) -> bool:
        """ Игра в числа """

        last_message = ""
        while "это" not in last_message:
            await wait_for(0.8, 1.5)
            guess = (upper_bound + lower_bound) // 2

            await self.type_in_chat(text=f"/number {guess}", entry_xpath="//div[@id='mess']")
            await self.click(xpath="//input[@id='mess_submit']")

            await wait_for(1.5, 3)
            last_message = await self.get_last_message()
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
                self.logger.info("+4 кроля!")
                return True
            else:
                self.logger.error(f"Произошла ошибка при парсинге сообщения с текстом {last_message}")
                return False

            self.logger.info(last_message.split(", ")[0])
            self.logger.info(f"({lower_bound}, {upper_bound}), difference = {upper_bound - lower_bound}")
        return True

    async def get_field_items(self) -> list:
        cages_with_items = await self.locate_elements(xpath="//div[@style!='' and @class='cage_items']",
                                                do_wait=False)
        items_ids = []

        if not cages_with_items:
            return []
        for element in cages_with_items:
            style_str = element.get_attribute("style")
            items_ids.append(re.findall(pattern=r"things\/(\d*)", string=style_str))

        return items_ids

    async def print_cats(self):
        """ Вывести список игроков на одной локации с вами """

        cages = []
        for row in range(1, 7):
            for column in range(1, 11):
                element = await self.locate_element(f"//table[@id='cages']/tbody/tr[{row}]/td[{column}]/"
                                              f"div//span[@class='cat_tooltip']/u/a", do_wait=False)
                if element:
                    cages.append([row, column])

        cats_list = await self.get_cats_list()
        if len(cats_list) == 1:
            self.logger.info("Других котов на локации нет.")
            return
        self.logger.info("Коты на локации:")
        temp_row = cages[0][0]
        cats_row_str = ""
        for i in range(len(cats_list)):
            cats_row_str += f"{cats_list[i]} ({cages[i][0]}x{cages[i][1]}) | "
            try:
                if cages[i + 1][0] != temp_row:
                    temp_row = cages[i + 1][0]
                    self.logger.info(cats_row_str)
                    cats_row_str = ""
            except IndexError:
                pass

    async def is_cat_in_action(self, cat_name: str) -> bool:
        """ Проверка кота на действие (потереться носом о нос и отменить действие)
         result = True -> кот занят действием """

        selector = await self.locate_element(xpath="//*[@id='mit']")
        dropdown_object = Select(selector)

        options_list = selector.find_elements(By.XPATH, "//option")
        names_list = [i.text for i in options_list]
        if cat_name not in names_list:
            self.logger.error(f"Кота по имени {cat_name} нет рядом с вами!")
            return False

        dropdown_object.select_by_visible_text(cat_name)
        await wait_for(0.3)
        await self.click(xpath="//*[@id='mitok']")
        await wait_for(0.5)
        await self.click(xpath="//img[@src='actions/9.png']")
        await wait_for(1.5, 3)
        result = await self.click(xpath="//a[@id='cancel']")
        return result

    async def get_hist_list(self) -> list:
        hist = await self.locate_element("//span[@id='ist']")
        hist_list = hist.text.split(".")[:-1]
        return hist_list

    async def has_moves(self) -> bool:
        available_locations = await self.get_available_locations()
        return available_locations is None

    async def is_held(self) -> bool:
        cw3_message_element = await self.locate_element(
            xpath="/html/body/div[1]/table/tbody/tr[2]/td/div[@id='block_mess']")
        if not cw3_message_element:
            return False
        cw3_message = get_text(cw3_message_element)
        if " держит вас во рту" in cw3_message:
            cat_name = cw3_message.split(" держит вас во рту")[0]
            href = self.get_cat_link(cat_name)
            self.logger.warning(f"ВАС ПОДНЯЛ ИГРОК ПО ИМЕНИ {cat_name}! Ссылка на профиль: {href}")
            await self.play_sound()
            return True
        return False

    async def get_cat_link(self, cat_name) -> str:
        """ Получить ссылку на кота по его имени (в Игровой) """
        cat_element = await self.locate_element(f"//span[@class='cat_tooltip']/u/a[text()='{cat_name}']")
        if not cat_element:
            return "N/A"
        href = "catwar.net" + cat_element.get_attribute("href")
        return href

    async def get_current_location(self) -> str:
        """ Получить название локации, на которой находится игрок """
        current_location = "[ Загружается… ]"
        while current_location == "[ Загружается… ]":
            location_element = await self.locate_element("/html/body/div[1]/table/tbody/tr[7]/td/"
                                                   "table/tbody/tr/td[2]/div/div/span")
            current_location = get_text(location_element)
            await wait_for(0.5)
        return current_location

    async def get_inv_items(self) -> list:
        """ Получить список id изображений всех предметов в инвентаре """

        inv_elements = await self.locate_elements("//div[@class='itemInMouth']/img")
        inv_ids = []
        for element in inv_elements:
            style_str = element.get_attribute("src")
            inv_ids.append(int(re.findall(pattern=r"things\/(\d*)", string=style_str)[0]))
        return inv_ids

    async def get_cages_list(self) -> list[Cage]:
        """ Получить список элементов всех клеток на поле """

        cages_list = [Cage(self, row, column) for column in range(1, 11) for row in range(1, 7)]
        return cages_list

    async def get_move_coords(self, loc_name) -> tuple:
        cages = await self.get_cages_list()
        for cage in cages:
            move_name = cage.get_move_name()
            if move_name == loc_name:
                return cage.row, cage.column
        return -1, -1

    async def find_cat_on_loc(self, names_to_find) -> tuple:
        """ Найти кота на текущей локации по имени или ID """

        cages_list = await self.get_cages_list()
        for cage in cages_list:
            cat_name = cage.get_cat_name()
            cat_id = cage.get_cat_id()
            if cat_name in names_to_find:
                location = self.get_current_location()
                return cat_name, location, cage.row, cage.column
            elif cat_id in names_to_find:
                location = self.get_current_location()
                return cat_id, location, cage.row, cage.column
        return False, False, False, False

    def get_weight(self):
        pass
