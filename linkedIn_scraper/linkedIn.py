import asyncio
import random
import re
from asyncio import sleep

import pandas as pd
from loguru import logger
from playwright.async_api import Page

from linkedIn_scraper.browser import Browser

semaphore = None


class LinkedIn(Browser):

    async def login(self):
        sign_in = self.page.locator('p > button', has_text='Sign in')
        if await sign_in.is_visible():
            await sign_in.click()
        login_field = self.page.locator('#session_key')
        if not await login_field.is_visible():
            return
        logger.info('Logging in...')
        await login_field.press_sequentially(self.login_record)
        password_field = self.page.locator('#session_password')
        await password_field.press_sequentially(self.password_record)
        await self.page.locator('button[type="submit"]', has_text='Sign in').click()
        logger.info('Logging in finish.')

    async def _parse_data(self, page: Page, url: str):
        data = []
        while await page.locator('div.feed-shared-update-v2').count() < self.count_posts:
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight);')
            await sleep(random.randrange(2, 5))
        for post in await page.locator('div.feed-shared-update-v2').all():
            await sleep(random.randrange(2, 5))
            more_el = post.locator('.feed-shared-inline-show-more-text__see-more-less-toggle').nth(0)
            if await more_el.is_visible():
                await more_el.click()
            profile_name = await (post.locator(
                ".update-components-actor__container .update-components-actor__title span span[aria-hidden='true']")
                                  .nth(0).inner_text())
            post_text_els = await post.locator(
                '.feed-shared-inline-show-more-text .update-components-text span.break-words').all()
            post_text = '\n'.join([await i.inner_text() for i in post_text_els])
            menu = post.locator('.feed-shared-control-menu__trigger')
            post_url = 'N/A'
            if await menu.is_visible():
                await menu.click()
                await sleep(random.randrange(3, 5))
                if await post.locator('.feed-shared-control-menu__content').is_visible():
                    await post.locator('li.feed-shared-control-menu__item').nth(1).click()
                    await sleep(random.randrange(3, 5))
                    post_url = await page.locator('.artdeco-toast-item__message > a').nth(0).get_attribute('href')
            data.append({
                "LinkedIn": url,
                "Profile Name": profile_name,
                "Post Text": post_text,
                "Post URL": post_url
            })

        self.data = pd.concat([self.data, pd.DataFrame(data)], ignore_index=True)

    async def _scape_data(self, link):
        async with semaphore:
            page: Page = await self.context.new_page()
            await page.goto(link)
            await self._parse_data(page, link)
            await page.close()

    async def scrape_datas(self):
        await self.goto(self.links['LinkedIn'][0])
        await self.login()
        await asyncio.gather(*[self.loop.create_task(self._scape_data(link)) for link in self.links['LinkedIn']])

    async def initialize(self, browser_name: str = 'Chrome', headless: bool = False):
        await self._init_browser(browser_name, headless)

    async def save_to_csv(self):
        self.data.to_csv(f"linkedin_posts.csv", index=False, sep=';')

    async def save_to_csv_by_profile_name(self):
        for profile_name, group in self.data.groupby("Profile Name"):
            filename = f"{re.sub(r'[^a-zA-Z0-9]', '_', profile_name)}.csv"
            group.to_csv(filename, index=False, encoding="utf-8", sep=';')

    def __init__(self, **kwargs):
        global semaphore
        super().__init__()
        link_path: str | None = kwargs.get('link_path', None)
        if link_path is not None:
            self.links = pd.read_csv(link_path)
        else:
            self.links = pd.DataFrame(columns=["LinkedIn"])
        self.data = pd.DataFrame(columns=["LinkedIn", "Profile Name", "Post Text", "Post URL"])
        self.login_record = kwargs.get('login')
        self.password_record = kwargs.get('password')
        self.count_posts = kwargs.get('count_post', 40)
        self.loop = kwargs.get('loop', asyncio.get_event_loop())
        semaphore = asyncio.Semaphore(kwargs.get('count_thread', 5))
