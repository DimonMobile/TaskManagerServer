from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed, HttpResponseBadRequest, HttpResponseForbidden
from django.core.validators import validate_email, ValidationError
from django.utils import timezone
from TaskManager.models import *

import datetime
import hashlib


def token_to_user(token):
    tokens = Token.objects.filter(token=token)
    if len(tokens) == 0:
        return None

    current_token = tokens.first()
    if current_token.expires < timezone.now():
        return None

    return current_token.user


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
    # Generate token
    token = Token.objects.filter(user=found_user)
    if not len(token) == 0:
        token[0].delete()

    generated_token = hashlib.md5((datetime.datetime.now().__str__() + found_user.name).encode()).hexdigest()
    token = Token(user=found_user, expires=timezone.now() + timezone.timedelta(days=30),
                  token=generated_token)
    token.save()

    # Prepare response
    if found_user.password == password:
        user_result['name'] = found_user.name
        user_result['email'] = found_user.email
        user_result['registration_date'] = found_user.register_date
        user_result['language'] = found_user.lang
        user_result['generated_token'] = generated_token
        result = {'result': 'success', 'user': user_result}

    return JsonResponse(result)


def remove_project(request):
    token = request.POST.get('token')

    if token is None:
        return HttpResponseBadRequest()

    user = token_to_user(token)
    if user is None:
        return HttpResponseBadRequest()

    project_name = request.POST.get('project_name')

    if project_name is None:
        return HttpResponseBadRequest()

    projects = Project.objects.filter(name=project_name)
    if len(projects) == 0:
        return HttpResponseBadRequest()

    current_project = projects.first()

    if not current_project.owner == user:
        return HttpResponseForbidden("No permissions")

    current_project.delete()
    return JsonResponse({'result': 'success'})


def add_project(request):
    token = request.POST.get("token")

    if token is None:
        return HttpResponseBadRequest()

    user = token_to_user(token)
    if user is None:
        return HttpResponseBadRequest()

    name = request.POST.get("name")
    description = request.POST.get("description")

    if name is None or description is None:
        return HttpResponseBadRequest()

    description = description.strip()
    name = name.strip()

    if len(name) < 3 or len(name) > 30:
        return JsonResponse({'result': 'error', 'error_code': 7})

    if len(Project.objects.filter(name=name)) > 0:
        return JsonResponse({'result': 'error', 'error_code': 6})

    project = Project(name=name, description=description, created=timezone.now(), owner=user)
    project.save()
    return JsonResponse({'result': 'success'})


def projects(request):
    token = request.POST.get("token")

    if token is None:
        return HttpResponseBadRequest()

    user = token_to_user(token)
    if user is None:
        return HttpResponseBadRequest()

    result = {}
    array = []
    for project in Project.objects.filter(owner=user):
        array.append(project.name)
    result['items'] = array
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


def create_issue(request):
    if not request.method == "POST":
        return HttpResponseNotAllowed()

    token = request.POST.get("token")

    if token is None:
        return HttpResponseBadRequest()

    user = token_to_user(token)
    if user is None:
        return HttpResponseBadRequest()

    issue_name = request.POST.get("name")
    issue_description = request.POST.get("description")
    issue_estimate = request.POST.get("estimate")
    issue_project = request.POST.get("project")
    issue_type = request.POST.get("type")

    if issue_name is None or issue_description is None or issue_estimate is None or\
            issue_project is None or issue_type is None:
        return HttpResponseBadRequest()

    issue_name = issue_name.strip()
    issue_description = issue_description.strip()
    issue_estimate = issue_estimate.strip()
    issue_project = issue_project.strip()
    issue_type = int(issue_type.strip())

    if len(issue_name) < 3 or len(issue_name) > 128:
        return JsonResponse({'result': 'error', 'error_code': 8})  # invalid issue name length

    if len(issue_description) > 4096:
        return JsonResponse({'result': 'error', 'error_code': 9})  # invalid issue description length

    if int(issue_estimate) < 0:
        return JsonResponse({'result': 'error', 'error_code': 10})  # issue estimate must have positive length

    projects_dictionary = Project.objects.filter(name=issue_project)
    if len(projects_dictionary) == 0:
        return JsonResponse({'result': 'error', 'error_code': 11})  # project is not exists

    issue = Issue(name=issue_name, description=issue_description, estimate=issue_estimate, creator=user, assignee=None
                  , project=projects_dictionary.first(), issue_type=issue_type)

    issue.save()
    if issue.id is None:
        return JsonResponse({'result': 'error', 'error_code': 12})  # unexpected error
    return JsonResponse({'result': 'success', 'id': issue.id})
