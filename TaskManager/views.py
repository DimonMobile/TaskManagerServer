from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed, HttpResponseBadRequest, \
    HttpResponseForbidden, Http404
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

    created_count = Issue.objects.filter(creator=user).count()
    assigned_count = Issue.objects.filter(assignee=user).count()
    assigned_feature = Issue.objects.filter(assignee=user, issue_type=0).count()
    assigned_bug = Issue.objects.filter(assignee=user, issue_type=1).count()
    result['created_count'] = created_count
    result['assigned_count'] = assigned_count
    result['assigned_feature'] = assigned_feature
    result['assigned_bug'] = assigned_bug

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

    if not projects_dictionary.first().owner == user:
        return JsonResponse({'result': 'error', 'error_code': 13})  # access denied

    issue = Issue(name=issue_name, description=issue_description, estimate=issue_estimate, creator=user, assignee=None
                  , project=projects_dictionary.first(), issue_type=issue_type)

    issue.save()
    if issue.id is None:
        return JsonResponse({'result': 'error', 'error_code': 12})  # unexpected error
    return JsonResponse({'result': 'success', 'id': issue.id})


def assign_issue(request):
    if not request.method == 'POST':
        return HttpResponseNotAllowed()

    token = request.POST.get('token')
    issue_id = request.POST.get('id')
    assignee_email = request.POST.get('assignee')

    if token is None or issue_id is None or assignee_email is None:
        return HttpResponseBadRequest()

    issue_id = int(issue_id.strip())
    assignee_email = assignee_email.strip().lower()

    current_user = token_to_user(token)
    if current_user is None:
        return HttpResponseForbidden()

    issues = Issue.objects.filter(id=issue_id)
    if len(issues) == 0:
        return Http404()

    current_issue = issues.first()
    if not current_issue.creator == current_user:
        return HttpResponseForbidden()

    found_users = UserProfile.objects.filter(email__contains=assignee_email)
    if len(found_users) == 0:
        return JsonResponse({'result': 'error', 'error_code': 14})  # User not found
    elif len(found_users) > 1:
        return JsonResponse({'result': 'error', 'error_code': 15})  # Too many users
    else:
        found_user = found_users.first()
        current_issue.assignee = found_user
        current_issue.save()
        can_edit = current_issue.creator == current_user
        can_log = current_issue.assignee == current_user
        return JsonResponse({'result': 'success', 'user_email': found_user.email, 'can_edit': can_edit,
                             'can_log': can_log})


def get_issue(request):
    if not request.method == 'POST':
        return HttpResponseNotAllowed()

    token = request.POST.get('token')
    issue_id = request.POST.get('id')

    if token is None or issue_id is None:
        return HttpResponseBadRequest()

    issue_id = int(issue_id.strip())

    current_user = token_to_user(token)
    if current_user is None:
        return HttpResponseForbidden()

    issues = Issue.objects.filter(id=issue_id)
    if len(issues) == 0:
        return Http404()

    issue = issues.first()

    issue_item = {
        'id': issue.id,
        'name': issue.name,
        'estimate': issue.estimate,
        'description': issue.description,
        'project_name': issue.project.name,
        'issue_type': issue.issue_type,
        'created': str(issue.created),
        'resolved': issue.resolved,
        'status': issue.status,
        'progress': issue.progress,
        'can_edit': issue.creator == current_user,
        'can_log': issue.assignee == current_user
    }
    issue_creator = {
        'id': issue.creator.id,
        'name': issue.creator.name,
        'email': issue.creator.email
    }
    if issue.assignee is None:
        issue_assignee = None
    else:
        issue_assignee = {
            'id': issue.assignee.id,
            'name': issue.assignee.name,
            'email': issue.assignee.email
        }
    issue_item['creator'] = issue_creator
    issue_item['assignee'] = issue_assignee
    return JsonResponse({'result': 'success', 'issue': issue_item})


def get_issues(request):
    if not request.method == "POST":
        return HttpResponseNotAllowed()

    issue_status = request.POST.get("status")
    issue_type = request.POST.get("type")
    issue_variant = request.POST.get("variant")
    issue_search_string = request.POST.get("s")
    token = request.POST.get("token")

    if issue_status is None or issue_type is None or issue_variant is None or token is None or\
            issue_search_string is None:
        return HttpResponseBadRequest()

    user = token_to_user(token)
    if user is None:
        return HttpResponseForbidden()

    issue_status = int(issue_status.strip())
    issue_type = int(issue_type.strip())
    issue_variant = int(issue_variant.strip())
    issue_search_string = issue_search_string.strip()

    result_query_set = Issue.objects

    if issue_status == 1:  # open issues
        result_query_set = result_query_set.filter(status=0)
    elif issue_status == 2:  # resolved issues
        result_query_set = result_query_set.filter(status=1)

    if issue_variant == 1:  # assigned to user
        result_query_set = result_query_set.filter(assignee=user)
    elif issue_variant == 2:
        result_query_set = result_query_set.filter(creator=user)

    if issue_type == 1:
        result_query_set = result_query_set.filter(issue_type=0)
    elif issue_type == 2:
        result_query_set = result_query_set.filter(issue_type=1)

    if len(issue_search_string) > 0:
        result_query_set = result_query_set.filter(name__contains=issue_search_string)

    items_count = result_query_set.count()

    result_query_set = result_query_set.all()[:200]

    result_array = []
    for issue in result_query_set:
        issue_item = {
            'id': issue.id,
            'name': issue.name,
            'estimate': issue.estimate,
            # 'description': issue.description,  # unnecessary in preview
            'project_name': issue.project.name,
            'issue_type': issue.issue_type,
            # 'created': issue.created,
            # 'resolved': issue.resolved,
            'status': issue.status,
            'progress': issue.progress,
        }
        issue_creator = {
            'id': issue.creator.id,
            'name': issue.creator.name,
            'email': issue.creator.email
        }
        if issue.assignee is None:
            issue_assignee = None
        else:
            issue_assignee = {
                'id': issue.assignee.id,
                'name': issue.assignee.name,
                'email': issue.assignee.email
            }
        issue_item['creator'] = issue_creator
        issue_item['assignee'] = issue_assignee
        result_array.append(issue_item)

    return JsonResponse({'result': 'success', 'count': items_count, 'items': result_array})


def log_work(request):
    if not request.method == 'POST':
        return HttpResponseNotAllowed()

    token = request.POST.get('token')
    issue_id = request.POST.get('id')
    time = request.POST.get('time')

    if token is None or issue_id is None or time is None:
        return HttpResponseBadRequest()

    issue_id = int(issue_id.strip())

    current_user = token_to_user(token)
    if current_user is None:
        return HttpResponseForbidden()

    issues = Issue.objects.filter(id=issue_id)
    if len(issues) == 0:
        return Http404()

    issue = issues.first()
    if not issue.assignee == current_user:
        return HttpResponseForbidden()

    time = int(time.strip())

    if time < 0:
        return HttpResponseBadRequest()

    issue.progress += time
    issue.save()

    return JsonResponse({'result': 'success', 'summary': issue.progress})


def project_statistics(request):
    project_name = request.POST.get('project')

    if project_name is None:
        return HttpResponseBadRequest()

    project_name = project_name.strip()

    projects = Project.objects.filter(name=project_name)
    if len(projects) == 0:
        return Http404()

    current_project = projects.first()
    issues = Issue.objects.filter(project=current_project, status=1)  # resolved issues for current project
    resolved_count = len(issues)
    open_count = len(Issue.objects.filter(project=current_project, status=0))
    response_array = []
    for issue in issues:
        item = {
            'real': (issue.resolved - issue.created).seconds / 60,
            'estimated': issue.estimate * 60,
            'logged': issue.progress * 60,
            'name': issue.id
        }
        response_array.append(item)

    return JsonResponse({
        'result': 'success',
        'chart1_items': response_array,
        'chart2': {
            'resolved': resolved_count,
            'open': open_count}
    })


def switch_status(request):
    if not request.method == 'POST':
        return HttpResponseNotAllowed()

    token = request.POST.get('token')
    issue_id = request.POST.get('id')
    status = request.POST.get('status')

    if token is None or issue_id is None or status is None:
        return HttpResponseBadRequest()

    issue_id = int(issue_id.strip())

    current_user = token_to_user(token)
    if current_user is None:
        return HttpResponseForbidden()

    issues = Issue.objects.filter(id=issue_id)
    if len(issues) == 0:
        return Http404()

    issue = issues.first()
    if not issue.creator == current_user and not issue.assignee == current_user:
        return HttpResponseForbidden()

    status = int(status.strip())

    issue.status = status
    issue.resolved = timezone.now()
    issue.save()
    return JsonResponse({'result': 'success', 'status': issue.status})


def re_estimate(request):
    if not request.method == 'POST':
        return HttpResponseNotAllowed()

    token = request.POST.get('token')
    issue_id = request.POST.get('id')
    time = request.POST.get('time')

    if token is None or issue_id is None or time is None:
        return HttpResponseBadRequest()

    issue_id = int(issue_id.strip())

    current_user = token_to_user(token)
    if current_user is None:
        return HttpResponseForbidden()

    issues = Issue.objects.filter(id=issue_id)
    if len(issues) == 0:
        return Http404()

    issue = issues.first()
    if not issue.creator == current_user:
        return HttpResponseForbidden()

    time = int(time.strip())

    if time < 0:
        return HttpResponseBadRequest()

    issue.estimate = time
    issue.save()

    return JsonResponse({'result': 'success', 'summary': issue.estimate})


def profile_statistics(request):
    if not request.method == 'POST':
        return HttpResponseNotAllowed()

    token = request.POST.get('token')
    if token is None:
        return HttpResponseBadRequest()

    current_user = token_to_user(token)
    if current_user is None:
        return HttpResponseForbidden()

    created_count = Issue.objects.filter(creator=current_user).count()
    assigned_count = Issue.objects.filter(assignee=current_user).count()
    assigned_feature = Issue.objects.filter(assignee=current_user, issue_type=0).count()
    assigned_bug = Issue.objects.filter(assignee=current_user, issue_type=1).count()

    return JsonResponse({'result': 'success', 'created_count': created_count, 'assigned_count': assigned_count,
                         'assigned_feature': assigned_feature, 'assigned_bug': assigned_bug})
