from django.http import JsonResponse
from celery import current_app
from django.views import View
from rest_framework import generics
from .models import OrgDate, Doc, FiltersUpdatedLastMonth
from .serializers import Tro, Lo
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from celery import shared_task
from .tasks import task_update, checkingUp_to_date, shlep, parsIn_PDF
from django.views.generic import TemplateView
from django.shortcuts import render
import xlsxwriter
import xlwt

from django.http import HttpResponse

def export_users_xls(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="export_actual_links.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Users Data')

    # Sheet header, first row
    row = 0
    col = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    for i in OrgDate.objects.all():
        tro = i.pep.all()
        last_element = tro[len(tro) - 1]
        print(last_element.trun.inn)
        row += 1
        ws.write(row, col, last_element.trun.inn)
        ws.write(row, col + 1, last_element.url_doc)

    wb.save(response)
    return response

def tableView(request):
    if request.method == 'POST':
        last_element = FiltersUpdatedLastMonth(Doc).get_filter()
        context = {'filtr': last_element}
        return render(request, 'home.html', context)


def index(request):
    task = shlep.delay(0.1)
    return render(request, 'home.html', {'task_id': task.task_id})

class getApi(generics.ListAPIView):
    queryset = OrgDate.objects.all()
    serializer_class = Lo


class HomePageView(TemplateView):
    template_name = 'home.html'

def update_click(request):
    context = {}
    if request.method == 'POST':
        task = checkingUp_to_date.delay(0.001)
        context['task_id'] = task.id
        context['task_status'] = task.status
        return render(request, 'home.html', context)

def pars_PDF(request):
    context = {}
    if request.method == 'POST':
        task = parsIn_PDF.delay(0.001)
        context['task_id'] = task.id
        context['task_status'] = task.status
        return render(request, 'home.html', context)

class APItro(APIView):
    def create(request):
        task_update.delay(request)


class TaskView(View):
    def get(self, request, task_id):
        task = current_app.AsyncResult(task_id)
        response_data = {'task_status': task.status, 'task_id': task.id}
        if task.status == 'SUCCESS':
            response_data['results'] = task.get()
        return JsonResponse(response_data)


