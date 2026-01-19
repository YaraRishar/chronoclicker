import re
from clicker_utils import wait_for
# from page_wrapper import PageWrapper


class Cage:
    def __init__(self, page, row: int, column: int):
        self.page = page
        self.row = int(row)
        self.column = int(column)
        if self.row not in range(1, 7) or self.column not in range(1, 11):
            self.page.logger.info("Неверные координаты клетки!")
            return

        self.items = ()
        self.has_move: bool = False
        self.move_name: str = ""
        self.cat_name: str = ""
        self.cat_id: str = ""
        self.cat_rank: str = ""
        self.cat_smell: int = -1
        self.cat_items = ()
        self.cat_status: str = ""
        self.cat_color_url: str = ""
        self.cat_size: int = -1

    async def get_items(self) -> list:
        item_ids = []
        cage_element = await self.page.locate_element(
            xpath=f"//*[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/div")
        style_str = cage_element.get_attribute("style")
        try:
            item_ids.append(re.findall(pattern=r"things\/(\d*)", string=style_str))
        except IndexError:
            return []
        item_ids = [int(i) for i in item_ids[0]]
        return item_ids

    async def is_move(self) -> bool:
        xpath = (f"//*[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/"
                 f"div/span[@class='move_parent']/span[@class='move_name']")
        cage_element = await self.page.locate_element(xpath=xpath)
        return bool(cage_element)

    async def has_cat(self) -> bool:
        cat = await self.page.locate_element(f"//*[@id='cages']/tbody/tr[{self.row}]/"
                                               f"td[{self.column}]/div/span[@class='catWithArrow']")
        return bool(cat)

    async def get_cat_name(self) -> str:
        xpath = f"//table[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/div/span/span/span/u/a"
        element = await self.page.locate_element(xpath=xpath)
        if not element:
            return ""
        cat_name = element.get_attribute(name="innerText")
        return cat_name

    async def get_cat_rank(self) -> str:
        xpath = (f"//table[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/"
                 f"div/span/span/span[@class='cat_tooltip']/div/small/i")
        rank = await self.page.locate_element(xpath=xpath)
        rank = rank.get_attribute("innerText")
        return rank

    async def get_cat_smell(self) -> int:
        smell = await self.page.locate_element(f"//table[@id='cages']/tbody/tr[{self.row}]/"
                                                 f"td[{self.column}]/div/span/span/"
                                                 f"span[@class='cat_tooltip']/img")
        cat_smell = re.findall(pattern=r"odoroj\/(\d+).png", string=smell.get_attribute("src"))[0]
        cat_smell = int(cat_smell)
        return cat_smell

    async def get_cat_items(self) -> list:
        items = await self.page.locate_elements(f"//table[@id='cages']/tbody/"
                                                  f"tr[{self.row}]/td[{self.column}]/div/"
                                                  f"span/span/span[@class='cat_tooltip']/ol/li/img")
        item_ids = []
        for element in items:
            item_ids.append(int(re.findall(pattern=r"things\/(\d*)", string=element.get_attribute("src"))[0]))
        return item_ids

    async def get_cat_status(self) -> str:
        status_element = await self.page.locate_element(f"//table[@id='cages']/tbody/tr[{self.row}]/"
                                                    f"td[{self.column}]/div/span/span/span/span/font")
        status = status_element.get_attribute("innerText")
        return status

    async def get_cat_color_url(self) -> str:
        xpath = f"//table[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/div/span/span/div/div"
        element = await self.page.locate_element(xpath=xpath)
        style_str = element.get_attribute("style")
        url = re.findall(pattern=r'url\(\"(.*?)\.png', string=style_str)[0]
        url = self.page.settings["catwar_url"] + url + ".png"
        return url

    async def get_cat_size(self) -> int:
        xpath = f"//table[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/div/span/span/div/div"
        element = await self.page.locate_element(xpath=xpath)
        style_str = element.get_attribute("style")
        size = re.findall(pattern=r'background-size: (\d+)%;', string=style_str)[0]
        return size

    async def get_cat_id(self):
        xpath = f"//table[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/div/span/span/span/u/a"
        element = await self.page.locate_element(xpath=xpath)
        if not element:
            return ""
        cat_id: str = element.get_attribute(name="href")
        cat_id = "".join([i for i in cat_id if i.isdigit()])
        return cat_id

    async def get_move_name(self) -> str:
        xpath = f"//table[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/div/span/span[@class='move_name']"
        move_element = await self.page.locate_element(xpath=xpath)
        move_name = move_element.text
        return move_name

    async def pretty_print(self):
        self.cat_name = await self.get_cat_name()
        self.items = await self.get_items()
        self.page.logger.info(f"{self.row} ряд, {self.column} клетка")
        if await self.is_move():
            self.move_name = await self.get_move_name()
            self.page.logger.info(f"Переход на локацию {self.move_name}")
            return
        if self.items:
            items_string = [f"{self.page.settings['catwar_url']}/cw3/things/{i}.png" for i in self.items]
            self.page.logger.info(f"Предметы на клетке: {", ".join(items_string)}")
        if self.cat_name:
            self.cat_rank = await self.get_cat_rank()
            self.cat_status = await self.get_cat_status()
            self.cat_size = await self.get_cat_size()
            self.cat_color_url = await self.get_cat_color_url()
            self.cat_id = await self.get_cat_id()
            self.page.logger.info(f"{self.cat_name} ({self.cat_id}): {self.cat_rank} | {self.cat_status}\n"
                  f"Рост: {self.cat_size}%, ссылка на окрас: {self.cat_color_url}")
            self.cat_items = await self.get_cat_items()
            if self.cat_items:
                items_string = [f"{self.page.settings['catwar_url']}/cw3/things/{i}.png" for i in self.cat_items]
                self.page.logger.info(f"Предметы во рту: {", ".join(items_string)}")

    async def jump(self) -> bool:
        if await self.has_cat():
            cat_name = await self.get_cat_name()
            self.page.logger.info(f"Клетка {self.row}x{self.column} занята котом по имени "
                                    f"{cat_name}!")
            return False
        await self.page.click_element(xpath=f"//*[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]",
                                random_offset=(40, 70))
        return True

    async def pick_up_item(self) -> bool:
        old_inv = await self.page.get_inv_items()
        await self.page.click_element(
            xpath="//td[@class='cage']/div[@class='cage_items' and not(*) and not(@style)]/..",
            random_offset=(40, 70))
        cage_items = self.get_items()
        if not cage_items:
            self.page.logger.info(f"На клетке {self.row}x{self.column} нет предметов!")
            return False
        if self.has_cat():
            self.page.logger.info(f"Клетка {self.row}x{self.column} занята котом по имени {self.cat_name}!")
            return False
        if self.is_move():
            self.move_name = await self.get_move_name()
            self.page.logger.info(f"Клетка {self.row}x{self.column} занята переходом на локацию {self.move_name}!")
            return False
        await wait_for(0.3, 1)
        await self.jump()
        new_inv = await self.page.get_inv_items()
        if new_inv == old_inv:
            self.page.logger.info(f"Не удалось подобрать предмет с клетки {self.row}x{self.column}!")
            return False
        self.page.logger.info("Предмет подобран! Предметы во рту:")
        for i in new_inv:
            self.page.logger.info(f"{self.page.settings['catwar_url']}/cw3/things/{i}.png")
        return True
