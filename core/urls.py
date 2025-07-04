from django.urls import path

from .views import (
    home_view,
    home_view_test,
    home_view_simple,
    home_view_debug,
    home_view_debug_simple,
    post_add,
    edit_post,
    delete_post,
    session_list_view,
    session_add_view,
    session_update_view,
    session_delete_view,
    semester_list_view,
    semester_add_view,
    semester_update_view,
    semester_delete_view,
    dashboard_view,
)


urlpatterns = [
    # Accounts url
    path("", home_view_simple, name="home"),  # Temporal: vista súper simple
    path("test/", home_view_test, name="home_test"),  # Vista con diagnóstico
    path("debug/", home_view_debug, name="home_debug"),  # Vista de debug
    path("debug2/", home_view_debug_simple, name="home_debug_simple"),  # Vista de debug simple
    path("home_secure/", home_view, name="home_secure"),  # Original con login_required
    path("add_item/", post_add, name="add_item"),
    path("item/<int:pk>/edit/", edit_post, name="edit_post"),
    path("item/<int:pk>/delete/", delete_post, name="delete_post"),
    path("session/", session_list_view, name="session_list"),
    path("session/add/", session_add_view, name="session_add"),
    path("session/<int:pk>/edit/", session_update_view, name="session_update"),
    path("session/<int:pk>/delete/", session_delete_view, name="session_delete"),
    path("semester/", semester_list_view, name="semester_list"),
    path("semester/add/", semester_add_view, name="semester_add"),
    path("semester/<int:pk>/edit/", semester_update_view, name="semester_update"),
    path("semester/<int:pk>/delete/", semester_delete_view, name="semester_delete"),
    path("dashboard/", dashboard_view, name="dashboard"),
]
