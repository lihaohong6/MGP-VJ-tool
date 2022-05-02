from pathlib import Path
from typing import Optional, List

from models.creators import Person


def upload_image(file: Path, filename: str, song_name: str,
                 authors: Optional[List[Person]], source_url: Optional[str]):
    raise NotImplementedError("Not implemented")
    # description = (
    #         "{{Template:Copyright}}\n" +
    #         "歌曲《" + song_name + "》的封面。\n\n" +
    #         (f"源地址:{source_url}\n" if source_url else "") +
    #         (''.join([f"[[分类:作者:{author.name}]]\n" for author in authors]) if authors else "") +
    #         "[[Category:视频封面]]\n"
    # )
    # logging.debug("Image description: \n" + description)
    # bot = UploadRobot(str(file.absolute()),
    #                   description=description, use_filename=filename,
    #                   keep_filename=True,
    #                   verify_description=False, aborts=True,
    #                   ignore_warning=False, chunk_size=0,
    #                   asynchronous=False,
    #                   summary="由[[User:Lihaohong/VJ条目辅助工具|VJ条目辅助工具]]自动上传")
    # bot.run()
