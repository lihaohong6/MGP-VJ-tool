import gettext

from config.path_config import document_path

target_dir = document_path.joinpath("i18n")
gettext.bindtextdomain('messages', target_dir)
gettext.textdomain('messages')
trans = gettext.gettext


def get_trans(s: str):
    return trans(s)


_ = get_trans


def set_language(lang: str = 'en'):
    global trans
    trans = gettext.translation('messages', target_dir, (lang,)).gettext
