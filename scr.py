fl_srt = input("SRT文件名：")
data = open(fl_srt, encoding="utf-8").read()
data = data.split("\n\n")
for cnt, line in enumerate(data):
    x = line.split("\n")
    if x[2].startswith("!s|"):
        continue
    if len(x) < 4:
        print(f"{' '.join(x)}->无法去除：长度错误")
        continue
    x.pop(2)
    data[cnt] = "\n".join(x)
open(fl_srt.split(".")[-2]+"_SCR"+".srt", "w", encoding="utf-8").write("\n\n".join(data))