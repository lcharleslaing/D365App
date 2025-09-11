from django.urls import path
from . import views

app_name = 'dynamics_search'

urlpatterns = [
    path('', views.search_page, name='search'),
    path('api/', views.search_api, name='search_api'),
    path('suggestions/', views.search_suggestions, name='search_suggestions'),
    path('part/<int:part_id>/', views.part_detail, name='part_detail'),
]
