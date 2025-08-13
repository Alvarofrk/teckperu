"""
URLs para los dashboards de certificados
"""

from django.urls import path
from . import dashboard_views

app_name = 'dashboards'

urlpatterns = [
    # Dashboard principal de certificados
    path('certificados/', dashboard_views.certificates_dashboard, name='certificates_dashboard'),
    
    # Dashboard por curso
    path('por-curso/', dashboard_views.course_dashboard, name='course_dashboard'),
    
    # Dashboard de análisis temporal
    path('temporal/', dashboard_views.temporal_dashboard, name='temporal_dashboard'),
    
    # Dashboard de exportación
    path('exportar/', dashboard_views.export_dashboard, name='export_dashboard'),
]
