import datetime


def print_logger(message, date_format='%m/%d/%Y %H:%M:%S'):
    """ We need to use print in order to avoid problems of misalignment between logging and  sys.stdout.write"""
    log_message = "[{date}] {message}".format(date=datetime.datetime.now().strftime(date_format), message=message)
    print(log_message)
