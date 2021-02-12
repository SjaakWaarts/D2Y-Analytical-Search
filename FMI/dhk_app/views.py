from datetime import datetime, time
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
import FMI.settings

# Create your views here.


def dhk_view(request):
    """Renders dhk page."""
    return render(
        request,
        'dhk_app/dhk.html',
        {'site' : FMI.settings.site, 'year':datetime.now().year}
    )
