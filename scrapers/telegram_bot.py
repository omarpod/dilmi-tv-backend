from telethon import TelegramClient, events
import requests
from bs4 import BeautifulSoup
import csv
import re
from datetime import datetime

# بياناتك الخاصة
api_id = 31157931
api_hash = '87c658df33bf9d8907019697dd23bc79'
phone = '+213770774731'

client = TelegramClient('bot_session', api_id, api_hash)

def extract_links_from_url(blog_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(blog_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        iframes = soup.find_all('iframe')
        
        extracted = []
        for iframe in iframes:
            src = iframe.get('src')
            if src and "facebook" not in src and "blogspot" not in src:
                extracted.append(src)
        return extracted
    except:
        return []

@client.on(events.NewMessage(chats='@YallaShootLiveLinks'))
async def handler(event):
    message_text = event.raw_text
    urls = re.findall(r'https://[^\s<>"]+blogspot\.com[^\s<>"]+', message_text)
    
    if urls:
        print(f"[{datetime.now()}] اكتشاف رابط جديد: {urls[0]}")
        links = extract_links_from_url(urls[0])
        
        if links:
            # 1. حفظ في ملف CSV
            with open('live_links.csv', 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for link in links:
                    writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), urls[0], link])
            
            # 2. إرسال تنبيه لك مباشرة على تليجرام
            alert_msg = f"⚠️ **تنبيه مباراة جديدة!**\n\nالرابط: {urls[0]}\nتم استخراج {len(links)} روابط بث.\n\nقم بتجهيز الشعارات وأسماء الفريقين!"
            await client.send_message('me', alert_msg)
            
            print(f"تم حفظ {len(links)} روابط بث وإرسال التنبيه.")

print("البوت يعمل الآن ويراقب القناة...")
client.start(phone)
client.run_until_disconnected()