"""apps/dashboard/views.py"""
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache

from apps.core.bulk_import import BulkImportError, run_bulk_import
from apps.core.forms import QuickMatchForm
from apps.core.models import Match

from .services import get_dashboard_context

staff_required = user_passes_test(lambda u: u.is_active and u.is_staff, login_url='dashboard:login')


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

    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            messages.error(request, 'يرجى اختيار ملف قبل الرفع.')
        else:
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
                        f'{len(import_result.row_errors)} صف تعذّرت معالجته — التفاصيل أدناه.',
                    )

    recent_matches = Match.objects.filter(external_id__isnull=True).order_by('-created_at')[:15]

    return render(request, 'dashboard/bulk_import_matches.html', {
        'import_result': import_result,
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

    return redirect('dashboard:index')
