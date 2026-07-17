import asyncio
from playwright.async_api import async_playwright
import csv

async def scrape_live_matches():
    async with async_playwright() as p:
        # headless=False يعني ستشاهد المتصفح وهو يعمل أمامك
        browser = await p.chromium.launch(headless=False) 
        page = await browser.new_page()
        
        # الانتقال لصفحة المباريات
        await page.goto('https://www.yalla-kora.com/matches/', wait_until='networkidle')
        
        # استخراج البيانات
        # ملاحظة: إذا لم يجد شيئاً، سنقوم بتعديل الكلاسات بناءً على ما يظهر لك
        matches = await page.eval_on_selector_all('.match-item', '''elements => {
            return elements.map(el => {
                return {
                    home: el.querySelector('.team-a')?.innerText.trim(),
                    away: el.querySelector('.team-b')?.innerText.trim(),
                    score: el.querySelector('.score')?.innerText.trim()
                };
            });
        }''')
        
        await browser.close()
        return matches

# تشغيل السكربت وحفظ البيانات
if __name__ == "__main__":
    data = asyncio.run(scrape_live_matches())
    with open('live_matches.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['home_team', 'away_team', 'score'])
        for m in data:
            writer.writerow([m['home'], m['away'], m['score']])
    print(f"تم سحب {len(data)} مباراة بنجاح!")