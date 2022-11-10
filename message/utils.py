from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import exception_handler


def app_response(data, status=None, is_errors=False):
    if is_errors:
        data = convert_errors(data, status_code=status)
    else:
        data.update({"status": status if status else status.HTTP_200_OK})
        if "results" in data:
            result = data["results"]
            del data["results"]
            data.update({"result": result})
    return Response(data, status=status, content_type="application/json")


# base
def convert_errors(dict_error, status_code=None):
    data = {"errors": {}}
    for field, value in dict_error.items():
        if field in settings.KEY_NOT_CONVERT_EXCEPTIONS:
            data["errors"].update({field: value})
        elif field not in settings.KEY_NOT_EXCEPTIONS:
            if isinstance(value, str):
                data["errors"].update({field: value})
            elif isinstance(value, list):
                if isinstance(value[0], dict):
                    for err in value:
                        if isinstance(err, dict):
                            tmp = {}
                            convert_dict_errors(err, tmp)
                            data["errors"].update(tmp)
                else:
                    data["errors"].update({field: value[0]})
            elif isinstance(value, dict):
                tmp = {}
                convert_dict_errors(value, tmp)
                data["errors"].update(tmp)
            else:
                data["errors"].update({field: value})
        else:
            data.update({field: value})
    if status_code:
        data.update({"status": status_code})
    return data


def convert_dict_errors(errors, tmp):
    for key, value in errors.items():
        if isinstance(value, str):
            tmp.update({key: value})
        elif isinstance(value, list):
            convert_list_error(value, key, tmp)
        elif isinstance(value, dict):
            convert_dict_errors(value, tmp)


def convert_list_error(error, key, tmp):
    for err in error:
        if isinstance(err, str):
            tmp.update({key: err})
        elif isinstance(err, list):
            tmp.update(convert_list_error(err, key, tmp))
        elif isinstance(err, dict):
            convert_dict_errors(err, tmp)


def convert_exception(e):
    result = {}
    for key, value in e.items():
        result.update({key: value.get("string", "")})
    return result


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        response.data = convert_errors(response.data, response.status_code)
    return response
