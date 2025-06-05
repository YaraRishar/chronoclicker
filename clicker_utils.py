import asyncio
import datetime
import json
import os
import random
import traceback

from selenium.webdriver.remote.webelement import WebElement


def get_next_index(length, index=-1, direction=1):
    """ Получить индекс следующей локации в патруле """

    index += direction
    if index == length and direction == 1:
        index -= 2
        direction = -1
    elif index == -1 and direction == -1:
        index += 2
        direction = 1
    return index, direction


def scroll_list(length, direction, previous_index):
    new_index = previous_index + direction
    if new_index < -length:
        new_index = -length
    elif new_index >= 0:
        new_index = -1

    return new_index


def load_json(filename: str) -> dict:
    """ Загрузить файл настроек и данных об игре """

    try:
        with open(filename, "r", encoding="utf-8") as file:
            parsed_json: dict = json.load(file)
            return parsed_json
    except FileNotFoundError:
        file = open(filename, "w")
        file.close()
        load_json(filename)
        return {}


def rewrite_config(new_config: dict):
    """ Обновить файл настроек config.json при их изменении """

    with open("config.json", "w", encoding="utf-8") as file:
        file.write(json.dumps(new_config, ensure_ascii=False, indent=4))


def crash_handler(exception_type: Exception):
    """ Создать крашлог в папке crashlogs, которая находится на том же уровне, что и main.py """

    now = datetime.datetime.now()
    crash_time = now.strftime("%y-%m-%d_%H.%M.%S")
    path = os.path.dirname(__file__)
    if not os.path.exists(f"{path}/crashlogs"):
        os.mkdir(f"{path}/crashlogs")
    crash_path = os.path.join(path, f"crashlogs/crash-{crash_time}.txt")
    print(f"Кликер вылетел, тип ошибки: {type(exception_type).__name__}. Крашлог находится по пути {crash_path}")
    with open(crash_path, "w") as crashlog:
        stacktrace = traceback.format_exc()
        crashlog.writelines(["---CHRONOCLICKER CRASHLOG---", "\n", "Time: ", crash_time, "\n", stacktrace])


def pathfind(start, end, forbidden_cages=()) -> list:
    """ Найти кратчайший путь между двумя клетками на поле 6х10 """

    directions = (-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)
    queue = [(start, [start])]
    visited = set()
    visited.add(start)
    for cell in forbidden_cages:
        visited.add(cell)

    while queue:
        current, path = queue.pop(0)
        if current == end:
            return path[1:]

        for direction in directions:
            next_x = current[0] + direction[0]
            next_y = current[1] + direction[1]
            next_position = (next_x, next_y)

            if next_x in range(1, 7) and next_y in range(1, 11) and next_position not in visited:
                visited.add(next_position)
                queue.append((next_position, path + [next_position]))
    print(f"Не удалось найти путь от клетки {start} до клетки {end}!")
    return []


def get_key_by_value(dictionary: dict, look_for):
    result = next((key for key, value in dictionary.items() if value == look_for), None)
    return result


def get_text(element: WebElement, max_retries=5, retries=0) -> str:
    try:
        return element.text
    except AttributeError:
        if retries == max_retries:
            return ""
        return get_text(element, max_retries, retries + 1)


async def wait_for(start: float | int, end=None):
    if end is None:
        end = start + start / 10
    seconds = random.uniform(start, end)
    await asyncio.sleep(seconds)
