from django.urls import path
from . import views
from . import authentication

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('akun/', views.pengaturan_akun, name='pengaturan_akun'),
    path('laporan-saya/', views.laporan_saya, name='laporan_saya'),
    path('notifikasi/', views.pengaturan_notifikasi, name='pengaturan_notifikasi'),
    
    # Endpoint rahasia untuk menyuplai data peta
    path('api/flood-data/', views.get_flood_data, name='flood_data'),
    path('api/ai-chat/', views.deepseek_chat, name='ai_chat'),
    
    # Endpoint untuk autentikasi
    path('login/', authentication.login_view, name='login'),
    path('register/', authentication.register_view, name='register'),
    path('logout/', authentication.logout_view, name='logout'),
]