"""apps/core/admin.py"""
from django.contrib import admin

from .models import Channel, Match, News


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'order')
    list_filter = ('category', 'is_active')
    list_editable = ('is_active', 'order')
    search_fields = ('name',)


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        '__str__', 'competition', 'status', 'home_score', 'away_score',
        'elapsed_minutes', 'channel',
    )
    list_filter = ('status',)
    search_fields = ('home_team', 'away_team', 'competition')
    date_hierarchy = 'match_datetime'


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'created_at', 'source_url')
    list_filter = ('is_published',)
    search_fields = ('title', 'content')
