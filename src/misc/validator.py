from ast import List
import validators
import re


def is_valid_url(url: str) -> bool:
    return validators.url(url)


def is_all_fields_blank(array: List) -> bool:
    return all(not item for item in array)


def is_valid_email(email):
    email_regex = r'^[^@]+@[^@]+\.[^@]+$'
    if (re.search(email_regex, email)):
        return True
    else:
        return False
