"""apps/dashboard/views.py"""
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache

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
