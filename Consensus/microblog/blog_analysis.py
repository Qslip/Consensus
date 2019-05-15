import os
import django
# import sqlite3
import jieba
import base64
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from snownlp import SnowNLP
from wordcloud import WordCloud, ImageColorGenerator, STOPWORDS
from gensim import corpora, models
from PIL import Image
from collections import Counter
from io import BytesIO

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Consensus.settings')
django.setup()

from microblog.models import MicroBlog, Comment, SpecialSubject

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Analyze:
    """
        对数据进行情感分析
    """

    def __init__(self, micro_blog_id=None, micro_blog_obj=None):
        """
        传入一个 一条微博的ID
        :param micro_blog_id:
        """
        self.micro_blog_id = micro_blog_id
        self.micro_blog_obj = micro_blog_obj

    def get_df(self):
        """
        通过传入一个 一条微博的ID，从数据库中查找该条微博所在的 专题下 的所有微博的所有评论数据
        :return: 返回一个 所有评论的 DataFrame
        """
        # conn = sqlite3.connect(os.path.join(BASE_DIR, 'db.sqlite3'))  # 打开本地sqlite数据库
        # 查询数据库内容,pandas官网解释Read SQL database table into a DataFrame
        # micro_blog_df = pd.read_sql_query("SELECT id,content from microblog_microblog;", conn)
        # print(micro_blog_df)
        # subject_df = pd.read_sql_query('select special_subject_id from microblog_microblog where id=%s'
        #                                % self.micro_blog_id, conn)
        # if subject_df.empty:
        #     comment_df = pd.read_sql_query('select id,comment_content from microblog_comment where micro_blog_id=%s'
        #                                    % self.micro_blog_id, conn)

        # conn.close()  # 关闭数据库连接
        micro_blog_obj = self.micro_blog_obj
        if not micro_blog_obj:
            try:    # 从数据库查询指定ID的微博
                micro_blog_obj = MicroBlog.objects.get(id=self.micro_blog_id)
            except MicroBlog.DoesNotExist:
                return False

        try:    # 通过该微博的专题ID查询专题
            subject_obj = SpecialSubject.objects.get(id=micro_blog_obj.special_subject_id)
        except SpecialSubject.DoesNotExist:  # 如果没有关联专题，则直接查询该微博下的所有评论数据
            comment_list = Comment.objects.filter(micro_blog=micro_blog_obj).values_list('comment_content')
        else:   # 如果有，则查询该专题下的所有微博对象
            micro_blog_sets = subject_obj.microblog_set.all()
            # print(micro_blog_sets)    # 查询每一个微博对象的评论数据
            comment_list = Comment.objects.filter(micro_blog__in=micro_blog_sets).values_list('comment_content')
        comment_list = [i[0] for i in comment_list]     # 获取列表里的每个元组的第一个元素

        comment_df = pd.DataFrame(comment_list)
        # print(comment_df)
        return comment_df

    def str_unique(self, raw_str, reverse=False):
        """
        去掉每句评论中的重复字；比如：我喜欢喜欢喜欢---》我喜欢
        :param raw_str: 原始字符串
        :param reverse: 是否反转
        :return: 去重之后的字符串
        """
        """
            raw_str: 语句
            reverse: 是否反转
        """
        # print(raw_str)
        if reverse:
            raw_str = raw_str[::-1]
        res_str = ''
        for i in raw_str:
            if i not in res_str:
                res_str += i
        if reverse:
            res_str = res_str[::-1]
        return res_str

    def drop_na(self):
        """
        清洗数据：进行数据去空、去重、短句过滤
        :return:
        """
        df = self.get_df()  # 获取数据
        if not df.empty:
            df = df.dropna()  # 去除空数据
            df = pd.DataFrame(df.iloc[:, 0].unique())  # 将第二列的数据去重，并生成一个新的 DataFrame

            ser1 = df.iloc[:, 0].apply(self.str_unique)  # type: # <class 'pandas.core.series.Series'>
            df = pd.DataFrame(ser1.apply(self.str_unique, reverse=True))
            df = df.rename(columns={0: 'info'})  # 重命名第一列列名为：info
            df = df[df.iloc[:, 0].apply(len) >= 4]  # 短句过滤

            return df
        return None

    def sno_nlp(self):
        """
        使用 snownlp 进行情感分析，分析出喜欢的；不喜欢的
        可用于绘制：饼图；喜欢、不喜欢的百分比
        :return:
        """
        # 用 snownlp 情感分析
        df = self.drop_na()  # 用清洗后的数据
        if not df.empty:
            coms = df.iloc[:, 0].apply(lambda x: SnowNLP(x).sentiments)
            positive_df = df[coms >= 0.5]  # 特别喜欢的
            negative_df = df[coms < 0.5]  # 不喜欢的

            return positive_df, negative_df
        return None, None

    def jie_ba(self):
        """
        用 jieba 分词
        :return:
        """
        positive_df, negative_df = self.sno_nlp()  # 用 snownlp 分析过的数据
        if not positive_df.empty and not negative_df.empty:
            my_cut = lambda x: ' '.join(jieba.cut(x))
            positive_ser = positive_df.iloc[:, 0].apply(my_cut)  # 喜欢中的正面分词， 大于0.5
            negative_ser = negative_df.iloc[:, 0].apply(my_cut)  # 不喜欢中的负面分词， 小于0.5

            positive_df = pd.DataFrame(positive_ser)
            negative_df = pd.DataFrame(negative_ser)
            return positive_df, negative_df
        return None, None

    def stop_(self):
        """
        去除分词中的停用词，如：哦，噢等
        :return:
        """
        stop_path = os.path.join(BASE_DIR, 'microblog/stoplist.txt')
        stops = pd.read_csv(stop_path, encoding='gbk', header=None, sep='tipdm', engine='python')
        # sep 设置分割词，由于csv默认以半角逗号为分割此，而该词恰好在停用词表中，因此会导致读取出错
        # 所以解决办法是手动设置一个不存在的分割词，如 tipdm ；
        positive_df, negative_df = self.jie_ba()  # 用分词后的数据
        if not positive_df.empty and not negative_df.empty:
            stops = [' ', ''] + list(stops[0])  # pandas 会自动省略空格符，这里手动添加
            # print(stops)
            # positive_df = pd.DataFrame(positive_ser)
            # negative_df = pd.DataFrame(negative_ser)

            positive_df[1] = positive_df['info'].apply(lambda x: x.split(' '))  # 定义一个分割函数并使用
            positive_df[2] = positive_df[1].apply(lambda x: [i for i in x if i not in stops])
            positive_df[3] = positive_df[2].apply(lambda x: ' '.join(x))

            # positive_df[1].apply(lambda x: print([i for i in x if i not in stops]))
            negative_df[1] = negative_df['info'].apply(lambda x: x.split(' '))  # 定义一个分割函数并使用
            negative_df[2] = negative_df[1].apply(lambda x: [i for i in x if i not in stops])
            negative_df[3] = negative_df[2].apply(lambda x: ' '.join(x))

            return positive_df, negative_df
        return None, None

    def lda_(self):
        """
        LDA 主题分析
        可用于绘制： 柱状图，
        :return:
        """
        # 正面主题分析
        positive_df, negative_df = self.stop_()  # 用去除停用词后的数据
        pos_dict = corpora.Dictionary(positive_df[2])
        pos_corpus = [pos_dict.doc2bow(i) for i in positive_df[2]]
        pos_lda = models.LdaModel(pos_corpus, num_topics=3, id2word=pos_dict)
        pos_lda_list = []
        for i in range(3):
            # print('topic', i)
            pos_lda_list.append(pos_lda.print_topic(i))

        # 负面主题分析
        neg_dict = corpora.Dictionary(negative_df[2])
        neg_corpus = [neg_dict.doc2bow(i) for i in negative_df[2]]
        neg_lda = models.LdaModel(neg_corpus, num_topics=3, id2word=neg_dict)
        neg_lda_list = []
        for i in range(3):
            neg_lda_list.append(neg_lda.print_topic(i))

        return pos_lda_list, neg_lda_list


class Matlib:
    """
    画图
    """

    def word_cloud(self, string, img_path=None,
                   font_path=os.path.join(BASE_DIR, 'microblog/simfang.ttf')):
        """
        绘制词云图
        """
        # s1[2] = s1[2].apply(lambda x: ' '.join(x))
        # # print(s1[2].values)
        # s2[2] = s2[2].apply(lambda x: ' '.join(x))

        if img_path:
            # img_array = plt.imread(img_path)
            img = Image.open(img_path)
            img_array = np.array(img)
        else:
            img_array = None
        stop_words = set(STOPWORDS)
        fig = plt.figure()
        my_wordcloud = WordCloud(
            background_color='white',  # 设置背景颜色
            mask=img_array,  # 背景图片
            max_words=35,  # 设置最大显示的词数
            # 设置字体格式，字体格式 .ttf文件需自己网上下载，最好将名字改为英文，中文名路径加载可能会出现问题。
            font_path=font_path,
            stopwords=stop_words,
            max_font_size=100,  # 设置字体最大值
            random_state=50,  # 设置随机生成状态，即多少种配色方案
            # 提高清晰度
            width=1000, height=600,
            min_font_size=20,
        ).generate(string)  # ''.join(a.values)
        # ImageColorGenerator()
        # 显示生成的词云图片
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.imshow(my_wordcloud)  # 用 plt 显示图片
        plt.title('词云图')
        plt.axis('off')  # 不显示坐标
        canvas = fig.canvas
        buffer = BytesIO()
        canvas.print_png(buffer)
        data = buffer.getvalue()
        buffer.close()
        data_b64 = base64.b64encode(data).decode('utf-8')
        return data_b64

    def bar_graph(self, df):
        """
        柱状图
        :return:
        """
        fig = plt.figure()
        plt.rcParams['font.sans-serif'] = ['SimHei']
        ser1 = df.iloc[:, 2]
        print('*' * 100)
        # print(ser1)
        res_list = list()
        for i in ser1.values:
            res_list += i
        # print(res_list)
        res_dict = Counter(res_list)
        # print(res_dict.most_common(10))
        data_list = res_dict.most_common(10)
        index_list = [i[0] for i in data_list]
        height_list = [i[1] for i in data_list]
        plt.bar(
            index_list, height_list,
            # label='高频词柱状图'
        )
        plt.xlabel('出现次数最多的词')
        plt.ylabel('出现的次数')
        # plt.legend()
        plt.title('高频词柱状图')
        # plt.ylim([])
        ax = plt.gca()  # 获取当前的轴
        ax.spines['right'].set_color('none')    # 右边的轴颜色设置为无
        ax.spines['top'].set_color('none')      # 顶部的轴颜色设置为无
        for x, y in enumerate(height_list):
            plt.text(x, y + 100, y, ha='center')
        canvas = fig.canvas
        buffer = BytesIO()
        canvas.print_png(buffer)
        data = buffer.getvalue()
        buffer.close()
        data_b64 = base64.b64encode(data).decode('utf-8')
        return data_b64

    def pie_graph(self, positive_df, negative_df):
        """
        饼图绘制
        :return:
        """
        fig = plt.figure()
        plt.rcParams['font.sans-serif'] = ['SimHei']
        positive_df_len = len(positive_df)  # 正面 DataFrame 的长度
        negative_df_len = len(negative_df)  # 负面 DataFrame 的长度
        all_length = positive_df_len + negative_df_len  # 总长度
        positive_percent = round(positive_df_len/all_length, 2)
        negative_percent = round(negative_df_len/all_length, 2)
        plt.pie(
            [positive_percent, negative_percent],   # 数据
            labels=['正面', '负面'],    # 标签
            autopct='%1.1f%%',   # 自动百分比格式
            shadow=False,   # 是否显示阴影
            startangle=90,  # 开始角度
        )
        plt.title('饼图示例-正负面比率图')
        plt.axis('equal')   # 使得饼图长宽相等
        # plt.show()
        canvas = fig.canvas
        buffer = BytesIO()
        canvas.print_png(buffer)
        data = buffer.getvalue()
        buffer.close()
        data_b64 = base64.b64encode(data).decode('utf-8')
        return data_b64


if __name__ == '__main__':
    pass
    # a = Analyze(micro_blog_id='680')

    # 去除空数据
    # droped_df = a.drop_na()
    # print('*'*100)
    # print(droped_df)

    # 情感分析
    # sno_df1, sno_df2 = a.sno_nlp()
    # print('@'*100)
    # print(sno_df1)
    # print(len(sno_df1))
    # print('%'*100)
    # print(sno_df2)
    # print(len(sno_df2))
    #
    # s1, s2 = a.stop_()
    # data1 = Matlib().pie_graph(positive_df=s1, negative_df=s2)
    # print(data1)
    # print(s1['info'])
    # print(s2['info'])

    # Matlib().bar_graph(df=s1)
    # Matlib().bar_graph(df=s2)
    # 生成词云图之前先处理数据（处理列表为字符串）
    # print(' '.join(s1[1].values))
    # background_img = os.path.join(BASE_DIR, 'static/xin.jpg')
    # data1 = Matlib().word_cloud(' '.join(s1[3].values), img_path=background_img)
    # print(data1)

    # Matlib().word_cloud(' '.join(s2[2].values), img_path=background_img).show()

    # s1, s2 = a.stop_()
    # data1 = Matlib().bar_graph(df=s1)
    # print(data1)
    # Matlib().bar_graph(df=s2)


