from datetime import datetime
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)

# Create your models here.

class UserManager(BaseUserManager):
    def create_user(self, username, first_name, last_name, email,
                    street, housenumber, zip, city, country,
                    password=None, phone_number=None, date_of_birth=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            username=username, first_name=first_name, last_name=last_name,
            email=self.normalize_email(email),
            street=street, housenumber=housenumber, zip=zip, city=city, country=country,
            phone_number=phone_number, date_of_birth=date_of_birth,
            date_joined = datetime.now(), last_login = None    
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, first_name, last_name, email,
                            street, housenumber, zip, city, country, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            username, first_name=first_name, last_name=last_name, email=email,
            street=street, housenumber=housenumber, zip=zip, city=city, country=country,
            password=password
        )
        user.is_admin = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150) 
    last_name = models.CharField(max_length=150)          
    email = models.EmailField(verbose_name='email address', max_length=255, unique=True)
    street = models.CharField(max_length=255)
    housenumber = models.CharField(max_length=255)
    zip = models.CharField(max_length=255) 
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=30, null=True)    
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    date_of_birth = models.DateField(null=True) 
    date_joined = models.DateField(null=True)
    last_login = models.DateField(null=True)        

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email', 'street', 'housenumber', 'zip', 'city', 'country']

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin

class LogMessage(models.Model):
    message = models.CharField(max_length=300)
    log_date = models.DateTimeField("date logged")

    def __str__(self):
        """Returns a string representation of a message."""
        date = timezone.localtime(self.log_date)
        return f"'{self.message}' logged on {date.strftime('%A, %d %B, %Y at %X')}"