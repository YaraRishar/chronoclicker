import time
import random
import re
import os.path
from urllib3.exceptions import ProtocolError
import browser_navigation
import clicker_utils


def repeat(args=None):
    """Команда для бесконечного повторения действий по списку из args. Использование:
    repeat действие1 - действие2 - действие3"""

    if not args or args == [""]:
        print("Для зацикленного действия нужны аргументы. Наберите help для вывода дополнительной информации.")
        return
    while True:
        do(args, show_avaliables=False)
        clicker_utils.trigger_long_break(long_break_chance=settings["long_break_chance"],
                                         long_break_duration=settings["long_break_duration"])


def do(args=None, show_avaliables=True):
    """Команда для исполнения последовательности действий 1 раз. Использование:
    do действие1 - действие2 - действие3"""

    if not args or args == [""]:
        print("Для действия нужны аргументы. Наберите help для вывода дополнительной информации.")
        return
    for action in args:
        availible_actions = driver.get_availible_actions(action_dict)
        if driver.is_action_active():
            action_active_sec = driver.check_time()
            print(f"Действие уже совершается! Чтобы отменить, введите cancel.\n"
                  f"(До окончания действия осталось {action_active_sec // 60} мин {action_active_sec % 60} сек)")
            if not show_avaliables:
                wait_for([action_active_sec, action_active_sec + driver.short_break_duration[1]])
            return
        if action not in availible_actions:
            print(f"Действие {action} не может быть выполнено. Возможно, действие недоступно/"
                  f"страница не прогрузилась до конца.\nДоступные действия: {', '.join(availible_actions)}.")
            continue
        success = driver.click(xpath=f"//a[@data-id={action_dict[action]}][@class='dey']/img",
                               offset_range=(30, 30))
        if success:
            seconds = driver.check_time() + random.uniform(settings["short_break_duration"][0],
                                                           settings["short_break_duration"][1])
            last_hist_entry = driver.locate_element("//span[@id='ist']").text.split(".")[-2]

            clicker_utils.print_timer(console_string=last_hist_entry, seconds=seconds)

            if action == "Принюхаться":
                print(driver.check_skill("smell"))
                driver.click(xpath="//input[@value='Вернуть поле']")
            elif action == "Копать землю":
                print(driver.check_skill("dig"))
            elif action == "Поплавать":
                print(driver.check_skill("swim"))

            if show_avaliables:
                print(f"Доступные действия: {', '.join(driver.get_availible_actions(action_dict))}")
        else:
            continue


def patrol(args=None):
    """Команда перехода, маршрут повторяется бесконечно
    (для маршрута из 3 локаций: 1 - 2 - 3 - 2 - 1 - 2 - 3 и так далее). Использование:
    patrol имя_локации1 - имя_локации2 - имя_локации3"""

    if not args or args == [""]:
        print("Для перехода нужны аргументы. Наберите help для вывода дополнительной информации.")
        return
    if len(args) == 1:
        while True:
            driver.move_to_location(args[0], show_availibles=False)
    index, direction = -1, 1
    while True:
        index, direction = clicker_utils.get_next_index(len(args), index, direction)
        success = driver.move_to_location(args[index], show_availibles=False)
        if not success:
            continue


def go(args=None):
    """Команда перехода, маршрут проходится один раз. Использование:
    go имя_локации1 - имя_локации2 - имя_локации3"""

    if not args or args == [""]:
        print("Для перехода нужны аргументы. Наберите help для вывода дополнительной информации.")
        return
    for index in range(len(args)):
        success = driver.move_to_location(args[index], show_availibles=True)
        if not success:
            continue


def start_rabbit_game():
    """ Начать игру в числа с Лапом, после 5 игр вернуться в cw3. Использование:
     rabbit_game"""

    driver.get("https://catwar.su/chat")
    time.sleep(random.uniform(1, 3))
    driver.click(xpath="//a[@data-bind='openPrivateWith_form']")
    driver.type_in_chat("Системолап", entry_xpath="//input[@id='openPrivateWith']")
    driver.click(xpath="//*[@id='openPrivateWith_form']/p/input[2]")  # OK button

    games_played = 0
    while games_played != 5:
        driver.rabbit_game()
        games_played += 1
    driver.get("https://catwar.su/cw3/")


def info():
    """Команда для вывода информации о состоянии игрока из Игровой. Использование:
    info"""

    current_location = driver.locate_element("//span[@id='location']").text
    while current_location == "[ Загружается… ]":
        current_location = driver.locate_element("//span[@id='location']").text

    print(f"Текущая локация: {current_location}\n"
          f"Доступные локации: {', '.join(driver.get_availible_locations())}\n"
          f"Доступные действия: {', '.join(driver.get_availible_actions(action_dict))}")
    driver.print_cats()
    print(f"\t Сонливость:\t{driver.check_parameter('dream')}%\n"
          f"\t Голод:\t\t{driver.check_parameter('hunger')}%\n"
          f"\t Жажда:\t\t{driver.check_parameter('thirst')}%\n"
          f"\t Нужда:\t\t{driver.check_parameter('need')}%\n"
          f"\t Здоровье:\t{driver.check_parameter('health')}%\n"
          f"\t Чистота: \t{driver.check_parameter('clean')}%")
    print("Последние 5 записей в истории (введите hist, чтобы посмотреть полную историю):")
    hist_list = driver.get_hist_list()
    print(f"\t{'.\n\t'.join(hist_list[-6:])}.")


def char():
    """ Команда для вывода информации о персонаже с домашней страницы/Игровой. Использование:
    char """

    driver.get("https://catwar.su/")
    rank = driver.locate_element('''//div[@id='pr']/i''', do_wait=False)

    print(f"Имя: {driver.locate_element('''//div[@id='pr']/big''').text}")
    if rank:
        print(f"Должность: {rank.text}\n")
    print(f"Луны: {driver.locate_element('''//div[@id='pr']/table/tbody/tr[2]/td[2]/b''').text}\n"
          f"ID: {driver.locate_element('''//b[@id='id_val']''').text}\n"
          f"Активность: {driver.locate_element('''//div[@id='act_name']/b''').text}")
    driver.back()
    print(f"{driver.check_skill('smell')}\n"
          f"{driver.check_skill('dig')}\n"
          f"{driver.check_skill('swim')}\n"
          f"{driver.check_skill('might')}\n"
          f"{driver.check_skill('tree')}\n"
          f"{driver.check_skill('observ')}")


def hist():
    """Команда для вывода истории действий из Игровой, использование:
    hist"""

    print("История:")
    hist_list = driver.get_hist_list()
    for item in hist_list:
        print(item)


def clear_hist():
    """Команда 'очистить историю', использование:
    clear_hist"""

    driver.click(xpath="//a[@id='history_clean']")
    print("История очищена.")


def cancel() -> bool:
    """Отменить действие. Использование:
    cancel"""

    success = driver.click(xpath="//a[@id='cancel']")
    if success:
        print("Действие отменено!")
        return True
    print("Действие не выполняется!")
    return False


def swim(escape_to_location=None):
    """ Команда для плавания с отсыпом на соседней локации. Критическое количество пикселей сна (при
    котором начнётся отсып) указывается в настройках. Для справки:
    20 пикс. = ~43 минуты сна, 30 пикс. = ~40 минут сна. Считаются 'оставшиеся' зелёные пиксели.
    ВНИМАНИЕ: перед использованием этой команды проверьте на безопасной ПУ локации,
    работает ли она на вашем устройстве.
    Использование (находясь на локации с ПУ):
    swim локация_для_отсыпа """

    if not escape_to_location:
        repeat(["Поплавать"])
    availible_locations = driver.get_availible_locations()
    if escape_to_location[0] and escape_to_location[0] not in availible_locations:
        print("Для отсыпа введите название локации, соседней с плавательной!")
        return
    while True:
        sleep_pixels = driver.check_parameter("dream")
        print(f"Сон: {sleep_pixels} зелёных пикселей.")
        if sleep_pixels < settings["critical_sleep_pixels"]:
            current_location = driver.locate_element("//span[@id='location']").text
            go(escape_to_location)
            do(["Поспать"])
            go([current_location])
        do(["Поплавать"])


def create_alias(comm):
    """Команда для создания сокращений для часто используемых команд.
    Использование:
    alias name comm
    Пример:
    alias кач_актив patrol Морозная поляна - Поляна для отдыха
    В дальнейшем команда patrol Морозная поляна - Поляна для отдыха будет исполняться при вводе кач_актив"""

    try:
        main_alias_comm = comm.split(" ")[1]
    except IndexError:
        print("Ошибка в парсинге сокращения. Пример использования команды:"
              "\nalias кач_актив patrol Морозная поляна - Поляна для отдыха")
        return
    if main_alias_comm not in comm_dict.keys():
        print(f"Команда {main_alias_comm} не найдена, сокращение не было создано.")
        return
    name = comm.split(" ")[0]
    comm_to_alias = comm.replace(name + " ", "")
    config["aliases"][name] = comm_to_alias
    print(f"Создано сокращение команды {comm_to_alias} под именем {name}.")
    clicker_utils.rewrite_config(config)


def refresh():
    """Перезагрузить страницу"""

    driver.refresh()
    print("Страница обновлена!")


def change_settings(args=None):
    """Команда для изменения настроек. Использование:
    settings key - value
    (Пример: settings is_headless - True)"""

    if not args:
        print(config["settings"])
        return
    if len(args) != 2:
        print("Ошибка в парсинге аргумента.")
        return
    key, value = args
    try:
        if key == "is_headless" or key == "driver_path":
            config["settings"][key] = value
        else:
            config["settings"][key] = eval(value)
    except ValueError:
        print("Ошибка в парсинге аргумента.")
        return
    clicker_utils.rewrite_config(config)


def wait_for(seconds=None):
    """ Ничего не делать рандомное количество времени от seconds_start до seconds_end секунд
     seconds: list = [seconds_start, seconds_end]"""

    if not seconds or seconds == [""] or len(seconds) > 2:
        print("Введите количество секунд")
    try:
        seconds[0], seconds[1] = int(seconds[0]), int(seconds[1])
    except (IndexError, ValueError):
        print("wait seconds_from - seconds_to")
        return
    seconds: float = random.uniform(int(seconds[0]), int(seconds[1]))
    clicker_utils.print_timer(console_string="Начато ожидание", seconds=seconds)


def text_to_chat(message=None):
    """Написать сообщение в чат Игровой"""

    if message is None or len(message) != 1:
        print("say message")
        return
    message = message[0]
    driver.type_in_chat(text=message, entry_xpath="//input[@id='text']")
    driver.click(xpath="//*[@id='msg_send']")


def print_rabbits_balance():
    """ Вывести баланс кролей игрока """

    driver.get("https://catwar.su/rabbit")
    rabbit_balance = driver.locate_element(xpath="//img[@src='img/rabbit.png']/preceding-sibling::b").text
    wait_for([0.5, 1.5])
    driver.back()

    print("Кролей на счету:", rabbit_balance)


def get_inv_items() -> list:
    """ Получить список id изображений всех предметов в инвентаре """

    inv_elements = driver.locate_elements(xpath="//div[@class='itemInMouth']/img")
    inv_ids = []
    for element in inv_elements:
        style_str = element.get_attribute("src")
        inv_ids.append(int(re.findall(pattern=r"things\/(\d*)", string=style_str)[0]))
    return inv_ids


def print_inv():
    inv_ids = get_inv_items()
    print("Предметы во рту:")
    for i in inv_ids:
        print(f"https://catwar.su/cw3/things/{i}.png")


def end_session():
    """ Завершить текущую сессию и закрыть вебдрайвер. Использование:
     q """

    print("\nВебдрайвер закрывается...")
    driver.quit()


def print_readme():
    """ Вывести содержимое файла README.md или ссылку на него. Использование:
     help """

    if not os.path.exists("README.md"):
        print("Файла справки README.md не существует или он удалён.\n"
              "Справка на GitHub: https://github.com/YaraRishar/chronoclicker?tab=readme-ov-file#chronoclicker")
        return
    with open("README.md", "r", encoding="utf-8") as readme:
        for line in readme:
            print(line, end="")


def print_cage_info(args=()):
    """ Вывести всю информацию о клетке в Игровой """

    if not args or len(args) != 2:
        print("c row - column")
        return
    cage = Cage(row=args[0], column=args[1])
    cage.pretty_print()


def multi_comm_handler(multi_comm: str):
    """ Исполнить каждую команду в мультикоманде по очереди """

    if not multi_comm:
        return print("Введите команду! Пример: patrol Морозная поляна - Каменная гряда")
    elif multi_comm in alias_dict.keys():
        return multi_comm_handler(alias_dict[multi_comm])

    multi_comm_list: list = multi_comm.split("; ")
    first_word = multi_comm.split(" ")[0]
    if first_word == "alias":
        multi_comm = multi_comm.replace("alias ", "")
        return create_alias(multi_comm)
    for comm in multi_comm_list:
        comm_handler(comm)


def comm_handler(comm: str):
    """ Разделить ключевое слово команды и аргументы """

    try:
        main_comm = comm.split(" ")[0]
        comm = comm.replace(main_comm + " ", "")
        args = comm.split(" - ")
    except IndexError:
        return print("Ошибка в парсинге аргумента. Введите help для просмотра списка команд.")

    if main_comm == "alias":
        return create_alias(comm)
    if main_comm not in comm_dict.keys():
        return print("Команда не найдена. Наберите help для просмотра списка команд.")

    if comm == main_comm:
        return comm_dict[main_comm]()
    return comm_dict[main_comm](args)


def bury_handler(args=None):
    """ Закопать предмет с айди картинки id на глубину level:
    bury id - level
    Закопать все предметы во рту на глубину level:
    bury inv - level """

    if args is None or args == [""] or len(args) != 2:
        print("Чтобы закопать предмет, введите айди его картинки и глубину закапывания.")
        return
    try:
        level = 1 if len(args) == 1 else int(args[1])
        level = 9 if level > 9 else level
        item_img_id = args[0]
        if item_img_id != "inv":
            item_img_id = int(args[0])
    except ValueError:
        print("bury id_img - level или bury inv - level")
        return
    inv_items = get_inv_items()
    if item_img_id == "inv":
        for item in inv_items:
            driver.bury_item(item, level)
            return
    if item_img_id not in inv_items:
        print(f"Предмета с айди {item_img_id} нет в инвентаре! Ссылка на изображение: "
              f"https://catwar.su/cw3/things/{item_img_id}.png")
        return
    driver.bury_item(item_img_id, level)


class Cage:
    def __init__(self, row: int, column: int):
        row, column = int(row), int(column)
        if row not in range(1, 7) or column not in range(1, 11):
            print("Неверные координаты клетки!")
            return

        self.row = row
        self.column = column
        self.items: [str] = self.get_items()
        self.has_move: bool = self.is_move()
        self.move_name: str = ""
        if self.has_move:
            self.move_name: str = self.get_move_name()

        self.cat_name: str = ""
        self.cat_rank: str = ""
        self.cat_smell: int = -1
        self.cat_items: [str] = ()
        self.cat_status: str = ""
        self.cat_color_url: str = ""
        self.cat_size: int = -1

        if not self.is_move() and self.has_cat():
            self.cat_name: str = self.get_cat_name()
            self.cat_rank: str = self.get_cat_rank()
            self.cat_smell: int = self.get_cat_smell()
            self.cat_items: [str] = self.get_cat_items()
            self.cat_status: str = self.get_cat_status()
            self.cat_color_url: str = self.get_cat_color_url()
            self.cat_size: int = self.get_cat_size()

    def get_items(self) -> [str]:
        item_ids = []
        cage_element = driver.locate_element(xpath=f"//*[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/div",
                                             do_wait=False)
        style_str = cage_element.get_attribute("style")
        try:
            item_ids.append(re.findall(pattern=r"things\/(\d*)", string=style_str))
        except IndexError:
            return ()
        item_ids = [int(i) for i in item_ids[0]]
        return item_ids

    def is_move(self) -> bool:
        xpath = (f"//*[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/"
                 f"div/span[@class='move_parent']/span[@class='move_name']")
        cage_element = driver.locate_element(xpath=xpath, do_wait=False)
        return bool(cage_element)

    def has_cat(self) -> bool:
        cat = driver.locate_element(xpath=f"//*[@id='cages']/tbody/tr[{self.row}]/"
                                          f"td[{self.column}]/div/span[@class='catWithArrow']", do_wait=False)
        return bool(cat)

    def get_cat_name(self) -> str:
        element = driver.locate_element(xpath=f"//table[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]"
                                              f"/div/span/span/span[@class='cat_tooltip']/u/a")
        cat_name = element.get_attribute(name="innerText")
        return cat_name

    def get_cat_rank(self) -> str:
        xpath = (f"//table[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/"
                 f"div/span/span/span[@class='cat_tooltip']/div/small/i")
        rank = driver.locate_element(xpath=xpath)
        rank = rank.get_attribute("innerText")
        return rank

    def get_cat_smell(self) -> int:
        smell = driver.locate_element(xpath=f"//table[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/div"
                                            f"/span/span/span[@class='cat_tooltip']/img")
        cat_smell = re.findall(pattern=r"odoroj\/(\d+).png", string=smell.get_attribute("src"))[0]
        cat_smell = int(cat_smell)
        return cat_smell

    def get_cat_items(self) -> [str]:
        items = driver.locate_elements(xpath=f"//table[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/div"
                                             f"/span/span/span[@class='cat_tooltip']/ol/li/img", do_wait=False)
        item_ids = []
        for element in items:
            item_ids.append(int(re.findall(pattern=r"things\/(\d*)", string=element.get_attribute("src"))[0]))
        return item_ids

    def get_cat_status(self) -> str:
        status_element = driver.locate_element(xpath=f"//table[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]"
                                                     f"/div/span/span/span/span/font")
        status = status_element.get_attribute("innerText")
        return status

    def get_cat_color_url(self) -> str:
        xpath = f"//table[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/div/span/span/div/div"
        element = driver.locate_element(xpath=xpath)
        style_str = element.get_attribute("style")
        url = re.findall(pattern=r'url\(\"(.*?)\.png', string=style_str)[0]
        url = "https://catwar.su/" + url + ".png"
        return url

    def get_cat_size(self) -> int:
        xpath = f"//table[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/div/span/span/div/div"
        element = driver.locate_element(xpath=xpath)
        style_str = element.get_attribute("style")
        size = re.findall(pattern=r'background-size: (\d+)%;', string=style_str)[0]
        return size

    def get_move_name(self) -> str:
        xpath = f"//table[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]/div/span/span[@class='move_name']"
        move_name = driver.locate_element(xpath=xpath).text
        return move_name

    def pretty_print(self):
        print(f"{self.row} ряд, {self.column} клетка")
        if self.is_move():
            print(f"Переход на локацию {self.move_name}")
            return
        if self.items:
            items_string = [f"https://catwar.su/cw3/things/{i}.png" for i in self.items]
            print(f"Предметы на клетке: {", ".join(items_string)}")
        if self.cat_name:
            print(f"{self.cat_name}: {self.cat_rank} | {self.cat_status}\n"
                  f"Рост: {self.cat_size}%, ссылка на окрас: {self.cat_color_url}")
            if self.cat_items:
                items_string = [f"https://catwar.su/cw3/things/{i}.png" for i in self.cat_items]
                print(f"Предметы во рту: {", ".join(items_string)}")

    def jump(self):
        if self.has_cat():
            print(f"Клетка {self.row}x{self.column} занята котом по имени {self.cat_name}!")
            return
        elif self.has_move:
            location_name = self.move_name
            go([location_name])
            return
        driver.click(xpath=f"//*[@id='cages']/tbody/tr[{self.row}]/td[{self.column}]", offset_range=(40, 70))
        print(f"Прыжок на {self.row} ряд, {self.column} клетку.")


def jump_to_cage(args=None):
    if not args or len(args) != 2:
        print("jump row - column")
        return
    cage = Cage(row=args[0], column=args[1])
    cage.jump()


# while true go to star steppe, get field items, if stardust found, jump to stardust cage


def stardust_farm():
    while True:
        go(["Звёздная степь"])
        for row in range(1, 7):
            for column in range(1, 11):
                cage = Cage(row=row, column=column)
                items = cage.get_items()


comm_dict = {"patrol": patrol,
             # patrol  location1 - locationN
             "go": go,
             # go  location1 - locationN
             "do": do,
             # do action1 - actionN
             "repeat": repeat,
             # repeat action1 - actionN
             "alias": create_alias,
             # alias name comm_to_execute
             "settings": change_settings,
             # settings key - value
             "swim": swim,
             # swim location_to_escape
             "char": char,
             # char
             "info": info,
             # info
             "hist": hist,
             # hist
             "help": print_readme,
             # help
             "clear_hist": clear_hist,
             # clear_hist
             "refresh": refresh,
             # refresh
             "say": text_to_chat,
             # say message
             "cancel": cancel,
             # cancel
             "jump": jump_to_cage,
             # jump row - column
             "wait": wait_for,
             # wait seconds_from - seconds_to
             "rabbit_game": start_rabbit_game,
             # rabbit_game number_of_games_to_play
             "balance": print_rabbits_balance,
             # balance
             "inv": print_inv,
             # inv
             "c": print_cage_info,
             # cage row - column
             "q": end_session,
             # q
             "bury": bury_item,
             # bury item_img_id - level
             }

if __name__ == "__main__":
    config = clicker_utils.load_config()
    settings, action_dict, alias_dict = config["settings"], config["actions"], config["aliases"]
    print("Настройки загружены...")

    driver = browser_navigation.DriverWrapper(long_break_chance=settings["long_break_chance"],
                                              long_break_duration=settings["long_break_duration"],
                                              short_break_duration=settings["short_break_duration"],
                                              critical_sleep_pixels=settings["critical_sleep_pixels"],
                                              is_headless=settings["is_headless"],
                                              driver_path=settings["driver_path"],
                                              max_waiting_time=settings["max_waiting_time"])

    print(f"Игровая загружается, если прошло более {settings['max_waiting_time'] * 10} секунд - перезапустите кликер.")
    driver.get("https://catwar.su/cw3/")  # vibecheck https://bot.sannysoft.com/

    if driver.current_url != "https://catwar.su/cw3/":
        print("Для включения кликера вам необходимо залогиниться в варовский аккаунт.\n"
              "ВНИМАНИЕ: все ваши данные (почта и пароль) сохраняются в папке selenium, она создаётся \n"
              "в той же папке, куда вы поместили этот скрипт (main.py). НЕ ОТПРАВЛЯЙТЕ НИКОМУ папку selenium, \n"
              "для работы кликера нужен main.py, browser_navigation.py, clicker_utils.py и config.json.\n"
              "Все команды кликера работают ИЗ ИГРОВОЙ!")
    else:
        info()

command = "null"
while command != "q":
    command = input(">>> ")
    try:
        multi_comm_handler(command)
    except (KeyboardInterrupt, ProtocolError):
        end_session()
        break
    except Exception as exception:
        print(type(exception).__name__)
        clicker_utils.crash_handler(exception)
        end_session()
        break
