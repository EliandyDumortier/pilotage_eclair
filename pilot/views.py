from django.shortcuts import render

# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import TemplateView,DetailView
from django.views.generic.edit import FormMixin
from django.urls import reverse
from .models import KPI, Commentaire
from django import forms
from django.shortcuts import render, redirect


class RoleDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        date_filter = request.GET.get('date')
        categorie_filter = request.GET.get('categorie')

        kpis = KPI.objects.all()

        if date_filter:
            from django.utils.dateparse import parse_date
            date = parse_date(date_filter)
            if date:
                kpis = kpis.filter(date=date)

        if categorie_filter:
            kpis = kpis.filter(categorie=categorie_filter)

        kpis = kpis.order_by('-date')

        context = {
            'kpis': kpis,
            'categories': KPI.CATEGORIES,
            'date_selected': date_filter,
            'categorie_selected': categorie_filter,
            'filter_applied': date_filter or categorie_filter
        }

        if user.role == 'admin':
            template_name = 'pilot/dash_admin.html'
        elif user.role == 'analyste':
            template_name = 'pilot/dash_analyste.html'
        elif user.role == 'metier':
            template_name = 'pilot/dash_metier.html'
        else:
            return redirect('home')

        return render(request, template_name, context)


# Formulaire pour les commentaires
class CommentaireForm(forms.ModelForm):
    class Meta:
        model = Commentaire
        fields = ['contenu']
        widgets = {
            'contenu': forms.Textarea(attrs={
                'placeholder': "Ajoutez un commentaire...",
                'class': 'w-full p-2 border rounded-md',
                'rows': 3,
            })
        }

class KPIDetailView(FormMixin, DetailView):
    model = KPI
    template_name = 'pilot/kpi_detail.html'
    context_object_name = 'kpi'
    form_class = CommentaireForm

    def get_success_url(self):
        return reverse('kpi-detail', kwargs={'pk': self.object.pk})

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            commentaire = form.save(commit=False)
            commentaire.kpi = self.object
            commentaire.utilisateur = request.user
            commentaire.save()
            return self.form_valid(form)
        return self.form_invalid(form)


