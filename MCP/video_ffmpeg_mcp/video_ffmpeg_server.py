# -*- coding: utf-8 -*-
import os
import sys
import subprocess

import ffmpeg
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

app = FastMCP("video-ffmpeg-tools", host='0.0.0.0', port=int(os.getenv("PORT", 4008)))


class VideoError(Exception):
    pass


def get_video_duration(video_path: str) -> float:
    """
    获取视频文件的时长

    :param video_path: 视频文件路径
    :return: 视频时长（秒）
    """
    logger.info(f"Getting video duration: {video_path}")

    if not os.path.exists(video_path):
        raise VideoError(f"视频文件不存在: {video_path}")

    try:
        probe = ffmpeg.probe(video_path)
        duration = float(probe['format']['duration'])
        logger.info(f"Video duration: {duration} seconds")
        return duration
    except Exception as e:
        logger.error(f"Failed to get video duration: {str(e)}")
        raise VideoError(f"获取视频时长失败: {str(e)}")


def extract_audio(video_path: str, output_path: str) -> str:
    """
    从视频文件中提取音频

    :param video_path: 输入视频文件路径
    :param output_path: 输出音频文件路径
    :return: 输出音频文件路径
    """
    logger.info(f"Extracting audio from {video_path} to {output_path}")

    if not os.path.exists(video_path):
        raise VideoError(f"视频文件不存在: {video_path}")

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    try:
        ffmpeg.input(video_path).output(
            output_path,
            acodec='pcm_s16le',
            ar='44100',
            ac=2
        ).run(overwrite_output=True)

        if not os.path.exists(output_path):
            raise VideoError(f"音频文件提取失败: {output_path}")

        logger.info(f"Audio extraction completed: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Audio extraction failed: {str(e)}")
        raise VideoError(f"音频提取失败: {str(e)}")


def extract_video(video_path: str, output_path: str) -> str:
    """
    从视频文件中提取视频流（无音频）

    :param video_path: 输入视频文件路径
    :param output_path: 输出视频文件路径
    :return: 输出视频文件路径
    """
    logger.info(f"Extracting video from {video_path} to {output_path}")

    if not os.path.exists(video_path):
        raise VideoError(f"视频文件不存在: {video_path}")

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    try:
        (
            ffmpeg
            .input(video_path)
            .output(output_path, **{'an': None, 'c:v': 'copy'})
            .run(overwrite_output=True)
        )

        if not os.path.exists(output_path):
            raise VideoError(f"视频文件提取失败: {output_path}")

        logger.info(f"Video extraction completed: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Video extraction failed: {str(e)}")
        raise VideoError(f"视频提取失败: {str(e)}")


def speed_up_video(video_path: str, output_path: str, speed_factor: float) -> str:
    """
    加快视频播放速度

    :param video_path: 输入视频文件路径
    :param output_path: 输出视频文件路径
    :param speed_factor: 速度倍数
    :return: 输出视频文件路径
    """
    logger.info(f"Speeding up video {video_path} by factor {speed_factor}")

    if not os.path.exists(video_path):
        raise VideoError(f"视频文件不存在: {video_path}")

    if speed_factor <= 0:
        raise VideoError("速度倍数必须大于0")

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # 删除已存在的输出文件
    if os.path.exists(output_path):
        os.remove(output_path)

    try:
        # 计算视频时间戳倍数
        video_pts_factor = 1.0 / speed_factor

        # 构建FFmpeg命令
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-filter:v', f'setpts={video_pts_factor}*PTS',
            '-filter:a', f'atempo={speed_factor}',
            output_path
        ]

        logger.info(f"Executing command: {' '.join(cmd)}")

        # 执行命令
        subprocess.run(cmd, check=True)

        if not os.path.exists(output_path):
            raise VideoError(f"视频速度处理失败: {output_path}")

        logger.info(f"Video speed up completed: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg command failed with return code {e.returncode}")
        raise VideoError(f"视频速度处理失败: FFmpeg命令执行错误")
    except Exception as e:
        logger.error(f"Video speed up failed: {str(e)}")
        raise VideoError(f"视频速度处理失败: {str(e)}")


def get_audio_duration(audio_path: str) -> float:
    """
    获取音频文件的时长

    :param audio_path: 音频文件路径
    :return: 音频时长（秒）
    """
    logger.info(f"Getting audio duration: {audio_path}")

    if not os.path.exists(audio_path):
        raise VideoError(f"音频文件不存在: {audio_path}")

    try:
        probe = ffmpeg.probe(audio_path)
        duration = float(probe['format']['duration'])
        logger.info(f"Audio duration: {duration} seconds")
        return duration
    except Exception as e:
        logger.error(f"Failed to get audio duration: {str(e)}")
        raise VideoError(f"获取音频时长失败: {str(e)}")


def generate_silence(input_audio_path: str, duration: float, output_path: str = None) -> str:
    """
    生成与输入音频同参数的静音音频

    :param input_audio_path: 参考音频文件路径
    :param duration: 静音音频时长（秒）
    :param output_path: 输出文件路径（可选）
    :return: 输出静音音频文件路径
    """
    logger.info(f"Generating silence audio based on {input_audio_path}")

    if not os.path.exists(input_audio_path):
        raise VideoError(f"参考音频文件不存在: {input_audio_path}")

    if duration <= 0:
        raise VideoError("时长必须大于0")

    if not output_path:
        output_path = f"silence_{duration}s.wav"

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    try:
        # 获取参考音频的参数
        probe = ffmpeg.probe(input_audio_path)
        audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)

        if not audio_stream:
            raise VideoError("无法找到音频流信息")

        sample_rate = int(audio_stream['sample_rate'])
        channels = int(audio_stream['channels'])

        # 确定声道布局
        channel_layout = "mono"
        if channels == 2:
            channel_layout = "stereo"
        elif channels > 2:
            channel_layout = "multi"

        logger.info(f"Generating {duration}s silence with {sample_rate}Hz, {channels} channels")

        # 生成静音音频
        (
            ffmpeg
            .input(f'anullsrc=r={sample_rate}:cl={channel_layout}', f='lavfi')
            .output(
                output_path,
                t=duration,
                acodec='pcm_s16le',
                ar=sample_rate,
                ac=channels
            )
            .run(overwrite_output=True)
        )

        if not os.path.exists(output_path):
            raise VideoError(f"静音音频生成失败: {output_path}")

        logger.info(f"Silence audio generated: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Silence generation failed: {str(e)}")
        raise VideoError(f"静音音频生成失败: {str(e)}")


def merge_multi_track_video(
        video_path: str,
        audio1_path: str,
        audio2_path: str,
        subtitle_path: str = None,
        output_path: str = None,
        audio1_weight: float = 1.0,
        audio2_weight: float = 0.05
) -> str:
    """
    创建多音轨视频，混合两个音频并添加字幕

    :param video_path: 视频文件路径（无音频）
    :param audio1_path: 主音频文件路径
    :param audio2_path: 背景音频文件路径
    :param subtitle_path: 字幕文件路径（可选）
    :param output_path: 输出视频文件路径（可选）
    :param audio1_weight: 主音频权重
    :param audio2_weight: 背景音频权重
    :return: 输出视频文件路径
    """
    logger.info(f"Merging multi-track video with {audio1_path} and {audio2_path}")

    # 检查输入文件
    for file_path, file_name in [(video_path, "视频"), (audio1_path, "主音频"), (audio2_path, "背景音频")]:
        if not os.path.exists(file_path):
            raise VideoError(f"{file_name}文件不存在: {file_path}")

    if subtitle_path and not os.path.exists(subtitle_path):
        raise VideoError(f"字幕文件不存在: {subtitle_path}")

    if not output_path:
        output_path = "output_multi_track.mov"

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    try:
        # 输入文件
        video_input = ffmpeg.input(video_path)
        audio1_input = ffmpeg.input(audio1_path)
        audio2_input = ffmpeg.input(audio2_path)

        # 混合音频
        mixed_audio = ffmpeg.filter(
            [audio1_input, audio2_input],
            'amix',
            inputs=2,
            duration='first',
            weights=f'{audio1_weight} {audio2_weight}'
        )

        # 添加字幕（如果有）
        video_stream = video_input.video
        if subtitle_path:
            video_stream = video_stream.filter('subtitles', subtitle_path)

        # 组合视频和混合音频
        output = ffmpeg.output(
            video_stream,
            mixed_audio,
            output_path,
            vcodec='libx264',
            crf=18,
            preset='fast',
            acodec='aac',
            audio_bitrate='192k'
        )

        # 执行命令
        ffmpeg.run(output, overwrite_output=True)

        if not os.path.exists(output_path):
            raise VideoError(f"多音轨视频生成失败: {output_path}")

        logger.info(f"Multi-track video generated: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Multi-track video merging failed: {str(e)}")
        raise VideoError(f"多音轨视频生成失败: {str(e)}")


# MCP Tools
@app.tool()
def get_video_file_duration(video_path: str) -> float:
    """
    获取视频文件的时长

    :param video_path: 视频文件的绝对路径
    :return: 视频时长（秒）
    """
    logger.info(f"Getting video file duration: {video_path}")

    try:
        duration = get_video_duration(video_path)
        logger.info(f"Video duration retrieved successfully: {duration} seconds")
        return duration
    except Exception as e:
        logger.error(f"Failed to get video duration: {str(e)}")
        raise VideoError(f"获取视频文件时长失败: {str(e)}")


@app.tool()
def extract_audio_from_video(video_path: str, output_path: str) -> str:
    """
    从视频文件中提取音频

    :param video_path: 输入视频文件的绝对路径
    :param output_path: 输出音频文件的绝对路径
    :return: 提取的音频文件路径
    """
    logger.info(f"Extracting audio from video: {video_path}")

    try:
        result_path = extract_audio(video_path, output_path)
        logger.info(f"Audio extraction completed: {result_path}")
        return result_path
    except Exception as e:
        logger.error(f"Audio extraction failed: {str(e)}")
        raise VideoError(f"从视频提取音频失败: {str(e)}")


@app.tool()
def extract_video_stream(video_path: str, output_path: str) -> str:
    """
    从视频文件中提取视频流（无音频）

    :param video_path: 输入视频文件的绝对路径
    :param output_path: 输出视频文件的绝对路径
    :return: 提取的视频文件路径
    """
    logger.info(f"Extracting video stream from: {video_path}")

    try:
        result_path = extract_video(video_path, output_path)
        logger.info(f"Video stream extraction completed: {result_path}")
        return result_path
    except Exception as e:
        logger.error(f"Video stream extraction failed: {str(e)}")
        raise VideoError(f"从视频提取视频流失败: {str(e)}")


@app.tool()
def compress_video_duration(video_path: str, output_path: str, speed_factor: float) -> str:
    """
    通过加速来压缩视频时长

    :param video_path: 输入视频文件的绝对路径
    :param output_path: 输出视频文件的绝对路径
    :param speed_factor: 速度倍数（大于1表示加速）
    :return: 处理后的视频文件路径
    """
    logger.info(f"Compressing video duration with speed factor {speed_factor}")

    try:
        result_path = speed_up_video(video_path, output_path, speed_factor)
        logger.info(f"Video duration compression completed: {result_path}")
        return result_path
    except Exception as e:
        logger.error(f"Video duration compression failed: {str(e)}")
        raise VideoError(f"视频时长压缩失败: {str(e)}")


@app.tool()
def get_audio_file_duration(audio_path: str) -> float:
    """
    获取音频文件的时长

    :param audio_path: 音频文件的绝对路径
    :return: 音频时长（秒）
    """
    logger.info(f"Getting audio file duration: {audio_path}")

    try:
        duration = get_audio_duration(audio_path)
        logger.info(f"Audio duration retrieved successfully: {duration} seconds")
        return duration
    except Exception as e:
        logger.error(f"Failed to get audio duration: {str(e)}")
        raise VideoError(f"获取音频文件时长失败: {str(e)}")


@app.tool()
def generate_silence_audio(input_audio_path: str, duration: float, output_path: str = None) -> str:
    """
    生成与输入音频同参数的静音音频

    :param input_audio_path: 参考音频文件的绝对路径
    :param duration: 静音音频时长（秒）
    :param output_path: 输出静音音频文件的绝对路径
    :return: 生成的静音音频文件路径
    """
    logger.info(f"Generating silence audio based on: {input_audio_path}")

    try:
        result_path = generate_silence(input_audio_path, duration, output_path)
        logger.info(f"Silence audio generation completed: {result_path}")
        return result_path
    except Exception as e:
        logger.error(f"Silence audio generation failed: {str(e)}")
        raise VideoError(f"生成静音音频失败: {str(e)}")


@app.tool()
def create_multi_track_video(
        video_path: str,
        audio1_path: str,
        audio2_path: str,
        subtitle_path: str = None,
        output_path: str = None,
        audio1_weight: float = 1.0,
        audio2_weight: float = 0.05
) -> str:
    """
    创建多音轨视频，混合两个音频并添加字幕

    :param video_path: 视频文件的绝对路径（无音频）
    :param audio1_path: 主音频文件的绝对路径
    :param audio2_path: 背景音频文件的绝对路径
    :param subtitle_path: 字幕文件的绝对路径
    :param output_path: 输出视频文件的绝对路径
    :param audio1_weight: 主音频权重
    :param audio2_weight: 背景音频权重
    :return: 生成的多音轨视频文件路径
    """
    logger.info(f"Creating multi-track video with: {audio1_path}, {audio2_path}")

    try:
        result_path = merge_multi_track_video(
            video_path, audio1_path, audio2_path, subtitle_path,
            output_path, audio1_weight, audio2_weight
        )
        logger.info(f"Multi-track video creation completed: {result_path}")
        return result_path
    except Exception as e:
        logger.error(f"Multi-track video creation failed: {str(e)}")
        raise VideoError(f"创建多音轨视频失败: {str(e)}")


if __name__ == '__main__':
    transport = "sse"
    app.run(transport=transport)
