from celery import shared_task
from django.http import JsonResponse
from celery.schedules import crontab
from rest_framework import status, renderers
from rest_framework.response import Response
import json
import os
from django.conf import settings
from celery_progress.backend import ProgressRecorder
from celery import Celery
app = Celery()
import time
import requests
import pickle
from .serializers import Tro, Lo
from rest_framework.renderers import JSONRenderer
from dima.models import Input_innDOC, Replacement_inn, Branch_checkSave, \
     CreateORG, UpdateDateFiler, ParsDt, WalkThroughAllOrg, OrgDate,\
    Calling_last_element, SelectPages, Page, Control

@shared_task(name='check', bind=True)
def checkingUp_to_date(self, duration):
    progress_recorder = ProgressRecorder(self)
    appeal = WalkThroughAllOrg().step_org()
    for ind, i in enumerate(appeal):
        time.sleep(duration)
        step_idOrg = ParsDt(i)
        act_year = step_idOrg.actual_year_URL()
        print(act_year)
        act_doc_dID = step_idOrg.actual_document_date_ID()
        choose_the_lastDocument = i.pep.all()
        last_element = choose_the_lastDocument[len(choose_the_lastDocument)-1]
        lasdDoc_inBD = last_element.url_doc
        if act_doc_dID != lasdDoc_inBD:
            step_idOrg.save_newORG()
        else:
            pass
        progress_recorder.set_progress(ind + 1.34, 134, f'Обновляется организаций {ind}')
    return 'Все обновилось'

@shared_task(name='tro')
def task_update(request):
    tro = Input_innDOC(r'C:\Users\777\PycharmProjects\dd\dima\Список ФМО ИНН.txt', 'r')
    pepe = tro.open()
    chto = tro.get_url_inn()
    for i in chto:
        print(i)
        replINN = Replacement_inn(i)
        get_repl = replINN.get_replacement_id()
        print(get_repl)
        examination_branch = Branch_checkSave(get_repl)
        name = examination_branch.find_name()
        print(name)
        id = examination_branch.find_id()
        print(id)
        inn = examination_branch.find_inn()
        new_org = CreateORG(name, id, inn)
        save = new_org.create_new_org()
        other_date = UpdateDateFiler(inn)
        input_dt = other_date.get_filter_reqForInn()
        prs_other_dt = ParsDt(input_dt)
        actual_year = prs_other_dt.actual_year_URL()
        print(actual_year)
        act_id = prs_other_dt.actual_document_date_ID()
        print(act_id)
        act_date = prs_other_dt.current_time()
        print(act_date)
        save = prs_other_dt.save_newORG()

@shared_task(name='parsPDF', bind=True)
def parsIn_PDF(self, duration):
    progress_recorder = ProgressRecorder(self)
    B = []
    for ind, i in enumerate(OrgDate.objects.all()):
        print(ind)
        time.sleep(duration)
        le = Calling_last_element(i).last_element()

        response = requests.get(le, headers={'User-agent': 'your bot 0.1'}, verify=False)

        new_path = settings.MEDIA_ROOT

        with open(f'{new_path}/{ind+1}doc.pdf', 'wb') as f:
            test_el = f.write(response.content)
            select_pages = SelectPages().get_actual_bumber_pages(f'{new_path}/{ind+1}doc.pdf')
            pages = Page(select_pages).information_on_current_page()
            # Замечняем ключ на название документа
            pages[f'{new_path}/{ind+1}doc.pdf'] = pages.pop(next(iter(pages.keys())))
            print(pages)
            lst = Control(pages).list_date()
            print(lst)

            string_titile_name = i.inn

            a = []
            for k in lst:
                for key, values in k.items():
                    for w in range(-1, (len(values))):
                        tro = map(list, zip(*values))
                    a.append(tro)

                for i in a:
                    for q in i:
                        t = {}
                        t[string_titile_name] = q
                        B.append(t)

            for p in B:
                print(p)


        progress_recorder.set_progress(ind + 1, 4, f'Обновляется организаций {ind}')
    with open('С_тебя_ящик_пива', 'wb') as fp:
        pickle.dump(B, fp)

    return 'Все обновилось'


@shared_task(bind=True)
def shlep(self, duration):
    progress_recorder = ProgressRecorder(self)
    for i, ind in enumerate(OrgDate.objects.all()):
        time.sleep(duration)
        progress_recorder.set_progress(i + 1.34, 134, f'Обновляется организаций {i}')
    return 'Обновилось'






