from bs4 import BeautifulSoup
import csv

def process_local_file(file_path):
    print(f"جاري قراءة الملف: {file_path}")
    
    try:
        # فتح وقراءة الملف من جهازك
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # هنا تضع الـ Selectors (الكلاسات) الخاصة بالمباريات
        # لاحظ: يجب أن تتأكد من الكلاسات الموجودة في ملفك المحفوظ
        matches = soup.select('.match-card') # قم بتغيير .match-card إذا لزم الأمر
        
        print(f"تم العثور على {len(matches)} مباراة في الملف.")
        
        # استخراج البيانات كما فعلنا سابقاً
        data = []
        for m in matches:
            # مثال لاستخراج البيانات
            home = m.select_one('.teamA .name').text.strip() if m.select_one('.teamA .name') else "N/A"
            away = m.select_one('.teamB .name').text.strip() if m.select_one('.teamB .name') else "N/A"
            data.append({'home': home, 'away': away})
            
        # حفظ النتائج
        with open('local_matches.csv', 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['home', 'away'])
            writer.writeheader()
            writer.writerows(data)
            print("تم استخراج البيانات بنجاح إلى local_matches.csv!")
            
    except FileNotFoundError:
        print("خطأ: الملف غير موجود. تأكد من وضعه في نفس المجلد.")

if __name__ == "__main__":
    process_local_file('matches.html')