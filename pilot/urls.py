from django.urls import path
from .views import  KPIDetailView, RoleDashboardView, WelcomeView

urlpatterns = [
    path('', WelcomeView.as_view(), name='home'),  # Home page
    path('dashboard/', RoleDashboardView.as_view(), name='dashboard'),
    path('kpi/<int:pk>/', KPIDetailView.as_view(), name='kpi-detail'),

]
