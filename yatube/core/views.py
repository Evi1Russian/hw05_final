from django.shortcuts import render
from http import HTTPStatus


def page_not_found(request, exception):
    return render(request, 'core/404.html', {'path': request.path},
                  status=HTTPStatus.NOT_FOUND)


def forbidden(request, reason=''):
    return render(request, 'core/403.html', status=HTTPStatus.FORBIDDEN)


def internal_server_eror(request, ):
    return render(request, 'core/500.html',
                  status=HTTPStatus.INTERNAL_SERVER_ERROR)
