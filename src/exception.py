import sys


def log_e() -> str:
    """
    Log the details of an exception.

    Returns:
        str: A formatted string containing information about the error.
    """
    e_c, e_m, exc_tb = sys.exc_info()
    file_name = exc_tb.tb_frame.f_code.co_filename
    return f"Error occured in [{file_name}], line [{exc_tb.tb_lineno}], [{e_c.__name__}: {e_m}]"


if __name__ == "__main__":
    try:
        1 / 0
    except Exception as e:
        print(log_e(e))
