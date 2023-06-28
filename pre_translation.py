import copy
import functools
import hashlib as hs
import json
import shutil
import sys
import os
import random

RUN_ASS_CONVERSION = True
try:
    from ass_conversion import run_conversion
except (ModuleNotFoundError, ImportError):
    print("无法从ass_conversion.py中导入转换逻辑，srt->ass自动转换将不可用")
    RUN_ASS_CONVERSION = False
try:
    import whisper.whisper as whisper
except (ModuleNotFoundError, ImportError):
    print("Failed to import whisper.whisper, trying 'import whisper' instead")
    import whisper
import subprocess
import time

import requests

from audio_slicer import process

print("Version 2023-6-28 21:23")
TMP_FILES_PATH = "__tmp_pre_translation__"
RUN_TRANSLATION = True  # 不要动这两个变量，即便它看上去能被你修改(当前代码版本这两个变量必须为True否则无法正常运行)
RUN_WHISPER = True  # 仅供调试使用

"""
    MODEL信息：
        模型等级	    参数量    	英语模型(如果用其他语言不用看)	模型名称(MODEL变量内容) 显存需求      	相对处理速度
        tiny	    39 M	    tiny.en	                    tiny	             ~1 GB	        ~32x
        base	    74 M	    base.en	                    base	             ~1 GB	        ~16x
        small	    244 M	    small.en	                small	             ~2 GB	        ~6x
        medium	    769 M	    medium.en	                medium	             ~5 GB	        ~2x
        large-v2	1550 M	    N/A	                        large-v2	         ~10 GB	        1x
"""

MODEL = "large-v2"
ARGS_GENERAL = {
    "threshold": -40,
    "min_length": 5000,
    "min_interval": 300,
    "hop_size": 10,
    "max_sil_kept": 500,
}
ARGS_CONS = {
    "threshold": -40,
    "min_length": 6000,
    "min_interval": 800,
    "hop_size": 10,
    "max_sil_kept": 500,
}
ARGS_RADI = {
    "threshold": -40,
    "min_length": 18000,
    "min_interval": 1400,
    "hop_size": 10,
    "max_sil_kept": 500,
}

ARGS_BAT1 = {
    "threshold": -40,
    "min_length": 10000,
    "min_interval": 1000,
    "hop_size": 10,
    "max_sil_kept": 500,
}

ARGS_BAT2 = {
    "threshold": -40,
    "min_length": 14000,
    "min_interval": 1200,
    "hop_size": 10,
    "max_sil_kept": 500,
}

runtime_args = [ARGS_CONS, ARGS_RADI, ARGS_GENERAL, ARGS_BAT1, ARGS_BAT2]
output_rename_rules = ["CONS", "RADI", "GENE", "BAT1", "BAT2"]
output_filter = [True, False, False, False, False]


def cmp(a, b):
    a = int(a.split(".")[-2].split("_")[-1])
    b = int(b.split(".")[-2].split("_")[-1])
    if a < b:
        return 1
    elif a > b:
        return -1
    else:
        return 0


def ms_to_srt_timestamp(ms):
    seconds = ms // 1000
    ms -= seconds * 1000
    minutes = seconds // 60
    seconds -= minutes * 60
    hours = minutes // 60
    minutes -= hours * 60
    return f"{hours}:{minutes}:{seconds},{ms}"


# 百度翻译api信息填在这里
ID = 20230409001635057
KEY = "uGwHlJA5mn9FfBRi3Akf"

print("即将使用whisper模型", MODEL, "，如需更改请编辑源代码MODEL变量")
lan = "Japanese"  # 设置为Auto以自动识别语言
fl_r = input("音频地址：").replace('"', "")
video_s = input("生肉视频地址：").replace('"', "")
video_d = input("预翻译输出地址：").replace('"', "")
rt = 5 if input("是否以扩充参数集运行?(输入y以使用扩充参数集)").lower() == "y" else 2
print("正在加载模型：", MODEL, "，语言：", lan)
model = whisper.load_model(MODEL)


def run(file_r, video_src, video_dst, slicing_args, burn=False, folder_name=None):
    print("正在分割音频")
    print(file_r, video_src, video_dst, slicing_args)
    file_r = process(file_r, slicing_args)
    fl = ''
    flt = []
    whisper_data = {}
    whisper_data_translated = {}
    print("正在生成时间轴与识别信息")
    fln = 0
    for root, dirs, files in os.walk(file_r):
        files = list(files)
        fln = len(files)
        fln += 1
        for ct, file in enumerate(files):
            print("\b" * 114 + "处理进度:" + str(round(ct / fln * 100, 2)) + "%" + f", {ct}/{fln - 1}", end="")
            sys.stdout.flush()
            flt.append(file)
            if lan.title() == "Auto":
                results = model.transcribe(os.path.join(root, file), fp16=False)
            else:
                results = model.transcribe(os.path.join(root, file), fp16=False, language=lan)
            whisper_data[file] = results
            # print("Finished one")

    flt.sort(key=functools.cmp_to_key(cmp))
    flt.reverse()
    print("\nwhisper运行结束，开始翻译")
    if RUN_TRANSLATION:
        for ct, file in enumerate(flt):
            print("\b" * 114 + "已完成项目数：", ct, ",", "总数", len(flt), end="")
            sys.stdout.flush()
            try:
                data = whisper_data[file]
                prt = {}
                for count, cont in enumerate(data['segments']):
                    try:
                        retry = 0
                        while True:
                            if retry > 3:
                                raise RuntimeError("Error occurred")
                            time.sleep(0.05)
                            key = hs.md5()
                            ch = cont['text']
                            rd = random.randint(1145140, 19198100)
                            sg = str(ID) + ch + str(rd) + KEY
                            key.update(sg.encode())
                            key = key.hexdigest()
                            params = {"q": ch, "from": "jp", "to": "zh", "appid": str(ID), "salt": str(rd), "sign": key}
                            res = requests.get("https://fanyi-api.baidu.com/api/trans/vip/translate", params=params)
                            trt: dict = json.loads(res.content)
                            try:
                                trt: str = trt["trans_result"][0]['dst']
                            except (IndexError, KeyError) as err:
                                retry += 1
                                print("Failed to translate", ch, str(err), ", retrying in 0.1 seconds --", trt)
                                continue
                            trt: str = trt.replace("卡夫", "花谱")
                            prt[count] = {'start': cont['start'], 'end': cont['end'], 'raw': cont['text'], 'trans': trt}
                            break
                    except Exception as err:
                        print("\n处理", file, "时发生错误，项目包含的对应片段将为空=>", str(err))
                whisper_data_translated[file] = prt
            except Exception as error:
                print("E=>", str(error))
    print("\n正在修正与合并srt文件")
    index = 0
    pd = []
    for file in flt:
        try:
            data: dict = whisper_data_translated[file]
            start = int(file.split(".")[-2].split("_")[-3])
            for cnt in range(len(data.keys())):
                cont = [str(index), ms_to_srt_timestamp(int(start + data[cnt]['start'] * 1000)) +
                        " --> " + ms_to_srt_timestamp(int(start + data[cnt]['end'] * 1000)), data[cnt]['raw'],
                        data[cnt]['trans']]
                index += 1
                pd.append("\n".join(cont))
        except Exception as err:
            print("ERROR=>", str(err))

    fn = file_r.split("\\")[-1]
    sp = os.sep
    try:
        os.mkdir(f".{sp}srt")
    except Exception:
        pass
    if not folder_name:
        folder_name = fn.split(sp)[-1].split('.')[0]
    try:
        os.mkdir(f".{sp}srt{sp}{folder_name}")
    except (OSError, FileExistsError) as err:
        # print(str(err))
        pass
    print("写入字幕文件：", f'{fn}_trans.srt')
    open(f'{fn}_trans.srt', "w", encoding="utf-8").write("\n\n".join(pd))
    open(f".{sp}srt{sp}{folder_name}{sp}{fn}_trans.srt", "w", encoding="utf-8").write(
        "\n\n".join(pd))
    if RUN_ASS_CONVERSION:
        run_conversion(f".{sp}srt{sp}{folder_name}{sp}{fn}_trans.srt")
        exec_fl = f"{fn}_trans.ass"
    else:
        print("警告：未能执行ass转换")
        exec_fl = f"{fn}_trans.srt"
    if burn:
        print("正在烧录字幕")
        try:
            subprocess.run(f"ffmpeg -i {video_src} -vf subtitles={exec_fl} -y {video_dst}")
        except Exception as err_ffmpeg:
            print(f"ffmpeg执行失败!({str(err_ffmpeg)})")
    print("字幕文件已写入srt目录以供参考")


raw_fl_r = fl_r
srt_folder = raw_fl_r.split(os.path.sep)[-1].split(".")[0]
sp = os.path.sep
try:
    first_run = False
    for x in range(rt):
        try:
            os.mkdir(sp.join(raw_fl_r.split(sp)[0:-1]) + sp + TMP_FILES_PATH)
        except Exception as error:
            if first_run:
                print("在音频同目录下创建临时文件目录失败", str(error), "")
        shutil.copy(raw_fl_r,
                    f"{sp}".join(raw_fl_r.split(sp)[0:-1]) + sp + TMP_FILES_PATH + sp + output_rename_rules[x] + "_" +
                    raw_fl_r.split(sp)[
                        -1])
        fl_r = f"{sp}".join(raw_fl_r.split(sp)[0:-1]) + sp + TMP_FILES_PATH + sp + output_rename_rules[x] + "_" + \
               raw_fl_r.split(sp)[
                   -1]
        print("复制：", fl_r)
        try:
            print("分割参数:", output_rename_rules[x], "按下CTRL+C以跳过本次运行")
            run(fl_r, video_s, sp.join(video_d.split(sp)[0:-1]) + sp + output_rename_rules[x] + "_" +
                video_d.split(sp)[-1], runtime_args[x], output_filter[x], folder_name=srt_folder)
        except Exception as err:
            print("处理", output_rename_rules[x], "时出现错误：", str(err))
        except KeyboardInterrupt:
            print("跳过处理：", output_rename_rules[x])
        first_run = False
        print("删除文件", fl_r)
        os.remove(fl_r)
finally:
    print("运行结束")
input("按回车键退出")
