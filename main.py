import asyncio
import datetime
import logging
import os
import random
import re
import threading
import time
import tkinter as tk
from functools import partial
from threading import Thread
from tkinter import ttk, scrolledtext, StringVar

from selenium.webdriver import Keys
from selenium.webdriver.common.by import By

import cage_utils
import clicker_utils
from clicker_utils import get_text
from browser_nav import DriverWrapper


class ChronoclickerGUI:
    def __init__(self):
        now = datetime.datetime.now()
        folders = ["logs", "crashlogs", "resources"]
        for folder in folders:
            os.makedirs(folder, exist_ok=True)
        self.logfile_path = "logs//" + now.strftime("%y-%m-%d_%H.%M.%S") + ".log"
        self.logger = logging.getLogger("DriverLogger")
        format_log = "%(asctime)s | %(message)s"
        logging.basicConfig(filename=self.logfile_path,
                            level=logging.INFO,
                            format=format_log,
                            datefmt="%H:%M:%S")
        self.logger.info(f"Создан новый .log файл на пути: {self.logfile_path}")

        self.script_task = None
        self.last_log_idx = 0
        self.previous_comms = []
        self.last_comm_idx = -1
        self.password_show_toggle = True

        self.config = clicker_utils.load_json("config.json")
        self.comm_dict = {
            "aliases": self.print_aliases,
            "patrol": self.patrol,
            # patrol  location1 - locationN
            "go": self.go,
            # go  location1 - locationN
            "do": self.do,
            # do action1 - actionN
            "alias": self.create_alias,
            # alias name comm_to_execute
            "settings": self.change_settings,
            # settings key - value
            "char": self.char,
            # char
            "info": self.info,
            # info
            "hist": self.hist,
            # hist
            "help": self.print_readme,
            # help
            "clear_hist": self.clear_hist,
            # clear_hist
            "refresh": self.refresh,
            # refresh
            "say": self.text_to_chat,
            # say message
            "cancel": self.cancel,
            # cancel
            "jump": self.jump_to_cage,
            # jump row - column
            "wait": self.wait,
            # wait seconds_from - seconds_to
            "rabbit_game": self.start_rabbit_game,
            # rabbit_game number_of_games_to_play
            "balance": self.print_rabbits_balance,
            # balance
            "inv": self.print_inv,
            # inv
            "c": self.print_cage_info,
            "с": self.print_cage_info,  # дубликат команды для с на латинице/кириллице
            # cage row - column
            "q": self.end_session,
            # q
            "bury": self.bury_handler,
            # bury item_img_id - level
            "loop": self.loop_handler,
            # loop alias_name
            "find_item": self.find_items,
            # find_items item_id1 - item_id2
            "find_cat": self.find_cats,
            # find_cat cat_name1 - cat_nameN
            "pathfind": self.pathfind_handler,
            # pathfind row - column
            "param": self.check_parameter,
            # param param_name
            "skill": self.check_skill,
            "findme": self.find_my_coords,
        }
        self.settings, self.alias_dict = self.config["settings"], self.config["aliases"]
        gamedata = clicker_utils.load_json("gamedata.json")
        self.action_dict, self.parameters_dict, self.skills_dict = (
            gamedata["actions"], gamedata["parameters"], gamedata["skills"])

        self.pause_event = asyncio.Event()
        self.stop_event = asyncio.Event()

        self.driver_loop = asyncio.new_event_loop()
        Thread(target=self.start_driver_loop, daemon=True).start()

        self.root = tk.Tk()
        self.root.geometry("800x600")
        self.root.iconphoto(False, tk.PhotoImage(file="resources/icon.png"))
        self.root.title("chronoclicker")
        self.loading_label = tk.Label(self.root, text="Загрузка...", font=("Verdana", 22))
        self.loading_label.pack(padx=200, pady=200)

        self.login_frame = tk.Frame(self.root)
        self.main_frame = tk.Frame(self.root)
        ttk.Style().configure("TButton", relief="flat")

        self.mail_entry = tk.Entry(self.login_frame)
        self.password_entry = tk.Entry(self.login_frame, show="*")
        self.password_show_btn = tk.Button(self.login_frame, text=u"\U0001F441",
                                           command=self.show_password, relief="flat")
        self.login_button = tk.Button(self.login_frame, text="Войти",
                                      command=self.do_login)
        self.login_status_label = tk.Label(self.login_frame, text="")

        self.log_area = scrolledtext.ScrolledText(self.main_frame)
        self.comm_entry = ttk.Entry(self.main_frame, width=50, font="Verdana")
        self.log_area.config(wrap=tk.WORD, state="disabled", font="Verdana")

        self.ok_btn = ttk.Button(self.main_frame, text="OK", width=5,
                                 command=self.ok_button_pressed)
        self.pause_btn = ttk.Button(self.main_frame, text=u"\u23F8", width=5,
                                    command=self.pause_script, state=tk.NORMAL)
        self.resume_btn = ttk.Button(self.main_frame, text=u"\u23F5", width=5,
                                     command=self.resume_script, state=tk.DISABLED)
        self.reload_btn = ttk.Button(self.main_frame, text=u"\u27F3", width=5,
                                     command=lambda: partial(self.main_frame.after, 0, self.update_log)(),
                                     state=tk.NORMAL)
        self.stop_btn = ttk.Button(self.main_frame, text=u"\u23F9", width=5,
                                   command=self.stop_event.set, state=tk.NORMAL)
        self.timer = StringVar()
        self.timer.set("Действие не выполняется.")
        self.timer_label = ttk.Label(self.main_frame, textvariable=self.timer, font="Verdana")

        self.driver: DriverWrapper = None
        asyncio.run_coroutine_threadsafe(self.open_browser(), self.driver_loop)
        asyncio.run_coroutine_threadsafe(self.run_script(comm_str="info"), self.driver_loop)

        partial(self.main_frame.after, 0, self.update_log)()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def show_login_screen(self):
        self.root.geometry("420x180")
        self.loading_label.destroy()
        tk.Misc.rowconfigure(self.login_frame, 0, weight=1)
        tk.Misc.columnconfigure(self.login_frame, 0, weight=1)
        self.login_frame.pack(padx=20, pady=20)
        tk.Label(self.login_frame, text="Почта:").grid(row=0, column=0)
        tk.Label(self.login_frame, text="Пароль:").grid(row=1, column=0)
        self.mail_entry.grid(row=0, column=1)
        self.password_entry.grid(row=1, column=1)
        self.password_show_btn.grid(row=1, column=2)
        self.login_button.grid(row=2, column=0, columnspan=2)
        self.login_status_label.grid(row=0, column=3, rowspan=2)

    def show_main_screen(self):
        if self.login_frame is not None:
            self.login_frame.destroy()
        if "cw3" not in self.driver.current_url:
            self.driver.get(self.driver.settings["catwar_url"] + "/cw3/")
            asyncio.run_coroutine_threadsafe(self.run_script(comm_str="info"), self.driver_loop)

        self.root.geometry("800x600")
        self.loading_label.destroy()
        tk.Misc.rowconfigure(self.main_frame, 0, weight=1)
        tk.Misc.columnconfigure(self.main_frame, 0, weight=1)
        self.main_frame.pack()
        self.log_area.grid(column=0, columnspan=5, row=0, rowspan=3, padx=10, pady=10)
        self.comm_entry.grid(column=0, row=4)
        self.timer_label.grid(column=0, row=3, padx=5)
        self.reload_btn.grid(column=2, row=3, padx=5)
        self.pause_btn.grid(column=3, row=3, padx=5)
        self.resume_btn.grid(column=3, row=4, padx=5)
        self.ok_btn.grid(column=1, row=4, padx=5, pady=10)
        self.stop_btn.grid(column=2, row=4)

        self.root.bind("<Return>", self.ok_button_pressed)
        self.root.bind("<Up>", self.up_button_pressed)
        self.root.bind("<Down>", self.down_button_pressed)

    def do_login(self):
        mail = self.mail_entry.get()
        password = self.password_entry.get()
        if not (mail or password):
            return
        self.login_button.config(text="Загрузка...")
        threading.Thread(target=self.run_login_sequence, args=(mail, password)).start()

    def run_login_sequence(self, mail, password):
        asyncio.run(self.driver.login_sequence(mail, password))
        time.sleep(1)
        if "login" not in self.driver.current_url:
            self.show_main_screen()
        else:
            self.login_button.config(text="Войти")
            self.login_status_label.config(text="Ошибка.\nНеверный логин \nили пароль.")

    def show_password(self):
        if self.password_show_toggle:
            self.password_entry.configure(show="")
        else:
            self.password_entry.configure(show="*")
        self.password_show_toggle = not self.password_show_toggle

    def ok_button_pressed(self, event=None):
        asyncio.run_coroutine_threadsafe(self.run_script(), self.driver_loop)
        partial(self.root.after, 0, self.update_log)()

        if not self.ensure_status():
            self.timer.set("Что-то пошло не так. Перезапустите кликер!")

        self.last_comm_idx = -1

    def up_button_pressed(self, event):
        prev_comm = self.previous_comms[self.last_comm_idx]

        self.comm_entry.select_clear()
        self.comm_entry.delete(0, tk.END)
        self.comm_entry.insert(0, prev_comm)

        self.last_comm_idx = clicker_utils.scroll_list(len(self.previous_comms), -1, self.last_comm_idx)

    def down_button_pressed(self, event):
        prev_comm = self.previous_comms[self.last_comm_idx]

        self.comm_entry.select_clear()
        self.comm_entry.delete(0, tk.END)
        self.comm_entry.insert(0, prev_comm)

        self.last_comm_idx = clicker_utils.scroll_list(len(self.previous_comms), 1, self.last_comm_idx)

    def ensure_status(self):
        """ Возвращает True, если webdriver instance работает и находится на сайте игры """
        if self.driver.service.is_connectable() and "catwar" in self.driver.current_url:
            return True
        return False

    def update_log(self):
        with open(self.logfile_path, 'rb') as file:
            file.seek(self.last_log_idx)
            new_lines = []
            for line in file:
                decoded_line = line.decode('utf-8').rstrip('\n')
                new_lines.append(decoded_line + '\n')
            self.last_log_idx = file.tell()
            if not new_lines:
                return
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, "".join(new_lines))
        self.log_area.see(tk.END)
        self.log_area.config(state="disabled")

    def start_driver_loop(self):
        asyncio.set_event_loop(self.driver_loop)
        self.driver_loop.run_forever()

    async def open_browser(self):
        self.driver: DriverWrapper = DriverWrapper(self.logger)
        self.ok_btn["state"] = tk.NORMAL
        if "login" in self.driver.current_url:
            self.show_login_screen()
            return
        self.show_main_screen()

    async def run_script(self, comm_str=None):
        self.pause_event.clear()
        self.stop_event.clear()
        self.comm_entry.select_clear()

        if comm_str is None:
            comm_str = self.comm_entry.get()
            self.previous_comms.append(comm_str)
            self.logger.info(f">>> {comm_str}")
            self.comm_entry.delete(0, tk.END)
        self.script_task = asyncio.run_coroutine_threadsafe(self.parse_command(comm_str), self.driver_loop)

    async def wait_for(self, start, end=None, do_random=True):
        if not do_random:
            await asyncio.sleep(start)
            await self.check_paused(0.01)
            return
        if end is None:
            end = start + start / 10
        await self.check_paused(0.1)
        seconds = random.uniform(start, end)
        await asyncio.sleep(seconds)
        await self.check_paused(0.1)

    async def print_timer(self, seconds: float, console_string=None):
        """ Печатать таймер до окончания действия с подписью console_string """

        if console_string is not None:
            for i in range(round(seconds), -1, -1):
                if self.stop_event.is_set() or self.script_task is None:
                    break
                self.timer.set(f"{console_string}. Осталось {i // 60} мин {i % 60} с.")
                await self.wait_for(1, do_random=False)
            self.timer.set("Действие не выполняется.")
            return

        message = await self.driver.get_action_str()
        message = message.replace("Отменить", "Введите cancel, чтобы отменить.")
        for i in range(round(seconds), -1, -1):
            if self.stop_event.is_set() or self.script_task is None:
                break

            console_string = re.sub(r"(\d*) мин", f"{i // 60} мин", message)
            console_string = re.sub(r"(\d*) с", f"{i % 60} с", console_string)
            self.timer.set(console_string)
            await self.wait_for(1, do_random=False)
        self.timer.set("Действие не выполняется.")

    async def trigger_long_break(self):
        """ Включение долгого перерыва после действия/перехода """

        if random.random() < self.settings["long_break_chance"]:
            seconds = random.uniform(self.settings["long_break_duration"][0],
                                     self.settings["long_break_duration"][1])
            await self.print_timer(console_string="Начался долгий перерыв",
                                   seconds=seconds)

    async def check_paused(self, seconds=0.1):
        partial(self.root.after, 0, self.update_log)()
        if self.stop_event.is_set():
            self.stop_script()
        # while self.pause_event.is_set() or self.stop_event.is_set():
        while self.pause_event.is_set():
            await asyncio.sleep(seconds)

    def stop_script(self):
        print("STOP SCRIPT")
        self.timer.set("Действие не выполняется.")
        self.script_task = None
        # self.stop_event.clear()

    def pause_script(self):
        self.pause_event.set()
        self.pause_btn["state"] = tk.DISABLED
        self.resume_btn["state"] = tk.NORMAL

    def resume_script(self):
        self.pause_event.clear()
        self.resume_btn["state"] = tk.DISABLED
        self.pause_btn["state"] = tk.NORMAL

    def on_close(self):
        self.stop_event.set()
        self.pause_event.clear()
        if self.driver is not None:
            self.driver.quit()
            partial(self.driver_loop.call_soon_threadsafe, self.driver_loop.stop)()
            # ^^^ WORKAROUND!!! Parameter 'args' unfilled, expected '*tuple[]'
        self.root.destroy()

    #   ///////////////////////////////////

    async def loop_handler(self, multi_comm=None):
        """ Повторять сокращение или команду бесконечно (как команда patrol и repeat)
         loop alias_name
         """
        if multi_comm is None:
            self.logger.info("Введите название сокращения или команду. Пример: loop do принюхаться - копать землю")
            return
        # if multi_comm[0] in self.driver.alias_dict.keys():
        #     alias_name = multi_comm[0]
        #     await self.loop_alias(alias_name)
        await self.loop_comm(multi_comm)

    async def loop_comm(self, comm):
        # True while not stopped and script is not None
        while not(self.stop_event.is_set() or self.script_task is None):
            print("self.stop_event.is_set()?", self.stop_event.is_set())
            print("self.script_task is None?", self.script_task is None)
            print("condition:", not(self.stop_event.is_set() or self.script_task is None))
            await self.multi_comm_handler(comm)
            await self.trigger_long_break()
        # self.stop_event.clear()

    async def multi_comm_handler(self, multi_comm: str):
        """ Исполнить каждую команду в мультикоманде по очереди """

        if not multi_comm:
            self.logger.info("Введите команду! Пример: patrol Морозная поляна - Каменная гряда")
            return False
        if multi_comm in self.alias_dict.keys():
            await self.multi_comm_handler(self.alias_dict[multi_comm])
            return True

        multi_comm_list: list = multi_comm.split("; ")
        first_word = multi_comm.split(" ")[0]
        if first_word == "alias":
            multi_comm = multi_comm.replace("alias ", "")
            return await self.create_alias(multi_comm)
        elif first_word == "loop":
            multi_comm = multi_comm.replace("loop ", "")
            return await self.loop_handler(multi_comm)
        for comm in multi_comm_list:
            print("multi_comm_list", multi_comm_list, "\ncomm", comm)
            await self.comm_handler(comm)

    async def comm_handler(self, comm: str) -> float | int | bool:
        """ Разделить ключевое слово команды и аргументы """

        try:
            main_comm = comm.split(" ")[0]
            comm = comm.replace(main_comm + " ", "")
            args = comm.split(" - ")
        except IndexError:
            self.logger.info("Ошибка в парсинге аргумента. Введите help для просмотра списка команд.")
            return False

        if main_comm == "alias":
            return await self.create_alias(comm)
        if main_comm not in self.comm_dict.keys():
            self.logger.info(f"Команда {main_comm} не найдена. Наберите help для просмотра списка команд.")
            partial(self.root.after, 0, self.update_log)()
            return False

        await self.check_paused(0.1)
        if comm == main_comm:
            result = await self.comm_dict[main_comm]()
        else:
            print(f"self.comm_dict[{main_comm}]({args})")
            result = await self.comm_dict[main_comm](args)
        partial(self.root.after, 0, self.update_log)()
        return result

    async def parse_command(self, comm: str):
        if " ? " in comm:
            await self.parse_condition(comm)
            return
        await self.multi_comm_handler(comm)

    async def parse_condition(self, comm):
        # param бодрость > 30 ? go Поляна для отдыха; do Поспать : wait 1
        condition_symbols = [" > ", " < ", " == ", " >= ", " <= ", " != "]
        condition = comm.split(" ? ")[0]  # param бодрость > 30
        symbol = False
        for i in range(len(condition_symbols)):
            if condition_symbols[i] in condition:
                symbol = condition_symbols[i]
                break
        if not symbol:
            return
        condition_comm = condition.split(symbol)  # ['param бодрость', '30']
        expected_value = condition_comm[1]  # 30
        real_value = await self.comm_handler(condition_comm[0])
        try:
            real_value = float(real_value)
            expected_value = float(expected_value)
        except ValueError:
            self.logger.info("value error")
            return

        result = eval(f"{real_value} {symbol} {expected_value}")
        ternary_list = comm.split(" ? ")[1].split(" : ")  # ['go Поляна для отдыха; do Поспать', 'wait 1']
        if result:
            await self.multi_comm_handler(ternary_list[0])
        else:
            await self.multi_comm_handler(ternary_list[1])

    #   ///////////////////////////////////

    def write_to_log(self, text):
        self.logger.info(text)
        partial(self.root.after, 0, self.update_log)()

    async def patrol(self, args=None):
        """Команда перехода, маршрут повторяется бесконечно
        (для маршрута из 3 локаций: 1 - 2 - 3 - 2 - 1 - 2 - 3 и так далее). Использование:
        patrol имя_локации1 - имя_локации2 - имя_локации3"""

        if args is None:
            self.logger.info("Для перехода нужны аргументы. Наберите help для вывода дополнительной информации.")
            return False
        if len(args) == 1:
            while True:
                await self.move_to_location(args[0], show_availables=False)
        index, direction = -1, 1
        while True:
            if self.stop_event.is_set() or self.script_task is None:
                return False
            index, direction = clicker_utils.get_next_index(len(args), index, direction)
            success = await self.move_to_location(args[index], show_availables=False)
            if not success:
                continue

    async def go(self, args=None) -> bool:
        """Команда перехода, маршрут проходится один раз. Использование:
        go имя_локации1 - имя_локации2 - имя_локации3"""

        if args is None:
            self.logger.info("Для перехода нужны аргументы. Наберите help для вывода дополнительной информации.")
            return False
        for index in range(len(args)):
            if self.stop_event.is_set() or self.script_task is None:
                return False
            success = await self.move_to_location(args[index], show_availables=True)
            if not success:
                continue
        return True

    async def do(self, args=None, show_availables=True) -> bool:
        """Команда для исполнения последовательности действий 1 раз. Использование:
        do действие1 - действие2 - действие3"""

        if await self.driver.is_held():
            self.driver.quit()
            return False
        if args is None:
            self.logger.info("Для действия нужны аргументы. Наберите help для вывода дополнительной информации.")
            return False
        args = [action.strip().lower() for action in args]
        for action in args:
            if self.stop_event.is_set() or self.script_task is None:
                return False
            if await self.driver.is_action_active():
                seconds = await self.driver.check_time()
                await self.print_timer(console_string="Действие уже совершается", seconds=seconds)
                return False
            available_actions = await self.driver.get_available_actions(self.action_dict)
            if action not in available_actions:
                self.logger.info(f'Действие "{action}" не может быть выполнено. Возможно, действие недоступно/'
                                 f'страница не прогрузилась до конца.'
                                 f'\nДоступные действия: {', '.join(available_actions)}.')
                continue
            action_active_sec = await self.driver.check_time()
            if action_active_sec != 1:
                await self.print_timer(seconds=action_active_sec + self.settings["short_break_duration"][1])
            await self.driver.click(
                f"//a[@data-id={self.action_dict[action]}][@class='dey has-tooltip']/img",
                offset_range=(30, 30))
            seconds = await self.driver.check_time() + random.uniform(
                self.settings["short_break_duration"][0],
                self.settings["short_break_duration"][1])
            await self.print_timer(seconds=seconds)
            if action == "принюхаться":
                self.logger.info(await self.driver.check_skill
                ("smell", clicker_utils.get_key_by_value(self.skills_dict, "smell")))
                await self.driver.click(xpath="//tr[@id='tr_tos']/td/table/tbody/tr/td[1]/button")
            elif action == "копать землю":
                self.logger.info(await self.driver.check_skill
                ("dig", clicker_utils.get_key_by_value(self.skills_dict, "dig")))
            elif action == "поплавать":
                self.logger.info(await self.driver.check_skill
                ("swim", clicker_utils.get_key_by_value(self.skills_dict, "swim")))

            if show_availables:
                self.logger.info(f"Доступные действия: {', '.join(
                    await self.driver.get_available_actions(self.action_dict))}")
        return True

    async def bury_handler(self, args=None):
        """ Закопать предмет с айди картинки id на глубину level:
        bury id - level
        Закопать все предметы во рту на глубину level:
        bury inv - level """

        if args is None or args == [""] or len(args) != 2:
            self.logger.info("Чтобы закопать предмет, введите айди его картинки и глубину закапывания.")
            return
        try:
            level = 1 if len(args) == 1 else int(args[1])
            level = 9 if level > 9 else level
            item_img_id = args[0]
            if item_img_id != "inv":
                item_img_id = int(args[0])
        except ValueError:
            self.logger.info("bury id_img - level или bury inv - level")
            return
        inv_items = await self.driver.get_inv_items()
        if not inv_items:
            self.logger.info("Во рту нет предметов!")
            return
        if item_img_id == "inv":
            for item in inv_items:
                await self.bury_item(item, level)
                level = 1
            return
        if item_img_id not in inv_items:
            self.logger.info(f"Предмета с айди {item_img_id} нет в инвентаре! Ссылка на изображение: "
                             f"{self.settings['catwar_url']}/cw3/things/{item_img_id}.png")
            return
        await self.bury_item(item_img_id, level)

    async def cancel(self) -> bool:
        """Отменить действие. Использование:
        cancel"""

        success = await self.driver.click(xpath="//a[@id='cancel']")
        if success:
            self.stop_event.set()
            self.logger.info("Действие отменено!")
            self.timer.set("Действие не выполняется.")
            return True
        self.logger.info("Действие не выполняется.")
        return False

    async def clear_hist(self):
        """Команда 'очистить историю', использование:
        clear_hist"""

        await self.driver.click(xpath="//a[@id='history_clean']")
        self.logger.info("История очищена.")

    async def hist(self):
        """Команда для вывода истории действий из Игровой, использование:
        hist"""

        self.logger.info("История:")
        hist_list = await self.driver.get_hist_list()
        for item in hist_list:
            self.logger.info(f"{item}.")

    async def char(self) -> bool:
        """ Команда для вывода информации о персонаже с домашней страницы/Игровой. Использование:
        char """

        self.driver.get(self.settings["catwar_url"])
        rank = await self.driver.locate_element('''//div[@id='pr']/i''', do_wait=False)

        self.logger.info(f"Имя: {get_text(await self.driver.locate_element('''//div[@id='pr']/big'''))}")
        if rank:
            self.logger.info(f"Должность: {get_text(rank)}\n")
        self.logger.info(
            f"Луны: {get_text(await self.driver.locate_element('''//div[@id='pr']/table/tbody/tr[2]/td[2]/b'''))}"
            f"\nID: {get_text(await self.driver.locate_element('''//b[@id='id_val']'''))}\n"
            f"Активность: {get_text(await self.driver.locate_element('''//div[@id='act_name']/b'''))}")
        self.driver.back()
        self.logger.info(await self.driver.check_skill("smell",
                                                       clicker_utils.get_key_by_value(
                                                           self.skills_dict, "smell")))
        self.logger.info(await self.driver.check_skill("dig",
                                                       clicker_utils.get_key_by_value(
                                                           self.skills_dict, "dig")))
        self.logger.info(await self.driver.check_skill("swim",
                                                       clicker_utils.get_key_by_value(
                                                           self.skills_dict, "swim")))
        self.logger.info(await self.driver.check_skill("might",
                                                       clicker_utils.get_key_by_value(
                                                           self.skills_dict, "might")))
        self.logger.info(await self.driver.check_skill("tree",
                                                       clicker_utils.get_key_by_value(
                                                           self.skills_dict, "tree")))
        self.logger.info(await self.driver.check_skill("observ",
                                                       clicker_utils.get_key_by_value(
                                                           self.skills_dict, "observ")))
        return True

    async def info(self) -> bool:
        """Команда для вывода информации о состоянии игрока из Игровой. Использование:
        info"""

        if self.driver.current_url != f"{self.settings['catwar_url']}/cw3/":
            return False
        current_location = await self.driver.get_current_location()
        self.logger.info(f"Текущая локация: {current_location}\n"
                         f"Доступные локации: {', '.join(await self.driver.get_available_locations())}\n"
                         f"Доступные действия: {', '.join(await self.driver.get_available_actions(self.action_dict))}")
        await self.driver.print_cats()
        self.logger.info(f"\tЗдоровье:\t\t{await self.driver.get_parameter('health')}%\n"
                         f"\t Бодрость:\t\t{await self.driver.get_parameter('dream')}%\n"
                         f"\t Чистота:\t\t{await self.driver.get_parameter('clean')}%\n"
                         f"\t Голод:\t\t{await self.driver.get_parameter('hunger')}%\n"
                         f"\t Жажда:\t\t{await self.driver.get_parameter('thirst')}%\n"
                         f"\t Нужда:\t\t{await self.driver.get_parameter('need')}%")

        self.logger.info("Последние 5 записей в истории (введите hist, чтобы посмотреть полную историю):")
        hist_list = await self.driver.get_hist_list()
        self.logger.info(f"\t{'.\n\t'.join(hist_list[-6:])}.")
        return True

    async def text_to_chat(self, message=None) -> bool:
        """Написать сообщение в чат Игровой"""

        if message is None or len(message) != 1:
            self.logger.info("say message")
            return False
        message = message[0]
        await self.driver.type_in_chat(text=message, entry_xpath="//input[@id='text']")
        await self.driver.click("//*[@id='msg_send']")
        return True

    async def wait(self, seconds=None) -> bool:
        """ Ничего не делать рандомное количество времени от seconds_start
        до seconds_end секунд либо ровно seconds секунд
         seconds: list = [seconds_start, seconds_end]"""

        if seconds is None or len(seconds) > 2:
            self.logger.info("Введите количество секунд! wait seconds_from - seconds_to ИЛИ wait seconds")
            return False
        if len(seconds) == 1:
            await self.print_timer(console_string="Начато ожидание",
                                   seconds=float(seconds[0]))
            return True
        try:
            seconds[0], seconds[1] = int(seconds[0]), int(seconds[1])
        except (IndexError, ValueError):
            self.logger.info("wait seconds_from - seconds_to ИЛИ wait seconds")
            return False
        seconds: float = random.uniform(int(seconds[0]), int(seconds[1]))
        await self.print_timer(console_string="Начато ожидание", seconds=seconds)
        return True

    async def print_inv(self):
        inv_ids = await self.driver.get_inv_items()
        self.logger.info("Предметы во рту:")
        for i in inv_ids:
            self.logger.info(f"{self.settings['catwar_url']}/cw3/things/{i}.png")

    async def find_items(self, items_to_seek=None):
        """ Искать перечисленные предметы по разным локациям, поднимать их, если найдены """

        if not items_to_seek:
            self.logger.info("find_item item_id - item_id")
            return
        items_to_seek = [int(item) for item in items_to_seek]
        cages_list = await self.driver.get_cages_list()
        for cage in cages_list:
            items_on_cage = await cage.get_items()
            if not items_on_cage:
                continue
            for item in items_on_cage:
                if item in items_to_seek:
                    self.logger.info(f"found item with id {item}")
                    await cage.pick_up_item()
        available_locations = await self.driver.get_available_locations()
        random_location = random.sample(available_locations, 1)
        await self.go(random_location)
        await self.find_items(items_to_seek)

    async def find_cats(self, args=None):
        """ Найти кота по его имени или ID на локациях, рандомно переходя по ним """

        if args is None:
            self.logger.info("find_cat имя_кота")
            return False

        names_to_find: list = args
        while names_to_find:
            cat_name, location, row, column = await self.driver.find_cat_on_loc(names_to_find)
            if cat_name:
                self.logger.info(f"Кот {cat_name} найден в локации {location} на клетке {row}x{column}!")
                names_to_find.remove(cat_name)
                if not names_to_find:
                    return True
                continue
            available_locations = await self.driver.get_available_locations()
            random_location = random.sample(available_locations, 1)
            await self.go(random_location)

    async def pathfind_handler(self, end: tuple, forbidden_cages_given=()):
        """ Найти путь по клеткам от вашего местоположения до end. Использование:
         pathfind row - column"""

        end = int(end[0]), int(end[1])
        end_cage = cage_utils.Cage(self.driver, end[0], end[1])
        if end_cage.is_move() or end_cage.has_cat():
            self.logger.info(f"Клетка {end} занята котом или переходом!")
            return
        my_coords = await self.find_my_coords(verbose=False)
        cages = await self.driver.get_cages_list()
        forbidden_cages = [_ for _ in forbidden_cages_given]

        for cage in cages:
            if cage.is_move() or cage.has_cat():
                forbidden_cages.append((cage.row, cage.column))

        path = clicker_utils.pathfind(start=my_coords, end=end, forbidden_cages=forbidden_cages)
        for cage in path:
            await self.jump_to_cage(cage, verbose=False)
        await self.driver.print_cats()

    async def jump_to_cage(self, args=None, verbose=True) -> int:
        if not args or len(args) != 2:
            self.logger.info("jump row - column")
            return -1
        row, column = args
        cage = cage_utils.Cage(self.driver, row, column)
        await cage.jump()
        if verbose:
            self.logger.info(f"Прыжок на {row} ряд, {column} клетку.")
        return 0

    async def check_parameter(self, args=None) -> float | int:
        """ Команда для проверки параметра parameter_name.
        Возвращает float или int - значение параметра в процентах.
         param бодрость"""

        if args is None or len(args) != 1:
            self.logger.info("param parameter_name")
            return -1
        param_name: str = args[0].strip().lower()
        if param_name not in self.parameters_dict:
            self.logger.info("param_name not in parameters_dict")
            return -1
        param_name_server = self.parameters_dict[param_name]
        param_value = await self.driver.get_parameter(param_name=param_name_server)
        self.logger.info(f"{param_name.capitalize()} - {param_value}")
        return param_value

    async def check_skill(self, args=None) -> int:
        """ Команда для проверки навыка skill_name. Возвращает fint - значение дроби навыка ('числитель').
         skill ун """

        if args is None or len(args) != 1:
            self.logger.info("skill аббревиатура_навыка")
            return -1
        skill_name: str = args[0].strip().lower()
        if skill_name not in self.skills_dict:
            self.logger.info("Невалидное имя навыка! Примеры: нюх, копание, боевые умения, "
                             "плавательные умения, зоркость, лазание")
            return -1
        skill_name_server = self.skills_dict[skill_name]
        skill_value = await self.driver.check_skill(skill_name_server, skill_name)
        self.logger.info(skill_value)
        skill_fraction = re.search(r"\((\d*)/", skill_value)
        if not skill_fraction:
            return -1
        return int(skill_fraction[1])

    async def print_rabbits_balance(self):
        """ Вывести баланс кролей игрока """

        self.driver.get(f"{self.settings['catwar_url']}/rabbit")
        rabbit_balance = get_text(await self.driver.locate_element(
            "//img[@src='img/rabbit.png']/preceding-sibling::b"))
        await self.wait_for(0.5, 1.5)
        self.driver.back()
        self.logger.info(f"Кролей на счету: {rabbit_balance}")

    async def print_readme(self):
        """ Вывести содержимое файла README.md или ссылку на него. Использование:
         help """

        if not os.path.exists("README.md"):
            self.logger.info("Файла справки README.md не существует или он удалён.\n"
                             "Справка на GitHub: "
                             "https://github.com/YaraRishar/chronoclicker?tab=readme-ov-file#chronoclicker")
            self.driver.get("https://github.com/YaraRishar/chronoclicker?tab=readme-ov-file#chronoclicker")
            return
        with open("README.md", "r", encoding="utf-8") as readme:
            for line in readme:
                self.logger.info(line)

    async def print_cage_info(self, args=()):
        """ Вывести всю информацию о клетке в Игровой """

        if not args or len(args) != 2:
            self.logger.info("c row - column")
            return
        cage = cage_utils.Cage(self.driver, row=args[0], column=args[1])
        await cage.pretty_print()

    async def start_rabbit_game(self) -> bool:
        """ Начать игру в числа с Лапом, после 5 игр вернуться в cw3. Использование:
         rabbit_game"""

        self.driver.get(f"{self.settings['catwar_url']}/chat")
        await self.wait_for(1, 3)
        await self.driver.click("//a[@data-bind='openPrivateWith_form']")
        await self.driver.type_in_chat("Системолап", entry_xpath="//input[@id='openPrivateWith']")
        await self.driver.click("//*[@id='openPrivateWith_form']/p/input[2]")

        games_played = 0
        while games_played != 5:
            await self.driver.rabbit_game()
            games_played += 1
        self.driver.get(f"{self.settings['catwar_url']}/cw3/")
        return True

    async def change_settings(self, args=None) -> bool:
        """Команда для изменения настроек. Использование:
        settings key - value
        (Пример: settings is_headless - True)"""

        if args is None or len(args) != 2:
            message = ""
            for key, value in self.settings.items():
                message += f"\t{key} - {value}\n"
            self.logger.info(message)
            return False
        key, value = args
        try:
            if key in ("driver_path", "my_id", "catwar_url"):
                self.settings[key] = value
            else:
                self.settings[key] = eval(value)
        except ValueError:
            self.logger.info("Ошибка в парсинге аргумента.")
            return False
        clicker_utils.rewrite_config(self.config)
        self.logger.info("Настройки обновлены!")
        return True

    async def refresh(self):
        """Перезагрузить страницу"""

        self.driver.refresh()
        self.logger.info("Страница обновлена!")

    async def print_aliases(self):
        message = ""
        for alias_name, comm in self.alias_dict.items():
            message += f"\t{alias_name}: {comm}\n"
        self.logger.info(message)

    async def create_alias(self, comm) -> bool:
        """Команда для создания сокращений для часто используемых команд.
        Использование:
        alias name comm
        Пример:
        alias кач_актив patrol Морозная поляна - Поляна для отдыха
        В дальнейшем команда patrol Морозная поляна - Поляна для отдыха будет исполняться при вводе кач_актив"""

        try:
            main_alias_comm = comm.split(" ")[1]
        except IndexError:
            self.logger.info("Ошибка в парсинге сокращения. Пример использования команды:"
                             "\nalias кач_актив patrol Морозная поляна - Поляна для отдыха")
            return False
        if main_alias_comm not in self.comm_dict.keys():
            self.logger.info(f"Команда {main_alias_comm} не найдена, сокращение не было создано.")
            return False
        name = comm.split(" ")[0]
        comm_to_alias = comm.replace(name + " ", "")
        self.config["aliases"][name] = comm_to_alias
        self.logger.info(f"Создано сокращение команды {comm_to_alias} под именем {name}.")
        clicker_utils.rewrite_config(self.config)
        return True

    async def move_to_location(self,
                               location_name: str, show_availables=False) -> bool:
        """ Общая функция для перехода на локацию """

        if await self.driver.is_held():
            self.driver.quit()

        if await self.driver.is_action_active():
            seconds = await self.driver.check_time()
            await self.print_timer(console_string="Действие уже совершается", seconds=seconds)
            return False
        elements = await self.driver.locate_elements(f"//span[text()='{location_name.replace(" (о)", "")}' "
                                                     f"and @class='move_name']/preceding-sibling::*")
        if not elements:
            return False
        random_element = random.sample(elements, 1)[0]
        has_moved = await self.driver.click(given_element=random_element,
                                            offset_range=(40, 70))
        if " (о)" in location_name:
            seconds = random.uniform(0.5, 3)
            await self.print_timer(console_string=f"Совершён переход с отменой в локацию {location_name}",
                                   seconds=seconds)
            await self.driver.click(xpath="//a[@id='cancel']")
            await self.wait_for(1, 3)
            return has_moved
        seconds = await self.driver.check_time() + random.uniform(self.settings["short_break_duration"][0],
                                                                  self.settings["short_break_duration"][1])
        await self.print_timer(console_string=f"Совершён переход в локацию {location_name}",
                               seconds=seconds)
        if show_availables:
            self.logger.info(f"Доступные локации: {', '.join(await self.driver.get_available_locations())}")
        await self.trigger_long_break()
        self.logger.info(f"Совершён переход в локацию {location_name}.")

        return has_moved

    async def bury_item(self, item_img_id: str, level: int):
        await self.driver.click(xpath=f"//div[@class='itemInMouth']/img[@src='things/{item_img_id}.png']",
                                offset_range=(10, 10))
        await self.wait_for(0.3, 0.6)
        slider = await self.driver.locate_element(
            "//div[@id='layer']/span[@class='ui-slider-handle ui-state-default ui-corner-all']")
        await self.driver.click(given_element=slider)
        while level != 1:
            await self.wait_for(0.1, 0.5)
            slider.send_keys(Keys.ARROW_RIGHT)
            level -= 1
        await self.driver.click(xpath="//a[text()='Закопать']")
        seconds = await self.driver.check_time() + random.uniform(
            self.settings["short_break_duration"][0], self.settings["short_break_duration"][1])
        await self.print_timer(seconds=seconds)

    async def find_my_coords(self, verbose=True) -> (int, int):
        my_info = await self.driver.find_cat_on_loc([self.settings["my_id"]])
        my_coords = my_info[2:]
        if verbose:
            current_location = self.driver.get_current_location()
            self.logger.info(f"Вы находитесь на локации «{current_location}» на клетке {my_coords[0]}x{my_coords[1]}.")
        return my_coords

    async def get_last_cw3_message_volume(self) -> int:
        chatbox = await self.driver.locate_element(xpath="//div[@id='chat_msg']")
        msg_element = chatbox.find_element(By.XPATH, value="//span/table/tbody/tr/td/span")
        if not msg_element:
            self.logger.info("В Игровой нет сообщений.")
            return -1
        volume_str = msg_element.get_attribute("class")
        volume = int("".join([i for i in volume_str if i.isdigit()]))
        return volume

    async def check_for_warning(self) -> bool:
        """ *CONSTRUCTION NOISES* """

        error_element = await self.driver.locate_element(xpath="//p[id='error']")
        error_style = error_element.get_attribute("style")
        return bool("block" in error_style)

    async def check_cage(self, cage_to_check: tuple, max_checks=10) -> int:
        """ *CONSTRUCTION NOISES* """

        checks = 0
        safe_cage = await self.find_my_coords(verbose=False)
        current_msg_count = self.count_cw3_messages()
        danger_level = -2
        while checks < max_checks:
            await self.jump_to_cage(cage_to_check, verbose=False)
            last_msg_count = self.count_cw3_messages()
            if last_msg_count > current_msg_count:
                danger_level = self.get_last_cw3_message_volume()
                break
            await self.wait_for(1, 2)
            await self.jump_to_cage(safe_cage, verbose=False)
        self.logger.info(f"danger_level {danger_level}" )
        return danger_level

    async def count_cw3_messages(self) -> int:
        chatbox = await self.driver.locate_element("//div[@id='chat_msg']")
        msg_list = chatbox.find_elements(By.XPATH, value="//span/table/tbody/tr/td/span")
        return len(msg_list)

    async def end_session(self):
        """ Завершить текущую сессию и закрыть вебдрайвер. Использование:
         q """

        self.logger.info("\nВебдрайвер закрывается...")
        self.on_close()

if __name__ == "__main__":
    app = ChronoclickerGUI()