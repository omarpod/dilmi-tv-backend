"""
apps/core/integrations/ar_translations.py
-----------------------------------------------
ترجمة عربية لأسماء أشهر الأندية والبطولات — قاموس ثابت (Mapping)، وليس
ترجمة آلية حقيقية. لا يوجد لدينا وصول لخدمة ترجمة مدفوعة (Google
Translate API وغيرها)، فهذا أفضل حل ممكن بدون تكلفة إضافية: تغطية جيدة
لكبرى الأندية والبطولات الأوروبية والعالمية المتداولة أكثر في المباريات
المباشرة، مع رجوع صادق للاسم الأصلي (الإنجليزي) لأي اسم غير موجود في
القاموس — بدل عرض ترجمة مكسورة أو مخترعة.

لإضافة أو تصحيح اسم: أضف سطراً هنا بنفس الصيغة (الاسم الإنجليزي بالحروف
الصغيرة كمفتاح). لو أردت تغطية أوسع لاحقاً (كل الأندية/البطولات دون
استثناء)، الحل الوحيد الصحيح هو ربط خدمة ترجمة آلية حقيقية.
"""

COMPETITION_NAME_AR = {
    'premier league': 'الدوري الإنجليزي الممتاز',
    'la liga': 'الدوري الإسباني',
    'laliga': 'الدوري الإسباني',
    'serie a': 'الدوري الإيطالي',
    'bundesliga': 'الدوري الألماني',
    'ligue 1': 'الدوري الفرنسي',
    'uefa champions league': 'دوري أبطال أوروبا',
    'champions league': 'دوري أبطال أوروبا',
    'uefa europa league': 'الدوري الأوروبي',
    'europa league': 'الدوري الأوروبي',
    'uefa europa conference league': 'دوري المؤتمر الأوروبي',
    'fifa world cup': 'كأس العالم',
    'world cup': 'كأس العالم',
    'uefa euro': 'بطولة أمم أوروبا',
    'euro championship': 'بطولة أمم أوروبا',
    'copa america': 'كوبا أمريكا',
    'africa cup of nations': 'كأس الأمم الأفريقية',
    'afcon': 'كأس الأمم الأفريقية',
    'fa cup': 'كأس الاتحاد الإنجليزي',
    'efl cup': 'كأس رابطة المحترفين الإنجليزية',
    'carabao cup': 'كأس رابطة المحترفين الإنجليزية',
    'copa del rey': 'كأس ملك إسبانيا',
    'coppa italia': 'كأس إيطاليا',
    'dfb pokal': 'كأس ألمانيا',
    'coupe de france': 'كأس فرنسا',
    'saudi pro league': 'دوري روشن السعودي',
    'egyptian premier league': 'الدوري المصري الممتاز',
    'uefa nations league': 'دوري الأمم الأوروبية',
    'club world cup': 'كأس العالم للأندية',
    'fifa club world cup': 'كأس العالم للأندية',
}

TEAM_NAME_AR = {
    # إنجلترا
    'manchester united': 'مانشستر يونايتد', 'manchester city': 'مانشستر سيتي',
    'liverpool': 'ليفربول', 'chelsea': 'تشيلسي', 'arsenal': 'أرسنال',
    'tottenham hotspur': 'توتنهام هوتسبير', 'tottenham': 'توتنهام',
    'newcastle united': 'نيوكاسل يونايتد', 'aston villa': 'أستون فيلا',
    'west ham united': 'وست هام يونايتد', 'everton': 'إيفرتون',
    'leicester city': 'ليستر سيتي', 'wolverhampton wanderers': 'وولفرهامبتون',
    'crystal palace': 'كريستال بالاس', 'brighton': 'برايتون',
    'brighton and hove albion': 'برايتون',
    'fulham': 'فولهام', 'brentford': 'برينتفورد', 'nottingham forest': 'نوتنغهام فورست',
    'bournemouth': 'بورنموث', 'southampton': 'ساوثهامبتون',
    # إسبانيا
    'real madrid': 'ريال مدريد', 'barcelona': 'برشلونة', 'fc barcelona': 'برشلونة',
    'atletico madrid': 'أتلتيكو مدريد', 'sevilla': 'إشبيلية', 'real betis': 'ريال بيتيس',
    'real sociedad': 'ريال سوسيداد', 'villarreal': 'فياريال', 'athletic bilbao': 'أتلتيك بيلباو',
    'valencia': 'فالنسيا',
    # إيطاليا
    'juventus': 'يوفنتوس', 'inter milan': 'إنتر ميلان', 'internazionale': 'إنتر ميلان',
    'ac milan': 'إيه سي ميلان', 'milan': 'ميلان', 'napoli': 'نابولي', 'roma': 'روما',
    'as roma': 'روما', 'lazio': 'لاتسيو', 'atalanta': 'أتالانتا', 'fiorentina': 'فيورنتينا',
    # ألمانيا
    'bayern munich': 'بايرن ميونخ', 'bayern münchen': 'بايرن ميونخ',
    'borussia dortmund': 'بوروسيا دورتموند', 'rb leipzig': 'لايبزيغ',
    'bayer leverkusen': 'باير ليفركوزن', 'eintracht frankfurt': 'آينتراخت فرانكفورت',
    'schalke 04': 'شالكه', 'wolfsburg': 'فولفسبورغ',
    # فرنسا
    'paris saint-germain': 'باريس سان جيرمان', 'psg': 'باريس سان جيرمان',
    'marseille': 'مارسيليا', 'lyon': 'ليون', 'monaco': 'موناكو', 'as monaco': 'موناكو',
    'lille': 'ليل', 'nice': 'نيس',
    # أخرى شائعة
    'al hilal': 'الهلال', 'al nassr': 'النصر', 'al ahli': 'الأهلي', 'al ittihad': 'الاتحاد',
    'al ahly': 'الأهلي المصري', 'zamalek': 'الزمالك',
    'flamengo': 'فلامنغو', 'boca juniors': 'بوكا جونيورز', 'river plate': 'ريفر بليت',
}


def translate_team(name):
    if not name:
        return name
    return TEAM_NAME_AR.get(name.strip().lower(), name)


def translate_competition(name):
    if not name:
        return name
    return COMPETITION_NAME_AR.get(name.strip().lower(), name)
