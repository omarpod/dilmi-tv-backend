"""
admin.py
--------
هذا الملف يتحكم في شكل لوحة تحكم Django الجاهزة (/admin).
تسجيل كل model هنا يجعله يظهر في اللوحة تلقائياً مع نموذج إدخال/تعديل جاهز.
"""
from django.contrib import admin
from .models import Channel, Team, Player, Match, LineupEntry, News, AdSettings
from django.contrib.auth.models import User

# كود ذكي لإنشاء المستخدم فور تحميل صفحة الأدمن لأول مرة
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin1234')

@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    # الأعمدة التي تظهر في قائمة القنوات
    list_display = ('name', 'category', 'is_active', 'order')
    list_editable = ('is_active', 'order')  # يمكن تعديلها مباشرة من القائمة دون فتح الصفحة
    search_fields = ('name',)
    list_filter = ('category', 'is_active')


class PlayerInline(admin.TabularInline):
    """يسمح بإضافة/تعديل لاعبي الفريق مباشرة من صفحة الفريق نفسه."""
    model = Player
    extra = 1  # عدد الحقول الفارغة الجاهزة للإضافة السريعة


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')
    search_fields = ('name',)
    inlines = [PlayerInline]


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'team', 'shirt_number', 'position')
    list_filter = ('team', 'position')
    search_fields = ('name',)


class LineupInline(admin.TabularInline):
    """يسمح بإدخال تشكيلة المباراة مباشرة من صفحة المباراة."""
    model = LineupEntry
    extra = 1


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'competition', 'status', 'home_score', 'away_score', 'channel')
    list_filter = ('status', 'competition')
    search_fields = ('home_team__name', 'away_team__name')
    inlines = [LineupInline]


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_at', 'is_published', 'related_match')
    list_filter = ('is_published',)
    search_fields = ('title', 'content')


@admin.register(AdSettings)
class AdSettingsAdmin(admin.ModelAdmin):
    # لا حاجة لقائمة كاملة، هذا السجل يكون واحداً فقط دائماً
    list_display = ('banner_enabled', 'interstitial_enabled', 'updated_at')

    def has_add_permission(self, request):
        # يمنع إنشاء أكثر من سجل واحد لإعدادات الإعلانات
        return not AdSettings.objects.exists()
