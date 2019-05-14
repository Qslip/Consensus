from django.shortcuts import render, redirect
from users.models import User
from django.contrib.auth import login, logout



def register_index(request):
    # 注册
    if request.method == 'POST':
        info = request.POST
        username = info.get('username', None)
        password = info.get('password', None)
        conpassword = info.get('conpassword', None)
        if username and password and conpassword:
            try:
                User.objects.get(username=username)
            except User.DoesNotExist:
                if 20 > len(username) > 2:
                    if 20 > len(password) > 5:
                        if password == conpassword:
                            User.objects.create_user(username=username, password=password)
                            context = {'success': '用户创建成功！', 'logining': True}
                            return render(request, 'users/user_index.html', context)

                        context = {'error': '两次密码不一致！', 'registering': True}
                        return render(request, 'users/user_index.html', context)

                    context = {'error': '密码长度应大于5位，小于20位！', 'registering': True}
                    return render(request, 'users/user_index.html', context)

                context = {'error': '用户名应大于2位，小于20位！', 'registering': True}
                return render(request, 'users/user_index.html', context)

            context = {'error': '该用户名已存在！', 'registering': True}
            return render(request, 'users/user_index.html', context)
        else:
            context = {'error': '请输入用户名、密码、确认密码！', 'registering': True}
            return render(request, 'users/user_index.html', context)
    context = {'registering': True}
    return render(request, 'users/user_index.html', context)


def login_index(request):
    # 登录
    if request.method == 'POST':
        info = request.POST
        username = info.get('username', None)
        password = info.get('password', None)
        try:
            user_obj = User.objects.get(username=username)
        except User.DoesNotExist:
            return render(request, 'users/user_index.html', {'error': '用户名不存在', 'logining': True})
        if user_obj.check_password(password):
            login(request, user_obj)
            return redirect('microblog:microblog_index')
        return render(request, 'users/user_index.html', {'error': '密码错误', 'logining': True})
    context = {'logining': True}
    return render(request, 'users/user_index.html', context)


def logout_index(request):
    logout(request)
    return redirect('microblog:microblog_index')
