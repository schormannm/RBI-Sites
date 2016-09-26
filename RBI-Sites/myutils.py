import dateparser
import datetime
import string


def format_date(userdate):
    date = dateparser.parse(userdate)
    try:
        return datetime.datetime.strftime(date, "%Y-%m-%d")
    except TypeError:
        return None


def sanitize_string(userinput):
    whitelist = string.letters + string.digits + " !?.,;:-'()&"
    return filter(lambda x: x in whitelist, userinput)

