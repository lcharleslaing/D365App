from django.urls import path
from . import views

app_name = 'dynamics_search'

urlpatterns = [
    path('', views.search_page, name='search'),
    path('api/', views.search_api, name='search_api'),
    path('suggestions/', views.search_suggestions, name='search_suggestions'),
    path('part/<int:part_id>/', views.part_detail, name='part_detail'),
    path('history/', views.search_history_api, name='search_history_api'),
    path('history/<int:history_id>/delete/', views.delete_search_history, name='delete_search_history'),
    path('history/clear-all/', views.clear_all_history, name='clear_all_history'),
]
