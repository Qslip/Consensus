# -*- coding: utf-8 -*-
"""
   Product:      PyCharm
   Project:      Consensus
   File:         my_thread
   Author :      ZXR 
   date：        2019/5/11
   time:         14:04 
"""
import threading, time


# MyThread.py线程类
class MyThread(threading.Thread):
    def __init__(self, func, args=()):
        super(MyThread, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        # time.sleep(2)
        self.result = self.func(*self.args)

    def get_result(self):
        # threading.Thread.join(self)  # 等待线程执行完毕
        try:
            return self.result
        except Exception as e:
            print(e)
            return None


def add(a, b):
    return a + b


if __name__ == "__main__":
    print(time.time())
    list = [23, 89]
    # 创建4个线程
    pool = []
    for i in range(4):
        task = MyThread(add, (list[0], list[1]))
        pool.append(task)
    res = []
    for t in pool:
        t.start()
    for t in pool:
        t.join()
        res.append(t.get_result())
    print(res)
    print(time.time())

    # res = []
    # for i in range(4):
    #     res.append(add(list[0], list[1]))
    # print(res)
    # print(time.time())


