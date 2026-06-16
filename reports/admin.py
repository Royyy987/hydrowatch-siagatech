from django.contrib.gis import admin
from .models import FloodReport

class FloodReportAdmin(admin.GISModelAdmin):
    # Memaksa peta Django Admin untuk selalu fokus ke Samarinda secara default
    gis_widget_kwargs = {
        'attrs': {
            'default_lon': 117.153709,
            'default_lat': -0.502106,
            'default_zoom': 13,
        }
    }

admin.site.register(FloodReport, FloodReportAdmin)