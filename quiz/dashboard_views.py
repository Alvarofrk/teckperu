"""
Vistas para los dashboards de certificados
Solo accesible para administradores e instructores
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Q, F, Prefetch
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.utils.translation import gettext as _
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from datetime import datetime, timedelta
import json
import csv
from io import StringIO

from accounts.decorators import admin_required, lecturer_required
from accounts.models import User, Student
from course.models import Course, Program
from quiz.models import Sitting, Quiz
from core.models import Semester, Session


def admin_or_lecturer_required(view_func):
    """
    Decorador personalizado que permite acceso a administradores e instructores
    """
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and (
            request.user.is_staff or 
            hasattr(request.user, 'lecturer') or 
            request.user.groups.filter(name='Instructores').exists()
        ):
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, _('No tienes permisos para acceder a esta sección.'))
            return redirect('home')
    return wrapper


@login_required
@admin_or_lecturer_required
def certificates_dashboard(request):
    """
    Dashboard principal de certificados - Vista general
    """
    # Generar clave de cache única basada en filtros
    cache_key = get_cache_key('certificates_dashboard', 
                             date_from=request.GET.get('date_from'),
                             date_to=request.GET.get('date_to'))
    
    # Intentar obtener del cache
    cached_context = cache.get(cache_key)
    if cached_context is not None:
        return render(request, 'quiz/dashboards/certificates_overview.html', cached_context)
    
    # Construir filtros de fecha
    date_filters = Q()
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        date_filters &= Q(fecha_aprobacion__gte=date_from)
    if date_to:
        date_filters &= Q(fecha_aprobacion__gte=date_to)
    
    # Obtener todos los sittings completos con prefetch optimizado
    completed_sittings = Sitting.objects.filter(
        quiz__course__isnull=False,
        complete=True
    ).filter(date_filters).select_related(
        'quiz', 'course', 'course__program'
    ).prefetch_related(
        Prefetch('user__student', queryset=Student.objects.only('empresa'))
    )
    
    # Calcular estadísticas de una vez
    total_attempts = completed_sittings.count()
    approved_certificates = 0
    
    for sitting in completed_sittings:
        if is_sitting_approved(sitting):
            approved_certificates += 1
    
    total_certificates = approved_certificates
    pending_certificates = total_attempts - approved_certificates
    approval_rate = (approved_certificates / total_attempts * 100) if total_attempts > 0 else 0
    
    # Datos para gráficos (con cache individual)
    monthly_data = get_monthly_certificates_data_cached(date_filters)
    program_data = get_program_distribution_data_cached(date_filters)
    company_data = get_company_distribution_data_cached(date_filters)
    gender_data = get_gender_distribution_data_cached(date_filters)
    top_courses = get_top_courses_data_cached(date_filters)
    
    context = {
        'total_certificates': total_certificates,
        'total_attempts': total_attempts,
        'approved_certificates': approved_certificates,
        'pending_certificates': pending_certificates,
        'approval_rate': approval_rate,
        'monthly_labels': json.dumps(monthly_data['labels']),
        'monthly_data': json.dumps(monthly_data['data']),
        'program_labels': json.dumps(program_data['labels']),
        'program_data': json.dumps(program_data['data']),
        'company_labels': json.dumps(company_data['labels']),
        'company_data': json.dumps(company_data['data']),
        'gender_labels': json.dumps(gender_data['labels']),
        'gender_data': json.dumps(gender_data['data']),
        'top_courses': top_courses,
        'filters': {
            'date_from': date_from,
            'date_to': date_to,
        },
        'last_update': timezone.now().strftime('%H:%M:%S'),
        'total_records': total_attempts
    }
    
    # Guardar en cache
    cache.set(cache_key, context, 300)  # 5 minutos
    
    return render(request, 'quiz/dashboards/certificates_overview.html', context)


@login_required
@admin_or_lecturer_required
def course_dashboard(request):
    """
    Dashboard de rendimiento por curso específico
    """
    # Generar clave de cache única
    cache_key = get_cache_key('course_dashboard', 
                             course=request.GET.get('course'),
                             date_from=request.GET.get('date_from'),
                             date_to=request.GET.get('date_to'),
                             page=request.GET.get('page', 1))
    
    # Intentar obtener del cache
    cached_context = cache.get(cache_key)
    if cached_context is not None:
        return render(request, 'quiz/dashboards/course_performance.html', cached_context)
    
    available_courses = Course.objects.all().order_by('title')
    selected_course = None
    course_stats = {}
    course_participants = []
    score_distribution = []
    monthly_course_data = {'labels': [], 'data': []}
    
    # Obtener filtros
    course_slug = request.GET.get('course')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if course_slug:
        selected_course = get_object_or_404(Course, slug=course_slug)
        
        # Construir filtros de fecha
        date_filters = Q()
        if date_from:
            date_filters &= Q(fecha_aprobacion__gte=date_from)
        if date_to:
            date_filters &= Q(fecha_aprobacion__lte=date_to)
        
        # Obtener participantes del curso con prefetch optimizado
        course_participants = Sitting.objects.filter(
            quiz__course=selected_course
        ).filter(date_filters).select_related(
            'user', 'user__student', 'quiz', 'course'
        ).prefetch_related(
            Prefetch('user__student', queryset=Student.objects.only('empresa'))
        ).order_by('-fecha_aprobacion')
        
        # Calcular nota en escala del 1 al 20 para cada participante
        for participant in course_participants:
            participant.grade_1_to_20 = round((participant.get_percent_correct / 100) * 20, 1)
        
        # Paginación - 10 participantes por página
        paginator = Paginator(course_participants, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Calcular estadísticas del curso
        course_stats = calculate_course_stats(course_participants)
        
        # Distribución de puntuaciones
        score_distribution = calculate_score_distribution(course_participants)
        
        # Datos mensuales del curso
        monthly_course_data = get_course_monthly_data(selected_course, date_filters)
    
    context = {
        'available_courses': available_courses,
        'selected_course': selected_course,
        'course_stats': course_stats,
        'course_participants': page_obj if 'page_obj' in locals() else [],
        'page_obj': page_obj if 'page_obj' in locals() else None,
        'score_distribution': json.dumps(score_distribution),
        'monthly_course_labels': json.dumps(monthly_course_data['labels']),
        'monthly_course_data': json.dumps(monthly_course_data['data']),
        'filters': {
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    
    # Guardar en cache
    cache.set(cache_key, context, 300)  # 5 minutos
    
    return render(request, 'quiz/dashboards/course_performance.html', context)


@login_required
@admin_or_lecturer_required
def temporal_dashboard(request):
    """
    Dashboard de análisis temporal de certificados
    """
    available_programs = Program.objects.all().order_by('title')
    
    # Obtener filtros
    period = request.GET.get('period', 'monthly')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    program_id = request.GET.get('program')
    
    # Construir filtros
    date_filters = Q()
    if date_from:
        date_filters &= Q(fecha_aprobacion__gte=date_from)
    if date_to:
        date_filters &= Q(fecha_aprobacion__lte=date_to)
    
    program_filters = Q()
    if program_id:
        program_filters &= Q(quiz__course__program_id=program_id)
    

    
    try:
        # Obtener datos temporales
        temporal_data = get_temporal_data(period, date_filters, program_filters)
        temporal_stats = calculate_temporal_stats(temporal_data)
        
        # Datos para gráficos
        year_comparison_data = get_year_comparison_data(date_filters, program_filters)
        seasonal_data = get_seasonal_patterns_data(date_filters, program_filters)
    except Exception as e:
        # En caso de error, usar datos vacíos
        print(f"Error en temporal_dashboard: {e}")
        temporal_data = {'labels': [], 'data': []}
        temporal_stats = {
            'growth_rate': 0,
            'peak_period': 'Error',
            'trend': 'Error',
            'avg_period': 0,
            'total_period': 0,
            'best_period': 'Error',
            'growth_trend': 'Error'
        }
        year_comparison_data = {'labels': [], 'data': []}
        seasonal_data = {'labels': [], 'data': []}
        error_message = str(e)
    
    context = {
        'available_programs': available_programs,
        'temporal_data': temporal_data,
        'temporal_stats': temporal_stats,
        'temporal_labels': json.dumps(temporal_data['labels']),
        'temporal_data_values': json.dumps(temporal_data['data']),
        'year_comparison_labels': json.dumps(year_comparison_data['labels']),
        'year_comparison_data': json.dumps(year_comparison_data['data']),
        'seasonal_labels': json.dumps(seasonal_data['labels']),
        'seasonal_data': json.dumps(seasonal_data['data']),
        'filters': {
            'period': period,
            'date_from': date_from,
            'date_to': date_to,
            'program': program_id,
        },
        'error_message': error_message if 'error_message' in locals() else None
    }
    
    return render(request, 'quiz/dashboards/temporal_analysis.html', context)


@login_required
@admin_or_lecturer_required
def export_dashboard(request):
    """
    Dashboard de exportación de reportes
    """
    available_courses = Course.objects.all().order_by('title')
    available_programs = Program.objects.all().order_by('title')
    available_instructors = User.objects.filter(
        Q(is_staff=True) | 
        Q(groups__name='Instructores') |
        Q(lecturer__isnull=False)
    ).distinct().order_by('first_name')
    
    # Obtener filtros
    report_type = request.GET.get('report_type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    format_type = request.GET.get('format', 'pdf')
    
    report_data = None
    report_headers = []
    report_summary = {}
    report_pagination = None
    
    if report_type:
        # Generar reporte
        report_data, report_headers, report_summary = generate_report(
            report_type, date_from, date_to, request.GET
        )
        
        # Paginación
        if report_data:
            paginator = Paginator(report_data, 50)  # 50 registros por página
            page_number = request.GET.get('page', 1)
            report_pagination = paginator.get_page(page_number)
            report_data = report_pagination
    
    # Si se solicita exportación
    if request.GET.get('export') == 'true' and report_data:
        return export_report_data(
            report_data, report_headers, report_type, format_type
        )
    
    context = {
        'available_courses': available_courses,
        'available_programs': available_programs,
        'available_instructors': available_instructors,
        'report_data': report_data,
        'report_headers': report_headers,
        'report_summary': report_summary,
        'report_pagination': report_pagination,
        'filters': {
            'report_type': report_type,
            'date_from': date_from,
            'date_to': date_to,
            'format': format_type,
        }
    }
    
    return render(request, 'quiz/dashboards/export_reports.html', context)


# ===== FUNCIONES AUXILIARES =====

def get_cache_key(prefix, **kwargs):
    """Generar clave de cache única"""
    key_parts = [prefix]
    for k, v in sorted(kwargs.items()):
        if v is not None:
            key_parts.append(f"{k}_{v}")
    return "_".join(key_parts)

def cache_dashboard_data(func):
    """Decorador para cachear datos del dashboard"""
    def wrapper(*args, **kwargs):
        # Generar clave de cache única
        cache_key = get_cache_key(f"dashboard_{func.__name__}", **kwargs)
        
        # Intentar obtener del cache
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Si no está en cache, ejecutar función y guardar
        result = func(*args, **kwargs)
        cache.set(cache_key, result, 300)  # 5 minutos
        return result
    return wrapper

def is_sitting_approved(sitting):
    """Determinar si un sitting está aprobado"""
    return sitting.complete and sitting.get_percent_correct >= sitting.quiz.pass_mark

def calculate_sittings_stats(sittings):
    """Calcular estadísticas de una lista de sittings"""
    approved_count = 0
    pending_count = 0
    total_score = 0
    
    for sitting in sittings:
        if sitting.complete:
            total_score += sitting.current_score
            if is_sitting_approved(sitting):
                approved_count += 1
            else:
                pending_count += 1
    
    avg_score = total_score / len(sittings) if sittings.exists() else 0
    
    return {
        'approved_count': approved_count,
        'pending_count': pending_count,
        'avg_score': avg_score
    }

@cache_dashboard_data
def get_monthly_certificates_data_cached(date_filters=None):
    """Obtener datos de certificados por mes (con cache)"""
    current_year = timezone.now().year
    months = []
    data = []
    
    # Construir filtros base
    base_filters = Q(
        quiz__course__isnull=False,
        fecha_aprobacion__year=current_year,
        complete=True
    )
    
    if date_filters:
        base_filters &= date_filters
    
    # Obtener todos los sittings del año de una vez
    year_sittings = Sitting.objects.filter(base_filters).select_related('quiz')
    
    # Agrupar por mes y contar aprobados
    monthly_counts = {}
    for sitting in year_sittings:
        if sitting.fecha_aprobacion and is_sitting_approved(sitting):
            month = sitting.fecha_aprobacion.month
            if month not in monthly_counts:
                monthly_counts[month] = 0
            monthly_counts[month] += 1
    
    # Crear array ordenado
    for month in range(1, 13):
        month_name = datetime(current_year, month, 1).strftime('%b')
        months.append(month_name)
        data.append(monthly_counts.get(month, 0))
    
    return {'labels': months, 'data': data}

def get_monthly_certificates_data():
    """Función original para compatibilidad"""
    return get_monthly_certificates_data_cached()


@cache_dashboard_data
def get_program_distribution_data_cached(date_filters=None):
    """Obtener distribución de certificados por programa (con cache)"""
    # Construir filtros base
    base_filters = Q(
        quiz__course__isnull=False,
        complete=True
    )
    
    if date_filters:
        base_filters &= date_filters
    
    # Obtener todos los sittings aprobados de una vez
    approved_sittings = Sitting.objects.filter(base_filters).select_related(
        'course__program'
    ).prefetch_related('quiz')
    
    # Agrupar por programa y contar
    program_counts = {}
    for sitting in approved_sittings:
        if is_sitting_approved(sitting) and sitting.course.program:
            program_title = sitting.course.program.title
            program_counts[program_title] = program_counts.get(program_title, 0) + 1
    
    # Ordenar y tomar top 8
    sorted_programs = sorted(program_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    
    labels = [p[0] for p in sorted_programs]
    data = [p[1] for p in sorted_programs]
    
    return {'labels': labels, 'data': data}

def get_program_distribution_data():
    """Función original para compatibilidad"""
    return get_program_distribution_data_cached()


@cache_dashboard_data
def get_company_distribution_data_cached(date_filters=None):
    """
    Obtener distribución de certificados por empresa (con cache)
    - Muestra top 10 empresas con más certificados
    - Si hay más de 10 empresas, agrupa las restantes en "Otras"
    - Incluye usuarios sin empresa en "Sin Empresa"
    """
    # Construir filtros base
    base_filters = Q(
        quiz__course__isnull=False,
        complete=True
    )
    
    if date_filters:
        base_filters &= date_filters
    
    # Obtener todos los sittings aprobados de una vez
    sittings = Sitting.objects.filter(base_filters).select_related(
        'user__student', 'quiz'
    ).prefetch_related('user__student')
    
    company_data = {}
    no_empresa_count = 0
    
    for sitting in sittings:
        if is_sitting_approved(sitting):
            # Verificar si tiene datos de empresa
            if (hasattr(sitting.user, 'student') and 
                sitting.user.student and 
                sitting.user.student.empresa and 
                sitting.user.student.empresa.strip()):
                
                empresa = sitting.user.student.empresa.strip()
                company_data[empresa] = company_data.get(empresa, 0) + 1
            else:
                no_empresa_count += 1
    
    # Agregar usuarios sin empresa si los hay
    if no_empresa_count > 0:
        company_data['Sin Empresa'] = no_empresa_count
    
    # Si no hay datos, retornar vacío
    if not company_data:
        return {'labels': [], 'data': []}
    
    # Mostrar top 10 empresas (o todas si hay menos de 10)
    sorted_companies = sorted(company_data.items(), key=lambda x: x[1], reverse=True)
    
    if len(sorted_companies) <= 10:
        labels = [c[0] for c in sorted_companies]
        data = [c[1] for c in sorted_companies]
    else:
        top_companies = sorted_companies[:10]
        other_companies = sorted_companies[10:]
        
        other_total = sum(count for _, count in other_companies)
        
        labels = [c[0] for c in top_companies]
        data = [c[1] for c in top_companies]
        
        if other_total > 0:
            labels.append('Otras')
            data.append(other_total)
    
    return {'labels': labels, 'data': data}

def get_company_distribution_data():
    """Función original para compatibilidad"""
    return get_company_distribution_data_cached()


@cache_dashboard_data
def get_gender_distribution_data_cached(date_filters=None):
    """Obtener distribución de certificados por género (con cache)"""
    # Construir filtros base
    base_filters = Q(
        quiz__course__isnull=False,
        complete=True
    )
    
    if date_filters:
        base_filters &= date_filters
    
    # Obtener todos los sittings aprobados de una vez
    sittings = Sitting.objects.filter(base_filters).select_related(
        'user', 'quiz'
    )
    
    gender_data = {'M': 0, 'F': 0}
    
    for sitting in sittings:
        if (sitting.user.gender and 
            sitting.user.gender.strip() and
            is_sitting_approved(sitting)):
            
            gender = sitting.user.gender
            if gender in gender_data:
                gender_data[gender] += 1
    
    labels = ['Masculino', 'Femenino']
    data = [gender_data['M'], gender_data['F']]
    
    return {'labels': labels, 'data': data}

def get_gender_distribution_data():
    """Función original para compatibilidad"""
    return get_gender_distribution_data_cached()


@cache_dashboard_data
def get_top_courses_data_cached(date_filters=None):
    """
    Obtener top 10 cursos con más certificados (con cache)
    - Solo cuenta el intento final aprobado por usuario/curso
    - Calcula promedio en escala del 1 al 20
    """
    # Construir filtros base
    base_filters = Q(
        quiz__course__isnull=False,
        complete=True
    )
    
    if date_filters:
        base_filters &= date_filters
    
    # Obtener todos los sittings aprobados de una vez
    approved_sittings = Sitting.objects.filter(base_filters).select_related(
        'course', 'course__program', 'quiz', 'user'
    )
    
    # Agrupar por usuario y curso para obtener solo el intento final aprobado
    user_course_approved = {}
    
    for sitting in approved_sittings:
        if is_sitting_approved(sitting):
            user_course_key = (sitting.user.id, sitting.course.id)
            
            if user_course_key not in user_course_approved or sitting.end > user_course_approved[user_course_key].end:
                user_course_approved[user_course_key] = sitting
    
    # Procesar solo los intentos finales aprobados
    course_data = {}
    for sitting in user_course_approved.values():
        course_key = (sitting.course.title, sitting.course.code, 
                     sitting.course.program.title if sitting.course.program else 'Sin programa')
        
        if course_key not in course_data:
            course_data[course_key] = {
                'total_certificates': 0,
                'total_score': 0
            }
        
        course_data[course_key]['total_certificates'] += 1
        score_1_to_20 = (sitting.get_percent_correct / 100) * 20
        course_data[course_key]['total_score'] += score_1_to_20
    
    # Calcular estadísticas y ordenar
    result = []
    for (title, code, program), data in course_data.items():
        avg_score = data['total_score'] / data['total_certificates'] if data['total_certificates'] > 0 else 0
        
        result.append({
            'course__title': title,
            'course__code': code,
            'course__program__title': program,
            'count': data['total_certificates'],
            'pass_rate': 100.0,
            'avg_score': avg_score
        })
    
    return sorted(result, key=lambda x: x['count'], reverse=True)[:10]

def get_top_courses_data():
    """Función original para compatibilidad"""
    return get_top_courses_data_cached()


def calculate_course_stats(participants):
    """Calcular estadísticas del curso"""
    if not participants:
        return {
            'total_participants': 0,
            'approved_participants': 0,
            'average_score': 0,
            'in_progress': 0,
            'total_certificates': 0,
            'approval_rate': 0
        }
    
    total = participants.count()
    approved = 0
    total_score = 0
    in_progress = 0
    
    for participant in participants:
        if participant.complete:
            # Convertir porcentaje a escala del 1 al 20
            percent_score = participant.get_percent_correct
            score_1_to_20 = (percent_score / 100) * 20
            total_score += score_1_to_20
            
            # Usar función consistente para aprobación
            if is_sitting_approved(participant):
                approved += 1
            else:
                in_progress += 1
    
    avg_score = total_score / total if total > 0 else 0
    
    return {
        'total_participants': total,
        'approved_participants': approved,
        'average_score': avg_score,
        'in_progress': in_progress,
        'total_certificates': total,
        'approval_rate': (approved / total * 100) if total > 0 else 0
    }


def calculate_score_distribution(participants):
    """Calcular distribución de puntuaciones en escala del 1 al 20"""
    if not participants:
        return [0, 0, 0, 0, 0]
    
    distribution = [0, 0, 0, 0, 0]  # 18-20, 15-17, 12-14, 9-11, <9
    
    for participant in participants:
        if participant.complete:
            # Convertir porcentaje a escala del 1 al 20
            score_1_to_20 = (participant.get_percent_correct / 100) * 20
            if score_1_to_20 >= 18:
                distribution[0] += 1  # 18-20 (Excelente)
            elif score_1_to_20 >= 15:
                distribution[1] += 1  # 15-17 (Muy Bueno)
            elif score_1_to_20 >= 12:
                distribution[2] += 1  # 12-14 (Bueno)
            elif score_1_to_20 >= 9:
                distribution[3] += 1  # 9-11 (Regular)
            else:
                distribution[4] += 1  # <9 (Deficiente)
    
    return distribution


def get_course_monthly_data(course, date_filters):
    """Obtener datos mensuales del curso"""
    current_year = timezone.now().year
    months = []
    data = []
    
    for month in range(1, 13):
        month_name = datetime(current_year, month, 1).strftime('%b')
        months.append(month_name)
        
        count = Sitting.objects.filter(
            quiz__course=course,
            fecha_aprobacion__year=current_year,
            fecha_aprobacion__month=month
        ).filter(date_filters).count()
        data.append(count)
    
    return {'labels': months, 'data': data}


def get_temporal_data(period, date_filters, program_filters):
    """Obtener datos temporales según el período"""
    base_filters = date_filters & program_filters
    
    if period == 'monthly':
        return get_monthly_temporal_data(base_filters)
    elif period == 'quarterly':
        return get_quarterly_temporal_data(base_filters)
    else:  # yearly
        return get_yearly_temporal_data(base_filters)


def get_monthly_temporal_data(base_filters):
    """Obtener datos mensuales temporales - Solo certificados aprobados"""
    current_year = timezone.now().year
    months = []
    data = []
    
    # Obtener todos los sittings del año de una vez
    year_sittings = Sitting.objects.filter(
        quiz__course__isnull=False,
        fecha_aprobacion__year=current_year,
        complete=True,
        fecha_aprobacion__isnull=False  # Solo con fecha de aprobación
    ).filter(base_filters).select_related('quiz')
    
    # Agrupar por mes y contar aprobados
    monthly_counts = {}
    for sitting in year_sittings:
        # Verificar que fecha_aprobacion no sea None
        if sitting.fecha_aprobacion and is_sitting_approved(sitting):
            month = sitting.fecha_aprobacion.month
            if month not in monthly_counts:
                monthly_counts[month] = 0
            monthly_counts[month] += 1
    
    # Crear array ordenado
    for month in range(1, 13):
        month_name = datetime(current_year, month, 1).strftime('%b')
        months.append(month_name)
        data.append(monthly_counts.get(month, 0))
    
    return {'labels': months, 'data': data}


def get_quarterly_temporal_data(base_filters):
    """Obtener datos trimestrales temporales - Solo certificados aprobados"""
    current_year = timezone.now().year
    quarters = ['Q1 (Ene-Mar)', 'Q2 (Abr-Jun)', 'Q3 (Jul-Sep)', 'Q4 (Oct-Dic)']
    data = []
    
    # Obtener todos los sittings del año de una vez
    year_sittings = Sitting.objects.filter(
        quiz__course__isnull=False,
        fecha_aprobacion__year=current_year,
        complete=True,
        fecha_aprobacion__isnull=False  # Solo con fecha de aprobación
    ).filter(base_filters).select_related('quiz')
    
    # Agrupar por trimestre y contar aprobados
    quarterly_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    
    for sitting in year_sittings:
        # Verificar que fecha_aprobacion no sea None
        if sitting.fecha_aprobacion and is_sitting_approved(sitting):
            month = sitting.fecha_aprobacion.month
            quarter = ((month - 1) // 3) + 1
            quarterly_counts[quarter] += 1
    
    # Crear array ordenado
    for quarter in range(1, 5):
        data.append(quarterly_counts[quarter])
    
    return {'labels': quarters, 'data': data}


def get_yearly_temporal_data(base_filters):
    """Obtener datos anuales temporales - Solo certificados aprobados"""
    years = list(range(2020, timezone.now().year + 1))
    data = []
    
    # Obtener todos los sittings de todos los años de una vez
    all_sittings = Sitting.objects.filter(
        quiz__course__isnull=False,
        fecha_aprobacion__year__in=years,
        complete=True,
        fecha_aprobacion__isnull=False  # Solo con fecha de aprobación
    ).filter(base_filters).select_related('quiz')
    
    # Agrupar por año y contar aprobados
    yearly_counts = {year: 0 for year in years}
    
    for sitting in all_sittings:
        # Verificar que fecha_aprobacion no sea None
        if sitting.fecha_aprobacion and is_sitting_approved(sitting):
            year = sitting.fecha_aprobacion.year
            if year in yearly_counts:
                yearly_counts[year] += 1
    
    # Crear array ordenado
    for year in years:
        data.append(yearly_counts[year])
    
    return {'labels': years, 'data': data}


def calculate_temporal_stats(temporal_data):
    """Calcular estadísticas temporales mejoradas"""
    data = temporal_data['data']
    if not data:
        return {
            'growth_rate': 0,
            'peak_period': 'N/A',
            'trend': 'Estable',
            'avg_period': 0,
            'total_period': 0,
            'best_period': 'N/A',
            'growth_trend': 'Sin datos'
        }
    
    total = sum(data)
    avg_period = total / len(data) if len(data) > 0 else 0
    
    # Calcular crecimiento
    if len(data) >= 2:
        growth_rate = ((data[-1] - data[0]) / data[0] * 100) if data[0] > 0 else 0
    else:
        growth_rate = 0
    
    # Encontrar período pico
    peak_index = data.index(max(data))
    peak_period = temporal_data['labels'][peak_index]
    
    # Determinar tendencia
    if len(data) >= 3:
        recent_avg = sum(data[-3:]) / 3
        earlier_avg = sum(data[:3]) / 3
        if recent_avg > earlier_avg * 1.1:
            trend = 'Ascendente'
        elif recent_avg < earlier_avg * 0.9:
            trend = 'Descendente'
        else:
            trend = 'Estable'
    else:
        trend = 'Estable'
    
    # Determinar tendencia de crecimiento
    if growth_rate > 10:
        growth_trend = 'Crecimiento Fuerte'
    elif growth_rate > 0:
        growth_trend = 'Crecimiento Moderado'
    elif growth_rate < -10:
        growth_trend = 'Descenso Significativo'
    elif growth_rate < 0:
        growth_trend = 'Descenso Moderado'
    else:
        growth_trend = 'Estable'
    
    return {
        'growth_rate': growth_rate,
        'peak_period': peak_period,
        'trend': trend,
        'avg_period': avg_period,
        'total_period': total,
        'best_period': peak_period,
        'growth_trend': growth_trend
    }


def get_year_comparison_data(date_filters, program_filters):
    """Obtener datos de comparación año tras año - Solo certificados aprobados"""
    current_year = timezone.now().year
    years = list(range(current_year - 3, current_year + 1))
    data = []
    
    base_filters = date_filters & program_filters
    
    # Obtener todos los sittings de todos los años de una vez
    all_sittings = Sitting.objects.filter(
        quiz__course__isnull=False,
        fecha_aprobacion__year__in=years,
        complete=True,
        fecha_aprobacion__isnull=False  # Solo con fecha de aprobación
    ).filter(base_filters).select_related('quiz')
    
    # Agrupar por año y contar aprobados
    yearly_counts = {year: 0 for year in years}
    
    for sitting in all_sittings:
        # Verificar que fecha_aprobacion no sea None
        if sitting.fecha_aprobacion and is_sitting_approved(sitting):
            year = sitting.fecha_aprobacion.year
            if year in yearly_counts:
                yearly_counts[year] += 1
    
    # Crear array ordenado
    for year in years:
        data.append(yearly_counts[year])
    
    return {'labels': years, 'data': data}


def get_seasonal_patterns_data(date_filters, program_filters):
    """Obtener distribución por trimestres - Solo certificados aprobados"""
    quarters = ['Q1 (Ene-Mar)', 'Q2 (Abr-Jun)', 'Q3 (Jul-Sep)', 'Q4 (Oct-Dic)']
    data = []
    
    base_filters = date_filters & program_filters
    
    # Obtener todos los sittings de una vez
    all_sittings = Sitting.objects.filter(
        quiz__course__isnull=False,
        complete=True,
        fecha_aprobacion__isnull=False  # Solo con fecha de aprobación
    ).filter(base_filters).select_related('quiz')
    
    # Agrupar por trimestre y contar aprobados
    quarterly_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    
    for sitting in all_sittings:
        # Verificar que fecha_aprobacion no sea None
        if sitting.fecha_aprobacion and is_sitting_approved(sitting):
            month = sitting.fecha_aprobacion.month
            quarter = ((month - 1) // 3) + 1
            quarterly_counts[quarter] += 1
    
    # Crear array ordenado
    for quarter in range(1, 5):
        data.append(quarterly_counts[quarter])
    
    return {'labels': quarters, 'data': data}


def generate_report(report_type, date_from, date_to, filters):
    """Generar reporte según el tipo"""
    date_filters = Q()
    if date_from:
        date_filters &= Q(fecha_aprobacion__gte=date_from)
    if date_to:
        date_filters &= Q(fecha_aprobacion__lte=date_to)
    
    if report_type == 'general':
        return generate_general_report(date_filters)
    elif report_type == 'course':
        return generate_course_report(date_filters, filters.get('course'))
    elif report_type == 'program':
        return generate_program_report(date_filters, filters.get('program'))
    elif report_type == 'instructor':
        return generate_instructor_report(date_filters, filters.get('instructor'))
    elif report_type == 'temporal':
        return generate_temporal_report(date_filters)
    else:
        return [], [], {}


def generate_general_report(date_filters):
    """Generar reporte general"""
    sittings = Sitting.objects.filter(
        quiz__course__isnull=False
    ).filter(date_filters).select_related(
        'user', 'quiz', 'course', 'course__program'
    ).order_by('-fecha_aprobacion')
    
    headers = [
        'Participante', 'Curso', 'Programa', 'Puntuación', 
        'Estado', 'Fecha Aprobación', 'Código Certificado'
    ]
    
    data = []
    for sitting in sittings:
        data.append([
            sitting.user.get_full_name(),
            sitting.course.title,
            sitting.course.program.title,
            f"{sitting.current_score}%",
            'Aprobado' if is_sitting_approved(sitting) else 'Reprobado',
            sitting.fecha_aprobacion.strftime('%d/%m/%Y') if sitting.fecha_aprobacion else '-',
            sitting.certificate_code or '-'
        ])
    
    stats = calculate_sittings_stats(sittings)
    summary = {
        'total_records': len(data),
        'approved_count': stats['approved_count'],
        'pending_count': stats['pending_count'],
        'avg_score': stats['avg_score']
    }
    
    return data, headers, summary


def generate_course_report(date_filters, course_slug):
    """Generar reporte por curso"""
    if not course_slug:
        return [], [], {}
    
    course = Course.objects.filter(slug=course_slug).first()
    if not course:
        return [], [], {}
    
    sittings = Sitting.objects.filter(
        quiz__course=course
    ).filter(date_filters).select_related(
        'user', 'user__student'
    ).order_by('-fecha_aprobacion')
    
    headers = [
        'Participante', 'Empresa', 'Puntuación', 'Estado', 
        'Fecha Aprobación', 'Código Certificado'
    ]
    
    data = []
    for sitting in sittings:
        empresa = sitting.user.student.empresa if hasattr(sitting.user, 'student') else '-'
        data.append([
            sitting.user.get_full_name(),
            empresa,
            f"{sitting.current_score}%",
            'Aprobado' if is_sitting_approved(sitting) else 'Reprobado',
            sitting.fecha_aprobacion.strftime('%d/%m/%Y') if sitting.fecha_aprobacion else '-',
            sitting.certificate_code or '-'
        ])
    
    stats = calculate_sittings_stats(sittings)
    summary = {
        'total_records': len(data),
        'approved_count': stats['approved_count'],
        'pending_count': stats['pending_count'],
        'avg_score': stats['avg_score']
    }
    
    return data, headers, summary


def generate_program_report(date_filters, program_id):
    """Generar reporte por programa"""
    if not program_id:
        return [], [], {}
    
    sittings = Sitting.objects.filter(
        quiz__course__program_id=program_id
    ).filter(date_filters).select_related(
        'user', 'quiz', 'course', 'course__program'
    ).order_by('-fecha_aprobacion')
    
    headers = [
        'Participante', 'Curso', 'Puntuación', 'Estado', 
        'Fecha Aprobación', 'Código Certificado'
    ]
    
    data = []
    for sitting in sittings:
        data.append([
            sitting.user.get_full_name(),
            sitting.course.title,
            f"{sitting.current_score}%",
            'Aprobado' if is_sitting_approved(sitting) else 'Reprobado',
            sitting.fecha_aprobacion.strftime('%d/%m/%Y') if sitting.fecha_aprobacion else '-',
            sitting.certificate_code or '-'
        ])
    
    stats = calculate_sittings_stats(sittings)
    summary = {
        'total_records': len(data),
        'approved_count': stats['approved_count'],
        'pending_count': stats['pending_count'],
        'avg_score': stats['avg_score']
    }
    
    return data, headers, summary


def generate_instructor_report(date_filters, instructor_id):
    """Generar reporte por instructor"""
    if not instructor_id:
        return [], [], {}
    
    sittings = Sitting.objects.filter(
        quiz__course__allocations__lecturer_id=instructor_id
    ).filter(date_filters).select_related(
        'user', 'quiz', 'course'
    ).order_by('-fecha_aprobacion')
    
    headers = [
        'Participante', 'Curso', 'Puntuación', 'Estado', 
        'Fecha Aprobación', 'Código Certificado'
    ]
    
    data = []
    for sitting in sittings:
        data.append([
            sitting.user.get_full_name(),
            sitting.course.title,
            f"{sitting.current_score}%",
            'Aprobado' if is_sitting_approved(sitting) else 'Reprobado',
            sitting.fecha_aprobacion.strftime('%d/%m/%Y') if sitting.fecha_aprobacion else '-',
            sitting.certificate_code or '-'
        ])
    
    stats = calculate_sittings_stats(sittings)
    summary = {
        'total_records': len(data),
        'approved_count': stats['approved_count'],
        'pending_count': stats['pending_count'],
        'avg_score': stats['avg_score']
    }
    
    return data, headers, summary


def generate_temporal_report(date_filters):
    """Generar reporte temporal"""
    sittings = Sitting.objects.filter(
        quiz__course__isnull=False
    ).filter(date_filters).select_related(
        'user', 'quiz', 'course', 'course__program'
    ).order_by('fecha_aprobacion')
    
    headers = [
        'Fecha', 'Participante', 'Curso', 'Programa', 'Puntuación', 
        'Estado', 'Código Certificado'
    ]
    
    data = []
    for sitting in sittings:
        data.append([
            sitting.fecha_aprobacion.strftime('%d/%m/%Y') if sitting.fecha_aprobacion else '-',
            sitting.user.get_full_name(),
            sitting.course.title,
            sitting.course.program.title,
            f"{sitting.current_score}%",
            'Aprobado' if is_sitting_approved(sitting) else 'Reprobado',
            sitting.certificate_code or '-'
        ])
    
    stats = calculate_sittings_stats(sittings)
    summary = {
        'total_records': len(data),
        'approved_count': stats['approved_count'],
        'pending_count': stats['pending_count'],
        'avg_score': stats['avg_score']
    }
    
    return data, headers, summary


def export_report_data(data, headers, report_type, format_type):
    """Exportar datos del reporte"""
    if format_type == 'csv':
        return export_to_csv(data, headers, report_type)
    elif format_type == 'excel':
        return export_to_excel(data, headers, report_type)
    else:  # PDF
        return export_to_pdf(data, headers, report_type)


def export_to_csv(data, headers, report_type):
    """Exportar a CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="reporte_{report_type}_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    # Configurar para caracteres especiales
    response.write('\ufeff')  # BOM para UTF-8
    
    writer = csv.writer(response)
    writer.writerow(headers)
    writer.writerows(data)
    
    return response


def export_to_excel(data, headers, report_type):
    """Exportar a Excel (CSV con extensión .xlsx)"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="reporte_{report_type}_{timezone.now().strftime("%Y%m%d")}.xlsx"'
    
    # Configurar para caracteres especiales
    response.write('\ufeff')  # BOM para UTF-8
    
    writer = csv.writer(response)
    writer.writerow(headers)
    writer.writerows(data)
    
    return response


def export_to_pdf(data, headers, report_type):
    """Exportar a PDF (por ahora devuelve CSV)"""
    # TODO: Implementar generación de PDF real
    return export_to_csv(data, headers, report_type)


def clear_dashboard_cache():
    """Limpiar todo el cache del dashboard"""
    # Obtener todas las claves de cache del dashboard
    cache_keys = []
    
    # Limpiar cache de funciones principales
    cache.delete_pattern('dashboard_*')
    
    # Limpiar cache específico
    cache.delete('certificates_dashboard')
    cache.delete('course_dashboard')
    
    print("Cache del dashboard limpiado")


def invalidate_cache_for_sitting(sitting_id):
    """Invalidar cache cuando se actualiza un sitting"""
    # Limpiar cache relacionado con certificados
    cache.delete_pattern('dashboard_certificates_*')
    cache.delete_pattern('dashboard_program_*')
    cache.delete_pattern('dashboard_company_*')
    cache.delete_pattern('dashboard_gender_*')
    cache.delete_pattern('dashboard_top_courses_*')
    
    print(f"Cache invalidado para sitting {sitting_id}")
