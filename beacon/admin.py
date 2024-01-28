from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from beacon.models import (
    Search, SearchResult, Area, ZipCodeTabulationArea, USState, CanadianProvince, ForwardStatisticalArea
)


@admin.register(Search)
class SearchAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created')
    search_fields = ('name', 'user__username', 'user__email')
    readonly_fields = ('user', 'within')


@admin.register(SearchResult)
class SearchResultAdmin(admin.ModelAdmin):
    list_display = ('search', 'update', 'created')
    search_fields = ('search__name', 'search__user__username', 'search__user__email')
    readonly_fields = ('search', 'update')


@admin.register(Area)
class AreaAdmin(GISModelAdmin):
    list_display = ('name', 'place_id', 'area_type')
    search_fields = ('name', 'place_id', 'belongs_to__name')
    list_filter = ('area_type',)
    readonly_fields = ('belongs_to',)


@admin.register(ZipCodeTabulationArea)
class ZCTAAdmin(GISModelAdmin):
    list_display = ('zip_code', 'area')
    search_fields = ('zip_code',)
    readonly_fields = ('area',)


@admin.register(USState)
class USStateAdmin(GISModelAdmin):
    list_display = ('name', 'abbreviation')
    readonly_fields = ('area',)


@admin.register(CanadianProvince)
class CanadianProvinceAdmin(GISModelAdmin):
    list_display = ('name', 'abbreviation')
    readonly_fields = ('area',)


@admin.register(ForwardStatisticalArea)
class ForwardStatisticalAreaAdmin(GISModelAdmin):
    list_display = ('code', 'area')
    search_fields = ('code',)
    readonly_fields = ('area',)
