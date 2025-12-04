from django import forms
from django.core.exceptions import ValidationError
from accounts.models import User
from .models import Program, Course, CourseAllocation, Upload, UploadVideo

class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update({"class": "form-control"})
        self.fields["summary"].widget.attrs.update({"class": "form-control"})


class CourseAddForm(forms.ModelForm):
    class Meta:
        model = Course
        # Excluir campos que se establecerán automáticamente
        exclude = ["credit", "level", "year", "semester", "slug", "is_elective", "is_active", "last_cert_code"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update({"class": "form-control"})
        self.fields["code"].widget.attrs.update({"class": "form-control"})
        self.fields["summary"].widget.attrs.update({"class": "form-control", "rows": "4"})
        self.fields["program"].widget.attrs.update({"class": "form-control"})
    
    def save(self, commit=True):
        """Sobrescribir save para establecer valores por defecto automáticamente"""
        from django.conf import settings
        course = super().save(commit=False)
        # Establecer valores por defecto
        course.credit = 1
        course.level = settings.BACHELOR_DEGREE
        course.year = 1
        course.semester = settings.FIRST
        if commit:
            course.save()
        return course


class CourseEditForm(forms.ModelForm):
    """
    Formulario simplificado para editar cursos con solo los campos relevantes
    """
    class Meta:
        model = Course
        fields = ["title", "code", "summary", "program"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Ingresa el título del curso"
        })
        self.fields["code"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Ej: 0001, 0002, etc."
        })
        self.fields["summary"].widget.attrs.update({
            "class": "form-control",
            "rows": "4",
            "placeholder": "Describe brevemente el contenido del curso"
        })
        self.fields["program"].widget.attrs.update({"class": "form-control"})


class CourseAllocationForm(forms.ModelForm):
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all().order_by("level"),
        widget=forms.CheckboxSelectMultiple(
            attrs={"class": "browser-default checkbox"}
        ),
        required=True,
    )
    lecturer = forms.ModelChoiceField(
        queryset=User.objects.filter(is_lecturer=True),
        widget=forms.Select(attrs={"class": "browser-default custom-select"}),
        label="lecturer",
    )

    class Meta:
        model = CourseAllocation
        fields = ["lecturer", "courses"]

    def __init__(self, *args, **kwargs):
        super(CourseAllocationForm, self).__init__(*args, **kwargs)
        self.fields["lecturer"].queryset = User.objects.filter(is_lecturer=True)


class EditCourseAllocationForm(forms.ModelForm):
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all().order_by("level"),
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )
    lecturer = forms.ModelChoiceField(
        queryset=User.objects.filter(is_lecturer=True),
        widget=forms.Select(attrs={"class": "browser-default custom-select"}),
        label="lecturer",
    )

    class Meta:
        model = CourseAllocation
        fields = ["lecturer", "courses"]

    def __init__(self, *args, **kwargs):
        super(EditCourseAllocationForm, self).__init__(*args, **kwargs)
        self.fields["lecturer"].queryset = User.objects.filter(is_lecturer=True)


# Formulario para subir archivos a un curso específico
class UploadFormFile(forms.ModelForm):
    class Meta:
        model = Upload
        fields = (
            "title",
            "file",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update({"class": "form-control"})
        self.fields["file"].widget.attrs.update({"class": "form-control"})



# Formulario para agregar videos usando URLs de Vimeo
class UploadFormVideo(forms.ModelForm):
    class Meta:
        model = UploadVideo
        fields = (
            "title",
            "vimeo_url",
            "summary",  # Incluimos 'summary' si es necesario
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update({"class": "form-control"})
        self.fields["vimeo_url"].widget.attrs.update({"class": "form-control"})
        self.fields["summary"].widget.attrs.update({"class": "form-control"})

    def clean_vimeo_url(self):
        url = self.cleaned_data.get('vimeo_url')
        if 'vimeo.com' not in url:
            raise ValidationError('Por favor, ingresa una URL válida de Vimeo.')
        return url