from django.contrib.gis.db import models
from django.contrib.auth.models import User

class FloodReport(models.Model):
    # Menghubungkan data laporan dengan akun pengguna yang terdaftar
    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Menentukan direktori penyimpanan file gambar yang diunggah
    image = models.ImageField(upload_to='flood_images/')
    
    # Menyimpan titik koordinat geografis menggunakan standar WGS 84 (SRID 4326)
    location = models.PointField(srid=4326) 
    
    # Menyimpan nilai numerik estimasi kedalaman air dalam sentimeter
    estimated_depth_cm = models.IntegerField(null=True, blank=True)
    
    # Mencatat waktu pembuatan laporan secara otomatis
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Menandai status visibilitas laporan di peta
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Laporan {self.id} oleh {self.reporter.username} - Aktif: {self.is_active}"
    

# Tambahkan model ini
class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pesan = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback dari {self.user.username}"