import datetime
import os
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from .forms import CustomUserCreationForm, FiledataForm
from .models import *
from object_detection import count_objects_in_video


def loginUser(request):
    page = 'login'
    if request.method == 'POST':
        print(request.POST)
        username = request.POST['username'].lower()
        password = request.POST['password']
        # print(username, password)
        try:
            user = User.objects.get(username=username)
            print(user)
        except User.DoesNotExist:
            print('User not found')
        user = authenticate(request, username=username, password=password)
        print(user)
        if user is not None:
            login(request, user)
            LoginHistory.objects.create(user=user.username, login_time=datetime.datetime.now())
            return redirect('homepage')
        else:
            print(request, 'Invalid username or password.')
    return render(request, 'User/login_register.html', {'page': page})


def logoutUser(request):
    logout(request)
    print(request, 'User was logged out!')
    return redirect('loginUser')


def createUser(request):
    page = 'register'
    form = CustomUserCreationForm()

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()

            print(request, 'User account was created!')

            return redirect('loginUser')

        else:
            print(request, 'An error has occurred during registration')

    context = {'page': page, 'form': form}
    return render(request, 'User/login_register.html', context)


def homepage(request):
    form = FiledataForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.save()
        return redirect('homepage')
    context = {
        'form': form,
    }
    return render(request, 'User/hompage.html', context)


def upload_video(request):
    if request.method == 'POST' and request.FILES['video']:
        uploaded_file = request.FILES['video']
        filename = uploaded_file.name
        # Ensure that the 'videos' directory exists
        video_dir = 'videos'
        if not os.path.exists(video_dir):
            os.makedirs(video_dir)
        # Save the uploaded file to a location on your server
        with open(os.path.join(video_dir, filename), 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        # Return the path to the uploaded file
        video_path = os.path.join(video_dir, filename)
        result = count_objects_in_video(video_path, "output.mp4")
        print(result)
        file_data = filedata.objects.create(
            title=filename,
            video_file=f"videos/{filename}",
            username=request.user.username,
            predatory_mites=result["feeder-mites"],
            feeder_mites=result["predatory-mites"]
        )

        return render(request, 'User/hompage.html', {'video_path': video_path})
    else:
        return render(request, 'User/hompage.html')


def admin_panel(request):
    users = User.objects.all()
    print(users)
    return render(request, 'User/admin_panel.html', {'users': users})


@login_required
def user_profile(request, user_id):
    profile = get_object_or_404(User, id=user_id)
    return render(request, 'User/user_profile.html', {'profile': profile})


def user_login_history(request, username):
    print("username: ", username)
    login_history = LoginHistory.objects.filter(user=username)
    print(login_history)
    return render(request, 'User/user_login_history.html', {'login_history': login_history})


def user_video_upload_history(request, username):
    video_upload_history = filedata.objects.filter(username=username)
    return render(request, 'User/user_video_upload_history.html', {'username': username, 'video_upload_history': video_upload_history})