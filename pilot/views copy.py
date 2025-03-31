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


    #################Analysess#######################
from django.views.generic import ListView,CreateView
from .models import Analyse
from django.urls import reverse_lazy

from .forms import AnalyseForm



class AnalyseListView(ListView):
    model = Analyse
    template_name = 'pilot/analyses/analyse_list.html'
    context_object_name = 'analyses'

    def get_queryset(self):
        user = self.request.user
        if user.role == 'analyste':
            return Analyse.objects.filter(auteur=user)  # Show only the analyst's own
        return Analyse.objects.filter(is_published=True)  # Métier only sees published

from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from .models import Analyse, KPI
from .forms import AnalyseForm

class CreateAnalyseView(CreateView):
    model = Analyse
    form_class = AnalyseForm
    template_name = 'pilot/analyses/analyse_create.html'
    success_url = reverse_lazy('analyse_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        selected_category = self.request.GET.get('categorie')
        if selected_category:
            kwargs['initial'] = {'categorie': selected_category}
            kwargs['filtered_category'] = selected_category
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_mode'] = self.request.GET.get('filter') == '1'
        return context

    def form_valid(self, form):
    # Save the instance first (now it has an ID)
        self.object = form.save(commit=False)
        self.object.auteur = self.request.user
        self.object.save()

    # 💥 Assign KPI ManyToMany after the instance is saved
        selected_names = form.cleaned_data.get('kpi_names', [])
        matching_kpis = KPI.objects.filter(nom__in=selected_names)
        self.object.kpis.set(matching_kpis)

    # Save filter info to session (for detail view)
        self.request.session['kpi_names'] = selected_names
        self.request.session['date_debut'] = self.request.POST.get('date_debut') or None
        self.request.session['date_fin'] = self.request.POST.get('date_fin') or None

        return super().form_valid(form)





from django.views.generic import DetailView
from .models import Analyse, KPI
import plotly.graph_objs as go
import plotly.offline as pyo
from datetime import datetime
from django.db import models
from django.utils.timezone import now


class AnalyseDetailView(DetailView):
    model = Analyse
    template_name = 'pilot/analyses/analyse_detail.html'
    context_object_name = 'analyse'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        analyse = self.get_object()

        # ✅ Retrieve session-stored filters
        selected_names = self.request.session.get('kpi_names', [])
        date_debut = self.request.session.get('date_debut')
        date_fin = self.request.session.get('date_fin')

        # ✅ Parse date strings
        if date_debut:
            date_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
        if date_fin:
            date_fin = datetime.strptime(date_fin, '%Y-%m-%d').date()

        # ✅ Filter KPIs based on names and date range
        kpis = KPI.objects.filter(nom__in=selected_names)
        if date_debut:
            kpis = kpis.filter(date__gte=date_debut)
        if date_fin:
            kpis = kpis.filter(date__lte=date_fin)

        # 🪵 Debug output
        print("\n📊 DEBUG — Analyse Detail View")
        print("Selected KPI names:", selected_names)
        print("Date début:", date_debut)
        print("Date fin:", date_fin)
        print("Total KPIs found:", kpis.count())
        for k in kpis:
            print(f" - KPI: {k.nom} | Date: {k.date} | Valeur actuelle: {k.valeur_actuelle}")

        # 💬 Collect comments and insights
        commentaires = []
        for kpi in kpis:
            commentaires.extend(kpi.commentaires.select_related('utilisateur').all())

        insights = [c for c in commentaires if c.is_insight]
        regular_comments = [c for c in commentaires if not c.is_insight]

        context['insights'] = insights
        context['commentaires'] = regular_comments

        # 📊 Generate Plotly chart
        chart_type = analyse.chart_type
        fig = go.Figure()

        if chart_type == 'line':
            for nom in selected_names:
                subset = kpis.filter(nom=nom).order_by('date')
                fig.add_trace(go.Scatter(
                    x=[k.date for k in subset],
                    y=[k.valeur_actuelle for k in subset],
                    mode='lines+markers',
                    name=nom
                ))

        elif chart_type == 'bar':
            for nom in selected_names:
                subset = kpis.filter(nom=nom).order_by('date')
                fig.add_trace(go.Bar(
                    x=[k.date for k in subset],
                    y=[k.valeur_actuelle for k in subset],
                    name=nom
                ))

        elif chart_type == 'pie':
            grouped = {}
            for nom in selected_names:
                total = kpis.filter(nom=nom).aggregate(total=models.Sum('valeur_actuelle'))['total']
                if total:
                    grouped[nom] = total
            fig = go.Figure(data=[go.Pie(labels=list(grouped.keys()), values=list(grouped.values()))])

        fig.update_layout(title=analyse.titre)
        plot_div = pyo.plot(fig, output_type='div')
        context['plotly_chart'] = plot_div

        return context


#### export analyses to PDF 
from django.views import View
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
from .models import Analyse, KPI
from datetime import datetime
import plotly.graph_objs as go
import plotly.io as pio
import base64
import logging
from django.contrib.staticfiles import finders
from django.db.models import Sum, Prefetch
from io import BytesIO

logger = logging.getLogger(__name__)
class ExportAnalysePDFView(View):
    def get(self, request, pk):
        try:
            analyse = Analyse.objects.select_related('auteur').get(pk=pk)

            selected_names = request.session.get('kpi_names', [])
            date_debut = request.session.get('date_debut')
            date_fin = request.session.get('date_fin')
            date_filters = {}

            if date_debut:
                date_filters['date__gte'] = datetime.strptime(date_debut, "%Y-%m-%d").date()
            if date_fin:
                date_filters['date__lte'] = datetime.strptime(date_fin, "%Y-%m-%d").date()

            kpis = KPI.objects.filter(nom__in=selected_names, **date_filters).select_related()

            commentaires = []
            for kpi in kpis:
                commentaires.extend(kpi.commentaires.select_related('utilisateur').all())

            insights = [c for c in commentaires if c.is_insight]
            regular_comments = [c for c in commentaires if not c.is_insight]

            # Chart generation
            fig = go.Figure()
            if analyse.chart_type in ['line', 'bar']:
                for nom in selected_names:
                    subset = sorted((k for k in kpis if k.nom == nom), key=lambda k: k.date)
                    trace = go.Scatter if analyse.chart_type == 'line' else go.Bar
                    fig.add_trace(trace(x=[k.date for k in subset], y=[k.valeur_actuelle for k in subset], name=nom))
            else:
                totals = {}
                for k in kpis:
                    totals[k.nom] = totals.get(k.nom, 0) + k.valeur_actuelle
                fig = go.Figure(data=[go.Pie(labels=list(totals.keys()), values=list(totals.values()))])

            fig.update_layout(
                title=analyse.titre,
                width=800, height=400,
                showlegend=True,
                margin=dict(l=50, r=50, t=50, b=50),
                paper_bgcolor='white',
                plot_bgcolor='white'
            )

            # Convert chart to base64 image
            img_buffer = BytesIO()
            pio.write_image(fig, img_buffer, format='jpeg', engine='kaleido')
            chart_base64 = base64.b64encode(img_buffer.getvalue()).decode()

            logo_base64 = None
            if logo_path := finders.find('img/logo-cacf.png'):
                with open(logo_path, 'rb') as f:
                    logo_base64 = base64.b64encode(f.read()).decode()

            template = get_template("pilot/analyses/analyse_pdf.html")
            result = BytesIO()
            html = template.render({
                'analyse': analyse,
                'kpis': kpis,
                'insights': insights,
                'commentaires': regular_comments,
                'chart_base64': chart_base64,
                'logo_base64': logo_base64,
                'now': datetime.now(),
            }).encode('UTF-8')

            pisa.CreatePDF(html, dest=result, encoding='utf-8')
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="analyse_{pk}.pdf"'
            return response

        except Exception as e:
            logger.error(f"PDF Export Error: {str(e)}", exc_info=True)
            return HttpResponse("Erreur lors de la génération du PDF", status=500)


#exemple

from django.views import View
from django.http import HttpResponse
from weasyprint import HTML

class TestPDFView(View):
    def get(self, request):
        html = "<h1>Hello from CACF PDF 🚀</h1><p>Si tu vois ceci, WeasyPrint fonctionne !</p>"
        pdf = HTML(string=html).write_pdf()

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename=\"test.pdf\"'
        return response
