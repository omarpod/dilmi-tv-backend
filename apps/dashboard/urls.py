"""apps/dashboard/urls.py"""
from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.DashboardLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='dashboard:login'), name='logout'),
    path('matches/quick-add/', views.quick_add_match, name='quick-add-match'),
    path('matches/bulk-import/', views.bulk_import_matches, name='bulk-import-matches'),
    path('matches/<uuid:pk>/broadcast/', views.broadcast_toggle, name='broadcast-toggle'),
]
