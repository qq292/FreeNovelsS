$(document).ready(function () {

    //兼容移动端
    var div_padding,div_width, img_width, img_height, span_font_size, line_clamp,chdata_div_width,shelf_img_width,shelf_img_height,shelf_img_margin,shelf_font_size;
    if ($("body").attr("is_windows") == "0") {
        div_padding=" 10px 0px 0px";
        div_width = "100%";
        img_width = "76px";
        img_height = "110px";
        span_font_size = "12px";
        line_clamp = "3";
        chdata_div_width = "100%";
        shelf_img_width="90px";
        shelf_img_height="130px";
        shelf_img_margin="14px 10px;";
        shelf_font_size="12px";
    } else {
        div_padding=" 10px 20px 0px 0px";
        div_width = "555px";
        img_width = "120px";
        img_height = "160px";
        span_font_size = "14px";
        line_clamp = "6";
        chdata_div_width = "350px";
        shelf_img_width="140px";
        shelf_img_height="200px";
        shelf_img_margin="30px 20px;";
        shelf_font_size="16px"
    }
    //初始化书源模板
    function init(){
        $("textarea[name='describe']").val(`
对书源的描述
subXpath不要用属性选择./div[@class='xxx']
没有book_img 必须指定为None

        `);
        $("textarea[name='constant']").val(`
{
"urlcode" : "utf-8",
"htmlcode" : "utf-8",
"host" : "https://www.qidian.com",
 "requests_verify" : True,
}`);
        $("textarea[name='findpage']").val(
        `
{
"findhtmlcode" : "utf-8", # 可以忽略，将使用全局htmlcode
"furl" : "https://www.qidian.com/search?kw=",
"book_xpath_root":"//div[@id='result-list']//li",
"book_img":"./div[1]/a/img/@src",
"book_url":'./div[1]/a/@href',
"book_url_js":'''

return "https:"+book_url+"#Catalog"
''',
"book_title":'./div[2]/h4/a',
"book_author":'./div[2]/p[1]/a[1]/text()',
"book_brief":'./div[2]/p[2]',

"sub_url":'https://www.biqudao.com/searchbook.php?keyword=*title*&page=',
"sub_page":'//em[@id="pagestats"]/text()',
"sub_page_split":'("/","1")',
}`);
        $("textarea[name='chapterpage']").val(
        `
{
"chapter_xpath_root":"//ul[@class='cf']/li",
"chapter_url":"./a/@href",
"chapter_url_js":'''

return "https:"+chapter_url
''',
"chapter_title":"./a/text()"
}`);
        $("textarea[name='contentpage']").val(
        `
{
"content":"//div[@class='read-content j_readContent']"
}`);
        $("textarea:eq(1)").css({"height": "174px"});
        $("textarea:eq(2)").css({"height": "434px"});
        $("textarea:eq(3)").css({"height": "234px"});
        $("textarea:eq(4)").css({"height": "114px"});

    }
    init();
    //应用背景色
    function getBookColor(){
        var bookcol=window.localStorage.getItem("bookColor");
        if(bookcol!=null){
            $("#dli8").removeClass($("#dli8").attr("data-remove-class")).attr({"data-remove-class":bookcol});
            $("#dli8").addClass(bookcol);
        }

    }
    getBookColor();





    //阅读背景色
    $("#by_set p").bind("click",function () {
        var storage=window.localStorage;
        var mthis=this;

        layer.confirm('把  【'+$(mthis).text()+'】  设置为背景色？', {
            btn: ['确认', '取消']
        }, function (index, layero) {

            storage.setItem("bookColor",$(mthis).attr("class"));
            getBookColor();
            layer.msg("设置成功")

        }, function (index) {
            // layer.msg("2")
        });

    });


    //加载书架
    function sby_shelf() {
        $("#by_shelf").empty();
        var storage=window.localStorage;
        var by_json,shelf_html;
        if (storage.length != 0) {
            for (var i = 0; i < storage.length; i++) {
                var keys=storage.key(i);
                if(keys!="bookColor"){
                    var obj = storage.getItem(keys);
                    by_json = $.parseJSON(obj);
                    shelf_html = `
                <div style="float: left;width: auto;margin:` + shelf_img_margin + `">
                    <a href="javascript:;" id="` + by_json['shelf_url'] + by_json['shelf_id'] + `" data-shelf-url="` + by_json['shelf_url'] + `" data-shelf-id="` + by_json['shelf_id'] + `" data-shelf-chapter="` + by_json['shelf_chapter'] + `"><img class="book-img-style" style="width: ` + shelf_img_width + `;height: ` + shelf_img_height + `"  src="` + by_json['shelf_img'] + `"  onerror="$(this).attr('src', '/static/img/nocover.jpg')"></a>
                    
                    <strong style="margin-top: 4px;font-size: ` + shelf_font_size + `;width: ` + shelf_img_width + `;height: 48px;text-align: center;overflow: hidden;text-overflow: ellipsis;display: -webkit-box;-webkit-line-clamp: 3;-webkit-box-orient: vertical;">` + by_json['shelf_title'] + `</strong>
                </div>
            
                `;
                    $("#by_shelf").append(shelf_html);
                }
            }

            //书架单击事件  从书架加载小说章节
            var TimeFn = null;
            $("a[data-shelf-url]").click(function () {
                var my_this= this;
                clearTimeout(TimeFn);
                TimeFn = setTimeout(function () {
                    $("a[data-shelf-url]").next().css({"color":"#000000"});
                    $(my_this).next().css({"color": "#009688"});
                    var data_shelf_url = $(my_this).attr("data-shelf-url");
                    var data_shelf_id = $(my_this).attr("data-shelf-id");
                    fun_chapter(data_shelf_url, data_shelf_id);
                }, 300);
            });
            //书架双击事件 从书架移除小说
            $("a[data-shelf-url]").dblclick( function(){
                clearTimeout(TimeFn);
                delate_book(this);

            });
        }

    }
    sby_shelf();
    //删除小说
    function delate_book(this_del) {//传递this
        var del_title=$(this_del).next().text();//data-shelf-url
        var storage=window.localStorage;
        var del_json=$(this_del).attr("data-shelf-url")+$(this_del).attr("data-shelf-id");
        var to_del=storage.getItem(del_json);
        layer.confirm('把  【'+del_title+'】  从书架移除？', {
            btn: ['确认', '取消']
        }, function (index, layero) {
            if(to_del!=null){
                storage.removeItem(del_json);
                sby_shelf();
                layer.msg("移除成功")
            }else{
                sby_shelf();
                layer.msg("移除失败，小说不存在！")
            }

        }, function (index) {
            // layer.msg("2")
        });
    }
    
    
    
    //加载小说正文
    function load_content(content_url,selectid,contentTitle) {
        //"div[class='layui-tab-content']"
        var load_chapter_url = layer.load(2, {time: 10 * 1000});//加载中
        $.post(url = '', data = {
            "mark": "content_url",
            "content_url": content_url,
            "selectid": selectid,

        }, function (data_content, status) {
            $("#content_head").text(contentTitle);
            $("#contents").empty();
            $("#contents").append(data_content);

            layui.use('element', function () {
                var element = layui.element;
                element.tabChange('docDemoTabBrief', 'li8');
                //如果是收藏的小说就切换到上次看到章节正文 并且滚动到上次的观看位置
                var storage = window.localStorage;
                var my_shelf = storage.getItem($("body").attr("is_shelf"));
                var thsScroll;
                if (my_shelf != null) {//书架
                    var parseJs = $.parseJSON(my_shelf);
                    thsScroll = parseJs["shelf_scroll"];
                    if (thsScroll == "0") {
                        $('html,body').animate({scrollTop: $("div[class='layui-tab-content']").offset().top}, 1);
                    } else {
                        $(document).scrollTop(thsScroll);
                    }
                }else{//非书架
                    $('html,body').animate({scrollTop: $("div[class='layui-tab-content']").offset().top}, 1);
                }



                layer.close(load_chapter_url); //关闭加载中的图标
            });
        }, dataType = 'html');
    }
    //加载章节
    function fun_chapter(book_url, selectid) {//url 和 源
        var load_data_url = layer.load(2, {time: 10 * 1000});//加载中
        var mbook_url=book_url;
        var funcPost = function () {
            $.post(url = '', data = {
                "mark": "book_urls",
                "book_url": book_url,
                "selectid": selectid
            }, function (chdata, status) {
                $("#chapters").empty();
                $("body").attr({"is_shelf": book_url + selectid});//是否为已收藏的小说
                var jdata = JSON.parse(chdata);
                for (var s in jdata) {
                    var chaterhtml = `
                         <div  style="float: left; width: ` + chdata_div_width + `;margin: 5px 0px;font-size: 18px">

                            <a id="` + s + `" href="javascript:;" chapter-url="` + jdata[s]['chapter_url'] + `" book_url_sub="`+book_url+`">` + jdata[s]['chapter_title'] + `</a>

                         </div>`;

                    $("#chapters").append(chaterhtml);
                }
                //chapter-url按钮点击 转到正文页 章节标签被点击
                $("a[chapter-url]").bind('click', function () {
                    $("#chapters a").css({"color":"#000000"});
                    $(this).css({"color": "#009688"});
                    var storage = window.localStorage;
                    var my_shelf = $("body").attr("is_shelf");
                    var my_storage = storage.getItem(my_shelf);

                    $("#content_head").attr({"data-content-id": $(this).attr("id")});
                    //从书架点击不使用chapter_url_js函数
                    console.log(mbook_url);
                    //保存小说观看的位置
                    if (my_storage != null) {
                        var my_json = $.parseJSON(my_storage);
                        my_json["shelf_chapter"] = $(this).attr("id");
                        storage.setItem(my_shelf, JSON.stringify(my_json));
                        if ($(".layui-this[lay-id='li7']").length != 0) {//在章节页面点击
                            saveScrollTop(0);
                        }

                    }
                    load_content(chapter_url_js($(this).attr("chapter-url"),$(this).attr("book_url_sub")), selectid,"《" + $(this).text() + "》");



                });
                // 切换到指定章节的小说正文
                layui.use('element', function () {
                    var element = layui.element;
                    var storage = window.localStorage;
                    var my_shelf = storage.getItem($("body").attr("is_shelf"));
                    var mm_id;
                    //如果是收藏的小说就切换到上次看到章节正文，否则切换到小说第一章正文
                    if (my_shelf != null) {
                        var parseJs=$.parseJSON(my_shelf);
                        mm_id = parseJs["shelf_chapter"];
                    } else {
                        mm_id = "0"
                    }
                    $("#" + mm_id).trigger("click");//加载小说正文
                    layer.close(load_data_url); //关闭加载中的图标
                });
            }, dataType = 'json')
        };
        add_script(selectid,funcPost);


    }
    //加载小说搜索页
    function book_style(data) {
        $("#find_books").empty();
        $("#chapters").empty();
        $("#contents").empty();

        for (var i in data) {
            if (i != "0") {
                var fbooks =
                    `<div style="padding:`+div_padding+`;float: left;width:`+div_width+`;">
                        <div style="float: left;width: 25%;"  >
                            <img class="book-img-style" src="` + data[i]['book_img'] + `" width=`+img_width+` height=`+img_height+` onerror="$(this).attr('src', '/static/img/nocover.jpg')">
                        </div>
                      
                        <div style="float: left;width: 75%;">
                        <div >
                            <a href="javascript:;" data-url="` + data[i]['book_url'] + `" style="color: #009688"><strong style="float: left;overflow: hidden;text-overflow: ellipsis;display: -webkit-box;-webkit-line-clamp: 1;width: 73%;-webkit-box-orient: vertical;">` + data[i]['book_title'] + `</strong></a>
                            <a style="float: right;width: 26%" class="shelfs" href="javascript:;" data-shelf-img="`+ data[i]['book_img'] +`"><span  class="layui-badge layui-bg-gray" style="float: right;margin-left: 10px;"><i style="font-size: 10px;" class="layui-icon layui-icon-add-1"> 书架 </i></span></a><br>
                            <span style="float: left;overflow: hidden;text-overflow: ellipsis;display: -webkit-box;-webkit-line-clamp: 1;width: 100%;-webkit-box-orient: vertical;">作者：` + data[i]['book_author'] + `</span><br>
                            <span style="margin-top: 10px; font-size: `+span_font_size+`; color: #807272;overflow: hidden;text-overflow: ellipsis;display: -webkit-box;-webkit-line-clamp: `+line_clamp+`;-webkit-box-orient: vertical;">` + data[i]['book_brief'] + `</span>
                        </div>
                        </div>
                     </div>`;

                $("#find_books").append(fbooks);
            }
        }
        //添加到书架按钮点击事件
        $('.shelfs').bind('click', function () {
            var storage=window.localStorage;
            var shelf_url=data_url_js($(this).siblings("a[data-url]").attr("data-url"));
            var shelf_title=$(this).siblings("a[data-url]").find("strong:first").text();
            var shelf_img=$(this).attr("data-shelf-img");
            var shelf_id=$("#selectsource").attr("select-id");
            var shelf_chapter="0";
            var shelf_scroll="0";
            if(storage.getItem(shelf_url+shelf_id) == null){
                var json_shelf=`{"shelf_url":"`+shelf_url+`","shelf_title":"`+$.trim(shelf_title)+`","shelf_img":"`+shelf_img+`","shelf_id":"`+shelf_id+`","shelf_chapter":"`+shelf_chapter+`","shelf_scroll":"`+shelf_scroll+`"}`;
                storage.setItem(shelf_url+shelf_id,json_shelf);
                sby_shelf();
                layer.msg("添加到书架成功！");
            }else{
                layer.msg("请不要重复添加到书架");
            }
        });

        //搜索data-url点击 加载章节
        $("a[data-url]").bind('click',function () {
            // alert(data_url($(this).attr("data-url")));

            $(this).css({"color":"#2F4056"});
            fun_chapter(data_url_js($(this).attr("data-url")),$("#selectsource").attr("select-id"))
        })

    }

    //选择源
    $.post(url = '', data = {"mark": "loadsource",}, function (data, status) {
        for (var i in data) {
            $("#trdli1").append(`<tr data-id="` + data[i]['id'] + `" data-describe="` + data[i]['describe'] + `">
                                <td>` + data[i]['id'] + `</td>
                                <td>` + data[i]['describe'] + `</td>
                                
                            </tr>`);
            $("tr[data-id='" + data[i]['id'] + "']").bind('click', function () {
                //layer.msg($(this).attr("data-id"));
                $("#find_books").empty();
                $("#chapters").empty();
                $("#contents").empty();
                $("#selectsource").attr({"select-id": $(this).attr("data-id")}).text("当前使用的源：『" + $(this).attr("data-describe") + "』ID：" + $(this).attr("data-id"))
            })
        }

    }, dataType = 'json');

    //重置书源按钮单击事件
    $("#reinit").bind('click', function () {
        init();

    });

    //保存书源按钮单击事件
    $("#source").bind('click', function () {//保存源
        var describe = $("textarea[name='describe']").val();
        var constant = $("textarea[name='constant']").val();
        var findpage = $("textarea[name='findpage']").val();
        var chapterpage = $("textarea[name='chapterpage']").val();
        var contentpage = $("textarea[name='contentpage']").val();
        $.post(url = '', data = {
            "mark": "source",
            "describe": describe,
            "constant": constant,
            "findpage": findpage,
            "chapterpage": chapterpage,
            "contentpage": contentpage
        }, function (data, status) {
            layer.msg(data['m']);
        }, dataType = 'json')
    });
    //渲染js 两个解析url的js脚本
    function add_script(selectid,func) {
        $.post(url = '', data = {
                "mark": "add_script",
                'selectid': selectid,
            }, function (data, status) {
                var docum_js= $("#javascript");
                docum_js.empty();
                docum_js.append(data["book_url_js"]);
                docum_js.append(data["chapter_url_js"]);
                func();
            }, dataType = 'json');

    }
    //搜索小说按钮单击事件
    $("#find").bind('click', function () {//搜索小说
        if($("#selectsource").text()=="**请选择一个源**"){
            layer.msg('请选择源');
        }else{
            var load_find = layer.load(2, {time: 10 * 1000});//加载中
            var selectsource=$("#selectsource").attr("select-id");
            var funcPost = function () {
                $.post(url = '', data = { //搜索小说
                    "mark": "find",
                    'title': $("#title").val(),
                    "selectid": selectsource
                }, function (data, status) {
                    $("#sub_page").text(data["0"]["sub_page"]);//总页数
                    $("#current_page").text("1");//当前页
                    $("#find").attr({"data-sub-url": data["0"]["sub_url"]});//子url
                    book_style(data);//加载bookhtml
                    layui.use('element', function () {
                        var element = layui.element;
                        element.tabChange('docDemoTabBrief', 'li6');
                        layer.close(load_find); //关闭加载中的图标
                    });
                }, dataType = 'json')
            };
             add_script(selectsource,funcPost);//先获取js脚本 再搜索小说
        }
    });

    $("#up_page").bind('click', function () {//上一页
        var var_current_page = $("#current_page").text();
        if (var_current_page != "1") {
            var up_page = layer.load(2, {time: 10 * 1000});//加载中
            $.post(url = '', data = {
                "mark": "up_page",
                'current_page': var_current_page,
                "data_sub_url": $("#find").attr("data-sub-url"),
                "selectid": $("#selectsource").attr("select-id")
            }, function (data, status) {
                $("#current_page").text(data["0"]["current_page"]);//当前页 Number
                book_style(data);//加载bookhtml
                layer.close(up_page);

            }, dataType = 'json')
        } else {
            layer.msg('已经是第一页');
        }
    });

    $("#load_page").bind('click', function () {//下一页
        var var_current_page = $("#current_page").text();
        if (var_current_page != $("#sub_page").text()) {
            var load_page = layer.load(2, {time: 10 * 1000});//加载中
            $.post(url = '', data = {
                "mark": "load_page",
                'current_page': var_current_page,
                "data_sub_url": $("#find").attr("data-sub-url"),
                "selectid": $("#selectsource").attr("select-id")
            }, function (data, status) {
                $("#current_page").text(data["0"]["current_page"]);//当前页 Number
                book_style(data);//加载bookhtml
                layer.close(load_page);
            }, dataType = 'json')
        } else {
            layer.msg('已经是最后一页');
        }
    });
    // Jump
    $("#current_input").bind('click', function () {//跳转页

        var var_jump_page = $("#jump_page").val();
        var var_sub_page = $("#sub_page").text();
        if (parseInt(var_jump_page) <= parseInt(var_sub_page) && parseInt(var_jump_page) > 0) {
            var current_input = layer.load(2, {time: 10 * 1000});//加载中
            $.post(url = '', data = {
                "mark": "jump_page",
                'jump_page': var_jump_page,
                "data_sub_url": $("#find").attr("data-sub-url"),
                "selectid": $("#selectsource").attr("select-id")
            }, function (data, status) {
                $("#current_page").text(data["0"]["current_page"]);//当前页 Number
                book_style(data);//加载bookhtml
                layer.close(current_input);
            }, dataType = 'json')
        } else {
            layer.msg('页码超出范围');
        }
    });
    //目录被点击
    $("#catalog_chapter").bind('click',function () {
        layui.use('element', function () {
            var element = layui.element;
            element.tabChange('docDemoTabBrief', 'li7');
            $('html,body').animate({scrollTop: $("#"+$("#content_head").attr("data-content-id")).offset().top-$(window).height()/2}, 1);
        });
    });
    //上一章被点击
    $("#up_chapter").bind('click',function () {
        var up_id=String(parseInt($("#content_head").attr("data-content-id"))-1);
        saveScrollTop(0);
        $("#"+up_id).trigger("click")
    });
    //下一章被点击
    $("#load_chapter").bind('click',function () {
        var up_id=String(parseInt($("#content_head").attr("data-content-id"))+1);
        saveScrollTop(0);
        $("#"+up_id).trigger("click")
    });
    //保存滚动条位置
    function saveScrollTop(topRags){
        var storage = window.localStorage;
        var my_shelf = $("body").attr("is_shelf");
        var my_storage = storage.getItem(my_shelf);
        //保存小说观看的  滚动条位置
        if (my_storage != null) {
            var my_json = $.parseJSON(my_storage);
            my_json["shelf_scroll"] = topRags;
            storage.setItem(my_shelf, JSON.stringify(my_json));
    }}

    //滚动条 滚动事件
    $(document).scroll(function () {
        var ths = $(".layui-this[lay-id='li8']");
        if (ths.length != 0) {
            $("#dli8").attr("save-scrolltop",$(document).scrollTop());
            saveScrollTop($(document).scrollTop());
        }
    })


});