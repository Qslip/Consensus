import random

from django.shortcuts import render, redirect
from microblog.wb_spider import WbSpider, MyThread
from microblog.blog_analysis import Analyze, Matlib
from microblog.models import MicroBlog, SpecialSubject
from django.db.models import Q


# Create your views here.


def index(request):
    random_list = random.sample(range(0, 50), 3)
    res_list = list()
    thread_pool = list()
    a = WbSpider()
    print(random_list)
    request.session['index'] = random_list
    for i in random_list:
        t = MyThread(a.get_blog_list, args=(i,))
        thread_pool.append(t)

    for t in thread_pool:
        t.start()

    for t in thread_pool:
        t.join()
        # print(t.get_result()[0:2])
        # res_list.extend(t.get_result())

    for t in thread_pool:
        res_list.extend(t.get_result())
    context = {'res_list': res_list}
    n = 0
    for i in res_list:
        p_url = 'bootstrap/img/content/news%s.jpg' % n
        i['img_url'] = p_url
        n += 1
        if n == 10:
            n = 0
    return render(request, 'microblog/index.html', context)


def save_index(request):
    if request.method == 'POST':
        req_info = request.POST
        res_list = req_info.get('res_list', None)
        if res_list:  # 如果获取到请求带入的多个博客列表
            print(1111111)
            try:  # 将 str 转换成 list
                res_list = eval(res_list)
            except Exception as e:
                print(e)
                res_list = None
            if res_list:
                print(22222222)
                wb_obj = WbSpider()  # 保存多个微博到数据库
                result_info = wb_obj.save_data_sql(micro_blog_list=res_list)
                if result_info == 'success':
                    print('OK')
                    context = {'success': '保存数据库成功！'}
                    return render(request, 'microblog/404.html', context)

        context = {'error': '保存失败，请重试！'}
        return render(request, 'microblog/404.html', context)

    elif request.method == 'GET':
        return redirect('microblog:microblog_index')


def subject_blog(request, subject_name):
    wb_obj = WbSpider()
    subject_json = wb_obj.get_subject_json(subject_name=subject_name)  # 获取该专题下的json数据
    if not subject_json:
        context = {'error': '未找到该专题相关的微博，请重试！', 'subject_name': subject_name}
        return render(request, 'microblog/subject.html', context)

    subject_dict = wb_obj.parse_subject_json(subject_json=subject_json)  # 解析专题的json数据
    context = {'subject_dict': subject_dict}
    print('OK!')
    n = 0
    for i in subject_dict['card_blog_list']:
        p_url = 'bootstrap/img/content/news%s.jpg' % n
        i['img_url'] = p_url
        n += 1
        if n == 10:
            n = 0
    return render(request, 'microblog/subject.html', context)


def save_subject(request):
    if request.method == 'POST':
        req_info = request.POST
        subject_dict = req_info.get('subject_dict', None)
        if subject_dict:  # 如果获取到请求带入的多个博客列表
            try:  # 将 str 转换成 list
                subject_dict = eval(subject_dict)
            except Exception as e:
                print(e)
                subject_dict = None
            if subject_dict:
                wb_obj = WbSpider()  # 保存多个微博到数据库
                result_info = wb_obj.save_subject_sql(have_subject_dict=subject_dict)
                if result_info == 'success':
                    print('OK')
                    subject_name = subject_dict['card_list_dict']['title']
                    context = {'success': '保存数据库成功！', 'subject': True,
                               'subject_name': subject_name}
                    return render(request, 'microblog/404.html', context)

        context = {'error': '保存失败，请重试！'}
        return render(request, 'microblog/404.html', context)

    elif request.method == 'GET':
        return redirect('microblog:microblog_index')


def detail_blog(request, detail_id):
    if request.method == 'POST':
        req_info = request.POST
        res_dict = dict()
        res_dict['video_url'] = req_info.get('video_url', None)
        res_dict['subject'] = req_info.get('subject', None)
        res_dict['content'] = req_info.get('content', None)
        res_dict['created_at'] = req_info.get('created_at', None)
        res_dict['comment_count'] = req_info.get('comment_count', None)
        res_dict['transmit_count'] = req_info.get('transmit_count', None)
        res_dict['detail_url'] = req_info.get('detail_url', None)
        pics_list = req_info.get('pics_list', None)
        new_pics_list = list()  # 定义一个新的图片列表
        if pics_list:  # 如果获取到图片列表
            try:  # 将获取到的图片列表转换成列表
                pics_list = eval(pics_list)
            except Exception as e:
                print(e)
                new_pics_list = list()
            else:
                if pics_list:
                    n = 0
                    for i in range(1, len(pics_list) + 1):
                        p_url = 'bootstrap/img/content/slide%s.jpg' % n
                        new_pics_list.append((pics_list[i-1], p_url))
                        n += 1
                        if n == 7:
                            n = 0
        res_dict['pics_list'] = new_pics_list
        wb_obj = WbSpider()  # 获取评论数据
        comment_list = wb_obj.get_comment_list(detail_id=detail_id)
        res_dict['comment_list'] = comment_list
        context = {'res': res_dict}
        return render(request, 'microblog/news.html', context)

    elif request.method == 'GET':
        return redirect('microblog:microblog_index')


def analyze_views(request, blog_id):
    try:  # 获取该条微博对象
        micro_blog_obj = MicroBlog.objects.get(id=blog_id)
    except MicroBlog.DoesNotExist:
        context = {'error': '参数有误，请重新输入！'}
        return render(request, 'microblog/analyse.html', context)
    try:
        subject_obj = SpecialSubject.objects.get(id=micro_blog_obj.special_subject_id)
    except SpecialSubject.DoesNotExist:
        subject_obj = None

    ana_obj = Analyze(micro_blog_obj=micro_blog_obj)
    positive_df, negative_df = ana_obj.stop_()  # 对DataFrame执行数据处理
    matlib_obj = Matlib()
    positive_word_cloud, negative_word_cloud = None, None
    positive_bar, negative_bar = None, None
    pie_graph = None
    if not positive_df.empty and not negative_df.empty:
        # 如果正负 DataFrame 都不为空
        # 生成词云图
        positive_word_cloud = matlib_obj.word_cloud(' '.join(positive_df[3].values))
        negative_word_cloud = matlib_obj.word_cloud(' '.join(negative_df[3].values))
        # 生成柱状图
        positive_bar = matlib_obj.bar_graph(df=positive_df)
        negative_bar = matlib_obj.bar_graph(df=negative_df)
        # 生成饼图
        pie_graph = matlib_obj.pie_graph(positive_df=positive_df, negative_df=negative_df)

    context = {
        'positive_word_cloud': positive_word_cloud, 'negative_word_cloud': negative_word_cloud,
        'positive_bar': positive_bar, 'negative_bar': negative_bar,
        'pie_graph': pie_graph, 'res': micro_blog_obj,
        'subject_obj': subject_obj
    }
    return render(request, 'microblog/analyse.html', context)


def microblog_search(request):
    req_info = request.GET
    print(req_info)
    microblog_name = req_info.get('keyword', None)
    print(microblog_name)
    if microblog_name:
        microblog_queryset = MicroBlog.objects.filter(Q(content__icontains=microblog_name)
                                                      | Q(subject__icontains=microblog_name)
                                                      | Q(special_subject__desc__icontains=microblog_name)
                                                      | Q(special_subject__title__icontains=microblog_name))
        context = {
            'res_list': microblog_queryset
        }
        return render(request, 'microblog/search.html', context)
    context = {
        'error': '请输入关键字查询'
    }
    return render(request, 'microblog/search.html', context)
