import asyncio
from threading import Thread

from playwright.async_api import BrowserContext, async_playwright

from clicker_utils import SettingsManager
from page_wrapper import PageWrapper


class DriverWrapper:
    def __init__(self, settings_manager: SettingsManager):
        self.driver: None | BrowserContext = None
        self.page: None | PageWrapper = None

        self.driver_ready = asyncio.Event()

        self.settings_manager = settings_manager
        self.logger = settings_manager.get_logger()
        self.settings = settings_manager.get_settings()

        self.driver_loop = asyncio.new_event_loop()
        self.browser_thread = Thread(target=self.start_driver_loop, daemon=True)
        self.browser_thread.start()

        asyncio.run_coroutine_threadsafe(self.run_browser(), self.driver_loop)

    def start_driver_loop(self):
        asyncio.set_event_loop(self.driver_loop)
        self.driver_loop.run_forever()

    async def run_browser(self):
        p = await async_playwright().start()
        args = ["--start-maximized"]
        self.driver = await p.firefox.launch_persistent_context(
            headless=False,
            args=args,
            user_data_dir="playwright",
            no_viewport=True,
            is_mobile=False,
            has_touch=False
        )
        playwright_page = self.driver.pages[0]
        self.page = PageWrapper(playwright_page, self.settings_manager)
        await self.page.spoof_plugins()
        self.driver_ready.set()
        await self.page.goto(self.settings["catwar_url"] + "/cw3/")
        return self

    @staticmethod
    async def execute_browser_action(action, *args, **kwargs):
        if asyncio.iscoroutinefunction(action):
            return await action(*args, **kwargs)
        return None

    def close_browser(self):
        if self.driver_loop.is_running():
            self.driver_loop.stop()
