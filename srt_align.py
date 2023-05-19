def srt_timestamp_to_milliseconds(ts: str) -> int:
    orn = [3600000, 60000]
    st = 0
    start_srt = ts
    start_srt = start_srt.split(":")
    sec_s, mil_s = start_srt.pop(-1).split(",")
    st += int(mil_s) + int(sec_s) * 1000
    for cnt, val in enumerate(orn):
        st += int(start_srt[cnt]) * val
    return st


def ms_to_srt_timestamp(ms):
    seconds = ms // 1000
    ms -= seconds * 1000
    minutes = seconds // 60
    seconds -= minutes * 60
    hours = minutes // 60
    minutes -= hours * 60
    return f"{hours}:{minutes}:{seconds},{ms}"


fl_srt = input("SRT文件名：")
target = srt_timestamp_to_milliseconds(input("目标起始时间轴："))
data = open(fl_srt, encoding="utf-8").read()
data = data.split("\n\n")
delta = target - srt_timestamp_to_milliseconds(data[0].split("\n")[1].split(" --> ")[0])

for cnt, x in enumerate(data):
    ln = x.split("\n")
    st, ed = [srt_timestamp_to_milliseconds(t) for t in ln[1].split(" --> ")]
    st += delta
    ed += delta
    ln[1] = f"{ms_to_srt_timestamp(st)} --> {ms_to_srt_timestamp(ed)}"
    data[cnt] = "\n".join(ln)

open(fl_srt.split(".")[-2] + "_Aligned.srt", "w", encoding="utf-8").write("\n\n".join(data))
