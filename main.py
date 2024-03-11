from selenium.webdriver.common.actions.action_builder import ActionBuilder

from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (NoSuchElementException,
                                        MoveTargetOutOfBoundsException,
                                        StaleElementReferenceException, TimeoutException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
import time
import random
import json
import re
import traceback
import datetime
import os


def check_time() -> int:
    """Проверить, сколько времени осталось до окончания действия.
    Если никакое действие в данный момент не выполняется, возвращает 1."""

    element: WebElement = locate("//span[@id='sek']")
    if not element:
        return 1
    match_seconds = re.match(r"(\d*) мин (\d*) с", element.text)
    if not match_seconds:
        match_seconds = re.match(r"(\d*) с", element.text)
        seconds = int(match_seconds[1])
    else:
        seconds = int(match_seconds[1]) * 60 + int(match_seconds[2])
    return seconds


def check_parameter(param_name) -> float | int:
    """Проверить параметр param_name, вернуть его значение в процентах"""

    element = locate(f"//span[@id='{param_name}']/*/*/*/descendant::*")
    if not element:
        return -1
    pixels = int(element.get_attribute("style").split("px")[0].split("width: ")[1])
    percents = round(pixels / 150 * 100, 2)
    if percents == int(percents):
        return int(percents)
    return percents


def check_skill(skill_name) -> str:
    """Проверить уровень и дробь навыка"""

    mouse_over(xpath=f"//span[@id='{skill_name}']/*/*/*/descendant::*")
    tooltip_elem = locate("//div[@id='tiptip_content']")
    if not tooltip_elem.text:
        mouse_over(xpath=f"//span[@id='{skill_name}']/*/*/*/descendant::*", hover_for=0.01)
    level_elem = locate(f"//table[@id='{skill_name}_table']")
    return tooltip_elem.text + ", уровень " + level_elem.text


def swim(escape_to_location=""):
    """Команда для плавания с отсыпом на соседней локации. Критическое количество пикселей сна (при
    котором начнётся отсып) указывается в настройках. Для справки:
    20 пикс. = ~43 минуты сна, 30 пикс. = ~40 минут сна. Считаются 'оставшиеся' зелёные пиксели.
    ВНИМАНИЕ: перед использованием этой команды проверьте на безопасной ПУ локации,
    работает ли она на вашем устройстве.
    Использование (находясь на локации с ПУ):
    swim локация_для_отсыпа"""

    availible_locations = get_availible_actions()
    if escape_to_location and escape_to_location not in availible_locations:
        print("Для отсыпа введите название локации, соседней с плавательной!")
    elif not escape_to_location:
        repeat(["Поплавать"])
    while True:
        sleep_pixels = check_parameter("dream")
        if sleep_pixels < settings["critical_sleep_pixels"]:
            current_location = locate("//span[@id='location']").text
            move_to_location(escape_to_location)
            do(["Поспать"])
            move_to_location(current_location)
        do(["Поплавать"])


def is_cw3_disabled() -> bool:
    """Проверка на активность Игровой"""

    try:
        cw3_disabled_element = driver.find_element(By.XPATH, "//body[text()='Вы открыли новую вкладку с Игровой, "
                                                             "поэтому старая (эта) больше не работает.']")
        if cw3_disabled_element:
            return True
    except NoSuchElementException:
        return False


def locate(xpath: str) -> WebElement | None:
    """Найти элемент на странице по xpath. """

    try:
        element = driver.find_element(By.XPATH, xpath)
        return element
    except NoSuchElementException:
        if is_cw3_disabled():
            refresh()
            locate(xpath)
        else:
            return None


def remove_cursor():
    action_builder = ActionBuilder(driver)
    action_builder.pointer_action.move_to_location(1, 8)
    action_builder.perform()


def click(xpath: str, offset_range=(0, 0)) -> bool:
    """Клик по элементу element с оффсетом offset_range.
    Возвращает True, если был совершён клик по элементу. """

    element = locate(xpath)
    if not element or not element.is_displayed():
        return False
    random_offset = (random.randint(-offset_range[0], offset_range[0]),
                     random.randint(-offset_range[1], offset_range[1]))
    try:
        action_chain = ActionChains(driver)
        action_chain.scroll_to_element(element).perform()
        action_chain.move_to_element_with_offset(to_element=element,
                                                 xoffset=random_offset[0],
                                                 yoffset=random_offset[1]
                                                 ).perform()
        action_chain.click_and_hold().perform()
        time.sleep(random.uniform(0, 0.1))
        action_chain.release().perform()
        remove_cursor()
    except MoveTargetOutOfBoundsException:
        print("MoveTargetOutOfBoundsException raised for reasons unknown to man :<")
        print("random offset =", random_offset)
        return False
    return True


def mouse_over(xpath: str, hover_for=0.1) -> bool:
    """Передвинуть курсор к элементу по xpath"""

    element = locate(xpath)
    if not element or not element.is_displayed():
        return False
    action_chain = ActionChains(driver)
    action_chain.scroll_to_element(element).perform()
    action_chain.move_to_element(element).perform()
    time.sleep(hover_for)
    return True


def is_action_active() -> bool:
    """Проверка на выволнение действия"""

    element = locate(xpath="//a[@id='cancel']")
    if element:
        return True
    return False


def cancel() -> bool:
    """Отменить действие. Использование:
    cancel"""

    success = click(xpath="//a[@id='cancel']")
    if success:
        print("Действие отменено!")
        return True
    print("Действие не выполняется!")
    return False


def repeat(args=None):
    """Команда для бесконечного повторения действий по списку из args. Использование:
    repeat действие1 - действие2 - действие3"""

    if not args or args == [""]:
        print("Для зацикленного действия нужны аргументы. Наберите comm_help для вывода дополнительной информации.")
        return
    while True:
        do(args)
        if random.random() < settings["long_break_chance"]:
            seconds = random.uniform(settings["long_break_duration"][0], settings["long_break_duration"][1])
            print("long break triggered! sleeping for", round(seconds), "seconds...")
            time.sleep(seconds)


def do(args=None):
    """Команда для исполнения последовательности действий 1 раз. Использование:
    do действие1 - действие2 - действие3"""

    if not args or args == [""]:
        print("Для действия нужны аргументы. Наберите comm_help для вывода дополнительной информации.")
        return
    for action in args:
        availible_actions = get_availible_actions()
        if is_action_active():
            print("Действие уже совершается! Чтобы отменить, введите cancel.")
            return
        if action not in availible_actions:
            print(f"Действие {action} не может быть выполнено. Возможно, действие недоступно/"
                  f"страница не прогрузилась до конца.\nДоступные действия: {', '.join(availible_actions)}.")
            continue
        success = click(xpath=f"//*[@id='akten']/a[@data-id={action_dict[action]}]/img",
                        offset_range=(30, 30))
        if success:
            seconds = check_time() + random.uniform(settings["short_break_duration"][0],
                                                    settings["short_break_duration"][1])
            last_hist_entry = locate("//span[@id='ist']").text.split(".")[-2]
            print(f"{last_hist_entry}. Действие продлится {round(seconds)} секунд.")
            if settings["monitor_chat_while_waiting"] == "True":
                monitor_cw3_chat(seconds)
            else:
                time.sleep(seconds)

            if action == "Принюхаться":
                print(check_skill("smell"))
                click(xpath="//input[@value='Вернуть поле']")
            elif action == "Копать землю":
                print(check_skill("dig"))
            elif action == "Поплавать":
                print(check_skill("swim"))
            print(f"Доступные действия: {', '.join(get_availible_actions())}")
        else:
            continue


def patrol(args=None):
    """Команда перехода, маршрут повторяется бесконечно
    (для маршрута из 3 локаций: 1 - 2 - 3 - 2 - 1 - 2 - 3 и так далее). Использование:
    patrol имя_локации1 - имя_локации2 - имя_локации3"""

    if not args or args == [""]:
        print("Для перехода нужны аргументы. Наберите comm_help для вывода дополнительной информации.")
        return
    if len(args) == 1:
        while True:
            move_to_location(args[0])
    index, direction = -1, 1
    while True:
        index, direction = get_next_index(len(args), index, direction)
        success = move_to_location(args[index])
        if not success:
            continue


def go(args=None):
    """Команда перехода, маршрут проходится один раз. Использование:
    go имя_локации1 - имя_локации2 - имя_локации3"""

    if not args or args == [""]:
        print("Для перехода нужны аргументы. Наберите comm_help для вывода дополнительной информации.")
        return
    for index in range(len(args)):
        success = move_to_location(args[index])
        if not success:
            continue


def move_to_location(location_name: str) -> bool:
    """Техническая функция для перехода на локацию. """

    locations = get_availible_locations()
    if location_name in locations:
        has_moved = click(xpath=f"//span[text()='{location_name}' and @class='move_name']/preceding-sibling::*",
                          offset_range=(40, 70))
    else:
        print("\t\tlocation name is not in av location list")
        return False
    seconds = check_time() + random.uniform(settings["short_break_duration"][0],
                                            settings["short_break_duration"][1])
    if random.random() < settings["long_break_chance"]:
        print("long break triggered")
        seconds += random.uniform(settings["long_break_duration"][0], settings["long_break_duration"][1])
    print(f"Совершён переход в {location_name}, до следующего действия {round(seconds)} секунд.")
    # print(f"Доступные локации: {', '.join(get_availible_locations())}")
    # print_cats()
    if settings["monitor_chat_while_waiting"] == "True":
        monitor_cw3_chat(seconds)
    else:
        time.sleep(seconds)

    return has_moved


def get_availible_actions() -> list:
    """Получить список доступных в данный момент действий"""

    elements = driver.find_elements(By.XPATH, "//div[@id='akten']/a[@class='dey']")
    actions_list = []
    for element in elements:
        for key, value in action_dict.items():
            if int(element.get_attribute("data-id")) == value:
                actions_list.append(key)
                break
    return actions_list


def get_availible_locations() -> list:
    """Получить список переходов на локации"""

    try:
        elements = WebDriverWait(driver, 5).until(expected_conditions.
                                                  visibility_of_all_elements_located
                                                  ((By.XPATH, "//span[@class='move_name']")))
    except TimeoutException:
        if is_cw3_disabled():
            refresh()
        elements = WebDriverWait(driver, 5).until(expected_conditions.
                                                  visibility_of_all_elements_located
                                                  ((By.XPATH, "//span[@class='move_name']")))
    location_list = []
    for element in elements:
        try:
            location_list.append(element.get_attribute(name="innerText"))
        except StaleElementReferenceException:
            print("\t\tencountered stale element, retrying getloc call...")
            time.sleep(1)
            get_availible_locations()

    return location_list


def print_cats():
    """Вывести список игроков на одной локации с вами"""

    elements = driver.find_elements(By.XPATH, "//span[@class='cat_tooltip']/u/*")
    cats_list = []
    for element in elements:
        try:
            cats_list.append(element.get_attribute(name="innerText"))
        except StaleElementReferenceException:
            print("\t\tencountered stale element, retrying print_cats call...")
    if cats_list:
        print("Коты на локации:")
        for i in range(len(cats_list)):
            if not i % 5:
                print("\t\t" + ", ".join(cats_list[i:i + 5]))


def info():
    """Команда для вывода информации о состоянии игрока из Игровой. Использование:
    info"""

    current_location = locate("//span[@id='location']").text
    while current_location == "[ Загружается… ]":
        current_location = locate("//span[@id='location']").text

    print(f"Текущая локация: {current_location}.\n"
          f"Доступные действия: {', '.join(get_availible_actions())}\n"
          f"Доступные локации: {', '.join(get_availible_locations())}")
    print_cats()
    print(f"\tСонливость:  {check_parameter('dream')}%\n"
          f"\tГолод:\t\t {check_parameter('hunger')}%\n"
          f"\tЖажда:\t\t {check_parameter('thirst')}%\n"
          f"\tНужда:\t\t {check_parameter('need')}%\n"
          f"\tЗдоровье:\t{check_parameter('health')}%\n"
          f"\tЧистота: \t {check_parameter('clean')}%")
    print("Последние 5 записей в истории (введите hist, чтобы посмотреть полную историю):")
    hist_list = locate("//span[@id='ist']").text.split('.')[-6:-1]
    print(f"\t{'. '.join(hist_list)}.")


def char():
    """Команда для вывода информации о персонаже с домашней страницы/Игровой. Использование:
    char"""

    driver.get("https://catwar.su/")
    rank = locate('''//div[@id='pr']/i''')

    print(f"Имя: {locate('''//div[@id='pr']/big''').text}")
    if rank:
        print(f"Должность: {rank.text}\n")
    print(f"Луны: {locate('''//div[@id='pr']/table/tbody/tr[2]/td[2]/b''').text}\n"
          f"ID: {locate('''//b[@id='id_val']''').text}\n"
          f"Активность: {locate('''//div[@id='act_name']/b''').text}")
    driver.get("https://catwar.su/cw3/")
    print(f"{check_skill('smell')}\n"
          f"{check_skill('dig')}\n"
          f"{check_skill('swim')}\n"
          f"{check_skill('might')}")


def hist():
    """Команда для вывода истории действий из Игровой, использование:
    hist"""

    print("История:")
    hist_list = locate("//span[@id='ist']").text.split(".")[:-1]
    for item in hist_list:
        print(item)


def clear_hist():
    """Команда 'очистить историю', использование:
    clear_hist"""

    click(xpath="//a[@id='history_clean']")
    print("История очищена.")


def get_last_cw3_message() -> tuple:
    """Получить последнее сообщение в чате Игровой и имя написавшего"""

    try:
        last_message = locate(xpath="//*[@id='chat_msg']/span[1]/table/tbody/tr/td[1]/span/span").text
        name_from = locate(xpath="//*[@id='chat_msg']/span[1]/table/tbody/tr/td[1]/span/b").text
    except AttributeError:
        return '', ''
    return last_message, name_from


def monitor_cw3_chat(monitor_until_time: float):
    """Выводить последние сообщения в чате Игровой, пока не истечёт время end_time"""

    end_time = time.time() + monitor_until_time
    temp_message = ('', '')
    while time.time() <= end_time:
        time.sleep(1)
        message_bundle = get_last_cw3_message()
        if message_bundle == temp_message:
            continue
        else:
            message_time = datetime.datetime.now()
            print(f"Чат |\t{message_bundle[0]} - {message_bundle[1]} | {message_time.strftime('%H:%M:%S')}")
        temp_message = message_bundle


def text_to_chat(message: str):
    """Написать сообщение в чат Игровой"""

    chat_entry = locate(xpath="//input[@id='text']")
    chat_entry.send_keys(message)
    click(xpath="//*[@id='msg_send']")


def get_next_index(length, index=-1, direction=1):
    """Получить индекс следующей локации в патруле"""

    index += direction
    if index == length and direction == 1:
        index -= 2
        direction = -1
    elif index == -1 and direction == -1:
        index += 2
        direction = 1
    return index, direction


def comm_handler(comm: str):
    """Разделить ключевое слово команды и аргументы"""

    if not comm:
        return print("Введите команду! Пример: patrol Морозная поляна - Каменная гряда")
    elif comm in alias_dict.keys():
        return comm_handler(alias_dict[comm])

    try:
        main_comm = comm.split(" ")[0]
        comm = comm.replace(main_comm + " ", "")
        args = comm.split(" - ")
    except IndexError:
        return print("Ошибка в парсинге аргумента. Введите comm_help для просмотра списка команд.")

    if main_comm == "alias":
        return create_alias(comm)
    if main_comm not in comm_dict.keys():
        return print("Команда не найдена. Наберите comm_help для просмотра списка команд.")

    if comm == main_comm:
        return comm_dict[main_comm]()
    return comm_dict[main_comm](args)


def load_config() -> dict:
    """Загрузить файл настроек config.json"""

    try:
        with open("config.json", "r", encoding="utf-8") as file:
            parsed_json: dict = json.load(file)
            return parsed_json
    except FileNotFoundError:
        file = open("config.json", "w")
        file.close()
        load_config()


def rewrite_config(new_config: dict):
    """Обновить файл настроек config.json при их изменении"""

    with open("config.json", "w") as file:
        file.write(json.dumps(new_config, ensure_ascii=False, indent=4))
    print("Настройки обновлены!")


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
    rewrite_config(config)


def change_settings(args=()):
    """Команда для изменения настроек. Использование:
    settings key - value
    (Пример: settings is_headless - True)"""

    if not args or len(args) > 2:
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
    rewrite_config(config)


def crash_handler(exception_type: Exception):
    """Создать крашлог в папке crashlogs, которая находится на том же уровне, что и main.py"""

    if type(exception_type).__name__ == "KeyboardInterrupt":
        return
    now = datetime.datetime.now()
    crash_time = now.strftime("%y-%m-%d_%H.%M.%S")
    path = os.path.dirname(__file__)
    if not os.path.exists(f"{path}/crashlogs"):
        os.mkdir(f"{path}/crashlogs")
    filename = os.path.join(path, f"crashlogs/crash-{crash_time}.txt")
    print(f"Кликер вылетел, exception: {type(exception_type).__name__}. Крашлог находится в папке crashlogs и "
          f"называется {filename}")
    with open(filename, "w") as crashlog:
        stacktrace = traceback.format_exc()
        crashlog.writelines(["---CHRONOCLICKER CRASHLOG---", "\n", "time:", crash_time, "\n", stacktrace])


def comm_help():
    """Вывести все доступные команды."""

    print(", ".join(comm_dict.keys()))


def refresh():
    """Перезагрузить страницу"""
    driver.refresh()
    print("Страница обновлена!")


def jump_to_cage(cage_index=None):
    if not cage_index or cage_index == [""]:
        print("no cage index!")
        return
    try:
        row, column = int(cage_index[0]), int(cage_index[1])
    except (IndexError, ValueError):
        print("jump row - column")
        return
    if row > 6 or row < 0 or column < 0 or column > 10:
        print("invalid cage index!")
        return
    xpath = f"//*[@id='cages']/tbody/tr[{row}]/td[{column}]/div"
    # cage_element = locate(xpath=f"{xpath}/span[@class='move_parent']/span[@class='move_name']")
    # if cage_element:
    #     move_to_location(cage_element.text)
    #     return
    click(xpath=xpath, offset_range=(40, 70))


def is_cat_in_action(cat_id: int) -> bool:
    element = locate(f"//select[@id='mit']/option[@value='{cat_id}']")
    element.submit()
    time.sleep(random.uniform(0.1, 0.5))
    click(xpath="//input[@id='mitok']")
    time.sleep(random.uniform(0.1, 0.5))
    click(xpath="//img[@src='actions/9.png']")
    time.sleep(random.uniform(0.5, 2))
    result = cancel()
    print(result)
    return result


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
             # settings key value
             "swim": swim,
             # swim location_to_escape
             "char": char,
             # char
             "info": info,
             # info
             "hist": hist,
             # hist
             "comm_help": comm_help,
             # comm_help
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
             """             "fight": fight_mode,
             # fight
             "turn": turn_arrow,
             # turn degrees
             "spin": spin_arrow,
             # spin seconds
             "hit": hit,
             # hit
             "train": training_with_sleep,
             # train bodypart - partner_id - hits_from_me - hits_from_partner - rounds"""
             "check_cat": is_cat_in_action,
             }

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")  # windows....
options.add_argument("--remote-debugging-port=9222")
options.add_argument("user-data-dir=selenium")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

if __name__ == "__main__":
    print("Загрузка...")
    config = load_config()
    settings = config["settings"]
    action_dict = config["actions"]
    alias_dict = config["aliases"]
    print("Настройки загружены...")

    if settings["is_headless"] == "True":
        print("Запуск в фоновом режиме...")
        options.add_argument("--headless")

    if settings["driver_path"]:
        driver_path = settings["driver_path"]
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        print(f"Вебдрайвер запущен, путь {driver_path}")
    else:
        driver = webdriver.Chrome(options=options)
        print("Вебдрайвер запущен.")

    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)

    driver.implicitly_wait(settings["max_waiting_time"])
    print(f"Игровая загружается, если прошло более {settings['max_waiting_time']} секунд - перезапустите кликер.")
    driver.get("https://catwar.su/cw3/")  # vibecheck https://bot.sannysoft.com/

    if driver.current_url != "https://catwar.su/cw3/":
        print("Для включения кликера вам необходимо залогиниться в варовский аккаунт.\n"
              "ВНИМАНИЕ: все ваши данные (почта и пароль) сохраняются в папке selenium, она создаётся \n"
              "в той же папке, куда вы поместили этот скрипт (main.py). НЕ ОТПРАВЛЯЙТЕ НИКОМУ папку selenium, \n"
              "для работы кликера нужен только main.py и config.json.\n"
              "Все команды кликера работают ИЗ ИГРОВОЙ!")
    else:
        info()

    try:
        while True:
            command = input(">>> ")
            if command != "q":
                comm_handler(command)
            else:
                break
    except Exception as exception:
        crash_handler(exception)
