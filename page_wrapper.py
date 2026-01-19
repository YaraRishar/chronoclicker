import datetime
import random
import re
from asyncio import CancelledError
from logging import Logger

from playwright.async_api import Page, expect

import clicker_utils
from cage_utils import Cage
from clicker_utils import SettingsManager, get_text


class PageWrapper:
    def __init__(self, page: Page, settings_manager: SettingsManager):
        self._page = page
        self.logger: Logger = settings_manager.get_logger()
        self.settings: dict = settings_manager.get_settings()
        self.gamedata: dict = settings_manager.get_gamedata()

        self.action_dict = self.gamedata["actions"]
        self.parameters_dict = self.gamedata["parameters"]
        self.skills_dict = self.gamedata["skills"]

    @property
    def page(self) -> Page:
        return self._page

    async def goto(self, title: str):
        await self._page.goto(title)

    async def go_back(self):
        await self._page.go_back()

    async def refresh(self):
        await self._page.reload()

    async def press_keys(self, key: str):
        await self._page.keyboard.press(key)

    def get_url(self):
        return self._page.url

    async def accept_popup(self):
        self._page.on('dialog', lambda dialog: dialog.accept())

    async def locate_element(self, xpath: str, timeout: float | int = 0.5):
        element = self._page.locator(f"xpath={xpath}")
        try:
            await expect(element).to_be_enabled(timeout=timeout * 1000)
            return element
        except AssertionError:
            return None

    async def locate_elements(self, xpath: str, timeout: float | int = 2):
        elements = await self._page.locator(f"xpath={xpath}").all()
        for element in elements:
            try:
                await expect(element).to_be_enabled(timeout=timeout * 1000)
            except AssertionError:
                return None
        return elements

    async def spoof_plugins(self, count=5):
        await self._page.add_init_script("delete Object.getPrototypeOf(navigator).webdriver")
        plugins_array = ','.join(str(i) for i in range(count))
        await self._page.add_init_script(
            'Object.defineProperty('
            'Object.getPrototypeOf(navigator),'
            '"plugins",'
            '{get() {return [' + plugins_array + ']}})')

    async def click_element(self, xpath: str, random_offset=(0, 0), timeout=1) -> bool:
        element = await self.locate_element(xpath, timeout)
        if element is None:
            return False

        try:
            await element.scroll_into_view_if_needed(timeout=timeout * 1000)
            bb = await element.bounding_box(timeout=timeout * 1000)
        except TimeoutError:
            return False
        center = (bb["x"] + bb["width"] // 2, bb["y"] + bb["height"] // 2)
        x = center[0] + random.randint(-random_offset[0], random_offset[0])
        y = center[1] + random.randint(-random_offset[1], random_offset[1])
        await self._page.mouse.click(x, y)
        return True

    async def get_available_locations(self) -> list:
        elements = await self.locate_elements(xpath="//span[@class='move_name']")
        return await clicker_utils.get_text_from_elements(elements)

    async def mouse_over(self, xpath: str, hover_for=0.1) -> bool:
        """ Передвинуть курсор к элементу по xpath """

        element = await self.locate_element(xpath)
        if not element or not await element.is_visible():
            return False
        await element.hover()
        await self.wait_silent(hover_for)
        return True

    async def check_skill(self, skill_name_server, skill_name) -> str:
        """ Проверить уровень и дробь навыка """

        await self.mouse_over(xpath=f"//div[@id='{skill_name_server}']",
                              hover_for=random.uniform(0.1, 0.2))
        skill_name = skill_name[0].upper() + skill_name[1:]
        xpath = f"//div[@class='tooltip-inner' and contains(text(), '{skill_name}')]"
        tooltip_elem = await self.locate_element(xpath=xpath)
        text = await get_text(tooltip_elem) if tooltip_elem else ""
        level_elem = await self.locate_element(
            f"//div[@id='{skill_name_server}']/div[3]", timeout=0.5)
        if not level_elem:
            return ""
        await self.mouse_over(f"//div[@id='{skill_name_server}']", hover_for=0.01)
        return text + ", уровень " + await get_text(level_elem)

    async def wait_silent(self, start: float|int,
                          end: float|int=0.0, do_random=True):
        start *= 1000
        end *= 1000
        if not do_random:
            await self.wait_for_timeout(start)
            return
        if end == 0:
            end = start + start / 10
        seconds = random.uniform(start, end)
        await self.wait_for_timeout(seconds)


    async def wait_for_timeout(self, seconds: int | float):
        try:
            await self._page.wait_for_timeout(seconds)
        except CancelledError:
            await self._page.close()
            self.logger.info("Кликер выключается...")


    async def login_sequence(self, mail: str, password: str):
        mail_xpath = "//input[@id='mail']"
        password_xpath = "//input[@id='pass']"
        login_xpath = "//input[@value='Войти']"

        await self.type_in_chat(mail, mail_xpath, type_speed_coeff=0.01)
        await self.type_in_chat(password, password_xpath, type_speed_coeff=0.01)

        await self.click_element(login_xpath)

    async def type_in_chat(self, text: str, entry_xpath: str,
                           type_speed_coeff=1.0):
        """ Написать сообщение в чат (занимает реалистичное количество времени на набор текста) """

        text = [i for i in text]
        await self.click_element(entry_xpath)
        # await self.press_keys("Ctrl+A")
        # await self.press_keys("Delete")
        for i in range(len(text)):
            await self._page.keyboard.type(text[i])
            if text[i - 1] == text[i]:
                await self.wait_silent(0, 0.1 * type_speed_coeff)
                continue
            await self.wait_silent(0.05 * type_speed_coeff, 0.5 * type_speed_coeff)
        if len(text) < 5:
            await self.wait_silent(0.5, 1.5)

    async def is_held(self) -> bool:
        cw3_message_element = await self.locate_element(
            xpath="/html/body/div[1]/table/tbody/tr[2]/td/div[@id='block_mess']")
        if not cw3_message_element:
            return False
        cw3_message = await clicker_utils.get_text(cw3_message_element)
        if " держит вас во рту" in cw3_message:
            cat_name = cw3_message.split(" держит вас во рту")[0]
            href = self.get_cat_link(cat_name)
            self.logger.warning(f"ВАС ПОДНЯЛ ИГРОК ПО ИМЕНИ {cat_name}! Ссылка на профиль: {href}")
            # await self.play_sound()
            return True
        return False

    async def get_cat_link(self, cat_name: str) -> str:
        """ Получить ссылку на кота по его имени (в Игровой) """
        cat_element = await self.locate_element(f"//span[@class='cat_tooltip']/u/a[text()='{cat_name}']")
        if not cat_element:
            return "N/A"
        catwar_url = self.settings["catwar_url"].replace("https://", "")
        href = catwar_url + cat_element.get_attribute("href")
        return href


    async def get_time_with_break(self) -> int | float:
        seconds_until_end = await self.check_time()
        if not seconds_until_end:
            return 0
        if random.random() < self.settings["long_break_chance"]:
            added_seconds = random.uniform(self.settings["long_break_duration"][0],
                                           self.settings["long_break_duration"][1])
        else:
            added_seconds = random.uniform(self.settings["short_break_duration"][0],
                                           self.settings["short_break_duration"][1])
        seconds = seconds_until_end + added_seconds
        return seconds


    async def print_timer(self, seconds: int|float, console_string=None):
        """ Печатать таймер длительностью seconds с подписью console_string """

        if seconds == 1:
            return

        if console_string is None:
            message = await self.get_action_str()
            console_string = re.sub(r"(\d*) мин", f"{seconds // 60} мин", message)
            console_string = re.sub(r"(\d*) с", f"{seconds % 60} с", console_string)
            self.logger.info(console_string)
        else:
            self.logger.info(f"{console_string}. Осталось {round(seconds // 60)} мин {round(seconds % 60)} с.")

        await self.wait_silent(seconds, do_random=False)
        # if console_string is None:
        #     try:
        #         message = await self.get_action_str()
        #         for i in range(round(seconds), -1, -1):
        #             console_string = re.sub(r"(\d*) мин", f"{i // 60} мин", message)
        #             console_string = re.sub(r"(\d*) с", f"{i % 60} с", console_string)
        #
        #             sys.stdout.write(f"\r{console_string}")
        #             sys.stdout.flush()
        #             await self.wait_silent(1, do_random=False)
        #         sys.stdout.write("\n")
        #     except KeyboardInterrupt:
        #         return
        # else:
        #     try:
        #         for i in range(round(seconds), -1, -1):
        #             sys.stdout.write(f"\r{console_string}. Осталось {i // 60} мин {i % 60} с.")
        #             sys.stdout.flush()
        #             await self.wait_silent(1, do_random=False)
        #         sys.stdout.write("\n")
        #     except KeyboardInterrupt:
        #         return


    async def move_to_location(self, location_name: str, gui) -> bool:
        seconds = await self.get_time_with_break()
        await gui.print_timer(seconds, console_string="Какое-то действие уже выполняется")
        # current_loc = await self.get_current_location()
        try:
            path = f"//span[text()='{location_name}' and @class='move_name']/preceding-sibling::*"
            await self.click_element( xpath=path, random_offset=(40, 70))

            now = datetime.datetime.now()
            # move_time = now.strftime("%H:%M:%S")

            seconds = await self.get_time_with_break()
            await gui.print_timer(seconds, console_string=f"Совершается переход на {location_name}")
            return True
        except AssertionError:
            self.logger.error(f"Ожидалась локация {location_name}, не найдена")
            return False


    async def get_cats_list(self) -> list:
        elements = await self.locate_elements(xpath="//span[@class='cat_tooltip']/u/a")
        return await clicker_utils.get_text_from_elements(elements)

    async def is_action_active(self) -> bool:
        """ Проверка на выполнение действия """

        element = await self.locate_element(xpath="//a[@id='cancel']", timeout=1)
        return element is not None

    async def get_inv_items(self) -> list:
        """ Получить список id изображений всех предметов в инвентаре """

        inv_elements = await self.locate_elements("//div[@class='itemInMouth']/img")
        inv_ids = []
        for element in inv_elements:
            style_str = await element.get_attribute("src")
            inv_ids.append(int(re.findall(pattern=r"things\/(\d*)", string=style_str)[0]))
        return inv_ids

    async def print_cats(self):
        """ Вывести список игроков на одной локации с вами """

        cages: list = []
        for row in range(1, 7):
            for column in range(1, 11):
                xpath = f"//table[@id='cages']/tbody/tr[{row}]/td[{column}]/div//span[@class='cat_tooltip']/u/a"
                element = await self.locate_element(xpath, timeout=0.01)
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
                    temp_row: int = cages[i + 1][0]
                    self.logger.info(cats_row_str)
                    cats_row_str = ""
            except IndexError:
                pass


    async def get_text(self, xpath: str) -> str:
        try:
            element = await self.locate_element(xpath)
            if element is not None:
                return await self._page.text_content(f"xpath={xpath}", timeout=500)
            return ""
        except TimeoutError:
            self.logger.error(f"Достигнут таймаут во время поиска элемента по адресу {xpath}")
            return ""


    async def check_time(self) -> int:
        message = await self.get_text("//div[@id='block_mess']")
        if not message:
            return 0

        match_seconds = re.search(r"(\d*) мин (\d*) с", message)
        if not match_seconds:
            match_seconds = re.search(r"(\d*) с", message)
            seconds = int(match_seconds[1])
        else:
            seconds = int(match_seconds[1]) * 60 + int(match_seconds[2])
        return seconds


    async def get_action_str(self):
        message = await self.get_text("//div[@id='block_mess']")
        if not message:
            return "Действие не выполняется"
        message = message.replace("Отменить", "")
        return message.strip()


    async def get_current_location(self):
        """ Получить название локации, на которой находится игрок """
        current_location = "[ Загружается… ]"
        while current_location == "[ Загружается… ]":
            current_location = await self.get_text("/html/body/div[1]/table/tbody/"
                                                    "tr[7]/td/table/tbody/tr/td[2]/div/div/span")
            await self.wait_silent(0.3)
        return current_location


    async def get_hist_list(self) -> list:
        hist_text = await self.get_text(xpath="//span[@id='ist']")
        hist_list = hist_text.split(".")[:-1]
        return hist_list


    async def get_parameter(self, param_name) -> float | int:
        """ Проверить параметр param_name, вернуть его значение в процентах """

        xpath = f"//div[@id='{param_name}']/div[@class='bar']/div[@class='bar-data']"
        element = await self.locate_element(xpath)
        if not element:
            return -1
        percents = re.search(r": (\d*)%", await self.get_text(xpath))
        return percents[1]


    async def get_available_actions(self) -> list:
        """ Получить список доступных в данный момент действий """

        elements = await self.locate_elements(xpath="//div/a[@class='dey has-tooltip']")
        actions_list = []
        for element in elements:
            for key, value in self.action_dict.items():
                if await element.get_attribute("data-id") == value:
                    actions_list.append(key)
                    break
                elif "hunt" in await element.get_attribute("data-id"):
                    actions_list.append("охота")
                    break
        if not actions_list:
            return ["нет"]
        return actions_list


    async def check_smell_timer(self) -> int:
        await self.click_element(xpath="//div[@id='smell']/div[1]")
        await self.wait_silent(0.1, 0.2)
        timer_text = await self.get_warning_text()
        if "Время прошло" in timer_text:
            return 0
        match_seconds = re.search(
            r"(\d*) мин (\d*) с", timer_text)
        if not match_seconds:
            match_seconds = re.search(r"(\d*) с", timer_text)
            seconds = int(match_seconds[1])
        else:
            seconds = int(match_seconds[1]) * 60 + int(match_seconds[2])
        return seconds

    async def get_warning_text(self) -> str:
        xpath = "//p[@id='error']"
        warning_element = await self.locate_element(xpath=xpath)
        warning_style = warning_element.get_attribute("style")
        has_warning = bool("block" in warning_style)
        if has_warning:
            warning_text = await self.get_text(xpath)
            return warning_text
        return ""

    async def find_cat_on_loc(self, names_to_find) -> tuple:
        """ Найти кота на текущей локации по имени или ID """

        cages_list = await self.get_cages_list()
        for cage in cages_list:
            cat_name = await cage.get_cat_name()
            cat_id = await cage.get_cat_id()
            if cat_name in names_to_find:
                location = await self.get_current_location()
                return cat_name, location, cage.row, cage.column
            elif cat_id in names_to_find:
                location = await self.get_current_location()
                return cat_id, location, cage.row, cage.column
        return False, False, False, False

    async def get_cages_list(self, coords_list=None) -> list[Cage]:
        """ Получить список элементов всех клеток на поле либо
        превратить список координат в список клеток """

        if coords_list is None:
            cages_list = [Cage(self, row, column) for column in range(1, 11) for row in range(1, 7)]
            return cages_list
        cages_list = []
        for row, column in coords_list:
            cages_list.append(Cage(self, row, column))
        return cages_list

    async def rabbit_game(self, lower_bound=-9999999999,
                          upper_bound=9999999999) -> bool:
        """ Игра в числа """

        last_message = ""
        while "это" not in last_message:
            await self.wait_silent(0.8, 1.5)
            guess = (upper_bound + lower_bound) // 2

            await self.type_in_chat(text=f"/number {guess}", entry_xpath="//div[@id='mess']")
            await self.click_element(xpath="//input[@id='mess_submit']")

            await self.wait_silent(1.5, 3)
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

    async def get_last_message(self) -> str:
        """ Получить последнее отправленное сообщение из текущей вкладки чата (не в игровой!) """

        last_message_element = await self.locate_element(xpath="//div[@class='mess_div']/div[@class='parsed']")
        last_message = get_text(last_message_element)
        while not bool(last_message):
            await self.refresh()
            await self.wait_silent(0.5)
            last_message = await self.get_last_message()

        return last_message

    async def count_cw3_messages(self) -> int:
        # todo
        self.logger.info("not implemented yet :( returning 0")
        return 0

        # chatbox = await self.locate_element("//div[@id='chat_msg']")
        # msg_list = chatbox.find_elements(By.XPATH, value="//span/table/tbody/tr/td/span")
        # return len(msg_list)

    async def do_action_with_cat(self, cat_name: str):
        # todo
        self.logger.info("not implemented yet :(")

        # cat_pos = await self.find_cat_on_loc([cat_name])
        # cat_pos = cat_pos[2], cat_pos[3]
        # nearest_to_cat = clicker_utils.get_nearest_cages(cat_pos)
        # can_jump_to_cat = False
        # cages_list = await self.get_cages_list(coords_list=nearest_to_cat)
        # random.shuffle(cages_list)
        # for cage in cages_list:
        #     if not (await cage.has_cat() or await cage.is_move()):
        #         await cage.jump()
        #         can_jump_to_cat = True
        #         break
        # if not can_jump_to_cat:
        #     self.logger.error(f"Рядом с игроком по имени {cat_name} нет свободных клеток!")
        #     return
        # selector = await self.locate_element(xpath="//*[@id='mit']")
        # dropdown_object = Select(selector)
        # dropdown_object.select_by_visible_text(cat_name)
        # await self.wait_silent(0.8)

    async def is_cat_in_action(self, cat_name: str) -> bool:
        """ Проверка кота на действие (потереться носом о нос и отменить действие).
         Возвращает True, если кот занят действием """

        # todo
        self.logger.info("not implemented yet :(")
        return False

        # selector = await self.locate_element(xpath="//*[@id='mit']")
        # dropdown_object = Select(selector)
        #
        # options_list = selector.find_elements(By.XPATH, "//option")
        # names_list = [i.text for i in options_list]
        # if cat_name not in names_list:
        #     self.logger.error(f"Кота по имени {cat_name} нет рядом с вами!")
        #     return False
        #
        # dropdown_object.select_by_visible_text(cat_name)
        # await self.wait_silent(0.3)
        # await self.click_element(xpath="//img[@src='actions/9.png']")
        # await self.wait_silent(1, 2)
        # result = await self.click_element(xpath="//a[@id='cancel']")
        # return not result



