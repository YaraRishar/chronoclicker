import time
import random
import os.path

from selenium.webdriver.common.by import By
from urllib3.exceptions import ProtocolError
import browser_navigation
import clicker_utils
import cage_utils


def do(args=None, show_availables=True) -> bool:
    """Команда для исполнения последовательности действий 1 раз. Использование:
    do действие1 - действие2 - действие3"""

    if driver.is_held():
        driver.quit()
        return False
    if args is None:
        print("Для действия нужны аргументы. Наберите help для вывода дополнительной информации.")
        return False
    for action in args:
        action = action.strip().lower()
        available_actions = driver.get_available_actions(action_dict)
        if driver.is_action_active():
            action_active_sec = driver.check_time()
            print(f"Действие уже совершается! Чтобы отменить, введите cancel.\n"
                  f"(До окончания действия осталось {action_active_sec // 60} мин {action_active_sec % 60} сек)")
            if not show_availables:
                wait_for([action_active_sec, action_active_sec + driver.short_break_duration[1]])
            return False
        if action not in available_actions:
            print(f"Действие {action} не может быть выполнено. Возможно, действие недоступно/"
                  f"страница не прогрузилась до конца.\nДоступные действия: {', '.join(available_actions)}.")
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
            if action == "принюхаться":
                print(driver.check_skill("smell"))
                driver.click(xpath="//input[@value='Вернуть поле']")
            elif action == "копать землю":
                print(driver.check_skill("dig"))
            elif action == "поплавать":
                print(driver.check_skill("swim"))

            if show_availables:
                print(f"Доступные действия: {', '.join(driver.get_available_actions(action_dict))}")
        else:
            continue
    return True


def patrol(args=None) -> bool:
    """Команда перехода, маршрут повторяется бесконечно
    (для маршрута из 3 локаций: 1 - 2 - 3 - 2 - 1 - 2 - 3 и так далее). Использование:
    patrol имя_локации1 - имя_локации2 - имя_локации3"""

    if args is None:
        print("Для перехода нужны аргументы. Наберите help для вывода дополнительной информации.")
        return False
    if len(args) == 1:
        while True:
            driver.move_to_location(args[0], show_availables=False)
    index, direction = -1, 1
    while True:
        index, direction = clicker_utils.get_next_index(len(args), index, direction)
        success = driver.move_to_location(args[index], show_availables=False)
        if not success:
            continue


def go(args=None) -> bool:
    """Команда перехода, маршрут проходится один раз. Использование:
    go имя_локации1 - имя_локации2 - имя_локации3"""

    if args is None:
        print("Для перехода нужны аргументы. Наберите help для вывода дополнительной информации.")
        return False
    for index in range(len(args)):
        success = driver.move_to_location(args[index], show_availables=True)
        if not success:
            continue
    return True


def start_rabbit_game() -> bool:
    """ Начать игру в числа с Лапом, после 5 игр вернуться в cw3. Использование:
     rabbit_game"""

    driver.get("https://catwar.net/chat")
    time.sleep(random.uniform(1, 3))
    driver.click(xpath="//a[@data-bind='openPrivateWith_form']")
    driver.type_in_chat("Системолап", entry_xpath="//input[@id='openPrivateWith']")
    driver.click(xpath="//*[@id='openPrivateWith_form']/p/input[2]")  # OK button

    games_played = 0
    while games_played != 5:
        driver.rabbit_game()
        games_played += 1
    driver.get("https://catwar.net/cw3/")
    return True


def info() -> bool:
    """Команда для вывода информации о состоянии игрока из Игровой. Использование:
    info"""

    if driver.current_url != "https://catwar.net/cw3/":
        return False
    current_location = driver.get_current_location()
    print(f"Текущая локация: {current_location}\n"
          f"Доступные локации: {', '.join(driver.get_available_locations())}\n"
          f"Доступные действия: {', '.join(driver.get_available_actions(action_dict))}")
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
    return True


def char() -> bool:
    """ Команда для вывода информации о персонаже с домашней страницы/Игровой. Использование:
    char """

    driver.get("https://catwar.net/")
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
    return True


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


def create_alias(comm) -> bool:
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
        return False
    if main_alias_comm not in comm_dict.keys():
        print(f"Команда {main_alias_comm} не найдена, сокращение не было создано.")
        return False
    name = comm.split(" ")[0]
    comm_to_alias = comm.replace(name + " ", "")
    config["aliases"][name] = comm_to_alias
    print(f"Создано сокращение команды {comm_to_alias} под именем {name}.")
    clicker_utils.rewrite_config(config)
    return True


def refresh():
    """Перезагрузить страницу"""

    driver.refresh()
    print("Страница обновлена!")


def change_settings(args=None) -> bool:
    """Команда для изменения настроек. Использование:
    settings key - value
    (Пример: settings is_headless - True)"""

    if args is None or len(args) != 2:
        print(config["settings"])
        return False
    key, value = args
    try:
        if key == "is_headless" or key == "driver_path" or key == "my_id":
            config["settings"][key] = value
        else:
            config["settings"][key] = eval(value)
    except ValueError:
        print("Ошибка в парсинге аргумента.")
        return False
    clicker_utils.rewrite_config(config)
    return True


def wait_for(seconds=None) -> bool:
    """ Ничего не делать рандомное количество времени от seconds_start до seconds_end секунд либо ровно seconds секунд
     seconds: list = [seconds_start, seconds_end]"""

    if seconds is None or len(seconds) > 2:
        print("Введите количество секунд! wait seconds_from - seconds_to ИЛИ wait seconds")
        return False
    if len(seconds) == 1:
        clicker_utils.print_timer(console_string="Начато ожидание",
                                  seconds=seconds[0],
                                  turn_off_timer=driver.turn_off_timer)
        return True
    try:
        seconds[0], seconds[1] = int(seconds[0]), int(seconds[1])
    except (IndexError, ValueError):
        print("wait seconds_from - seconds_to ИЛИ wait seconds")
        return False
    seconds: float = random.uniform(int(seconds[0]), int(seconds[1]))
    clicker_utils.print_timer(console_string="Начато ожидание", seconds=seconds, turn_off_timer=driver.turn_off_timer)
    return True


def text_to_chat(message=None) -> bool:
    """Написать сообщение в чат Игровой"""

    if message is None or len(message) != 1:
        print("say message")
        return False
    message = message[0]
    driver.type_in_chat(text=message, entry_xpath="//input[@id='text']")
    driver.click(xpath="//*[@id='msg_send']")
    return True


def print_rabbits_balance():
    """ Вывести баланс кролей игрока """

    driver.get("https://catwar.net/rabbit")
    rabbit_balance = driver.locate_element(xpath="//img[@src='img/rabbit.png']/preceding-sibling::b").text
    wait_for([0.5, 1.5])
    driver.back()

    print("Кролей на счету:", rabbit_balance)


def print_inv():
    inv_ids = driver.get_inv_items()
    print("Предметы во рту:")
    for i in inv_ids:
        print(f"https://catwar.net/cw3/things/{i}.png")


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


def parse_condition(comm):
    # param сон > 30 ? go Поляна для отдыха; do Поспать : wait 1
    condition_symbols = [" > ", " < ", " == ", " >= ", " <= ", " != "]
    condition = comm.split(" ? ")[0]  # param сон > 30
    symbol = False
    for i in range(len(condition_symbols)):
        if condition_symbols[i] in condition:
            symbol = condition_symbols[i]
            break
    if not symbol:
        return
    condition_comm = condition.split(symbol)  # ['param сон', '30']
    expected_value = condition_comm[1]  # 30
    real_value = comm_handler(condition_comm[0])
    try:
        real_value = float(real_value)
        expected_value = float(expected_value)
    except ValueError:
        print("value error")
        return

    result = eval(f"{real_value} {symbol} {expected_value}")
    ternary_list = comm.split(" ? ")[1].split(" : ")  # ['go Поляна для отдыха; do Поспать', 'wait 1']
    if result:
        multi_comm_handler(ternary_list[0])
    else:
        multi_comm_handler(ternary_list[1])


def multi_comm_handler(multi_comm: str) -> bool:
    """ Исполнить каждую команду в мультикоманде по очереди """

    if not multi_comm:
        print("Введите команду! Пример: patrol Морозная поляна - Каменная гряда")
        return False
    if multi_comm in alias_dict.keys():
        multi_comm_handler(alias_dict[multi_comm])
        return True

    multi_comm_list: list = multi_comm.split("; ")
    first_word = multi_comm.split(" ")[0]
    if first_word == "alias":
        multi_comm = multi_comm.replace("alias ", "")
        return create_alias(multi_comm)
    for comm in multi_comm_list:
        comm_handler(comm)


def comm_handler(comm: str) -> float | int | bool:
    """ Разделить ключевое слово команды и аргументы """

    try:
        main_comm = comm.split(" ")[0]
        comm = comm.replace(main_comm + " ", "")
        args = comm.split(" - ")
    except IndexError:
        print("Ошибка в парсинге аргумента. Введите help для просмотра списка команд.")
        return False

    if main_comm == "alias":
        return create_alias(comm)
    if main_comm not in comm_dict.keys():
        print(f"Команда {main_comm} не найдена. Наберите help для просмотра списка команд.")
        return False

    if comm == main_comm:
        result = comm_dict[main_comm]()
        return result
    result = comm_dict[main_comm](args)
    return result


def parse_command(comm: str):
    if " ? " in comm:
        parse_condition(comm)
        return
    multi_comm_handler(comm)


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
              f"https://catwar.net/cw3/things/{item_img_id}.png")
        return
    driver.bury_item(item_img_id, level)


def jump_to_cage(args=None, verbose=True) -> int:
    if not args or len(args) != 2:
        print("jump row - column")
        return -1
    row, column = args
    cage = cage_utils.Cage(driver, row, column)
    cage.jump()
    if verbose:
        print(f"Прыжок на {row} ряд, {column} клетку.")
    return 0


def loop_alias(args=None):
    """ Повторять сокращение или команду бесконечно (как команда patrol и repeat)
     loop alias_name
     """
    if args is None:
        print("Введите название сокращения. Пример: loop название_сокращения")
        return
    alias_name = args[0]
    if alias_name in alias_dict.keys():
        while True:
            multi_comm_handler(alias_dict[alias_name])
            driver.trigger_long_break(long_break_chance=settings["long_break_chance"],
                                      long_break_duration=settings["long_break_duration"])

    while True:
        multi_comm_handler(alias_name)
        driver.trigger_long_break(long_break_chance=settings["long_break_chance"],
                                  long_break_duration=settings["long_break_duration"])


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
    available_locations = driver.get_available_locations()
    random_location = random.sample(available_locations, 1)
    go(random_location)
    find_items(items_to_seek)


def find_cats(args=None):
    """ Найти кота по его имени или ID на локациях, рандомно переходя по ним """

    if args is None:
        print("find_cat имя_кота")

    names_to_find: list = args
    while names_to_find:
        cat_name, location, row, column = driver.find_cat_on_loc(names_to_find)
        if cat_name:
            print(f"Кот {cat_name} найден в локации {location} на клетке {row}x{column}!")
            names_to_find.remove(cat_name)
            continue
        available_locations = driver.get_available_locations()
        random_location = random.sample(available_locations, 1)
        go(random_location)


def pathfind_handler(end:tuple, forbidden_cages_given=()):
    """ Найти путь по клеткам от вашего местоположения до end. Использование:
     pathfind row - column"""

    end = int(end[0]), int(end[1])
    end_cage = cage_utils.Cage(driver, end[0], end[1])
    if end_cage.is_move() or end_cage.has_cat():
        print(f"Клетка {end} занята котом или переходом!")
        return
    my_coords = find_my_coords()
    cages = driver.get_cages_list()
    forbidden_cages = [_ for _ in forbidden_cages_given]

    for cage in cages:
        if cage.is_move() or cage.has_cat():
            forbidden_cages.append((cage.row, cage.column))

    path = clicker_utils.pathfind(start=my_coords, end=end, forbidden_cages=forbidden_cages)
    for cage in path:
        jump_to_cage(cage, verbose=False)
    driver.print_cats()


def check_parameter(args=None) -> float | int:
    """ Команда для проверки параметра parameter_name. Возвращает float или int - значение параметра в процентах.
     param сон"""

    if args is None or len(args) != 1:
        print("param parameter_name")
        return -1
    param_name: str = args[0].strip().lower()
    if param_name not in parameters_dict:
        print("param_name not in parameters_dict")
        return -1
    param_name_server = parameters_dict[param_name]
    param_value = driver.get_parameter(param_name=param_name_server)
    print(f"{param_name.capitalize()} - {param_value}")
    return param_value


def count_cw3_messages() -> int:
    chatbox = driver.locate_element(xpath="//div[@id='chat_msg']")
    msg_list = chatbox.find_elements(By.XPATH, value="//span/table/tbody/tr/td/span")
    print(len(msg_list), "cw3 messages!")
    return len(msg_list)


def get_last_cw3_message_volume() -> int:
    chatbox = driver.locate_element(xpath="//div[@id='chat_msg']")
    msg_element = chatbox.find_element(By.XPATH, value="//span/table/tbody/tr/td/span")
    if not msg_element:
        print("no cw3 messages found")
        return -1
    volume_str = msg_element.get_attribute("class")
    volume = int("".join([i for i in volume_str if i.isdigit()]))
    print("vol", volume)
    return volume


def check_for_warning() -> bool:
    """ *CONSTRUCTION NOISES* """

    error_element = driver.locate_element(xpath="//p[id='error']")
    error_style = error_element.get_attribute("style")
    if "block" in error_style:
        return True
    return False


def find_my_coords() -> (int, int):
    my_info = driver.find_cat_on_loc(settings["my_id"])
    my_coords = my_info[2:]
    return my_coords


def check_cage(cage_to_check: tuple, max_checks=10) -> int:
    """ *CONSTRUCTION NOISES* """

    checks = 0
    safe_cage = find_my_coords()
    current_msg_count = count_cw3_messages()
    danger_level = -2
    while checks < max_checks:
        jump_to_cage(cage_to_check)
        last_msg_count = count_cw3_messages()
        if last_msg_count > current_msg_count:
            danger_level = get_last_cw3_message_volume()
            break
    return danger_level


comm_dict = {"patrol": patrol,
             # patrol  location1 - locationN
             "go": go,
             # go  location1 - locationN
             "do": do,
             # do action1 - actionN
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
             "param": check_parameter,
             # param param_name
             }

if __name__ == "__main__":
    config = clicker_utils.load_config()
    settings, action_dict, alias_dict, parameters_dict = (config["settings"], config["actions"],
                                                          config["aliases"], config["parameters"])
    print("Настройки загружены...")
    if not settings["my_id"]:
        print("[!!!] Параметр my_id в файле config.json не заполнен, поиск пути по клеткам \n"
              "\t и (в будущем) автотренировки не будут работать! Введите settings my_id - 1, заменив 1 на ваш ID, \n"
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
    driver.get("https://catwar.net/cw3/")  # vibecheck https://bot.sannysoft.com/

    if driver.current_url != "https://catwar.net/cw3/":
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
        parse_command(command)
    except (KeyboardInterrupt, ProtocolError):
        end_session()
        break
    # except Exception as exception:
    #     print(type(exception).__name__)
    #     clicker_utils.crash_handler(exception)
    #     end_session()
    #     break
