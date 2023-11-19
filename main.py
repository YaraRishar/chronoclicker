from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, MoveTargetOutOfBoundsException
from selenium.webdriver.common.action_chains import ActionChains
import time
import random
import json
import re


def check_time() -> int:
    """Проверить, сколько времени осталось до окончания действия.
    Если никакое действие в данный момент не выполняется, возвращает 1."""

    xpath_string = "//span[@id='sek']"
    try:
        element = driver.find_element(By.XPATH, xpath_string)
    except NoSuchElementException:
        return 1
    match_seconds = re.match(r"(\d*) мин (\d*) с", element.text)
    if not match_seconds:
        match_seconds = re.match(r"(\d*) с", element.text)
        seconds = int(match_seconds[1])
    else:
        seconds = int(match_seconds[1]) * 60 + int(match_seconds[2])
    return seconds


def locate(text: str, xpath_key: str):
    xpath_val = xpath_dict[xpath_key].format(text=text)
    try:
        element = driver.find_element(By.XPATH, xpath_val)
        return element
    except (NoSuchElementException, MoveTargetOutOfBoundsException):
        print(f"Элемент {text} не найден.")
        return ""


def click(text, xpath_key, offset_range=(45, 45)):
    """Кликает по элементу element с оффсетом offset_range"""

    element = locate(text, xpath_key)
    if not element:
        return False
    random_offset = (random.randint(-offset_range[0], offset_range[0]),
                     random.randint(-offset_range[1], offset_range[1]))
    action_chain = ActionChains(driver)
    action_chain.scroll_to_element(element).perform()
    action_chain.move_to_element_with_offset(to_element=element,
                                             xoffset=random_offset[0],
                                             yoffset=random_offset[1]
                                             ).perform()
    action_chain.click_and_hold().perform()
    time.sleep(random.uniform(0, 0.5))
    action_chain.release().perform()
    time.sleep(random.uniform(0.1, 0.5))
    return True


def action(alt_comm="", args=""):
    if alt_comm == "--endless" or alt_comm == "-e":
        while True:
            for i in range(len(args)):
                locate(action_dict.get(args[i]), "action")
                time.sleep(check_time() + random.uniform(1, 5))
    else:
        for i in range(len(args)):
            success = locate(action_dict.get(args[i]), "action")
            if success:
                time.sleep(check_time() + random.uniform(1, 5))
            else:
                try:
                    i += 1
                    continue
                except IndexError:
                    print("Действие не может быть выполнено.")


def patrol(args=""):
    """Команда перехода, маршрут повторяется бесконечно
    (для маршрута из 3 локаций: 1 - 2 - 3 - 2 - 1 - 2 и так далее)."""

    if not args:
        print("Для перехода нужны аргументы. Наберите help move для вывода дополнительной информации.")
    index, direction = get_next_index(len(args))
    while True:
        index = get_next_index(len(args), index, direction)[0]
        direction = get_next_index(len(args), index, direction)[1]
        success = click(args[index], "move")
        time.sleep(0.2)
        if success:
            if random.random() < settings["long_break_chance"]:
                seconds = check_time() + random.uniform(100, 1000)
                time.sleep(seconds)
            else:
                seconds = check_time() + random.uniform(3, 20)
                print("Совершён переход в ", args[index], ", до следующего действия ", round(seconds), " секунд.")
                time.sleep(seconds)
        else:
            continue


def go(args=""):
    """Команда перехода, маршрут проходится один раз до конца."""

    if not args:
        print("Для перехода нужны аргументы. Наберите help move для вывода дополнительной информации.")
    for loc in args:
        click(loc, "move")
        time.sleep(check_time() + random.uniform(1, 5))


def get_next_index(length, index=-1, direction=1):
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

    if comm in alias_dict.keys():
        comm_handler(alias_dict[comm])
    comm_list = comm.split(' ')
    main_comm = comm_list[0]
    if main_comm == "alias":
        args = ' ('.join(comm.split(' (')[1:3:])[:-1]
    else:
        args = comm.split(' (')[1].rstrip(')').split(' - ') if comm_list[-1][-1] == ')' else ''

    if main_comm in comm_dict.keys():
        return comm_dict[main_comm](args)
    else:
        print('Команда не найдена. Наберите help для просмотра списка команд.')
        pass


def load_config() -> list:
    try:
        with open("config.json", "r", encoding="utf-8") as file:
            parsed_json = json.load(file)
            return parsed_json
    except FileNotFoundError:
        file = open("config.json", "w")
        file.close()
        load_config()


def rewrite_config(new_config):
    with open("config.json", "w") as file:
        file.write(json.dumps(new_config, ensure_ascii=False, indent=4))


def create_alias(name, comm):
    """Использование:
    alias name (comm)
    Пример:
    alias кач_актив (move --endless (Морозная поляна - Поляна для отдыха))
    В дальнейшем команда в скобках будет исполняться при вводе кач_актив"""

    config[-1][name] = comm
    rewrite_config(config)


def change_settings(args=""):
    key, value = args
    if key != "is_headless":
        config[0][key] = eval(value)
    else:
        config[0][key] = value
    rewrite_config(config)


comm_dict = {"patrol": patrol,
             # patrol  (location1 - locationN)
             "go": go,
             # patrol  (location1 - locationN)
             "action": action,
             # action (action1 - action2)
             "alias": create_alias,
             # alias name (comm_to_execute)
             "settings": change_settings
             # settings "key: value" key:value
             }

# mainloop

config = load_config()
settings, xpath_dict, action_dict, alias_dict = config[0], config[1], config[2], config[3]

options = webdriver.ChromeOptions()

if settings["is_headless"] == "True":
    options.add_argument("--headless")

options.add_argument("user-data-dir=selenium")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
driver = webdriver.Chrome(options=options)

stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )

driver.get("https://catwar.su/cw3/")
time.sleep(2)

while True:
    command = input()
    comm_handler(command)
    if command == "exit":
        driver.quit()
        break

# ДРЕВНИЕ МУДРОСТИ
# regex в обработке строки в check_time - ок
# try except keyboard interrupt
# index & direction плохо (спрятать в next_index(index, len)) - ок
