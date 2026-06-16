from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta, datetime
from .models import FloodReport
from ai_vision.services import estimate_flood_depth

@login_required(login_url='/login/')
def submit_report(request):
    # CEK APAKAH AKUN SEDANG DI-SUSPEND
    suspended_until_str = request.session.get('suspended_until')
    if suspended_until_str:
        suspended_until = datetime.fromisoformat(suspended_until_str)
        if timezone.now() < suspended_until:
            messages.error(request, "AKUN DIBEKUKAN! Anda terdeteksi mengirim SPAM. Silakan coba lagi nanti.")
            return redirect('dashboard')
        else:
            # Waktu suspend habis, hapus hukuman
            del request.session['suspended_until']
            request.session['spam_count'] = 0

    if request.method == 'POST':
        image_file = request.FILES.get('image')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        
        if image_file and latitude and longitude:
            location = Point(float(longitude), float(latitude), srid=4326)

            # Simpan sementara
            report = FloodReport.objects.create(
                reporter=request.user,
                image=image_file,
                location=location
            )

            # Tembak AI
            estimated_depth = estimate_flood_depth(report.image.path)

            if estimated_depth is not None:
                if estimated_depth > 0:
                    report.estimated_depth_cm = estimated_depth
                    report.save()
                    messages.success(request, f"Validasi AI Berhasil: Kedalaman {estimated_depth} cm.")
                else:
                    # HAPUS LAPORAN KARENA SPAM/KERING
                    report.delete()
                    
                    if estimated_depth == -1:
                        # LOGIKA 3 STRIKES SUSPEND
                        spam_count = request.session.get('spam_count', 0) + 1
                        request.session['spam_count'] = spam_count
                        
                        if spam_count >= 3:
                            # Suspend selama 1 jam
                            suspend_time = timezone.now() + timedelta(hours=1)
                            request.session['suspended_until'] = suspend_time.isoformat()
                            messages.error(request, "AKUN DIBEKUKAN SEMENTARA! Anda telah 3 kali mengirim gambar SPAM.")
                        else:
                            messages.error(request, f"LAPORAN DITOLAK! AI mendeteksi foto SPAM/Tidak Relevan. (Peringatan {spam_count}/3)")
                    else:
                        messages.warning(request, "Laporan dibatalkan. AI mendeteksi jalanan kering.")
            else:
                report.delete()
                messages.error(request, "Gagal memproses gambar ke AI.")

            return redirect('dashboard')

    return render(request, 'reports/submit.html')