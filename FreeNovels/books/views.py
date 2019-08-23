from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.http import HttpResponse
from django.views.generic.base import View
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
    print(["by_book_find-搜索页URL","第一次搜索" if findFrist else url])
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
                book_img="/static/img/nocover.jpg"
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


class Mainpage(View):
    def get(self, request):
        agent = request.META.get('HTTP_USER_AGENT', None)
        is_windows = "1" if "Windows" in agent else "0"

        return render(request, 'books/mainpage.html', {"is_windows": is_windows})

    def post(self, request):
        mark = request.POST.get('mark', 'no')
        sources = []
        if mark == "loadsource": #加载书源
            db = Source.objects.all()
            for i in db:
                l = {"describe": i.describe, "id": i.id}
                sources.append(l)
            rejson = json.dumps({str(a): b for a, b in enumerate(sources)})

            return HttpResponse(rejson)
        elif mark == "add_script":  # 加载书源定义的js脚本
            fdb = Source.objects.get(id=request.POST.get("selectid"))
            getfindpage = eval(r"{0}".format(fdb.findpage))
            getchapterpage = eval(r"{0}".format(fdb.chapterpage))
            book_url_js = "<script>\nfunction data_url_js(book_url){0}\n{1}\n{2}\n</script>".format("{",
                                                                                                    getfindpage.get(
                                                                                                        "book_url_js"),
                                                                                                    "}")
            chapter_url_js = "<script>\nfunction chapter_url_js(chapter_url,book_url){0}\n{1}\n{2}\n</script>".format(
                "{", getchapterpage.get("chapter_url_js"), "}")
            return HttpResponse(
                json.dumps({"book_url_js": mark_safe(book_url_js), "chapter_url_js": mark_safe(chapter_url_js)}))

        elif mark == "find":  # 搜索
            fdb = Source.objects.get(id=request.POST.get("selectid"))
            getfindpage = eval(r"{0}".format(fdb.findpage))
            getfconstant = eval(r"{0}".format(fdb.constant))
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

            return HttpResponse(response_json)

        elif mark == "source":  # 保存源
            return HttpResponse(json.dumps({"m":"不开放此功能"}))  # 前端写书源保存到数据库，注释这行代码即可使用。
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
            return HttpResponse(json.dumps(rejson))

        elif mark == "up_page":  # 到上一页（搜索页）
            fdb = Source.objects.get(id=request.POST.get("selectid"))
            getfindpage = eval(r"{0}".format(fdb.findpage))
            getfconstant = eval(r"{0}".format(fdb.constant))
            current_page = request.POST.get("current_page", None)
            data_sub_url = request.POST.get("data_sub_url", None)
            sub_url = '{0}{1}'.format(data_sub_url, int(current_page) - 1)
            response_json = by_book_find(request, sub_url, getfindpage, getfconstant,
                                         {'current_page': str(int(current_page) - 1)})

            return HttpResponse(response_json)

        elif mark == "load_page":  # 到下一页（搜索页）
            fdb = Source.objects.get(id=request.POST.get("selectid"))
            getfindpage = eval(r"{0}".format(fdb.findpage))
            getfconstant = eval(r"{0}".format(fdb.constant))
            current_page = request.POST.get("current_page", None)
            data_sub_url = request.POST.get("data_sub_url", None)
            sub_url = '{0}{1}'.format(data_sub_url, int(current_page) + 1)

            response_json = by_book_find(request, sub_url, getfindpage, getfconstant,
                                         {'current_page': str(int(current_page) + 1)})

            return HttpResponse(response_json)

        elif mark == "jump_page":  # 跳到某一页（搜索页）
            fdb = Source.objects.get(id=request.POST.get("selectid"))
            getfindpage = eval(r"{0}".format(fdb.findpage))
            getfconstant = eval(r"{0}".format(fdb.constant))
            jump_page = request.POST.get("jump_page", None)
            data_sub_url = request.POST.get("data_sub_url", None)
            sub_url = '{0}{1}'.format(data_sub_url, int(jump_page))

            response_json = by_book_find(request, sub_url, getfindpage, getfconstant,
                                         {'current_page': jump_page})

            return HttpResponse(response_json)

        elif mark == "book_urls":  # 到章节页
            fdb = Source.objects.get(id=request.POST.get("selectid"))
            getfconstant = eval(r"{0}".format(fdb.constant))
            getchapterpage = eval(r"{0}".format(fdb.chapterpage))
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
            return HttpResponse(json.dumps(response_json))

        elif mark == "content_url":  # 到正文页
            fdb = Source.objects.get(id=request.POST.get("selectid"))
            getfconstant = eval(r"{0}".format(fdb.constant))
            getcontent = eval(r"{0}".format(fdb.contentpage))
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

            return HttpResponse(content)
        else:
            HttpResponse(json.dumps({"Error": " 你提交的mark参数不对！"}))
