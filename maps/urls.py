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
    
    # RUTE KHUSUS OPERATOR
    path('operator/users/', views.manajemen_user, name='manajemen_user'),
    path('operator/users/toggle-ban/<int:user_id>/', views.toggle_ban_user, name='toggle_ban_user'),
    path('operator/users/toggle-role/<int:user_id>/', views.toggle_role_user, name='toggle_role_user'),
    path('operator/laporan/', views.laporan_masuk, name='laporan_masuk'),
    path('operator/laporan/setujui/<int:report_id>/', views.setujui_laporan, name='setujui_laporan'),
    path('operator/laporan/tolak/<int:report_id>/', views.tolak_laporan, name='tolak_laporan'),
    path('operator/feedback/', views.daftar_feedback, name='daftar_feedback'),
    path('feedback/kirim/', views.kirim_feedback, name='kirim_feedback'),
]