# MGP-VJ-Tool 自动生成萌娘百科VJ条目

Automatically generates Wikitext for Japanese VOCALOID songs, tailored specifically for the [Chinese Moegirlpedia](https://zh.moegirl.org.cn). If you are not a Chinese speaker, this project is probably useless to you.

本程序用于生成自动[萌娘百科](https://zh.moegirl.org.cn)的日语VOCALOID歌曲条目。

## 启动方法

从GitHub下载代码。

确保以下要求被满足：
* 安装了`Python3.9`或更高（3.9以下的版本可能可以，但是没有测试过），并且`Python`在`path`里。安装程序一般会自动将`Python`加入`path`，所以不用手动添加。
* 安装程序依赖的库。可以直接运行`run.bat`，也可以手动用`pip` [安装](https://packaging.python.org/en/latest/tutorials/installing-packages/#requirements-files) 。所有的依赖都在`requirements.txt`中。目前只有[requests](https://github.com/psf/requests) 和 [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/) 

运行`run.bat`（Windows）或`run.sh`（OS X），或者在命令行中输入
```shell
python3 main.py
```

## 使用方法

程序会自动输出需要的信息，往里面填就行。

正常流程：
1. 提供日语曲名（必填）
2. 提供中文曲名（如果与日语曲名一样或没有翻译则留空）
3. 提供B站视频链接（如有）。如果填了，程序会询问视频是否是亲自投稿。

如果出现无法解决的问题，程序会
1. 询问用户该怎么办。例如：在vocadb上找到多个同名歌时让用户做决定；找不到歌曲的中文翻译时要求用户提供。
2. 崩溃。遇到这种情况请联系作者修复bug。

## 可选功能

如有需求，请在Issues催更。没有列出来的功能和未修复的bug也可以催更。如果已经有人写了Issue，请点赞让开发者知道哪些功能更受欢迎。

尽量详细描述产生需要的功能或者产生bug的原因。

错误范例："用不了，总是出错"

正确范例：输入曲名xxx，视频链接xxx之后，程序输出了以下错误信息"..."

* 除了AtWiki和vocadb，可以考虑从别的网站抓取信息。没什么技术困难，但是费时间。例如抓取网易云音乐的歌词（不过Ann好像写过这个的脚本）
* 添加文件输入歌曲信息，而不是局限于控制台，避免输入半天信息结果发现输错了必须重来的尴尬。难度同上（其实可以直接用pipe达成）。
* 自动上传封面至萌娘共享。开发者不懂MW api，不会做。如果需求过多开发者可以试着学怎么整。
* 更智能的歌词选择：现在已经可以去除大部分开头与歌词无关的内容。但是不一定能适配所有AtWiki条目。