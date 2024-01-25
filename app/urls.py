from django.urls import path, include

from app import views

urlpatterns = [
    path('', views.index, name='index'),
    path('searches', views.searches, name='searches-list'),
    path('searches/new', views.new_search, name='search-new'),
    path('searches/<int:search_id>', views.edit_search, name='search-edit'),
    path('updates/feed', views.CustomFeed(), name='updates-feed'),
    path('station/<slug:beacon_name>', views.station, name='station'),
    path('updates_partial', views.updates_partial, name='updates_partial'),
    path('', include('plausible_proxy.urls')),
]
