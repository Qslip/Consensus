# -*- coding: utf-8 -*-
"""
   Product:      PyCharm
   Project:      Consensus
   File:         wb_spider
   Author :      ZXR 
   date：        2019/5/10
   time:         9:26 
"""
import os
import re
import random
import time
import requests
import django
import threading
from urllib import parse
from microblog.usergent import get_one_agent
from django.db.utils import IntegrityError

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Consensus.settings')
django.setup()

from microblog.models import MicroBlog, MbImg, Comment, SpecialSubject


class WbSpider:
    """
    微博爬虫类
    """
    # headers = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'}

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:66.0) Gecko/20100101 Firefox/66.0',
        # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        # 'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        # 'Accept-Encoding': 'gzip, deflate, br',
        # 'Connection': 'keep-alive',
        # 'Cookie': '_T_WM=84501405709; MLOGIN=0; WEIBOCN_FROM=1110006030; M_WEIBOCN_PARAMS=luicode=10000011&lfid=102803&fid=102803&uicode=10000011',
        # 'Cookie': 'MLOGIN=0; _T_WM=84501405709; WEIBOCN_FROM=1110006030',
    }

    url = 'https://m.weibo.cn/api/container/getIndex?containerid=102803&openApp={}&since_id={}'

    thread_lock = threading.Lock()

    ses = requests.session()

    def get_wb_json(self, app_num, page_num):
        """
        传入页码数、匹配成请求的URL，请求API的URL；
        成功返回一个包含json数据的列表，失败返回None
        """
        url = self.url.format(app_num, page_num)
        print(url)
        res = self.ses.get(url)
        if res.status_code == 200:
            try:
                res_info = res.json()['data']['cards']
            except KeyError:
                return None
            else:
                return res_info
        return None

    def parse_json_list(self, json_list):
        """
        传入获取到的热门微博 json  列表数据，解析列表中的每一个对象，获取需要用到的属性
        :return:
        """
        if json_list:
            micro_blog_list = list()
            for mb in json_list:
                item_dict = dict()
                pics_list = list()
                i_mblog = mb['mblog']
                item_dict['detail_url'] = mb['scheme']
                item_dict['micro_blog_id'] = i_mblog['id']
                item_dict['content'] = i_mblog['text']
                try:
                    page_content1 = i_mblog['page_info']['content1']
                    page_content2 = i_mblog['page_info']['content2']
                    if page_content1 and page_content2:  # 如果这两个内容都有，则拼接两个内容
                        item_dict['content'] = page_content1 + page_content2
                    elif page_content2:     # 再如果只有内容2：
                        item_dict['content'] = page_content2
                    subject_list = re.findall('#(.*?)#', page_content2)     # 用正则匹配专题名称
                    if subject_list:    # 如果匹配到，则取第一个专题名称
                        item_dict['special_subject'] = '#' + subject_list[0] + '#'
                    else:
                        item_dict['special_subject'] = None
                except KeyError:
                    item_dict['special_subject'] = None

                try:  # 如果这条微博有 主题
                    item_dict['subject'] = i_mblog['page_info']['page_title']
                except KeyError:
                    item_dict['subject'] = None
                try:  # 如果这条微博有 视频
                    video_url = i_mblog['page_info']['media_info']['mp4_720p_mp4']
                    video_url2 = i_mblog['page_info']['media_info']['mp4_sd_url']
                    video_count = i_mblog['page_info']['play_count']
                except KeyError:
                    video_url = None
                    video_url2 = None
                    video_count = None
                item_dict['video_url'] = video_url2
                if video_url:
                    item_dict['video_url'] = video_url
                item_dict['video_count'] = video_count
                item_dict['created_at'] = i_mblog['created_at']
                item_dict['comment_count'] = i_mblog['comments_count']
                item_dict['like_count'] = i_mblog['attitudes_count']
                item_dict['transmit_count'] = i_mblog['reposts_count']
                item_dict['author'] = i_mblog['user']['screen_name']
                item_dict['author_description'] = i_mblog['user']['description']
                item_dict['author_profile'] = i_mblog['user']['profile_image_url']
                item_dict['author_url'] = i_mblog['user']['profile_url']
                item_dict['source'] = i_mblog['source']
                try:
                    pics = i_mblog['pics']
                except KeyError:
                    pics = None
                if pics:  # 如果这条微博有 图片
                    for p in pics:
                        pic_url = p['url']
                        pics_list.append(pic_url)
                item_dict['pics_list'] = pics_list

                micro_blog_list.append(item_dict)

            return micro_blog_list

        return None

    def get_wb_comment(self, detail_id):
        """
        通过传入的微博详细ID，请求该条微博评论API，获取评论数据
        成功返回一个包含评论数据的列表，失败返回None
        :param detail_id:
        :return:
        """
        comment_url = 'https://m.weibo.cn/comments/hotflow?id={}&mid={}&max_id_type=0'.format(detail_id, detail_id)
        res = self.ses.get(comment_url, headers=self.headers)
        if res.status_code == 200:
            try:
                res_info = res.json()['data']['data']
            except KeyError:
                return None
            else:
                return res_info
        return None

    def parse_comment_list(self, comment_list):
        """
        传入获取到的评论列表，解析列表，抓取需要的属性
        :param comment_list: 一个包含评论数据的列表
        :return:
        """
        if comment_list:
            new_comment_list = list()
            for comm in comment_list:
                item_dict = dict()
                item_dict['comment_content'] = comm['text']
                item_dict['author_name'] = comm['user']['screen_name']
                item_dict['author_description'] = comm['user']['description']
                item_dict['author_profile'] = comm['user']['profile_image_url']
                item_dict['author_url'] = comm['user']['profile_url']
                item_dict['created_at'] = comm['created_at']

                new_comment_list.append(item_dict)

            return new_comment_list

        return None

    def save_data_sql(self, micro_blog_list, subject_obj=None):
        """
        传入一个微博的json列表，将数据循环写入数据库（循环的同时获取每一条微博的评论数据并写入数据库）
        :param micro_blog_list: 一个多条微博数据的列表（）
        :param subject_obj: 专题对象（如果传入了专题对象，则不再去抓取专题对象；用于专题下保存数据库）
        :return:
        """
        if micro_blog_list:
            for micro_b in micro_blog_list:
                # 创建微博对象实例
                print(micro_b['micro_blog_id'])
                special_subject_name = micro_b['special_subject']
                if not subject_obj:
                    if special_subject_name:
                        try:    # 从数据库查询是否有该专题名称的专题对象
                            subject_obj = SpecialSubject.objects.get(title=special_subject_name)
                        except SpecialSubject.DoesNotExist:  # 如果没有，则先请求该专题的API获取json数据
                            special_subject_json = self.get_subject_json(subject_name=special_subject_name)
                            if special_subject_json:    # 如果获取到json数据，解析json数据，获取到专题的信息
                                card_list_dict = self.parse_subject_info(subject_json=special_subject_json)
                                # 创建专题对象
                                subject_obj = SpecialSubject.objects.create(
                                    title=card_list_dict['title'], desc=card_list_dict['desc'],
                                    midtext=card_list_dict['midtext'], downtext=card_list_dict['downtext'],
                                    background_url=card_list_dict['background_url'], portrait=card_list_dict['portrait']
                                )
                            else:   # 如果没有获取到json数据
                                subject_obj = None
                    else:
                        subject_obj = None
                try:
                    micro_blog_obj = MicroBlog.objects.create(
                        detail_url=micro_b['detail_url'], micro_blog_id=micro_b['micro_blog_id'],
                        content=micro_b['content'], subject=micro_b['subject'], video_url=micro_b['video_url'],
                        video_count=micro_b['video_count'], created_at=micro_b['created_at'],
                        comment_count=micro_b['comment_count'], like_count=micro_b['like_count'],
                        transmit_count=micro_b['transmit_count'], author=micro_b['author'],
                        author_description=micro_b['author_description'], author_profile=micro_b['author_profile'],
                        author_url=micro_b['author_url'], source=micro_b['source'], special_subject=subject_obj
                    )
                except IntegrityError:
                    print('*' * 100)
                    print('重复错误！')
                    continue

                pics_list = micro_b['pics_list']
                # 如果这条微博有图片，则循环创建图片实例
                if pics_list:
                    for pic in pics_list:
                        MbImg.objects.create(img_url=pic, micro_blog=micro_blog_obj)

                micro_blog_id = micro_b['micro_blog_id']
                print(micro_blog_id)
                # 通过该条微博的ID，请求该条微博的评论API
                res_info = self.get_wb_comment(detail_id=micro_blog_id)
                print('*' * 100)
                print('获取评论：')
                if res_info is None:
                    # print(res_info)
                    pass
                else:
                    print(res_info[0: 1])
                if res_info:
                    new_comment_list = self.parse_comment_list(comment_list=res_info)
                    # 如果解析成功，则循环创建这条微博的评论实例对象
                    print('*' * 100)
                    print('评论：')
                    print(new_comment_list[0:2])
                    if new_comment_list:
                        for comment in new_comment_list:
                            Comment.objects.create(
                                comment_content=comment['comment_content'], author_name=comment['author_name'],
                                author_description=comment['author_description'], author_url=comment['author_url'],
                                author_profile=comment['author_profile'], created_at=comment['created_at'],
                                micro_blog=micro_blog_obj
                            )
            print('写入数据库完成！')
            return 'success'

        return None

    def get_blog_list(self, page_num):
        """
        通过传入页码数，请求微博API获取json数据，并解析数据
        成功返回一个包含微博信息的列表，失败返回None
        :param page_num: 微博API的页码数
        :return:
        """
        json_list = self.get_wb_json(app_num=0, page_num=page_num)
        micro_blog_list = self.parse_json_list(json_list)
        return micro_blog_list

    def get_comment_list(self, detail_id):
        """
        通过传入的详细微博ID，调用已有的方法，请求该条微博的评论API，获取评论数据，并解析需要的评论数据
        成功返回一个包含评论数据的列表，失败返回None
        :param detail_id:
        :return:
        """
        comment_list = self.get_wb_comment(detail_id=detail_id)
        new_comment_list = self.parse_comment_list(comment_list=comment_list)
        return new_comment_list

    def save_sql_run(self, page_num, have_blog_list=None):
        """
        保存数据到数据库：通过传入一个页码数，请求该页码数的API，获取数据，并解析数据；
        同时请求每一条数据的评论数据，保存到数据库
        :param page_num: 传入一个页码数，进行实时爬取数据；与 have_blog_list 参数 二选一
        :param have_blog_list: 如果传入了此参数，则不再去实时爬取数据
        :return:
        """
        micro_blog_list = have_blog_list
        if not micro_blog_list:
            json_list = self.get_wb_json(app_num=0, page_num=page_num)
            micro_blog_list = self.parse_json_list(json_list)
        # 写入微博内容（同时爬取评论内容）到数据库
        WbSpider.thread_lock.acquire()
        res = self.save_data_sql(micro_blog_list=micro_blog_list)
        WbSpider.thread_lock.release()
        random_num = random.choice(range(1, 3))
        time.sleep(random_num)
        return res

    def get_subject_json(self, subject_name):
        """
        通过传入一个 专题名字，获取该专题下的所有微博内容
        :param: subject_name: 专题名字；例如：#搞笑#
        :return:
        """
        # 请求参数字典
        params_dict = {
            'containerid': '231522type=1&t=10&q={}'.format(subject_name),
            'extparam': subject_name,
            'luicode': 10000011,
            'lfid': 102803,
            'page_type': 'searchall'
        }
        print(params_dict)
        quote_str = parse.urlencode(params_dict)  # 将请求参数进行URL编码

        api_url = 'https://m.weibo.cn/api/container/getIndex?{}'
        search_url = api_url.format(quote_str)  # 组成完整URL

        res = requests.get(search_url)
        if res.status_code == 200:
            res.encoding = 'utf-8'
            try:
                res_data = res.json()['data']
            except KeyError:
                return None
            else:
                return res_data
        return None

    def parse_subject_info(self, subject_json):
        """
        通过传入获取到的 专题json数据，解析该数据，提出该专题的专题信息部分；
        :param subject_json:
        :return:
        """
        card_list_dict = dict()
        card_list_info = subject_json['cardlistInfo']
        card_list_dict['title'] = card_list_info['cardlist_title']  # 标题
        card_list_dict['desc'] = card_list_info['desc']  # 专题描述
        try:
            # 阅读量、讨论量
            card_list_dict['midtext'] = card_list_info['cardlist_head_cards'][0]['head_data']['midtext']
            # 主持人
            card_list_dict['downtext'] = card_list_info['cardlist_head_cards'][0]['head_data']['downtext']
            # 背景图片
            card_list_dict['background_url'] = card_list_info['cardlist_head_cards'][0]['head_data']['background_url']
        except KeyError:
            card_list_dict['midtext'] = None
            card_list_dict['downtext'] = None
            card_list_dict['background_url'] = None

        card_list_dict['portrait'] = card_list_info['portrait']  # 头像
        return card_list_dict

    def parse_subject_json(self, subject_json):
        """
        通过传入获取到的 专题json数据，解析该数据，提出该专题的专题信息部分、该专题下的多个微博部分；
        :param subject_json:
        :return:
        """
        if subject_json:
            # 专题信息部分
            subject_dict = dict()   # 最后需要的数据的字典

            card_list_dict = self.parse_subject_info(subject_json=subject_json)
            subject_dict['card_list_dict'] = card_list_dict

            # 该专题下的多个 微博部分
            cards_list = subject_json['cards']
            card_blog_list = list()
            for card in cards_list:
                if 'card_group' in card:
                    for card_g in card['card_group']:
                        card_g_dict = dict()
                        # print(card_g)
                        # print('*' * 100)
                        try:
                            card_g_mblog = card_g['mblog']
                        except KeyError:
                            continue
                        card_g_dict['detail_url'] = card_g['scheme']  # 该条微博的URL
                        card_g_dict['micro_blog_id'] = card_g_mblog['id']  # 该条微博的ID
                        card_g_dict['content'] = card_g_mblog['text']  # 该条微博的内容
                        try:
                            page_content1 = card_g_mblog['page_info']['content1']  # 该条微博的内容1
                            page_content2 = card_g_mblog['page_info']['content2']  # 内容2
                            if page_content1 and page_content2:  # 如果都有，则拼接起来
                                card_g_dict['content'] = page_content1 + page_content2
                            elif page_content2:
                                card_g_dict['content'] = page_content2

                            subject_list = re.findall('#(.*?)#', page_content2)   # 用正则匹配专题名称
                            if subject_list:    # 如果匹配到：则将第一个专题保存
                                card_g_dict['special_subject'] = '#' + subject_list[0] + '#'
                            else:
                                card_g_dict['special_subject'] = None
                        except KeyError:
                            card_g_dict['special_subject'] = None

                        try:  # 如果这条微博有 主题
                            card_g_dict['subject'] = card_g_mblog['page_info']['page_title']
                        except KeyError:
                            card_g_dict['subject'] = None
                        try:  # 如果这条微博有 视频
                            video_url = card_g_mblog['page_info']['media_info']['mp4_720p_mp4']
                            video_url2 = card_g_mblog['page_info']['media_info']['mp4_sd_url']
                            video_count = card_g_mblog['page_info']['play_count']
                        except KeyError:
                            video_url = None
                            video_url2 = None
                            video_count = None
                        card_g_dict['video_url'] = video_url2
                        if video_url:
                            card_g_dict['video_url'] = video_url
                        card_g_dict['video_count'] = video_count
                        card_g_dict['created_at'] = card_g_mblog['created_at']
                        card_g_dict['comment_count'] = card_g_mblog['comments_count']
                        card_g_dict['like_count'] = card_g_mblog['attitudes_count']
                        card_g_dict['transmit_count'] = card_g_mblog['reposts_count']
                        card_g_dict['author'] = card_g_mblog['user']['screen_name']
                        card_g_dict['author_description'] = card_g_mblog['user']['description']
                        card_g_dict['author_profile'] = card_g_mblog['user']['profile_image_url']
                        card_g_dict['author_url'] = card_g_mblog['user']['profile_url']
                        card_g_dict['source'] = card_g_mblog['source']
                        pics_list = list()
                        try:
                            pics = card_g_mblog['pics']
                        except KeyError:
                            pics = None
                        if pics:  # 如果这条微博有 图片
                            for p in pics:
                                pic_url = p['url']
                                pics_list.append(pic_url)
                        card_g_dict['pics_list'] = pics_list

                        card_blog_list.append(card_g_dict)
            subject_dict['card_blog_list'] = card_blog_list
            return subject_dict

        return None

    def save_subject_sql(self, subject_name=None, have_subject_dict=None):
        """
        通过传入一个专题名称，请求该专题下的所有微博内容，并解析需要的内容，保存到数据库
        :param subject_name: 专题名称，如果传入了 subject_dict 参数，则该参数无效
        :param have_subject_dict: 专题的字典信息，如果传入该参数，则不再去爬取专题信息
        :return: 成功返回 'success' ，失败返回 None
        """
        subject_dict = have_subject_dict
        if not subject_dict:    # 如果没有传入已有的专题信息字典数据，就通过专题名去获取json数据
            subject_json = self.get_subject_json(subject_name=subject_name)
            if subject_json:    # 如果获取到数据
                subject_dict = self.parse_subject_json(subject_json=subject_json)
            else:
                return None
        if subject_dict:
            card_list_dict = subject_dict['card_list_dict']
            card_blog_list = subject_dict['card_blog_list']
            try:
                subject_obj = SpecialSubject.objects.get(title=card_list_dict['title'])
            except SpecialSubject.DoesNotExist:
                subject_obj = SpecialSubject.objects.create(
                    title=card_list_dict['title'], desc=card_list_dict['desc'],
                    midtext=card_list_dict['midtext'], downtext=card_list_dict['downtext'],
                    background_url=card_list_dict['background_url'], portrait=card_list_dict['portrait']
                )
            print(subject_obj)
            res_info = self.save_data_sql(micro_blog_list=card_blog_list, subject_obj=subject_obj)
            if res_info == 'success':
                return 'success'
            else:
                return None

        print('获取专题json数据失败！')
        return None


class MyThread(threading.Thread):
    """
    自定义多线程类：修改了 run 方法（运行init中的func函数，并将函数结果赋值给self.result）；
    自定义 get_result 方法，返回 run函数 中的函数运行结果
    成功返回 函数结果；失败返回 None
    """

    def __init__(self, func, args=()):
        super(MyThread, self).__init__()
        self.func = func
        self.args = args
        self.result = self.func(*self.args)

    # def run(self):
    #     time.sleep(2)
    #     self.result = self.func(*self.args)

    def get_result(self):
        # threading.Thread.join(self)  # 等待线程执行完毕
        # return self.result
        try:
            return self.result
        except Exception as e:
            print(e)
            return None


if __name__ == '__main__':
    a = WbSpider()
    rs = a.save_subject_sql(subject_name='#NBA吐槽大会#')
    print(rs)
    # s = a.get_subject_json(subject_name='#搞笑#')
    # rs = a.parse_subject_json(subject_json=s)
    # print(rs)

    # a = WbSpider()
    # c = a.get_comment_list(detail_id='4370533581672379')
    # print(c)

    # res_list = list()
    # thread_pool = list()
    # for num in range(0, 5, 5):
    #     for x in range(num, num+5):
    #         t = MyThread(a.get_blog_list, args=(x,),)
    #         thread_pool.append(t)
    #     for t in thread_pool:
    #         t.start()
    #     for t in thread_pool:
    #         t.join()
    # print(t.get_result()[0:2])
    # res_list.extend(t.get_result())
    # thread_pool = list()
    # print(res_list)

    # print(thread_pool[0].get_result()[0:2])
    # print(thread_pool[1].get_result()[0:2])
    # print(len(res_list))

    # 多线程爬取微博信息
    thread_pool = list()
    a = WbSpider()
    for i in range(0, 6, 5):
        for x in range(i, i+5):
            t = threading.Thread(target=a.save_sql_run, args=(x, ))
            thread_pool.append(t)
        for t in thread_pool:
            t.start()
        for t in thread_pool:
            t.join()
        thread_pool = list()

    # print('*'*100)
    # # 关于评论内容
    # comment_list = a.get_wb_comment(detail_id='4370166492286327')
    # new_comment_list = a.parse_comment_list(comment_list)
    # print(new_comment_list)
