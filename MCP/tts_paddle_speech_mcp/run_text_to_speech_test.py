# -*- coding: utf-8 -*-
import os
import time

from tts_paddle_speech_server import text_to_speech


def run():
    """测试文本转语音功能"""
    test_text = "你好，这是一个文本转语音的测试。"
    output_file = "test.wav"
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(current_dir, output_file)

    print(f"正在转换文本: {test_text}")
    print(f"输出文件: {output_file}")

    try:
        result_path = text_to_speech(test_text, output_file)
        print(f"转换成功！生成文件: {result_path}")
        print(f"文件是否存在: {os.path.exists(result_path)}")

        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            print(f"文件大小: {file_size} bytes")
    except Exception as e:
        print(f"转换失败: {e}")


if __name__ == '__main__':
    t1 = time.time()

    run()

    t2 = time.time()
    print(f'运行时间: {t2 - t1:.2f}s')
