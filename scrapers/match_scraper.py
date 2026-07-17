from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_flashscore():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # نستخدم context لضمان تحميل الصفحة بشكل كامل
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
        page = context.new_page()
        
        url = "https://www.flashscore.com/"
        print(f"جاري جلب البيانات من: {url}")
        
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # زيادة وقت الانتظار والتأكد من وجود العنصر الأساسي
            page.wait_for_selector(".event__match", timeout=20000)
            
            # استخراج محتوى الصفحة بعد اكتمال التحميل
            soup = BeautifulSoup(page.content(), 'html.parser')
            matches = soup.select('.event__match')
            
            print(f"تم العثور على {len(matches)} حاوية مباريات.")
            
            for m in matches:
                # استخدام find بدلاً من select_one لتجنب الانهيار إذا كان العنصر مفقوداً
                home_elem = m.find('div', class_='event__participant--home')
                away_elem = m.find('div', class_='event__participant--away')
                
                if home_elem and away_elem:
                    home = home_elem.text.strip()
                    away = away_elem.text.strip()
                    print(f"المباراة: {home} vs {away}")
                else:
                    print("تم العثور على حاوية مباراة ولكن لا يمكن قراءة الأسماء.")
            
        except Exception as e:
            print(f"فشل السكربت: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_flashscore()