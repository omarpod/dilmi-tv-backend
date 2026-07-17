import requests
import csv

def fetch_matches_api():
    url = "https://www.scorebat.com/video-api/v3/"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            matches = data.get('response', [])
            
            results = []
            for match in matches:
                home = match.get('homeTeam', {}).get('name', 'Unknown')
                away = match.get('awayTeam', {}).get('name', 'Unknown')
                
                # استخراج رابط البث (الـ embed الأول المتاح)
                videos = match.get('videos', [])
                embed_link = ""
                if videos:
                    # نقوم باستخراج رابط src الموجود داخل كود الـ iframe
                    # هذا الجزء يبحث عن الرابط داخل نص الـ HTML الخاص بالـ embed
                    raw_embed = videos[0].get('embed', '')
                    if "src='" in raw_embed:
                        embed_link = raw_embed.split("src='")[1].split("'")[0]

                results.append({
                    'home_team': home,
                    'away_team': away,
                    'match_datetime': match.get('date', '').replace('T', ' ').replace('Z', ''),
                    'competition': match.get('competition', 'General'),
                    'stream_link': embed_link  # هذا هو رابط البث الجديد
                })
            
            fieldnames = ['home_team', 'away_team', 'match_datetime', 'competition', 'stream_link']
            with open('live_matches.csv', 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
            print(f"تم استخراج {len(results)} مباراة مع روابط البث!")
    except Exception as e:
        print(f"حدث خطأ: {e}")

if __name__ == "__main__":
    fetch_matches_api()