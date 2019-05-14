from django.shortcuts import render, redirect
from django.contrib.auth.models import User


def register(request):
    # 注册
    if request.method == 'POST':
        info = request.POST
        username = info['username']
        password = info['password']
        conpassword = info['conpassword']
        if username and password and 20  > len(username) > 2 and 20 > len(password) >5 :
            if password == conpassword:
                User.objects.create_user(username=username, password=password)
                return render(request, 'login.html', {})
            return render(request, 'register.html', {'error':'俩次密码不一致'})
        return render(request, 'register.html', {'error':'请输入合法数据。'})
    return render(request, 'register.html', {})

def login(request):
    # 登录
    if request.method == 'POST':
        info = request.POST
        username = info['username']
        password = info['password']
        try:
            user = User.objects.get(username=username)
        except:
            return render(request, 'login.html', {'error':'用户名不存在'})
        if user.check_password(password):
            login(request, user)
            return redirect('microblog:microblog_index')
        return render(request, 'login.html', {'error':'密码错误'})
    return render(request, 'login.html', {})

