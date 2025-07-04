from django.urls import path
from .views import *

urlpatterns = [
    path('', index, name='index'),
    path('testing', tests_view, name='testing'),
    path('reports', reports, name='reports'),
    path('reports/analysis', analysis_view, name='analysis'),
    path('reports/summary', summary_view, name='summary'),
    path('reports/protocols', protocols_view, name='protocols'),
    path('reports/protocols/<int:test_id>', test_protocols_view, name='test_protocols'),
    path('reports/protocols/<int:test_id>/<int:result_id>', worker_protocol, name='worker_protocol'),
    path('testing/<int:test_id>', test_detailed, name='test'),
    path('testing/<int:test_id>/members', test_members_view, name='test_members'),
    path('testing/<int:test_id>/start', start_test, name='start_test'),
    path('testing/<int:test_id>/practice', practice_start, name='practice_start'),
    path('testing/<int:test_id>/practice/<int:question_id>', practice_question_view, name='practice_question'),
    path('testing/<int:test_id>/edit', test_edit_view, name='edit_test'),
    path('testing/<int:test_id>/delete', delete_test_view, name='delete_test'),
    path('testing/<int:test_id>/<int:question_id>', question_view, name='question'),
    path('testing/<int:test_id>/<int:question_id>/edit', question_edit_view, name='edit_question'),
    path('testing/<int:test_id>/<int:question_id>/delete', delete_question, name='delete_question'),
    path('testing/<int:test_id>/new_question', new_question_view, name='new_question'),
    path('testing/<int:test_id>/results', test_attempts, name='test_attempts'),
    path('testing/<int:test_id>/results/<int:result_id>', test_result, name='test_result'),
    path('testing/files/<int:file_id>/delete', delete_file, name='delete_file'),
    path('testing/new', new_test_view, name='new_test'),
    path('login', user_login, name='login'),
    path('logout', user_logout, name='logout'),
    path('download_pdf/<int:test_id>/<int:result_id>', form_protocol_file, name='download_pdf'),
]

# [0] -> [-1]
