from django.urls import path
from .views import DashboardView, KPIDetailView, RoleDashboardView

urlpatterns = [
    path('dashboard', DashboardView.as_view(), name='dashboard'),
    path('mon-espace/', RoleDashboardView.as_view(), name='role-dashboard'),
    path('kpi/<int:pk>/', KPIDetailView.as_view(), name='kpi-detail'),

]
