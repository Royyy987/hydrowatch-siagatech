import os
import json
import requests
from django.shortcuts import render
from django.http import JsonResponse
# from django.utils import timezone
# from datetime import timedelta
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
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
@user_passes_test(is_operator, login_url='dashboard') # Jika warga biasa nekat ngetik URL ini, lempar balik ke map!
def manajemen_user(request):
    # Ambil semua user dari database, urutkan dari yang terbaru
    users = User.objects.all().order_by('-date_joined')
    
    context = {
        'user_list': users,
        'page_title': 'Manajemen User'
    }
    return render(request, 'maps/manajemen_user.html', context)

# --- 2. VIEW LAPORAN MASUK ---
@login_required
@user_passes_test(is_operator, login_url='dashboard')
def laporan_masuk(request):
    # Logika query database laporan genangan akan kita taruh di sini nanti
    
    context = {
        'page_title': 'Laporan Masuk'
    }
    return render(request, 'maps/laporan_masuk.html', context)