from django.shortcuts import render, redirect
from zhihu.zhihu_pa import content_data, get_data, get_content_save
from zhihu.models import ZhihuInfo, ZhihuQuestion, ZhihuAnswer
from django.views.decorators.cache import cache_page
from django.http import  HttpResponse
from Consensus.settings import TIME_OUT
from zhihu.zhihu_analysis import Analyze, Matlib
import threading
import time


# @cache_page(TIME_OUT)  # 设置缓存时间
def data(request, page=None):
    """
        默认展示知乎热榜前 10 个数据
    """
    # print(datas)
    pages = request.GET.get('pages', 10)
    limit = request.GET.get('limit', 10)
    request.session['pages'] = pages
    request.session['limit'] = limit
    rq = request.session
    if page:
        data = get_data(rq['pages'], rq['limit'], page, 1)
        question_id = int(page)
        # print(data['data'][0])
        return render(request, 'zhihu/zhihu-info.html', context=data['data'][0])
    data = get_data(rq['pages'], rq['limit'])
    # print(data)
    n = 0
    for i in data['data']:
        p_url = 'bootstrap/img/content/news%s.jpg'%n
        i['picture'] = p_url
        n += 1
        if n == 10:
            n = 0
    # for n in range((rq['pages']-1)//10+1):
    #     for i in range(10):
    #         p_url = 'bootstrap/img/content/news%s.jpg'%i
    #         try:    
    #             data['data'][i+n]['picture'] = p_url
    #         except IndexError:
    #             break
    # print(data)
    return render(request, 'zhihu/zhihu-index.html', context=data)

def save_(info, q, arg_a, arg_b):
    for k,v in tuple(info['answer'].items())[arg_a:arg_b]:
        an = q.zhihuanswer_set.create(arg=k)
        for i in v:
            time.sleep(0.1)
            an.zhihuinfo_set.create(info=i)
        print('第%s个回答保存完毕'%k)

def save_data(request, url_id):
    info = get_content_save(url_id,300)
    try:
        ZhihuQuestion.objects.get(question=info['question'])
    except:
        zhihu_url = 'https://www.zhihu.com/question/%s'%url_id
        q = ZhihuQuestion.objects.create(info_url=zhihu_url, question=info['question'])
        t = []
        for i in range(0, len(info['answer']),60):
            t.append(threading.Thread(target=save_,args=(info, q, i, i+60)))
            # t.start  
        for s in t:
            s.start()
        for j in t:
            j.join()
    return render(request, 'zhihu/zhihu-result.html', {'ok':'数据库保存完成'})


def search(request):
    if request.method == 'POST':
        key_word = request.POST['key_word']
        question = ZhihuQuestion.objects.filter(question__contains=key_word)
        if question:
            data = {
                'data':[]
            }
            n = 0
            for i in question:
                p_url = 'bootstrap/img/content/news%s.jpg'%n
                data['data'].append({'id':i.id,'question':i.question,'picture':p_url})
                n += 1
                if n == 10:
                    n = 0
            return render(request, 'zhihu/zhihu_search_r.html', context=data)
        return render(request, 'zhihu/zhihu_search_r.html', context={'error':'根据您提供的词，不能搜索到相关问题，请检查关键词是否正确'})
    return redirect('zhihu:index')

def search_analyze(request, question_id):
    """ 对指定问题的分析绘图  """
    try:
        an = Analyze(question_id)
    except:
        return render(request, 'zhihu_show.html', context={'error':'没有此问题的ID'})
    b64 = 'data:image/jpeg;base64,'
    p,n = an.jie_ba()
    p_w = b64 + str(Matlib().word_cloud(''.join(p.values)))
    n_w = b64 + str(Matlib().word_cloud(''.join(n.values)))
    p2,n2 = an.stop_()
    p_f = b64 + str(Matlib().frequency(p2[2].values))
    n_f = b64 + str(Matlib().frequency(n2[2].values))
    data={'p':p_w,'n':n_w,'p2':p_f,'n2':n_f}
    return render(request, 'zhihu/zhihu_show.html', context=data)



