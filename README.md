# MGP-VJ-Tool 萌娘百科VJ条目辅助工具

Automatically generates Wikitext for Japanese VOCALOID songs, tailored specifically for the [Chinese Moegirlpedia](https://zh.moegirl.org.cn). If you are not a Chinese speaker, this project is probably useless to you.

本程序用于生成自动[萌娘百科](https://zh.moegirl.org.cn)的日语VOCALOID歌曲条目。

## 启动方法

从[releases](https://www.github.com/syccxcc/MGP-VJ-tool/releases) 下载程序。请选择与操作系统对应的压缩包。例如：Windows10用户请选择`Windows10.zip`。

将压缩包解压后运行`main`即可使用。

## 使用方法

程序会自动输出需要的信息，往里面填就行。

正常流程：
1. 提供日语曲名（必填）
2. 提供中文曲名（如果与日语曲名一样或没有翻译则留空）
3. 提供B站视频链接（如有）。如果填了，程序会询问视频是否是亲自投稿。

通过修改`config.yaml`文件，可以解锁以下功能：
1. 询问是否有投稿文。如果输入投稿文，则需要输入多行内容，结束时输入空行告诉程序输入停止。
2. 展示歌曲的封面图，并要求用户点击图片选择背景颜色，该颜色会被用在`VOCALOID_Songbox`和`VOCALOID Songbox Introduction`两个模板。
3. 自动处理中日对照的翻译。
4. 以及其它默认打开的功能，如裁剪封面图片的黑边。

如果出现无法解决的问题，程序会
1. 询问用户该怎么办。例如：在vocadb上找到多个同名歌时让用户做决定；找不到歌曲的中文翻译时要求用户提供。
2. 崩溃。遇到这种情况请联系作者修复bug。

## 可选功能

如有需求，请在Issues催更。没有列出来的功能和未修复的bug也可以催更。如果已经有人写了Issue，请点赞让开发者知道哪些功能更受欢迎。

尽量详细描述产生需要的功能或者产生bug的原因。

错误范例："用不了，总是出错"

正确范例：输入曲名xxx，视频链接xxx之后，程序输出了以下错误信息"..."
