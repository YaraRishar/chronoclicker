from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import time
import random

options = webdriver.ChromeOptions()
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


def locator(text, elem_type):
    random_offset = (random.randint(-50, 50), random.randint(-75, 75))
    action_chain = ActionChains(driver)
    if elem_type == "move":
        xpath_string = f"//span[text()='{text}']/preceding-sibling::*"
    elif elem_type == "dey":
        xpath_string = f"//*[@class='move_parent'][@data-id='{dey_dict.get(text)}']/descendant::*"
    else:
        print('xpath not recognised')
        return
    try:
        element = driver.find_element(By.XPATH, xpath_string)
    except NoSuchElementException:
        print(f"Элемент {text} не найден.")
        return
    # action_chain.scroll_by_amount(0, random.randint(0, 800)).perform()
    action_chain.scroll_to_element(element).perform()
    action_chain.move_to_element_with_offset(to_element=element,
                                             xoffset=random_offset[0],
                                             yoffset=random_offset[1]
                                             ).perform()
    action_chain.click().perform()
    print("+1")

# move --endless (Морозная поляна - Поляна для отдыха)
# move --endless (Великое Древо - Морозная поляна)


def move(alt_comm='', args=''):
    if not args:
        print('Для перехода нужны аргументы. Наберите help move для вывода дополнительной информации.')
        return
    if not alt_comm:
        for loc in args:
            locator(loc, 'move')
            time.sleep(150 + random.uniform(1, 5))
    elif alt_comm == "--endless":
        print('endless confirmed')
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
            print("moving to ", args[index])
            locator(args[index], 'move')
            if random.random() < long_break_chance:
                print("long break triggered")
                time.sleep(150 + random.uniform(100, 1000))
            else:
                time.sleep(150 + random.uniform(1, 10))
    pass


def comm_handler(comm):
    comm_list = comm.split(' ')
    main_comm = comm_list[0]
    alt_comm = comm_list[1] if comm_list[1][0] == '-' else ''
    args = comm.split(' (')[1].rstrip(')').split(' - ') if comm_list[-1][-1] == ')' else ''

    if main_comm in comm_dict.keys():
        return comm_dict[main_comm](alt_comm, args)
    else:
        print('Команда не найдена. Наберите help для просмотра списка команд.')
        pass


def create_alias(name, comm):
    pass


comm_dict = {"move": move,
             "action": 'act',
             "help": 'comm_help',
             "alias": create_alias}

alt_list = ["--endless", "-e", ""]

dey_dict = {"Поспать": 1,
            "Вылизаться": 3,
            "Принюхаться": 13}

xpath_dict = {"move": "//span[text()='{text}']/preceding-sibling::*"}

long_break_chance = 0.005

# mainloop
config = open("config.txt", "a")
while True:
    command = input()
    comm_handler(command)
    if command == "exit":
        driver.quit()
        break
