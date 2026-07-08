from django.contrib import admin
from .models import Channel, Team, Player, Match, LineupEntry, News, AdSettings

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
    list_display = ('name', 'team', 'shirt_number', 'position')
    list_filter = ('team', 'position')
    search_fields = ('name',)

class LineupInline(admin.TabularInline):
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
    list_display = ('banner_enabled', 'interstitial_enabled', 'updated_at')
    def has_add_permission(self, request):
        return not AdSettings.objects.exists()
