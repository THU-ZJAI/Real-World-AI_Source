# -*- coding: utf-8 -*-
import os
import sys
from typing import List, Tuple, Dict, Any
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

app = FastMCP("video-compression-calculator-tools", host='0.0.0.0', port=int(os.getenv("PORT", 4007)))


class VideoCompressionError(Exception):
    pass


def calculate_video_compression(
        key: float,
        step_list: List[float],
        key_range_target: List[float],
        count_target: float = 60.0
) -> Tuple[float, List[float], float, float, List[float]]:
    """
    计算视频压缩时长分配 - 严格满足总时长约束，同时追求压缩倍率一致性

    核心算法：
    1. 尝试统一压缩倍率
    2. 如果key视频超出范围，将其固定在边界
    3. 剩余时间严格分配给其他视频，确保总和=count_target

    :param key: Key视频原始时长
    :param step_list: 其他视频时长的列表
    :param key_range_target: Key视频压缩后的允许范围 [最小值, 最大值]
    :param count_target: 目标总时长
    :return: 压缩后的key时长、其他视频时长列表、总时长、key压缩倍率、其他视频压缩倍率列表
    """
    logger.info(f"Calculating video compression: key={key}, steps={step_list}, range={key_range_target}, target={count_target}")

    # 参数验证
    if key <= 0:
        raise VideoCompressionError("Key视频时长必须大于0")
    if not step_list or any(s <= 0 for s in step_list):
        raise VideoCompressionError("Step视频列表不能为空且所有时长必须大于0")
    if len(key_range_target) != 2 or key_range_target[0] >= key_range_target[1]:
        raise VideoCompressionError("Key视频约束范围无效，需要[最小值, 最大值]且最小值小于最大值")
    if count_target <= 0:
        raise VideoCompressionError("目标总时长必须大于0")

    try:
        # 计算总时长
        step_total = sum(step_list)
        total_original = key + step_total

        if total_original == 0:
            return 0, [], 0, 1.0, []

        # key视频的约束范围
        k_min, k_max = key_range_target

        # 修正：处理key约束范围
        # 1. 如果原始key小于k_min，压缩后应该使用k_min（相当于延长）
        # 2. 如果原始key大于k_max，压缩后最多只能是原始时长
        # 3. 正常情况下，压缩后不能超过原始时长

        # 确定实际可用的约束范围
        actual_k_min = k_min  # 最小值保持不变，可以延长视频
        actual_k_max = min(k_max, key) if key > k_min else k_max  # 最大值不能超过原始时长

        # 但如果原始key < k_min，我们需要特殊处理
        if key < k_min:
            # 原始时长小于最小约束，必须延长到至少k_min
            actual_k_min = k_min
            actual_k_max = max(k_min, min(k_max, count_target - step_total * 0.5))  # 确保其他视频至少有0.5秒
        else:
            # 原始时长大于等于最小约束，正常压缩
            actual_k_min = min(k_min, key)
            actual_k_max = min(k_max, key)

        # 方案1：尝试统一压缩倍率
        uniform_ratio = count_target / total_original
        key_uniform = key * uniform_ratio

        # 根据key_uniform的情况选择策略
        if actual_k_min <= key_uniform <= actual_k_max:
            # 理想情况：统一压缩倍率
            key_compress = key_uniform
        elif key_uniform < actual_k_min:
            # key视频压缩后太短，固定在最小值
            key_compress = actual_k_min
        else:  # key_uniform > actual_k_max
            # key视频压缩后太长，固定在最大值
            key_compress = actual_k_max

        # 计算剩余时间
        remaining_time = count_target - key_compress

        # 严格分配剩余时间给step videos
        if step_total > 0 and remaining_time > 0:
            # 按原始比例分配剩余时间
            step_ratio = remaining_time / step_total
            step_list_compress = []

            # 首先按比例分配
            for i, duration in enumerate(step_list):
                compressed = duration * step_ratio
                # 确保每个视频至少0.5秒
                compressed = max(0.5, compressed)
                step_list_compress.append(compressed)

            # 检查是否因为最小值限制导致总和不等于remaining_time
            current_step_sum = sum(step_list_compress)

            if abs(current_step_sum - remaining_time) > 0.001:  # 允许小误差
                if current_step_sum > remaining_time:
                    # 需要减少一些时长
                    excess = current_step_sum - remaining_time

                    # 从最长的视频开始减少，但保持最小0.5秒
                    sorted_indices = sorted(range(len(step_list_compress)),
                                            key=lambda i: step_list_compress[i],
                                            reverse=True)

                    for idx in sorted_indices:
                        if excess <= 0.001:
                            break
                        available = step_list_compress[idx] - 0.5
                        if available > 0:
                            reduction = min(available, excess)
                            step_list_compress[idx] -= reduction
                            excess -= reduction

                    # 如果还有剩余（极端情况），可能需要调整key
                    if excess > 0.001:
                        # 尝试减少key_compress，但不能低于actual_k_min
                        available_key_reduction = key_compress - actual_k_min
                        if available_key_reduction > 0:
                            reduction = min(available_key_reduction, excess)
                            key_compress -= reduction
                            remaining_time = count_target - key_compress
                            # 重新计算step_list_compress
                            step_ratio = remaining_time / step_total
                            step_list_compress = [max(0.5, duration * step_ratio)
                                                  for duration in step_list]

                else:  # current_step_sum < remaining_time
                    # 需要增加一些时长，按比例分配到所有视频
                    deficit = remaining_time - current_step_sum
                    for i in range(len(step_list_compress)):
                        step_list_compress[i] += deficit * (step_list[i] / step_total)

            # 最终微调确保总和精确等于count_target
            current_total = key_compress + sum(step_list_compress)
            if abs(current_total - count_target) > 0.001:
                # 调整最长的step视频
                adjustment = count_target - current_total
                if step_list_compress:
                    max_idx = step_list_compress.index(max(step_list_compress))
                    step_list_compress[max_idx] += adjustment

        elif remaining_time <= 0:
            # 特殊情况：key_compress已经占满或超过目标时长
            if key_compress >= count_target:
                key_compress = min(key_compress, count_target)
                step_list_compress = []
            else:
                # 剩余时间很少，平均分配给每个视频0.5秒
                step_list_compress = [0.5] * len(step_list)
                total_step = sum(step_list_compress)
                if key_compress + total_step > count_target:
                    key_compress = count_target - total_step
        else:
            step_list_compress = []

        # 计算压缩倍率
        key_compression_ratio = key_compress / key if key > 0 else 1.0
        step_compression_ratios = [
            compressed / original if original > 0 else 1.0
            for compressed, original in zip(step_list_compress, step_list)
        ]

        # 最终总时长（应该正好等于count_target）
        count_compress = key_compress + sum(step_list_compress)

        # 验证总和
        assert abs(count_compress - count_target) < 0.01, \
            f"总时长{count_compress:.2f}不等于目标{count_target}"

        logger.info(f"Video compression calculation completed successfully")
        return key_compress, step_list_compress, count_compress, key_compression_ratio, step_compression_ratios

    except AssertionError as e:
        logger.error(f"Calculation assertion failed: {str(e)}")
        raise VideoCompressionError(f"计算验证失败: {str(e)}")
    except Exception as e:
        logger.error(f"Video compression calculation failed: {str(e)}")
        raise VideoCompressionError(f"视频压缩计算失败: {str(e)}")


@app.tool()
def video_compression_calculator(
    key: float,
    step_list: List[float],
    key_range_target: List[float],
    count_target: float = 60.0
) -> Dict[str, Any]:
    """
    视频压缩时长计算器 - MCP工具接口

    ========== 功能说明 ==========
    用于计算多个视频的压缩时长分配，确保压缩后的总时长不超过目标时长。
    主要应用于教学视频或演示视频的场景，其中包含：
    - 展示效果部分（前10-15秒）：需要重点展示
    - 步骤讲解部分：安装配置步骤的简要说明

    ========== 输入参数详细说明 ==========

    key: float
    - 参数含义：展示效果视频的原始时长（秒）
    - 取值范围：大于0的浮点数
    - 示例值：15.0 (表示15秒的展示效果视频)
    - 约束：必须大于0
    - 说明：这个视频通常放在最前面，用于展示软件或功能的效果

    step_list: List[float]
    - 参数含义：其余各个讲解视频的原始时长列表（秒）
    - 取值范围：每个元素都是大于0的浮点数
    - 示例值：[30.0, 45.0, 20.0] (表示3个讲解视频，分别是30秒、45秒、20秒)
    - 约束：列表不能为空，所有时长必须大于0
    - 说明：这些视频通常包含安装、配置、操作步骤等讲解内容

    key_range_target: List[float]
    - 参数含义：展示效果视频压缩后的期望时长范围 [最小值, 最大值]
    - 取值范围：[最小值, 最大值]，且最小值 < 最大值
    - 示例值：[10.0, 15.0] (表示希望展示效果视频压缩后在10-15秒之间)
    - 约束：必须包含2个元素的列表，第一个元素小于第二个元素
    - 说明：用于控制展示效果部分的最终时长，确保足够的展示时间

    count_target: float (可选参数，默认值: 60.0)
    - 参数含义：所有视频压缩后的目标总时长（秒）
    - 取值范围：大于0的浮点数
    - 示例值：60.0 (表示希望最终总时长为60秒)
    - 约束：必须大于0
    - 说明：这是整个视频组合的目标总时长，算法会确保压缩后的总时长接近这个值

    ========== 返回值详细说明 ==========

    返回一个包含以下字段的字典：

    key_original: float
    - 含义：展示效果视频的原始时长
    - 单位：秒

    step_list_original: List[float]
    - 含义：讲解视频的原始时长列表
    - 单位：秒

    key_compressed: float
    - 含义：展示效果视频压缩后的时长
    - 单位：秒
    - 特点：保证在 key_range_target 范围内或接近该范围

    step_list_compressed: List[float]
    - 含义：讲解视频压缩后的时长列表
    - 单位：秒
    - 特点：按比例分配剩余时间，每个视频至少0.5秒

    total_original: float
    - 含义：所有视频的原始总时长
    - 单位：秒

    total_compressed: float
    - 含义：所有视频压缩后的实际总时长
    - 单位：秒
    - 特点：应该接近或等于 count_target

    target_total: float
    - 含义：目标总时长（即输入的 count_target）
    - 单位：秒

    key_compression_ratio: float
    - 含义：展示效果视频的压缩倍率
    - 计算方式：key_compressed / key_original
    - 说明：大于1表示延长，小于1表示压缩

    step_compression_ratios: List[float]
    - 含义：讲解视频的压缩倍率列表
    - 计算方式：step_compressed / step_original
    - 说明：每个元素对应一个视频的压缩倍率

    key_range_target: List[float]
    - 含义：展示效果视频的目标时长范围
    - 单位：秒

    calculation_successful: bool
    - 含义：计算是否成功
    - 取值：True 表示成功，False 表示失败

    ========== 使用示例 ==========

    示例1：标准使用
    video_compression_calculator(
        key=15.0,                    # 展示效果视频15秒
        step_list=[30.0, 45.0],      # 两个讲解视频，分别30秒和45秒
        key_range_target=[10.0, 15.0], # 希望展示效果在10-15秒之间
        count_target=60.0             # 总时长控制在60秒
    )

    ========== 算法特点 ==========
    1. 优先保持展示效果视频在指定范围内
    2. 严格保证总时长接近目标值
    3. 按比例分配剩余时间给讲解视频
    4. 确保每个视频至少0.5秒的基本时长
    5. 返回详细的压缩信息便于分析

    :param key: Key视频原始时长
    :param step_list: 其他视频时长的列表
    :param key_range_target: Key视频压缩后的允许范围 [最小值, 最大值]
    :param count_target: 目标总时长
    :return: 包含压缩结果详细信息的字典
    """
    logger.info(f"Video compression calculator request: key={key}, target={count_target}")

    try:
        result = calculate_video_compression(key, step_list, key_range_target, count_target)

        key_compress, step_list_compress, count_compress, key_compression_ratio, step_compression_ratios = result

        return {
            "key_original": key,
            "step_list_original": step_list,
            "key_compressed": key_compress,
            "step_list_compressed": step_list_compress,
            "total_original": key + sum(step_list),
            "total_compressed": count_compress,
            "target_total": count_target,
            "key_compression_ratio": key_compression_ratio,
            "step_compression_ratios": step_compression_ratios,
            "key_range_target": key_range_target,
            "calculation_successful": True
        }
    except Exception as e:
        logger.error(f"Video compression calculator failed: {str(e)}")
        raise VideoCompressionError(f"视频压缩计算失败: {str(e)}")


if __name__ == '__main__':
    transport = "sse"
    app.run(transport=transport)
