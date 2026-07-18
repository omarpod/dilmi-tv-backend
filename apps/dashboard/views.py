"""apps/dashboard/views.py"""
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache

from apps.core.bulk_import import BulkImportError, run_bulk_import, run_stream_link_merge
from apps.core.forms import (
    AdsSettingsForm, ChannelForm, MatchEditForm, NewsForm, QuickMatchForm,
    StaffUserCreateForm, StaffUserEditForm,
)
from apps.core.integrations.push_notifications import send_topic_notification
from apps.core.models import Channel, Match, News, SiteSettings

from .services import get_dashboard_context

staff_required = user_passes_test(lambda u: u.is_active and u.is_staff, login_url='dashboard:login')


def _paginate(request, queryset, per_page=25):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get('page'))


class DashboardLoginView(LoginView):
    template_name = 'dashboard/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return '/dashboard/'


@never_cache
@staff_required
def index(request):
    # never_cache يُرسل Cache-Control: no-store صراحة — بدون هذا، أي طبقة
    # وسيطة بين المستخدم والخادم (Cloudflare إن كنت تستخدمه أمام النطاق
    # الجديد، أو حتى ذاكرة تخزين المتصفح نفسه) قد تُبقي نسخة قديمة من
    # هذه الصفحة الديناميكية دون أن يكون لهذا أي علاقة بذاكرة تخزين Django
    # المؤقت (غير مُفعَّلة على هذه الصفحة أصلاً — راجع رد المحادثة)
    return render(request, 'dashboard/index.html', get_dashboard_context())


@staff_required
def quick_add_match(request):
    """
    إضافة يدوية سريعة لمباراة — بلا أي اتصال خارجي (لا RapidAPI، لا
    Scraping). مصمَّمة لتكرار الإدخال بسرعة: بعد كل حفظ ناجح، إعادة توجيه
    فورية لنفس الصفحة (نموذج فارغ جديد + رسالة نجاح + التركيز التلقائي
    على أول حقل)، بدل البقاء على صفحة النتيجة والحاجة للرجوع يدوياً.
    """
    if request.method == 'POST':
        form = QuickMatchForm(request.POST)
        if form.is_valid():
            match = form.save()
            if match.status == Match.Status.LIVE:
                send_topic_notification(
                    topic='match_live', title='مباشر الآن',
                    body=f'{match.home_team} vs {match.away_team}',
                    data={'match_id': str(match.pk)},
                )
            messages.success(request, f'أُضيفت: {match.home_team} vs {match.away_team}')
            return redirect('dashboard:quick-add-match')
    else:
        form = QuickMatchForm(initial={'status': Match.Status.UPCOMING})

    recent_matches = Match.objects.filter(external_id__isnull=True).order_by('-created_at')[:8]

    return render(request, 'dashboard/quick_add_match.html', {
        'form': form,
        'recent_matches': recent_matches,
    })


@staff_required
def bulk_import_matches(request):
    """
    استيراد جماعي من ملف CSV/JSON يرفعه المستخدم يدوياً — بلا أي اتصال
    خارجي، راجع apps/core/bulk_import.py لمنطق التحليل والاستيراد نفسه.
    """
    import_result = None
    merge_result = None

    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        stream_links_file = request.FILES.get('stream_links_file')

        if not uploaded_file and not stream_links_file:
            messages.error(request, 'يرجى اختيار ملف مباريات على الأقل قبل الرفع.')

        if uploaded_file:
            try:
                import_result = run_bulk_import(uploaded_file.read(), uploaded_file.name)
            except BulkImportError as e:
                messages.error(request, str(e))
            else:
                if import_result.total_ok:
                    messages.success(
                        request,
                        f'تم الاستيراد: {import_result.created} مباراة جديدة، '
                        f'{import_result.updated} مباراة محدَّثة.',
                    )
                if import_result.row_errors:
                    messages.warning(
                        request,
                        f'{len(import_result.row_errors)} صف من ملف المباريات تعذّرت معالجته — التفاصيل أدناه.',
                    )

        # الدمج الذكي: يعمل بعد ملف المباريات (إن رُفع في نفس الطلب) حتى
        # يجد المباريات المُستوردة للتو أثناء البحث عن تطابق الأسماء
        if stream_links_file:
            try:
                merge_result = run_stream_link_merge(stream_links_file.read(), stream_links_file.name)
            except BulkImportError as e:
                messages.error(request, str(e))
            else:
                if merge_result.matched:
                    messages.success(
                        request,
                        f'تم دمج رابط البث مع {merge_result.matched} مباراة بنجاح.',
                    )
                if merge_result.row_errors:
                    messages.warning(
                        request,
                        f'{len(merge_result.row_errors)} صف من ملف روابط البث تعذّر دمجه — التفاصيل أدناه.',
                    )

    recent_matches = Match.objects.filter(external_id__isnull=True).order_by('-created_at')[:15]

    return render(request, 'dashboard/bulk_import_matches.html', {
        'import_result': import_result,
        'merge_result': merge_result,
        'recent_matches': recent_matches,
    })


@staff_required
def broadcast_toggle(request, pk):
    if request.method != 'POST':
        return redirect('dashboard:index')

    match = get_object_or_404(Match, pk=pk)
    if match.status == Match.Status.LIVE:
        match.status = Match.Status.FINISHED
    else:
        match.status = Match.Status.LIVE
        match.elapsed_minutes = 0
        match.save(update_fields=['status', 'elapsed_minutes', 'updated_at'])
        # هذا التبديل اليدوي ("بدء البث") لا يمر عبر advance_match_lifecycle
        # (المهمة الدورية التي تُرسِل الإشعار تلقائياً) — بدون هذا السطر
        # لا يصل أي إشعار عند بدء مباراة يدوياً من الداشبورد
        send_topic_notification(
            topic='match_live', title='مباشر الآن',
            body=f'{match.home_team} vs {match.away_team}',
            data={'match_id': str(match.pk)},
        )
        return redirect('dashboard:index')

    match.save(update_fields=['status', 'elapsed_minutes', 'updated_at'])
    return redirect('dashboard:index')


# =============================================================================
# المباريات — قائمة كاملة / تعديل / حذف (بديل دائم لـ /admin/core/match/)
# =============================================================================

@staff_required
def matches_list(request):
    today_local = timezone.localtime(timezone.now()).date()

    status_filter = request.GET.get('status')
    queryset = Match.objects.select_related('channel').order_by('-match_datetime')
    if status_filter in dict(Match.Status.choices):
        queryset = queryset.filter(status=status_filter)

    todays_matches = Match.objects.select_related('channel').filter(
        match_datetime__date=today_local,
    ).order_by('match_datetime')

    return render(request, 'dashboard/matches_list.html', {
        'page_obj': _paginate(request, queryset),
        'todays_matches': todays_matches,
        'status_filter': status_filter or '',
        'status_choices': Match.Status.choices,
        'extra_qs': f'&status={status_filter}' if status_filter else '',
    })


@staff_required
def match_edit(request, pk):
    match = get_object_or_404(Match, pk=pk)
    if request.method == 'POST':
        was_live = match.status == Match.Status.LIVE
        form = MatchEditForm(request.POST, instance=match)
        if form.is_valid():
            form.save()
            if not was_live and match.status == Match.Status.LIVE:
                # نفس منطق broadcast_toggle: تعديل الحالة يدوياً هنا إلى
                # "مباشر" لا يمر عبر المهمة الدورية advance_match_lifecycle،
                # فلا إشعار بدونه
                send_topic_notification(
                    topic='match_live', title='مباشر الآن',
                    body=f'{match.home_team} vs {match.away_team}',
                    data={'match_id': str(match.pk)},
                )
            messages.success(request, f'تم تحديث: {match.home_team} vs {match.away_team}')
            return redirect('dashboard:matches-list')
    else:
        form = MatchEditForm(instance=match)

    return render(request, 'dashboard/match_edit.html', {'form': form, 'match': match})


@staff_required
def match_delete(request, pk):
    if request.method != 'POST':
        return redirect('dashboard:matches-list')
    match = get_object_or_404(Match, pk=pk)
    label = f'{match.home_team} vs {match.away_team}'
    match.delete()
    messages.success(request, f'تم حذف: {label}')
    return redirect('dashboard:matches-list')


@staff_required
def matches_bulk_delete(request):
    if request.method != 'POST':
        return redirect('dashboard:matches-list')

    ids = request.POST.getlist('selected_ids')
    if not ids:
        messages.warning(request, 'لم تُحدَّد أي مباراة للحذف.')
    else:
        queryset = Match.objects.filter(pk__in=ids)
        deleted_count = queryset.count()
        queryset.delete()
        messages.success(request, f'تم حذف {deleted_count} مباراة.')

    status_filter = request.POST.get('status_filter', '')
    redirect_url = reverse('dashboard:matches-list')
    if status_filter:
        redirect_url += f'?status={status_filter}'
    return redirect(redirect_url)


# =============================================================================
# القنوات — قائمة / إضافة / تعديل / حذف (بديل دائم لـ /admin/core/channel/)
# روابط البث (StreamSource) تبقى تُدار من /admin/ فقط عمداً — خارج نطاق
# هذا الطلب، وإدارتها (أولوية/فحص صحة تلقائي) مرتبطة بمنطق الإدارة هناك
# =============================================================================

@staff_required
def channels_list(request):
    channels = Channel.objects.all().order_by('order', 'name')
    return render(request, 'dashboard/channels_list.html', {'page_obj': _paginate(request, channels)})


@staff_required
def channel_form(request, pk=None):
    channel = get_object_or_404(Channel, pk=pk) if pk else None
    if request.method == 'POST':
        form = ChannelForm(request.POST, request.FILES, instance=channel)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم حفظ القناة.')
            return redirect('dashboard:channels-list')
    else:
        form = ChannelForm(instance=channel)

    return render(request, 'dashboard/channel_form.html', {'form': form, 'channel': channel})


@staff_required
def channel_delete(request, pk):
    if request.method != 'POST':
        return redirect('dashboard:channels-list')
    channel = get_object_or_404(Channel, pk=pk)
    name = channel.name
    channel.delete()
    messages.success(request, f'تم حذف القناة: {name}')
    return redirect('dashboard:channels-list')


@staff_required
def channels_bulk_delete(request):
    if request.method != 'POST':
        return redirect('dashboard:channels-list')

    ids = request.POST.getlist('selected_ids')
    if not ids:
        messages.warning(request, 'لم تُحدَّد أي قناة للحذف.')
    else:
        queryset = Channel.objects.filter(pk__in=ids)
        deleted_count = queryset.count()
        queryset.delete()
        messages.success(request, f'تم حذف {deleted_count} قناة (وكل روابط بثها).')

    return redirect('dashboard:channels-list')


# =============================================================================
# الأخبار — قائمة / إضافة / تعديل / حذف (بديل دائم لـ /admin/core/news/)
# =============================================================================

@staff_required
def news_list(request):
    news_items = News.objects.all().order_by('-created_at')
    return render(request, 'dashboard/news_list.html', {'page_obj': _paginate(request, news_items)})


@staff_required
def news_form(request, pk=None):
    news_item = get_object_or_404(News, pk=pk) if pk else None
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES, instance=news_item)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم حفظ الخبر.')
            return redirect('dashboard:news-list')
    else:
        form = NewsForm(instance=news_item)

    return render(request, 'dashboard/news_form.html', {'form': form, 'news_item': news_item})


@staff_required
def news_delete(request, pk):
    if request.method != 'POST':
        return redirect('dashboard:news-list')
    news_item = get_object_or_404(News, pk=pk)
    title = news_item.title
    news_item.delete()
    messages.success(request, f'تم حذف الخبر: {title}')
    return redirect('dashboard:news-list')


# =============================================================================
# المستخدمون — قائمة / إضافة / تعديل / حذف (بديل دائم لـ /admin/auth/user/)
# مع حواجز أمان: لا حذف للحساب الحالي، ولا حذف آخر موظف نشِط في النظام
# (لتفادي قفل الوصول للوحة التحكم بالكامل بالخطأ)
# =============================================================================

@staff_required
def users_list(request):
    users = User.objects.all().order_by('username')
    return render(request, 'dashboard/users_list.html', {'page_obj': _paginate(request, users)})


@staff_required
def user_form(request, pk=None):
    target = get_object_or_404(User, pk=pk) if pk else None
    form_class = StaffUserEditForm if target else StaffUserCreateForm

    if request.method == 'POST':
        form = form_class(request.POST, instance=target)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم حفظ المستخدم.')
            return redirect('dashboard:users-list')
    else:
        form = form_class(instance=target)

    return render(request, 'dashboard/user_form.html', {'form': form, 'target': target})


@staff_required
def user_delete(request, pk):
    if request.method != 'POST':
        return redirect('dashboard:users-list')

    target = get_object_or_404(User, pk=pk)

    if target.pk == request.user.pk:
        messages.error(request, 'لا يمكنك حذف حسابك الخاص من هنا.')
        return redirect('dashboard:users-list')

    other_active_staff_exists = User.objects.filter(
        is_staff=True, is_active=True,
    ).exclude(pk=target.pk).exists()
    if target.is_staff and target.is_active and not other_active_staff_exists:
        messages.error(request, 'لا يمكن حذف آخر مستخدم موظف نشِط — سيُفقَد الوصول للوحة التحكم بالكامل.')
        return redirect('dashboard:users-list')

    username = target.username
    target.delete()
    messages.success(request, f'تم حذف المستخدم: {username}')
    return redirect('dashboard:users-list')


@staff_required
def ads_settings(request):
    """
    إعدادات شبكات الإعلانات — صف وحيد (SiteSettings.get_solo). الحفظ هنا
    يُحدِّث قاعدة البيانات مباشرة، ويقرأها تطبيق Flutter فوراً عند طلبه
    التالي لـ /api/app-config/ (لا حاجة لإعادة تشغيل أي خدمة).
    """
    settings_obj = SiteSettings.get_solo()

    if request.method == 'POST':
        form = AdsSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم حفظ إعدادات الإعلانات — التطبيق سيقرأ القيم الجديدة فوراً.')
            return redirect('dashboard:ads-settings')
    else:
        form = AdsSettingsForm(instance=settings_obj)

    return render(request, 'dashboard/ads_settings.html', {'form': form})
