from django import forms
from django.forms.widgets import RadioSelect, Textarea, CheckboxInput
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _
from django.forms.models import inlineformset_factory
from .models import Question, Quiz, MCQuestion, Choice


class QuestionForm(forms.Form):
    def __init__(self, question, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        choice_list = [x for x in question.get_choices_list()]
        self.fields["answers"] = forms.ChoiceField(
            choices=choice_list, widget=RadioSelect
        )


class AnexoForm(forms.Form):
    fecha_ingreso = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}), label="Fecha de Ingreso")
    ocupacion = forms.CharField(max_length=100, label="Ocupación")
    area_trabajo = forms.CharField(max_length=100, label="Área de Trabajo")
    empresa = forms.CharField(max_length=100, label="E.C.M./CONEXAS")
    distrito = forms.CharField(max_length=100, label="Distrito")
    provincia = forms.CharField(max_length=100, label="Provincia")

class EssayForm(forms.Form):
    def __init__(self, question, *args, **kwargs):
        super(EssayForm, self).__init__(*args, **kwargs)
        self.fields["answers"] = forms.CharField(
            widget=Textarea(attrs={"style": "width:100%"})
        )


class QuizAddForm(forms.ModelForm):
    class Meta:
        model = Quiz
        exclude = []

    questions = forms.ModelMultipleChoiceField(
        queryset=Question.objects.all().select_subclasses(),
        required=False,
        label=_("Preguntas"),
        widget=FilteredSelectMultiple(verbose_name=_("Preguntas"), is_stacked=False),
    )

    def __init__(self, *args, **kwargs):
        super(QuizAddForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["questions"].initial = (
                self.instance.question_set.all().select_subclasses()
            )
        
        # Configurar checkboxes para que funcionen correctamente
        checkbox_fields = ['random_order', 'answers_at_end', 'exam_paper', 'single_attempt', 'draft']
        for field_name in checkbox_fields:
            if field_name in self.fields:
                self.fields[field_name].widget = CheckboxInput(attrs={
                    'class': 'form-check-input',
                })
                self.fields[field_name].required = False

    def save(self, commit=True):
        quiz = super(QuizAddForm, self).save(commit=False)
        quiz.save()
        quiz.question_set.set(self.cleaned_data["questions"])
        self.save_m2m()
        return quiz


class MCQuestionForm(forms.ModelForm):
    class Meta:
        model = MCQuestion
        exclude = ()


class MCQuestionFormSet(forms.BaseInlineFormSet):
    def clean(self):
        """
        Custom validation for the formset to ensure:
        1. At least two choices are provided and not marked for deletion.
        2. At least one of the choices is marked as correct.
        """
        super().clean()

        # Collect non-deleted forms
        valid_forms = [
            form for form in self.forms if not form.cleaned_data.get("DELETE", True)
        ]

        valid_choices = [
            "choice_text" in form.cleaned_data.keys() for form in valid_forms
        ]
        if not all(valid_choices):
            raise forms.ValidationError(_("Debes agregar un nombre de opción válido."))

        # If all forms are deleted, raise a validation error
        if len(valid_forms) < 2:
            raise forms.ValidationError(_("Debes proporcionar al menos dos opciones."))

        # Check if at least one of the valid forms is marked as correct
        correct_choices = [
            form.cleaned_data.get("correct", False) for form in valid_forms
        ]

        if not any(correct_choices):
            raise forms.ValidationError(_("Debes marcar una opción como correcta."))

        if correct_choices.count(True) > 1:
            raise forms.ValidationError(_("Solo una opción debe estar marcada como correcta."))


MCQuestionFormSet = inlineformset_factory(
    MCQuestion,
    Choice,
    form=MCQuestionForm,
    formset=MCQuestionFormSet,
    fields=["choice_text", "correct"],
    can_delete=True,
    extra=5,
)
