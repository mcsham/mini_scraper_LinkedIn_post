import asyncio
import os

from linkedIn_scraper.linkedIn import LinkedIn
from dotenv import load_dotenv

load_dotenv()


async def main(_loop):
    linked_in = LinkedIn(
        loop=_loop,
        count_thread=int(os.getenv('COUNT_THREAD')),
        link_path=os.path.join(os.getcwd(), "linkedin.csv"),
        login=os.getenv('LOGIN'),
        password=os.getenv('PASSWORD'),
        count_post=int(os.getenv('COUNT_POST')),
    )
    await linked_in.initialize(browser_name='Chrome', headless=False)
    await linked_in.scrape_datas()
    if os.getenv('SAVE_FROM_PROFILE_NAMES') == 'TRUE':
        await linked_in.save_to_csv_by_profile_name()
    else:
        await linked_in.save_to_csv()


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main(loop))
