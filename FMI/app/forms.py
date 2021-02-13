"""
Definition of forms.
"""

from django import forms
from django.forms.utils import ErrorList
from django.forms.utils import ErrorDict
from django.forms.forms import NON_FIELD_ERRORS
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class BootstrapAuthenticationForm(AuthenticationForm):
    """Authentication form which uses boostrap CSS."""
    username = forms.CharField(max_length=254,
                               widget=forms.TextInput({
                                   'class': 'form-control',
                                   'placeholder': 'User name'}))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput({
                                   'class': 'form-control',
                                   'placeholder':'Password'}))


class scrape_form(forms.Form):
    site_choices = (('fragrantica', 'Fragrantica'), ('amazon', 'Amazon'), ('sephora', 'Sephora'), ('bbw', 'BBW'), ('fotw', 'Fragrances of the World'))
    site_choices_field = forms.MultipleChoiceField(label='Web Site', choices=site_choices, widget=forms.CheckboxSelectMultiple, required=True)
    scrape_choices = (('accords', 'Accords'), ('moods', 'Moods'), ('notes', 'Notes'), ('reviews', 'Reviews'), ('longevity', 'Longevity'), ('sillage', 'Sillage'))
    scrape_choices_field = forms.MultipleChoiceField(label='Scrape', choices=scrape_choices, widget=forms.CheckboxSelectMultiple, required=True)
    brand_name_field = forms.CharField(label='Brand', max_length=40, required = True, initial = '', help_text='Scrape for this brand')
    def add_form_error(self, message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(message)


class product_form(forms.Form):
    product_field = forms.CharField(label='Product', max_length=40, required = False, initial = '', help_text='Index this product')
    def add_form_error(self, message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(message)

class aws_form(forms.Form):
    s3_choices = (('deheerlijkekeuken', 'deheerlijkekeuken'), ('media', 'media'))
    s3_choices_field = forms.MultipleChoiceField(label='S3', choices=s3_choices, widget=forms.CheckboxSelectMultiple, required=False)
    def add_form_error(self, message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(message)

class crawl_form(forms.Form):
    from_dt = forms.DateField(label='From Date (DD/MM/YYYY)', required=False)
    nrpages_field = forms.IntegerField(label='Number of Pages to Scrape', initial = 50)
    site_choices = (('cosmetics', 'Cosmetics'), ('apf', 'APF'), ('contagious', 'Contagious'), ('mit', 'MIT Media Lab'), ('gci', 'GCI magazine'))
    site_choices_field = forms.MultipleChoiceField(label='Web Site', choices=site_choices, widget=forms.CheckboxSelectMultiple, required=False)
    scrape_choices = (('market', 'Market'), ('business', 'Business'), ('product', 'Product'), ('events', 'Events'),
                      ('publications', 'Publications'), ('blog', 'Blog'))
    scrape_choices_field = forms.MultipleChoiceField(label='Scrape', choices=scrape_choices, widget=forms.CheckboxSelectMultiple, required=True)
    rss_field = forms.CharField(label='RSS Category', max_length=40, required = False, initial = '', help_text='Crawl this category')
    brand_name_field = forms.CharField(label='Brand Name', max_length=40, required = False, initial = '', help_text='Scrape for this brand')
    brand_variant_field = forms.CharField(label='Brand Variant', max_length=40, required = False, initial = '', help_text='Scrape for this brand variant')
    perfume_code_field = forms.CharField(label='Perfume Code', max_length=40, required = False, initial = '' , help_text='Amazon Standard Identification Number')
    username = forms.CharField(label="User (domain\\user)", max_length=254, widget=forms.TextInput({'class': 'form-control','placeholder': 'User name'}), required=False)
    password = forms.CharField(label="Password", widget=forms.PasswordInput({'class': 'form-control','placeholder':'Password'}), required=False)
    def add_form_error(self, message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(message)

class load_form(forms.Form):
    cft_filename_field = forms.CharField(label='CFT file', max_length=80, required = False, initial = 'CFT Ing.csv')
    ci_filename_field = forms.CharField(label='CI file', max_length=80, required = False, initial = 'fresh and clean - test.csv')
    recipes_foldername_field = forms.CharField(label='Recipes folder', max_length=256, required = False, initial = "C:\\Users\\sww5648\\Documents\\Sjaak\\Culinair koken met het seizoen")
    cimap_filename_field = forms.CharField(label='CI Map file', max_length=80, required = False, initial = 'fresh and clean - Map.csv')
    excel_choices = (('recreate', 'Re-Create'), ('reload', 'Re-Load'), ('incrload', 'Incremental-Load'), ('delete', 'Delete'))
    excel_choices_field = forms.MultipleChoiceField(label='Load Mode', choices=excel_choices, required=False)
    excel_filename_field = forms.CharField(label='Excel file (xlsx)', max_length=80, required = False, initial = 'patents.xlsx')
    excelmap_filename_field = forms.CharField(label='Excel Map file', max_length=80, required = False, initial = '')
    cmis_choices = (('recreate', 'Re-Create'), ('reload', 'Re-Load'), ('incrload', 'Incremental-Load'), ('delete', 'Delete'))
    cmis_choices_field = forms.MultipleChoiceField(label='Load Mode', choices=cmis_choices, required=False)
    cmis_foldername_field = forms.CharField(label='Folder', max_length=80, required = False, initial = '/')
    cmis_objtype_field = forms.CharField(label='CMIS Object TYpe', max_length=80, required = False, initial = 'cmis:document')
    email_choices = (('imap', 'IMAP'), ('pop3', 'POP3'), ('smtp', 'SMTP'))
    email_choices_field = forms.ChoiceField(label='Mail protocol', choices=email_choices, required=False)
    email_address_field = forms.CharField(label='Your e-mail address', max_length=80, required = False, initial = '')
    email_password_field = forms.CharField(label="Your e-main password", widget=forms.PasswordInput({'class': 'form-control','placeholder':'Password'}), required=False)
    index_doc_name_field = forms.CharField(label='Index/Doc name', max_length=80, required = False, initial = '')
    #ci_filename_field = forms.CharField(label='CI file', max_length=40, required = False, initial = 'ChoiceModel FF USA.csv')
    def add_form_error(self, message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(message)

class d2y_admin_form(forms.Form):
    index_choices = (('conf', 'Configuration'), ('excel', 'Excel Files'), ('pi', 'Product Intelligence'), ('mi', 'MI - Market Intelligence'), ('si_sites', 'SI - Sites'),
                     ('feedly', 'Feedly'), ('mail', 'Mail'), ('scentemotion', 'Scent Emotion'), ('survey', 'CI Survey'),
                     ('dhk', 'de Heerlijke Keuken'))
    index_choices_field = forms.MultipleChoiceField(label='ES Index', choices=index_choices, widget=forms.CheckboxSelectMultiple, required=False)
    excel_filename_field = forms.CharField(label='Excel file (xlsx)', max_length=80, required = False, initial = 'ecosystem.xlsx')
    opml_filename_field = forms.CharField(label='OPML file', max_length=40, required = False, initial = '')
    auth_group_choices = (('d2y', 'DOUBLE2YY'), ('divault', 'DiVault'), ('dhk', 'de Heerlijke Keuken'))
    auth_group_choices_field = forms.MultipleChoiceField(label='Groups', choices=auth_group_choices, widget=forms.CheckboxSelectMultiple, required=False)
    auth_permission_choices = (('mi', 'Market Intelligence'), ('pi', 'Product Intelligence'), ('ci', 'Consumer Intelligence'),
                               ('se', 'Scent Emotion'), ('edepot', 'E-Depot'))
    auth_permission_choices_field = forms.MultipleChoiceField(label='Groups', choices=auth_permission_choices, widget=forms.CheckboxSelectMultiple, required=False)
    keyword_filename_field = forms.CharField(label='Keyword file', max_length=40, required = False, initial = '')
    def add_form_error(self, message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(message)


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        
    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            
        return user
