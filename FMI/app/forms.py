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

class excitometer_form(forms.Form):
    uptake_field = forms.CharField(label='Uptake', max_length=18, required = False, initial = 'one')
    IPC_field = forms.CharField(label='new IPC', max_length=18, required = True, initial = '')
    correlations_field = forms.IntegerField(label='Nr of Top Correlations', initial = 3)
    FITTE_norm_field = forms.FloatField(label='FITTE', initial = 0)
    CIU_field = forms.FloatField(label='CIU', initial = 0)
    regions_field = forms.IntegerField(label='Nr of Regions', initial = 0)
    type_choices = (('Brown', 'Brown'), ('Citrus', 'Citrus'), ('Cooling', 'Cooling'), ('Dairy/Cheese', 'Dairy/Cheese'), ('Fruit-General', 'Fruit-General'),
                    ('Fruit-Tropical', 'Fruit-Tropical'), ('Mint/Herb', 'Mint/Herb'), ('Modulator-Experience', 'Modulator-Experience'), ('Modulator-Fatty', 'Modulator-Fatty'),
                    ('Modulator-Masking', 'Modulator-Masking'), ('Modulator-Sweet', 'Modulator-Sweet'), ('Savory-Meat', 'Savory-Meat'), ('Savory-Non-Meat', 'Savory-Non-Meat'),
                    ('Savory-Salt/Umami', 'Savory-Salt/Umami'), ('Tea', 'Tea'), ('Vanilla', 'Vanilla'))
    type_field = forms.ChoiceField(label='Bucket/Type', choices=type_choices)
    regulator_choices = (('Nat', 'Natural'), ('Art', 'Artificial'), ('Nat Art', 'Natural/Artificial'))
    regulator_field = forms.ChoiceField(label='Regulator', choices=regulator_choices)
    def add_form_error(self, message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(message)

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

class r_and_d_form(forms.Form):
    ipc_field = forms.CharField(label='IPC', max_length=40, required = True, initial = '', help_text='IPC for which to retrieve the models')
    def add_form_error(self, message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(message)

class facts_form(forms.Form):
    survey_field = forms.CharField(label='Survey', max_length=40, required = True, initial = '', help_text='Survey for which to create Facts and Norms')
    facts_choices = (('emotion', 'Emotion'), ('concept', 'Concept'), ('suitable_product', 'Suitable Product'), ('suitable_stage', 'Suitable Stage'),
                     ('intensity', 'Intensity'), ('freshness', 'Freshness'), ('cleanliness', 'Cleanliness'), ('lastingness', 'Lastingness'),
                     ('liking.keyword', 'Linking/Hedonics'))
    facts_choices_field = forms.MultipleChoiceField(label='Facts', choices=facts_choices, widget=forms.CheckboxSelectMultiple, required=True)
    norms_choices = (('country', 'Country'), ('gender', 'Gender'), ('children', 'Children'), ('education', 'Education'), ('income', 'Income'),
                     ('age', 'Age groups'), ('ethnics', 'Ethnics'))
    norms_choices_field = forms.MultipleChoiceField(label='Norms', choices=norms_choices, widget=forms.CheckboxSelectMultiple, required=True)
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

class crawl_form(forms.Form):
    #index_choices = (('elastic', 'Elastic Index/Search'), ('azure', 'Azure Index/Search'))
    #index_choices_field = forms.MultipleChoiceField(label='Index', choices=index_choices, widget=forms.CheckboxSelectMultiple, required=True)
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

class fmi_admin_form(forms.Form):
    index_choices = (('conf', 'Configuration'), ('excel', 'Excel Files'), ('pi', 'Product Intelligence'), ('mi', 'MI - Market Intelligence'), ('si_sites', 'SI - Sites'),
                     ('feedly', 'Feedly'), ('mail', 'Mail'), ('scentemotion', 'Scent Emotion'), ('studies', 'CI/SE Studies'), ('survey', 'CI Survey'),
                     ('dhk', 'de Heerlijke Keuken'))
    index_choices_field = forms.MultipleChoiceField(label='ES Index', choices=index_choices, widget=forms.CheckboxSelectMultiple, required=False)
    excel_filename_field = forms.CharField(label='Excel file (xlsx)', max_length=80, required = False, initial = 'ecosystem.xlsx')
    opml_filename_field = forms.CharField(label='OPML file', max_length=40, required = False, initial = '')
    auth_group_choices = (('iff', 'IFF'), ('divault', 'DiVault'), ('dhk', 'de Heerlijke Keuken'), ('d2y', 'DOUBLE2YY'))
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
