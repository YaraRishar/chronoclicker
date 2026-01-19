import asyncio
import datetime
import json
import logging
import os
import random
import traceback
from collections import deque
from logging import Logger

import chardet
from playwright.async_api import Locator


class SettingsManager:
    def __init__(self):
        self.logger = logging.getLogger("DriverLogger")

        now = datetime.datetime.now()
        folders = ["logs", "crashlogs", "resources"]
        for folder in folders:
            os.makedirs(folder, exist_ok=True)
        self.logfile_path = "logs//" + now.strftime("%y-%m-%d_%H.%M.%S") + ".log"
        format_log = "%(asctime)s | %(message)s"
        logging.basicConfig(filename=self.logfile_path,
                            level=logging.INFO,
                            format=format_log,
                            datefmt="%H:%M:%S")
        self.logger.info(f"ВЕРСИЯ КЛИКЕРА: {get_version()}")
        self.logger.info(f"Создан новый .log файл на пути: {self.logfile_path}")

        self.settings = load_json("config.json")
        self.aliases = load_json("aliases.json")
        self.gamedata: dict = load_json("gamedata.json")

        # self.action_dict = gamedata["actions"]
        # self.parameters_dict = gamedata["parameters"]
        # self.skills_dict = gamedata["skills"]

    def get_logger(self) -> Logger:
        _logger: logging.Logger = self.logger
        return _logger

    def get_settings(self) -> dict:
        _settings = self.settings
        return _settings

    def get_aliases(self) -> dict:
        _aliases = self.aliases
        return _aliases

    def get_gamedata(self) -> dict:
        _gamedata = self.gamedata
        return _gamedata

    def get_logpath(self) -> str:
        _logpath = self.logfile_path
        return _logpath


def get_version():
    try:
        with open("version.txt", "r") as file:
            chronoclicker_version = file.readline()
    except FileNotFoundError:
        return "NULL"
    return chronoclicker_version


def get_next_index(length, index=-1, direction=1) -> tuple[int, int]:
    """ Получить индекс следующей локации в патруле """

    index += direction
    if index == length and direction == 1:
        index -= 2
        direction = -1
    elif index == -1 and direction == -1:
        index += 2
        direction = 1
    return index, direction


def scroll_list(length, direction, previous_index) -> int:
    new_index = previous_index + direction
    if new_index < -length:
        new_index = -length
    elif new_index >= 0:
        new_index = -1

    return new_index


async def get_text_from_elements(elements: list) -> list[str]:
    text_contents = []
    for element in elements:
        text_contents.append(await element.inner_text())
    return text_contents


async def get_text(element: Locator, timeout: float | int=30) -> str:
    return await element.inner_text(timeout=timeout)


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


def rewrite_json(json_name: str, new_json: dict) -> None:
    """ Обновить файл настроек/сокращений при их изменении """

    with open(json_name, "w", encoding="utf-8") as file:
        file.write(json.dumps(new_json, ensure_ascii=False, indent=4))


def crash_handler(exception_type: Exception) -> None:
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


def pathfind(start, end, forbidden_cages=()) -> list[tuple[int, int]] | list:
    """ Найти кратчайший путь между двумя клетками на поле 6х10 """

    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    queue = deque([(start, [start])])
    visited = set(forbidden_cages)
    visited.add(start)

    while queue:
        current, path = queue.popleft()
        if current == end:
            return path[1:]

        for dx, dy in directions:
            next_x, next_y = current[0] + dx, current[1] + dy
            next_position = (next_x, next_y)
            if 0 <= next_x < 6 and 0 <= next_y < 10 and next_position not in visited:
                visited.add(next_position)
                queue.append((next_position, path + [next_position]))
    return []


def get_nearest_cages(current_position: tuple) -> list[tuple[int, int]]:
    directions = (-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)
    nearest_cages = []
    for direction in directions:
        next_x: int = current_position[0] + direction[0]
        next_y: int = current_position[1] + direction[1]
        if next_x in range(1, 7) and next_y in range(1, 11):
            nearest_cages.append((next_x, next_y))
    return nearest_cages


def get_key_by_value(dictionary: dict, look_for) -> str | int | None:
    result = next((key for key, value in dictionary.items() if value == look_for), None)
    return result


async def wait_for(start: float | int, end=None) -> None:
    if end is None:
        end = start + start / 10
    seconds = random.uniform(start, end)
    await asyncio.sleep(seconds)


def get_decoder(logfile_path: str) -> str:
    """ Возвращает название декодировщика, который подходит для вашей системы """

    with open(logfile_path, "rb") as f:
        raw_data = f.read(512)
        decoder = chardet.detect(raw_data)["encoding"]
        if not decoder or chardet.detect(raw_data)["confidence"] < 0.7:
            decoder = "utf-8"
    return decoder
