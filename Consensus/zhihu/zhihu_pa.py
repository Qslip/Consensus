from bs4 import BeautifulSoup
from .usergent import get_one_agent
import requests
import threading
import random
import time

# Create your views here.



def news_url(newurl, encode='utf-8'):
    """
        得到知乎热榜第一个url_id
    """
    html = requests.get(newurl).json()
    url_id = html['data']['site']['subs'][0]['items'][0]['iid']
    # print('url_id:',url_id)
    return url_id

def urls_list(pages, page=None):
    """
        输入要得到知乎热榜的数量pages（最多50条），得到跳转完整网址
        page: 指定第几个问题
    """
    anyknew_zhihu = 'https://www.anyknew.com/api/v1/sites/zhihu'
    url_id = news_url(anyknew_zhihu)
    info_url = 'https://www.anyknew.com/go/%s'
    info_list_url = [info_url%url_id]
    for i in range(1, pages):
        info_list_url.append(info_url%(url_id-i))
    if page:
        return [info_list_url[page-1]]
    return info_list_url


def get_content(zhihu_url_id='318144086', limit=1):
    """
        输入 zhihu_url_id，和回答个数 limit， 得到 limit 个回答的内容字典
    """
    # 这是个知乎接口
    url = """https://www.zhihu.com/api/v4/questions/%s/answers?include=data[*].is_normal,admin_closed_comment,
    reward_info,is_collapsed,annotation_action,annotation_detail,collapse_reason,is_sticky,collapsed_by,
    suggest_edit,comment_count,can_comment,content,editable_content,voteup_count,reshipment_settings,
    comment_permission,created_time,updated_time,review_info,relevant_info,question,excerpt,relationship.is_authorized,
    is_author,voting,is_thanked,is_nothelp,is_labeled,is_recognized,paid_info;data[*].mark_infos[*].url;
    data[*].author.follower_count,badge[*].topics&limit=5&offset=%s&platform=desktop&sort_by=default"""
    headers = {"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36"}
    content = requests.get(url%(zhihu_url_id, 5), headers=headers).json()
    # print(content)
    # print(url%(zhihu_url_id, 5))
    nums = content['paging']['totals']
    if limit+5 >= nums:
        limit = nums
    content_info = {}
    for li in range(0, limit, 5):   
        content = requests.get(url%(zhihu_url_id, li), headers=headers).json()
        for i in range(5):
            try:
                html = content['data'][i]['content']
            except Exception as e:
                print(e)
                break
            soup = BeautifulSoup(html, 'html.parser')
            p_list = soup.find_all('p')
            content_list = []
            for p in p_list:
                if p.string:
                    content_list.append(p.string)
            content_info[li+i+1] = content_list
            if li+i+1 == limit:
                break
    # print(content_info)
    return content_info


def get_content_save(zhihu_url_id='318144086', limit=300):
    """
        输入 zhihu_url_id，和回答个数 limit， 得到 limit 个回答的内容，question，url，字典
    """
    # 这是个知乎接口
    url = """https://www.zhihu.com/api/v4/questions/%s/answers?include=data[*].is_normal,admin_closed_comment,
    reward_info,is_collapsed,annotation_action,annotation_detail,collapse_reason,is_sticky,collapsed_by,
    suggest_edit,comment_count,can_comment,content,editable_content,voteup_count,reshipment_settings,
    comment_permission,created_time,updated_time,review_info,relevant_info,question,excerpt,relationship.is_authorized,
    is_author,voting,is_thanked,is_nothelp,is_labeled,is_recognized,paid_info;data[*].mark_infos[*].url;
    data[*].author.follower_count,badge[*].topics&limit=5&offset=%s&platform=desktop&sort_by=default"""
    headers = {"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36"}
    content = requests.get(url%(zhihu_url_id, 5), headers=headers).json()
    # print(content)
    # print(url%(zhihu_url_id, 5))
    nums = content['paging']['totals']
    if limit+5 >= nums:
        limit = nums
    content_info = {
        'answer':{}
    }
    content_info['question'] = content['data'][0]['question']['title']
    for li in range(0, limit, 5):   
        content = requests.get(url%(zhihu_url_id, li), headers=headers).json()
        for i in range(5):
            try:
                html = content['data'][i]['content']
            except Exception as e:
                print(e)
                break
            soup = BeautifulSoup(html, 'html.parser')
            p_list = soup.find_all('p')
            content_list = []
            for p in p_list:
                if p.string:
                    content_list.append(p.string)
            content_info['answer'][li+i+1] = content_list
            if li+i+1 == limit:
                break
    # print(content_info)
    return content_info

# print(get_content_save())

def info(url='https://www.anyknew.com/go/3600688', limit=10, ne=None):
    """
        传入url，得到 data : {新url : question, answer}
        limit : 想要得到几个回答
        ne : 是否需要回答
    """
    headers = {"User-Agent" : get_one_agent(),
    'Cookie':'_ga=GA1.2.53859037.1554208898; Hm_lvt_031106cf3698b51040412308929d5e01=1557360791; _gid=GA1.2.521072332.1557547461; Hm_lpvt_031106cf3698b51040412308929d5e01=1557560638; _gat_gtag_UA_131079741_1=1'} #随机chrome浏览器任意版本
    html = requests.get(url, headers=headers).content.decode('utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    # print(html)
    # 得到 question
    title = soup.title.string
    # 热榜中的准确url
    zhihu_url_div = soup.find(class_='QuestionPage')
    if not zhihu_url_div:
        print('QuestionPage:',zhihu_url_div, title)
        return None
    zhihu_url = zhihu_url_div.find_all('meta')[1].get('content')
    try:
        zhihu_url_id = zhihu_url.split('/')[-1]
    except:
        zhihu_url_id = None
    print(zhihu_url)
    if ne:
        # print('ne', ne)
        content_info = get_content(zhihu_url_id, limit)
        data = {
            'urls':zhihu_url,
            'question':title,
            'answer':content_info,
            'url_id':zhihu_url_id,
        }
    else:
        data = {
                'urls':zhihu_url,
                'question':title,
            }
    return data

# print(info())

def content_data(pages=10, limit=10, page=None, ne=None):
    """
        实时爬取得到想要的数据
        pages: 要得到知乎热榜的数量pages（最多50条），得到跳转完整网址
        page: 指定第几个问题
        limit : 想要得到几个回答
        ne : 是否需要问题的回答
    """
    urls_lists = urls_list(pages, page)
    datas = {
        'data':[]
    }
    for u in urls_lists:
        content_info = info(u, limit, ne)
        if content_info:
            datas['data'].append(content_info)
    return datas

# print(info())

class DataThread (threading.Thread):
    """
        多线程爬虫
    """
    def __init__(self, url, limit=10, ne=None, sav='save'):
        threading.Thread.__init__(self)
        self.url = url
        self.limit = limit
        self.ne = ne
        self.sav = sav
    def run(self):
        if self.sav:
            r = random.choice(range(10))
            time.sleep(r)
        self.data = info(self.url, self.limit, self.ne)

    def get_result(self):
        try:
            return self.data
        except Exception as e:
            print(e)
            return None

def get_data(pages=10, limit=10, page=None, ne=None, sav='save'):
    """
        实时爬取得到想要的数据
        pages: 要得到知乎热榜的数量pages（最多50条），得到跳转完整网址
        page: 指定第几个问题
        limit : 想要得到几个回答
        ne : 是否需要问题的回答
    """
    urls_lists = urls_list(pages, page)
    datas = {
        'data':[]
    }
    pool = []
    for t in urls_lists:
        # print('t',t)
        pool.append(DataThread(t, limit, ne, sav=sav))
    for s in pool:
        s.start()
    for j in pool:
        j.join()
        get_result = j.get_result()
        # print('get_result',get_result)
        if get_result:
            datas['data'].append(get_result)
    return datas
# headers = {"User-Agent" : "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;"}
# res = requests.get('https://www.anyknew.com/go/3600688',headers=headers)
# print(res)
# print(urls_list())


if __name__ == "__main__":
    pass