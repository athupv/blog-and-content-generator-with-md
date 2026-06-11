from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # AI Generators
    path('generate/blog/', views.generate_blog, name='generate_blog'),
    path('generate/product/', views.generate_product, name='generate_product'),
    path('generate/caption/', views.generate_caption, name='generate_caption'),
    
    # Settings
    path('settings/save/', views.save_api_keys, name='save_api_keys'),
    
    # History
    path('history/', views.history_list, name='history_list'),
    path('history/<int:item_id>/', views.history_detail, name='history_detail'),
]
