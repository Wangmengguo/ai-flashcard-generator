#!/usr/bin/env python3
"""
AI Flashcard Generator 基准测试工具
比较优化前后的性能差异
"""

import asyncio
import time
import json
import statistics
from typing import List, Dict, Any, Tuple
from main import (
    parse_llm_output, 
    parse_llm_output_optimized,
    FlashcardPair
)
import re

class BenchmarkTester:
    def __init__(self):
        self.test_data = []
        self.load_test_data()
    
    def load_test_data(self):
        """加载测试数据"""
        # 模拟各种LLM输出格式
        self.test_data = [
            # 标准格式
            """Q: 什么是机器学习？
A: 机器学习是人工智能的一个分支，让计算机能从数据中学习。

---

Q: 监督学习的特点是什么？
A: 监督学习使用标记的训练数据进行学习。""",
            
            # 中文冒号格式
            """Q：深度学习的核心是什么？
A：深度学习的核心是神经网络。

---

Q：CNN的主要用途是什么？
A：CNN主要用于图像处理和计算机视觉任务。""",
            
            # 复杂格式
            """Q: Python有哪些特点？
A: Python具有以下特点：
1. 语法简洁易懂
2. 跨平台支持
3. 丰富的库生态

---

Q: 什么是列表推导式？
A: 列表推导式是Python中创建列表的简洁方式，
语法为：[expression for item in iterable if condition]

---

Q: 如何处理异常？
A: 使用try-except语句：
try:
    # 可能出错的代码
except Exception as e:
    # 错误处理""",
            
            # 边界情况
            """Q: 简单问题？
A: 简单答案。

---

Q: 多行问题
这是问题的第二行？
A: 多行答案
这是答案的第二行
这是答案的第三行。""",
            
            # 大量卡片
            "\n---\n".join([
                f"""Q: 问题{i}？
A: 答案{i}。""" for i in range(1, 21)
            ])
        ]
    
    def benchmark_parsing(self, num_iterations: int = 1000) -> Dict[str, Any]:
        """基准测试解析函数性能"""
        print(f"开始解析性能基准测试 ({num_iterations} 次迭代)...")
        
        original_times = []
        optimized_times = []
        
        original_results = []
        optimized_results = []
        
        for test_input in self.test_data:
            # 测试原始函数
            for _ in range(num_iterations):
                start_time = time.perf_counter()
                result = parse_llm_output(test_input)
                end_time = time.perf_counter()
                original_times.append((end_time - start_time) * 1000)  # 转换为毫秒
                if _ == 0:  # 只保存第一次的结果用于验证
                    original_results.append(result)
            
            # 测试优化函数
            for _ in range(num_iterations):
                start_time = time.perf_counter()
                result = parse_llm_output_optimized(test_input)
                end_time = time.perf_counter()
                optimized_times.append((end_time - start_time) * 1000)  # 转换为毫秒
                if _ == 0:  # 只保存第一次的结果用于验证
                    optimized_results.append(result)
        
        # 验证结果一致性
        results_match = self._compare_results(original_results, optimized_results)
        
        return {
            "iterations": num_iterations,
            "test_cases": len(self.test_data),
            "results_match": results_match,
            "original_function": {
                "avg_time_ms": statistics.mean(original_times),
                "min_time_ms": min(original_times),
                "max_time_ms": max(original_times),
                "median_time_ms": statistics.median(original_times),
                "p95_time_ms": self._percentile(original_times, 0.95),
                "total_time_ms": sum(original_times)
            },
            "optimized_function": {
                "avg_time_ms": statistics.mean(optimized_times),
                "min_time_ms": min(optimized_times),
                "max_time_ms": max(optimized_times),
                "median_time_ms": statistics.median(optimized_times),
                "p95_time_ms": self._percentile(optimized_times, 0.95),
                "total_time_ms": sum(optimized_times)
            },
            "improvement": {
                "avg_speedup": statistics.mean(original_times) / statistics.mean(optimized_times),
                "total_speedup": sum(original_times) / sum(optimized_times),
                "time_saved_ms": sum(original_times) - sum(optimized_times),
                "improvement_percent": (
                    (statistics.mean(original_times) - statistics.mean(optimized_times)) / 
                    statistics.mean(original_times) * 100
                )
            }
        }
    
    def _compare_results(self, original: List[List[FlashcardPair]], 
                        optimized: List[List[FlashcardPair]]) -> bool:
        """比较两个结果是否一致"""
        if len(original) != len(optimized):
            return False
        
        for orig_list, opt_list in zip(original, optimized):
            if len(orig_list) != len(opt_list):
                return False
            
            for orig_card, opt_card in zip(orig_list, opt_list):
                if orig_card.q.strip() != opt_card.q.strip() or orig_card.a.strip() != opt_card.a.strip():
                    return False
        
        return True
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """计算百分位数"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def benchmark_memory_usage(self) -> Dict[str, Any]:
        """基准测试内存使用"""
        import tracemalloc
        
        print("开始内存使用基准测试...")
        
        # 测试原始函数内存使用
        tracemalloc.start()
        for test_input in self.test_data * 100:  # 重复100次
            parse_llm_output(test_input)
        current, peak_original = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # 测试优化函数内存使用
        tracemalloc.start()
        for test_input in self.test_data * 100:  # 重复100次
            parse_llm_output_optimized(test_input)
        current, peak_optimized = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        return {
            "original_peak_mb": peak_original / 1024 / 1024,
            "optimized_peak_mb": peak_optimized / 1024 / 1024,
            "memory_saved_mb": (peak_original - peak_optimized) / 1024 / 1024,
            "memory_improvement_percent": (
                (peak_original - peak_optimized) / peak_original * 100
                if peak_original > 0 else 0
            )
        }
    
    def regex_performance_test(self) -> Dict[str, Any]:
        """测试正则表达式性能"""
        print("开始正则表达式性能测试...")
        
        # 测试不同的正则表达式模式
        patterns = {
            "simple": re.compile(r'^Q:\s*'),
            "complex": re.compile(r'^[\s\-]*[Qq][：:]?\s*', re.MULTILINE),
            "optimized": re.compile(r'^[\s\-]*[Qq][\uff1a:]?\s*', re.MULTILINE)
        }
        
        test_text = "\n".join(self.test_data) * 10  # 扩大测试文本
        
        results = {}
        iterations = 1000
        
        for pattern_name, pattern in patterns.items():
            times = []
            for _ in range(iterations):
                start_time = time.perf_counter()
                matches = pattern.findall(test_text)
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)
            
            results[pattern_name] = {
                "avg_time_ms": statistics.mean(times),
                "min_time_ms": min(times),
                "max_time_ms": max(times),
                "matches_found": len(matches) if matches else 0
            }
        
        return results
    
    def comprehensive_benchmark(self) -> Dict[str, Any]:
        """综合基准测试"""
        print("="*60)
        print("AI Flashcard Generator 性能基准测试")
        print("="*60)
        
        # 解析性能测试
        parsing_results = self.benchmark_parsing()
        
        # 内存使用测试
        memory_results = self.benchmark_memory_usage()
        
        # 正则表达式性能测试
        regex_results = self.regex_performance_test()
        
        # 综合结果
        comprehensive_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "parsing_performance": parsing_results,
            "memory_usage": memory_results,
            "regex_performance": regex_results,
            "test_environment": {
                "test_cases": len(self.test_data),
                "total_test_text_length": sum(len(text) for text in self.test_data)
            }
        }
        
        return comprehensive_results
    
    def print_results(self, results: Dict[str, Any]):
        """打印测试结果"""
        print("\n解析性能测试结果:")
        print("-" * 40)
        parsing = results["parsing_performance"]
        
        print(f"测试用例数: {parsing['test_cases']}")
        print(f"迭代次数: {parsing['iterations']}")
        print(f"结果一致性: {'✓' if parsing['results_match'] else '✗'}")
        
        print(f"\n原始函数性能:")
        orig = parsing["original_function"]
        print(f"  平均时间: {orig['avg_time_ms']:.4f} ms")
        print(f"  中位数: {orig['median_time_ms']:.4f} ms")
        print(f"  95百分位: {orig['p95_time_ms']:.4f} ms")
        
        print(f"\n优化函数性能:")
        opt = parsing["optimized_function"]
        print(f"  平均时间: {opt['avg_time_ms']:.4f} ms")
        print(f"  中位数: {opt['median_time_ms']:.4f} ms")
        print(f"  95百分位: {opt['p95_time_ms']:.4f} ms")
        
        print(f"\n性能提升:")
        imp = parsing["improvement"]
        print(f"  平均加速: {imp['avg_speedup']:.2f}x")
        print(f"  总体加速: {imp['total_speedup']:.2f}x")
        print(f"  改进百分比: {imp['improvement_percent']:.2f}%")
        print(f"  节省时间: {imp['time_saved_ms']:.2f} ms")
        
        print(f"\n内存使用测试结果:")
        print("-" * 40)
        memory = results["memory_usage"]
        print(f"原始函数峰值内存: {memory['original_peak_mb']:.2f} MB")
        print(f"优化函数峰值内存: {memory['optimized_peak_mb']:.2f} MB")
        print(f"内存节省: {memory['memory_saved_mb']:.2f} MB")
        print(f"内存改进: {memory['memory_improvement_percent']:.2f}%")
        
        print(f"\n正则表达式性能测试:")
        print("-" * 40)
        regex = results["regex_performance"]
        for pattern_name, stats in regex.items():
            print(f"{pattern_name.capitalize()}模式:")
            print(f"  平均时间: {stats['avg_time_ms']:.4f} ms")
            print(f"  匹配数量: {stats['matches_found']}")

def main():
    """主函数"""
    tester = BenchmarkTester()
    results = tester.comprehensive_benchmark()
    
    # 打印结果
    tester.print_results(results)
    
    # 保存结果到文件
    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n详细结果已保存到: benchmark_results.json")
    
    # 生成简化报告
    parsing = results["parsing_performance"]
    if parsing["results_match"]:
        improvement = parsing["improvement"]["improvement_percent"]
        speedup = parsing["improvement"]["avg_speedup"]
        
        print(f"\n🎉 性能优化成功!")
        print(f"📈 平均性能提升: {improvement:.1f}%")
        print(f"⚡ 平均加速比: {speedup:.1f}x")
        
        if improvement > 20:
            print("🏆 优化效果显著!")
        elif improvement > 10:
            print("👍 优化效果良好!")
        else:
            print("📊 优化效果一般")
    else:
        print("❌ 警告: 优化后结果不一致，请检查代码!")

if __name__ == "__main__":
    main()