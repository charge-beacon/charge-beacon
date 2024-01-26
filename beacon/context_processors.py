from beacon.models import Search

search_limit = 5


def searches(request):
    ret = {}
    if request.user.is_authenticated:
        search_count = Search.objects.filter(user=request.user).count()
        ret = {
            'searches': Search.objects.filter(user=request.user).order_by('-created')[:search_limit],
            'searches_count': search_count,
            'has_more_searches': search_count > search_limit
        }
    return ret
