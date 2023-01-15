import os
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    # The user needs to edit some files, so can't use _MEIPASS
    application_path = Path(os.path.dirname(sys.executable))
    document_path = application_path.joinpath("_MEIPASS")
else:
    application_path = Path(os.path.dirname(os.path.abspath(__file__)))
    application_path = application_path.joinpath("..")
    document_path = application_path

# os.environ['PYWIKIBOT_DIR'] = str(application_path.absolute())
# this will be changed later when the config is loaded
program_output_path: Path = application_path.joinpath("output")


