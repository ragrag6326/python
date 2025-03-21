#!/usr/bin/env python3
import sys
import urllib.parse
import os


def version_check () :

    py_versin=sys.version
    py_versin = py_versin.split(" ")[0]

    try:
        args = sys.argv[1]
    except IndexError:
        args=False
    finally :
        try :
            if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 8):
                raise Exception (f"警告: 您的 Python 版本 {py_versin} 低於 3.8 ,某些功能可能無法正常運行。請升級到 <= 3.8。")
            else:
                message = (f'Hello From Python Test Script! \nSee This Message Indicates That You Can executed Python \nSyStem Python Version is {py_versin}')
                return True
        except Exception as err :
            message = err
            return False
        
        finally:
            if args == 'show' :
                print(message)

result = version_check()
print(result)