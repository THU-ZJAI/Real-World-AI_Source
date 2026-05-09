# -*- coding: utf-8 -*-
import os
import sys

from funasr import AutoModel
from loguru import logger
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

env_name = 'dev'
logger.remove()
log_level = 'INFO'
filename = os.path.basename(__file__)
log_dir = os.path.join('logs', env_name, filename.split('.')[0])
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, '{time:YYYY-MM-DD}.log')
logger.add(sys.stderr, level=log_level)
logger.add(log_file, level=log_level, rotation="00:00", enqueue=True, serialize=False, encoding="utf-8")

model = AutoModel(
    # 语音识别: paraformer-zh, paraformer-en(without timestamp).
    model="paraformer-zh",
    # 语音端点检测，实时
    vad_model="fsmn-vad",
    # 标点恢复
    punc_model="ct-punc-c",
    # 说话人确认/分割. paraformer-zh.
    spk_model="cam++",
)

app = FastMCP("asr-funasr-tools", host='0.0.0.0', port=int(os.getenv("PORT", 4005)))


class ASRError(Exception):
    pass


def format_seconds(seconds: float) -> str:
    """
    将秒数转换为小时、分钟、秒和毫秒的格式化字符串。

    参数:
    seconds (float): 秒数。

    返回:
    str: 格式化后的时间字符串。
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def audio2result(audio_path: str, hotword: str = "魔搭"):
    """
    使用 FunASR 进行语音识别

    :param audio_path: 音频文件路径
    :param hotword: 热词，默认为"魔搭"
    :return: 识别结果
    """
    logger.info(f"Processing audio file: {audio_path}")
    logger.info(f"Using hotword: {hotword}")

    if not os.path.exists(audio_path):
        raise ASRError(f"音频文件不存在: {audio_path}")

    try:
        res = model.generate(
            input=audio_path,
            batch_size_s=300,
            hotword=hotword
        )
        logger.info(f"Recognition completed, got {len(res)} results")
        return res
    except Exception as e:
        logger.error(f"ASR processing failed: {str(e)}")
        raise ASRError(f"语音识别处理失败: {str(e)}")


@app.tool()
def audio2srt_text(audio_path: str, hotword: str = "魔搭") -> str:
    """
    将音频文件转换为 SRT 格式的字幕文本

    :param audio_path: 音频文件路径（支持 wav、mp3 等格式）
    :param hotword: 热词，用于提高特定词汇的识别准确率，默认为"魔搭"
    :return: SRT 格式的字幕文本
    """
    logger.info(f"Converting audio to SRT: {audio_path}")

    try:
        result = audio2result(audio_path, hotword)
        if not result or not result[0].get('sentence_info'):
            raise ASRError("未能获取有效的识别结果")

        srt_tex_list = []
        sentence_info = result[0].get('sentence_info')

        for index, segment in enumerate(sentence_info):
            start_time = format_seconds(segment.get('start') / 1000.0)
            end_time = format_seconds(segment.get('end') / 1000.0)
            text = segment.get('text') or ''
            srt_tex = f'{index + 1}\n{start_time} --> {end_time}\n{text}\n'
            srt_tex_list.append(srt_tex)

        srt_text = '\n'.join(srt_tex_list)
        logger.info(f"SRT conversion completed, generated {len(srt_tex_list)} subtitle segments")
        return srt_text
    except Exception as e:
        logger.error(f"SRT conversion failed: {str(e)}")
        raise ASRError(f"SRT 转换失败: {str(e)}")


if __name__ == '__main__':
    transport = "sse"
    app.run(transport=transport)
