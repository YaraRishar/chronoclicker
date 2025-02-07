import datetime
import json
import os
import sys
import time
import traceback


def print_timer(console_string: str, seconds: float, turn_off_timer=False) -> bool:
    """ Печатать таймер до окончания действия с подписью console_string """

    try:
        if turn_off_timer:
            seconds = round(seconds)
            print(f"{console_string}. Осталось {seconds // 60} мин {seconds % 60} с.")
            time.sleep(seconds)
            return False
        for i in range(round(seconds), -1, -1):
            sys.stdout.write(f"\r{console_string}. Осталось {i // 60} мин {i % 60} с.")
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write("\n")
        return False
    except KeyboardInterrupt:
        return True


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


def load_config() -> dict:
    """ Загрузить файл настроек config.json """

    try:
        with open("config.json", "r", encoding="utf-8") as file:
            parsed_json: dict = json.load(file)
            return parsed_json
    except FileNotFoundError:
        file = open("config.json", "w")
        file.close()
        load_config()


def rewrite_config(new_config: dict):
    """ Обновить файл настроек config.json при их изменении """

    with open("config.json", "w", encoding="utf-8") as file:
        file.write(json.dumps(new_config, ensure_ascii=False, indent=4))
    print("Настройки обновлены!")


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
        crashlog.writelines(["---CHRONOCLICKER CRASHLOG---", "\n", "Time: ", crash_time, "\n",

                            stacktrace])


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
