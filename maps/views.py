import os
import json
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
# from django.utils import timezone
# from datetime import timedelta
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.gis.geos import Point, LineString
from reports.models import FloodReport
from openai import OpenAI


def dashboard(request):
    return render(request, 'maps/dashboard.html')

@login_required(login_url='/login/')
def pengaturan_akun(request):
    return render(request, 'maps/pengaturan_akun.html')

@login_required(login_url='/login/')
def laporan_saya(request):
    user_reports = FloodReport.objects.filter(reporter=request.user).order_by('-timestamp')
    
    context = {
        'reports': user_reports
    }
    return render(request, 'maps/laporan_saya.html', context)

@login_required(login_url='/login/')
def pengaturan_notifikasi(request):
    return render(request, 'maps/pengaturan_notifikasi.html')

def get_flood_data(request):
    # 1. Tarik SEMUA data laporan yang aktif (Filter 24 jam DIMATIKAN untuk keperluan DEMO)
    reports = FloodReport.objects.filter(
        is_active=True,
        estimated_depth_cm__gt=0
    )

    # 2. Siapkan wadah klaster berdasarkan kategori indikator cuaca
    clusters = {
        "Bahaya": {"base_depth": 60, "geom": None},
        "Awas": {"base_depth": 30, "geom": None},
        "Waspada": {"base_depth": 10, "geom": None},
    }

    # 3. Iterasi dan leburkan (ST_Union) poligon yang saling tumpang tindih
    for report in reports:
        zona_poly = report.location.buffer(0.0003)
        depth = report.estimated_depth_cm

        # Kategorisasi level ancaman
        if depth >= 60:
            cat = "Bahaya"
        elif depth >= 30:
            cat = "Awas"
        else:
            cat = "Waspada"

        # Proses ST_Union menggunakan API GEOS GeoDjango
        if clusters[cat]["geom"] is None:
            clusters[cat]["geom"] = zona_poly
        else:
            clusters[cat]["geom"] = clusters[cat]["geom"].union(zona_poly)

    # 4. Format hasil leburan menjadi FeatureCollection GeoJSON
    features = []
    for cat, data in clusters.items():
        if data["geom"]:
            features.append({
                "type": "Feature",
                "geometry": json.loads(data["geom"].geojson),
                "properties": {
                    "kedalaman": data["base_depth"],
                    "kategori": cat,
                    "keterangan": f"Zona {cat} Genangan"
                }
            })

    return JsonResponse({"type": "FeatureCollection", "features": features})


@csrf_exempt
def deepseek_chat(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_msg = data.get('message')
        user_lat = data.get('lat')
        user_lon = data.get('lon')

        # Tarik data banjir yang sedang aktif untuk dijadikan konteks bagi AI DeepSeek
        floods = FloodReport.objects.filter(is_active=True, estimated_depth_cm__gt=0)
        flood_context = ", ".join([f"Banjir di koordinat lat {f.location.y}, lon {f.location.x} sedalam {f.estimated_depth_cm}cm" for f in floods])
        
        if not flood_context:
            flood_context = "Saat ini tidak ada laporan genangan air aktif di Samarinda. Semua rute aman."

        # Prompt system khusus Samarinda
        system_prompt = f"""Kamu adalah HydroBot, AI cerdas untuk navigasi dan mitigasi bencana di kota Samarinda. 
        Lokasi pengguna saat ini: Latitude {user_lat}, Longitude {user_lon}.
        Kondisi jalanan saat ini: {flood_context}.
        Tugasmu: Pengguna akan memberitahu tujuannya. Berikan saran rute alternatif yang logis, sebutkan nama jalannya, dan hindari titik banjir yang disebutkan di atas. Jawab dengan singkat, padat, dan jelas dalam bahasa Indonesia."""

        try:
            client = OpenAI(api_key=os.getenv('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.3 # Temperature rendah agar tidak halusinasi
            )
            return JsonResponse({'reply': response.choices[0].message.content})
        except Exception as e:
            return JsonResponse({'reply': f"Maaf, koneksi ke AI terputus: {str(e)}"})
        
def is_operator(user):
    return user.groups.filter(name='Operator').exists() or user.is_superuser

# --- 1. VIEW MANAJEMEN USER ---
@login_required
@user_passes_test(is_operator, login_url='dashboard')
def manajemen_user(request):
    # FIX: Sembunyikan Superuser dari daftar
    users = User.objects.exclude(is_superuser=True).order_by('-date_joined')
    
    context = {
        'user_list': users,
        'page_title': 'Manajemen User'
    }
    return render(request, 'maps/manajemen_user.html', context)

# --- 2. FITUR BAN / UNBAN AKUN ---
@login_required
@user_passes_test(is_operator, login_url='dashboard')
@require_POST
def toggle_ban_user(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    
    # Cegah ban diri sendiri
    if target_user == request.user:
        messages.error(request, "Anda tidak bisa membekukan akun sendiri!")
        return redirect('manajemen_user')

    # Toggle status aktif
    target_user.is_active = not target_user.is_active
    target_user.save()
    
    status_text = "diaktifkan kembali" if target_user.is_active else "dibekukan"
    messages.success(request, f"Akun {target_user.username} berhasil {status_text}.")
    return redirect('manajemen_user')

# --- 3. FITUR PROMOTE / DEMOTE ROLE ---
@login_required
@user_passes_test(is_operator, login_url='dashboard')
@require_POST
def toggle_role_user(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    
    # Cegah ubah role diri sendiri
    if target_user == request.user:
        messages.error(request, "Anda tidak bisa mengubah role Anda sendiri!")
        return redirect('manajemen_user')

    # Ambil atau buat grup Operator
    operator_group, created = Group.objects.get_or_create(name='Operator')
    
    if operator_group in target_user.groups.all():
        target_user.groups.remove(operator_group)
        messages.success(request, f"{target_user.username} sekarang menjadi Warga biasa.")
    else:
        target_user.groups.add(operator_group)
        messages.success(request, f"{target_user.username} berhasil diangkat menjadi Operator.")
        
    return redirect('manajemen_user')

# --- 4. VIEW LAPORAN MASUK ---
@login_required
@user_passes_test(is_operator, login_url='dashboard')
def laporan_masuk(request):
    # Gunakan FloodReport dan urutkan berdasarkan timestamp
    laporan_list = FloodReport.objects.all().order_by('-timestamp')
    
    context = {
        'laporan_list': laporan_list,
        'page_title': 'Laporan Masuk'
    }
    return render(request, 'maps/laporan_masuk.html', context)

# --- 5. AKSI OPERATOR: SETUJUI LAPORAN ---
@login_required
@user_passes_test(is_operator, login_url='dashboard')
@require_POST
def setujui_laporan(request, report_id):
    laporan = get_object_or_404(FloodReport, id=report_id)
    laporan.is_active = True  # Ubah is_active jadi True agar muncul di peta
    laporan.save()
    
    messages.success(request, f"Laporan divalidasi! Poligon banjir ditarik ke peta.")
    return redirect('laporan_masuk')

# --- 6. AKSI OPERATOR: TOLAK / HAPUS LAPORAN ---
@login_required
@user_passes_test(is_operator, login_url='dashboard')
@require_POST
def tolak_laporan(request, report_id):
    laporan = get_object_or_404(FloodReport, id=report_id)
    laporan.delete()  # Langsung hapus dari database agar tidak nyampah
    
    messages.warning(request, f"Laporan palsu/spam telah ditolak dan dihapus.")
    return redirect('laporan_masuk')

# --- 7. VIEW UNTUK WARGA: KIRIM FEEDBACK ---
@login_required
@require_POST
def kirim_feedback(request):
    pesan = request.POST.get('pesan')
    if pesan:
        from .models import Feedback # Sesuaikan import jika file models beda folder
        Feedback.objects.create(user=request.user, pesan=pesan)
        messages.success(request, "Terima kasih! Feedback kamu berhasil dikirim ke Operator.")
    return redirect('dashboard')

# --- 8. VIEW UNTUK OPERATOR: BACA FEEDBACK ---
@login_required
@user_passes_test(is_operator, login_url='dashboard')
def daftar_feedback(request):
    from .models import Feedback
    # Ambil semua feedback urut dari yang paling baru
    feedbacks = Feedback.objects.all().order_by('-created_at')
    
    context = {
        'feedbacks': feedbacks,
        'page_title': 'Feedback Pengguna'
    }
    return render(request, 'maps/daftar_feedback.html', context)