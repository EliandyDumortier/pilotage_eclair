from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView,DetailView
from django.views.generic.edit import FormMixin
from django.urls import reverse
from .models import KPI, Commentaire
from django import forms

class DashboardView(TemplateView):
    template_name = 'pilot/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['kpis'] = KPI.objects.all().order_by('-date')
        return context

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
