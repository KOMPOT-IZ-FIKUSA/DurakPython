import logging

logging.basicConfig(filename='errors.log', level=logging.DEBUG)
def error(*args, **kwargs):
    string = ""
    for a in args:
        if isinstance(a, Exception):
            a = f"{a.__class__.__name__}{str(a.args)}"
        if len(string) > 0:
            string += " | "
        string += str(a)
    for k, v in kwargs.items():
        string += f" | {k}: {v}"
    try:
        logging.error(string)
    except Exception:
        pass
    print("\033[93m" + string + "\033[0m")