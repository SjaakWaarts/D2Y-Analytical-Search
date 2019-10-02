from datetime import datetime, time
from django.shortcuts import render
import FMI.settings

# Create your views here.

def workshops_view(request):
    """Renders dhk page."""
    workshops = [
        {
            'title'     : "Bakken in de herfst voor de hele familie",
            'excempt'  : """Wat is er leuker en gezelliger dan op een herfstige dag
                             samen met je (klein)kind lekkere koekjes, taartjes en cakejes te bakken?
                             Deze workshop is voor jong en oud en staat in het teken van de herfst en decemberlekkers!""",
            'cook'      : "Lieke",
            'docent'    : "Lieke Waarts",
            'starttime' : "14:30",
            'endtime'   : "16:00",
            'dates'     : ["2019-11-20"],
            'cost'      : 25,
            'images'    : [{'location': 'data/dhk/workshops/Bakken in de herfst voor de hele familie.png'}],
            'instructions' : ["Meld je aan via de Deelnemers tab", "Instructies staan in de mail"],
            'reviews'   : [],
            'participants'  : []
         },
        {
            'title'     : "Culinair met seizoenen",
            'excempt'  : """Kooktechnieken en de klassieke keuken dienen als uitgangspunt voor de gerechten en menu’s in deze cursus.
                             Iedere bijeenkomst worden een of meerdere technieken toegepast in klassieke gerechten. 
                             bijv. het maken van een mousse of een bavarois en het maken van verschillende sauzen voor vlees of vis.
                             Ook aan het combineren van verschillende gerechten en het samenvoegen van verschillende gerechten 
                             tot een menu wordt aandacht besteed""",
            'cook'      : "Lieke",
            'docent'    : "Lieke Waarts",
            'starttime' : "9:30",
            'endtime'   : "12:00",
            'dates'     : ["2019-10-2","2019-10-30","2019-11-13","2019-11-21","2019-12-11","2020-1-8"],
            'cost'      : 155,
            'images'    : [{'location': 'data/dhk/workshops/Culinair met seizoenen.png'}],
            'instructions' : ["Meld je aan via de Deelnemers tab", "Instructies staan in de mail"],
            'reviews'   : [],
            'participants'  : [{'user' : "Sjaak", 'email' : "sjaak_waarts@hotmail.com", 'comment': "Ik kom graag"}]
         },
        ];
    
    #workshops_json = json.dumps(workshops)
    return render(
        request,
        'dhk_app/workshops.html',
        {'workshops': workshops, 'site' : FMI.settings.site, 'year':datetime.now().year}
    )
