import re
from datetime import datetime
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import ListView
#from django.contrib.auth.models import User
import django.contrib.auth as auth

from users_app.forms import LogMessageForm
from users_app.forms import RegisterForm
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
                    form.cleaned_data['email'], 
                    #form.cleaned_data['password'], Needs to be crypted
                    form.cleaned_data['email'],
                    form.cleaned_data['password'],
                    form.cleaned_data['first_name'],
                    form.cleaned_data['last_name'],
                    form.cleaned_data['street'],
                    form.cleaned_data['housenumber'],
                    form.cleaned_data['zip'],
                    form.cleaned_data['city'],
                    form.cleaned_data['country']                    
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

def registrer_complete(request):
    return render_to_response('registration/register_complete.html')

def profile(request):
    # if this is a POST request we need to process the form data
    template = 'registration/profile.html'
    
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = RegisterForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            if form.cleaned_data['password'] != form.cleaned_data['password_repeat']:
                return render(request, template, {
                    'form': form, 
                    'error_message': 'Passwords do not match.'
                })
            else:
                # Create the user:
                user = User.objects.get(username=form.cleaned_data['username'])
                user.email = form.cleaned_data['email']
                user.password = form.cleaned_data['password']
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
                auth.login(request, user)
                
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
        form = RegisterForm(initial=initial)

    return render(request, template, {'form': form})  
