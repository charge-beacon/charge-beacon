from django.urls import re_path, path, include

from app import views, geojson_views

urlpatterns = [
    path('', views.index, name='index'),
    path('searches', views.searches, name='searches-list'),
    path('searches/new', views.new_search, name='search-new'),
    path('searches/<int:search_id>', views.edit_search, name='search-edit'),
    path('updates/feed', views.CustomFeed(), name='updates-feed'),
    path('geojson/stations', geojson_views.stations_in_bounds, name='stations_in_bounds'),
    re_path(r'station/(?P<beacon_name>[\w_-]+)\.(?P<fmt>json)', views.station, name='station'),
    re_path(r'station/(?P<beacon_name>[\w_-]+)', views.station, name='station', kwargs={'fmt': 'html'}),
    path('updates_partial', views.updates_partial, name='updates_partial'),
    path('', include('plausible_proxy.urls')),
]
