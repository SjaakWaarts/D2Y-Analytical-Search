import re
import json
from datetime import datetime
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import ListView
from django.views.decorators.csrf import requires_csrf_token
#from django.contrib.auth.models import User
import django.contrib.auth as auth
from django.contrib.auth import update_session_auth_hash
from django.core.mail import send_mail
 
from users_app.forms import LogMessageForm
from users_app.forms import RegisterForm, ProfileForm
from users_app.models import LogMessage

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

    return render(request, template, {'form': form})  
