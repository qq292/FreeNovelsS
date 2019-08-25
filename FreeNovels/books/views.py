from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.http import HttpResponse
from django.views.generic.base import View, TemplateView
import json, re, requests
from .models import Source
from urllib.parse import quote
from lxml import etree

# Create your views here.

headers = {
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "cookie": "__cfduid=d1240b10758285a08a37f9ed80f2c4fe21560276635; UM_distinctid=16b47bc0d183a2-0e9cf74bce3f78-9333061-1fa400-16b47bc0d19640; bookid=134128; chapterid=6815295; chaptername=%25u5E8F%253A%25u795E%25u77F3%25u964D%2520%25u5929%25u5730%25u846C; CNZZDATA1257156613=700615596-1560271565-%7C1560276965",
    "upgrade-insecure-requests": "1",
    "cache-control": "max-age=0",
    "accept-language": "zh-CN,zh;q=0.9",
    "accept-encoding": "gzip, deflate, br",

}


def findHtmlCode(getfindpage, getfconstant):  # html编码
    """

    :param getfindpage: 搜索页
    :param getfconstant: 全局常量
    :return:
    """
    encoding = getfindpage.get("findhtmlcode", None)
    if encoding == None:
        encoding = getfconstant.get("htmlcode", "utf-8")
    return encoding


def listToStr(l):  # xpath转str
    try:
        text = l[0].xpath('string(.)').strip()
    except Exception:
        text = l[0]

    # print(["listToStr",text])
    return text


def by_book_find(request, url, getfindpage, getfconstant, adddict, findFrist=None):
    # 有findFrist则使用findFrist 不用再次请求网页
    if findFrist:
        text = findFrist
    else:
        html = requests.get(url=url, headers=headers, verify=getfconstant.get("requests_verify", True), timeout=10)
        html.encoding = findHtmlCode(getfindpage, getfconstant)
        text = html.text

    dom_tree = etree.HTML(text)
    xpath_root = dom_tree.xpath(getfindpage.get("book_xpath_root"))
    print(len(xpath_root))
    print(["by_book_find-搜索页URL", "第一次搜索" if findFrist else url])
    # print(getfindpage.get("book_xpath_root"))
    # print(html.text)
    book_lists = [adddict]  # {'sub_page':sub_page}
    for mxpath in xpath_root:
        try:
            book_url = mxpath.xpath(getfindpage.get('book_url'))[0]  # 小说URL
            # print(book_url)
            book_title = listToStr(mxpath.xpath(getfindpage.get('book_title')))  # 小说名
            # print(book_title)
            book_author = listToStr(mxpath.xpath(getfindpage.get('book_author')))  # 小说作者
            # print(book_author)
            try:
                book_img = mxpath.xpath(getfindpage.get('book_img'))[0]  # 小说图片
            except Exception:
                book_img = "/static/img/nocover.jpg"
            try:
                book_brief = listToStr(mxpath.xpath(getfindpage.get('book_brief')))  # 小说简介
            except Exception:
                book_brief = "<i style='color:red'>暂无小说简介</i>"

            book_lists.append(
                {'book_img': book_img, 'book_url': book_url, 'book_title': book_title, 'book_author': book_author,
                 'book_brief': book_brief})

        except Exception as e:
            print(['by_book_find', e.args])

    response_json = json.dumps({str(a): b for a, b in enumerate(book_lists)})

    return response_json


class DbMixin(object):
    db_name = None

    def get_db_queryset(self):
        if self.db_name is not None:
            return self.db_name.objects.all()
        else:
            raise Exception("db_name不能为空")

    def get_db(self, request):
        select_id = request.POST.get('selectid', None)
        query_db = self.get_db_queryset()

        if select_id:
            # 返回一个 {字段：字段值} 的dict(不包涵["id","describe"]字段)
            db_filter = query_db.filter(id=select_id).first()
            db_dict = {field.name: eval(getattr(db_filter, field.name)) for field in db_filter._meta.get_fields() if
                       field.name not in ["id", "describe"]}

            return db_dict

        else:
            return {'query_db': query_db}


class PostMixin(DbMixin):
    """
    分发post请求
    """
    mark = ['loadsource',  # 加载书源
            "add_script",  # 加载书源定义的js脚本
            'find',  # 搜索
            'source',  # 保存书源
            'up_page',  # 上一页（搜索翻页）
            'load_page',  # 下一页（搜索翻页）
            'jump_page',  # 跳到一页（搜索翻页）
            'book_urls',  # 章节url
            'content_url']  # 正文url

    def post(self, request):
        try:
            post_mark = request.POST.get('mark', None)
            if post_mark in self.mark:
                self_name = getattr(self, post_mark, self)
                if hasattr(self, self_name.__name__) and not hasattr(self, "MainPage"):
                    return HttpResponse(self_name(request, **self.get_db(request)))
                else:
                    return HttpResponse(json.dumps({"m": "服务器找不到处理视图"}))
            else:
                return HttpResponse(json.dumps({"m": "mark参数错误"}))
        except Exception as e:
            print(e.args)


class MainPage(PostMixin, TemplateView):
    template_name = "books/mainpage.html"
    db_name = Source

    def get_context_data(self, **kwargs):  # 为get请求 添加参数
        context = super(MainPage, self).get_context_data(**kwargs)
        context["is_windows"] = "1" if "Windows" in context['view'].request.META.get('HTTP_USER_AGENT', None) else "0"
        return context

    @staticmethod
    def loadsource(request, **kwargs):  # 加载源
        sources = []
        db = kwargs.get("query_db")  # Source.objects.all()
        for i in db:
            l = {"describe": i.describe, "id": i.id}
            sources.append(l)
        rejson = json.dumps({str(a): b for a, b in enumerate(sources)})

        return rejson

    @staticmethod
    def add_script(request, **kwargs):  # 加载书源定义的js脚本

        getfindpage = kwargs.get('findpage')
        getchapterpage = kwargs.get('chapterpage')
        book_url_js = "<script>\nfunction data_url_js(book_url){0}\n{1}\n{2}\n</script>".format("{",
                                                                                                getfindpage.get(
                                                                                                    "book_url_js"),
                                                                                                "}")
        chapter_url_js = "<script>\nfunction chapter_url_js(chapter_url,book_url){0}\n{1}\n{2}\n</script>".format(
            "{", getchapterpage.get("chapter_url_js"), "}")
        return json.dumps({"book_url_js": mark_safe(book_url_js), "chapter_url_js": mark_safe(chapter_url_js)})

    @staticmethod
    def find(request, **kwargs):

        getfindpage = kwargs.get('findpage')
        getfconstant = kwargs.get('constant')

        title = quote(request.POST.get('title', None).encode(getfconstant.get("urlcode", "utf-8")))
        find_url = getfindpage['furl'] + title
        print(["find-搜索的URL", find_url])
        html = requests.get(url=find_url, headers=headers, verify=getfconstant.get("requests_verify", True),
                            timeout=10)
        # 指定html的编码
        html.encoding = findHtmlCode(getfindpage, getfconstant)
        dom_tree = etree.HTML(html.text)
        sub_url = getfindpage.get("sub_url", None).replace(r"*title*", title)
        sub_page = getfindpage.get("sub_page", None)
        sub_page_split = eval(getfindpage.get("sub_page_split", None))

        # 解析 搜索的小说页数
        if sub_page:
            try:
                sub_page = dom_tree.xpath(sub_page)[0]
                sub_page = re.split(sub_page_split[0], sub_page)[int(sub_page_split[1])]
            except Exception as e:
                print(['find-页码解析错误', e.args])
                sub_page = "1"
        else:
            sub_page = "1"
        print(["sub_page-小说页码", sub_page])

        response_json = by_book_find(request, None, getfindpage, getfconstant,
                                     {'sub_page': sub_page, "sub_url": sub_url}, findFrist=html.text)

        return response_json

    @staticmethod
    def source(request, **kwargs):  # 保存源
        return HttpResponse(json.dumps({"m": "不开放此功能"}))
        describe = request.POST.get('describe', None)
        constant = request.POST.get('constant', None)
        findpage = request.POST.get('findpage', None)
        chapterpage = request.POST.get('chapterpage', None)
        contentpage = request.POST.get('contentpage', None)
        print(['-------------', findpage, chapterpage, contentpage])
        try:
            Source.objects.create(describe=describe, constant=constant, findpage=findpage, chapterpage=chapterpage,
                                  contentpage=contentpage).save()
        except Exception as e:
            rejson = {'m': str(e.args)}
        else:
            rejson = {'m': '保存成功'}
        return json.dumps(rejson)

    @staticmethod
    def up_page(request, **kwargs):  # 到上一页（搜索页）
        getfindpage = kwargs.get('findpage')
        getfconstant = kwargs.get('constant')
        current_page = request.POST.get("current_page", None)
        data_sub_url = request.POST.get("data_sub_url", None)
        sub_url = '{0}{1}'.format(data_sub_url, int(current_page) - 1)
        response_json = by_book_find(request, sub_url, getfindpage, getfconstant,
                                     {'current_page': str(int(current_page) - 1)})

        return response_json

    @staticmethod
    def load_page(request, **kwargs):  # 到下一页（搜索页）

        getfindpage = kwargs.get('findpage')
        getfconstant = kwargs.get('constant')
        current_page = request.POST.get("current_page", None)
        data_sub_url = request.POST.get("data_sub_url", None)
        sub_url = '{0}{1}'.format(data_sub_url, int(current_page) + 1)

        response_json = by_book_find(request, sub_url, getfindpage, getfconstant,
                                     {'current_page': str(int(current_page) + 1)})

        return response_json

    @staticmethod
    def jump_page(request, **kwargs):  # 跳到某一页（搜索页）
        getfindpage = kwargs.get('findpage')
        getfconstant = kwargs.get('constant')
        jump_page = request.POST.get("jump_page", None)
        data_sub_url = request.POST.get("data_sub_url", None)
        sub_url = '{0}{1}'.format(data_sub_url, int(jump_page))

        response_json = by_book_find(request, sub_url, getfindpage, getfconstant,
                                     {'current_page': jump_page})

        return response_json

    @staticmethod
    def book_urls(request, **kwargs):  # 到章节页
        getfconstant = kwargs.get('constant')
        getchapterpage = kwargs.get('chapterpage')
        book_url = request.POST.get("book_url")

        if "http" not in book_url:
            book_url = getfconstant.get("host") + book_url
        print(["book_url", book_url])

        html = requests.get(book_url, headers=headers, verify=getfconstant.get("requests_verify", True))
        html.encoding = getfconstant.get("htmlcode", "utf-8")
        dom_tree = etree.HTML(html.text)

        # print(html.text)

        chapter_xpath_root = dom_tree.xpath(getchapterpage.get("chapter_xpath_root"))
        print(len(chapter_xpath_root))
        chapter_list = []
        for mchapter in chapter_xpath_root:
            chapter_url = listToStr(mchapter.xpath(getchapterpage.get("chapter_url")))
            chapter_title = listToStr(mchapter.xpath(getchapterpage.get("chapter_title")))
            chapter_list.append({"chapter_url": chapter_url, "chapter_title": chapter_title})

        response_json = json.dumps({str(a): b for a, b in enumerate(chapter_list)})
        return json.dumps(response_json)

    @staticmethod
    def content_url(request, **kwargs):  # 到正文页
        getfconstant = kwargs.get('constant')
        getcontent = kwargs.get('contentpage')
        content_url = request.POST.get("content_url")

        if "http" not in content_url:
            content_url = getfconstant.get("host") + content_url

        print(["正文url", content_url])

        html = requests.get(content_url, headers=headers, verify=getfconstant.get("requests_verify", True))
        html.encoding = getfconstant.get("htmlcode", "utf-8")
        dom_tree = etree.HTML(html.text)
        content = dom_tree.xpath(getcontent.get("content"))[0]
        content = etree.tostring(content, method='html')
        # print(content_url)

        return content
