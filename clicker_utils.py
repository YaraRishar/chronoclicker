import datetime
import json
import os
import random
import sys
import time
import traceback


def print_timer(console_string: str, seconds: float):
    for i in range(round(seconds), -1, -1):
        sys.stdout.write(f"\r{console_string}. Осталось {i // 60} мин {i % 60} с.")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\n")


def trigger_long_break(long_break_chance: float, long_break_duration: list):
    """ Включение долгого перерыва после действия/перехода """

    if random.random() < long_break_chance:
        seconds = random.uniform(long_break_duration[0], long_break_duration[1])
        print_timer(console_string="Начался долгий перерыв", seconds=seconds)


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

    print("crash handler called!")
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
