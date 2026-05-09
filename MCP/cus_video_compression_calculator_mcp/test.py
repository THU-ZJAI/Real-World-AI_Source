# -*- coding: utf-8 -*-
import os
import time
from typing import List, Dict, Any

from server import video_compression_calculator


def analyze_compression_quality(
        key: float,
        step_list: List[float],
        key_compress: float,
        step_list_compress: List[float],
        count_target: float
) -> Dict[str, Any]:
    """
    分析压缩质量，特别是压缩倍率的一致性
    """
    # 计算压缩倍率
    key_ratio = key_compress / key if key > 0 else 1.0
    step_ratios = [c / o if o > 0 else 1.0
                   for c, o in zip(step_list_compress, step_list)]

    # 统计指标
    all_ratios = [key_ratio] + step_ratios
    avg_ratio = sum(all_ratios) / len(all_ratios)

    # 计算标准差
    variance = sum((r - avg_ratio) ** 2 for r in all_ratios) / len(all_ratios)
    std_dev = variance ** 0.5

    # 计算最大最小差异
    max_ratio = max(all_ratios)
    min_ratio = min(all_ratios)

    # 验证总和
    actual_total = key_compress + sum(step_list_compress)
    total_error = abs(actual_total - count_target)

    return {
        'key_ratio': key_ratio,
        'step_ratios': step_ratios,
        'avg_ratio': avg_ratio,
        'std_dev': std_dev,
        'max_min_diff': max_ratio - min_ratio,
        'actual_total': actual_total,
        'total_error': total_error,
        'ratios_consistent': std_dev < 0.05  # 标准差小于5%认为一致
    }


def run():
    """测试视频压缩计算功能"""
    test_case = {
        'key': 106.05,
        'step_list': [24.026667, 37.733333, 22.2, 31.933333],
        'key_range': [10.0, 20.0],
        'target': 60.0
    }

    print(f"原始数据:")
    print(f"  Key视频: {test_case['key']:.2f}秒")
    print(f"  其他视频: {test_case['step_list']}")
    print(f"  总时长: {test_case['key'] + sum(test_case['step_list']):.2f}秒")
    print(f"  Key约束范围: {test_case['key_range']}")
    print(f"  目标总时长: {test_case['target']}秒")

    try:
        result = video_compression_calculator(
            key=test_case['key'],
            step_list=test_case['step_list'],
            key_range_target=test_case['key_range'],
            count_target=test_case['target']
        )

        print(f"\n压缩结果:")
        key_compression_factor = 1 / result['key_compression_ratio'] if result['key_compression_ratio'] > 0 else float('inf')
        step_compression_factors = [1 / r if r > 0 else float('inf') for r in result['step_compression_ratios']]

        print(f"  Key视频: {result['key_compressed']:.2f}秒 (压缩率: {result['key_compression_ratio']:.3f}, 倍数: {key_compression_factor:.3f})")
        print(f"  其他视频: {[f'{x:.2f}' for x in result['step_list_compressed']]}")
        print(f"  其他视频压缩率: {[f'{r:.3f}' for r in result['step_compression_ratios']]}")
        print(f"  其他视频倍数: {[f'{f:.3f}' for f in step_compression_factors]}")
        print(f"  实际总时长: {result['total_compressed']:.2f}秒")

        print(f"\n验证:")
        in_range = test_case['key_range'][0] <= result['key_compressed'] <= test_case['key_range'][1]
        print(
            f"  {'✓' if in_range else '✗'} Key在约束范围内: {test_case['key_range'][0]} ≤ {result['key_compressed']:.2f} ≤ {test_case['key_range'][1]}")
        print(
            f"  {'✓' if abs(result['total_compressed'] - test_case['target']) < 0.01 else '✗'} 总时长等于目标: {result['total_compressed']:.2f} = {test_case['target']}")

        # 使用原有的分析函数
        analysis = analyze_compression_quality(
            test_case['key'],
            test_case['step_list'],
            result['key_compressed'],
            result['step_list_compressed'],
            test_case['target']
        )

        print(f"\n一致性分析:")
        print(f"  平均压缩率: {analysis['avg_ratio']:.3f}")
        print(f"  标准差: {analysis['std_dev']:.4f}")
        print(f"  压缩率一致: {'✓ 是' if analysis['ratios_consistent'] else '✗ 否'}")

        print(f"\n✅ 测试成功完成")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    t1 = time.time()

    run()

    t2 = time.time()
    print(f'运行时间: {t2 - t1:.2f}s')
