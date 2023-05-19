def srt_timestamp_to_milliseconds(ts: str) -> tuple[int, int]:
    orn = [3600000, 60000]
    st = 0
    ed = 0
    start_srt, end_srt = ts.split(" --> ")
    start_srt = start_srt.split(":")
    end_srt = end_srt.split(":")
    sec_s, mil_s = start_srt.pop(-1).split(",")
    sec_e, mil_e = end_srt.pop(-1).split(",")
    st += int(mil_s) + int(sec_s) * 1000
    ed += int(mil_e) + int(sec_e) * 1000
    for cnt, val in enumerate(orn):
        st += int(start_srt[cnt]) * val
        ed += int(end_srt[cnt]) * val
    return st, ed


fl_srt = input("SRT文件名：")
while True:
    try:
        sta = input("起始时间戳：")
        end = input("结束时间戳：")
        tag = input("需要打上的标志：")
        sta, end = srt_timestamp_to_milliseconds(" --> ".join([sta, end]))
        data = open(fl_srt, encoding="utf-8").read()
        data = data.split("\n\n")
        for cnt, line in enumerate(data):
            try:
                x = line.split("\n", 2)
                ts, te = srt_timestamp_to_milliseconds(x[1])
                if (ts >= sta or te >= sta) and (ts <= end or te <= end):
                    x[-1] = tag + x[-1]
                data[cnt] = "\n".join(x)
            except Exception as err:
                print(f"处理{cnt}项时发生错误：{str(err)}")
        open(fl_srt, "w", encoding="utf-8").write("\n\n".join(data))
    except Exception as err:
        print(f"发生错误=>{str(err)}")
