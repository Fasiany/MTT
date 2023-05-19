# MTT

~~上传之前进行了一些修改，应该能直接用不会出问题的吧~~

一些平时用来加快翻译进程的小玩意儿，主要文件：

`pre_translation.py` 音频识别+字幕识别+翻译功能的整合。识别功能要求安装whisper

`srt_align.py` 给定一个srt目标时间戳和一个srt文件，计算srt文件第一条字幕与目标时间戳的偏移量并应用在文件中的每一条字幕上，输出文件为`[原文件名]_Aligned.srt`。一般用来复用之前的歌词字幕

`add_tag.py` 给定一个srt文件，每次给出开始和结束时间戳，对目标时间戳内的所有字幕前打上一个标记，一般用于为 `ass_conversion.py` 标注大量歌词。原装可用标记为`!s|`(淡蓝色歌词), `!s2|`(绿色译注), 默认没标记为粉色。注意：打标记直接在原文件上进行

`ass_conversion.py` 把srt文件转换成ass文件，字幕样式由每条字幕前的标记决定。输出文件名与原文件一致(除了扩展名)。需要更多标记或添加修改样式可照着源代码自行修改

`scr.py` 快速删掉双语字幕的日语部分(每段字幕信息中的第3条，如果有歌词标记则不删)，输出为`[原文件名]_SCR.srt`

其他东西是前置，放在同一目录就行。audio_slicer修改自[openvpi的audio_slicer](https://github.com/openvpi/audio-slicer)

# 环境配置

下文假定已配置完毕虚拟环境

如果用不到`pre_translation.py`，克隆仓库后执行

`pip install -r requirements.txt`

即可

如果需要使用`pre_translation.py`，需要额外安装**whisper**并自行配置**pytorch**与**cuda**

此处省略**pytorch**与**cuda**配置流程。相关教程可在网上查阅

如果你不知道什么是**whisper**或应该使用哪个模型，请查看[此仓库](https://github.com/openai/whisper)

安装**whisper**:

`pip install -U openai-whisper`

`pip install --upgrade --no-deps --force-reinstall git+https://github.com/openai/whisper.git`

# 一些注意事项

`pre_translation.py`默认情况下使用两种参数集运行两次，旨在查看最后结果时相互对照以降低错误率

"参数集"此指分割音频时所用的一系列参数的总称，不同的参数集通常会产生不同的结果。5个参数集名称为CONS(默认), GENE, BAT1, BAT2, RADI(默认)。按照切割结果单体平均长度排序

初次使用`pre_translation.py`的翻译功能时，需要先配置百度翻译api的ID与KEY。也可以选择更改whisper的运行参数并将源代码中翻译部分更改为使用本地英译中模型(不包含于源代码中，需要自行编写相关代码)

whisper有时会因未知原因报错退出，此时本轮次将处理失败并导致缺失使用本次参数集的翻译识别结果。如果出现这种情况，可在开始运行时选择使用扩充的三个参数集(原为两个，均为默认情况下两个参数集的不同折中)以弥补报错中止导致的翻译识别结果空缺

默认情况下`pre_translation.py`仅在CONS参数集运行成功后会将翻译识别结果烧入生肉视频并输出。其余参数集翻译识别结果不会自动烧写

~~一开始没想着公开所以代码基本**没有注释**~~
