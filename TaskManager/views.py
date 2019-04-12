from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed, HttpResponseBadRequest
from django.core.validators import validate_email, ValidationError
from TaskManager.models import UserProfile

import datetime
import hashlib


def index(request):
    return HttpResponse("<h1>TaskManager Server</h1><br><h5>Web interface not supported, use TaskManager application</h5>")


def server_test(request):
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])

    response = {"status": True,
                "server_time": datetime.datetime.now(),
                "system_uptime": uptime_seconds}

    return JsonResponse(response)


def user_data(request):
    result = {'result': 'error', 'error_code': 5}

    if request.POST.get("email") is None or request.POST.get('password') is None:
        return JsonResponse(result)

    email = request.POST.get("email").lower()
    password = hashlib.sha3_256(request.POST.get("password").encode()).hexdigest()

    users = UserProfile.objects.filter(email=email)

    if len(users) == 0:
        return JsonResponse(result)
    found_user = users[0]
    user_result = {}
    if found_user.password == password:
        user_result['name'] = found_user.name
        user_result['email'] = found_user.email
        user_result['registration_date'] = found_user.register_date
        user_result['language'] = found_user.lang
        result = {'result': 'success', 'user': user_result}

    return JsonResponse(result)


def register(request):
    if not request.method == "POST":
        return HttpResponseNotAllowed()

    username = request.POST.get("name")
    email = request.POST.get("email")
    password = request.POST.get("password")
    language = request.POST.get("language")

    error_codes = []

    if username is None or 3 > len(username) or len(username) > 20:
        error_codes.append(0)

    if password is None or 8 > len(password) or len(password) > 64:
        error_codes.append(1)

    if email is not None:
        try:
            validate_email(email)
            if len(UserProfile.objects.filter(email=email.lower())) > 0:
                error_codes.append(3)
        except ValidationError:
            error_codes.append(2)
    else:
        error_codes.append(2)

    if len(error_codes) > 0:
        response = {"result": "error", "items": error_codes}
    else:
        response = {"result": "success"}
        profile = UserProfile(name=username, email=email.lower(),
                              password=hashlib.sha3_256(password.encode()).hexdigest(), lang=language)
        profile.save()

    return JsonResponse(response)

