from django.urls import path, include
from .import views

app_name = 'microblog'

urlpatterns = [
    path('', views.home, name='home'),
    path('index/', views.index, name='microblog_index'),
    path('save_index/', views.save_index, name='microblog_save_index'),
    path('subject/<str:subject_name>/', views.subject_blog, name='microblog_subject'),
    path('save_subject/', views.save_subject, name='microblog_save_subject'),
    path('detail/<int:detail_id>/', views.detail_blog, name='microblog_detail'),
    path('analyze_views/<int:blog_id>/', views.analyze_views, name='microblog_analyze'),
    path('microblog_search/', views.microblog_search, name='microblog_search'),
]
