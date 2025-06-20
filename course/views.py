from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django_filters.views import FilterView
import os

from accounts.decorators import lecturer_required, student_required
from accounts.models import Student
from core.models import Semester
from course.filters import CourseAllocationFilter, ProgramFilter
from course.forms import (
    CourseAddForm,
    CourseAllocationForm,
    EditCourseAllocationForm,
    ProgramForm,
    UploadFormFile,  
    UploadFormVideo,
    CourseEditForm,
)
from course.models import (
    Course,
    CourseAllocation,
    Program,
    Upload,
    UploadVideo,
)
from result.models import TakenCourse
from quiz.models import Quiz

from django.http import HttpResponse
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch 
from reportlab.pdfgen import canvas
from django.utils import timezone
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Spacer
from datetime import datetime
from babel.dates import format_date
# ########################################################
# Program Views
# ########################################################


@method_decorator([login_required, lecturer_required], name="dispatch")
class ProgramFilterView(FilterView):
    filterset_class = ProgramFilter
    template_name = "course/program_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Programas"
        return context

def wrap_text(text, max_length):
    """ Función para envolver el texto de manera que no se corten palabras """
    words = text.split(' ')
    lines = []
    current_line = []

    for word in words:
        # Si el largo de la línea actual + la nueva palabra excede el límite, crear una nueva línea
        if sum(len(w) for w in current_line) + len(word) + len(current_line) > max_length:
            lines.append(' '.join(current_line))
            current_line = [word]
        else:
            current_line.append(word)

    if current_line:
        lines.append(' '.join(current_line))

    return lines
@login_required
@lecturer_required
def program_add(request):
    if request.method == "POST":
        form = ProgramForm(request.POST)
        if form.is_valid():
            program = form.save()
            messages.success(request, f"{program.title} program has been created.")
            return redirect("programs")
        messages.error(request, "Correct the error(s) below.")
    else:
        form = ProgramForm()
    return render(
        request, "course/program_add.html", {"title": "Add Program", "form": form}
    )


@login_required
def program_detail(request, pk):
    program = get_object_or_404(Program, pk=pk)
    courses = Course.objects.filter(program_id=pk).order_by("-year")
    credits = courses.aggregate(total_credits=Sum("credit"))
    
    # Agregar rutas de imágenes a cada curso
    for course in courses:
        course.image_path = get_course_image_path(course.code)
    
    paginator = Paginator(courses, 10)
    page = request.GET.get("page")
    courses = paginator.get_page(page)
    return render(
        request,
        "course/program_single.html",
        {
            "title": program.title,
            "program": program,
            "courses": courses,
            "credits": credits,
        },
    )


@login_required
@lecturer_required
def program_edit(request, pk):
    program = get_object_or_404(Program, pk=pk)
    if request.method == "POST":
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            program = form.save()
            messages.success(request, f"{program.title} program has been updated.")
            return redirect("programs")
        messages.error(request, "Correct the error(s) below.")
    else:
        form = ProgramForm(instance=program)
    return render(
        request, "course/program_add.html", {"title": "Edit Program", "form": form}
    )


@login_required
@lecturer_required
def program_delete(request, pk):
    program = get_object_or_404(Program, pk=pk)
    title = program.title
    program.delete()
    messages.success(request, f"Program {title} has been deleted.")
    return redirect("programs")


# ########################################################
# Course Views
# ########################################################


@login_required
def course_single(request, slug):
    course = get_object_or_404(Course, slug=slug)
    files = Upload.objects.filter(course__slug=slug)
    videos = UploadVideo.objects.filter(course__slug=slug)
    lecturers = CourseAllocation.objects.filter(courses__pk=course.id)
    return render(
        request,
        "course/course_single.html",
        {
            "title": course.title,
            "course": course,
            "files": files,
            "videos": videos,
            "lecturers": lecturers,
            "media_url": settings.MEDIA_URL,
        },
    )



@login_required
def course_video_navigation(request, slug, video_id=None):
    course = get_object_or_404(Course, slug=slug)
    videos = UploadVideo.objects.filter(course=course).order_by("timestamp")
    documents = Upload.objects.filter(course=course).order_by("upload_time")

    # Encuentra el video actual o selecciona el primero si no hay un video_id
    if video_id:
        current_video = get_object_or_404(videos, id=video_id)
    else:
        current_video = videos.first()

    # Obtener el índice del video actual y los videos anterior y siguiente
    current_index = list(videos).index(current_video)
    previous_video = videos[current_index - 1] if current_index > 0 else None
    next_video = videos[current_index + 1] if current_index < len(videos) - 1 else None

    # Verificar si es el último video
    is_last_video = current_index == len(videos) - 1

    # Obtener el documento correspondiente al video actual, si existe
    current_document = documents[current_index] if current_index < len(documents) else None

    return render(
        request,
        "course/video_navigation.html",
        {
            "course": course,
            "current_video": current_video,
            "previous_video": previous_video,
            "next_video": next_video,
            "is_last_video": is_last_video,
            "current_document": current_document,  # Documento relacionado con el video
        },
    )


@login_required
@lecturer_required
def course_add(request, pk):
    program = get_object_or_404(Program, pk=pk)
    if request.method == "POST":
        form = CourseAddForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(
                request, f"{course.title} ({course.code}) has been created."
            )
            return redirect("program_detail", pk=program.pk)
        messages.error(request, "Correct the error(s) below.")
    else:
        form = CourseAddForm(initial={"program": program})
    return render(
        request,
        "course/course_add.html",
        {"title": "Add Course", "form": form, "program": program},
    )


@login_required
@lecturer_required
def course_edit(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == "POST":
        form = CourseEditForm(request.POST, instance=course)
        if form.is_valid():
            course = form.save()
            messages.success(
                request, f"{course.title} ({course.code}) ha sido actualizado."
            )
            return redirect("program_detail", pk=course.program.pk)
        messages.error(request, "Corrige los errores a continuación.")
    else:
        form = CourseEditForm(instance=course)
    return render(
        request, "course/course_add.html", {"title": "Editar Curso", "form": form, "course": course}
    )


@login_required
@lecturer_required
def course_delete(request, slug):
    course = get_object_or_404(Course, slug=slug)
    title = course.title
    program_id = course.program.id
    course.delete()
    messages.success(request, f"Course {title} has been deleted.")
    return redirect("program_detail", pk=program_id)


# ########################################################
# Course Allocation Views
# ########################################################


@method_decorator([login_required, lecturer_required], name="dispatch")
class CourseAllocationFormView(CreateView):
    form_class = CourseAllocationForm
    template_name = "course/course_allocation_form.html"

    def form_valid(self, form):
        lecturer = form.cleaned_data["lecturer"]
        selected_courses = form.cleaned_data["courses"]
        allocation, created = CourseAllocation.objects.get_or_create(lecturer=lecturer)
        allocation.courses.set(selected_courses)
        messages.success(
            self.request, f"Courses allocated to {lecturer.get_full_name} successfully."
        )
        return redirect("course_allocation_view")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Assign Course"
        return context


@method_decorator([login_required, lecturer_required], name="dispatch")
class CourseAllocationFilterView(FilterView):
    filterset_class = CourseAllocationFilter
    template_name = "course/course_allocation_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Course Allocations"
        return context


@login_required
@lecturer_required
def edit_allocated_course(request, pk):
    allocation = get_object_or_404(CourseAllocation, pk=pk)
    if request.method == "POST":
        form = EditCourseAllocationForm(request.POST, instance=allocation)
        if form.is_valid():
            form.save()
            messages.success(request, "Course allocation has been updated.")
            return redirect("course_allocation_view")
        messages.error(request, "Correct the error(s) below.")
    else:
        form = EditCourseAllocationForm(instance=allocation)
    return render(
        request,
        "course/course_allocation_form.html",
        {"title": "Edit Course Allocation", "form": form},
    )


@login_required
@lecturer_required
def deallocate_course(request, pk):
    allocation = get_object_or_404(CourseAllocation, pk=pk)
    allocation.delete()
    messages.success(request, "Successfully deallocated courses.")
    return redirect("course_allocation_view")


# ########################################################
# File Upload Views
# ########################################################


@login_required
@lecturer_required
def handle_file_upload(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == "POST":
        form = UploadFormFile(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save(commit=False)
            upload.course = course
            upload.save()
            messages.success(request, f"{upload.title} has been uploaded.")
            return redirect("course_detail", slug=slug)
        messages.error(request, "Correct the error(s) below.")
    else:
        form = UploadFormFile()
    return render(
        request,
        "upload/upload_file_form.html",
        {"title": "File Upload", "form": form, "course": course},
    )


@login_required
@lecturer_required
def handle_file_edit(request, slug, file_id):
    course = get_object_or_404(Course, slug=slug)
    upload = get_object_or_404(Upload, pk=file_id)
    if request.method == "POST":
        form = UploadFormFile(request.POST, request.FILES, instance=upload)
        if form.is_valid():
            upload = form.save()
            messages.success(request, f"{upload.title} has been updated.")
            return redirect("course_detail", slug=slug)
        messages.error(request, "Correct the error(s) below.")
    else:
        form = UploadFormFile(instance=upload)
    return render(
        request,
        "upload/upload_file_form.html",
        {"title": "Edit File", "form": form, "course": course},
    )


@login_required
@lecturer_required
def handle_file_delete(request, slug, file_id):
    upload = get_object_or_404(Upload, pk=file_id)
    title = upload.title
    upload.delete()
    messages.success(request, f"{title} has been deleted.")
    return redirect("course_detail", slug=slug)


# ########################################################
# Video Upload Views
# ########################################################


@login_required
@lecturer_required
def handle_video_upload(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == "POST":
        form = UploadFormVideo(request.POST)
        if form.is_valid():
            video = form.save(commit=False)
            video.course = course
            video.save()
            messages.success(request, f"{video.title} ha sido agregado.")
            return redirect("course_detail", slug=slug)
        else:
            messages.error(request, "Corrige los errores a continuación.")
    else:
        form = UploadFormVideo()
    return render(
        request,
        "upload/upload_video_form.html",
        {"title": "Agregar Video", "form": form, "course": course},
    )


@login_required
def handle_video_single(request, slug, video_slug):
    course = get_object_or_404(Course, slug=slug)
    video = get_object_or_404(UploadVideo, slug=video_slug)
    return render(
        request,
        "upload/video_single.html",
        {"video": video, "course": course},
    )


@login_required
@lecturer_required
def handle_video_edit(request, slug, video_slug):
    course = get_object_or_404(Course, slug=slug)
    video = get_object_or_404(UploadVideo, slug=video_slug)
    if request.method == "POST":
        form = UploadFormVideo(request.POST, instance=video)
        if form.is_valid():
            video = form.save()
            messages.success(request, f"{video.title} ha sido actualizado.")
            return redirect("course_detail", slug=slug)
        else:
            messages.error(request, "Corrige los errores a continuación.")
    else:
        form = UploadFormVideo(instance=video)
    return render(
        request,
        "upload/upload_video_form.html",
        {"title": "Editar Video", "form": form, "course": course},
    )

@login_required
@lecturer_required
def handle_video_delete(request, slug, video_slug):
    video = get_object_or_404(UploadVideo, slug=video_slug)
    title = video.title
    video.delete()
    messages.success(request, f"{title} has been deleted.")
    return redirect("course_detail", slug=slug)


# ########################################################
# Course Registration Views
# ########################################################


@login_required
@student_required
def course_registration(request):
    if request.method == "POST":
        student = Student.objects.get(student__pk=request.user.id)
        ids = ()
        data = request.POST.copy()
        data.pop("csrfmiddlewaretoken", None)  # remove csrf_token
        for key in data.keys():
            ids = ids + (str(key),)
        for s in range(0, len(ids)):
            course = Course.objects.get(pk=ids[s])
            obj = TakenCourse.objects.create(student=student, course=course)
            obj.save()
        messages.success(request, "Courses registered successfully!")
        return redirect("course_registration")
    else:
        current_semester = Semester.objects.filter(is_current_semester=True).first()
        if not current_semester:
            messages.error(request, "No active semester found.")
            return render(request, "course/course_registration.html")

        # student = Student.objects.get(student__pk=request.user.id)
        student = get_object_or_404(Student, student__id=request.user.id)
        taken_courses = TakenCourse.objects.filter(student__student__id=request.user.id)
        t = ()
        for i in taken_courses:
            t += (i.course.pk,)

        courses = (
            Course.objects.filter(
                program__pk=student.program.id,
                level=student.level,
                semester=current_semester,
            )
            .exclude(id__in=t)
            .order_by("year")
        )
        all_courses = Course.objects.filter(
            level=student.level, program__pk=student.program.id
        )

        no_course_is_registered = False  # Check if no course is registered
        all_courses_are_registered = False

        registered_courses = Course.objects.filter(level=student.level).filter(id__in=t)
        if (
            registered_courses.count() == 0
        ):  # Check if number of registered courses is 0
            no_course_is_registered = True

        if registered_courses.count() == all_courses.count():
            all_courses_are_registered = True

        total_first_semester_credit = 0
        total_sec_semester_credit = 0
        total_registered_credit = 0
        for i in courses:
            if i.semester == "First":
                total_first_semester_credit += int(i.credit)
            if i.semester == "Second":
                total_sec_semester_credit += int(i.credit)
        for i in registered_courses:
            total_registered_credit += int(i.credit)
        context = {
            "is_calender_on": True,
            "all_courses_are_registered": all_courses_are_registered,
            "no_course_is_registered": no_course_is_registered,
            "current_semester": current_semester,
            "courses": courses,
            "total_first_semester_credit": total_first_semester_credit,
            "total_sec_semester_credit": total_sec_semester_credit,
            "registered_courses": registered_courses,
            "total_registered_credit": total_registered_credit,
            "student": student,
        }
        return render(request, "course/course_registration.html", context)


@login_required
@student_required
def course_drop(request):
    if request.method == "POST":
        student = get_object_or_404(Student, student__pk=request.user.id)
        course_ids = request.POST.getlist("course_ids")
        print("course_ids", course_ids)
        for course_id in course_ids:
            course = get_object_or_404(Course, pk=course_id)
            TakenCourse.objects.filter(student=student, course=course).delete()
        messages.success(request, "Courses dropped successfully!")
        return redirect("course_registration")

@login_required
@student_required
def download_courses_pdf(request):
    # Obtener los cursos que el estudiante tiene registrados
    student = get_object_or_404(Student, student__pk=request.user.id)
    taken_courses = TakenCourse.objects.filter(student=student)
    
    # Crear una respuesta HTTP con tipo de contenido PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_cursos_estudiante.pdf"'

    # Crear un documento PDF
    doc = SimpleDocTemplate(response, pagesize=letter)
    
    # Lista de elementos para el documento
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1  # Centrado
    title_style.fontSize = 24
    title_style.spaceAfter = 30
    title_style.textColor = colors.HexColor('#BA6022')  # Color naranja de la plataforma
    
    subtitle_style = styles['Heading2']
    subtitle_style.fontSize = 14
    subtitle_style.spaceAfter = 20
    subtitle_style.textColor = colors.HexColor('#333333')
    
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    normal_style.spaceAfter = 12
    
    # Título principal
    title = Paragraph("REPORTE DE CURSOS REGISTRADOS", title_style)
    elements.append(title)
    
    # Información del estudiante
    student_name = f"{student.student.first_name} {student.student.last_name}"
    student_info = f"<b>Estudiante:</b> {student_name}"
    student_paragraph = Paragraph(student_info, subtitle_style)
    elements.append(student_paragraph)
    
    # Información del programa
    if student.program:
        program_info = f"<b>Programa:</b> {student.program.title}"
        program_paragraph = Paragraph(program_info, normal_style)
        elements.append(program_paragraph)
    
    # Fecha del reporte
    current_date = format_date(datetime.now(), format='d \'de\' MMMM \'de\' y', locale='es_ES')
    date_info = f"<b>Fecha de generación:</b> {current_date}"
    date_paragraph = Paragraph(date_info, normal_style)
    elements.append(date_paragraph)
    
    # Espacio
    elements.append(Spacer(1, 30))
    
    # Tabla de cursos
    if taken_courses.exists():
        # Encabezados de la tabla
        headers = ["Código", "Nombre del Curso"]
        
        # Datos de los cursos
        data = []
        for taken_course in taken_courses:
            course = taken_course.course
            
            data.append([
                course.code,
                course.title
            ])
        
        # Crear la tabla
        course_table = Table([headers] + data, colWidths=[1.5*inch, 4.5*inch])
        
        # Estilo de la tabla
        course_table.setStyle(TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#BA6022')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 15),
            ('TOPPADDING', (0, 0), (-1, 0), 15),
            
            # Datos
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Código centrado
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Nombre del curso alineado a la izquierda
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#BA6022')),
            
            # Colores alternados para las filas
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        
        elements.append(course_table)
    else:
        # Mensaje si no hay cursos
        no_courses = Paragraph("No tienes cursos registrados actualmente.", normal_style)
        elements.append(no_courses)
    
    # Espacio
    elements.append(Spacer(1, 30))
    
    # Pie de página
    footer_text = "Este reporte fue generado automáticamente por el Sistema de Gestión de Aprendizaje TeckPeru"
    footer_style = styles['Normal']
    footer_style.fontSize = 8
    footer_style.textColor = colors.grey
    footer_style.alignment = 1  # Centrado
    footer = Paragraph(footer_text, footer_style)
    elements.append(footer)
    
    # Construir el documento PDF
    doc.build(elements)
    
    return response
# ########################################################
# User Course List View
# ########################################################


@login_required
def user_course_list(request):
    """
    Shows a list of courses the current user is registered for.
    """
    if request.user.is_student:
        student = get_object_or_404(Student, student__id=request.user.id)
        courses = TakenCourse.objects.select_related('course').filter(student=student)
        
        # Inyecta la ruta de la imagen en cada objeto del curso
        for taken_course in courses:
            taken_course.course.image_path = get_course_image_path(taken_course.course.code)
        
        # Calcular estadísticas
        total_courses = courses.count()
        active_courses = courses.filter(course__is_active=True).count()
        
        # Calcular progreso (simulado por ahora)
        courses_in_progress = 0
        completed_courses = 0
        
        # Paginación
        paginator = Paginator(courses, 9)  # 9 cursos por página
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            "student": student,
            "taken_courses": page_obj,
            "total_courses": total_courses,
            "active_courses": active_courses,
            "courses_in_progress": courses_in_progress,
            "completed_courses": completed_courses,
        }
        return render(request, "course/user_course_list.html", context)

    if request.user.is_lecturer:
        # Obtener cursos asignados al instructor
        courses = Course.objects.filter(
            id__in=CourseAllocation.objects.select_related('lecturer').filter(lecturer=request.user).values_list(
                "courses__id", flat=True
            )
        ).order_by('title')
        
        # Calcular estadísticas
        total_courses = courses.count()
        active_courses = courses.filter(is_active=True).count()
        
        # Contar estudiantes totales
        total_students = 0
        for course in courses:
            student_count = TakenCourse.objects.filter(course=course).count()
            total_students += student_count
        
        # Contar cuestionarios totales
        total_quizzes = Quiz.objects.filter(course__in=courses).count()
        
        # Contar materiales totales (archivos y videos)
        total_materials = 0
        for course in courses:
            total_materials += course.upload_set.count() + course.uploadvideo_set.count()
        
        # Inyecta la ruta de la imagen en cada objeto del curso
        for course in courses:
            course.image_path = get_course_image_path(course.code)
        
        # Paginación
        paginator = Paginator(courses, 9)  # 9 cursos por página (3x3 grid)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            "courses": page_obj,
            "total_courses": total_courses,
            "active_courses": active_courses,
            "total_students": total_students,
            "total_quizzes": total_quizzes,
            "total_materials": total_materials,
        }
        return render(request, "course/user_course_list.html", context)

    # For other users
    return render(request, "course/user_course_list.html")

def get_course_image_path(course_code):
    """
    Función helper para obtener la ruta de la imagen de un curso
    basado en su código (ej: '0001' -> 'curso001.png', '0002' -> 'curso002.png')
    """
    try:
        code_str = str(course_code).strip()
        # Solo tomar los últimos 3 dígitos para armar el nombre de la imagen
        if len(code_str) >= 3 and code_str[-3:].isdigit():
            img_number = code_str[-3:]
            image_path = f'/static/img/curso{img_number}.png'
            return image_path
        return '/static/img/course-default.png'
    except Exception:
        return '/static/img/course-default.png'
