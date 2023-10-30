from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import time
import random
import json


def check_time() -> int:
    """Проверить, сколько времени осталось до окончания действия.
    Если никакое действие в данный момент не выполняется, возвращает 1."""

    xpath_string = "//span[@id='sek']"
    try:
        element = driver.find_element(By.XPATH, xpath_string)
    except NoSuchElementException:
        return 1
    seconds = eval((element.text.replace(' мин ', '*60+')).replace(' с', ''))
    return seconds


def locator(text: str, elem_type: str, offset_range=(40, 60), do_click=True, get_text=False) -> str:
    """Найти элемент на странице по xpath. Возвращает true/false в зависимости от того, было ли выполнено действие."""

    xpath_string = xpath_dict[elem_type].format(text=text)
    try:
        element = driver.find_element(By.XPATH, xpath_string)
    except NoSuchElementException:
        print(f"Элемент {text} не найден.")
        return ""
    if do_click:
        return clicker(element, offset_range=offset_range)
    if get_text:
        return element.text


def clicker(element, offset_range=(40, 60)) -> str:
    """Кликает по элементу element с оффсетом offset_range"""

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
    return "+1"


def action(alt_comm="", args=""):
    if alt_comm == "--endless" or alt_comm == "-e":
        while True:
            for i in range(len(args)):
                locator(action_dict.get(args[i]), "action", (30, 30))
                time.sleep(check_time() + random.uniform(1, 5))
    else:
        for i in range(len(args)):
            success = locator(action_dict.get(args[i]), "action", (30, 30))
            if success:
                time.sleep(check_time() + random.uniform(1, 5))
            else:
                try:
                    i += 1
                    continue
                except IndexError:
                    print("Действие не может быть выполнено.")


def move(alt_comm="", args=""):
    """Команда перехода. Если присутствует модификатор --endless или -e, то маршрут повторяется
    бесконечно (для маршрута из 3 локаций: 1 - 2 - 3 - 2 - 1 - 2 и так далее)."""

    if not args:
        print('Для перехода нужны аргументы. Наберите help move для вывода дополнительной информации.')
        return
    if not alt_comm:
        for loc in args:
            locator(loc, "move")
            time.sleep(check_time() + random.uniform(1, 5))
    elif alt_comm == "--endless" or "-e":
        index = -1
        direction = 1
        while True:
            index += direction
            if index == len(args) and direction == 1:
                index -= 2
                direction = -1
            elif index == -1 and direction == -1:
                index += 2
                direction = 1
            success = locator(args[index], "move")
            if success:
                if random.random() < settings["long_break_chance"]:
                    seconds = check_time() + random.uniform(100, 1000)
                    time.sleep(seconds)
                else:
                    seconds = check_time() + random.uniform(3, 20)
                    time.sleep(seconds)
            else:
                continue


def comm_handler(comm: str):
    """Разделить ключевое слово команды, модификатор и аргументы"""

    if comm in alias_dict.keys():
        comm_handler(alias_dict[comm])
    comm_list = comm.split(' ')
    try:
        main_comm = comm_list[0]
        alt_comm = comm_list[1] if comm_list[1][0] != '(' else ''
    except IndexError:
        print("Ошибка синтаксиса.")
        return

    if main_comm == "alias":
        args = ' ('.join(comm.split(' (')[1:3:])[:-1]
    else:
        args = comm.split(' (')[1].rstrip(')').split(' - ') if comm_list[-1][-1] == ')' else ''

    if main_comm in comm_dict.keys():
        return comm_dict[main_comm](alt_comm, args)
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


def change_settings(args=''):
    key, value = args[0], args[1]
    if key != "is_headless":
        config[0][key] = eval(value)
    else:
        config[0][key] = value
    rewrite_config(config)


def check_ls():
    locator("newls", "ls")
    print()


comm_dict = {"move": move,
             # move --alt_comm (location1 - locationN)
             "action": action,
             # action --alt_comm (action1 - action2)
             "alias": create_alias,
             # alias name (comm_to_execute)
             "settings": change_settings
             # settings (key - value)
             }

alt_list = ["--endless", "-e", ""]

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
