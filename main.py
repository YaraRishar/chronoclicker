from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, MoveTargetOutOfBoundsException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
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

    element = locate("//span[@id='sek']")
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
    element = locate(f"//span[@id='{param_name}']/*/*/*/descendant::*")
    if not element:
        return -1
    pixels = int(element.get_attribute("style").split("px")[0].split("width: ")[1])
    percents = round(pixels / 150 * 100, 2)
    if percents == int(percents):
        return int(percents)
    return percents


def check_skill(skill_name) -> str:
    mouse_over(xpath=f"//span[@id='{skill_name}']/*/*/*/descendant::*")
    tooltip_elem = locate("//div[@id='tiptip_content']")
    if not tooltip_elem.text:
        mouse_over(xpath=f"//span[@id='{skill_name}']/*/*/*/descendant::*", hover_for=0.01)
    level_elem = locate(f"//table[@id='{skill_name}_table']")
    return tooltip_elem.text + ", уровень " + level_elem.text


def swim(escape_to_location=""):
    availible_locations = get_availible_actions()
    if escape_to_location and escape_to_location not in availible_locations:
        print("Для отсыпа введите название локации, соседней с плавательной!")
    elif not escape_to_location:
        action_loop(["Поплавать"])
    while True:
        sleep_pixels = check_parameter("dream")
        if sleep_pixels < settings["critical_sleep_pixels"]:
            current_location = locate("//span[@id='location']").text
            move_to_location(escape_to_location)
            action(["Поспать"])
            move_to_location(current_location)
        action(["Поплавать"])


def is_cw3_disabled() -> bool:
    try:
        cw3_disabled_element = driver.find_element(By.XPATH, "//body[text()='Вы открыли новую вкладку с Игровой, "
                                                             "поэтому старая (эта) больше не работает.']")
        if cw3_disabled_element:
            return True
    except NoSuchElementException:
        return False


def locate(xpath: str) -> WebElement | None:
    """Найти элемент на странице по XPath. """

    try:
        element = driver.find_element(By.XPATH, xpath)
        return element
    except NoSuchElementException:
        if is_cw3_disabled():
            refresh()
            locate(xpath)
        else:
            return None


def click(xpath: str, offset_range=(0, 0)) -> bool:
    """Кликает по элементу element с оффсетом offset_range.
    Возвращает True, если был совершён клик по элементу. """

    element = locate(xpath)
    if not element or not element.is_displayed():
        return False
    random_offset = (random.randint(-offset_range[0], offset_range[0]),
                     random.randint(-offset_range[1], offset_range[1]))
    action_chain = ActionChains(driver)
    try:
        action_chain.scroll_to_element(element).perform()
        action_chain.move_to_element_with_offset(to_element=element,
                                                 xoffset=random_offset[0],
                                                 yoffset=random_offset[1]
                                                 ).perform()
        action_chain.click_and_hold().perform()
    except MoveTargetOutOfBoundsException:
        print("MoveTargetOutOfBoundsException raised for reasons unknown to man(")
    time.sleep(random.uniform(0, 0.2))
    action_chain.release().perform()
    time.sleep(random.uniform(0.01, 0.3))
    return True


def mouse_over(xpath: str, hover_for=0.1) -> bool:
    element = locate(xpath)
    if not element or not element.is_displayed():
        return False
    action_chain = ActionChains(driver)
    action_chain.scroll_to_element(element).perform()
    action_chain.move_to_element(element).perform()
    time.sleep(hover_for)
    return True


def is_action_active() -> bool:
    element = locate(xpath="//a[@id='cancel']")
    if element:
        return True
    return False


def cancel():
    element = locate(xpath="//a[@id='cancel']")
    if element:
        click(xpath="//a[@id='cancel']")


def action_loop(args=None):
    """Команда для бесконечного повторения действий по списку из arg. """
    if not args or args == [""]:
        print("Для зацикленного действия нужны аргументы. Наберите comm_help для вывода дополнительной информации.")
        return
    while True:
        action(args)


def action(args=None):
    if not args or args == [""]:
        print("Для действия нужны аргументы. Наберите comm_help для вывода дополнительной информации.")
        return
    for i in range(len(args)):
        success = click(xpath=f"//*[@id='akten']/a[@data-id={action_dict[args[i]]}]/img",
                        offset_range=(30, 30))
        if success:
            seconds = check_time() + random.uniform(settings["short_break_duration"][0],
                                                    settings["short_break_duration"][1])
            last_hist_entry = locate("//span[@id='ist']").text.split(".")[-2]
            print(f"{last_hist_entry}. Действие продлится {round(seconds)} секунд.")
            monitor_cw3_chat(seconds)

            if args[i] == "Принюхаться":
                print(check_skill("smell"))
                click(xpath="//input[@value='Вернуть поле']")
            elif args[i] == "Копать землю":
                print(check_skill("dig"))
            elif args[i] == "Поплавать":
                print(check_skill("swim"))
            print(f"Доступные действия: {', '.join(get_availible_actions())}")
        else:
            if is_action_active():
                print("Действие уже совершается! Чтобы отменить, введите cancel.")
                return
            print(f"Действие {args[i]} не может быть выполнено. Возможно, действие недоступно/"
                  f"страница не прогрузилась до конца.")
            continue


def patrol(args=None):
    """Команда перехода, маршрут повторяется бесконечно
    (для маршрута из 3 локаций: 1 - 2 - 3 - 2 - 1 - 2 - 3 и так далее)."""

    if not args or args == [""]:
        print("Для перехода нужны аргументы. Наберите comm_help для вывода дополнительной информации.")
        return
    index, direction = -1, 1
    while True:
        index, direction = get_next_index(len(args), index, direction)
        success = move_to_location(args[index])
        if not success:
            continue


def go(args=None):
    """Команда перехода, маршрут проходится один раз. """

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
    if location_name not in locations:
        print(f"Локация {location_name} недоступна. Доступные локации: {', '.join(locations)}.")
        return False
    has_moved = click(xpath=f"//span[text()='{location_name}']/preceding-sibling::*",
                      offset_range=(45, 70))
    seconds = check_time() + random.uniform(3, 20)
    if random.random() < settings["long_break_chance"]:
        print("long break triggered")
        seconds += random.uniform(settings["long_break_duration"][0], settings["long_break_duration"][1])
    print(f"Совершён переход в {location_name}, до следующего действия {round(seconds)} секунд.")
    print(f"Доступные локации: {', '.join(get_availible_locations())}")
    print_cats()
    monitor_cw3_chat(seconds)

    return has_moved


def get_availible_locations() -> list:
    elements = driver.find_elements(By.XPATH, "//span[@class='move_name']")
    locations_list = [element.text for element in elements]
    return locations_list


def get_availible_actions() -> list:
    elements = driver.find_elements(By.XPATH, "//div[@id='akten']/a[@class='dey']")
    actions_list = []
    for element in elements:
        for key, value in action_dict.items():
            if int(element.get_attribute("data-id")) == value:
                actions_list.append(key)
                break
    return actions_list


def print_cats():
    xpath = "//span[@class='cat_tooltip']/u/*"
    elements = driver.find_elements(By.XPATH, xpath)
    cats_list = [element.get_attribute(name="innerText") for element in elements]
    if cats_list:
        print("Коты на локации:")
        for i in range(len(cats_list)):
            if not i % 5:
                print("\t\t" + ", ".join(cats_list[i:i + 5]))


def info():
    """Команда для вывода информации о состоянии игрока из Игровой."""

    current_location = locate("//span[@id='location']").text
    while current_location == "[ Загружается… ]":
        current_location = locate("//span[@id='location']").text

    print(f"Текущая локация: {current_location}.")
    print(f"Доступные действия: {', '.join(get_availible_actions())}")
    print(f"Доступные локации: {', '.join(get_availible_locations())}")
    print_cats()

    print(f"\tСонливость:  {check_parameter('dream')}%")
    print(f"\tГолод:\t\t {check_parameter('hunger')}%")
    print(f"\tЖажда:\t\t {check_parameter('thirst')}%")
    print(f"\tНужда:\t\t {check_parameter('need')}%")
    print(f"\tЗдоровье:\t{check_parameter('health')}%")
    print(f"\tЧистота: \t {check_parameter('clean')}%")

    print("Последние 5 записей в истории (введите hist, чтобы посмотреть полную историю):")
    hist_list = locate("//span[@id='ist']").text.split('.')[-6:-1]
    print(f"\t{'. '.join(hist_list)}.")


def char():
    """Команда для вывода информации о персонаже с домашней страницы/Игровой."""

    driver.get("https://catwar.su/")

    print(f"Имя: {locate('''//div[@id='pr']/big''').text}\n"
          f"Должность: {locate('''//div[@id='pr']/i''').text}\n"
          f"Луны: {locate('''//div[@id='pr']/table/tbody/tr[2]/td[2]/b''').text}\n"
          f"ID: {locate('''//b[@id='id_val']''').text}\n"
          f"Активность: {locate('''//div[@id='act_name']/b''').text}")
    driver.get("https://catwar.su/cw3/")
    print(check_skill("smell"))
    print(check_skill("dig"))
    print(check_skill("swim"))
    print(check_skill("might"))


def hist():
    print("История:")
    hist_list = locate("//span[@id='ist']").text.split(".")[:-1]
    for item in hist_list:
        print(item)


def clear_hist():
    click(xpath="//a[@id='history_clean']")
    print("История очищена.")


def get_last_cw3_message() -> tuple:
    try:
        last_message = locate(xpath="//*[@id='chat_msg']/span[1]/table/tbody/tr/td[1]/span/span").text
        name_from = locate(xpath="//*[@id='chat_msg']/span[1]/table/tbody/tr/td[1]/span/b").text
    except AttributeError:
        return '', ''
    return last_message, name_from


def monitor_cw3_chat(monitor_until_time: float):
    current_time = time.time() + monitor_until_time
    temp_message = ('', '')
    while time.time() <= current_time:
        time.sleep(1)
        message_bundle = get_last_cw3_message()
        if message_bundle == temp_message:
            continue
        else:
            message_time = datetime.datetime.now()
            print(f"Чат |\t{message_bundle[0]} - {message_bundle[1]} | {message_time.strftime('%H:%M:%S')}")
        temp_message = message_bundle


def text_to_chat(message: str):
    chat_entry = locate(xpath="//input[@id='text']")
    chat_entry.send_keys(message)
    click(xpath="//*[@id='msg_send']")


def get_next_index(length, index=-1, direction=1):
    """Техническая функция для получения индекса следующей локации в патруле."""

    index += direction
    if index == length and direction == 1:
        index -= 2
        direction = -1
    elif index == -1 and direction == -1:
        index += 2
        direction = 1
    return index, direction


def comm_handler(comm: str):
    """Техническая функция, разделяющая ключевое слово команды и аргументы."""

    if comm in alias_dict.keys():
        comm_handler(alias_dict[comm])

    try:
        main_comm = comm.split(" ")[0]
        comm = comm.replace(main_comm + " ", "")
        args = comm.split(" - ")
    except IndexError:
        print("Ошибка в парсинге аргумента. Введите comm_help для просмотра списка команд.")
        return
    # comm = name patrol loc1 - loc2
    if main_comm == "alias" and comm.split(" ")[1] in comm_dict.keys():
        name = comm.split(" ")[0]
        comm_to_alias = comm.replace(name + " ", "")
        args = name, comm_to_alias

    if main_comm in comm_dict.keys():
        if args:
            return comm_dict[main_comm](args)
        else:
            return comm_dict[main_comm]()
    else:
        print("Команда не найдена. Наберите comm_help для просмотра списка команд.")
        pass


def load_config() -> dict:
    """Техническая функция, загружающая файл настроек config.json."""

    try:
        with open("config.json", "r", encoding="utf-8") as file:
            parsed_json: dict = json.load(file)
            return parsed_json
    except FileNotFoundError:
        file = open("config.json", "w")
        file.close()
        load_config()


def rewrite_config(new_config):
    """Техническая функция, обновляющая файл настроек config.json при их изменении."""

    with open("config.json", "w") as file:
        file.write(json.dumps(new_config, ensure_ascii=False, indent=4))


def create_alias(args=()):
    """Команда для создания сокращений для часто используемых команд.
    Использование:
    alias name comm
    Пример:
    alias кач_актив patrol Морозная поляна - Поляна для отдыха
    В дальнейшем команда patrol Морозная поляна - Поляна для отдыха будет исполняться при вводе кач_актив"""

    name, comm = args
    config[-1][name] = comm
    rewrite_config(config)


def change_settings(args=""):
    key, value = args
    if key != "is_headless":
        config[0][key] = eval(value)
    else:
        config[0][key] = value
    rewrite_config(config)


def crash_handler(exception_type: Exception):
    if type(exception_type).__name__ == "KeyboardInterrupt":
        pass
    now = datetime.datetime.now()
    crash_time = now.strftime("%y-%m-%d_%H.%M.%S")
    path = os.path.dirname(__file__)
    if not os.path.exists(f"{path}/crashlogs"):
        os.mkdir(f"{path}/crashlogs")
    filename = os.path.join(path, f"crashlogs/crash-{crash_time}.txt")
    with open(filename, "w") as crashlog:
        stacktrace = traceback.format_exc()
        crashlog.writelines(["---CHRONOCLICKER CRASHLOG---", "\n", "time:", crash_time, "\n", stacktrace])


def comm_help():
    print(comm_dict.keys())


def refresh():
    driver.refresh()


def driver_exit():
    driver.quit()


comm_dict = {"patrol": patrol,
             # patrol  location1 - locationN
             "go": go,
             # go  location1 - locationN
             "action": action,
             # action action1 - actionN
             "action_loop": action_loop,
             # action_loop action1 - actionN
             "alias": create_alias,
             # alias name comm_to_execute
             "settings": change_settings,
             # settings "key: value" key:value
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
             "q": driver_exit
             # q
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
    config = load_config()
    settings = config["settings"]
    action_dict = config["actions"]
    alias_dict = config["aliases"]

    if settings["is_headless"] == "True":
        options.add_argument("--headless")

    if settings["driver_path"]:
        driver_path = settings["driver_path"]
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=options)
    else:
        driver = webdriver.Chrome(options=options)

    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)

    driver.implicitly_wait(settings["max_waiting_time"])
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
            if not command:
                print("Введите команду! Пример: patrol Морозная поляна - Каменная гряда")
                continue
            comm_handler(command)
    except Exception as exception:
        crash_handler(exception)
