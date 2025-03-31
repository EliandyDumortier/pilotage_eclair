from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Analyse, KPI

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs.update({
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md',
            })


from django import forms
from .models import Analyse, KPI
from django.forms.widgets import DateInput

from django import forms
from .models import Analyse, KPI
from django.forms.widgets import DateInput

from django import forms
from .models import Analyse, KPI

class AnalyseForm(forms.ModelForm):
    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    kpi_names = forms.MultipleChoiceField(
        required=False,
        label="Indicateurs (noms des KPIs)",
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        choices=[],
    )

    def __init__(self, *args, **kwargs):
        filtered_category = kwargs.pop('filtered_category', None)
        super().__init__(*args, **kwargs)

        # Prevent validation error on actual ManyToMany field
        self.fields['kpis'].required = False

        # Populate kpi_names choices
        if filtered_category:
            noms = KPI.objects.filter(categorie=filtered_category).values_list('nom', flat=True).distinct()
        else:
            noms = KPI.objects.values_list('nom', flat=True).distinct()

        self.fields['kpi_names'].choices = [(n, n) for n in sorted(set(noms))]

    def clean(self):
        cleaned_data = super().clean()
        selected_names = cleaned_data.get('kpi_names')

        if not selected_names:
            raise forms.ValidationError("Veuillez sélectionner au moins un indicateur.")

        # Fetch real KPI objects
        matching_kpis = KPI.objects.filter(nom__in=selected_names)
        cleaned_data['matching_kpis'] = matching_kpis
        return cleaned_data

    def save(self, commit=True):

        instance = super().save(commit=commit)
        return instance


    class Meta:
        model = Analyse
        fields = ['titre', 'description', 'chart_type', 'categorie', 'is_published', 'kpis']
        widgets = {
            'kpis': forms.SelectMultiple(attrs={'style': 'display: none'}),
        }
