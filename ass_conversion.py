import datetime
from collections import OrderedDict

import ass
from ass import ScriptInfoSection, StylesSection, Style, Dialogue, EventsSection
from ass.data import Color

alpha_level = 100


def sort_key(obj):
    return obj[1]


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


asf = ass.document.Document()
style_kaf_dia = Style(name='Kaf', fontname='Arial', fontsize=28.0,
                      primary_color=Color(r=0xff, g=0x9c, b=0xca, a=alpha_level),
                      secondary_color=Color(r=0xff, g=0xc0, b=0xcb, a=alpha_level),
                      outline_color=Color(r=0x00, g=0x00, b=0x00, a=alpha_level),
                      back_color=Color(r=0x00, g=0x00, b=0x00, a=alpha_level), bold=False, italic=False,
                      underline=False,
                      strike_out=False, scale_x=100.0, scale_y=100.0, spacing=0.0, angle=0.0, border_style=1,
                      outline=4.0, shadow=0.0, alignment=2, margin_l=10, margin_r=10, margin_v=25, encoding=134)
style_lyric = Style(name='Lyric', fontname='Arial', fontsize=28.0,
                    primary_color=Color(r=0x0, g=245, b=255, a=alpha_level),
                    secondary_color=Color(r=0x57, g=0xfa, b=0xff, a=alpha_level),
                    outline_color=Color(r=0x00, g=0x00, b=0x00, a=alpha_level),
                    back_color=Color(r=0x00, g=0x00, b=0x00, a=alpha_level), bold=False, italic=False, underline=False,
                    strike_out=False, scale_x=100.0, scale_y=100.0, spacing=0.0, angle=0.0, border_style=1, outline=4.0,
                    shadow=0.0, alignment=2, margin_l=10, margin_r=10, margin_v=25, encoding=134)

style_secondary_lyric = Style(name='Note', fontname='Arial', fontsize=23.0,
                              primary_color=Color(r=0x00, g=0xff, b=0x00, a=alpha_level),
                              secondary_color=Color(r=0x57, g=0xfa, b=0xff, a=alpha_level),
                              outline_color=Color(r=0x00, g=0x00, b=0x00, a=alpha_level),
                              back_color=Color(r=0x00, g=0x00, b=0x00, a=alpha_level), bold=False, italic=False,
                              underline=False,
                              strike_out=False, scale_x=100.0, scale_y=100.0, spacing=0.0, angle=0.0, border_style=1,
                              outline=4.0,
                              shadow=0.0, alignment=2, margin_l=10, margin_r=10, margin_v=25, encoding=134)
styles = StylesSection('V4+ Styles', [style_kaf_dia, style_lyric, style_secondary_lyric])
events = []
asf.info = ScriptInfoSection('Script Info',
                             OrderedDict([('ScriptType', 'v4.00+'),
                                          ('PlayResX', 500),
                                          ('PlayResY', 500),
                                          ("WrapStyle", 3)
                                          ]))
asf.styles = styles


def run_conversion(fl_srt):
    data = open(fl_srt, encoding="utf-8").read()
    data = data.split("\n\n")
    for line in data:
        try:
            x = line.split("\n", 2)
            x.pop(0)
            start, end = srt_timestamp_to_milliseconds(x[0])
            if x[1].startswith("!s2|"):
                stl = "Note"
                x[1] = x[1][4:]
            elif x[1].startswith("!s|"):
                stl = "Lyric"
                x[1] = x[1][3:]
            else:
                stl = "Kaf"
            events.append(
                (Dialogue(layer=0,
                          start=datetime.timedelta(milliseconds=start),
                          end=datetime.timedelta(milliseconds=end),
                          style=stl,
                          name='Kaf',
                          margin_l=0,
                          margin_r=0,
                          margin_v=25,
                          effect='',
                          text=r"{\fad(50, 50)}" + "\n".join(x[1:]).replace("\n", r" \N ")), start))
        except Exception as err:
            line = line.replace('\n', ' ')
            print(f"处理{line}时发生错误：({str(err)})")
    sorted(events, key=sort_key)
    event = []
    for x in events:
        event.append(x[0])
    asf.events = EventsSection('Events', event)
    with open(".".join(fl_srt.split(".")[0:-1]) + ".ass", "w", encoding="utf-8") as ass_file:
        asf.dump_file(ass_file)


if __name__ == '__main__':
    fl_srt = input("SRT文件名：")
    run_conversion(fl_srt)
