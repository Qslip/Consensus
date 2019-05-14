from snownlp import SnowNLP
from wordcloud import WordCloud, ImageColorGenerator, STOPWORDS
from gensim import corpora, models
from collections import Counter
from PIL import Image
from io import BytesIO
import pandas as pd
import numpy as np
import sqlite3
import jieba
import base64
import matplotlib.pyplot as plt
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Analyze:
    """
        对数据进行情感分析
    """
    def __init__(self, question_id):
        #  根据 question_id 得到该 question 下的所有回答
        self.question_id = question_id

    def get_df(self):
        #   得到 dataframe 数据
        conn = sqlite3.connect(os.path.join(BASE_DIR, 'db.sqlite3'))      # 打开本地 sqlite数据库
        df_a = pd.read_sql_query('select id,arg from zhihu_zhihuanswer where question_id=%s'%self.question_id,conn)
        # print(df_a)
        df_info2 = None
        for i in df_a['id']:
            df_info1 = pd.read_sql_query('select info from zhihu_zhihuinfo where answer_id=%s'%i, conn)
            df_info2 = df_info1.append(df_info2,ignore_index=True)
        # print(df_info2)   # 察看取出的数据
        conn.close()    # 关闭数据库连接
        return df_info2

    # 去掉每句话中的重复字
    def str_unique(self, raw_str, reverse=False):
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
                try:
                    int(i)
                    continue
                except ValueError:
                    res_str += i
        if reverse:
            res_str = res_str[::-1]
        return res_str
    
    def drop_na(self):
        # 清洗数据：去空，去重，短句过滤
        df = self.get_df()
        df = df.dropna()
        df = pd.DataFrame(df.iloc[:,0].unique())
        # print(df.iloc[:,0])
        ser1 = df.iloc[:,0].apply(self.str_unique)  # type: <class 'pandas.core.series.Series'>
        df = pd.DataFrame(ser1.apply(self.str_unique, reverse=True))
        df = df.rename(columns = {0:'info'})
        # 短句过滤：
        df = df[df.iloc[:,0].apply(len) >= 4]

        return df

    def snow_nlp(self):
        # 用 snownip 情感分析
        df = self.drop_na()  # 用清洗后的数据
        coms = df.iloc[:,0].apply(lambda x: SnowNLP(x).sentiments)
        positive_df = df[coms >= 0.8 ] # 特别喜欢的
        negative_df = df[coms < 0.4 ]  # 不喜欢的

        return positive_df, negative_df

    def jie_ba(self):
        # 用 jieba 分词
        positive_df,negative_df = self.snow_nlp() #用 snownip 分析过的数据
        my_cut = lambda s:' '.join(jieba.cut(s))
        positive_ser = positive_df.iloc[:,0].apply(my_cut)  # 喜欢中的正面分词， 大于0.5
        negative_ser = negative_df.iloc[:,0].apply(my_cut)  # 不喜欢中的负面分词， 小于0.5
        return positive_ser, negative_ser

    def stop_(self):
        # 去除分词中的停用词
        stop_list = './zhihu/stoplist.txt'
        stops = pd.read_csv(stop_list, encoding='gbk', header=None, sep='tipdm', engine='python')
        # sep 设置分割词，由于csv默认以半角逗号为分割此，而该词恰好在停用词表中，因此会导致读取出错
        # 所以解决办法是手动设置一个不存在的分割词，如 tipdm ；
        positive_ser, negative_ser = self.jie_ba()   # 用分词后的数据
        stops = [' ','','人','最','／','说'] + list(stops[0].values)     # pandas 会自动省略空格符，这里手动添加
        # print('stops',stops)
        positive_df = pd.DataFrame(positive_ser)
        negative_df = pd.DataFrame(negative_ser)

        positive_df[1] = positive_df['info'].apply(lambda s:s.split(' ')) # 定义一个分割函数并使用
        positive_df[2] = positive_df[1].apply(lambda x:[i for i in x if i not in stops])
        # print(positive_df[2])
        negative_df[1] = negative_df['info'].apply(lambda s:s.split(' ')) # 定义一个分割函数并使用
        negative_df[2] = negative_df[1].apply(lambda x:[i for i in x if i not in stops])

        return positive_df, negative_df

    def lda_(self):
        # LDA 主题分析
        # 正面主题分析
        positive_df, negative_df = self.stop_()      # 用去除停用词后的数据
        pos_dict = corpora.Dictionary(positive_df[2])
        pos_corpus = [pos_dict.doc2bow(i) for i in positive_df[2]]
        pos_lda = models.LdaModel(pos_corpus, num_topics=3, id2word=pos_dict)
        pos_lda_list = []
        for i in range(3):
            # print('topic',i)
            pos_lda_list.append(pos_lda.print_topic(i))

        # 负面主题分析
        neg_dict = corpora.Dictionary(negative_df[2])
        neg_corpus = [neg_dict.doc2bow(i) for i in negative_df[2]]
        neg_lda = models.LdaModel(neg_corpus, num_topics=3, id2word=neg_dict)
        neg_lda_list = []
        for i in range(3):
            neg_lda_list.append(neg_lda.print_topic(i))
        
        return pos_lda_list, neg_lda_list


# a,b = Analyze(67).stop_()
# print('a',a)
# print('b',b)
# with open('./zhihu/stoplist.txt') as f:
#     print(f.read())

class Matlib:
    """
        画图
    """
    def word_cloud(self, string, img_path=None,
    font_path='./static/fonts/simfang.ttf',):
        """ 绘制词云 """
        # 示例  : a,b = Analyze(67).jie_ba()  Matlib().word_cloud(''.join(a.values))  jieba 词的分析
        if img_path:
            img = Image.open(img_path)
            img_array = np.array(img)
        else:
            img_array = None
        my_wordcloud = WordCloud(
            background_color='white',  # 设置背景颜色
            mask=img_array,  # 背景图片
            max_words=200,  # 设置最大显示的词数
            # 设置字体格式，字体格式 .ttf文件需自己网上下载，最好将名字改为英文，中文名路径加载可能会出现问题。
            font_path=font_path,
            max_font_size=100,  # 设置字体最大值
            random_state=50,  # 设置随机生成状态，即多少种配色方案
            ##提高清晰度
            width=1000,height=600,
            min_font_size=20,
        ).generate(string)      # ''.join(a.values)
        fig = plt.figure()
        #解决matplotlib显示中文乱码的问题
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['font.family']='sans-serif'
        # 生成的词云图片
        plt.imshow(my_wordcloud)    # 用 plt 显示图片
        plt.axis('off') # 不显示坐标
        canvas = fig.canvas
        buffer = BytesIO()
        canvas.print_png(buffer)
        data = buffer.getvalue()
        buffer.close()
        data_b64 = base64.b64encode(data).decode('utf-8')
        # print('*'*100,data_b64[0:10])
        # plt.show()  # 显示图片
        # f = BytesIO()  # 创建一个内存地址
        # my_wordcloud.to_file('word.png')    # 保存图片
        # img_ = Image.open('word.png')   # 打开图片
        return data_b64        # 返回保存到内存的图片，以字节的形式返回图像的png版本
        # return plt

    def frequency(self,vs_list):
        """ 高频词的柱状图 """
        # 示例： a,b = Analyze(67).stop_()  Matlib().frequency(a[2].values)
        v_list = []
        for i in list(vs_list):
            v_list = v_list+i
        # print(v_list)
        c = Counter(v_list).most_common(10)  # 最多十组
        name_list = [x[0] for x in c]
        num_list = [x[1] for x in c]
        fig = plt.figure()
        #解决matplotlib显示中文乱码的问题
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['font.family']='sans-serif'
        b = plt.bar(range(len(num_list)), num_list, tick_label=name_list)
        print('c',c)
        plt.xlabel('热词')
        plt.ylabel('次数')
        plt.title('热词频率统计')
        canvas = fig.canvas
        buffer = BytesIO()
        canvas.print_png(buffer)
        data = buffer.getvalue()
        buffer.close()
        data_b64 = base64.b64encode(data).decode('utf-8')
        # plt.show()  # 显示图片
        # f = BytesIO()  # 创建一个内存地址
        # plt.savefig("fre.png")    # 保存图片
        # img_ = Image.open('fre.png')   # 打开图片
        return data_b64        # 返回保存到内存的图片，以字节的形式返回图像的png版本

# print(a[2].values)
# Matlib().frequency(b[2].values)
a,b = Analyze(67).jie_ba()  
Matlib().word_cloud(''.join(a.values))


