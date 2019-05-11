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
import random
import time
import requests
import django
# import threading
from microblog.usergent import get_one_agent
from django.db.utils import IntegrityError

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Consensus.settings')
django.setup()

from microblog.models import MicroBlog, MbImg, Comment


class WbSpider:
    """
    微博爬虫类
    """
    # headers = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'}

    headers = {
        'User-Agent': get_one_agent(),
    }

    url = 'https://m.weibo.cn/api/container/getIndex?containerid=102803&openApp={}&since_id={}'

    def get_wb_json(self, app_num, page_num):
        """
        传入页码数、匹配成请求的URL，请求API的URL；
        成功返回一个包含json数据的列表，失败返回None
        """
        url = self.url.format(app_num, page_num)
        res = requests.get(url, headers=self.headers)
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
        传入获取到的 json  列表数据，解析列表中的每一个对象，获取需要用到的属性
        :return:
        """
        if json_list:
            micro_blog_list = list()
            for i in json_list:
                item_dict = dict()
                pics_list = list()
                i_mblog = i['mblog']
                item_dict['detail_url'] = i['scheme']
                item_dict['micro_blog_id'] = i_mblog['id']
                item_dict['content'] = i_mblog['text']
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
        res = requests.get(comment_url, headers=self.headers)
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
            for i in comment_list:
                item_dict = dict()
                item_dict['comment_content'] = i['text']
                item_dict['author_name'] = i['user']['screen_name']
                item_dict['author_description'] = i['user']['description']
                item_dict['author_profile'] = i['user']['profile_image_url']
                item_dict['author_url'] = i['user']['profile_url']
                item_dict['created_at'] = i['created_at']

                new_comment_list.append(item_dict)

            return new_comment_list

        return None

    def save_data_sql(self, micro_blog_list):
        """
        传入一个微博的json列表，将数据循环写入数据库（循环的同时获取每一条微博的评论数据并写入数据库）
        :param micro_blog_list:
        :return:
        """
        if micro_blog_list:
            for i in micro_blog_list:
                # 创建微博对象实例
                print(i['micro_blog_id'])
                try:
                    micro_blog_obj = MicroBlog.objects.create(
                        detail_url=i['detail_url'], micro_blog_id=i['micro_blog_id'],
                        content=i['content'], subject=i['subject'], video_url=i['video_url'],
                        video_count=i['video_count'], created_at=i['created_at'],
                        comment_count=i['comment_count'], like_count=i['like_count'],
                        transmit_count=i['transmit_count'], author=i['author'],
                        author_description=i['author_description'], author_profile=i['author_profile'],
                        author_url=i['author_url'], source=i['source']
                    )
                except IntegrityError:
                    print('*'*100)
                    print('重复错误！')
                    continue

                pics_list = i['pics_list']
                # 如果这条微博有图片，则循环创建图片实例
                if pics_list:
                    for pic in pics_list:
                        MbImg.objects.create(img_url=pic, micro_blog=micro_blog_obj)

                micro_blog_id = i['micro_blog_id']
                print(micro_blog_id)
                # 通过该条微博的ID，请求该条微博的评论API
                res_info = self.get_wb_comment(detail_id=micro_blog_id)
                print('*'*100)
                print('获取评论：')
                print(res_info[0:2])
                if res_info:
                    new_comment_list = self.parse_comment_list(comment_list=res_info)
                    # 如果解析成功，则循环创建这条微博的评论实例对象
                    print('*'*100)
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


if __name__ == '__main__':
    # a = WbSpider()

    # 关于微博内容
    # json_list = a.get_wb_json(page_num=1)
    # micro_blog_list = a.parse_json_list(json_list)
    # print(micro_blog_list)
    # # 写入微博内容（同时爬取评论内容）到数据库
    # res = a.save_data_sql(micro_blog_list=micro_blog_list)
    # print(res)

    # print('*'*100)
    # # 关于评论内容
    # comment_list = a.get_wb_comment(detail_id='4370166492286327')
    # new_comment_list = a.parse_comment_list(comment_list)
    # print(new_comment_list)

    # 爬取15次
    spider_obj = WbSpider()
    for num in range(50, 100):
        json_list = spider_obj.get_wb_json(app_num=0, page_num=num)
        micro_blog_list = spider_obj.parse_json_list(json_list)
        print('*' * 100)
        print('微博：')
        print(micro_blog_list[0:2])
        # 写入微博内容（同时爬取评论内容）到数据库
        res = spider_obj.save_data_sql(micro_blog_list=micro_blog_list)
        print(res)
        random_num = random.choice(range(3, 7))
        time.sleep(random_num)
