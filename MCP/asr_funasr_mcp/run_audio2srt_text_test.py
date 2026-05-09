# -*- coding: utf-8 -*-
import time

from funasr_server import audio2srt_text


def run():
    """测试音频转 SRT 功能"""
    audio = input("请输入音频文件路径（默认: zh.wav）：").strip()
    if not audio:
        audio = "zh.wav"

    srt_text = audio2srt_text(audio)
    print(srt_text)


if __name__ == '__main__':
    t1 = time.time()

    run()

    t2 = time.time()
    print(f'运行时间: {t2 - t1:.2f}s')
