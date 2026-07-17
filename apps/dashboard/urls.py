"""apps/dashboard/urls.py"""
from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.DashboardLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='dashboard:login'), name='logout'),

    # المباريات
    path('matches/', views.matches_list, name='matches-list'),
    path('matches/quick-add/', views.quick_add_match, name='quick-add-match'),
    path('matches/bulk-import/', views.bulk_import_matches, name='bulk-import-matches'),
    path('matches/<uuid:pk>/broadcast/', views.broadcast_toggle, name='broadcast-toggle'),
    path('matches/<uuid:pk>/edit/', views.match_edit, name='match-edit'),
    path('matches/<uuid:pk>/delete/', views.match_delete, name='match-delete'),

    # القنوات
    path('channels/', views.channels_list, name='channels-list'),
    path('channels/add/', views.channel_form, name='channel-add'),
    path('channels/<uuid:pk>/edit/', views.channel_form, name='channel-edit'),
    path('channels/<uuid:pk>/delete/', views.channel_delete, name='channel-delete'),

    # الأخبار
    path('news/', views.news_list, name='news-list'),
    path('news/add/', views.news_form, name='news-add'),
    path('news/<uuid:pk>/edit/', views.news_form, name='news-edit'),
    path('news/<uuid:pk>/delete/', views.news_delete, name='news-delete'),

    # المستخدمون
    path('users/', views.users_list, name='users-list'),
    path('users/add/', views.user_form, name='user-add'),
    path('users/<int:pk>/edit/', views.user_form, name='user-edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user-delete'),

    # الإعلانات
    path('ads/', views.ads_settings, name='ads-settings'),
]
