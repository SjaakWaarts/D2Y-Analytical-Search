from datetime import datetime, time
from django.shortcuts import render
import FMI.settings

# Create your views here.


def stuurhuis_view(request):
    """Renders dhk page."""
    return render(
        request,
        'dhk_app/stuurhuis.html',
        {'site' : FMI.settings.site, 'year':datetime.now().year}
    )

def workshops_view(request):
    """Renders dhk page."""
    return render(
        request,
        'dhk_app/workshops.html',
        {'site' : FMI.settings.site, 'year':datetime.now().year}
    )
