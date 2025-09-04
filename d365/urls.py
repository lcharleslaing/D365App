from django.urls import path
from . import views

urlpatterns = [
    path('', views.d365_home, name='d365_home'),
    path('generate-all/', views.generate_all, name='d365_generate_all'),
    path('generate-selected/', views.generate_selected, name='d365_generate_selected'),
    path('save-selection/', views.save_selection, name='d365_save_selection'),
    path('generate/heater/', views.generate_heater, name='d365_generate_heater'),
    path('generate/tank/', views.generate_tank, name='d365_generate_tank'),
    path('generate/pump/', views.generate_pump, name='d365_generate_pump'),
    path('excel-preview/', views.excel_preview, name='d365_excel_preview'),
    path('delete-job/<int:job_id>/', views.delete_job, name='d365_delete_job'),
    path('save-job/', views.save_job, name='d365_save_job'),
    path('load-job/<int:job_id>/', views.load_job_by_id, name='d365_load_job_by_id'),
    path('load-job-number/<str:job_number>/', views.load_job_by_number, name='d365_load_job_by_number'),
    path('jobs/', views.jobs_list, name='d365_jobs_list'),
    path('print/<str:job_number>/', views.print_job, name='d365_print_job'),
]


