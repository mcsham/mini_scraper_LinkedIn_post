from loguru import logger
from playwright.async_api import async_playwright, Page, BrowserContext

from .install import install

logger.add("file_{time}.log", format="{time} {level} {message}", level="INFO")


class Browser:
    def __init__(self):
        self.playwright = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    async def exit(self):
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
        except Exception as e:
            logger.error(f'Browser exit error: {e}')

    async def _init_browser(self, name='Chrome', headless=False, ):
        await self.exit()
        try:
            if self.playwright is None:
                self.playwright = await async_playwright().start()
            arg = {
                'headless': headless,
                'locale': "en-EN",
                'user_data_dir': './user_data',
                'args': ["--start-maximized"],
                'no_viewport': True
            }
            match name:
                case 'Chrome':
                    install(self.playwright.chromium)
                    self.context = await self.playwright.chromium.launch_persistent_context(**arg)
                case 'Firefox':
                    install(self.playwright.firefox)
                    self.context = await self.playwright.firefox.launch_persistent_context(**arg)
                case 'Webkit':
                    install(self.playwright.webkit)
                    self.context = await self.playwright.webkit.launch_persistent_context(**arg)

            self.page = self.context.pages[0]
        except Exception as e:
            logger.error(f'Init browser is fail {e}')

    async def is_browser_close(self):
        return not self.page or self.page.is_closed()

    async def goto(self, url: str):
        try:
            await self.page.goto(url)
            return True
        except Exception as e:
            logger.error(f'Open url failed: {e}')
            return False
