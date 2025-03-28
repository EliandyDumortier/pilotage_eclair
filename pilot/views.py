from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView
from .models import KPI

class DashboardView(TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['kpis'] = KPI.objects.all().order_by('-date')
        return context
