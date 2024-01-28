from django.contrib.gis.db import models
from django.db import IntegrityError
from django.db.models.query import Q
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth import get_user_model


class SearchQuerySet(models.QuerySet):
    def publish(self, update, idempotency_key) -> (int, list['Search']):
        query = Q(user__is_active=True)
        # identify searches that specify the EV networks or have no EV networks defined
        query &= Q(ev_networks__contains=[update.station.ev_network]) | Q(ev_networks__len=0)

        # identify searches that specify the plug types or have no plug types defined
        if len(update.station.ev_connector_types):
            plug_type_q = Q(plug_types__contains=[update.station.ev_connector_types[0]])
            for plug_type in update.station.ev_connector_types[1:]:
                plug_type_q |= Q(plug_types__contains=[plug_type])
            query &= plug_type_q | Q(plug_types__len=0)

        # identify searches that are within the station's area or have no areas defined
        query &= Q(within__geom__contains=update.station.point) | Q(within=None)

        # if the station is not a DC fast charger, only notify searches that do not specify DC fast chargers
        if update.station.ev_dc_fast_num == 0:
            query &= Q(dc_fast=False)
        # if the update is not new, only notify searches that do not specify new stations
        if not update.is_creation:
            query &= Q(only_new=False)

        searches = self.filter(query)
        errors = []
        n_success = 0

        for search in searches:
            try:
                SearchResult.objects.create(
                    search=search,
                    update=update,
                    idempotency_key=idempotency_key
                )
                n_success += 1
            except IntegrityError:
                errors.append(search)

        return n_success, errors


class Search(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    ev_networks = ArrayField(models.CharField(max_length=255), blank=True)
    plug_types = ArrayField(models.CharField(max_length=255), blank=True)
    dc_fast = models.BooleanField(default=False)
    only_new = models.BooleanField(default=False)
    within = models.ManyToManyField('Area', related_name='within', blank=True)
    daily_email = models.BooleanField(default=False)
    weekly_email = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)
    last_notified_id = models.DateTimeField(null=True, blank=True)

    objects = SearchQuerySet.as_manager()

    class Meta:
        verbose_name_plural = 'Searches'

    def __str__(self):
        return self.name


class SearchResult(models.Model):
    search = models.ForeignKey(Search, on_delete=models.CASCADE)
    update = models.ForeignKey('app.Update', on_delete=models.CASCADE)
    idempotency_key = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('search', 'update', 'idempotency_key')

    def __str__(self):
        return str(self.created)


class AreaType(models.TextChoices):
    CITY = 'c', 'City'
    STATE = 's', 'State'
    ZIP = 'z', 'Zip'
    COUNTRY = 'y', 'Country'


class Area(models.Model):
    """
    An area is a geographic region that can be used to filter search results.
    """
    name = models.CharField(max_length=255, db_index=True)
    place_id = models.SlugField(max_length=255)
    area_type = models.CharField(max_length=1, choices=AreaType.choices)
    belongs_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    geom = models.MultiPolygonField(srid=4326, null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ZipCodeTabulationArea(models.Model):
    """
    Zip Code Tabulation Areas (ZCTAs) are generalized areal representations of United States Postal Service (USPS)
    ZIP Code service areas. This model is used to sync with the US Census Bureau's ZCTA shapefile.
    """
    zip_code = models.CharField(max_length=5, primary_key=True)
    area = models.OneToOneField(
        Area, on_delete=models.CASCADE, related_name='us_zip', null=True, blank=True, editable=False
    )
    geom = models.MultiPolygonField(srid=4326)

    def __str__(self):
        return self.zip_code


class USState(models.Model):
    """
    US states and territories. This model is used to sync with the US Census Bureau's state shapefile.
    """
    name = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=2)
    area = models.OneToOneField(
        Area, on_delete=models.CASCADE, related_name='us_state', null=True, blank=True, editable=False
    )
    geom = models.MultiPolygonField(srid=4326)

    def __str__(self):
        return self.name


class CanadianProvince(models.Model):
    """
    Canadian provinces and territories. This model is used to sync with the Canadian Census Program's
    province shapefile.
    """
    name = models.CharField(max_length=255)
    name_fr = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=10)
    abbreviation_fr = models.CharField(max_length=10)
    area = models.OneToOneField(
        Area, on_delete=models.CASCADE, related_name='ca_state', null=True, blank=True, editable=False
    )
    geom = models.MultiPolygonField(srid=4326)

    def __str__(self):
        return self.name


class ForwardStatisticalArea(models.Model):
    """
    Forward sortation areas (FSAs) are the first three characters of a Canadian postal code.
    This model is used to sync with the Canadian Census Program's FSA shapefile.
    """
    code = models.CharField(max_length=3)
    area = models.OneToOneField(
        Area, on_delete=models.CASCADE, related_name='ca_zip', null=True, blank=True, editable=False
    )
    geom = models.MultiPolygonField(srid=4326)

    def __str__(self):
        return self.code
