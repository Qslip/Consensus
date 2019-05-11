import threading

from django.shortcuts import render
from microblog.wb_spider import WbSpider
# Create your views here.

def home(request):
    context = {}
    return render(request, 'microblog/index.html', context)


def index(request):

    context = {}
    return render(request, 'microblog/index.html', context)
