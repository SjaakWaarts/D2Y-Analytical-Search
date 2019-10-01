from datetime import datetime, time
from django.shortcuts import render
import FMI.settings

# Create your views here.


def club_view(request):
    """Renders dhk page."""
    return render(
        request,
        'dhk_app/club.html',
        {'site' : FMI.settings.site, 'year':datetime.now().year}
    )


