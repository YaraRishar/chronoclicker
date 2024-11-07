import re
import time
import random
import os.path
from urllib3.exceptions import ProtocolError
import browser_navigation
import clicker_utils
import cage_utils


def repeat(args=None):
    """Команда для бесконечного повторения действий по списку из args. Использование:
    repeat действие1 - действие2 - действие3"""

    if not args or args == [""]:
        print("Для зацикленного действия нужны аргументы. Наберите help для вывода дополнительной информации.")
        return
    while True:
        do(args, show_avaliables=False)
        driver.trigger_long_break(long_break_chance=settings["long_break_chance"],
                                  long_break_duration=settings["long_break_duration"])


def do(args=None, show_avaliables=True):
    """Команда для исполнения последовательности действий 1 раз. Использование:
    do действие1 - действие2 - действие3"""

    if driver.is_held():
        driver.quit()
        return
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

            do_cancel = clicker_utils.print_timer(console_string=last_hist_entry,
                                                  seconds=seconds, turn_off_timer=driver.turn_off_timer)
            if do_cancel:
                cancel()
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

    current_location = driver.get_current_location()
    print(f"Текущая локация: {current_location}\n"
          f"Доступные локации: {', '.join(driver.get_availible_locations())}\n"
          f"Доступные действия: {', '.join(driver.get_availible_actions(action_dict))}")
    driver.print_cats()
    print(f"\t Сонливость:\t{driver.get_parameter('dream')}%\n"
          f"\t Голод:\t\t{driver.get_parameter('hunger')}%\n"
          f"\t Жажда:\t\t{driver.get_parameter('thirst')}%\n"
          f"\t Нужда:\t\t{driver.get_parameter('need')}%\n"
          f"\t Здоровье:\t{driver.get_parameter('health')}%\n"
          f"\t Чистота: \t{driver.get_parameter('clean')}%")
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
        if key == "is_headless" or key == "driver_path" or key == "my_id":
            config["settings"][key] = value
        else:
            config["settings"][key] = eval(value)
    except ValueError:
        print("Ошибка в парсинге аргумента.")
        return
    clicker_utils.rewrite_config(config)


def wait_for(seconds=None):
    """ Ничего не делать рандомное количество времени от seconds_start до seconds_end секунд либо ровно seconds секунд
     seconds: list = [seconds_start, seconds_end]"""

    if not seconds or seconds == [""] or len(seconds) > 2:
        print("Введите количество секунд")
    try:
        seconds[0], seconds[1] = int(seconds[0]), int(seconds[1])
    except (IndexError, ValueError):
        print("wait seconds_from - seconds_to ИЛИ wait seconds")
        return
    if len(seconds) == 1:
        clicker_utils.print_timer(console_string="Начато ожидание", seconds=seconds[0], turn_off_timer=driver.turn_off_timer)
        return
    seconds: float = random.uniform(int(seconds[0]), int(seconds[1]))
    clicker_utils.print_timer(console_string="Начато ожидание", seconds=seconds, turn_off_timer=driver.turn_off_timer)


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


def print_inv():
    inv_ids = driver.get_inv_items()
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
    cage = cage_utils.Cage(driver, row=args[0], column=args[1])
    cage.pretty_print()


def command_parser(comm):
    # param - сон > 30 ? go Поляна для отдыха; do Поспать : wait 1
    # loop param - сон > 30 ? go Поляна для отдыха; do Поспать : wait 1
    pass


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


def comm_handler(comm: str) -> str | None:
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
        return print(f"Команда {main_comm} не найдена. Наберите help для просмотра списка команд.")

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
    inv_items = driver.get_inv_items()
    if not inv_items:
        print("Во рту нет предметов!")
        return
    if item_img_id == "inv":
        for item in inv_items:
            driver.bury_item(item, level)
            level = 1
        return
    if item_img_id not in inv_items:
        print(f"Предмета с айди {item_img_id} нет в инвентаре! Ссылка на изображение: "
              f"https://catwar.su/cw3/things/{item_img_id}.png")
        return
    driver.bury_item(item_img_id, level)


def jump_to_cage(args=None, verbose=True):
    if not args or len(args) != 2:
        print("jump row - column")
        return
    row, column = args
    cage = cage_utils.Cage(driver, row, column)
    cage.jump()
    if verbose:
        print(f"Прыжок на {row} ряд, {column} клетку.")


def loop_alias(args=None):
    """ Повторять сокращение бесконечно (как команда patrol и repeat)
     loop alias_name
     """
    if not args or args == [""] or len(args) != 1:
        print("Введите название сокращения. Пример: loop название_сокращения")
        return
    alias_name = args[0]
    if alias_name not in alias_dict.keys():
        print(f"Сокращение под названием {alias_name} не найдено.")
        return
    while True:
        multi_comm_handler(alias_dict[alias_name])
        driver.trigger_long_break(long_break_chance=settings["long_break_chance"],
                                  long_break_duration=settings["long_break_duration"])


def dig_everything(locations_checked=None):
    if locations_checked is None:
        locations_checked = []
    current_location = driver.get_current_location()
    if current_location in locations_checked:
        locations = driver.get_availible_locations()
        go(random.sample(locations, 1))
        dig_everything(locations_checked)

    for row in range(1, 7):
        for column in range(1, 11):
            time.sleep(random.uniform(1, 2))
            cage = cage_utils.Cage(driver, row, column)
            print(f"cage {row}x{column}, location {current_location}")
            do(["Копать землю"], show_avaliables=False)
            items_dug = cage.get_items()
            if items_dug:
                print("Найдены предметы!")
                cage.pretty_print()
                cage.pick_up_item()
            if not cage.get_items() and not cage.has_cat():
                cage.jump()
    time.sleep(random.uniform(1, 5))
    locations_checked.append(current_location)


def find_items(items_to_seek=None):
    """ Искать перечисленные предметы по разным локациям, поднимать их, если найдены """

    if not items_to_seek:
        print("find_items item_id - item_id")
        return
    items_to_seek = [int(item) for item in items_to_seek]
    cages_list = driver.get_cages_list()
    for cage in cages_list:
        items_on_cage = cage.get_items()
        if not items_on_cage:
            continue
        for item in items_on_cage:
            if item in items_to_seek:
                print(f"found item with id {item}")
                cage.pick_up_item()
    availible_locations = driver.get_availible_locations()
    random_location = random.sample(availible_locations, 1)
    go(random_location)
    find_items(items_to_seek)


def find_cat_on_loc(names_to_find) -> tuple:
    """ Найти кота на текущей локации по имени или ID """

    cages_list = driver.get_cages_list()
    for cage in cages_list:
        if not cage.has_cat():
            continue
        cat_name = cage.get_cat_name()
        cat_id = cage.get_cat_id()
        location = driver.get_current_location()
        if cat_name in names_to_find:
            return cat_name, location, cage.row, cage.column
        elif cat_id in names_to_find:
            return cat_id, location, cage.row, cage.column
    return False, False, False, False


def find_cats(args=None):
    """ Найти кота по его имени или ID на локациях, рандомно переходя по ним """

    if args is None:
        print("find_cat имя_кота")

    names_to_find: list = args
    while names_to_find:
        cat_name, location, row, column = find_cat_on_loc(names_to_find)
        if cat_name:
            print(f"Кот {cat_name} найден в локации {location} на клетке {row}x{column}!")
            names_to_find.remove(cat_name)
            continue
        availible_locations = driver.get_availible_locations()
        random_location = random.sample(availible_locations, 1)
        go(random_location)


def parse_swim_location(sleep_loc, swim_loc) -> dict:
    loc_dict = {sleep_loc: driver.get_move_coords(sleep_loc), swim_loc: driver.get_move_coords(swim_loc)}

    jump_to_cage(loc_dict[swim_loc])
    driver.has_moves()

    return loc_dict


def pathfind_handler(end):
    """ Найти путь по клеткам от вашего местоположения до end. Использование:
     pathfind row - column"""

    end = int(end[0]), int(end[1])
    end_cage = cage_utils.Cage(driver, end[0], end[1])
    if end_cage.is_move() or end_cage.has_cat():
        print(f"Клетка {end} занята котом или переходом!")
        return
    my_info = find_cat_on_loc(settings["my_id"])
    my_coords = my_info[2:]
    cages = driver.get_cages_list()
    forbidden_cages = []

    for cage in cages:
        if cage.is_move() or cage.has_cat():
            forbidden_cages.append((cage.row, cage.column))

    path = clicker_utils.pathfind(start=my_coords, end=end, forbidden_cages=forbidden_cages)
    for cage in path:
        jump_to_cage(cage, verbose=False)
    driver.print_cats()


def check_parameter(args=None):
    if args is None or len(args) != 1:
        print("ОШЫБКА")
        return
    param_name: str = args[0].lower()
    if param_name not in parameters_dict:
        print("тоже ошыбка")
        return
    param_value = driver.get_parameter(param_name=param_name)
    print(f"{param_name.capitalize()} - {param_value}")
    return param_value


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
             "с": print_cage_info,  # дубликат команды для с на латинице/кириллице
             # cage row - column
             "q": end_session,
             # q
             "bury": bury_handler,
             # bury item_img_id - level
             "loop": loop_alias,
             # loop alias_name
             "find_item": find_items,
             # find_items item_id1 - item_id2
             "find_cat": find_cats,
             # find_cat cat_name1 - cat_nameN
             "pathfind": pathfind_handler,
             # pathfind row - column
             }

if __name__ == "__main__":
    config = clicker_utils.load_config()
    settings, action_dict, alias_dict, parameters_dict = (config["settings"], config["actions"],
                                                          config["aliases"], config["parameters"])
    print("Настройки загружены...")
    if not settings["my_id"]:
        print("[!!!] Параметр my_id в файле config.json не заполнен, поиск пути по клеткам \n"
              "\t и автотренировки не будут работать! Введите settings my_id - 1, заменив 1 на ваш ID, \n"
              "\t либо не используйте автокач ПУ в опасных локациях! Кликер ВЫЛЕТИТ и вы УТОНЕТЕ!")

    driver = browser_navigation.DriverWrapper(long_break_chance=settings["long_break_chance"],
                                              long_break_duration=settings["long_break_duration"],
                                              short_break_duration=settings["short_break_duration"],
                                              critical_sleep_pixels=settings["critical_sleep_pixels"],
                                              is_headless=settings["is_headless"],
                                              driver_path=settings["driver_path"],
                                              max_waiting_time=settings["max_waiting_time"],
                                              turn_off_timer=settings["turn_off_dynamic_timer"])

    print(f"Игровая загружается, если прошло более {settings['max_waiting_time'] * 10} секунд - перезапустите кликер.")
    driver.get("https://catwar.su/cw3/")  # vibecheck https://bot.sannysoft.com/

    if driver.current_url != "https://catwar.su/cw3/":
        print("Для включения кликера вам необходимо залогиниться в варовский аккаунт.\n"
              "ВНИМАНИЕ: все ваши данные (почта и пароль) сохраняются в папке selenium (либо в профилях chrome),"
              " она создаётся в той же папке, \n"
              "куда вы поместили этот скрипт (main.py). НЕ ОТПРАВЛЯЙТЕ НИКОМУ папку selenium, \n"
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
