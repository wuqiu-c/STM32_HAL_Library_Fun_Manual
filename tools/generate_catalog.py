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


def chinese_brief(module_id: str, name: str, kind: str) -> str:
    if name in DETAIL_OVERRIDES:
        return DETAIL_OVERRIDES[name]["brief"]
    subject = chinese_subject(module_id, name)
    upper_name = name.upper()

    if kind == "macro":
        macro_actions = [
            ("_SET_", "设置"),
            ("_GET_", "获取"),
            ("_ENABLE_", "使能"),
            ("_DISABLE_", "禁用"),
            ("_CLEAR_", "清除"),
            ("_RESET_", "复位"),
            ("_READ_", "读取"),
            ("_WRITE_", "写入"),
            ("_IS_", "判断"),
        ]
        for marker, action in macro_actions:
            if marker in upper_name:
                return f"通过宏{action}{subject}。"
        return f"用于直接操作{subject}的常用 HAL 宏。"

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


def chinese_parameter(module_id: str, name: str) -> str:
    normalized = name.strip().strip("[]").strip("*").upper()
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
        if "_GET_" in name or "_IS_" in name or "_READ_" in name:
            return "返回对应的寄存器值、配置值或状态。"
        return "无；宏直接修改寄存器或句柄字段。"
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
        if name == "__HAL_TIM_SET_COMPARE":
            notes = "直接写入指定通道的 CCR 捕获比较寄存器，常用于运行中更新 PWM 占空比。比较值通常应限制在 0 到 ARR 之间；若启用了预装载，新值会在更新事件后生效。"
        else:
            notes = "该宏直接访问寄存器或句柄字段，适合对已完成初始化的外设做快速配置。传入表达式应避免自增、函数调用等可能被重复求值的副作用。"
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


def make_example(
    name: str,
    params: list[dict[str, str]],
    prototype: str,
    kind: str,
) -> str:
    if name in DETAIL_OVERRIDES:
        return DETAIL_OVERRIDES[name]["example"]
    if name == "__HAL_TIM_SET_COMPARE":
        return "__HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_3, Tcmp3);"
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
    macros = []
    for match in MACRO_PATTERN.finditer(text):
        name = match.group("name")
        parameter_names = [item.strip() for item in match.group("params").split(",") if item.strip()]
        macros.append(
            {
                "name": name,
                "family": family,
                "kind": "macro",
                "prototype": f"#define {name}({', '.join(parameter_names)})",
                "params": [{"name": item, "description": ""} for item in parameter_names],
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
                "description": chinese_parameter(module_id, str(param["name"])),
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
                "example": make_example(name, params, prototype, kind),
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
