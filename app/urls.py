from django.urls import path, include
from app import views

urlpatterns = [
    path('', views.index, name='index'),
    path('updates/feed', views.CustomFeed(), name='updates-feed'),
    path('station/<slug:beacon_name>', views.station, name='station'),
    path('updates_partial', views.updates_partial, name='updates_partial'),
    path('', include('plausible_proxy.urls')),
]
