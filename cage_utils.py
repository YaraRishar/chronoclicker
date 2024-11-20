import random
import re
import time


class Cage:
    def __init__(self, driver, row: int, column: int):
        row, column = int(row), int(column)
        if row not in range(1, 7) or column not in range(1, 11):
            print("Неверные координаты клетки!")
            return

        self.driver = driver

        self.row = row
        self.column = column
        self.items: [str] = ()
        self.has_move: bool = False
        self.move_name: str = ""
        self.cat_name: str = ""
        self.cat_id: str = ""
        self.cat_rank: str = ""
        self.cat_smell: int = -1
        self.cat_items: [str] = ()
        self.cat_status: str = ""
        self.cat_color_url: str = ""
        self.cat_size: int = -1

    def get_items(self) -> list:
        item_ids = []
        cage_element = self.driver.locate_element(xpath=f"//*[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/div",
                                                  do_wait=False)
        style_str = cage_element.get_attribute("style")
        try:
            item_ids.append(re.findall(pattern=r"things\/(\d*)", string=style_str))
        except IndexError:
            return []
        item_ids = [int(i) for i in item_ids[0]]
        return item_ids

    def is_move(self) -> bool:
        xpath = (f"//*[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/"
                 f"div/span[@class='move_parent']/span[@class='move_name']")
        cage_element = self.driver.locate_element(xpath=xpath, do_wait=False)
        return bool(cage_element)

    def has_cat(self) -> bool:
        cat = self.driver.locate_element(xpath=f"//*[@id='cages']/tbody/tr[{self.row}]/"
                                               f"td[{self.column}]/div/span[@class='catWithArrow']", do_wait=False)
        return bool(cat)

    def get_cat_name(self) -> str:
        xpath = f"//table[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/div/span/span/span/u/a"
        element = self.driver.locate_element(xpath=xpath, do_wait=False)
        if not element:
            return ""
        cat_name = element.get_attribute(name="innerText")
        return cat_name

    def get_cat_rank(self) -> str:
        xpath = (f"//table[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/"
                 f"div/span/span/span[@class='cat_tooltip']/div/small/i")
        rank = self.driver.locate_element(xpath=xpath)
        rank = rank.get_attribute("innerText")
        return rank

    def get_cat_smell(self) -> int:
        smell = self.driver.locate_element(xpath=f"//table[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/div"
                                                 f"/span/span/span[@class='cat_tooltip']/img")
        cat_smell = re.findall(pattern=r"odoroj\/(\d+).png", string=smell.get_attribute("src"))[0]
        cat_smell = int(cat_smell)
        return cat_smell

    def get_cat_items(self) -> list:
        items = self.driver.locate_elements(xpath=f"//table[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/div"
                                                  f"/span/span/span[@class='cat_tooltip']/ol/li/img", do_wait=False)
        item_ids = []
        for element in items:
            item_ids.append(int(re.findall(pattern=r"things\/(\d*)", string=element.get_attribute("src"))[0]))
        return item_ids

    def get_cat_status(self) -> str:
        status_element = self.driver.locate_element(xpath=f"//table[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]"
                                                          f"/div/span/span/span/span/font")
        status = status_element.get_attribute("innerText")
        return status

    def get_cat_color_url(self) -> str:
        xpath = f"//table[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/div/span/span/div/div"
        element = self.driver.locate_element(xpath=xpath)
        style_str = element.get_attribute("style")
        url = re.findall(pattern=r'url\(\"(.*?)\.png', string=style_str)[0]
        url = "https://catwar.net/" + url + ".png"
        return url

    def get_cat_size(self) -> int:
        xpath = f"//table[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/div/span/span/div/div"
        element = self.driver.locate_element(xpath=xpath)
        style_str = element.get_attribute("style")
        size = re.findall(pattern=r'background-size: (\d+)%;', string=style_str)[0]
        return size

    def get_cat_id(self):
        xpath = f"//table[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/div/span/span/span/u/a"
        element = self.driver.locate_element(xpath=xpath)
        if not element:
            return ""
        cat_id: str = element.get_attribute(name="href")
        cat_id = cat_id.replace("https://catwar.net/cat", "")
        return cat_id

    def get_move_name(self) -> str:
        xpath = f"//table[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/div/span/span[@class='move_name']"
        move_name = self.driver.locate_element(xpath=xpath).text
        return move_name

    def pretty_print(self):
        self.cat_name = self.get_cat_name()
        self.items = self.get_items()
        print(f"{self.row} ряд, {self.column} клетка")
        if self.is_move():
            self.move_name = self.get_move_name()
            print(f"Переход на локацию {self.move_name}")
            return
        if self.items:
            items_string = [f"https://catwar.net/cw3/things/{i}.png" for i in self.items]
            print(f"Предметы на клетке: {", ".join(items_string)}")
        if self.cat_name:
            self.cat_rank = self.get_cat_rank()
            self.cat_status = self.get_cat_status()
            self.cat_size = self.get_cat_size()
            self.cat_color_url = self.get_cat_color_url()
            self.cat_id = self.get_cat_id()
            print(f"{self.cat_name} ({self.cat_id}): {self.cat_rank} | {self.cat_status}\n"
                  f"Рост: {self.cat_size}%, ссылка на окрас: {self.cat_color_url}")
            self.cat_items = self.get_cat_items()
            if self.cat_items:
                items_string = [f"https://catwar.net/cw3/things/{i}.png" for i in self.cat_items]
                print(f"Предметы во рту: {", ".join(items_string)}")

    def jump(self):
        if self.has_cat():
            print(f"Клетка {self.row}x{self.column} занята котом по имени {self.cat_name}!")
            return
        elif self.has_move:
            location_name = self.move_name
            self.driver.move_to_location(location_name, show_availibles=True)
            return
        self.driver.click(xpath=f"//*[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]", offset_range=(40, 70))

    def pick_up_item(self) -> bool:
        old_inv = self.driver.get_inv_items()
        self.driver.click(xpath="//td[@class='cage']/div[@class='cage_items' and not(*) and not(@style)]/..",
                          offset_range=(40, 70))
        cage_items = self.get_items()
        if not cage_items:
            print(f"На клетке {self.row}x{self.column} нет предметов!")
            return False
        if self.has_cat():
            print(f"Клетка {self.row}x{self.column} занята котом по имени {self.cat_name}!")
            return False
        if self.is_move():
            self.move_name = self.get_move_name()
            print(f"Клетка {self.row}x{self.column} занята переходом на локацию {self.move_name}!")
            return False
        time.sleep(random.uniform(0.3, 1))
        self.jump()
        new_inv = self.driver.get_inv_items()
        if new_inv == old_inv:
            print(f"Не удалось подобрать предмет с клетки {self.row}x{self.column}!")
            return False
        print("Предмет подобран! Предметы во рту:")
        for i in new_inv:
            print(f"https://catwar.net/cw3/things/{i}.png")
        return True
