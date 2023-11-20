from django.db import models
import json
from urllib.request import urlopen
from urllib.error import HTTPError
import time
import datetime
from datetime import datetime
from urllib.parse import urlsplit, parse_qs, urlencode
from urllib.error import URLError
import ssl
import certifi
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
start_time = time.time()
import requests
import pdfplumber
import sys, fitz
import camelot
import numpy as np
import re
import pandas as pd
from django.conf import settings
from yargy import rule, and_, Parser
from yargy.predicates import gte, lte
from django.contrib.postgres.fields import ArrayField
ssl._create_default_https_context = ssl._create_unverified_context


class OrgDate(models.Model):

    objects = models.Manager()
    name = models.CharField(max_length=350, verbose_name='название')
    id_ogr = models.IntegerField(null=True, verbose_name='id организации')
    inn = models.BigIntegerField(null=True, verbose_name='инн организации')
    actual_year = models.IntegerField(null=True, verbose_name='актуальный год') ##Task
    url_pars = models.URLField(null=True, max_length=200, verbose_name='урл_для парсинга')
    publishDate = models.BigIntegerField(null=True, verbose_name='время публикации')

class Doc(models.Model):

    objects = models.Manager()
    trun = models.ForeignKey(OrgDate, related_name='pep', null=True,
                             on_delete=models.CASCADE)
    url_doc = models.URLField(max_length=200, null=True, verbose_name='Ссылка на актуальный документ')

    update_date = models.DateField(null=True)


    class Meta:
        unique_together = ['trun', 'update_date']
        ordering = ['url_doc', '-id']


    def __str__(self):
        card_name = (self.url_doc, str(self.update_date))
        return str(card_name)

class Qot(models.Model):
    objects = models.Manager()
    second = models.ForeignKey(Doc, related_name='sec', null=True,
                               on_delete=models.CASCADE)
    board = ArrayField(
        ArrayField(
            models.CharField(max_length=10, blank=True),
            size=8,
        ),
        size=8,
    )

class Inquiry:

    def __init__(self, start_url):
        self.start_url = start_url

    def get_start_url(self):
        return self.start_url

    def InquiryPrs(self):
        query = urlsplit(self.start_url).query
        params = parse_qs(query)
        for key, val in params.items():
            # Делаем словарь из части запроса
            if len(val) == 1:
                params[key] = val[0]
        return params

class JsonParse:

    def __init__(self, inquiry, input_urlencode):
        self.inquiry = inquiry
        self.input_urlencode = input_urlencode

    def get_urlencode_input(self):
        return urlencode(self.input_urlencode)

    def AssemblyInquiry(self):##Собираем запрос
        tro = urlsplit(self.inquiry).scheme+'://'+ urlsplit(self.inquiry).netloc \
              + urlsplit(self.inquiry).path + '?'+ self.get_urlencode_input()
        return tro

take_default_json = Inquiry('https://bus.gov.ru/public/agency/agency_tasks.json?agency=182691&task=')
take_default_address = take_default_json.get_start_url()
prs_default_dict = take_default_json.InquiryPrs()

## Запрос в котором можно подставить инн и получить id орг ##

inn_input = 'https://bus.gov.ru/public-rest/api/register/init?agency=' \
                        '7713059497&agencyTypesDropDownValue=b_c_a_types&annulment' \
                        '=false&authority=&city=&d-442831-p=1&level=&ogv=&page=1&pageSize' \
                        '=10&params=%7B%22d-442831-p%22:1%7D&status=&tofkCode='
take_inn = Inquiry(inn_input)
get_inn_req = take_inn.get_start_url()
prs_inn_req = take_inn.InquiryPrs()

## 1.1 Подставляем инн и формируем ссылку ##
##     Подставляем инн из запроса         ##

class Input_inn:

    def __init__(self, req, name):
        self.req = req
        self.name = name
    def substituteANDget_url(self):
            x = self.req.POST[self.name]
            prs_inn_req['agency'] = x
            a = JsonParse(get_inn_req, prs_inn_req).AssemblyInquiry()
            return a

## 1.2 Подставляем инн и формируем ссылку ##
##     Подставляем инн из документа со списком инн  ##

class Input_innDOC:

    def __init__(self, file_name, method):
        self.file_name = file_name
        self.method = method

    def open(self):
        list_inn = []
        file = open(self.file_name, self.method)
        while True:
            line = file.readline()
            if not line:
                break
            line_inn = line.strip()
            list_inn.append(line_inn)
        return list_inn

    def get_url_inn(self):
        lstINN = self.open()
        listURL = []
        for inn in lstINN:
            prs_inn_req['agency'] = inn
            a = JsonParse(get_inn_req, prs_inn_req).AssemblyInquiry()
            listURL.append(a)
        return listURL

## 2.0 Подгружаем Json со всех запросов ##

class JsonLoads:

    def __init__(self, url):

        self.url = url

    def reqJson(self):

        try:
            response = urlopen(self.url,
                           context=ssl._create_unverified_context(cafile=certifi.where()))
            data_json = json.loads(response.read())
            return data_json

        except TimeoutError:
            time.sleep(0.1)

        except URLError:
            pass

        except AttributeError:
            time.sleep(0.1)

url_inn = 'https://bus.gov.ru/public/agency/agency.json?agency=531369' ##Урл для id организацир
agency_json_url = Inquiry(url_inn)
get_agency_json_url = agency_json_url.get_start_url()
pars_agency_json = agency_json_url.InquiryPrs()

## 3.0 Узнаем ID у всех оргов

class Replacement_inn:

    def __init__(self, link):
        self.link = link

    ## Надо сохранять все ID что-бы потом проверять на филиалы ##

    def get_replacement_id(self):
        jsLoads = JsonLoads(self.link)
        get_jsLoads = jsLoads.reqJson()
        agency = [item['agencyId'] for item in get_jsLoads['agencies']]
        list_id = []
        for i in agency:
            tro = pars_agency_json
            tro['agency'] = i
            formed_url = JsonParse(get_agency_json_url, tro).AssemblyInquiry()
            list_id.append(formed_url)
        return list_id

## 4.0 Выясняем являеться есть ли организации филиалы ##
## отсеииваем филиалы ,выясняем название, инн, id ##

class Branch_checkSave:

    def __init__(self, open_url):
        self.open_url = open_url

    def branch_true(self):
        for url_in_id in self.open_url:
            jsLoads = JsonLoads(url_in_id)
            get_jsLoads = jsLoads.reqJson()
            try:
                ## Вызов запроса и загрузки джейсона
                if get_jsLoads['agency']['branchFlag'] == False:
                    return get_jsLoads
                else:
                    pass
            except TimeoutError:
                time.sleep(0.3)
            except HTTPError:
                pass
            except TypeError:
                time.sleep(1.0)

    def find_name(self):
        try:
            agency_name = self.branch_true()['agency']['fullClientName']
            return agency_name
        except TypeError:
            time.sleep(1.0)

    def find_id(self):
        try:
            agency_id = self.branch_true()['agency']['id']
            return agency_id
        except TypeError:
            time.sleep(1.0)

    def find_inn(self):
        try:
            agency_inn = int(self.branch_true()['agency']['inn'])
            return agency_inn
        except TypeError:
            time.sleep(1.0)

## 5.0 Создаем в бд новую организацию  ##

class CreateORG:

    def __init__(self, NAME, ID, INN):
        self.NAME = NAME
        self.ID = ID
        self.INN = INN

    def create_new_org(self):
        crt = OrgDate(name=self.NAME, id_ogr=self.ID, inn=self.INN)
        try:
            crt.save()
            return crt
        except IntegrityError:
            print('инн организации удален')

## 6.0  Добавляем: добавляем ссслку на документ, статус, дату обновления и год  ##


prs_last_year = Inquiry('https://bus.gov.ru/public/agency/agency_tasks.json?agency=182691&task=')
get_prs_last_year = prs_last_year.get_start_url()
part_last_year_json = prs_last_year.InquiryPrs()

__const_url = 'https://bus.gov.ru/public/download/download.html?id='

prs_download_doc = Inquiry(__const_url)
get_get_prs_inquiry_doc = prs_download_doc.get_start_url()
prs_part_doc = prs_download_doc.InquiryPrs()


class UpdateDateFiler:

    def __init__(self, find_inn):
        self.find_inn = find_inn

    def get_filter_reqForInn(self):
        try:
            b = OrgDate.objects.get(inn=self.find_inn)
            return b
        except ObjectDoesNotExist:
            pass

class WalkThroughAllOrg:

    def step_org(self):
        list_step = []
        for i in OrgDate.objects.all():
            list_step.append(i)
        return list_step

class ParsDt:

    def __init__(self, action_choice):
        self.action_choice = action_choice

    def actual_year_URL(self):

        try:
            lo = self.action_choice.id_ogr
            part_last_year_json['agency'] = lo
            part_last_year_json['task'] = ''
            collect = JsonParse(get_prs_last_year, part_last_year_json).AssemblyInquiry()
            req_last = JsonLoads(collect)
            get_jsonData = req_last.reqJson()
            tasks_dict = get_jsonData['tasks']
            task = tasks_dict[-1:]
            for last_year in task:
                for key, values in last_year.items():
                    all_last_year = last_year.get('id')
            Prs_tasks = part_last_year_json
            try:
                Prs_tasks['task'] = all_last_year
                finally_url = JsonParse(get_prs_last_year,
                                        Prs_tasks).AssemblyInquiry()  ## урл с актуальным годом
                return finally_url

            except UnboundLocalError:
                print('Нет данных по государственному заданию')

        except AttributeError:
            print('Инн удален и организации не существует')

    def actual_document_date_ID(self):
        req_date = JsonLoads(self.actual_year_URL())
        get_jsonData = req_date.reqJson()
        try:
            a = []
            doc = get_jsonData['currentTask']['attachments']  ##Документ
            for i in doc:
                all_last_document = i.get('id')
                c = 'https://bus.gov.ru/public/download/download.html?id=' + str(all_last_document)
                a.append(c)
            return a
        except TypeError:
            """Без ссылки"""

    def current_time(self):

        if self.actual_document_date_ID() == None:
            pass
        else:
            current_date = datetime.now().date()
            return current_date


def save_newORG(i, actual_year_URL ,actual_document_date_ID):

    try:
        i.url_pars = actual_year_URL
        i.save()
        i.pep.create(url_doc=actual_document_date_ID,
                           update_date=datetime.now().date())
    except AttributeError:
        """Ссылки для парсинга нет"""

DAY = and_(
    gte(1),
    lte(31)
)
MONTH = and_(
    gte(1),
    lte(12)
)
YEAR = and_(
    gte(1),
    lte(2028)
)
DATE = rule(
    DAY,
    '.',
    MONTH,
    '.',
    YEAR
)
parser = Parser(DATE)
class OpenAndWrite:
    def __init__(self, media_root, list_all_url_date):
        self.media_root = media_root
        self.list_all_url_date = list_all_url_date

    def download_file(self):
        dct = {}
        for ind, i in enumerate(self.list_all_url_date):
            response = requests.get(i, headers={'User-agent': 'your bot 0.1'}, verify=False)
            part = i.split('=')[1]
            name_file = f'{self.media_root}/{part}.pdf'
            with open(name_file, 'wb') as f:
                f.write(response.content)
                op = Open_filePdf(name_file).get_open()
                text = WorkPages(op).get_text_one_pages(0)
                all_date_list = []
                for match in parser.findall(text):
                    tro = [_.value for _ in match.tokens]
                    deadline = int(tro[4]), int(tro[2]), int(tro[0])
                    all_date_list.append(deadline)
                if len(all_date_list) == 1:
                    dct[all_date_list[0]] = i
                else:
                    dct[all_date_list[2]] = i

        for k, v in list(dct.items()):
            if k[0] == 2024:
                del dct[k]
        print(dct)
        max_key_date = max(dct.keys())
        print(max_key_date)
        for k, v in dct.items():
            if k == max_key_date:
                return v

# 7.0 Делаем фильтр для последних документов обнолвленных за месяц

class FiltersUpdatedLastMonth:

    def __init__(self, bd):
        self.bd = bd

    def get_filter(self):

        # Фильтруем по акуальному месяцу
        today = datetime.now()
        fl = self.bd.objects.filter(update_date__month=today.month)
        return fl


class Calling_last_element:
    def __init__(self, db_field):
        # Вызываем поле бд по которому потом
        # можно будет выбрать последнюю запись

        self.db_field = db_field

    def last_element(self):
        """" Мемтод с последним элементом """
        tro = self.db_field.pep.all()
        last_element = tro[len(tro) - 1]
        le = last_element.url_doc
        return le

class Open_filePdf:

    def __init__(self, list_name_PDF):
        self.list_name_PDF = list_name_PDF

    def get_open(self):
        pdf = pdfplumber.open(self.list_name_PDF)
        return pdf

class WorkPages:

    def __init__(self, obj_file):
        self.obj_file = obj_file

    def get_len_pages(self):
        return self.obj_file.pages

    def step_all_pages(self):

        squares = enumerate(self.get_len_pages())
        return list(squares)

    def get_text_all_pages(self):

        for i in self.step_all_pages():
            page = self.get_len_pages()[i[0]]
            text = page.extract_text()
            yield text

    def get_text_one_pages(self, itr):

        page = self.get_len_pages()[itr]
        text = page.extract_text()
        return text

    def seek_to_divide(self):
        # Разбивка для поиска одного ключевого слова

        for i in self.get_text_all_pages():
            sep = '\n'
            result = [x + sep for x in i.split(sep)]
            list_number = [line.rstrip() for line in result]
            yield list_number

    def number_pages(self, *args):
        # Поиск по длине слова и возврат индекса станицы документа
        list_in_pages = list(self.seek_to_divide())
        for k in list_in_pages:
            for j in k:
                x = j.replace(*args, "")
                if (len(x) != len(j)):
                    return list_in_pages.index(k)


class AhoNode:
    ''' Вспомогательный класс для построения дерева
    '''

    def __init__(self):
        self.goto = {}
        self.out = []
        self.fail = None

def aho_create_forest(patterns):
    '''Создать бор - дерево паттернов
    '''
    root = AhoNode()

    for path in patterns:
        node = root
        for symbol in path:
            node = node.goto.setdefault(symbol, AhoNode())
        node.out.append(path)
    return root

def aho_create_statemachine(patterns):
    '''Создать автомат Ахо-Корасика.
    Фактически создает бор и инициализирует fail-функции
    всех узлов, обходя дерево в ширину.
    '''
    # Создаем бор, инициализируем
    # непосредственных потомков корневого узла
    root = aho_create_forest(patterns)
    queue = []
    for node in root.goto.values():
        queue.append(node)
        node.fail = root

    # Инициализируем остальные узлы:
    # 1. Берем очередной узел (важно, что проход в ширину)
    # 2. Находим самую длинную суффиксную ссылку для этой вершины - это и будет fail-функция
    # 3. Если таковой не нашлось - устанавливаем fail-функцию в корневой узел
    while len(queue) > 0:
        rnode = queue.pop(0)

        for key, unode in rnode.goto.items():
            queue.append(unode)
            fnode = rnode.fail
            while fnode is not None and key not in fnode.goto:
                fnode = fnode.fail
            unode.fail = fnode.goto[key] if fnode else root
            unode.out += unode.fail.out
    return root

def aho_find_all(s, root, callback):
    '''Находит все возможные подстроки из набора паттернов в строке.
    '''
    node = root

    for i in range(len(s)):
        while node is not None and s[i] not in node.goto:
            node = node.fail
        if node is None:
            node = root
            continue
        node = node.goto[s[i]]
        for pattern in node.out:
            callback(i - len(pattern) + 1, pattern)


## Сделать список и проиндексировать страницы ##

class SelectPages:

    @staticmethod
    def get_actual_bumber_pages(iter_element):

        B = list()

        open = Open_filePdf(iter_element).get_open()
        pages = WorkPages(open)
        txt = pages.get_text_all_pages()

        for indx, words in enumerate(txt):
            def on_occurence(pos, patterns):
                A = list()
                A.append(indx)
                A.append(patterns)
                B.append(A)

            patterns = ['Высокотехнологичная медицинская помощь, не включенная в базовую программу',
                        'Показатели, характеризующие объем государственной услуги',
                        'Нормативные правовые акты, устанавливающие размер платы (цену, тариф) либо порядок ее (его) установления',
                        'Сведения о фактическом достижении показателей, характеризующих объем государственной услуги:',
                        'Часть 2. Сведения о выполняемых работах',
                        'Раздел 2', 'Раздел 3', 'Раздел 4', 'Раздел 5', 'Раздел 6', 'Раздел 7', 'Раздел 8', 'Раздел 9', 'Раздел 10',
                        'Раздел 11', 'Раздел 12', 'Раздел 13', 'Раздел 14', 'Раздел 15', 'Раздел 16', 'Раздел 17', 'Раздел 18',
                        'Раздел 19', 'Раздел 20', 'Руководитель (уполномоченное лицо)']

            root = aho_create_statemachine(patterns)
            aho_find_all(words, root, on_occurence)

        return B

class Page:

    def __init__(self, all_page_matches):
        self.all_page_matches = all_page_matches

    def information_on_current_page(self):

        A = {}

        ## Надо вместо ind вставлять ссылку на док

        for ind, i in enumerate(self.all_page_matches):

            B = []

            if i[1] == 'Высокотехнологичная медицинская помощь, не включенная в базовую программу':

                # Ищем в списке состоящем из номера страницы и ключевого слова
                tro = ind + 1
                tro2 = ind + 2

                # ↑↑↑ Плюсуем к индексам найденного элемента следующие 2, 3 элементы

                try:

                    B.append(self.all_page_matches[tro][0])
                    B.append(self.all_page_matches[tro2][0])
                    A[ind] = B

                except IndexError:
                    B.append(self.all_page_matches[tro][0])
                    B.append(None)
                    A[ind] = B

        # ↓↓↓ Ссылка на документ и страницы где находиться раздел для парсинга
        return A

class ConversionBackend(object):
    def convert(self, pdf_path, png_path):
        # Открываем документ
        doc = fitz.open(pdf_path)
        for page in doc.pages():
            # Переводим страницу в картинку
            pix = page.get_pixmap()
            # Сохраняем
            pix.save(png_path)

class Collect:
    def __init__(self, element_dtf):
        self.element_dtf = element_dtf

    def collecting_element_DataFrame(self):
        # Очищяем датафрейм от переносов и новых строк и пробелов
        arr = self.element_dtf.split('\n')
        ob = " ".join(arr)
        if '/' in ob:
            a = ob.split()
            b = ''.join(a)
            match = re.split("([0-9]+/)", b)
            finish = list(filter(None, match))
            odd = finish[1::2]
            od = finish[::2]
            res = [sub.replace('/', '') for sub in od]
            fin = [a + b for a, b in zip(od, odd)]
            return res
        else:
            a = ob.split()
            b = ''.join(a)
            r = re.sub(r'([А-Я])', r' \1', b).split()
            return r

class Examination:

    def __init__(self, dtf):
        # Загружаем датафрейм
        self.dtf = dtf

    def performance_check(self):
        # проверяем есть ли в 7 столбце ключевое слово ("Процент", "Уникальный номер")
        stock_search = (self.dtf[7].eq('Процент').any()
                        or self.dtf[1].str.contains('Показатель, характеризующий содержание работы').any()
                        or pd.isnull(self.dtf.loc[1]).any()
                        or pd.isnull(self.dtf.loc[2]).any())
        return stock_search

    def performance_check_column_number9(self):
        # Костыль, который надо потом исправить
        # Пусть ищет в столбце слово и потом будем
        # Делать срез либо с 0 строрки, или с 3
        stock_search = (self.dtf[9].str.contains('Значение').any()
                        or self.dtf[9].str.contains('значение').any()
                        or self.dtf[1].eq('Уникальный номер реестровой записи').any())

        if stock_search == False:
            return self.get_quotas().iloc[0:]
        else:
            return self.get_quotas().iloc[4:]

    def string_intro(self):
        # Костыль чтобы достать квоты
        A = []
        for i in self.performance_check_column_number9():
            cl = Collect(i).collecting_element_DataFrame()
            A.append(cl)
        fin = [x for l in A for x in l]
        return fin

    def get_quotas(self):
        # Парсинг квот 10 стобец
        return self.dtf[9]

    def replace_blank_lines(self):
        # Заменяем пустые строчки в датафрейме на NaN
        df2 = self.dtf.loc[:, [1, 2]].replace('', np.nan, regex=True)
        return df2

    def reset_NAN(self):
        # Сброс индекса после удаления строк с NaN
        reset_nan = self.replace_blank_lines().dropna()
        reset_index = reset_nan.reset_index(drop=True)
        return reset_index

    def get_medical_care_profiles(self):
        # Достаем и обрабатываем профили медицинской момощи (первый стобец)
        nominal_column = self.reset_NAN()

        if nominal_column[1].eq('Человек').any()==True:
            # Значит часть таблицы не дорисована и ее надо будет дорабатывать
            return None
        else:
            if len(nominal_column) == 1 or len(nominal_column) == 2:
                return nominal_column.iloc[0]
            else:
            # Надо написать штуку чтобы отправлять список от среза
                return nominal_column.iloc[2:]

    def clean_and_collect(self):
        # Получаем датафрейм
        a = []
        try:
            if type(self.get_medical_care_profiles()) == pd.DataFrame:
                # Проверяем тип, если Датафрейм, то ↓↓↓

                for i in (self.get_medical_care_profiles()):
                    for k in self.get_medical_care_profiles()[i]:
                        cl = Collect(k).collecting_element_DataFrame()
                        a.append(cl)
                return a
        except TypeError:
            pass

        else:
            try:
                # Если тип - pandas.core.series.Series ↓↓↓

                for q in self.get_medical_care_profiles():
                    cl = Collect(q).collecting_element_DataFrame()
                    a.append(cl)
                return a
            except TypeError:
                pass

    def patch(self):

        nominal_column = self.reset_NAN()
        a = []
        if self.dtf[1].str.contains('Группа').any() == False:
            # Проверяем есть ли в первом столбце ключевое слово
            # Чтобы потом сделать срез с самого начала
            shlep = nominal_column.iloc[0:]
            for i in shlep:
                for k in shlep[i]:
                    cl = Collect(k).collecting_element_DataFrame()
                    a.append(cl)
            return a
        else:
            shlep = nominal_column.iloc[0:]
            for i in shlep:
                for k in shlep[i]:
                    cl = Collect(k).collecting_element_DataFrame()
                    a.append(cl)
            return a

class Crutch:

    def __init__(self, list_under):

        self.list_under = list_under

    def crutch_for_lists(self):
        # Делаем костыль и проверяем чтобы спиок после среза
        # превратился в список двумя списками

        A = []
        try:

            if len(self.list_under) == 2:
                # Если все впорядке то возвращаем обычный список ↓↓↓
                return self.list_under
            else:
                # В сосавльных случаях каждый элемент добавляем в сисок
                # и получеться список списков и потом делим ровно на 2

                for i in self.list_under:
                    for k in i:
                        string_p = str(k)
                        A.append(string_p)

                k = sum(tuple(divmod(len(A), 2)))
                c = [A[:k], A[k:]]
                return c

        except TypeError:
            pass

class ReadPdf:
    def __init__(self, _key, _num):
        self._Key = _key
        self._num = _num

    def get_read(self):
        # Открываем для парсинга таблиц
        tables = camelot.read_pdf(self._Key,
                                  backend=ConversionBackend(),
                                  line_scale=40,
                                  pages=str(self._num), )
        return tables

    def replace_file_doc(self):
        new_path = settings.MEDIA_ROOT
        # Открываем для прорисовки недостающих линий и дорисовываем
        doc = fitz.open(self._Key)
        page = doc[int(self._num) - 1]
        shape = page.new_shape()
        shape.draw_line((28, 28), (1300, 28))
        shape.finish(color=(0, 0, 0), fill=(1, 1, 0))
        shape.commit()
        part_2 = self._Key[-4:]
        part_1 = self._Key.split(part_2)
        return doc.save(part_1[0]+'R'+part_2)

class Reformatting:
    def __init__(self, stock_list):
        self.stock_list = stock_list

    def get_stock_list(self):
        main_list = []
        for q in Crutch(self.stock_list.clean_and_collect()).crutch_for_lists():
            main_list.append(q)
        main_list.append(self.stock_list.string_intro())
        if len(main_list[2]) != len(main_list[1] or len(main_list[2]) != len(main_list[0])):
            part_lst = Crutch(self.stock_list.patch()).crutch_for_lists()
            part_lst.append(self.stock_list.string_intro())
            if len(part_lst[0]) != len(part_lst[2]) or len(part_lst[1]) != len(part_lst[2]):
                del part_lst[0][0]
                del part_lst[1][0]
            return part_lst
        return main_list

class Control:

    def __init__(self, dct_number_pages):
        self.dct_number_pages = dct_number_pages

    def list_date(self):
        for key, value in self.dct_number_pages.items():
            final_list = []
            for num in range(value[0] + 1, value[1] + 2):
                intermediate_dict = {}
                try:
                    for i in range(999):
                        tb = ReadPdf(key, num)
                        ex = Examination(tb.get_read()[i].df)
                        try:
                            if ex.performance_check() == False:
                                if ex.clean_and_collect() == None:
                                    print('Надо дорисовывать таблицу')
                                    tb.replace_file_doc()
                                    part_2 = key[-4:]
                                    part_1 = key.split(part_2)
                                    new_key = part_1[0]+'R'+part_2
                                    tb = ReadPdf(new_key, num)
                                    ex = Examination(tb.get_read()[i].df)
                                    tran = Reformatting(ex).get_stock_list()
                                    intermediate_dict[key] = tran
                                else:
                                    tran = Reformatting(ex).get_stock_list()
                                    intermediate_dict[key] = tran
                        except KeyError:
                            """ в 7 столбце не найден стобец """

                except IndexError:
                    """Нет такой информации в таблице, крутим номера таблиц"""
                    final_list.append(intermediate_dict)
            return final_list

print('1:'+str(start_time-time.time()))




