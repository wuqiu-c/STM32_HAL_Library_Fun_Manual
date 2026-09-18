#!/usr/bin/env python3
"""从本机 STM32Cube HAL 源码生成网页函数目录。"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


FAMILY_CONFIG = {
    "F1": ("STM32Cube_FW_F1_V1.8.7", "STM32F1xx_HAL_Driver", "stm32f1xx"),
    "F4": ("STM32Cube_FW_F4_V1.28.3", "STM32F4xx_HAL_Driver", "stm32f4xx"),
    "G4": ("STM32Cube_FW_G4_V1.6.3", "STM32G4xx_HAL_Driver", "stm32g4xx"),
}

MODULE_SOURCES = {
    "gpio": ["gpio"],
    "dma": ["dma", "dma_ex"],
    "nvic": ["cortex"],
    "rcc": ["rcc", "rcc_ex"],
    "adc": ["adc", "adc_ex"],
    "dac": ["dac", "dac_ex"],
    "tim": ["tim", "tim_ex"],
    "uart": ["uart", "uart_ex"],
    "i2c": ["i2c", "i2c_ex"],
    "spi": ["spi", "spi_ex"],
    "can": ["can"],
    "fdcan": ["fdcan"],
    "rtc": ["rtc", "rtc_ex"],
    "iwdg": ["iwdg"],
}

FUNCTION_PATTERN = re.compile(
    r"(?P<doc>/\*\*.*?\*/)\s*"
    r"(?P<signature>(?:__weak\s+)?(?:[A-Za-z_][A-Za-z0-9_\s\*]*?)\s+"
    r"(?P<name>HAL_[A-Za-z0-9_]+)\s*\([^;{}]*?\))\s*\{",
    re.DOTALL,
)

MACRO_PATTERN = re.compile(
    r"^\s*#define\s+(?P<name>__HAL_[A-Z0-9_]+)\s*\((?P<params>[^)]*)\)",
    re.MULTILINE,
)

MACRO_DOC_PATTERN = re.compile(
    r"(?P<doc>/\*\*.*?\*/)\s*"
    r"#define\s+(?P<name>__HAL_[A-Z0-9_]+)\s*\((?P<params>[^)]*)\)",
    re.MULTILINE | re.DOTALL,
)

MODULE_NAMES = {
    "gpio": "GPIO",
    "dma": "DMA",
    "nvic": "中断控制器",
    "rcc": "时钟控制",
    "adc": "ADC",
    "dac": "DAC",
    "tim": "定时器",
    "uart": "串口",
    "i2c": "I²C",
    "spi": "SPI",
    "can": "CAN",
    "fdcan": "FDCAN",
    "rtc": "RTC",
    "iwdg": "独立看门狗",
}

SUBJECT_RULES = [
    ("TRANSMITRECEIVE", "同步收发"),
    ("RECEIVETOIDLE", "空闲线接收"),
    ("HALFDUPLEX", "半双工模式"),
    ("MULTIBUFFER", "双缓冲传输"),
    ("BREAKINPUT", "刹车输入"),
    ("CLOCKSOURCE", "时钟源"),
    ("CLOCKCONFIG", "时钟配置"),
    ("AUTORELOAD", "自动重装载值"),
    ("REPETITION", "重复计数值"),
    ("PRESCALER", "预分频值"),
    ("COMPARE", "捕获比较值"),
    ("CAPTURE", "输入捕获值"),
    ("COUNTER", "计数器值"),
    ("ENCODER", "编码器接口"),
    ("HALLSENSOR", "霍尔传感器接口"),
    ("ONEPULSE", "单脉冲模式"),
    ("BASE", "定时器基本计数单元"),
    ("PWM", "PWM 输出"),
    ("INPUTCAPTURE", "输入捕获"),
    ("OUTPUTCOMPARE", "输出比较"),
    ("TIM_OC", "输出比较"),
    ("TIM_IC", "输入捕获"),
    ("CHANNEL", "外设通道"),
    ("FIFO", "FIFO"),
    ("FILTER", "过滤器"),
    ("NOTIFICATION", "中断通知"),
    ("CALLBACK", "回调函数"),
    ("ERROR", "错误状态"),
    ("STATE", "运行状态"),
    ("CONFIG", "配置参数"),
    ("TRANSMIT", "发送过程"),
    ("RECEIVE", "接收过程"),
    ("TRANSFER", "传输过程"),
    ("OSC", "振荡器"),
    ("CLOCK", "时钟"),
    ("DATE", "日期"),
    ("TIME", "时间"),
    ("ALARM", "闹钟"),
    ("WAKEUP", "唤醒定时器"),
    ("PIN", "引脚"),
]

DETAIL_OVERRIDES = {
    "HAL_TIM_PeriodElapsedCallback": {
        "brief": "定时器周期更新或计数溢出回调，常用于周期中断任务。",
        "notes": "HAL_TIM_IRQHandler() 检测到更新事件后会调用该回调；基本定时器 DMA 传输完成时也可能进入。可通过 htim->Instance 区分 TIM1、TIM6 等实例。该函数运行在中断上下文，应只设置标志、更新短计数或执行确定耗时的控制计算，避免阻塞延时和轮询式串口发送。",
        "example": "void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)\n{\n    if (htim->Instance == TIM6) {\n        control_tick_flag = 1;\n    }\n}",
    },
    "HAL_TIM_PeriodElapsedHalfCpltCallback": {
        "brief": "定时器基本计数 DMA 传输到达缓冲区一半时的回调。",
        "notes": "该回调用于 HAL_TIM_Base_Start_DMA() 启动的传输。适合双半缓冲处理：DMA 写入后半区时处理前半区。回调仍处于中断上下文，缓冲区处理应短小并注意与 DMA 的并发访问。",
        "example": "void HAL_TIM_PeriodElapsedHalfCpltCallback(TIM_HandleTypeDef *htim)\n{\n    if (htim->Instance == TIM2) {\n        timer_dma_half_ready = 1;\n    }\n}",
    },
    "HAL_TIM_IC_CaptureCallback": {
        "brief": "定时器输入捕获事件完成回调，用于测量脉宽、周期或频率。",
        "notes": "捕获通道出现配置的有效边沿后调用。可检查 htim->Channel 判断活动通道，再用 HAL_TIM_ReadCapturedValue() 读取 CCR。计算相邻捕获值差时需要处理计数器溢出。",
        "example": "void HAL_TIM_IC_CaptureCallback(TIM_HandleTypeDef *htim)\n{\n    if ((htim->Instance == TIM2) &&\n        (htim->Channel == HAL_TIM_ACTIVE_CHANNEL_1)) {\n        capture_value = HAL_TIM_ReadCapturedValue(htim, TIM_CHANNEL_1);\n    }\n}",
    },
    "HAL_TIM_IC_CaptureHalfCpltCallback": {
        "brief": "输入捕获 DMA 缓冲区写入一半时的回调。",
        "notes": "配合 HAL_TIM_IC_Start_DMA() 使用，可在 DMA 填充后半区时处理前半区捕获值。处理前应确认缓冲区长度、数据宽度和缓存一致性配置。",
        "example": "void HAL_TIM_IC_CaptureHalfCpltCallback(TIM_HandleTypeDef *htim)\n{\n    capture_half_ready = 1;\n}",
    },
    "HAL_TIM_OC_DelayElapsedCallback": {
        "brief": "定时器输出比较匹配事件回调。",
        "notes": "当计数器 CNT 与指定通道 CCR 匹配并产生输出比较中断时调用。可通过 htim->Channel 判断活动通道，适合精确时刻触发、软件定时和波形调度。",
        "example": "void HAL_TIM_OC_DelayElapsedCallback(TIM_HandleTypeDef *htim)\n{\n    if (htim->Channel == HAL_TIM_ACTIVE_CHANNEL_1) {\n        compare_event_flag = 1;\n    }\n}",
    },
    "HAL_TIM_PWM_PulseFinishedCallback": {
        "brief": "PWM 通道脉冲或比较事件完成回调。",
        "notes": "以中断或 DMA 方式启动 PWM 后，在对应通道比较事件或 DMA 传输完成时调用。更新下一周期占空比前，应确认使用的是预装载值还是立即生效值。",
        "example": "void HAL_TIM_PWM_PulseFinishedCallback(TIM_HandleTypeDef *htim)\n{\n    if (htim->Channel == HAL_TIM_ACTIVE_CHANNEL_3) {\n        pwm_update_ready = 1;\n    }\n}",
    },
    "HAL_TIM_PWM_PulseFinishedHalfCpltCallback": {
        "brief": "PWM DMA 缓冲区传输到一半时的回调。",
        "notes": "适合用双半缓冲连续更新 PWM 比较值。回调触发后可改写已传输完成的半区，不能覆盖 DMA 正在读取的另一半。",
        "example": "void HAL_TIM_PWM_PulseFinishedHalfCpltCallback(TIM_HandleTypeDef *htim)\n{\n    pwm_dma_half_ready = 1;\n}",
    },
    "HAL_TIM_TriggerCallback": {
        "brief": "定时器触发事件完成回调。",
        "notes": "当配置的内部或外部触发事件到达，并启用了相应中断或 DMA 请求时调用。使用前应核对主从模式、触发源选择和触发极性。",
        "example": "void HAL_TIM_TriggerCallback(TIM_HandleTypeDef *htim)\n{\n    timer_trigger_flag = 1;\n}",
    },
    "HAL_TIM_TriggerHalfCpltCallback": {
        "brief": "定时器触发 DMA 传输到达一半时的回调。",
        "notes": "用于触发事件驱动的 DMA 双半缓冲处理。回调中只标记可处理半区，复杂运算放到主循环或任务中执行。",
        "example": "void HAL_TIM_TriggerHalfCpltCallback(TIM_HandleTypeDef *htim)\n{\n    trigger_dma_half_ready = 1;\n}",
    },
    "HAL_TIM_ErrorCallback": {
        "brief": "定时器中断或 DMA 操作发生错误时的回调。",
        "notes": "该回调表示当前定时器操作未正常完成。建议记录 htim->Instance、停止相关通道并交由应用层决定重启或进入安全状态；不要在回调中无限重试。",
        "example": "void HAL_TIM_ErrorCallback(TIM_HandleTypeDef *htim)\n{\n    timer_error_flag = 1;\n}",
    },
    "HAL_TIMEx_BreakCallback": {
        "brief": "高级定时器刹车输入触发回调，用于 PWM 故障保护。",
        "notes": "刹车输入触发后，硬件可立即关闭主输出。回调中应锁存故障、禁止重新启动并记录故障来源；必须先确认功率级安全，才能清故障恢复 PWM。",
        "example": "void HAL_TIMEx_BreakCallback(TIM_HandleTypeDef *htim)\n{\n    motor_fault = 1;\n}",
    },
    "HAL_TIMEx_Break2Callback": {
        "brief": "高级定时器第二刹车输入触发回调。",
        "notes": "仅适用于带 BKIN2 的定时器。处理原则与主刹车输入相同，应区分故障来源并保持输出关闭，直到应用层完成安全检查。",
        "example": "void HAL_TIMEx_Break2Callback(TIM_HandleTypeDef *htim)\n{\n    motor_break2_fault = 1;\n}",
    },
    "HAL_TIMEx_CommutCallback": {
        "brief": "高级定时器换相事件完成回调。",
        "notes": "用于电机控制的换相事件同步。回调中可准备下一组通道状态或设置任务标志；换相时序应与预装载、触发源和功率级死区配置配合。",
        "example": "void HAL_TIMEx_CommutCallback(TIM_HandleTypeDef *htim)\n{\n    commutation_ready = 1;\n}",
    },
    "HAL_TIMEx_CommutHalfCpltCallback": {
        "brief": "换相事件 DMA 传输到达一半时的回调。",
        "notes": "适合连续换相表的双半缓冲更新。修改缓冲区前，应确认 DMA 当前正在读取哪一半。",
        "example": "void HAL_TIMEx_CommutHalfCpltCallback(TIM_HandleTypeDef *htim)\n{\n    commutation_half_ready = 1;\n}",
    },
    "HAL_TIMEx_DirectionChangeCallback": {
        "brief": "编码器计数方向发生改变时的回调。",
        "notes": "适用于支持方向改变中断的定时器编码器接口。可读取计数方向并更新速度符号，但仍需结合采样周期和计数器溢出计算实际转速。",
        "example": "void HAL_TIMEx_DirectionChangeCallback(TIM_HandleTypeDef *htim)\n{\n    encoder_direction_changed = 1;\n}",
    },
    "HAL_TIMEx_EncoderIndexCallback": {
        "brief": "编码器索引脉冲到达回调。",
        "notes": "索引脉冲通常每机械圈出现一次，可用于零位校准或圈数同步。是否自动复位计数器取决于索引配置，不能只凭回调假定当前位置已归零。",
        "example": "void HAL_TIMEx_EncoderIndexCallback(TIM_HandleTypeDef *htim)\n{\n    encoder_index_seen = 1;\n}",
    },
    "HAL_TIMEx_IndexErrorCallback": {
        "brief": "编码器索引事件检测到错误时的回调。",
        "notes": "表示索引信号与配置的方向、位置窗口或计数条件不一致。建议记录当前 CNT、方向和索引配置，用于诊断接线或参数问题。",
        "example": "void HAL_TIMEx_IndexErrorCallback(TIM_HandleTypeDef *htim)\n{\n    encoder_index_error = 1;\n}",
    },
    "HAL_TIMEx_TransitionErrorCallback": {
        "brief": "编码器非法跳变或转换错误回调。",
        "notes": "常见原因包括编码器信号抖动、相位接线错误、滤波不足或转速过高。应记录错误并检查输入滤波、GPIO 电气配置和信号完整性。",
        "example": "void HAL_TIMEx_TransitionErrorCallback(TIM_HandleTypeDef *htim)\n{\n    encoder_transition_error = 1;\n}",
    },
    "HAL_TIM_RegisterCallback": {
        "brief": "为指定定时器事件动态注册用户回调函数。",
        "notes": "仅在 USE_HAL_TIM_REGISTER_CALLBACKS 设为 1 时可用。回调编号必须与函数指针类型匹配，注册时还要满足 HAL 对句柄状态的要求。",
        "example": "HAL_TIM_RegisterCallback(&htim1,\n                         HAL_TIM_PERIOD_ELAPSED_CB_ID,\n                         Timer_PeriodCallback);",
    },
    "HAL_TIM_UnRegisterCallback": {
        "brief": "取消定时器用户回调注册并恢复默认弱回调。",
        "notes": "仅在 USE_HAL_TIM_REGISTER_CALLBACKS 设为 1 时可用。取消前应确认没有并发中断正在使用该回调。",
        "example": "HAL_TIM_UnRegisterCallback(&htim1,\n                           HAL_TIM_PERIOD_ELAPSED_CB_ID);",
    },
}

MACRO_DETAIL_OVERRIDES = {
    "__HAL_TIM_CALC_PSC": {
        "brief": "根据定时器输入时钟和目标计数频率计算预分频寄存器 PSC 的值。",
        "params": {
            "TIMCLK": "定时器输入时钟频率，单位 Hz。",
            "CNTCLK": "期望的计数器时钟频率，单位 Hz。",
        },
        "returns": "计算得到的 PSC 寄存器值，范围 0～65535；实际分频系数为 PSC + 1。",
        "notes": "计算关系为 TIMCLK / CNTCLK - 1。CNTCLK 不应为 0；当 TIMCLK 小于 CNTCLK 时宏返回 0。结果写入 Prescaler 后，通常需产生更新事件才能立即装载。",
        "example": "uint32_t psc = __HAL_TIM_CALC_PSC(170000000U, 1000000U);",
    },
    "__HAL_TIM_CALC_PERIOD": {
        "brief": "根据定时器输入时钟、预分频值和目标输出频率计算自动重装载值 ARR。",
        "params": {
            "TIMCLK": "定时器输入时钟频率，单位 Hz。",
            "PSC": "预分频寄存器 PSC 的值，实际分频系数为 PSC + 1。",
            "FREQ": "期望的更新事件或输出信号频率，单位 Hz。",
        },
        "returns": "计算得到的 ARR 值，范围 0～65535。",
        "notes": "边沿对齐向上计数时，频率关系通常为 TIMCLK / ((PSC + 1) × (ARR + 1))。FREQ 不应为 0，并应确认结果未超过当前定时器的计数位宽。",
        "example": "uint32_t arr = __HAL_TIM_CALC_PERIOD(170000000U, 169U, 1000U);",
    },
    "__HAL_TIM_CALC_PERIOD_DITHER": {
        "brief": "在已启用抖动功能时，根据目标频率计算带小数抖动位的自动重装载值。",
        "params": {
            "TIMCLK": "定时器输入时钟频率，单位 Hz。",
            "PSC": "预分频寄存器 PSC 的值，实际分频系数为 PSC + 1。",
            "FREQ": "期望的更新事件或输出信号频率，单位 Hz。",
        },
        "returns": "带抖动小数位编码的自动重装载值，范围 0～65519。",
        "notes": "仅在定时器抖动功能已经启用时使用。宏将周期结果按 1/16 计数精度编码；FREQ 不应为 0，写入前还应确认目标定时器支持抖动功能。",
        "example": "uint32_t arr_dither = __HAL_TIM_CALC_PERIOD_DITHER(170000000U, 169U, 1000U);",
    },
    "__HAL_TIM_CALC_PULSE": {
        "brief": "根据定时器时钟、预分频值和微秒延时计算输出比较寄存器 CCR 的值。",
        "params": {
            "TIMCLK": "定时器输入时钟频率，单位 Hz。",
            "PSC": "预分频寄存器 PSC 的值，实际分频系数为 PSC + 1。",
            "DELAY": "期望的输出比较有效或无效延时，单位 μs。",
        },
        "returns": "计算得到的捕获比较值，范围 0～65535。",
        "notes": "该宏把微秒时间换算为定时器计数值。结果应与通道的 CCR 位宽和 ARR 周期匹配；若比较值大于 ARR，本周期内可能不会产生匹配事件。",
        "example": "uint32_t compare = __HAL_TIM_CALC_PULSE(170000000U, 169U, 250U);",
    },
    "__HAL_TIM_CALC_PULSE_DITHER": {
        "brief": "在已启用抖动功能时，将微秒延时换算为带小数抖动位的比较值。",
        "params": {
            "TIMCLK": "定时器输入时钟频率，单位 Hz。",
            "PSC": "预分频寄存器 PSC 的值，实际分频系数为 PSC + 1。",
            "DELAY": "期望的输出比较有效或无效延时，单位 μs。",
        },
        "returns": "带抖动小数位编码的捕获比较值，范围 0～65519。",
        "notes": "仅在目标定时器已启用抖动功能时使用。结果按 1/16 计数精度编码，并应限制在当前自动重装载周期以内。",
        "example": "uint32_t compare_dither = __HAL_TIM_CALC_PULSE_DITHER(170000000U, 169U, 250U);",
    },
    "__HAL_TIM_CALC_PERIOD_BY_DELAY": {
        "brief": "根据单脉冲的启动延时和脉宽计算自动重装载值 ARR。",
        "params": {
            "TIMCLK": "定时器输入时钟频率，单位 Hz。",
            "PSC": "预分频寄存器 PSC 的值，实际分频系数为 PSC + 1。",
            "DELAY": "单脉冲开始前的延时，单位 μs。",
            "PULSE": "单脉冲持续时间，单位 μs。",
        },
        "returns": "延时计数值与脉宽计数值之和，作为单脉冲模式的 ARR，范围 0～65535。",
        "notes": "用于单脉冲模式，周期由启动延时与有效脉宽共同组成。应同时用相同 TIMCLK 和 PSC 计算 CCR，并检查总计数未超过定时器位宽。",
        "example": "uint32_t arr = __HAL_TIM_CALC_PERIOD_BY_DELAY(170000000U, 169U, 10U, 20U);",
    },
    "__HAL_TIM_CALC_PERIOD_DITHER_BY_DELAY": {
        "brief": "在抖动模式下，根据单脉冲启动延时和脉宽计算带小数位的 ARR。",
        "params": {
            "TIMCLK": "定时器输入时钟频率，单位 Hz。",
            "PSC": "预分频寄存器 PSC 的值，实际分频系数为 PSC + 1。",
            "DELAY": "单脉冲开始前的延时，单位 μs。",
            "PULSE": "单脉冲持续时间，单位 μs。",
        },
        "returns": "带抖动小数位编码的单脉冲 ARR，范围 0～65519。",
        "notes": "仅在已启用定时器抖动功能时使用。返回值由延时和脉宽的 1/16 计数结果相加得到，并应检查未超过抖动模式允许的 ARR 上限。",
        "example": "uint32_t arr_dither = __HAL_TIM_CALC_PERIOD_DITHER_BY_DELAY(170000000U, 169U, 10U, 20U);",
    },
}


def clean_doc_lines(doc: str) -> list[str]:
    lines = []
    for raw_line in doc.splitlines():
        line = re.sub(r"^\s*/?\*+/?\s?", "", raw_line)
        line = re.sub(r"\s*\*/\s*$", "", line)
        lines.append(line.rstrip())
    return lines


def parse_doc(doc: str) -> dict[str, object]:
    result: dict[str, object] = {
        "brief": "",
        "params": [],
        "returns": [],
        "notes": [],
    }
    current_kind = ""
    current_item: dict[str, str] | None = None

    for line in clean_doc_lines(doc):
        stripped = line.strip()
        if not stripped:
            continue

        brief_match = re.match(r"@brief\s*(.*)", stripped)
        note_match = re.match(r"@note\s*(.*)", stripped)
        param_match = re.match(r"@param(?:\[[^\]]+\])?\s+(\S+)\s*(.*)", stripped)
        return_match = re.match(r"@(?:retval|return)\s*(.*)", stripped)

        if brief_match:
            result["brief"] = brief_match.group(1).strip()
            current_kind = "brief"
            current_item = None
        elif note_match:
            result["notes"].append(note_match.group(1).strip())
            current_kind = "note"
            current_item = None
        elif param_match:
            current_item = {
                "name": param_match.group(1).strip(),
                "description": param_match.group(2).strip(),
            }
            result["params"].append(current_item)
            current_kind = "param"
        elif return_match:
            result["returns"].append(return_match.group(1).strip())
            current_kind = "return"
            current_item = None
        elif stripped.startswith("@"):
            current_kind = ""
            current_item = None
        elif current_kind == "brief":
            result["brief"] = f"{result['brief']} {stripped}".strip()
        elif current_kind == "note" and result["notes"]:
            result["notes"][-1] = f"{result['notes'][-1]} {stripped}".strip()
        elif current_kind == "param" and current_item is not None:
            current_item["description"] = f"{current_item['description']} {stripped}".strip()
        elif current_kind == "return" and result["returns"]:
            result["returns"][-1] = f"{result['returns'][-1]} {stripped}".strip()

    return result


def normalize_signature(signature: str) -> str:
    signature = re.sub(r"\s+", " ", signature).strip()
    signature = signature.replace("__weak ", "")
    signature = re.sub(r"\s*,\s*", ", ", signature)
    signature = re.sub(r"\(\s+", "(", signature)
    signature = re.sub(r"\s+\)", ")", signature)
    return f"{signature};"


def chinese_subject(module_id: str, name: str) -> str:
    normalized = re.sub(r"[^A-Z0-9_]", "", name.upper())
    for keyword, subject in SUBJECT_RULES:
        if keyword in normalized:
            return subject
    return f"{MODULE_NAMES[module_id]} 外设"


def macro_tail(module_id: str, name: str) -> str:
    prefix = f"__HAL_{module_id.upper()}_"
    return name[len(prefix):] if name.startswith(prefix) else name.removeprefix("__HAL_")


def macro_target(module_id: str, raw_target: str) -> str:
    target = raw_target.strip("_")
    if not target:
        return f"{MODULE_NAMES[module_id]} 外设"

    target_rules = [
        ("TAMPER_TIMESTAMP_EXTI", "入侵检测与时间戳 EXTI 线"),
        ("WAKEUPTIMER_EXTI", "唤醒定时器 EXTI 线"),
        ("ALARM_EXTI", "闹钟 EXTI 线"),
        ("AUTORELOAD", "自动重装载寄存器 ARR"),
        ("CLOCKDIVISION", "时钟分频配置"),
        ("ICPRESCALER", "输入捕获预分频配置"),
        ("REPETITIONCOUNTER", "重复计数寄存器 RCR"),
        ("COMPARE", "捕获比较寄存器 CCR"),
        ("COUNTER", "计数器 CNT"),
        ("PRESCALER", "预分频寄存器 PSC"),
        ("UIFCPY", "更新中断标志复制位 UIFCPY"),
        ("CAPTUREPOLARITY", "输入捕获极性"),
        ("DMA_BURST_LENGTH", "DMA 突发传输长度"),
        ("WRITEPROTECTION", "写保护"),
        ("SHIFTCONTROL", "时间校准移位控制"),
        ("REFERENCECLOCKDETECTION", "参考时钟检测"),
        ("COARSE_CALIB", "粗略数字校准"),
        ("CALIBRATION_OUTPUT", "校准输出"),
        ("BYPASS_SHADOW", "影子寄存器旁路"),
        ("ALARMA", "闹钟 A"),
        ("ALARMB", "闹钟 B"),
        ("WAKEUPTIMER", "唤醒定时器"),
        ("TIMESTAMP", "时间戳功能"),
        ("TAMPER", "入侵检测功能"),
        ("BACKUP", "备份域"),
        ("SYNCHRO", "RTC 寄存器同步"),
        ("MOE", "主输出使能 MOE"),
        ("DMA", "DMA 请求"),
        ("EXTI", "EXTI 线"),
        ("FLAG", "状态标志"),
    ]
    for marker, description in target_rules:
        if marker in target:
            return description

    if module_id == "rcc":
        return f"{target.replace('_', ' ')} 外设"
    return f"{MODULE_NAMES[module_id]} 的 {target.replace('_', ' ')} 功能"


def macro_brief(module_id: str, name: str) -> str:
    if name in MACRO_DETAIL_OVERRIDES:
        return str(MACRO_DETAIL_OVERRIDES[name]["brief"])

    special_briefs = {
        "__HAL_ADC_CHANNEL_INTERNAL_TO_EXTERNAL": "将 ADC 内部通道编号转换为对应的外部通道编号。",
        "__HAL_ADC_CHANNEL_TO_DECIMAL_NB": "将 ADC 通道常量转换为十进制通道序号。",
        "__HAL_ADC_COMMON_INSTANCE": "获取当前 ADC 所属的公共控制寄存器实例。",
        "__HAL_ADC_CONVERT_DATA_RESOLUTION": "在不同 ADC 分辨率之间换算原始转换数据。",
        "__HAL_ADC_DECIMAL_NB_TO_CHANNEL": "将十进制通道序号转换为 ADC 通道常量。",
        "__HAL_ADC_DIGITAL_SCALE": "计算指定 ADC 分辨率对应的数字满量程值。",
        "__HAL_ADC_MULTI_CONV_DATA_MASTER_SLAVE": "从 ADC 多模式数据寄存器中拆分主从 ADC 转换结果。",
        "__HAL_RCC_CRS_RELOADVALUE_CALCULATE": "根据目标同步频率计算 CRS 时钟恢复的重装载值。",
        "__HAL_RCC_HSI_CALIBRATIONVALUE_ADJUST": "调整 HSI 内部高速时钟的校准值。",
        "__HAL_RCC_RTC_CLKPRESCALER": "配置 RTC 使用 HSE 时的时钟预分频值。",
        "__HAL_RCC_TIMCLKPRESCALER": "配置 APB 定时器内核时钟的预分频规则。",
        "__HAL_TIM_IS_TIM_COUNTING_DOWN": "判断定时器当前是否处于向下计数方向。",
        "__HAL_TIM_MOE_DISABLE_UNCONDITIONALLY": "无条件关闭高级定时器主输出使能 MOE。",
        "__HAL_TIM_SELECT_CCDMAREQUEST": "选择捕获比较 DMA 请求由 CC 事件还是更新事件触发。",
        "__HAL_UART_FLUSH_DRREGISTER": "清空串口接收数据寄存器中的待读数据。",
        "__HAL_UART_SEND_REQ": "向串口请求寄存器写入指定的软件请求。",
        "__HAL_RTC_DAYLIGHT_SAVING_TIME_ADD1H": "将 RTC 当前日历时间增加 1 小时。",
        "__HAL_RTC_DAYLIGHT_SAVING_TIME_SUB1H": "将 RTC 当前日历时间减少 1 小时。",
        "__HAL_RTC_IS_CALENDAR_INITIALIZED": "判断 RTC 日历是否已经完成初始化。",
        "__HAL_IWDG_RELOAD_COUNTER": "重装独立看门狗计数器，防止本周期内产生复位。",
        "__HAL_IWDG_START": "启动独立看门狗；启动后通常只能由系统复位停止。",
    }
    if name in special_briefs:
        return special_briefs[name]

    tail = macro_tail(module_id, name)
    if module_id == "rcc":
        rcc_rules = [
            ("_IS_CLK_SLEEP_DISABLED", "判断睡眠模式下{target}时钟是否已禁用。"),
            ("_IS_CLK_SLEEP_ENABLED", "判断睡眠模式下{target}时钟是否已使能。"),
            ("_CLK_SLEEP_DISABLE", "禁止{target}在处理器睡眠期间继续接收时钟。"),
            ("_CLK_SLEEP_ENABLE", "允许{target}在处理器睡眠期间继续接收时钟。"),
            ("_IS_CLK_DISABLED", "判断{target}时钟是否已禁用。"),
            ("_IS_CLK_ENABLED", "判断{target}时钟是否已使能。"),
            ("_CLK_DISABLE", "关闭{target}的外设时钟。"),
            ("_CLK_ENABLE", "开启{target}的外设时钟。"),
            ("_FORCE_RESET", "将{target}保持在硬件复位状态。"),
            ("_RELEASE_RESET", "释放{target}的硬件复位。"),
        ]
        for suffix, sentence in rcc_rules:
            if tail == suffix.lstrip("_") or tail.endswith(suffix):
                target = tail[:-len(suffix)].replace("_", " ") if tail.endswith(suffix) else "RCC"
                return sentence.format(target=target)
        if tail.startswith("GET_") and tail.endswith("_SOURCE"):
            target = tail[4:-7].replace("_", " ")
            return f"读取 {target} 当前选择的时钟源。"
        if tail.endswith("_CONFIG"):
            target = tail[:-7].replace("_", " ")
            return f"选择 {target} 外设的内核时钟源。"
        if tail == "GET_FLAG":
            return "读取指定的 RCC 复位或时钟状态标志。"
        if tail == "CLEAR_RESET_FLAGS":
            return "清除 RCC 复位原因标志。"
        if tail == "ENABLE_IT":
            return "使能指定的 RCC 中断源。"
        if tail == "DISABLE_IT":
            return "禁用指定的 RCC 中断源。"
        if tail == "CLEAR_IT":
            return "清除指定的 RCC 中断挂起标志。"
        if tail == "GET_IT":
            return "读取指定的 RCC 中断挂起状态。"
        if tail == "BACKUPRESET_FORCE":
            return "强制复位 RCC 备份域。"
        if tail == "BACKUPRESET_RELEASE":
            return "释放 RCC 备份域复位。"

    if tail.endswith("_EXTI_RISING_IT"):
        target = macro_target(module_id, tail[:-len("_EXTI_RISING_IT")])
        return f"判断{target}的 EXTI 上升沿中断是否挂起。"
    if tail.endswith("_EXTI_FALLING_IT"):
        target = macro_target(module_id, tail[:-len("_EXTI_FALLING_IT")])
        return f"判断{target}的 EXTI 下降沿中断是否挂起。"

    action_rules = [
        ("_EXTI_ENABLE_RISING_FALLING_EDGE", "同时使能{target}的上升沿和下降沿触发。"),
        ("_EXTI_DISABLE_RISING_FALLING_EDGE", "同时禁用{target}的上升沿和下降沿触发。"),
        ("_EXTI_ENABLE_RISING_EDGE", "使能{target}的上升沿触发。"),
        ("_EXTI_DISABLE_RISING_EDGE", "禁用{target}的上升沿触发。"),
        ("_EXTI_ENABLE_FALLING_EDGE", "使能{target}的下降沿触发。"),
        ("_EXTI_DISABLE_FALLING_EDGE", "禁用{target}的下降沿触发。"),
        ("_EXTI_GENERATE_SWIT", "软件触发{target}中断事件。"),
        ("_EXTI_ENABLE_EVENT", "使能{target}事件请求。"),
        ("_EXTI_DISABLE_EVENT", "禁用{target}事件请求。"),
        ("_EXTI_ENABLE_IT", "使能{target}中断请求。"),
        ("_EXTI_DISABLE_IT", "禁用{target}中断请求。"),
        ("_EXTI_CLEAR_FLAG", "清除{target}挂起标志。"),
        ("_EXTI_CLEAR_IT", "清除{target}中断挂起位。"),
        ("_EXTI_GET_FLAG", "读取{target}挂起标志。"),
        ("_GET_IT_SOURCE", "判断指定的{target}中断源是否已使能。"),
        ("_DISABLE_IT", "禁用指定的{target}中断源。"),
        ("_ENABLE_IT", "使能指定的{target}中断源。"),
        ("_CLEAR_FLAG", "清除指定的{target}状态标志。"),
        ("_CLEAR_IT", "清除指定的{target}中断挂起标志。"),
        ("_GET_FLAG", "读取指定的{target}状态标志。"),
        ("_GET_IT", "读取指定的{target}中断挂起状态。"),
        ("_RESET_HANDLE_STATE", "将{target}句柄的软件状态恢复为复位态。"),
        ("_GENERATE_SWIT", "通过软件产生{target}中断。"),
        ("_GENERATE_NACK", "控制{target}在下一字节应答阶段发送 NACK。"),
        ("_DISABLE_DMA", "禁用指定通道的{target}请求。"),
        ("_ENABLE_DMA", "使能指定通道的{target}请求。"),
        ("_DISABLE", "禁用{target}。"),
        ("_ENABLE", "使能{target}。"),
    ]
    for suffix, sentence in action_rules:
        if tail == suffix.lstrip("_") or tail.endswith(suffix):
            raw_target = tail[:-len(suffix)] if tail.endswith(suffix) else ""
            target = macro_target(module_id, raw_target)
            return sentence.format(target=target)

    start_rules = [
        ("SET_", "设置"),
        ("GET_", "读取"),
        ("IS_", "判断"),
        ("CLEAR_", "清除"),
        ("SEND_", "发送"),
        ("FLUSH_", "清空"),
        ("START", "启动"),
        ("RELOAD_", "重装载"),
    ]
    for prefix, action in start_rules:
        if tail.startswith(prefix):
            target = tail[len(prefix):]
            return f"{action}{macro_target(module_id, target)}。"

    middle_rules = [
        ("_SET_", "设置"),
        ("_GET_", "读取"),
        ("_IS_", "判断"),
        ("_CLEAR_", "清除"),
        ("_SEND_", "发送"),
    ]
    for marker, action in middle_rules:
        if marker in tail:
            _, target = tail.split(marker, 1)
            return f"{action}{macro_target(module_id, target)}。"

    if tail.startswith("CALC_"):
        return f"计算{macro_target(module_id, tail[5:])}所需的寄存器值。"
    return f"执行 {MODULE_NAMES[module_id]} 的 {tail.replace('_', ' ')} 操作。"


def chinese_brief(module_id: str, name: str, kind: str) -> str:
    if name in DETAIL_OVERRIDES:
        return DETAIL_OVERRIDES[name]["brief"]
    subject = chinese_subject(module_id, name)
    upper_name = name.upper()

    if kind == "macro":
        return macro_brief(module_id, name)

    if "MspDeInit" in name:
        return f"执行{subject}的底层硬件反初始化回调。"
    if "MspInit" in name:
        return f"执行{subject}的底层硬件初始化回调。"
    if "UnRegisterCallback" in name:
        return f"取消注册{subject}的用户回调函数。"
    if "RegisterCallback" in name:
        return f"注册{subject}的用户回调函数。"
    if "Callback" in name:
        return f"处理{subject}对应的回调事件。"
    if "IRQHandler" in name:
        return f"处理{subject}产生的中断。"

    action_rules = [
        ("TransmitReceive_DMA", "以 DMA 方式启动同步收发"),
        ("TransmitReceive_IT", "以中断方式启动同步收发"),
        ("TransmitReceive", "以阻塞方式执行同步收发"),
        ("ReceiveToIdle_DMA", "以 DMA 和空闲线方式启动接收"),
        ("ReceiveToIdle_IT", "以中断和空闲线方式启动接收"),
        ("Transmit_DMA", "以 DMA 方式启动发送"),
        ("Transmit_IT", "以中断方式启动发送"),
        ("Transmit", "以阻塞方式执行发送"),
        ("Receive_DMA", "以 DMA 方式启动接收"),
        ("Receive_IT", "以中断方式启动接收"),
        ("Receive", "以阻塞方式执行接收"),
        ("Start_DMA", "以 DMA 方式启动"),
        ("Start_IT", "以中断方式启动"),
        ("Stop_DMA", "停止 DMA 方式的"),
        ("Stop_IT", "停止中断方式的"),
        ("DeInit", "反初始化"),
        ("Init", "初始化"),
        ("Start", "启动"),
        ("Stop", "停止"),
        ("PollFor", "轮询等待"),
        ("GetState", "获取运行状态"),
        ("GetError", "获取错误码"),
        ("Get", "获取"),
        ("Set", "设置"),
        ("Read", "读取"),
        ("Write", "写入"),
        ("Config", "配置"),
        ("Enable", "使能"),
        ("Disable", "禁用"),
        ("Activate", "启用"),
        ("Deactivate", "停用"),
        ("Abort", "中止"),
        ("Suspend", "暂停"),
        ("Resume", "恢复"),
        ("Reset", "复位"),
        ("Clear", "清除"),
        ("Lock", "锁定"),
        ("Unlock", "解锁"),
    ]
    for marker, action in action_rules:
        if marker in name:
            return f"{action}{subject}。"
    return f"提供{subject}相关的 HAL 操作接口。"


def normalized_parameter_name(name: str) -> str:
    return re.sub(r"^_+|_+$", "", re.sub(r"\\\s*", "", name).strip()).upper()


def macro_parameter(
    module_id: str,
    macro_name: str,
    parameter_name: str,
    source_description: str,
) -> str:
    normalized = normalized_parameter_name(parameter_name)
    override = MACRO_DETAIL_OVERRIDES.get(macro_name, {})
    override_params = override.get("params", {}) if isinstance(override, dict) else {}
    if normalized in override_params:
        return str(override_params[normalized])

    if "HANDLE" in normalized:
        handle_examples = {
            "dma": "&hdma_usart1_tx",
            "rtc": "&hrtc",
            "iwdg": "&hiwdg",
        }
        example = handle_examples.get(module_id, f"&h{module_id}1")
        return f"{MODULE_NAMES[module_id]} 句柄指针，例如 {example}。"
    if normalized in {"INTERRUPT", "IT"}:
        return f"要操作的 {MODULE_NAMES[module_id]} 中断源位掩码；多个中断源可按位或组合。"
    if "FLAG" in normalized:
        return f"要查询或清除的 {MODULE_NAMES[module_id]} 状态标志位掩码。"
    if normalized == "CHANNEL" or normalized.endswith("CHANNEL"):
        channel_examples = {
            "tim": "TIM_CHANNEL_1",
            "adc": "ADC_CHANNEL_1",
            "dac": "DAC_CHANNEL_1",
            "rtc": "RTC_TAMPER_1",
        }
        example = channel_examples.get(module_id, f"{module_id.upper()}_CHANNEL_1")
        return f"目标 {MODULE_NAMES[module_id]} 通道，例如 {example}。"
    if normalized in {"COMPARE", "PULSE"}:
        return "写入捕获比较寄存器 CCR 的计数值，通常应位于 0～ARR 范围内。"
    if normalized == "COUNTER":
        return "写入计数器 CNT 的当前计数值。"
    if normalized in {"AUTORELOAD", "PERIOD"}:
        return "写入自动重装载寄存器 ARR 的周期计数值。"
    if normalized in {"PRESCALER", "PSC", "PRESC"}:
        return "预分频寄存器值；实际分频系数通常为该值加 1。"
    if normalized == "TIMCLK":
        return "定时器输入时钟频率，单位 Hz。"
    if normalized in {"CNTCLK", "COUNTERCLOCK"}:
        return "期望的计数器时钟频率，单位 Hz。"
    if normalized in {"FREQ", "FTARGET", "FSYNC"}:
        return "期望的目标频率，单位 Hz。"
    if normalized == "DELAY":
        return "期望的延时时间，单位 μs。"
    if "EXTI_LINE" in normalized:
        return "需要操作的 EXTI 线路位掩码。"
    if normalized == "SOURCE" or "CLKSOURCE" in normalized or "CLOCKSOURCE" in normalized:
        target = normalized.removesuffix("CLKSOURCE").strip("_")
        if not target or target == "SOURCE":
            target = macro_tail(module_id, macro_name)
            target = re.sub(r"_(?:GET_)?SOURCE$|_CONFIG$", "", target)
        return f"为 {target.replace('_', ' ')} 选择的时钟源常量。"
    if normalized in {"STATE", "HAL_STATE"}:
        return "写入句柄的 HAL 软件状态枚举值。"
    if normalized in {"DMA", "DMAREQUEST", "DMASOURCE"}:
        return "要使能或禁用的 DMA 请求源位掩码。"
    if normalized in {"MODE", "POLARITY", "EDGE"}:
        return f"{MODULE_NAMES[module_id]} 的{normalized.lower()}选择值。"
    if "ADC_DATA" in normalized:
        return "ADC 转换得到的原始数字量。"
    if "ADC_RESOLUTION" in normalized or normalized == "RESOLUTION":
        return "ADC 分辨率配置，用于确定满量程数字值。"
    if "VREFANALOG" in normalized:
        return "ADC 模拟参考电压，单位 mV。"
    if "TEMPSENSOR" in normalized:
        return "芯片温度传感器校准值或当前采样值。"
    if normalized in {"BKP", "BACKUPREGISTER"}:
        return "目标 RTC 备份寄存器编号。"
    if normalized == "TAMPER":
        return "目标 RTC 入侵检测通道。"
    if "DAC_CHANNEL" in normalized:
        return "目标 DAC 输出通道。"
    if "PLLCLOCKOUT" in normalized:
        return "要查询、使能或禁用的 PLL 输出通道，例如 PLLP、PLLQ 或 PLLR。"
    if "PLL" in normalized and ("DIV" in normalized or normalized.endswith(("M", "N", "P", "Q", "R"))):
        return "PLL 倍频或分频参数，用于计算对应 PLL 输出频率。"
    if "PLLMUL" in normalized or normalized.endswith("MUL"):
        return "PLL 倍频系数选择值。"
    if "PLL" in normalized and "SOURCE" in normalized:
        return "PLL 输入时钟源选择值。"
    if "LSEDRIVE" in normalized:
        return "LSE 低速外部晶振驱动能力等级。"
    if "MCODIV" in normalized:
        return "MCO 时钟输出分频系数。"
    if normalized in {"ADCX", "ADC_INSTANCE", "ADCXY_COMMON"}:
        return "目标 ADC 实例或 ADC 公共寄存器实例。"
    if normalized == "DECIMAL_NB":
        return "十进制表示的 ADC 通道序号。"
    if normalized == "ADC_MULTI_MASTER_SLAVE":
        return "ADC 多模式数据寄存器中的主从转换组合值。"
    if normalized == "CCDMA":
        return "捕获比较 DMA 请求源选择，决定由 CC 事件或更新事件触发。"
    if normalized == "CKD":
        return "定时器数字滤波采样时钟分频配置。"
    if normalized == "ICPSC":
        return "输入捕获预分频配置，例如每 1、2、4 或 8 个有效边沿捕获一次。"
    if normalized == "IT_CLEAR":
        return "需要清除的串口中断清除位掩码。"
    if normalized == "REQ":
        return "要发送的串口软件请求，例如发送数据刷新或接收数据刷新。"
    if "VALUE" in normalized or normalized.endswith("DATA"):
        return f"传给 {macro_tail(module_id, macro_name).replace('_', ' ')} 操作的数据值。"

    readable_name = normalized.replace("_", " ")
    if source_description:
        if "frequency" in source_description.lower() and "hz" in source_description.lower():
            return f"{readable_name} 对应的频率值，单位 Hz。"
        if "voltage" in source_description.lower():
            return f"{readable_name} 对应的电压值。"
    return f"{macro_tail(module_id, macro_name).replace('_', ' ')} 操作使用的 {readable_name} 参数。"


def chinese_parameter(
    module_id: str,
    name: str,
    owner_name: str = "",
    source_description: str = "",
    kind: str = "function",
) -> str:
    if kind == "macro":
        return macro_parameter(module_id, owner_name, name, source_description)

    normalized = normalized_parameter_name(name)
    if "HEADER" in normalized:
        return "报文头配置或输出结构体。"
    if "HANDLE" in normalized or normalized.startswith("H") and len(normalized) <= 8:
        return f"{MODULE_NAMES[module_id]} 外设句柄。"
    if "CHANNEL" in normalized:
        return "目标外设通道。"
    if "COMPARE" in normalized:
        return "待设置的捕获比较值。"
    if "CALLBACK" in normalized:
        return "用户回调函数指针。"
    if "CONFIG" in normalized or "INIT" in normalized:
        return "配置结构体或配置参数。"
    if "PDATA" in normalized or "ADATA" in normalized or "BUFFER" in normalized:
        return "数据缓冲区指针。"
    if "SIZE" in normalized or "LENGTH" in normalized or normalized == "LEN":
        return "数据项数量或缓冲区长度。"
    if "TIMEOUT" in normalized:
        return "最大等待时间。"
    if "ADDRESS" in normalized or "ADDR" in normalized:
        return "目标地址或寄存器地址。"
    if "STATE" in normalized:
        return "待设置或读取的状态。"
    if "MODE" in normalized:
        return "工作模式选择。"
    if "VALUE" in normalized or "DATA" in normalized:
        return "待设置的数据或数值。"
    if "FLAG" in normalized or "IT" == normalized:
        return "状态标志或中断标志。"
    return f"参数 {name}，具体含义以当前系列 HAL 头文件为准。"


def chinese_return(prototype: str, kind: str, name: str) -> str:
    if kind == "macro":
        override = MACRO_DETAIL_OVERRIDES.get(name)
        if override:
            return str(override["returns"])
        tail = name.upper()
        return_rules = [
            ("GET_COUNTER", "返回当前计数器 CNT 的数值。"),
            ("GET_AUTORELOAD", "返回自动重装载寄存器 ARR 的数值。"),
            ("GET_COMPARE", "返回指定通道捕获比较寄存器 CCR 的数值。"),
            ("GET_CLOCKDIVISION", "返回定时器时钟分频位的寄存器编码。"),
            ("GET_ICPRESCALER", "返回指定通道输入捕获预分频位的寄存器编码。"),
            ("GET_FLAG", "目标标志置位时返回非 0，否则返回 0。"),
            ("GET_IT_SOURCE", "目标中断源已使能时返回非 0，否则返回 0。"),
            ("GET_IT", "目标中断处于挂起状态时返回非 0，否则返回 0。"),
            ("IS_CLK_ENABLED", "时钟已使能时返回非 0，否则返回 0。"),
            ("IS_CLK_DISABLED", "时钟已禁用时返回非 0，否则返回 0。"),
            ("IS_CLK_SLEEP_ENABLED", "睡眠时钟已使能时返回非 0，否则返回 0。"),
            ("IS_CLK_SLEEP_DISABLED", "睡眠时钟已禁用时返回非 0，否则返回 0。"),
        ]
        for marker, description in return_rules:
            if marker in tail:
                return description
        if "_GET_" in tail or tail.startswith("__HAL_RCC_GET_") or "_IS_" in tail:
            return "返回该配置项对应的寄存器编码值或条件判断结果。"
        return "无返回值；宏直接修改外设寄存器或 HAL 句柄字段。"
    return_type = prototype.split(name, 1)[0].strip()
    if return_type.endswith("void"):
        return "无。"
    if "HAL_StatusTypeDef" in return_type:
        return "HAL 状态：HAL_OK、HAL_ERROR、HAL_BUSY 或 HAL_TIMEOUT，实际范围由该接口决定。"
    return "返回对应的状态、计数值或数据，具体含义以函数原型和当前系列头文件为准。"


def chinese_notes(
    module_id: str,
    name: str,
    kind: str,
    different_prototypes: bool,
) -> str:
    if name in DETAIL_OVERRIDES:
        return DETAIL_OVERRIDES[name]["notes"]
    if kind == "macro":
        override = MACRO_DETAIL_OVERRIDES.get(name)
        if override:
            notes = str(override["notes"])
        elif name == "__HAL_TIM_SET_COMPARE":
            notes = "直接写入指定通道的 CCR 捕获比较寄存器，常用于运行中更新 PWM 占空比。比较值通常应限制在 0 到 ARR 之间；若启用了预装载，新值会在更新事件后生效。"
        elif name == "__HAL_IWDG_START":
            notes = "写入启动键后独立看门狗开始计数，通常只能通过芯片复位停止。启动前必须先设置分频和重装载值，并保证程序后续能按周期喂狗。"
        elif name == "__HAL_IWDG_RELOAD_COUNTER":
            notes = "该宏写入重装载键以刷新看门狗倒计时。调用周期必须小于按 LSI、预分频和重装载值计算出的超时时间；不要用喂狗掩盖任务卡死。"
        elif "CLK_SLEEP_ENABLE" in name or "CLK_SLEEP_DISABLE" in name:
            notes = "该宏只控制处理器睡眠期间的外设时钟，不改变正常运行时的时钟使能状态。是否保留睡眠时钟应结合低功耗功耗预算和外设唤醒需求决定。"
        elif "CLK_ENABLE" in name:
            notes = "访问外设寄存器前必须先开启对应总线时钟。时钟使能后可读取一次使能寄存器或执行短暂屏障，确保后续外设访问发生在时钟稳定之后。"
        elif "CLK_DISABLE" in name:
            notes = "关闭时钟前应确认外设传输已经结束且不再产生 DMA 或中断请求。关闭后继续访问该外设寄存器不会得到有效结果。"
        elif "FORCE_RESET" in name or "BACKUPRESET_FORCE" in name:
            notes = "强制复位会清除该外设的寄存器配置。通常应随后调用对应的 RELEASE_RESET 宏，再重新执行外设初始化。"
        elif "RELEASE_RESET" in name or "BACKUPRESET_RELEASE" in name:
            notes = "该宏只释放硬件复位，不会恢复时钟、GPIO、DMA 或 HAL 句柄配置；释放后仍需按正常流程初始化外设。"
        elif "_CONFIG" in name and module_id == "rcc":
            notes = "切换外设内核时钟源前，应停止相关外设并确认候选时钟源已经就绪。切换后需要重新核对波特率、采样率或定时参数。"
        elif "ENABLE_IT" in name:
            notes = "该宏只打开外设内部中断源；还必须配置对应 NVIC IRQ、优先级和中断服务函数。使能前建议先清除遗留挂起标志。"
        elif "DISABLE_IT" in name:
            notes = "该宏只关闭指定的外设内部中断源，不会自动清除已经置位的状态标志或 NVIC 挂起位。"
        elif "CLEAR_FLAG" in name or "CLEAR_IT" in name:
            notes = "不同外设的标志清除方式可能是写 0、写 1 或读寄存器序列；应调用本宏完成清除，不要自行对状态寄存器做通用读改写。"
        elif "CLEAR_" in name:
            notes = "该宏按目标外设规定的寄存器读写序列清除对应状态。某些错误标志需要先读状态寄存器再读数据寄存器，不能用普通位清零代替。"
        elif "GET_FLAG" in name or "GET_IT" in name or "_IS_" in name:
            notes = "该宏读取的是调用瞬间的硬件状态。若标志由中断或硬件异步更新，应在读取后及时处理，并按该外设规定的方法清除。"
        elif "_EXTI_" in name:
            notes = "该宏只配置与该功能相连的 EXTI 线路。要真正响应事件，还需配置触发边沿、解除中断屏蔽并在 NVIC 中使能对应 IRQ。"
        elif "RESET_HANDLE_STATE" in name:
            notes = "该宏只重置 HAL 句柄中的软件状态与锁，不会复位外设寄存器、停止正在进行的 DMA，也不会清除硬件错误标志。"
        elif "_SET_" in name:
            notes = "该宏直接写入对应寄存器字段。调用前应确认外设状态允许修改；带预装载的寄存器可能要等更新事件后才真正生效。"
        elif "_GET_" in name:
            notes = "该宏直接读取寄存器字段，返回值通常是原始计数值或位域编码；换算为时间、电压或频率时还需结合当前时钟和配置参数。"
        elif name.endswith("_ENABLE"):
            notes = "使能前应先完成时钟、GPIO 和工作参数配置，并清除可能残留的状态标志。宏只改变对应硬件使能位。"
        elif name.endswith("_DISABLE"):
            notes = "禁用前应等待当前传输或转换结束。宏只改变对应硬件使能位，不会自动释放 GPIO、DMA 或中断资源。"
        else:
            notes = f"该宏完成“{macro_tail(module_id, name).replace('_', ' ')}”寄存器操作。调用前应确认 {MODULE_NAMES[module_id]} 已完成初始化，并避免传入带自增或函数调用的表达式，以免宏展开后被重复求值。"
    else:
        if "IRQHandler" in name:
            notes = "应在对应外设的 IRQHandler 中调用。该函数会检查并清除中断标志，再分发完成、错误等回调；用户回调应保持短小，避免阻塞操作。"
        elif "_DMA" in name:
            notes = "调用前必须完成 DMA 通道、请求映射和缓冲区配置。传输完成前缓冲区必须持续有效，并应处理 HAL_BUSY、完成回调和错误回调。"
        elif "_IT" in name:
            notes = "调用前必须正确配置外设中断源和 NVIC。操作完成后由对应 HAL 回调通知结果；再次启动前应确认句柄不处于忙状态。"
        elif "PollFor" in name:
            notes = "该接口会阻塞等待事件或超时，不适合放在高频中断和严格实时控制环中。超时时间通常基于 HAL_GetTick() 计算。"
        elif "DeInit" in name:
            notes = "用于停止并复位该功能相关的软件状态和外设配置。是否关闭外设时钟、GPIO 或 DMA，取决于对应 MSP 反初始化实现。"
        elif "Init" in name:
            notes = "调用前应准备句柄和初始化结构体，并确保外设时钟、GPIO、DMA 与中断资源配置一致。失败时应检查参数断言和句柄错误状态。"
        elif "Get" in name or "Read" in name:
            notes = "读取结果的单位、有效位宽和清零行为取决于具体外设配置；连续读取前应确认是否需要等待状态标志或处理寄存器锁存。"
        elif "Set" in name or "Config" in name:
            notes = "修改运行中外设配置前，应确认当前句柄状态允许该操作。部分寄存器使用预装载机制，新配置会在更新事件或下一次传输时生效。"
        else:
            notes = "调用前应确认外设时钟已开启、句柄已初始化且参数与当前工作模式一致。异步操作必须结合完成回调、错误回调和句柄忙状态使用。"
    if different_prototypes:
        notes += " F1、F4、G4 的原型存在差异，移植时需要核对当前工程头文件。"
    return notes


def macro_example_argument(module_id: str, macro_name: str, parameter_name: str) -> str:
    normalized = normalized_parameter_name(parameter_name)
    handle_names = {
        "gpio": "GPIOA",
        "dma": "&hdma_usart1_tx",
        "adc": "&hadc1",
        "dac": "&hdac1",
        "tim": "&htim1",
        "uart": "&huart1",
        "i2c": "&hi2c1",
        "spi": "&hspi1",
        "can": "&hcan1",
        "fdcan": "&hfdcan1",
        "rtc": "&hrtc",
        "iwdg": "&hiwdg",
    }
    interrupt_names = {
        "dma": "DMA_IT_TC",
        "adc": "ADC_IT_EOC",
        "dac": "DAC_IT_DMAUDR1",
        "tim": "TIM_IT_UPDATE",
        "uart": "UART_IT_IDLE",
        "i2c": "I2C_IT_ERRI",
        "spi": "SPI_IT_RXNE",
        "can": "CAN_IT_RX_FIFO0_MSG_PENDING",
        "fdcan": "FDCAN_IT_RX_FIFO0_NEW_MESSAGE",
        "rtc": "RTC_IT_ALRA",
        "rcc": "RCC_IT_CSS",
    }
    flag_names = {
        "gpio": "GPIO_PIN_13",
        "dma": "DMA_FLAG_TCIF0_4",
        "adc": "ADC_FLAG_EOC",
        "dac": "DAC_FLAG_DMAUDR1",
        "tim": "TIM_FLAG_UPDATE",
        "uart": "UART_FLAG_IDLE",
        "i2c": "I2C_FLAG_STOPF",
        "spi": "SPI_FLAG_RXNE",
        "can": "CAN_FLAG_ERROR",
        "fdcan": "FDCAN_FLAG_ERROR_PASSIVE",
        "rtc": "RTC_FLAG_ALRAF",
        "rcc": "RCC_FLAG_PINRST",
    }
    if "HANDLE" in normalized:
        return handle_names.get(module_id, f"&h{module_id}1")
    if normalized in {"INTERRUPT", "IT"}:
        return interrupt_names.get(module_id, f"{module_id.upper()}_IT_UPDATE")
    if "FLAG" in normalized:
        return flag_names.get(module_id, f"{module_id.upper()}_FLAG_READY")
    if "EXTI_LINE" in normalized:
        return "GPIO_PIN_13"
    if normalized.endswith("CHANNEL") or normalized == "CHANNEL":
        return "TIM_CHANNEL_1" if module_id == "tim" else f"{module_id.upper()}_CHANNEL_1"
    if normalized in {"COMPARE", "PULSE"}:
        return "500U"
    if normalized == "COUNTER":
        return "0U"
    if normalized in {"AUTORELOAD", "PERIOD"}:
        return "999U"
    if normalized in {"PRESCALER", "PSC", "PRESC"}:
        return "169U"
    if normalized == "TIMCLK":
        return "170000000U"
    if normalized in {"CNTCLK", "FREQ", "FTARGET", "FSYNC"}:
        return "1000U"
    if normalized in {"DELAY", "PULSE"}:
        return "20U"
    if normalized == "STATE":
        return "HAL_READY"
    if normalized == "DMA":
        return "TIM_DMA_UPDATE" if module_id == "tim" else f"{module_id.upper()}_DMA_REQUEST"
    variable = re.sub(r"[^a-z0-9]+", "_", normalized.lower()).strip("_")
    return variable or "value"


def make_example(
    name: str,
    params: list[dict[str, str]],
    prototype: str,
    kind: str,
    module_id: str = "",
) -> str:
    if name in DETAIL_OVERRIDES:
        return DETAIL_OVERRIDES[name]["example"]
    if name == "__HAL_TIM_SET_COMPARE":
        return "__HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_3, Tcmp3);"
    if kind == "macro":
        override = MACRO_DETAIL_OVERRIDES.get(name)
        if override:
            return str(override["example"])
        arguments = [macro_example_argument(module_id, name, str(param["name"])) for param in params]
        call = f"{name}({', '.join(arguments)})"
        if "_GET_FLAG" in name or "_GET_IT" in name or "_IS_" in name:
            return f"if ({call}) {{\n    // 条件成立时处理对应状态\n}}"
        if "_GET_" in name or name.startswith("__HAL_RCC_GET_"):
            return f"uint32_t value = {call};"
        return f"{call};"
    if kind == "function" and "Callback" in name:
        declaration = prototype.rstrip(";")
        return f"{declaration}\n{{\n    // 在此处理对应事件，保持回调短小\n}}"
    names = [param["name"].strip("[]") for param in params]
    return f"{name}({', '.join(names)});"


def extract_source(path: Path, family: str) -> list[dict[str, object]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    functions = []
    for match in FUNCTION_PATTERN.finditer(text):
        doc = parse_doc(match.group("doc"))
        name = match.group("name")
        functions.append(
            {
                "name": name,
                "family": family,
                "kind": "function",
                "prototype": normalize_signature(match.group("signature")),
                "brief": doc["brief"] or f"{name} HAL library function.",
                "params": doc["params"],
                "returns": "; ".join(doc["returns"]) or "See the current HAL source for return semantics.",
                "notes": " ".join(doc["notes"]),
            }
        )
    return functions


def extract_macros(path: Path, family: str) -> list[dict[str, object]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    docs = {
        match.group("name"): parse_doc(match.group("doc"))
        for match in MACRO_DOC_PATTERN.finditer(text)
    }
    macros = []
    for match in MACRO_PATTERN.finditer(text):
        name = match.group("name")
        raw_params = re.sub(r"\\\s*", "", match.group("params"))
        parameter_names = [re.sub(r"\s+", "", item) for item in raw_params.split(",") if item.strip()]
        doc = docs.get(name, {"brief": "", "params": [], "returns": [], "notes": []})
        documented_params = {
            normalized_parameter_name(str(item["name"])): str(item["description"])
            for item in doc["params"]
        }
        macros.append(
            {
                "name": name,
                "family": family,
                "kind": "macro",
                "prototype": f"#define {name}({', '.join(parameter_names)})",
                "brief": doc["brief"],
                "params": [
                    {
                        "name": item,
                        "description": documented_params.get(normalized_parameter_name(item), ""),
                    }
                    for item in parameter_names
                ],
                "returns": "; ".join(doc["returns"]),
                "notes": " ".join(doc["notes"]),
            }
        )
    return macros


def merge_records(
    records: list[dict[str, object]],
    module_id: str,
    kind: str,
) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for record in records:
        grouped.setdefault(str(record["name"]), []).append(record)

    merged = []
    family_order = {"F1": 0, "F4": 1, "G4": 2}
    for name, variants in grouped.items():
        variants.sort(key=lambda item: family_order[str(item["family"])])
        prototypes = [str(item["prototype"]) for item in variants]
        prototype = Counter(prototypes).most_common(1)[0][0]
        preferred = next(item for item in reversed(variants) if item["prototype"] == prototype)
        families = sorted({str(item["family"]) for item in variants}, key=family_order.get)
        prototype_map = {str(item["family"]): str(item["prototype"]) for item in variants}
        different_prototypes = len(set(prototype_map.values())) > 1

        params = [
            {
                "name": str(param["name"]),
                "description": chinese_parameter(
                    module_id,
                    str(param["name"]),
                    owner_name=name,
                    source_description=str(param.get("description", "")),
                    kind=kind,
                ),
            }
            for param in preferred["params"]
        ]

        merged.append(
            {
                "id": f"catalog-{'macro-' if kind == 'macro' else ''}{name.lower().replace('_', '-')}",
                "name": name,
                "kind": kind,
                "brief": chinese_brief(module_id, name, kind),
                "prototype": prototype,
                "params": params,
                "returns": chinese_return(prototype, kind, name),
                "notes": chinese_notes(module_id, name, kind, different_prototypes),
                "example": make_example(name, params, prototype, kind, module_id),
                "families": families,
                "familyPrototypes": prototype_map,
            }
        )

    return sorted(merged, key=lambda item: str(item["name"]).lower())


def build_catalog(repository_root: Path) -> dict[str, list[dict[str, object]]]:
    catalog: dict[str, list[dict[str, object]]] = {}
    for module_id, source_names in MODULE_SOURCES.items():
        function_records = []
        macro_records = []
        for family, (package, driver, prefix) in FAMILY_CONFIG.items():
            source_root = repository_root / package / "Drivers" / driver / "Src"
            header_root = repository_root / package / "Drivers" / driver / "Inc"
            for source_name in source_names:
                source_path = source_root / f"{prefix}_hal_{source_name}.c"
                if source_path.exists():
                    function_records.extend(extract_source(source_path, family))
                header_path = header_root / f"{prefix}_hal_{source_name}.h"
                if header_path.exists():
                    macro_records.extend(extract_macros(header_path, family))
        functions = merge_records(function_records, module_id, "function")
        macros = merge_records(macro_records, module_id, "macro")
        catalog[module_id] = functions + macros
    return catalog


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path.home() / "STM32Cube" / "Repository",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "dist" / "catalog.js",
    )
    args = parser.parse_args()

    catalog = build_catalog(args.repository_root)
    all_items = [item for items in catalog.values() for item in items]
    function_count = sum(item["kind"] == "function" for item in all_items)
    macro_count = sum(item["kind"] == "macro" for item in all_items)
    payload = json.dumps(catalog, ensure_ascii=False, indent=4)
    args.output.write_text(
        "// 由 tools/generate_catalog.py 从本机 STM32Cube HAL 源码生成。\n"
        f"window.HAL_GENERATED_CATALOG = {payload};\n",
        encoding="utf-8",
    )
    print(
        f"Generated {function_count} functions and {macro_count} macros "
        f"in {len(catalog)} modules: {args.output}"
    )


if __name__ == "__main__":
    main()
