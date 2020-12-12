import re
import json
from datetime import datetime
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.views.generic import ListView
from django.views.decorators.csrf import requires_csrf_token
#from django.contrib.auth.models import User
import django.contrib.auth as auth
from django.contrib.auth import update_session_auth_hash
from django.core.mail import send_mail
from django.conf import settings
from FMI.settings import SAML_FOLDER 
from users_app.forms import LogMessageForm
from users_app.forms import RegisterForm, ProfileForm
from users_app.models import LogMessage

from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from onelogin.saml2.utils import OneLogin_Saml2_Utils

# Create your views here.

from django.contrib.auth import get_user_model
User = get_user_model()

class HomeListView(ListView):
    """Renders the home page, with a list of all messages."""
    model = LogMessage

    def get_context_data(self, **kwargs):
        context = super(HomeListView, self).get_context_data(**kwargs)
        return context

def log_message(request):
    form = LogMessageForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            message = form.save(commit=False)
            message.log_date = datetime.now()
            message.save()
            return redirect("home")
    else:
        return render(request, "users_app/log_message.html", {"form": form})


def register(request):
    # if this is a POST request we need to process the form data
    template = 'registration/register.html'
    
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = RegisterForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            if User.objects.filter(username=form.cleaned_data['username']).exists():
                return render(request, template, {
                    'form': form, 
                    'error_message': 'Username already exists.'
                })
            elif User.objects.filter(email=form.cleaned_data['email']).exists():
                return render(request, template, {
                    'form': form, 
                    'error_message': 'Email already exists.'
                })
            elif form.cleaned_data['password'] != form.cleaned_data['password_repeat']:
                return render(request, template, {
                    'form': form, 
                    'error_message': 'Passwords do not match.'
                })
            else:
                # Create the user: 
                user = User.objects.create_user(
                    form.cleaned_data['username'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    email=form.cleaned_data['email'],
                    street=form.cleaned_data['street'],
                    housenumber=form.cleaned_data['housenumber'],
                    zip=form.cleaned_data['zip'],
                    city=form.cleaned_data['city'],
                    country=form.cleaned_data['country'],
                    password=form.cleaned_data['password']
                )
                user.phone_number = form.cleaned_data['phone_number']
                user.date_of_birth = form.cleaned_data['date_of_birth']  
                user.save()
                
                # Login the user
                auth.login(request, user)
                
                # redirect to accounts page:
                return HttpResponseRedirect(reverse('home'))
                #return redirect('/accounts/register_complete')

   # No post data availabe, let's just show the page.
    else:
        if request.user.is_authenticated:
            return redirect("users_app/profile")
        else:
            form = RegisterForm()

    return render(request, template, {'form': form})

def login(request):
    if request.method == 'POST':
        json_data = json.loads(request.body)
        username = json_data.get('username', None)
        password = json_data.get('password', None)
        if "@" in username:
            users = User.objects.filter(email=username)
        else:
            users = User.objects.filter(username=username)
        if len(users) > 0:
            user = users[0]
            username = user.username
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            is_authenticated = True
            next = reverse('dhk:home')
            #return HttpResponseRedirect(reverse('dhk:home'))
        else:
            is_authenticated = False
            next = ""
        context = {
            'is_authenticated' : is_authenticated,
            'next' : next
            }
        return HttpResponse(json.dumps(context), content_type='application/json')
    else:
        template = 'registration/register.html'
        form = RegisterForm()
        return render(request, template, {'form': form})

def logout(request):
    response = auth.logout(request)
    context = {
        'is_authenticated' : False,
        'next' : ""
        }
    return HttpResponse(json.dumps(context), content_type='application/json')


@requires_csrf_token
def unlock(request):
    # set breakpoint AFTER reading the request.body. The debugger will otherwise already consume the stream!
    #json_data = json.loads(request.body)
    #username = json_data.get('username', None)
    username = request.POST['username']
    if "@" in username:
        users = User.objects.filter(email=username)
    else:
        users = User.objects.filter(username=username)
    if len(users) > 0:
        user = users[0]
        send_mail('Reset Password', 'Password reset naar "0000"', 'info@deheerlijkekeuken.nl', [user.email], fail_silently=True)
    context = {
        'username' : username
        }
    return HttpResponse(json.dumps(context), content_type='application/json')


def registrer_complete(request):
    return render(request, 'registration/register_complete.html')

def profile(request):
    # if this is a POST request we need to process the form data
    template = 'registration/profile.html'
    
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = ProfileForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            if form.cleaned_data['password'] != form.cleaned_data['password_repeat']:
                return render(request, template, {
                    'form': form, 
                    'error_message': 'Passwords do not match.'
                })
            else:
                # Modify the user:
                user = User.objects.get(username=form.cleaned_data['username'])
                user.email = form.cleaned_data['email']
                if len(form.cleaned_data['password']) > 0:
                    user.set_password(form.cleaned_data['password'])
                #user.password = form.cleaned_data['password'] # Needs to be crypted
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                user.street = form.cleaned_data['street']
                user.housenumber = form.cleaned_data['housenumber']
                user.zip = form.cleaned_data['zip']
                user.city = form.cleaned_data['city']
                user.country = form.cleaned_data['country']
                user.phone_number = form.cleaned_data['phone_number']
                user.date_of_birth = form.cleaned_data['date_of_birth']                
                user.save()               
                # Login the user
                # auth.login(request, user)
                update_session_auth_hash(request, user)  # Important!
                
                # redirect to accounts page:
                return HttpResponseRedirect(reverse('home'))

   # No post data availabe, let's just show the page.
    else:
        if request.user.is_authenticated:
            initial = {
                'username'      : request.user.username,
                'first_name'    : request.user.first_name,
                'last_name'     : request.user.last_name,          
                'email'         : request.user.email,
                'street'        : request.user.street,
                'housenumber'   : request.user.housenumber,
                'zip'           : request.user.zip, 
                'city'          : request.user.city,
                'country'       : request.user.country,
                'phone_number'  : request.user.phone_number,             
                'is_active'     : request.user.is_active,
                'is_admin'      : request.user.is_admin,
                'date_of_birth' : request.user.date_of_birth, 
                'date_joined'   : request.user.date_joined,
                'last_login'    : request.user.last_login,
            }
            form = ProfileForm(initial=initial)
        else:
            return redirect("users_app/register")

    return render(request, template, {'form': form})  

def init_saml_auth(req):
    auth = OneLogin_Saml2_Auth(req, custom_base_path=settings.SAML_FOLDER)
    return auth

def prepare_django_request(request):
    # If server is behind proxys or balancers use the HTTP_X_FORWARDED fields
    result = {
        'https': 'on' if request.is_secure() else 'off',
        'http_host': request.META['HTTP_HOST'],
        'script_name': request.META['PATH_INFO'],
        'server_port': request.META['SERVER_PORT'],
        'get_data': request.GET.copy(),
        # Uncomment if using ADFS as IdP, https://github.com/onelogin/python-saml/pull/144
        # 'lowercase_urlencoding': True,
        'post_data': request.POST.copy()
    }
    return result

def saml_index(request):
    req = prepare_django_request(request)
    auth = init_saml_auth(req)
    errors = []
    error_reason = None
    not_auth_warn = False
    success_slo = False
    attributes = False
    paint_logout = False

    if 'sso' in req['get_data']:
        return HttpResponseRedirect(auth.login())
        # If AuthNRequest ID need to be stored in order to later validate it, do instead
        # sso_built_url = auth.login()
        # request.session['AuthNRequestID'] = auth.get_last_request_id()
        # return HttpResponseRedirect(sso_built_url)
    elif 'sso2' in req['get_data']:
        return_to = OneLogin_Saml2_Utils.get_self_url(req) + reverse('attrs')
        return HttpResponseRedirect(auth.login(return_to))
    elif 'slo' in req['get_data']:
        name_id = session_index = name_id_format = name_id_nq = name_id_spnq = None
        if 'samlNameId' in request.session:
            name_id = request.session['samlNameId']
        if 'samlSessionIndex' in request.session:
            session_index = request.session['samlSessionIndex']
        if 'samlNameIdFormat' in request.session:
            name_id_format = request.session['samlNameIdFormat']
        if 'samlNameIdNameQualifier' in request.session:
            name_id_nq = request.session['samlNameIdNameQualifier']
        if 'samlNameIdSPNameQualifier' in request.session:
            name_id_spnq = request.session['samlNameIdSPNameQualifier']

        return HttpResponseRedirect(auth.logout(name_id=name_id, session_index=session_index, nq=name_id_nq, name_id_format=name_id_format, spnq=name_id_spnq))
        # If LogoutRequest ID need to be stored in order to later validate it, do instead
        # slo_built_url = auth.logout(name_id=name_id, session_index=session_index)
        # request.session['LogoutRequestID'] = auth.get_last_request_id()
        # return HttpResponseRedirect(slo_built_url)
    elif 'acs' in req['get_data']:
        request_id = None
        if 'AuthNRequestID' in request.session:
            request_id = request.session['AuthNRequestID']

        auth.process_response(request_id=request_id)
        errors = auth.get_errors()
        not_auth_warn = not auth.is_authenticated()

        if not errors:
            if 'AuthNRequestID' in request.session:
                del request.session['AuthNRequestID']
            request.session['samlUserdata'] = auth.get_attributes()
            request.session['samlNameId'] = auth.get_nameid()
            request.session['samlNameIdFormat'] = auth.get_nameid_format()
            request.session['samlNameIdNameQualifier'] = auth.get_nameid_nq()
            request.session['samlNameIdSPNameQualifier'] = auth.get_nameid_spnq()
            request.session['samlSessionIndex'] = auth.get_session_index()
            if 'RelayState' in req['post_data'] and OneLogin_Saml2_Utils.get_self_url(req) != req['post_data']['RelayState']:
                return HttpResponseRedirect(auth.redirect_to(req['post_data']['RelayState']))
        elif auth.get_settings().is_debug_active():
                error_reason = auth.get_last_error_reason()
    elif 'sls' in req['get_data']:
        request_id = None
        if 'LogoutRequestID' in request.session:
            request_id = request.session['LogoutRequestID']
        dscb = lambda: request.session.flush()
        url = auth.process_slo(request_id=request_id, delete_session_cb=dscb)
        errors = auth.get_errors()
        if len(errors) == 0:
            if url is not None:
                return HttpResponseRedirect(url)
            else:
                success_slo = True
        elif auth.get_settings().is_debug_active():
            error_reason = auth.get_last_error_reason()

    if 'samlUserdata' in request.session:
        paint_logout = True
        if len(request.session['samlUserdata']) > 0:
            attributes = request.session['samlUserdata'].items()

    return render(request, 'index.html', {'errors': errors, 'error_reason': error_reason, 'not_auth_warn': not_auth_warn, 'success_slo': success_slo,
                                          'attributes': attributes, 'paint_logout': paint_logout})


def saml_attrs(request):
    paint_logout = False
    attributes = False

    if 'samlUserdata' in request.session:
        paint_logout = True
        if len(request.session['samlUserdata']) > 0:
            attributes = request.session['samlUserdata'].items()
    return render(request, 'attrs.html',
                  {'paint_logout': paint_logout,
                   'attributes': attributes})


def saml_metadata(request):
    # req = prepare_django_request(request)
    # auth = init_saml_auth(req)
    # saml_settings = auth.get_settings()
    saml_settings = OneLogin_Saml2_Settings(settings=None, custom_base_path=settings.SAML_FOLDER, sp_validation_only=True)
    metadata = saml_settings.get_sp_metadata()
    errors = saml_settings.validate_metadata(metadata)

    if len(errors) == 0:
        resp = HttpResponse(content=metadata, content_type='text/xml')
    else:
        resp = HttpResponseServerError(content=', '.join(errors))
    return resp
