"""apps/core/admin.py"""
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as DjangoGroupAdmin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group, User
from unfold.admin import ModelAdmin, TabularInline
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from apps.streaming.models import StreamSource

from .models import Channel, IntegrationHealth, Match, News, SiteSettings

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


class StreamSourceInline(TabularInline):
    """
    روابط البث الخاصة بالقناة (Primary + Fallbacks) — تُدار كلها من نفس
    صفحة القناة بدل قسم إدارة منفصل. حقول الصحة (is_healthy/last_checked_at
    وغيرها) للقراءة فقط لأن Celery Beat هو من يُحدّثها دورياً، وليس الإدخال
    اليدوي.
    """
    model = StreamSource
    extra = 1
    fields = ('url', 'label', 'priority', 'is_active', 'is_healthy', 'consecutive_failures', 'last_checked_at')
    readonly_fields = ('is_healthy', 'consecutive_failures', 'last_checked_at')
    ordering = ('priority',)


@admin.register(Channel)
class ChannelAdmin(ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'order', 'sources_count')
    list_filter = ('category', 'is_active')
    list_editable = ('is_active', 'order')
    search_fields = ('name',)
    inlines = [StreamSourceInline]

    def sources_count(self, obj):
        return obj.sources.filter(is_active=True).count()
    sources_count.short_description = 'روابط بث نشِطة'


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
    """مطابقة عمداً لـ MatchAdmin: نفس نمط list_filter/date_hierarchy
    لحالة (Status) مُدارة بنفس الفلسفة (Scheduled/Published/Archived)."""
    list_display = ('title', 'status', 'publish_at', 'archive_at', 'created_at', 'source_url')
    list_filter = ('status',)
    list_editable = ('status',)
    search_fields = ('title', 'content')
    date_hierarchy = 'created_at'


@admin.register(IntegrationHealth)
class IntegrationHealthAdmin(ModelAdmin):
    """للعرض فقط — sync_data.py هو من يُحدّث هذه الصفوف تلقائياً مع كل
    محاولة مزامنة، لا فائدة من إضافة/حذف يدوي."""
    list_display = ('label', 'is_healthy', 'last_checked_at', 'last_success_at')
    list_filter = ('is_healthy',)
    readonly_fields = ('key', 'label', 'is_healthy', 'last_checked_at', 'last_success_at', 'last_error')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


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
