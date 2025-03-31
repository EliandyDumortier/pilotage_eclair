from django.urls import path
from .views import (KPIDetailView, RoleDashboardView, WelcomeView, AddUserView, UserManagementView,UpdateUserView
, UploadPowerBIView,AddInsightView,ExportExcelView
) 


urlpatterns = [
    path('', WelcomeView.as_view(), name='home'),  # Home page
    path('dashboard/', RoleDashboardView.as_view(), name='dashboard'),
    path('kpi/<int:pk>/', KPIDetailView.as_view(), name='kpi-detail'),
    # admin views
    path('ajouter-utilisateur/', AddUserView.as_view(), name='add_user'),
    path('utilisateur/action/', UserManagementView.as_view(), name='user_action'),
    path('modifier-utilisateur/', UpdateUserView.as_view(), name='update_user'),
    #analyst views
    path('upload-powerbi/', UploadPowerBIView.as_view(), name='upload_powerbi'),
    path('ajouter-insight/', AddInsightView.as_view(), name='add_insight'),
    path('export/', ExportExcelView.as_view(), name='export_excel'),

]
