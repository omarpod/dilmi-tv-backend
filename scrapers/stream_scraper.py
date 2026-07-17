import asyncio
from playwright.async_api import async_playwright
import csv

async def scrape_streams():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # هنا ستضع رابط صفحة تفاصيل المباراة (يمكن تعديله ليدخل عدة روابط)
        await page.goto('https://www.yalla-kora.com/matches/', wait_until='networkidle')
        
        # استخراج روابط البث (المتوقع وجودها داخل إطار iframe أو صفحة فرعية)
        streams = await page.eval_on_selector_all('.match-item', '''elements => {
            return elements.map(el => {
                return {
                    team_names: el.querySelector('.team-a')?.innerText.trim() + " vs " + el.querySelector('.team-b')?.innerText.trim(),
                    stream_url: el.querySelector('iframe')?.src || "No Stream"
                };
            });
        }''')
        
        await browser.close()
        return streams

# حفظ الروابط في ملف منفصل
data = asyncio.run(scrape_streams())
with open('stream_links.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['match_name', 'stream_url'])
    for s in data:
        writer.writerow([s['team_names'], s['stream_url']])

print("تم استخراج روابط البث بنجاح في ملف stream_links.csv!")