from django.urls import path
from beacon import views

urlpatterns = [
    path('area_autocomplete', views.area_autocomplete, name='area-autocomplete'),
]
