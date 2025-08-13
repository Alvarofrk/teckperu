from django import template

register = template.Library()


@register.inclusion_tag("quiz/correct_answer.html", takes_context=True)
def correct_answer_for_all(context, question):
    """
    processes the correct answer based on a given question object
    if the answer is incorrect, informs the user
    """
    answers = question.get_choices()
    incorrect_list = context.get("incorrect_questions", [])
    if question.id in incorrect_list:
        user_was_incorrect = True
    else:
        user_was_incorrect = False

    return {"previous": {"answers": answers}, "user_was_incorrect": user_was_incorrect}


@register.filter
def answer_choice_to_string(question, answer):
    return question.answer_choice_to_string(answer)


@register.filter
def percent_to_grade_20(percent):
    """Convertir porcentaje a nota en escala del 1 al 20"""
    try:
        grade = (float(percent) / 100) * 20
        return round(grade, 1)
    except (ValueError, TypeError):
        return 0.0
