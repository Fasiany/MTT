import copy
import functools
import hashlib as hs
import json
import os
import random
import subprocess
import time

import requests

from audio_slicer import process

"""
    MODEL信息：
        模型等级	    参数量    	英语模型(如果用其他语言不用看)	模型名称(MODEL变量内容) 显存需求      	相对处理速度
        tiny	    39 M	    tiny.en	                    tiny	             ~1 GB	        ~32x
        base	    74 M	    base.en	                    base	             ~1 GB	        ~16x
        small	    244 M	    small.en	                small	             ~2 GB	        ~6x
        medium	    769 M	    medium.en	                medium	             ~5 GB	        ~2x
        large-v2	1550 M	    N/A	                        large-v2	         ~10 GB	        1x
"""

MODEL = "medium"
RUN_WHISPER = False if input("是否跳过whisper识别?(输入y跳过，对所有参数集生效)").strip().lower() == "y" else True
RUN_TRANSLATION = False if input("是否跳过翻译?(输入y跳过，对所有参数集生效)").strip().lower() == "y" else True
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


def sec_to_srt_timestamp(ms):
    seconds = ms // 1000
    ms -= seconds * 1000
    minutes = seconds // 60
    seconds -= minutes * 60
    hours = minutes // 60
    minutes -= hours * 60
    return hours, minutes, seconds, ms


# 百度翻译api信息填在这里
ID = 00000000000000000
KEY = "YourKey"

print("即将使用whisper模型", MODEL, "，如需更改请编辑源代码MODEL变量")
fl_r = input("音频地址：").replace('"', "")
video_s = input("生肉视频地址：").replace('"', "")
video_d = input("预翻译输出地址：").replace('"', "")
rt = 5 if input("是否以扩充参数集运行?(输入y以使用扩充参数集)").lower() == "y" else 2


def run(file_r, video_src, video_dst, slicing_args, burn=False):
    print("正在分割音频")
    print(file_r, video_src, video_dst, slicing_args)
    file_r = process(file_r, slicing_args)
    fl = ''
    flt = []
    print("正在运行whisper")
    for root, dirs, files in os.walk(file_r):
        for ct, file in enumerate(files):
            flt.append(file)
            fl += f'"{os.path.join(root, file)}" '
    flt.sort(key=functools.cmp_to_key(cmp))
    flt.reverse()
    if RUN_WHISPER:
        subprocess.run(fr'whisper {fl} --language Japanese --model {MODEL}')
    print("whisper运行结束，开始翻译")
    if RUN_TRANSLATION:
        for ct, file in enumerate(flt):
            print("文件进度：", ct)
            data = open(file.split(".")[-2] + ".srt", encoding="utf-8").read().split("\n\n")
            try:
                sm = int(data[-2][0])
            except IndexError:
                sm = 200
            for count, cont in enumerate(data):
                try:
                    if len(cont.split("\n")) < 3:
                        continue
                    retry = 0
                    while True:
                        if retry > 3:
                            raise RuntimeError("Error occurred")
                        time.sleep(0.05)
                        key = hs.md5()
                        ch = cont.split("\n")[-1]
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
                        cont = cont.split("\n")
                        trt: str = trt.replace("卡夫", "花谱")
                        cont[-1] += "\n" + trt
                        now = cont[0]
                        cont = "\n".join(cont)
                        print(now, ch, "=>", trt, round(int(now) / sm, 2))
                        data[count] = copy.deepcopy(cont)
                        break
                except Exception as err:
                    print("ERROR=>", str(err))
            data = "\n\n".join(data)
            open(f"{file.split('.')[-2]}_trans.srt", "w", encoding="utf-8").write(data)
    print("正在修正与合并srt文件")
    index = 0
    pd = []
    for file in flt:
        try:
            data = open(f'{file.split(".")[-2]}_trans.srt', encoding="utf-8").read()
            start = int(file.split(".")[-2].split("_")[-3])
            start = sec_to_srt_timestamp(start)
            end = int(file.split(".")[-2].split("_")[-2])
            end = sec_to_srt_timestamp(end)
            data = data.split("\n\n")
            for cont in data:
                try:
                    ts = cont.split("\n")[1]  # 00:01:24,800 --> 00:01:27,800
                except IndexError:
                    continue
                tss, tse = ts.split(" --> ")
                tss: list = tss.split(":")
                tse: list = tse.split(":")
                tmp = tss.pop(-1)
                tss += tmp.split(",")
                tmp = tse.pop(-1)
                tse += tmp.split(",")
                for i in range(4):
                    tss[i] = int(tss[i])
                    tse[i] = int(tse[i])
                    tss[i] += start[i]
                    tse[i] += start[i]
                if tse[-1] >= 1000:
                    tse[-2] += 1
                    tse[-1] -= 1000
                if tse[-2] >= 60:
                    tse[-3] += 1
                    tse[-2] -= 60
                if tse[-3] >= 60:
                    tse[-4] += 1
                    tse[-3] -= 60
                if tss[-1] >= 1000:
                    tss[-2] += 1
                    tss[-1] -= 1000
                if tss[-2] >= 60:
                    tss[-3] += 1
                    tss[-2] -= 60
                if tss[-3] >= 60:
                    tss[-4] += 1
                    tss[-3] -= 60
                for i in range(4):
                    tss[i] = str(tss[i])
                    tse[i] = str(tse[i])
                cont = cont.split("\n")
                tm = tss.pop(-1)
                ts = tss.pop(-1)
                tss += [ts + "," + tm]
                tm = tse.pop(-1)
                ts = tse.pop(-1)
                tse += [ts + "," + tm]
                cont[0] = str(index)
                index += 1
                cont[1] = " --> ".join((":".join(tss), ":".join(tse)))
                pd.append("\n".join(cont))
        except Exception as err:
            print("ERROR=>", str(err))

    fn = file_r.split("\\")[-1]
    sp = os.sep
    try:
        os.mkdir(f".{sp}srt{sp}{fn.split(sp)[-1].split('.')[0]}")
    except Exception as err:
        print(str(err))
    print("写入字幕文件：", f'{fn}_trans.srt')
    open(f'{fn}_trans.srt', "w", encoding="utf-8").write("\n\n".join(pd))
    open(f".{sp}srt{sp}{fn.split(sp)[-1].split('.')[0]}{sp}{fn}_trans.srt", "w", encoding="utf-8").write(
        "\n\n".join(pd))
    if burn:
        print("合并视频与字幕中")
        subprocess.run(f"ffmpeg -i {video_src} -vf subtitles={fn}_trans.srt -y {video_dst}")
    print("字幕文件已写入srt目录以供参考")


raw_fl_r = fl_r
sp = os.path.sep
try:
    for x in range(rt):
        print("分割参数:", output_rename_rules[x], "按下CTRL+C以跳过本次运行")
        os.rename(fl_r,
                  f"{sp}".join(raw_fl_r.split(sp)[0:-1]) + sp + output_rename_rules[x] + "_" + raw_fl_r.split(sp)[
                      -1])
        fl_r = sp.join(raw_fl_r.split(sp)[0:-1]) + sp + output_rename_rules[x] + "_" + raw_fl_r.split(sp)[-1]
        print("更名：", fl_r)
        try:
            run(fl_r, video_s, sp.join(video_d.split(sp)[0:-1]) + sp + output_rename_rules[x] + "_" +
                video_d.split(sp)[-1], runtime_args[x], output_filter[x])
        except Exception as err:
            print("处理", output_rename_rules[x], "时出现错误：", str(err))
        except KeyboardInterrupt:
            print("跳过处理：", output_rename_rules[x])
finally:
    os.rename(fl_r, raw_fl_r)
    print("恢复文件名：", raw_fl_r)
input("按回车键退出")
