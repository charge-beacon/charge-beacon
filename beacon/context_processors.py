from beacon.models import Search


def searches(request):
    if request.user.is_authenticated:
        limit = 5
        search_count = Search.objects.filter(user=request.user).count()
        return {
            'searches': Search.objects.filter(user=request.user).order_by('-created')[:limit],
            'searches_count': search_count,
            'has_more_searches': search_count > limit
        }
    return {}
