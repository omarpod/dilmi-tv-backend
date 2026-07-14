"""apps/core/admin.py"""
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as DjangoGroupAdmin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group, User
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import Channel, Match, News, SiteSettings

# بدون هذا، صفحات المستخدمين/المجموعات (django.contrib.auth) تبقى بالشكل
# القديم غير المُنسَّق بينما بقية /admin/ أصبحت Unfold — نفس "الفوضى"
# المطلوب التخلص منها، فقط في مكان آخر
admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(DjangoUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(DjangoGroupAdmin, ModelAdmin):
    pass


@admin.register(Channel)
class ChannelAdmin(ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'order')
    list_filter = ('category', 'is_active')
    list_editable = ('is_active', 'order')
    search_fields = ('name',)


@admin.register(Match)
class MatchAdmin(ModelAdmin):
    list_display = (
        '__str__', 'competition', 'status', 'home_score', 'away_score',
        'elapsed_minutes', 'channel',
    )
    list_filter = ('status',)
    search_fields = ('home_team', 'away_team', 'competition')
    date_hierarchy = 'match_datetime'


@admin.register(News)
class NewsAdmin(ModelAdmin):
    list_display = ('title', 'is_published', 'created_at', 'source_url')
    list_filter = ('is_published',)
    search_fields = ('title', 'content')


@admin.register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin):
    """صف وحيد (Singleton) — لا إضافة ولا حذف، تعديل فقط."""

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # يذهب مباشرة لصفحة التعديل (لا فائدة من عرض قائمة لصف واحد فقط)
        settings_obj = SiteSettings.get_solo()
        from django.shortcuts import redirect
        return redirect('admin:core_sitesettings_change', settings_obj.pk)
