from bs4 import BeautifulSoup
import requests
from django.views.decorators.cache import cache_page

# Create your views here.


anyknew_zhihu = 'https://www.anyknew.com/api/v1/sites/zhihu'
start_urls = 'http://thepaper.cn/'

def news_url(newurl, encode='utf-8'):
    """
        得到知乎热榜第一个url_id
    """
    html = requests.get(newurl).json()
    url_id = html['data']['site']['subs'][0]['items'][0]['iid']
    print('url_id:',url_id)
    return url_id

def urls_list(page):
    """
        输入要得到知乎热榜的数量page（最多50条），得到跳转完整网址
    """
    url_id = news_url(anyknew_zhihu)
    info_url = 'https://www.anyknew.com/go/%s'
    info_list_url = [info_url%url_id]
    for i in range(1,page):
        info_list_url.append(info_url%(url_id-i))
    return info_list_url


def get_content(zhihu_url_id='318144086', limit=1):
    """
        输入id，和回答排序次数，得到此回答内容列表
    """
    url = """https://www.zhihu.com/api/v4/questions/%s/answers?include=data[*].is_normal,admin_closed_comment,
    reward_info,is_collapsed,annotation_action,annotation_detail,collapse_reason,is_sticky,collapsed_by,
    suggest_edit,comment_count,can_comment,content,editable_content,voteup_count,reshipment_settings,
    comment_permission,created_time,updated_time,review_info,relevant_info,question,excerpt,relationship.is_authorized,
    is_author,voting,is_thanked,is_nothelp,is_labeled,is_recognized,paid_info;data[*].mark_infos[*].url;
    data[*].author.follower_count,badge[*].topics&limit=%s&offset=5&platform=desktop&sort_by=default"""
    headers = {"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36"}
    content = requests.get(url%(zhihu_url_id, limit), headers=headers).json()
    content_info = {}
    for li in range(limit):
        try:
            html = content['data'][li]['content']
        except IndexError:
            break
        soup = BeautifulSoup(html, 'html.parser')
        p_list = soup.find_all('p')
        content_list = []
        for p in p_list:
            if p.string:
                content_list.append(p.string)
        content_info[li+1] = content_list
    # print(content_info)
    return content_info

# get_content()

def info(url='https://www.anyknew.com/go/3600688', l=10):
    """
        传入url，得到 data : {新url : question, answer}
    """
    headers = {"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36"}
    html = requests.get(url, headers=headers).content.decode('utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    # 得到 question
    title = soup.title.string
    # 热榜中的准确url
    zhihu_url_div = soup.find(class_='QuestionPage')
    zhihu_url = zhihu_url_div.find_all('meta')[1].get('content')
    zhihu_url_id = zhihu_url.split('/')[-1]
    print(zhihu_url_id)
    content_info = get_content(zhihu_url_id, l)
    data = {
        'url':zhihu_url,
        'question':title,
        'answer':content_info
    }
    return data


def content_data(page=10, limit=10):
    urls_lists = urls_list(page)
    datas = {
        'data':[]
    }
    for u in urls_lists:
        content_info = info(u, limit)
        datas['data'].append(content_info)
    return datas

# print(info())




# headers = {"User-Agent" : "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;"}
# res = requests.get('https://www.anyknew.com/go/3600688',headers=headers)
# print(res)
# print(urls_list())

