"""
admin.py
--------
هذا الملف يتحكم في شكل لوحة تحكم Django الجاهزة (/admin).
تسجيل كل model هنا يجعله يظهر في اللوحة تلقائياً مع نموذج إدخال/تعديل جاهز.
"""
import logging

from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import (
    League, Channel, Team, Player, Match, MatchEvent, LineupEntry, News, AdSettings,
    Analytics, SiteSettings, NotificationSubscriber, StaticPage,
)

logger = logging.getLogger(__name__)


class SafeAdminMixin:
    """
    ⚠️ طبقة الحماية "العنيفة" الحقيقية: تُغلّف صفحتَي القائمة (changelist)
    والإضافة/التعديل (changeform) بـ try/except شامل على مستوى Django
    نفسه — وليس فقط على مستوى دالة عرض حقل واحد كما في safe_name/
    safe_match_title (تلك تحمي عرض حقل *بعد* نجاح الاستعلام فقط).

    هذا يعني: حتى لو فشل الاستعلام الأساسي نفسه (مثال حقيقي: عمود
    "league_id" غير موجود فعلياً في قاعدة البيانات بسبب ترحيل ناقص —
    وهو خطأ يحدث *قبل* وصول الكود لأي دالة عرض إطلاقاً)، لا تظهر صفحة
    "Server Error (500)" الافتراضية القبيحة أبداً — بدلاً منها: رسالة
    عربية واضحة + إعادة توجيه فوري للوحة الرئيسية، مع تسجيل كامل تفاصيل
    الخطأ الحقيقي في السجلات (Logs) لتشخيصه لاحقاً عبر check_db_health.
    """

    def changelist_view(self, request, extra_context=None):
        try:
            return super().changelist_view(request, extra_context)
        except Exception as e:
            logger.error(
                'فشل عرض قائمة %s: %s', self.model.__name__, e, exc_info=True,
            )
            messages.error(
                request,
                f'تعذّر عرض قائمة "{self.model._meta.verbose_name_plural}" بسبب '
                f'خطأ تقني ({type(e).__name__}). شغّل "python manage.py check_db_health" '
                'لتشخيص السبب الدقيق (غالباً عمود/جدول مفقود في قاعدة البيانات).',
            )
            return HttpResponseRedirect(reverse('admin:index'))

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        try:
            return super().changeform_view(request, object_id, form_url, extra_context)
        except Exception as e:
            logger.error(
                'فشل عرض نموذج %s (id=%s): %s', self.model.__name__, object_id, e, exc_info=True,
            )
            messages.error(
                request,
                f'تعذّر عرض/تعديل هذا السجل بسبب خطأ تقني ({type(e).__name__}). '
                'شغّل "python manage.py check_db_health" لتشخيص السبب.',
            )
            return HttpResponseRedirect(reverse('admin:index'))



@admin.register(League)
class LeagueAdmin(SafeAdminMixin, admin.ModelAdmin):
    list_display = ('safe_name', 'country', 'external_id')
    search_fields = ('name',)

    def safe_name(self, obj):
        return obj.name or 'غير محدَّد'
    safe_name.short_description = 'الاسم'


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
class TeamAdmin(SafeAdminMixin, admin.ModelAdmin):
    list_display = ('safe_name', 'country')
    search_fields = ('name',)
    inlines = [PlayerInline]

    def safe_name(self, obj):
        return obj.name or 'غير محدَّد'
    safe_name.short_description = 'الاسم'


@admin.register(Player)
class PlayerAdmin(SafeAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'team', 'shirt_number', 'position', 'has_photo')
    list_filter = ('team', 'position')
    search_fields = ('name',)

    def has_photo(self, obj):
        return bool(obj.photo)
    has_photo.short_description = 'له صورة؟'
    has_photo.boolean = True


class LineupInline(admin.TabularInline):
    """يسمح بإدخال تشكيلة المباراة مباشرة من صفحة المباراة."""
    model = LineupEntry
    extra = 1


class MatchEventInline(admin.TabularInline):
    """يسمح بإدخال أحداث المباراة (أهداف، بطاقات) مباشرة من صفحة المباراة."""
    model = MatchEvent
    extra = 1


@admin.register(Match)
class MatchAdmin(SafeAdminMixin, admin.ModelAdmin):
    list_display = (
        'safe_match_title', 'safe_competition', 'status',
        'home_score', 'away_score', 'elapsed_minutes', 'channel',
    )
    list_filter = ('status', 'league')
    search_fields = ('home_team__name', 'away_team__name')
    inlines = [LineupInline, MatchEventInline]

    def safe_match_title(self, obj):
        # لا نعتمد على __str__ مباشرة في list_display (رغم أنها محصَّنة
        # الآن في models.py) — طبقة حماية إضافية صريحة هنا في الأدمن
        # نفسه، حتى لا تعتمد صفحة القائمة على افتراض واحد فقط.
        try:
            return str(obj)
        except Exception:
            return f'مباراة #{obj.pk}'
    safe_match_title.short_description = 'المباراة'

    def safe_competition(self, obj):
        try:
            return obj.competition_display
        except Exception:
            return 'غير محدَّد'
    safe_competition.short_description = 'البطولة'


@admin.register(News)
class NewsAdmin(SafeAdminMixin, admin.ModelAdmin):
    list_display = ('title', 'published_at', 'is_published', 'source_url', 'related_match')
    list_filter = ('is_published',)
    search_fields = ('title', 'content')


@admin.register(AdSettings)
class AdSettingsAdmin(admin.ModelAdmin):
    # لا حاجة لقائمة كاملة، هذا السجل يكون واحداً فقط دائماً
    list_display = ('banner_enabled', 'interstitial_enabled', 'updated_at')

    def has_add_permission(self, request):
        # يمنع إنشاء أكثر من سجل واحد لإعدادات الإعلانات
        return not AdSettings.objects.exists()


@admin.register(Analytics)
class AnalyticsAdmin(admin.ModelAdmin):
    # هذا الجدول للقراءة فقط عملياً (يُملأ تلقائياً من التطبيق، وليس يدوياً)
    list_display = ('device', 'screen', 'ip_address', 'timestamp')
    list_filter = ('screen',)
    search_fields = ('device', 'ip_address')
    readonly_fields = ('ip_address', 'device', 'screen', 'timestamp')

    def has_add_permission(self, request):
        # لا معنى لإضافة زيارة يدوياً من لوحة التحكم
        return False


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('contact_email', 'facebook_url', 'instagram_url', 'telegram_url', 'updated_at')

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()


@admin.register(NotificationSubscriber)
class NotificationSubscriberAdmin(admin.ModelAdmin):
    list_display = ('device_platform', 'fcm_token_short', 'is_active', 'subscribed_at')
    list_editable = ('is_active',)
    list_filter = ('device_platform', 'is_active')
    search_fields = ('fcm_token',)

    def fcm_token_short(self, obj):
        # نعرض جزءاً قصيراً فقط من الرمز الطويل حتى لا تتشوّه القائمة
        return f'{obj.fcm_token[:24]}...'
    fcm_token_short.short_description = 'رمز الجهاز'


@admin.register(StaticPage)
class StaticPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'updated_at')
