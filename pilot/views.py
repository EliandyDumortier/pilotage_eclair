from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.views.generic import TemplateView, DetailView
from django.views.generic.edit import FormMixin
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
import pandas as pd
from .models import KPI, Commentaire, User, PowerBIReport
from django import forms
from django.db.models import Q
from django.db.models import F


class WelcomeView(TemplateView):
    template_name = 'pilot/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['role'] = self.request.user.role
        return context

class RoleDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        date_filter = request.GET.get('date')
        categorie_filter = request.GET.get('categorie')
        search_query = request.GET.get('search')

        # Base KPI queryset
        kpis = KPI.objects.all()

        # Apply filters
        if date_filter:
            date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            kpis = kpis.filter(date=date)
        else:
            # Default to current month if no date filter
            current_month = timezone.now().replace(day=1)
            kpis = kpis.filter(date__gte=current_month)

        if categorie_filter:
            kpis = kpis.filter(categorie=categorie_filter)

        if search_query:
            kpis = kpis.filter(
                Q(nom__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        # Order KPIs
        kpis = kpis.order_by('-date', 'nom')

        # Common context
        context = {
            'kpis': kpis,
            'categories': KPI.CATEGORIES,
            'date_selected': date_filter,
            'categorie_selected': categorie_filter,
            'search_query': search_query,
        }

        # Role-specific context and template
        if user.role == 'admin':
            users = User.objects.all()
            role_filter = request.GET.get('role')
            if role_filter:
                users = users.filter(role=role_filter)
            
            context.update({
                'users': users,
                'role_selected': role_filter,
                'total_users': User.objects.count(),
                'active_users': User.objects.filter(is_active=True).count(),
            })
            template_name = 'pilot/dash_admin.html'

        elif user.role == 'analyste':
            context.update({
                'powerbi_reports': PowerBIReport.objects.filter(is_active=True).order_by('-date_upload')[:5],
                'recent_insights': Commentaire.objects.filter(is_insight=True).order_by('-date_creation')[:5],
            })
            template_name = 'pilot/dash_analyste.html'

        elif user.role == 'metier':
            # Add critical KPIs for métier dashboard
            critical_kpis = kpis.filter(
                Q(valeur_actuelle__lt=F('objectif') - F('seuil_critique')) |
                Q(valeur_actuelle__gt=F('objectif') + F('seuil_critique'))
            )
            context['critical_kpis'] = critical_kpis
            template_name = 'pilot/dash_metier.html'
        else:
            return redirect('home')

        return render(request, template_name, context)

class CommentaireForm(forms.ModelForm):
    class Meta:
        model = Commentaire
        fields = ['contenu', 'is_insight']
        widgets = {
            'contenu': forms.Textarea(attrs={
                'placeholder': "Ajoutez un commentaire...",
                'class': 'w-full p-2 border rounded-md',
                'rows': 3,
            }),
            'is_insight': forms.CheckboxInput(attrs={
                'class': 'mr-2',
            })
        }

class KPIDetailView(LoginRequiredMixin, FormMixin, DetailView):
    model = KPI
    template_name = 'pilot/kpi_detail.html'
    context_object_name = 'kpi'
    form_class = CommentaireForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['commentaires'] = self.object.commentaires.all().select_related('utilisateur')
        context['insights'] = self.object.commentaires.filter(is_insight=True)
        return context

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
            messages.success(request, 'Commentaire ajouté avec succès.')
            return self.form_valid(form)
        return self.form_invalid(form)

class ExportExcelView(View):
    def get(self, request):
        kpis = KPI.objects.all()
        date_filter = request.GET.get('date')
        categorie_filter = request.GET.get('categorie')

        if date_filter:
            try:
                date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                kpis = kpis.filter(date=date)
            except ValueError:
                pass  # ignore invalid date format

        if categorie_filter:
            kpis = kpis.filter(categorie=categorie_filter)

        # Build data
        data = [
            {
                'Indicateur': kpi.nom,
                'Valeur Actuelle': kpi.valeur_actuelle,
                'Objectif': kpi.objectif,
                'Écart': kpi.ecart(),
                'Catégorie': kpi.get_categorie_display(),
                'Date': kpi.date.strftime('%d/%m/%Y'),
                'Statut': kpi.statut(),
            }
            for kpi in kpis
        ]

        df = pd.DataFrame(data)

        # Excel response
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="kpis_export.xlsx"'
        df.to_excel(response, index=False, sheet_name='KPIs')

        return response

class UserManagementView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == 'admin'

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        if not user_id:
            return JsonResponse({'error': 'User ID required'}, status=400)
            
        user = get_object_or_404(User, id=user_id)
        
        if action == 'deactivate':
            user.is_active = False
            user.save()
            messages.success(request, f'Utilisateur {user.username} désactivé avec succès.')
        elif action == 'activate':
            user.is_active = True
            user.save()
            messages.success(request, f'Utilisateur {user.username} activé avec succès.')
        elif action == 'delete':
            username = user.username
            user.delete()
            messages.success(request, f"L'utilisateur {username} a été supprimé avec succès.")

        
        return redirect('dashboard')


class UploadPowerBIView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        file = request.FILES.get('powerbi_file')
        if file:
            PowerBIReport.objects.create(
                titre=file.name,
                fichier=file,
                utilisateur=request.user,
                description=request.POST.get('description', '')
            )
            messages.success(request, "Rapport Power BI uploadé avec succès.")
        else:
            messages.error(request, "Erreur lors de l'upload du fichier.")
        return redirect('dashboard')

####

from .forms import CustomUserCreationForm
from django.views import View
from django.contrib import messages
from django.shortcuts import render, redirect

class AddUserView(LoginRequiredMixin, View):
    def get(self, request):
        form = CustomUserCreationForm()
        return render(request, 'pilot/add_user.html', {'form': form})

    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Utilisateur créé avec succès.")
            return redirect('dashboard')
        messages.error(request, "Une erreur est survenue.")
        return render(request, 'pilot/add_user.html', {'form': form})

class UpdateUserView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == 'admin'

    def post(self, request, *args, **kwargs):
        user_id = request.POST.get('user_id')
        user = get_object_or_404(User, id=user_id)

        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.role = request.POST.get('role')
        user.save()
        messages.success(request, f"L'utilisateur {user.username} a été modifié avec succès.")
        return redirect('dashboard')


class AddInsightView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        kpi_id = request.POST.get('kpi_id')
        contenu = request.POST.get('contenu')

        if not kpi_id or not contenu:
            messages.error(request, "Veuillez remplir tous les champs.")
            return redirect('dashboard')

        kpi = get_object_or_404(KPI, id=kpi_id)
        Commentaire.objects.create(
            kpi=kpi,
            utilisateur=request.user,
            contenu=contenu,
            is_insight=True
        )
        messages.success(request, "💡 Insight ajouté avec succès.")
        return redirect('dashboard')