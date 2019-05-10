from django.shortcuts import render
from zhihu.zhihu import content_data
from zhihu.models import ZhiInfo
from django.views.decorators.cache import cache_page
from Consensus.settings import TIME_OUT

@cache_page(TIME_OUT)  # 设置缓存时间
def data(request):
    """
        展示知乎热榜前 10 个数据
    """
    data = content_data(8, 5)
    # print(datas)
    if request.method == 'POST':
        question_id = int(request.POST['id'])
        return render(request, 'zhihu/zhihu-info.html', context=data['data'][question_id])
    return render(request, 'zhihu/zhihu-index.html', context=data)
