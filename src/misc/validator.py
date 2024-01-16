from ast import List
import validators


def is_valid_url(url: str) -> bool:
    return validators.url(url)


def is_all_fields_blank(array: List) -> bool:
    return all(not item for item in array)
