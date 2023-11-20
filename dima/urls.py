from django.urls import path
from . import views
from dima.views import getApi, APItro
from .views import HomePageView, tableView, update_click,export_users_xls, pars_PDF


urlpatterns = [
    path('api/getApi/', getApi.as_view()),
    path('', HomePageView.as_view(), name='home'),
    path('update_click', views.update_click, name='update_click'),
    path('task/<str:task_id>/', views.TaskView.as_view(), name='task'),
    path('export/excel', views.export_users_xls, name='export_excel'),
    path('tableView', views.tableView, name='tableView'),
    path('pars_PDF', views.pars_PDF, name='pars_PDF'),
]


