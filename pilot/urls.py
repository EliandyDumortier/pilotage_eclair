from django.urls import path
from .views import (KPIDetailView, RoleDashboardView, WelcomeView, AddUserView, UserManagementView,UpdateUserView
, UploadPowerBIView,AddInsightView,ExportExcelView, AnalyseListView, CreateAnalyseView,AnalyseDetailView, ExportAnalysePDFView,
TestPDFView,UpdateAnalyseView,DeleteAnalyseView
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
    #analyses views
    #path('analyses/', AnalyseListView.as_view(), name='analyse_list'),
    #path('analyses/create/', CreateAnalyseView.as_view(), name='create_analyse'),
    #path('analyses/<int:pk>/', AnalyseDetailView.as_view(), name='analyse_detail'),
    #path('analyses/<int:pk>/pdf/', ExportAnalysePDFView.as_view(), name='export_analyse_pdf'),

    path('analyses/', AnalyseListView.as_view(), name='analyse_list'),
    path('analyses/create/', CreateAnalyseView.as_view(), name='create_analyse'),
    path('analyses/<int:pk>/', AnalyseDetailView.as_view(), name='analyse_detail'),
    path('analyses/<int:pk>/update/', UpdateAnalyseView.as_view(), name='update_analyse'),
    path('analyses/<int:pk>/delete/', DeleteAnalyseView.as_view(), name='delete_analyse'),
    path('analyses/<int:pk>/pdf/', ExportAnalysePDFView.as_view(), name='export_analyse_pdf'),
    path('test-pdf/', TestPDFView.as_view(), name='test_pdf'),




]
