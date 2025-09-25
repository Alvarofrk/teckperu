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
import time

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
            request.user.is_lecturer or  # ✅ CORREGIDO: usar is_lecturer directamente
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
    
    # Construir filtros de fecha con validación
    date_filters = Q()
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Validar que las fechas sean válidas
    try:
        if date_from:
            # Validar formato de fecha
            datetime.strptime(date_from, '%Y-%m-%d')
            date_filters &= Q(end__gte=date_from)  # ✅ Usar fecha de finalización
        
        if date_to:
            # Validar formato de fecha
            datetime.strptime(date_to, '%Y-%m-%d')
            date_filters &= Q(end__lte=date_to)    # ✅ Usar fecha de finalización
            
        # Validar que date_from <= date_to
        if date_from and date_to and date_from > date_to:
            # Si las fechas están invertidas, intercambiarlas
            date_filters = Q()
            if date_from:
                date_filters &= Q(end__gte=date_to)  # ✅ Usar fecha de finalización
            if date_to:
                date_filters &= Q(end__lte=date_from) # ✅ Usar fecha de finalización
                
    except ValueError:
        # Si hay error en el formato de fecha, no aplicar filtros
        date_filters = Q()
        print(f"Error en formato de fecha: date_from={date_from}, date_to={date_to}")
    
    # Obtener todos los datos del dashboard de manera optimizada en una sola query
    optimized_data = get_optimized_dashboard_data(date_filters, date_from, date_to)
    
    # Extraer los datos de la función optimizada
    total_attempts = optimized_data['total_attempts']
    approved_certificates = optimized_data['approved_certificates']
    failed_attempts = optimized_data['failed_attempts']
    
    total_certificates = approved_certificates
    pending_certificates = failed_attempts
    approval_rate = (approved_certificates / total_attempts * 100) if total_attempts > 0 else 0
    
    # Datos para gráficos (ya procesados por la función optimizada)
    monthly_data = optimized_data['monthly_data']
    program_data = optimized_data['program_data']
    company_data = optimized_data['company_data']
    gender_data = optimized_data['gender_data']
    courses_data = optimized_data['courses_data']
    
    # Preparar contexto con manejo de errores
    try:
        context = {
            'total_certificates': total_certificates,
            'total_attempts': total_attempts,
            'approved_certificates': approved_certificates,
            'pending_certificates': pending_certificates,
            'approval_rate': approval_rate,
            'monthly_labels': json.dumps(monthly_data.get('labels', [])),
            'monthly_data': json.dumps(monthly_data.get('data', [])),
            'program_labels': json.dumps(program_data.get('labels', [])),
            'program_data': json.dumps(program_data.get('data', [])),
            'company_labels': json.dumps(company_data.get('labels', [])),
            'company_data': json.dumps(company_data.get('data', [])),
            'gender_labels': json.dumps(gender_data.get('labels', [])),
            'gender_data': json.dumps(gender_data.get('data', [])),
            'courses_data': courses_data or [],
            'filters': {
                'date_from': date_from,
                'date_to': date_to,
            },
            'last_update': timezone.now().strftime('%H:%M:%S'),
            'total_records': total_attempts
        }
    except Exception as e:
        print(f"Error preparando contexto: {e}")
        # Contexto de fallback
        context = {
            'total_certificates': 0,
            'total_attempts': 0,
            'approved_certificates': 0,
            'pending_certificates': 0,
            'approval_rate': 0,
            'monthly_labels': json.dumps([]),
            'monthly_data': json.dumps([]),
            'program_labels': json.dumps([]),
            'program_data': json.dumps([]),
            'company_labels': json.dumps([]),
            'company_data': json.dumps([]),
            'gender_labels': json.dumps([]),
            'gender_data': json.dumps([]),
            'courses_data': [],
            'filters': {
                'date_from': date_from,
                'date_to': date_to,
            },
            'last_update': timezone.now().strftime('%H:%M:%S'),
            'total_records': 0
        }
    
    # Limpiar cache corrupto antes de guardar
    try:
        cache.delete_pattern('certificates_dashboard*')
    except:
        pass
    
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
            date_filters &= Q(end__gte=date_from)  # Usar end en lugar de fecha_aprobacion
        if date_to:
            date_filters &= Q(end__lte=date_to)    # Usar end en lugar de fecha_aprobacion
        
        # Obtener participantes del curso con prefetch optimizado en una sola query
        course_participants = Sitting.objects.filter(
            quiz__course=selected_course
        ).filter(date_filters).select_related(
            'user', 'user__student', 'quiz', 'course'
        ).prefetch_related(
            Prefetch('user__student', queryset=Student.objects.only('empresa'))
        ).order_by('-end')  # Usar end en lugar de fecha_aprobacion
        
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
    """Generar clave de cache única de manera robusta"""
    try:
        key_parts = [str(prefix)]
        for k, v in sorted(kwargs.items()):
            if v is not None:
                # Convertir valores a string de manera segura
                safe_value = str(v).replace(' ', '_').replace('/', '_').replace(':', '_')
                key_parts.append(f"{k}_{safe_value}")
        return "_".join(key_parts)
    except Exception as e:
        print(f"Error generando clave de cache: {e}")
        # Clave de fallback
        return f"{prefix}_fallback_{int(time.time())}"

def cache_dashboard_data(func):
    """Decorador para cachear datos del dashboard de manera robusta"""
    def wrapper(*args, **kwargs):
        try:
            # Generar clave de cache única
            cache_key = get_cache_key(f"dashboard_{func.__name__}", **kwargs)
            
            # Intentar obtener del cache
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return cached_data
            
            # Si no está en cache, ejecutar función y guardar
            result = func(*args, **kwargs)
            
            # Validar que el resultado sea válido antes de cachear
            if result is not None:
                try:
                    cache.set(cache_key, result, 300)  # 5 minutos
                except Exception as e:
                    print(f"Error guardando en cache {cache_key}: {e}")
            
            return result
        except Exception as e:
            print(f"Error en decorador de cache para {func.__name__}: {e}")
            # En caso de error, ejecutar función sin cache
            return func(*args, **kwargs)
    return wrapper

def is_sitting_approved(sitting):
    """Determinar si un sitting está aprobado - Usa la lógica del modelo"""
    try:
        # Usar la lógica del modelo para consistencia
        return sitting.check_if_passed
    except (AttributeError, TypeError):
        # Fallback a la lógica anterior si hay problemas
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

def get_monthly_certificates_data_cached(date_filters=None, date_from=None, date_to=None):
    """Obtener datos de certificados por mes (OPTIMIZADO)"""
    from datetime import datetime
    current_year = timezone.now().year
    months = []
    data = []
    
    # Construir filtros base - Usar fecha de finalización para incluir todos los intentos
    base_filters = Q(
        quiz__course__isnull=False,
        complete=True
    )
    
    # Si hay filtros de fecha específicos, usarlos
    if date_filters:
        base_filters &= date_filters
    
    # Determinar el rango de meses basado en las fechas proporcionadas
    if date_from and date_to:
        try:
            # Parsear las fechas si son strings
            if isinstance(date_from, str):
                start_date = datetime.strptime(date_from, '%Y-%m-%d')
            else:
                start_date = date_from
                
            if isinstance(date_to, str):
                end_date = datetime.strptime(date_to, '%Y-%m-%d')
            else:
                end_date = date_to
            
            start_month = start_date.month
            start_year = start_date.year
            end_month = end_date.month
            end_year = end_date.year
            
            # Si es el mismo año, mostrar solo los meses del rango
            if start_year == end_year:
                month_range = range(start_month, end_month + 1)
            else:
                # Si cruza años, mostrar todos los meses del rango
                month_range = []
                for year in range(start_year, end_year + 1):
                    if year == start_year:
                        month_range.extend(range(start_month, 13))
                    elif year == end_year:
                        month_range.extend(range(1, end_month + 1))
                    else:
                        month_range.extend(range(1, 13))
                        
        except Exception as e:
            print(f"Error procesando fechas: {e}")
            # Fallback al año actual
            month_range = range(1, 13)
    else:
        # Si no hay fechas específicas, usar año actual como default
        base_filters &= Q(end__year=current_year)
        month_range = range(1, 13)
    
    # Crear array ordenado solo para los meses relevantes
    for month in month_range:
        # Determinar el año para el nombre del mes
        if date_from and isinstance(date_from, str):
            try:
                year_for_month = datetime.strptime(date_from, '%Y-%m-%d').year
            except:
                year_for_month = current_year
        elif date_from and hasattr(date_from, 'year'):
            year_for_month = date_from.year
        else:
            year_for_month = current_year
            
        month_name = datetime(year_for_month, month, 1).strftime('%b')
        months.append(month_name)
        
        # OPTIMIZACIÓN: Contar aprobados por mes usando query directa
        month_filter = base_filters & Q(end__month=month)
        if date_from and isinstance(date_from, str):
            try:
                start_date = datetime.strptime(date_from, '%Y-%m-%d')
                month_filter &= Q(end__year=start_date.year)
            except:
                pass
        
        # Contar solo los aprobados para este mes específico
        month_sittings = Sitting.objects.filter(month_filter).select_related('quiz')
        approved_count = 0
        
        for sitting in month_sittings:
            try:
                if sitting.check_if_passed:
                    approved_count += 1
            except:
                # Fallback si check_if_passed falla
                if sitting.complete and sitting.get_percent_correct >= sitting.quiz.pass_mark:
                    approved_count += 1
        
        data.append(approved_count)
    
    return {'labels': months, 'data': data}

def get_monthly_certificates_data():
    """Función original para compatibilidad"""
    return get_monthly_certificates_data_cached()


def get_program_distribution_data_cached(date_filters=None):
    """Obtener distribución de certificados por programa (sin cache individual)"""
    # Construir filtros base - Incluir todos los intentos completados
    base_filters = Q(
        quiz__course__isnull=False,
        complete=True
    )
    
    if date_filters:
        base_filters &= date_filters
    
    # Obtener todos los sittings completados de una vez
    all_sittings = Sitting.objects.filter(base_filters).select_related(
        'course__program'
    ).prefetch_related('quiz')
    
    # Agrupar por programa y contar solo los aprobados
    program_counts = {}
    for sitting in all_sittings:
        try:
            if is_sitting_approved(sitting) and sitting.course.program:
                program_title = sitting.course.program.title
                program_counts[program_title] = program_counts.get(program_title, 0) + 1
        except Exception as e:
            # Log del error para debugging
            print(f"Error procesando sitting {sitting.id} en distribución por programa: {e}")
            continue
    
    # Ordenar y tomar top 8
    sorted_programs = sorted(program_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    
    labels = [p[0] for p in sorted_programs]
    data = [p[1] for p in sorted_programs]
    
    return {'labels': labels, 'data': data}

def get_program_distribution_data():
    """Función original para compatibilidad"""
    return get_program_distribution_data_cached()


def get_company_distribution_data_cached(date_filters=None):
    """
    Obtener distribución de certificados por empresa (sin cache individual)
    - Muestra top 10 empresas con más certificados
    - Si hay más de 10 empresas, agrupa las restantes en "Otras"
    - Incluye usuarios sin empresa en "Sin Empresa"
    """
    # Construir filtros base - Incluir todos los intentos completados
    base_filters = Q(
        quiz__course__isnull=False,
        complete=True
    )
    
    if date_filters:
        base_filters &= date_filters
    
    # Obtener todos los sittings completados de una vez
    sittings = Sitting.objects.filter(base_filters).select_related(
        'user__student', 'quiz'
    ).prefetch_related('user__student')
    
    company_data = {}
    no_empresa_count = 0
    
    for sitting in sittings:
        try:
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
        except Exception as e:
            # Log del error para debugging
            print(f"Error procesando sitting {sitting.id} en distribución por empresa: {e}")
            continue
    
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


def get_gender_distribution_data_cached(date_filters=None):
    """Obtener distribución de certificados por género (sin cache individual)"""
    # Construir filtros base - Incluir todos los intentos completados
    base_filters = Q(
        quiz__course__isnull=False,
        complete=True
    )
    
    if date_filters:
        base_filters &= date_filters
    
    # Obtener todos los sittings completados de una vez
    sittings = Sitting.objects.filter(base_filters).select_related(
        'user', 'quiz'
    )
    
    gender_data = {'M': 0, 'F': 0}
    
    for sitting in sittings:
        try:
            if (sitting.user.gender and 
                sitting.user.gender.strip() and
                is_sitting_approved(sitting)):
                
                gender = sitting.user.gender
                if gender in gender_data:
                    gender_data[gender] += 1
        except Exception as e:
            # Log del error para debugging
            print(f"Error procesando sitting {sitting.id} en distribución por género: {e}")
            continue
    
    labels = ['Masculino', 'Femenino']
    data = [gender_data['M'], gender_data['F']]
    
    return {'labels': labels, 'data': data}

def get_gender_distribution_data():
    """Función original para compatibilidad"""
    return get_gender_distribution_data_cached()


def get_courses_data_cached(date_filters=None):
    """
    Obtener todos los cursos con certificados otorgados (sin cache individual)
    - Solo cuenta el intento final aprobado por usuario/curso
    - Calcula promedio en escala del 1 al 20
    - Respeta los filtros de fecha aplicados
    """
    # Construir filtros base - Incluir todos los intentos completados
    base_filters = Q(
        quiz__course__isnull=False,
        complete=True
    )
    
    if date_filters:
        base_filters &= date_filters
    
    # Obtener todos los sittings completados de una vez
    all_sittings = Sitting.objects.filter(base_filters).select_related(
        'course', 'course__program', 'quiz', 'user'
    )
    
    # Agrupar por usuario y curso para obtener solo el intento final aprobado
    user_course_approved = {}
    
    for sitting in all_sittings:
        try:
            if is_sitting_approved(sitting):
                user_course_key = (sitting.user.id, sitting.course.id)
                
                if user_course_key not in user_course_approved or sitting.end > user_course_approved[user_course_key].end:
                    user_course_approved[user_course_key] = sitting
        except Exception as e:
            # Log del error para debugging
            print(f"Error procesando sitting {sitting.id} en top courses: {e}")
            continue
    
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
    
    # Ordenar por cantidad de certificados (mayor a menor) y devolver todos
    return sorted(result, key=lambda x: x['count'], reverse=True)

def get_top_courses_data():
    """Función original para compatibilidad"""
    return get_courses_data_cached()


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
        try:
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
        except Exception as e:
            # Log del error para debugging
            print(f"Error procesando participant {participant.id} en calculate_course_stats: {e}")
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
            end__year=current_year,
            end__month=month
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
    """Obtener datos mensuales temporales - Solo certificados aprobados (OPTIMIZADO)"""
    current_year = timezone.now().year
    months = []
    data = []
    
    # Query única optimizada
    year_sittings = Sitting.objects.filter(
        quiz__course__isnull=False,
        end__year=current_year,
        complete=True
    ).filter(base_filters).select_related('quiz').only(
        'id', 'end', 'current_score', 'quiz__pass_mark'
    )
    
    # Agrupar por mes y contar aprobados
    monthly_counts = {}
    for sitting in year_sittings:
        # Verificar que tenga fecha de finalización y esté aprobado
        if sitting.end:
            # Calcular si está aprobado directamente
            is_approved = sitting.current_score >= sitting.quiz.pass_mark
            if is_approved:
                month = sitting.end.month
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
    """Obtener datos trimestrales temporales - Solo certificados aprobados (OPTIMIZADO)"""
    current_year = timezone.now().year
    quarters = ['Q1 (Ene-Mar)', 'Q2 (Abr-Jun)', 'Q3 (Jul-Sep)', 'Q4 (Oct-Dic)']
    data = []
    
    # Query única optimizada
    year_sittings = Sitting.objects.filter(
        quiz__course__isnull=False,
        end__year=current_year,
        complete=True
    ).filter(base_filters).select_related('quiz').only(
        'id', 'end', 'current_score', 'quiz__pass_mark'
    )
    
    # Agrupar por trimestre y contar aprobados
    quarterly_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    
    for sitting in year_sittings:
        # Verificar que tenga fecha de finalización y esté aprobado
        if sitting.end:
            # Calcular si está aprobado directamente
            is_approved = sitting.current_score >= sitting.quiz.pass_mark
            if is_approved:
                month = sitting.end.month
                quarter = ((month - 1) // 3) + 1
                quarterly_counts[quarter] += 1
    
    # Crear array ordenado
    for quarter in range(1, 5):
        data.append(quarterly_counts[quarter])
    
    return {'labels': quarters, 'data': data}


def get_yearly_temporal_data(base_filters):
    """Obtener datos anuales temporales - Solo certificados aprobados (OPTIMIZADO)"""
    years = list(range(2020, timezone.now().year + 1))
    data = []
    
    # Query única optimizada
    all_sittings = Sitting.objects.filter(
        quiz__course__isnull=False,
        end__year__in=years,
        complete=True
    ).filter(base_filters).select_related('quiz').only(
        'id', 'end', 'current_score', 'quiz__pass_mark'
    )
    
    # Agrupar por año y contar aprobados
    yearly_counts = {year: 0 for year in years}
    
    for sitting in all_sittings:
        # Verificar que tenga fecha de finalización y esté aprobado
        if sitting.end:
            # Calcular si está aprobado directamente
            is_approved = sitting.current_score >= sitting.quiz.pass_mark
            if is_approved:
                year = sitting.end.year
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
    """Obtener datos de comparación año tras año - Solo certificados aprobados (OPTIMIZADO)"""
    current_year = timezone.now().year
    years = list(range(current_year - 3, current_year + 1))
    data = []
    
    base_filters = date_filters & program_filters
    
    # Query única optimizada
    all_sittings = Sitting.objects.filter(
        quiz__course__isnull=False,
        end__year__in=years,
        complete=True
    ).filter(base_filters).select_related('quiz').only(
        'id', 'end', 'current_score', 'quiz__pass_mark'
    )
    
    # Agrupar por año y contar aprobados
    yearly_counts = {year: 0 for year in years}
    
    for sitting in all_sittings:
        # Verificar que tenga fecha de finalización y esté aprobado
        if sitting.end:
            # Calcular si está aprobado directamente
            is_approved = sitting.current_score >= sitting.quiz.pass_mark
            if is_approved:
                year = sitting.end.year
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
        complete=True
    ).filter(base_filters).select_related('quiz')
    
    # Agrupar por trimestre y contar aprobados
    quarterly_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    
    for sitting in all_sittings:
        # Verificar que tenga fecha de finalización y esté aprobado
        if sitting.end and is_sitting_approved(sitting):
            month = sitting.end.month
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
        date_filters &= Q(end__gte=date_from)  # ✅ Usar fecha de finalización
    if date_to:
        date_filters &= Q(end__lte=date_to)    # ✅ Usar fecha de finalización
    
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
    ).order_by('-end')  # ✅ Usar fecha de finalización
    
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
    ).order_by('-end')  # ✅ Usar fecha de finalización
    
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
    ).order_by('-end')  # ✅ Usar fecha de finalización
    
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
    ).order_by('-end')  # ✅ Usar fecha de finalización
    
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
    ).order_by('end')  # ✅ Usar fecha de finalización
    
    headers = [
        'Fecha', 'Participante', 'Curso', 'Programa', 'Puntuación', 
        'Estado', 'Código Certificado'
    ]
    
    data = []
    for sitting in sittings:
        data.append([
            sitting.end.strftime('%d/%m/%Y') if sitting.end else '-',  # ✅ Usar fecha de finalización
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
    """Limpiar todo el cache del dashboard de manera robusta"""
    try:
        cache.delete('certificates_dashboard')
        cache.delete('course_dashboard')
        print("✅ Cache del dashboard limpiado exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error limpiando cache: {e}")
        try:
            cache.clear()
            print("✅ Cache completo limpiado como fallback")
            return True
        except:
            print("❌ No se pudo limpiar el cache")
            return False


def invalidate_cache_for_sitting(sitting_id):
    """Invalidar cache cuando se actualiza un sitting de manera robusta"""
    try:
        # Limpiar cache principal del dashboard
        cache.delete('certificates_dashboard')
        cache.delete('course_dashboard')
        
        print(f"✅ Cache invalidado exitosamente para sitting {sitting_id}")
        return True
    except Exception as e:
        print(f"❌ Error invalidando cache para sitting {sitting_id}: {e}")
        # Fallback: limpiar todo el cache del dashboard
        try:
            clear_dashboard_cache()
            return True
        except:
            return False


def get_optimized_dashboard_data(date_filters, date_from, date_to):
    """
    Función optimizada que obtiene todos los datos del dashboard en una sola query
    manteniendo EXACTAMENTE la misma funcionalidad y lógica de las funciones actuales
    """
    from datetime import datetime
    current_year = timezone.now().year
    
    # 1. UNA SOLA QUERY para obtener todos los datos base
    base_sittings = Sitting.objects.filter(
        quiz__course__isnull=False,
        complete=True
    ).filter(date_filters).select_related(
        'quiz', 'course', 'course__program', 'user'
    ).prefetch_related(
        Prefetch('user__student', queryset=Student.objects.only('empresa'))
    )
    
    # 2. Procesar TODOS los datos en una sola iteración
    monthly_counts = {}
    program_counts = {}
    company_counts = {}
    gender_counts = {}
    user_course_approved = {}  # Para lógica de cursos
    
    # Contadores principales
    total_attempts = 0
    approved_certificates = 0
    failed_attempts = 0
    
    for sitting in base_sittings:
        total_attempts += 1
        
        try:
            # Usar EXACTAMENTE la misma función actual
            if is_sitting_approved(sitting):
                approved_certificates += 1
                
                # Procesar para mensual (misma lógica que get_monthly_certificates_data_cached)
                if sitting.end:
                    month = sitting.end.month
                    if month not in monthly_counts:
                        monthly_counts[month] = 0
                    monthly_counts[month] += 1
                
                # Procesar para programa (misma lógica que get_program_distribution_data_cached)
                if sitting.course.program:
                    program_title = sitting.course.program.title
                    program_counts[program_title] = program_counts.get(program_title, 0) + 1
                
                # Procesar para empresa (misma lógica que get_company_distribution_data_cached)
                if (hasattr(sitting.user, 'student') and 
                    sitting.user.student and 
                    sitting.user.student.empresa and 
                    sitting.user.student.empresa.strip()):
                    
                    empresa = sitting.user.student.empresa.strip()
                    company_counts[empresa] = company_counts.get(empresa, 0) + 1
                
                # Procesar para género (misma lógica que get_gender_distribution_data_cached)
                if (sitting.user.gender and 
                    sitting.user.gender.strip() and
                    sitting.user.gender in ['M', 'F']):
                    
                    gender = sitting.user.gender
                    gender_counts[gender] = gender_counts.get(gender, 0) + 1
                
                # Procesar para cursos (misma lógica que get_courses_data_cached)
                user_course_key = (sitting.user.id, sitting.course.id)
                if user_course_key not in user_course_approved or sitting.end > user_course_approved[user_course_key].end:
                    user_course_approved[user_course_key] = sitting
                    
            else:
                failed_attempts += 1
                
        except Exception as e:
            print(f"Error procesando sitting {sitting.id}: {e}")
            failed_attempts += 1
    
    # 3. Procesar datos mensuales (misma lógica que get_monthly_certificates_data_cached)
    months = []
    data = []
    
    # Determinar el rango de meses basado en las fechas proporcionadas
    if date_from and date_to:
        try:
            if isinstance(date_from, str):
                start_date = datetime.strptime(date_from, '%Y-%m-%d')
            else:
                start_date = date_from
                
            if isinstance(date_to, str):
                end_date = datetime.strptime(date_to, '%Y-%m-%d')
            else:
                end_date = date_to
            
            start_month = start_date.month
            start_year = start_date.year
            end_month = end_date.month
            end_year = end_date.year
            
            if start_year == end_year:
                month_range = range(start_month, end_month + 1)
            else:
                month_range = []
                for year in range(start_year, end_year + 1):
                    if year == start_year:
                        month_range.extend(range(start_month, 13))
                    elif year == end_year:
                        month_range.extend(range(1, end_month + 1))
                    else:
                        month_range.extend(range(1, 13))
                        
        except Exception as e:
            print(f"Error procesando fechas: {e}")
            month_range = range(1, 13)
    else:
        month_range = range(1, 13)
    
    # Crear array ordenado solo para los meses relevantes
    for month in month_range:
        if date_from and isinstance(date_from, str):
            try:
                year_for_month = datetime.strptime(date_from, '%Y-%m-%d').year
            except:
                year_for_month = current_year
        elif date_from and hasattr(date_from, 'year'):
            year_for_month = date_from.year
        else:
            year_for_month = current_year
            
        month_name = datetime(year_for_month, month, 1).strftime('%b')
        months.append(month_name)
        data.append(monthly_counts.get(month, 0))
    
    monthly_data = {'labels': months, 'data': data}
    
    # 4. Procesar datos de programa (misma lógica que get_program_distribution_data_cached)
    sorted_programs = sorted(program_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    program_data = {
        'labels': [p[0] for p in sorted_programs],
        'data': [p[1] for p in sorted_programs]
    }
    
    # 5. Procesar datos de empresa (misma lógica que get_company_distribution_data_cached)
    no_empresa_count = approved_certificates - sum(company_counts.values())
    if no_empresa_count > 0:
        company_counts['Sin Empresa'] = no_empresa_count
    
    sorted_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)
    
    if len(sorted_companies) <= 10:
        company_data = {
            'labels': [c[0] for c in sorted_companies],
            'data': [c[1] for c in sorted_companies]
        }
    else:
        top_companies = sorted_companies[:10]
        other_companies = sorted_companies[10:]
        other_total = sum(count for _, count in other_companies)
        
        labels = [c[0] for c in top_companies]
        data = [c[1] for c in top_companies]
        
        if other_total > 0:
            labels.append('Otras')
            data.append(other_total)
        
        company_data = {'labels': labels, 'data': data}
    
    # 6. Procesar datos de género (misma lógica que get_gender_distribution_data_cached)
    gender_data = {
        'labels': ['Masculino', 'Femenino'],
        'data': [gender_counts.get('M', 0), gender_counts.get('F', 0)]
    }
    
    # 7. Procesar datos de cursos (misma lógica que get_courses_data_cached)
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
    
    # Calcular estadísticas y ordenar (misma lógica)
    courses_result = []
    for (title, code, program), data in course_data.items():
        avg_score = data['total_score'] / data['total_certificates'] if data['total_certificates'] > 0 else 0
        
        courses_result.append({
            'course__title': title,
            'course__code': code,
            'course__program__title': program,
            'count': data['total_certificates'],
            'pass_rate': 100.0,
            'avg_score': avg_score
        })
    
    courses_data = sorted(courses_result, key=lambda x: x['count'], reverse=True)
    
    # 8. Retornar datos en el formato EXACTO que esperan las funciones actuales
    return {
        'total_attempts': total_attempts,
        'approved_certificates': approved_certificates,
        'failed_attempts': failed_attempts,
        'monthly_data': monthly_data,
        'program_data': program_data,
        'company_data': company_data,
        'gender_data': gender_data,
        'courses_data': courses_data
    }
