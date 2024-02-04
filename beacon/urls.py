from django.urls import path, re_path
from beacon import views

urlpatterns = [
    path('area_autocomplete', views.area_autocomplete, name='area-autocomplete'),
    re_path(f'map.*', views.map, name='map'),
]
