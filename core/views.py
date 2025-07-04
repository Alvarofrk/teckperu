from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from accounts.decorators import admin_required, lecturer_required
from accounts.models import User, Student
from .forms import SessionForm, SemesterForm, NewsAndEventsForm
from .models import NewsAndEvents, ActivityLog, Session, Semester


# ########################################################
# News & Events
# ########################################################
@login_required
def home_view(request):
    items = NewsAndEvents.objects.all().order_by("-updated_date")
    context = {
        "title": "News & Events",
        "items": items,
    }
    return render(request, "core/index.html", context)


def home_view_test(request):
    """Vista de prueba temporal sin login_required"""
    try:
        # Paso 1: Verificar que podemos importar el modelo
        from core.models import NewsAndEvents
        
        # Paso 2: Verificar que la tabla existe
        try:
            items = NewsAndEvents.objects.all().order_by("-updated_date")
            items_count = items.count()
        except Exception as db_error:
            return HttpResponse(f"Error en base de datos: {str(db_error)}", status=500)
        
        # Paso 3: Verificar que podemos crear el contexto
        try:
            context = {
                "title": "News & Events",
                "items": items,
            }
        except Exception as context_error:
            return HttpResponse(f"Error creando contexto: {str(context_error)}", status=500)
        
        # Paso 4: Verificar que podemos renderizar el template
        try:
            return render(request, "core/index.html", context)
        except Exception as template_error:
            return HttpResponse(f"Error en template: {str(template_error)}", status=500)
            
    except Exception as e:
        return HttpResponse(f"Error general en home_view: {str(e)}", status=500)


def home_view_simple(request):
    """Vista súper simple para diagnóstico"""
    return HttpResponse("¡Hola! La vista simple funciona correctamente.", status=200)


def home_view_basic(request):
    """Vista súper básica sin nada de Django"""
    try:
        return HttpResponse("Vista básica funciona", status=200)
    except Exception as e:
        return HttpResponse(f"Error en vista básica: {str(e)}", status=500)


def home_view_env_check(request):
    """Vista para verificar variables de entorno"""
    try:
        from decouple import config
        import os
        
        # Verificar variables críticas
        secret_key = config("SECRET_KEY", default="NO_DEFINIDA")
        debug = config("DEBUG", default="NO_DEFINIDA")
        allowed_hosts = config("ALLOWED_HOSTS", default="NO_DEFINIDA")
        
        # Verificar si las variables están vacías
        secret_key_status = "OK" if secret_key and secret_key != "NO_DEFINIDA" else "ERROR"
        debug_status = "OK" if debug != "NO_DEFINIDA" else "ERROR"
        allowed_hosts_status = "OK" if allowed_hosts and allowed_hosts != "NO_DEFINIDA" else "ERROR"
        
        response = f"""
        <h1>Verificación de Variables de Entorno</h1>
        <p><strong>SECRET_KEY:</strong> {secret_key_status} - {secret_key[:10] if secret_key and secret_key != "NO_DEFINIDA" else "NO DEFINIDA"}...</p>
        <p><strong>DEBUG:</strong> {debug_status} - {debug}</p>
        <p><strong>ALLOWED_HOSTS:</strong> {allowed_hosts_status} - {allowed_hosts}</p>
        <p><strong>DATABASE_NAME:</strong> {config('DATABASE_NAME', default='NO_DEFINIDA')}</p>
        <p><strong>DATABASE_HOST:</strong> {config('DATABASE_HOST', default='NO_DEFINIDA')}</p>
        """
        
        return HttpResponse(response, status=200)
    except Exception as e:
        return HttpResponse(f"Error verificando variables: {str(e)}", status=500)


def home_view_ssl_check(request):
    """Vista para verificar configuración SSL/HTTPS"""
    try:
        from django.conf import settings
        
        # Verificar configuración de seguridad
        debug = getattr(settings, 'DEBUG', None)
        secure_ssl_redirect = getattr(settings, 'SECURE_SSL_REDIRECT', None)
        secure_proxy_ssl_header = getattr(settings, 'SECURE_PROXY_SSL_HEADER', None)
        
        # Verificar headers de la request
        is_secure = request.is_secure()
        x_forwarded_proto = request.META.get('HTTP_X_FORWARDED_PROTO', 'NO')
        x_forwarded_ssl = request.META.get('HTTP_X_FORWARDED_SSL', 'NO')
        
        response = f"""
        <h1>Verificación de Configuración SSL/HTTPS</h1>
        <h2>Configuración Django:</h2>
        <p><strong>DEBUG:</strong> {debug}</p>
        <p><strong>SECURE_SSL_REDIRECT:</strong> {secure_ssl_redirect}</p>
        <p><strong>SECURE_PROXY_SSL_HEADER:</strong> {secure_proxy_ssl_header}</p>
        
        <h2>Headers de la Request:</h2>
        <p><strong>request.is_secure():</strong> {is_secure}</p>
        <p><strong>HTTP_X_FORWARDED_PROTO:</strong> {x_forwarded_proto}</p>
        <p><strong>HTTP_X_FORWARDED_SSL:</strong> {x_forwarded_ssl}</p>
        
        <h2>URL de la Request:</h2>
        <p><strong>request.build_absolute_uri():</strong> {request.build_absolute_uri()}</p>
        """
        
        return HttpResponse(response, status=200)
    except Exception as e:
        return HttpResponse(f"Error verificando SSL: {str(e)}", status=500)


def home_view_debug(request):
    """Vista de diagnóstico paso a paso"""
    try:
        # Paso 1: Probar solo el template base sin includes
        return render(request, "base.html", {})
    except Exception as e:
        return HttpResponse(f"Error en base.html: {str(e)}", status=500)


def home_view_debug_simple(request):
    """Vista de diagnóstico sin javascript-catalog"""
    try:
        # Crear un template simple sin la línea problemática
        template_content = """
{% load static %}
{% load i18n %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test</title>
</head>
<body>
    <h1>Test sin javascript-catalog</h1>
    <p>Si ves esto, el problema está en la línea del javascript-catalog</p>
</body>
</html>
"""
        from django.template import Template, Context
        template = Template(template_content)
        context = Context({})
        return HttpResponse(template.render(context), status=200)
    except Exception as e:
        return HttpResponse(f"Error en template simple: {str(e)}", status=500)


@login_required
@admin_required
def dashboard_view(request):
    logs = ActivityLog.objects.all().order_by("-created_at")[:10]
    gender_count = Student.get_gender_count()
    context = {
        "student_count": User.objects.get_student_count(),
        "lecturer_count": User.objects.get_lecturer_count(),
        "superuser_count": User.objects.get_superuser_count(),
        "males_count": gender_count["M"],
        "females_count": gender_count["F"],
        "logs": logs,
    }
    return render(request, "core/dashboard.html", context)


@login_required
def post_add(request):
    if request.method == "POST":
        form = NewsAndEventsForm(request.POST)
        title = form.cleaned_data.get("title", "Post") if form.is_valid() else None
        if form.is_valid():
            form.save()
            messages.success(request, f"{title} has been uploaded.")
            return redirect("home")
        messages.error(request, "Please correct the error(s) below.")
    else:
        form = NewsAndEventsForm()
    return render(request, "core/post_add.html", {"title": "Add Post", "form": form})


@login_required
@lecturer_required
def edit_post(request, pk):
    instance = get_object_or_404(NewsAndEvents, pk=pk)
    if request.method == "POST":
        form = NewsAndEventsForm(request.POST, instance=instance)
        title = form.cleaned_data.get("title", "Post") if form.is_valid() else None
        if form.is_valid():
            form.save()
            messages.success(request, f"{title} has been updated.")
            return redirect("home")
        messages.error(request, "Please correct the error(s) below.")
    else:
        form = NewsAndEventsForm(instance=instance)
    return render(request, "core/post_add.html", {"title": "Edit Post", "form": form})


@login_required
@lecturer_required
def delete_post(request, pk):
    post = get_object_or_404(NewsAndEvents, pk=pk)
    post_title = post.title
    post.delete()
    messages.success(request, f"{post_title} has been deleted.")
    return redirect("home")


# ########################################################
# Session
# ########################################################
@login_required
@lecturer_required
def session_list_view(request):
    """Show list of all sessions"""
    sessions = Session.objects.all().order_by("-is_current_session", "-session")
    return render(request, "core/session_list.html", {"sessions": sessions})


@login_required
@lecturer_required
def session_add_view(request):
    """Add a new session"""
    if request.method == "POST":
        form = SessionForm(request.POST)
        if form.is_valid():
            if form.cleaned_data.get("is_current_session"):
                unset_current_session()
            form.save()
            messages.success(request, "Session added successfully.")
            return redirect("session_list")
    else:
        form = SessionForm()
    return render(request, "core/session_update.html", {"form": form})


@login_required
@lecturer_required
def session_update_view(request, pk):
    session = get_object_or_404(Session, pk=pk)
    if request.method == "POST":
        form = SessionForm(request.POST, instance=session)
        if form.is_valid():
            if form.cleaned_data.get("is_current_session"):
                unset_current_session()
            form.save()
            messages.success(request, "Session updated successfully.")
            return redirect("session_list")
    else:
        form = SessionForm(instance=session)
    return render(request, "core/session_update.html", {"form": form})


@login_required
@lecturer_required
def session_delete_view(request, pk):
    session = get_object_or_404(Session, pk=pk)
    if session.is_current_session:
        messages.error(request, "You cannot delete the current session.")
    else:
        session.delete()
        messages.success(request, "Session successfully deleted.")
    return redirect("session_list")


def unset_current_session():
    """Unset current session"""
    current_session = Session.objects.filter(is_current_session=True).first()
    if current_session:
        current_session.is_current_session = False
        current_session.save()


# ########################################################
# Semester
# ########################################################
@login_required
@lecturer_required
def semester_list_view(request):
    semesters = Semester.objects.all().order_by("-is_current_semester", "-semester")
    return render(request, "core/semester_list.html", {"semesters": semesters})


@login_required
@lecturer_required
def semester_add_view(request):
    if request.method == "POST":
        form = SemesterForm(request.POST)
        if form.is_valid():
            if form.cleaned_data.get("is_current_semester"):
                unset_current_semester()
                unset_current_session()
            form.save()
            messages.success(request, "Semester added successfully.")
            return redirect("semester_list")
    else:
        form = SemesterForm()
    return render(request, "core/semester_update.html", {"form": form})


@login_required
@lecturer_required
def semester_update_view(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    if request.method == "POST":
        form = SemesterForm(request.POST, instance=semester)
        if form.is_valid():
            if form.cleaned_data.get("is_current_semester"):
                unset_current_semester()
                unset_current_session()
            form.save()
            messages.success(request, "Semester updated successfully!")
            return redirect("semester_list")
    else:
        form = SemesterForm(instance=semester)
    return render(request, "core/semester_update.html", {"form": form})


@login_required
@lecturer_required
def semester_delete_view(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    if semester.is_current_semester:
        messages.error(request, "You cannot delete the current semester.")
    else:
        semester.delete()
        messages.success(request, "Semester successfully deleted.")
    return redirect("semester_list")


def unset_current_semester():
    """Unset current semester"""
    current_semester = Semester.objects.filter(is_current_semester=True).first()
    if current_semester:
        current_semester.is_current_semester = False
        current_semester.save()


def home_view_static_check(request):
    """Vista para verificar problemas de staticfiles"""
    try:
        from django.conf import settings
        from django.contrib.staticfiles.finders import find
        from django.contrib.staticfiles.storage import staticfiles_storage
        
        # Verificar archivos problemáticos
        dashboard_js = find('js/dashboard.js')
        brand_svg = find('img/brand.svg')
        login_css = find('css/login-modern.css')
        
        # Verificar si están en staticfiles
        dashboard_js_static = staticfiles_storage.exists('js/dashboard.js')
        brand_svg_static = staticfiles_storage.exists('img/brand.svg')
        login_css_static = staticfiles_storage.exists('css/login-modern.css')
        
        response = f"""
        <h1>Verificación de Staticfiles</h1>
        <h2>Archivos problemáticos:</h2>
        <p><strong>js/dashboard.js:</strong></p>
        <ul>
            <li>Encontrado por find(): {dashboard_js}</li>
            <li>Existe en staticfiles: {dashboard_js_static}</li>
        </ul>
        
        <p><strong>img/brand.svg:</strong></p>
        <ul>
            <li>Encontrado por find(): {brand_svg}</li>
            <li>Existe en staticfiles: {brand_svg_static}</li>
        </ul>
        
        <p><strong>css/login-modern.css:</strong></p>
        <ul>
            <li>Encontrado por find(): {login_css}</li>
            <li>Existe en staticfiles: {login_css_static}</li>
        </ul>
        
        <h2>Configuración:</h2>
        <p><strong>STATIC_ROOT:</strong> {settings.STATIC_ROOT}</p>
        <p><strong>STATIC_URL:</strong> {settings.STATIC_URL}</p>
        <p><strong>STATICFILES_STORAGE:</strong> {settings.STATICFILES_STORAGE}</p>
        """
        
        return HttpResponse(response, status=200)
    except Exception as e:
        return HttpResponse(f"Error verificando staticfiles: {str(e)}", status=500)


def home_view_minimal(request):
    """Vista súper mínima sin HttpResponse"""
    try:
        from django.http import HttpResponse
        return HttpResponse("Vista mínima funciona", status=200)
    except Exception as e:
        return f"Error en vista mínima: {str(e)}"


def home_view_raw(request):
    """Vista raw sin Django"""
    try:
        return "Vista raw funciona"
    except Exception as e:
        return f"Error en vista raw: {str(e)}"
