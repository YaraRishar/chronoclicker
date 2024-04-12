from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.support.select import Select

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

    tooltip_elem = locate("//div[@id='tiptip_content']")
    level_elem = locate(f"//table[@id='{skill_name}_table']")
    mouse_over(xpath=f"//span[@id='{skill_name}']/*/*/*/descendant::*")
    if not tooltip_elem.text:
        mouse_over(xpath=f"//span[@id='{skill_name}']/*/*/*/descendant::*", hover_for=0.01)
    if skill_name in tooltip_elem.text:
        return tooltip_elem.text + ", уровень " + level_elem.text
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


def click(xpath="xpath", offset_range=(0, 0), given_element=None) -> bool:
    """Клик по элементу element с оффсетом offset_range.
    Возвращает True, если был совершён клик по элементу. """

    if xpath != "xpath" and not given_element:
        element = locate(xpath)
    elif given_element:
        element = given_element
    else:
        return False

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
        success = click(xpath=f"//a[@data-id={action_dict[action]}][@class='dey']/img",
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

    element = locate(f"//span[text()='{location_name}' and @class='move_name']/preceding-sibling::*")
    wait = WebDriverWait(driver, 5)
    element = wait.until(expected_conditions.visibility_of(element))
    if not element:
        return False
    else:
        has_moved = click(xpath=f"//span[text()='{location_name}' and @class='move_name']/preceding-sibling::*",
                          offset_range=(40, 70))
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

    elements_self = driver.find_elements(By.XPATH, "//div[@id='akten']/a[@class='dey']")
    elements_others = driver.find_elements(By.XPATH, "//div[@id='dein']/a[@class='dey']")
    elements = elements_self + elements_others
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
        elements = WebDriverWait(driver, 30).until(expected_conditions.
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


def get_cats_list():
    """Получить список игроков на одной локации с вами"""
    elements = driver.find_elements(By.XPATH, "//span[@class='cat_tooltip']/u/a")
    cats_list = []
    for element in elements:
        try:
            cats_list.append(element.get_attribute(name="innerText"))
        except StaleElementReferenceException:
            print("\t\tencountered stale element!...")
    return cats_list


def print_cats():
    """Вывести список игроков на одной локации с вами"""

    cats_list = get_cats_list()
    if cats_list:
        print("Коты на локации:")
        for i in range(len(cats_list)):
            if not i % 5:
                print("\t\t" + ", ".join(cats_list[i:i + 5]))
    else:
        print("Других котов на локации нет.")


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


def multi_comm_handler(multi_comm: str):
    if not multi_comm:
        return print("Введите команду! Пример: patrol Морозная поляна - Каменная гряда")
    elif multi_comm in alias_dict.keys():
        return comm_handler(alias_dict[multi_comm])

    multi_comm_list: list = multi_comm.split("; ")
    first_word = multi_comm.split(" ")[0]
    if first_word == "alias":
        multi_comm = multi_comm.replace("alias ", "")
        return create_alias(multi_comm)
    for comm in multi_comm_list:
        comm_handler(comm, multi_comm)


def comm_handler(comm: str, multi_comm=None):
    """Разделить ключевое слово команды и аргументы"""

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
        print(main_alias_comm)
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
    crash_path = os.path.join(path, f"crashlogs/crash-{crash_time}.txt")
    print(f"Кликер вылетел, exception: {type(exception_type).__name__}. Крашлог находится по пути {crash_path}")
    with open(crash_path, "w") as crashlog:
        stacktrace = traceback.format_exc()
        crashlog.writelines(["---CHRONOCLICKER CRASHLOG---", "\n", "time: ", crash_time, "\n", stacktrace])


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
        print("jump ряд - клетка")
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


def is_cat_in_action(cat_name: str) -> bool:
    selector = locate(xpath="//*[@id='mit']")
    dropdown_object = Select(selector)

    options_list = selector.find_elements(By.XPATH, "//option")
    names_list = [i.text for i in options_list]
    if cat_name in names_list:
        dropdown_object.select_by_visible_text(cat_name)
        time.sleep(0.5)
        click(xpath="//*[@id='mitok']")
        time.sleep(0.5)
        click(xpath="//img[@src='actions/9.png']")
        time.sleep(random.uniform(1, 2))
        result = cancel()
        print(result)
        return result


def wait_for(seconds=None):
    if not seconds or seconds == [""] or len(seconds) > 2:
        print("invalid seconds count")
    try:
        seconds[0], seconds[1] = int(seconds[0]), int(seconds[1])
    except (IndexError, ValueError):
        print("wait seconds_from - seconds_to")
        return
    seconds: float = random.uniform(int(seconds[0]), int(seconds[1]))
    time.sleep(seconds)


def start_rabbit_game():
    driver.get("https://catwar.su/chat")
    time.sleep(random.uniform(1, 3))

    games_played = 0
    while games_played != 4:
        success = rabbit_game()
        if success:
            games_played += 1
        else:
            print("not success, breaking")
            break


def rabbit_game(lower_bound=-9999999999, upper_bound=9999999999) -> bool:
    """max 35 guesses"""

    chatbox: WebElement = locate("//div[@id='mess']")
    submit_button: WebElement = locate(xpath="//input[@id='mess_submit']")

    timestamp = locate(xpath="//td[@class='time_td']/span").get_attribute("title")
    delta = datetime.datetime.now() - datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    if delta.seconds > 60:
        type_in_chat(text=f"/number 0", entry_element=chatbox)
        click(given_element=submit_button)
        time.sleep(random.uniform(1.5, 3))
        rabbit_game(lower_bound, upper_bound)

    guess = (upper_bound + lower_bound) // 2

    time.sleep(random.uniform(0.2, 0.5))
    last_message = locate(xpath="//div[@class='mess_div']/div[@class='parsed']").text

    if "Меньше" in last_message:
        upper_bound = guess
    elif "Больше" in last_message:
        lower_bound = guess
    elif "это" in last_message:
        print("+4 кроля!")
        return True
    else:
        print(f"Произошла ошибка при парсинге сообщения с текстом {last_message}")
        return False

    type_in_chat(text=f"/number {guess}", entry_element=chatbox)
    click(given_element=submit_button)
    print(last_message)
    print(f"({lower_bound}, {upper_bound})\n")
    time.sleep(random.uniform(1.5, 3))
    rabbit_game(lower_bound, upper_bound)


def type_in_chat(text: str, entry_element: WebElement):
    text = list(text)
    for i in range(len(text)):
        entry_element.send_keys(text[i])
        if text[i - 1] == text[i]:
            time.sleep(random.uniform(0, 0.1))
            continue
        time.sleep(random.uniform(0, 0.3))
    if len(text) < 5:
        time.sleep(random.uniform(1, 3))


def cat_event(locations_checked=None):
    if locations_checked is None:
        locations_checked = []
    locations = get_availible_locations()
    current_location = locate("//span[@id='location']").text
    if current_location in locations_checked:
        go(random.sample(locations, 1))
        cat_event(locations_checked)

    free_cages = driver.find_elements(By.XPATH, "//td[@class='cage']/div[@class='cage_items' and not(*)]/..")
    cats_unchecked = get_cats_list()

    for cage in free_cages:
        click(given_element=cage)
        time.sleep(random.uniform(3, 5))
        cats_checked = event_action_with_cat(cats_unchecked)
        if cats_checked:
            cats_unchecked = [i for i in cats_unchecked if i not in cats_checked]
    locations_checked.append(current_location)
    cat_event(locations_checked)


def event_action_with_cat(cats_unchecked: list) -> list:
    selector = locate(xpath="//*[@id='mit']")
    dropdown_object = Select(selector)

    options_list = selector.find_elements(By.XPATH, "//option")
    names_list = [i.text for i in options_list]
    cats_checked = []

    for i in range(1, len(names_list)):
        try:
            if names_list[i] not in cats_unchecked:
                continue
            dropdown_object.select_by_visible_text(names_list[i])
            time.sleep(0.5)
            click(xpath="//*[@id='mitok']")
            time.sleep(0.5)
            do(["Поискать зацепки"])
            cats_checked.append(names_list[i])
        except (StaleElementReferenceException, ValueError):
            print("!!!!!!!! stale or value error")
            time.sleep(30)
            event_action_with_cat(cats_unchecked)
        except NoSuchElementException:
            print("no element?(")
            continue
        return cats_checked


def cat_search(names_to_search: list, forbidden_locations=("Таёжная тропа", "Обитель духов", "Морозная поляна")):
    # locations_checked = []
    cats_list = get_cats_list()
    for name in names_to_search:
        if name in cats_list:
            cat_element = locate(
                xpath=f"//span[@class='cat_tooltip']/u/a[text()='{name}']/../../preceding-sibling::*/*[1]")
            s = cat_element.get_attribute("style")
            url = re.findall(r'url\(\"(.*?)\.png', s)[0]
            url = "https://catwar.su/" + url + ".png"
            current_location = locate("//span[@id='location']").text
            print(
                f"\n\t\t\t !!! НАЙДЕН ИГРОК по имени {name}, ссылка на окрас: {url}, на локации {current_location} !!!")
            names_to_search.remove(name)
            if not names_to_search:
                return
    locations = get_availible_locations()
    location_headed = random.sample(locations, 1)
    while location_headed[0] in forbidden_locations:
        location_headed = random.sample(locations, 1)
    go(location_headed)
    cat_search(names_to_search)


def parse_top_args(args=None):
    if not args or len(args) != 4:
        print("Ошибка при парсинге аргумента.")
        return
    moons_start = 0 if args[0] == "?" else int(args[0])
    moons_end = 9999 if args[1] == "?" else int(args[1])
    gender, activity = args[2], args[3]
    search_cat_in_top(search_gender=gender, search_activity=activity, moons_from=moons_start, moons_to=moons_end)


def search_cat_in_top(search_gender="?", search_activity="?", moons_from=0, moons_to=9999):
    """ page_index = len(options_list) // 2
    change_top_page(page_index)"""

    driver.get("https://catwar.su/top")
    now = datetime.datetime.now()
    gender = search_gender

    driver.implicitly_wait(0)

    all_entries = driver.find_elements(By.XPATH, "//tr")
    count = 0
    wait = WebDriverWait(driver, 5)
    selector = locate(xpath="//select[@id='page']")
    options_list = selector.find_elements(By.XPATH, "//option")
    for j in range(1, len(options_list)):
        change_top_page(j)
        for i in range(2, len(all_entries)):
            if gender != "?":
                element = locate(xpath=f"//tbody/tr[{i}]/td[1]/a[@class='pol{gender}']")
                if not element:
                    continue
                wait.until(expected_conditions.none_of(expected_conditions.staleness_of(element)))
                name = element.text
                url = element.get_attribute("href")
            else:
                element = locate(xpath=f"//tbody/tr[{i}]/td[1]/a")
                wait.until(expected_conditions.none_of(expected_conditions.staleness_of(element)))
                name = element.text
                url = element.get_attribute("href")

            moons = 0
            if moons_to != 9999 or moons_from:
                reg = datetime.datetime.strptime(locate(xpath=f"//tr[{i}]/td[2]").text, '%Y-%m-%d %H:%M:%S')
                moons = (now - reg).days // 4
                if moons > moons_to:
                    break

            activity = locate(xpath=f"//tr[{i}]/td[3]").text
            is_match = True
            if moons in range(moons_from, moons_to):
                is_match = False if activity.lower() != search_activity and search_activity != "?" else is_match
                is_match = False if gender != search_gender and search_gender != "?" else is_match
                if not is_match:
                    continue
                if is_match:
                    count += 1
                    print(f"Найден игрок по имени {name}, ссылка: {url}")
    print(f"\t\tВсего найдено {count} совпадений.")
    driver.implicitly_wait(settings["max_waiting_time"])
    driver.get("https://catwar.su/cw3/")


def change_top_page(page_index: int):
    selector = locate(xpath="//select[@id='page']")
    while not selector:
        selector = locate(xpath="//select[@id='page']")
    dropdown_object = Select(selector)
    button = locate(xpath="//form/input[@type='submit']")

    dropdown_object.select_by_value(str(page_index))
    time.sleep(random.uniform(0.2, 0.5))
    click(given_element=button)
    time.sleep(random.uniform(0.1, 0.3))


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
             "wait": wait_for,
             "rabbit_game": start_rabbit_game,
             "investigate": cat_event,
             "parse_top": parse_top_args,
             ""
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
        print("Запуск в фоновом режиме... Может занять некоторое время.")
        options.add_argument("--headless")

    print("Вебдрайвер запускается, может занять некоторое время...")
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

    """build: pyinstaller --onefile --add-data=config.json main.py"""

    if driver.current_url != "https://catwar.su/cw3/":
        print("Для включения кликера вам необходимо залогиниться в варовский аккаунт.\n"
              "ВНИМАНИЕ: все ваши данные (почта и пароль) сохраняются в папке selenium, она создаётся \n"
              "в той же папке, куда вы поместили этот скрипт (main.py). НЕ ОТПРАВЛЯЙТЕ НИКОМУ папку selenium, \n"
              "для работы кликера нужен только main.py и config.json.\n"
              "Все команды кликера работают ИЗ ИГРОВОЙ!")
    else:
        pass
        info()

    try:
        while True:
            command = input(">>> ")
            if command != "q":
                multi_comm_handler(command)
            else:
                break
    except Exception as exception:
        crash_handler(exception)
