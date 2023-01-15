import gettext

from config.path_config import document_path

target_dir = document_path.joinpath("i18n")
gettext.bindtextdomain('domain', target_dir)
gettext.textdomain('domain')
trans = gettext.gettext


def get_trans(s: str):
    return trans(s)


_ = get_trans


def set_language(lang: str = 'en'):
    global trans
    trans = gettext.translation('domain', target_dir, (lang,)).gettext
