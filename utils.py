# -*- coding: utf-8 -*-

import re
import os
import sys
import bcrypt


# Func which validate fields: email, password and password confirmation.
def validate_values(email, password, re_password=None):
    pattern = re.compile(r'\w{4,35}@\w{2,10}\.\w{2,6}')

    try:
        re.match(pattern, email).group()

        if len(password) < 6:
            return False

        if re_password is not None:
            if password != re_password:
                return False

        return True

    except AttributeError:
        return False


def passwd_hashing(password):
    return bcrypt.hashpw(password, bcrypt.gensalt())


def passwd_checker(hash_, password):
    return bcrypt.checkpw(password, hash_)


def get_path(dir_name, file_name):
    path = sys.argv[0]
    path = os.path.join(os.path.dirname(path), dir_name)

    return path + '/' + file_name
