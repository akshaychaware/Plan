from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = 'plan_app'

urlpatterns = [
    path('', views.dog_list, name='dog_list'),
    path('dogs/new/', views.dog_form, name='dog_create'),
    path('dogs/<int:pk>/', views.dog_detail, name='dog_detail'),
    path('dogs/<int:pk>/edit/', views.dog_form, name='dog_edit'),
    path('dogs/<int:pk>/plan/', views.plan_edit, name='plan_edit'),
    path('dogs/<int:pk>/plan/new/', views.plan_new, name='plan_new'),
    path('dogs/<int:pk>/sessions/', views.session_history, name='session_history'),
    path('dogs/<int:pk>/sessions/record/', views.session_record, name='session_record'),
    path('dogs/<int:pk>/sessions/<int:session_pk>/', views.session_record, name='session_edit'),
    path(
        'dogs/<int:pk>/sessions/quick-log/<int:activity_pk>/', views.session_quick_log, name='session_quick_log'
    ),
    path('offline/', TemplateView.as_view(template_name='plan_app/offline.html'), name='offline'),
    path(
        'sw.js',
        TemplateView.as_view(template_name='plan_app/sw.js', content_type='application/javascript'),
        name='service_worker',
    ),
]
