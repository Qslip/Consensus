from django.urls import path, include
from zhihu import views 

app_name = 'zhihu'

urlpatterns = [
    path('', views.data, name='index'),
    path('<int:page>', views.data, name='info'),
    path('save_data/<int:url_id>', views.save_data, name='save_data'),
    path('search/', views.search, name = 'search'),
    path('search/<int:question_id>', views.search_analyze, name='s_result'),
]


