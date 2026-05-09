# -*- coding: utf-8 -*-
import os
import sys

from paddlespeech.cli.tts.infer import TTSExecutor
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

tts = TTSExecutor()

app = FastMCP("tts-paddle-speech-tools", host='0.0.0.0', port=int(os.getenv("PORT", 4006)))


class TTSError(Exception):
    pass


def text2speech(text: str, output_path: str) -> str:
    """
    使用 PaddleSpeech 进行文本转语音

    :param text: 要转换的文本
    :param output_path: 输出音频文件路径（必填，必须是包含文件名的绝对路径）
    :return: 生成的音频文件绝对路径
    """
    logger.info(f"Converting text to speech: {text}")

    if not text or not text.strip():
        raise TTSError("输入文本不能为空")

    if not output_path or not output_path.strip():
        raise TTSError("输出路径不能为空，请提供有效的输出文件路径")

    if not os.path.isabs(output_path):
        raise TTSError("输出路径必须是绝对路径，请提供完整的文件路径（如：/path/to/output.wav）")

    # 检查是否包含文件名
    filename = os.path.basename(output_path)
    if not filename:
        raise TTSError("输出路径必须包含文件名，请提供完整的文件路径（如：/path/to/output.wav）")

    # 检查文件扩展名
    valid_extensions = ['.wav', '.mp3', '.flac', '.aac', '.m4a']
    file_ext = os.path.splitext(filename)[1].lower()
    if not file_ext:
        raise TTSError("输出文件必须包含扩展名，支持格式：.wav, .mp3, .flac, .aac, .m4a")
    if file_ext not in valid_extensions:
        raise TTSError(f"不支持的文件格式：{file_ext}，支持格式：.wav, .mp3, .flac, .aac, .m4a")

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    try:
        tts(text=text.strip(), output=output_path)

        if not os.path.exists(output_path):
            raise TTSError(f"语音文件生成失败: {output_path}")

        logger.info(f"TTS conversion completed: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"TTS processing failed: {str(e)}")
        raise TTSError(f"文本转语音处理失败: {str(e)}")


@app.tool()
def text_to_speech(text: str, output_path: str) -> str:
    """
    将文本转换为语音文件

    :param text: 要转换的文本内容
    :param output_path: 输出音频文件路径（必填，必须是包含文件名的绝对路径）
    :return: 生成的音频文件的绝对路径
    """
    logger.info(f"Text to speech conversion request: {text[:50]}...")

    try:
        result_path = text2speech(text, output_path)
        logger.info(f"Text to speech conversion completed: {result_path}")
        return result_path
    except Exception as e:
        logger.error(f"Text to speech conversion failed: {str(e)}")
        raise TTSError(f"文本转语音失败: {str(e)}")


if __name__ == '__main__':
    transport = "sse"
    app.run(transport=transport)
