import asyncio
import json
from playwright.async_api import async_playwright

def link_formatter(sym):
    return f"https://www.screener.in/company/{sym}/"

async def run_browser(name, pages):
    """Function to handle individual tab logic."""
    print(f"[{name}] Opening...")
    # This represents a context/tab
    async with async_playwright() as p:
        # 1. Launch Browser (Sync-like start within an Async loop)
        # browser = await p.chromium.launch(headless=True) # Set to True for less CPU usage
        # context = await browser.new_context()

        # 2. Open two tabs (Pages)
        # page1 = await context.new_page()
        # page2 = await context.new_page()

        # 3. Pairing Pages
        chunk_size = 2
        for idx in range(0, len(pages), chunk_size):
            pair_pages = tuple(pages[idx:idx+chunk_size])

            # 3. Run them concurrently
            if (len(pair_pages) == 1):
                print(f"[{name}] Navigating one tab...")
                # await asyncio.gather(
                #     page1.goto(pair_pages[0])
                # )
                print(pair_pages[0])
            else:
                print(f"[{name}] Navigating both tabs...")
                # await asyncio.gather(
                #     page1.goto(pair_pages[0]),
                #     page2.goto(pair_pages[1]),
                # )
                print(pair_pages[0], pair_pages[1])

            print(f"[{name}] Both tabs loaded. Waiting 5 seconds...")
            await asyncio.sleep(5)

        # # 4. Close Browser (Handles all tabs automatically)
        # await browser.close()
        print(f"[{name}] Browser closed.")

async def main(page_list):
    # Running the task
    chunk_size = 10
    session_id = 1
    for idx in range(0, len(page_list), chunk_size):
        await run_browser(f"Session_{session_id}", page_list[idx:idx+chunk_size])
        session_id += 1

if __name__ == "__main__":
    with open("/home/shrikar/web_apps/nifty_financial_results/starter_files.json", "r") as f:
        files = json.load(f)

    page_list = [link_formatter(sym.strip()) for sym in open(files['tracks'], 'r').readlines()]

    asyncio.run(main(page_list))


# Next Updates Required
# 1. Add a counter so that currently how many symbols are processed can be calculated
# 2. Add the Parser Functions
# 3. Convert the read data into dictionaries and upload them into DB (async)
