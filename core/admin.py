"""
admin.py
--------
لوحة تحكم معدلة بأسلوب دفاعي لمنع انهيار الموقع عند وجود بيانات غير مكتملة.
"""
from django.contrib import admin
from .models import (
    League, Channel, Team, Player, Match, MatchEvent, LineupEntry, News, AdSettings,
    Analytics, SiteSettings, NotificationSubscriber, StaticPage,
)

@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'external_id')
    search_fields = ('name',)

@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    search_fields = ('name',)
    list_filter = ('category', 'is_active')

class PlayerInline(admin.TabularInline):
    model = Player
    extra = 1

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')
    search_fields = ('name',)
    inlines = [PlayerInline]

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'team', 'shirt_number', 'position', 'has_photo')
    list_filter = ('team', 'position')
    search_fields = ('name',)

    def has_photo(self, obj):
        return bool(obj.photo)
    has_photo.short_description = 'له صورة؟'
    has_photo.boolean = True

class LineupInline(admin.TabularInline):
    model = LineupEntry
    extra = 1

class MatchEventInline(admin.TabularInline):
    model = MatchEvent
    extra = 1

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    # استخدام الدوال الدفاعية الجديدة لمنع الخطأ 500
    list_display = ('match_name', 'competition_display', 'status', 'home_score', 'away_score', 'elapsed_minutes', 'channel')
    list_filter = ('status', 'league')
    search_fields = ('home_team__name', 'away_team__name')
    inlines = [LineupInline, MatchEventInline]

    def match_name(self, obj):
        home = obj.home_team.name if obj.home_team else "فريق غير معروف"
        away = obj.away_team.name if obj.away_team else "فريق غير معروف"
        return f"{home} vs {away}"
    match_name.short_description = 'المباراة'

    def competition_display(self, obj):
        return obj.league.name if obj.league else "دوري غير معروف"
    competition_display.short_description = 'الدوري'

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_at', 'is_published', 'related_match')
    list_filter = ('is_published',)
    search_fields = ('title', 'content')

@admin.register(AdSettings)
class AdSettingsAdmin(admin.ModelAdmin):
    list_display = ('banner_enabled', 'interstitial_enabled', 'updated_at')
    def has_add_permission(self, request):
        return not AdSettings.objects.exists()

@admin.register(Analytics)
class AnalyticsAdmin(admin.ModelAdmin):
    list_display = ('device', 'screen', 'ip_address', 'timestamp')
    list_filter = ('screen',)
    search_fields = ('device', 'ip_address')
    readonly_fields = ('ip_address', 'device', 'screen', 'timestamp')
    def has_add_permission(self, request):
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
        return f'{obj.fcm_token[:24]}...' if obj.fcm_token else 'N/A'
    fcm_token_short.short_description = 'رمز الجهاز'

@admin.register(StaticPage)
class StaticPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'updated_at')