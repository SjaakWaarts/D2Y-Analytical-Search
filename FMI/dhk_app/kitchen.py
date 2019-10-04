from datetime import datetime, time
from django.shortcuts import render
import FMI.settings

# Create your views here.


def kitchen_view(request):
    """Renders dhk page."""
    return render(
        request,
        'dhk_app/kitchen.html',
        {'site' : FMI.settings.site, 'year':datetime.now().year, 'layout_template': 'dhk_app/dhk_layout.html'}
    )
