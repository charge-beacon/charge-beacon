from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth import get_user_model


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

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Searches'


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
