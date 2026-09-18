"use strict";

const DB_NAME = "stm32_hal_quick_reference";
const DB_VERSION = 1;
const STORE_NAME = "manual_data";
const DATA_KEY = "current";

function createFunction(name, brief, prototype, params, returns, notes, example, families = ["F1", "F4", "G4"]) {
    return {
        id: `${name.toLowerCase().replace(/[^a-z0-9]+/g, "-")}-${crypto.randomUUID()}`,
        name,
        brief,
        prototype,
        params,
        returns,
        notes,
        example,
        families
    };
}

const commonStatusReturn = "HAL_OK：操作成功；HAL_ERROR：参数或外设状态异常；部分异步函数还可能返回 HAL_BUSY。";
const timeoutNote = "Timeout 的单位通常由 HAL_GetTick() 决定，默认配置下一般按毫秒理解。具体行为以当前工程 HAL 源码为准。";

const seedData = {
    schemaVersion: 5,
    updatedAt: new Date().toISOString(),
    categories: [
        {
            id: "system-core",
            name: "System Core",
            modules: [
                {
                    id: "gpio",
                    name: "GPIO",
                    description: "通用输入输出：初始化、读写、翻转与外部中断处理。",
                    functions: [
                        createFunction(
                            "HAL_GPIO_Init",
                            "按照 GPIO_InitTypeDef 配置一个或多个引脚。",
                            "void HAL_GPIO_Init(GPIO_TypeDef *GPIOx, GPIO_InitTypeDef *GPIO_Init);",
                            [
                                { name: "GPIOx", description: "GPIO 端口，例如 GPIOA。" },
                                { name: "GPIO_Init", description: "引脚号、模式、上下拉、速度和复用配置。" }
                            ],
                            "无。",
                            "调用前必须先打开对应 GPIO 端口时钟。复用功能编号及速度等级会随芯片系列和具体型号变化。",
                            "GPIO_InitTypeDef gpio_init = {0};\ngpio_init.Pin = GPIO_PIN_5;\ngpio_init.Mode = GPIO_MODE_OUTPUT_PP;\ngpio_init.Pull = GPIO_NOPULL;\ngpio_init.Speed = GPIO_SPEED_FREQ_LOW;\nHAL_GPIO_Init(GPIOA, &gpio_init);"
                        ),
                        createFunction(
                            "HAL_GPIO_DeInit",
                            "将指定 GPIO 引脚恢复到复位状态。",
                            "void HAL_GPIO_DeInit(GPIO_TypeDef *GPIOx, uint32_t GPIO_Pin);",
                            [
                                { name: "GPIOx", description: "GPIO 端口。" },
                                { name: "GPIO_Pin", description: "一个或多个 GPIO_PIN_x 位组合。" }
                            ],
                            "无。",
                            "该函数不会自动关闭 GPIO 端口时钟。",
                            "HAL_GPIO_DeInit(GPIOA, GPIO_PIN_5);"
                        ),
                        createFunction(
                            "HAL_GPIO_ReadPin",
                            "读取指定 GPIO 引脚的当前逻辑电平。",
                            "GPIO_PinState HAL_GPIO_ReadPin(GPIO_TypeDef *GPIOx, uint16_t GPIO_Pin);",
                            [
                                { name: "GPIOx", description: "GPIO 端口。" },
                                { name: "GPIO_Pin", description: "要读取的单个引脚。" }
                            ],
                            "GPIO_PIN_SET 或 GPIO_PIN_RESET。",
                            "返回的是输入数据寄存器中的引脚状态。读取输出脚时，结果仍代表引脚输入电平。",
                            "if (HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_13) == GPIO_PIN_RESET) {\n    // 按键按下\n}"
                        ),
                        createFunction(
                            "HAL_GPIO_WritePin",
                            "设置指定 GPIO 输出引脚为高电平或低电平。",
                            "void HAL_GPIO_WritePin(GPIO_TypeDef *GPIOx, uint16_t GPIO_Pin, GPIO_PinState PinState);",
                            [
                                { name: "GPIOx", description: "GPIO 端口。" },
                                { name: "GPIO_Pin", description: "一个或多个待写入引脚。" },
                                { name: "PinState", description: "GPIO_PIN_SET 或 GPIO_PIN_RESET。" }
                            ],
                            "无。",
                            "函数通过置位/复位寄存器写入，可一次修改多个引脚。引脚必须先配置为合适的输出模式。",
                            "HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_SET);"
                        ),
                        createFunction(
                            "HAL_GPIO_TogglePin",
                            "翻转指定 GPIO 输出引脚的电平。",
                            "void HAL_GPIO_TogglePin(GPIO_TypeDef *GPIOx, uint16_t GPIO_Pin);",
                            [
                                { name: "GPIOx", description: "GPIO 端口。" },
                                { name: "GPIO_Pin", description: "一个或多个待翻转引脚。" }
                            ],
                            "无。",
                            "适合 LED 等低频控制。并发修改同一端口时，应检查读改写是否符合实时要求。",
                            "HAL_GPIO_TogglePin(GPIOA, GPIO_PIN_5);"
                        ),
                        createFunction(
                            "HAL_GPIO_EXTI_IRQHandler",
                            "处理指定 GPIO 外部中断线，并触发 HAL 回调。",
                            "void HAL_GPIO_EXTI_IRQHandler(uint16_t GPIO_Pin);",
                            [
                                { name: "GPIO_Pin", description: "产生中断的 GPIO_PIN_x。" }
                            ],
                            "无。",
                            "通常在对应 EXTI 中断服务函数中调用。用户逻辑一般放在 HAL_GPIO_EXTI_Callback()。",
                            "void EXTI15_10_IRQHandler(void)\n{\n    HAL_GPIO_EXTI_IRQHandler(GPIO_PIN_13);\n}"
                        )
                    ]
                },
                {
                    id: "dma",
                    name: "DMA",
                    description: "直接存储器访问：启动传输、中止传输与中断处理。",
                    functions: [
                        createFunction(
                            "HAL_DMA_Start_IT",
                            "以中断方式启动一次 DMA 传输。",
                            "HAL_StatusTypeDef HAL_DMA_Start_IT(DMA_HandleTypeDef *hdma, uint32_t SrcAddress, uint32_t DstAddress, uint32_t DataLength);",
                            [
                                { name: "hdma", description: "DMA 句柄。" },
                                { name: "SrcAddress", description: "源地址。" },
                                { name: "DstAddress", description: "目标地址。" },
                                { name: "DataLength", description: "传输数据项数量，不一定等于字节数。" }
                            ],
                            commonStatusReturn,
                            "数据项宽度由 DMA 初始化配置决定。缓存一致性要求取决于内核和芯片型号。",
                            "HAL_DMA_Start_IT(&hdma1_ch1,\n+    (uint32_t)source,\n+    (uint32_t)target,\n+    64);"
                        ),
                        createFunction(
                            "HAL_DMA_Abort",
                            "阻塞式中止当前 DMA 传输。",
                            "HAL_StatusTypeDef HAL_DMA_Abort(DMA_HandleTypeDef *hdma);",
                            [{ name: "hdma", description: "DMA 句柄。" }],
                            commonStatusReturn,
                            "中止由外设触发的 DMA 前，通常还需先停止对应外设的 DMA 请求。",
                            "HAL_DMA_Abort(&hdma1_ch1);"
                        ),
                        createFunction(
                            "HAL_DMA_IRQHandler",
                            "处理 DMA 中断标志并调用完成或错误回调。",
                            "void HAL_DMA_IRQHandler(DMA_HandleTypeDef *hdma);",
                            [{ name: "hdma", description: "与该中断通道对应的 DMA 句柄。" }],
                            "无。",
                            "应从正确的 DMA 通道或数据流中断服务函数调用。",
                            "void DMA1_Channel1_IRQHandler(void)\n{\n    HAL_DMA_IRQHandler(&hdma1_ch1);\n}"
                        )
                    ]
                },
                {
                    id: "nvic",
                    name: "NVIC",
                    description: "中断控制：优先级设置、使能与关闭。",
                    functions: [
                        createFunction(
                            "HAL_NVIC_SetPriority",
                            "设置外设中断的抢占优先级和子优先级。",
                            "void HAL_NVIC_SetPriority(IRQn_Type IRQn, uint32_t PreemptPriority, uint32_t SubPriority);",
                            [
                                { name: "IRQn", description: "中断号，例如 USART1_IRQn。" },
                                { name: "PreemptPriority", description: "抢占优先级。" },
                                { name: "SubPriority", description: "子优先级。" }
                            ],
                            "无。",
                            "可用优先级位数由内核实现和优先级分组决定。数值越小通常优先级越高。",
                            "HAL_NVIC_SetPriority(USART1_IRQn, 2, 0);"
                        ),
                        createFunction(
                            "HAL_NVIC_EnableIRQ",
                            "使能指定外设中断。",
                            "void HAL_NVIC_EnableIRQ(IRQn_Type IRQn);",
                            [{ name: "IRQn", description: "待使能的中断号。" }],
                            "无。",
                            "通常应先设置优先级，再使能中断。",
                            "HAL_NVIC_EnableIRQ(USART1_IRQn);"
                        ),
                        createFunction(
                            "HAL_NVIC_DisableIRQ",
                            "关闭指定外设中断。",
                            "void HAL_NVIC_DisableIRQ(IRQn_Type IRQn);",
                            [{ name: "IRQn", description: "待关闭的中断号。" }],
                            "无。",
                            "关闭 NVIC 通道不会自动清除外设内部的中断标志。",
                            "HAL_NVIC_DisableIRQ(USART1_IRQn);"
                        )
                    ]
                },
                {
                    id: "rcc",
                    name: "RCC",
                    description: "复位与时钟控制：振荡器、总线时钟和频率查询。",
                    functions: [
                        createFunction(
                            "HAL_RCC_OscConfig",
                            "配置 HSE、HSI、LSE、LSI、PLL 等振荡器资源。",
                            "HAL_StatusTypeDef HAL_RCC_OscConfig(RCC_OscInitTypeDef *RCC_OscInitStruct);",
                            [{ name: "RCC_OscInitStruct", description: "振荡器及 PLL 配置结构体。" }],
                            commonStatusReturn,
                            "不同系列的结构体成员和 PLL 参数差异较大。建议由 CubeMX 生成基础配置。",
                            "HAL_StatusTypeDef status;\nstatus = HAL_RCC_OscConfig(&rcc_osc_init);"
                        ),
                        createFunction(
                            "HAL_RCC_ClockConfig",
                            "选择系统时钟源并配置 AHB、APB 分频。",
                            "HAL_StatusTypeDef HAL_RCC_ClockConfig(RCC_ClkInitTypeDef *RCC_ClkInitStruct, uint32_t FLatency);",
                            [
                                { name: "RCC_ClkInitStruct", description: "系统和总线时钟配置。" },
                                { name: "FLatency", description: "Flash 等待周期。" }
                            ],
                            commonStatusReturn,
                            "Flash 等待周期必须与目标频率和供电电压匹配。具体取值以数据手册为准。",
                            "HAL_RCC_ClockConfig(&rcc_clk_init, FLASH_LATENCY_4);"
                        ),
                        createFunction(
                            "HAL_RCC_GetSysClockFreq",
                            "返回当前系统时钟 SYSCLK 的估算频率。",
                            "uint32_t HAL_RCC_GetSysClockFreq(void);",
                            [],
                            "SYSCLK 频率，单位 Hz。",
                            "返回值依据 RCC 配置计算，不会测量真实晶振误差。",
                            "uint32_t sysclk_hz = HAL_RCC_GetSysClockFreq();"
                        )
                    ]
                }
            ]
        },
        {
            id: "analog",
            name: "Analog",
            modules: [
                {
                    id: "adc",
                    name: "ADC",
                    description: "模数转换：轮询、中断和 DMA 三种常见采样方式。",
                    functions: [
                        createFunction(
                            "HAL_ADC_Start",
                            "启动 ADC 常规组转换。",
                            "HAL_StatusTypeDef HAL_ADC_Start(ADC_HandleTypeDef *hadc);",
                            [{ name: "hadc", description: "ADC 句柄。" }],
                            commonStatusReturn,
                            "启动后可轮询转换完成，再读取结果。连续模式下停止条件不同。",
                            "HAL_ADC_Start(&hadc1);"
                        ),
                        createFunction(
                            "HAL_ADC_PollForConversion",
                            "阻塞等待 ADC 常规组转换完成。",
                            "HAL_StatusTypeDef HAL_ADC_PollForConversion(ADC_HandleTypeDef *hadc, uint32_t Timeout);",
                            [
                                { name: "hadc", description: "ADC 句柄。" },
                                { name: "Timeout", description: "最大等待时间。" }
                            ],
                            "HAL_OK、HAL_ERROR 或 HAL_TIMEOUT。",
                            timeoutNote,
                            "if (HAL_ADC_PollForConversion(&hadc1, 10) == HAL_OK) {\n    adc_value = HAL_ADC_GetValue(&hadc1);\n}"
                        ),
                        createFunction(
                            "HAL_ADC_GetValue",
                            "读取最近一次 ADC 常规转换结果。",
                            "uint32_t HAL_ADC_GetValue(ADC_HandleTypeDef *hadc);",
                            [{ name: "hadc", description: "ADC 句柄。" }],
                            "ADC 转换原始值。",
                            "原始值对应的电压范围与分辨率、参考电压、校准和输入配置有关。",
                            "uint32_t adc_value = HAL_ADC_GetValue(&hadc1);"
                        ),
                        createFunction(
                            "HAL_ADC_Start_IT",
                            "以中断方式启动 ADC 常规组转换。",
                            "HAL_StatusTypeDef HAL_ADC_Start_IT(ADC_HandleTypeDef *hadc);",
                            [{ name: "hadc", description: "ADC 句柄。" }],
                            commonStatusReturn,
                            "转换完成后执行 HAL_ADC_ConvCpltCallback()。不要在高频回调里执行阻塞打印。",
                            "HAL_ADC_Start_IT(&hadc1);"
                        ),
                        createFunction(
                            "HAL_ADC_Start_DMA",
                            "以 DMA 方式启动 ADC 常规组转换。",
                            "HAL_StatusTypeDef HAL_ADC_Start_DMA(ADC_HandleTypeDef *hadc, uint32_t *pData, uint32_t Length);",
                            [
                                { name: "hadc", description: "ADC 句柄。" },
                                { name: "pData", description: "接收缓冲区。" },
                                { name: "Length", description: "转换数据项数量。" }
                            ],
                            commonStatusReturn,
                            "缓冲区类型、数据对齐和缓存一致性必须与当前芯片及 DMA 配置匹配。",
                            "uint32_t adc_buffer[32];\nHAL_ADC_Start_DMA(&hadc1, adc_buffer, 32);"
                        ),
                        createFunction(
                            "HAL_ADC_Stop",
                            "停止 ADC 常规组转换。",
                            "HAL_StatusTypeDef HAL_ADC_Stop(ADC_HandleTypeDef *hadc);",
                            [{ name: "hadc", description: "ADC 句柄。" }],
                            commonStatusReturn,
                            "若以中断或 DMA 方式启动，应优先调用对应的 Stop_IT 或 Stop_DMA 接口。",
                            "HAL_ADC_Stop(&hadc1);"
                        )
                    ]
                },
                {
                    id: "dac",
                    name: "DAC",
                    description: "数模转换：设置输出值并控制通道启停。",
                    functions: [
                        createFunction(
                            "HAL_DAC_Start",
                            "启动指定 DAC 通道。",
                            "HAL_StatusTypeDef HAL_DAC_Start(DAC_HandleTypeDef *hdac, uint32_t Channel);",
                            [
                                { name: "hdac", description: "DAC 句柄。" },
                                { name: "Channel", description: "DAC_CHANNEL_1 或支持的其他通道。" }
                            ],
                            commonStatusReturn,
                            "并非所有 STM32 型号都包含 DAC；通道数量也随型号变化。",
                            "HAL_DAC_Start(&hdac1, DAC_CHANNEL_1);"
                        ),
                        createFunction(
                            "HAL_DAC_SetValue",
                            "设置指定 DAC 通道的数字量。",
                            "HAL_StatusTypeDef HAL_DAC_SetValue(DAC_HandleTypeDef *hdac, uint32_t Channel, uint32_t Alignment, uint32_t Data);",
                            [
                                { name: "hdac", description: "DAC 句柄。" },
                                { name: "Channel", description: "目标 DAC 通道。" },
                                { name: "Alignment", description: "数据对齐方式。" },
                                { name: "Data", description: "待转换数字量。" }
                            ],
                            commonStatusReturn,
                            "Data 有效范围由分辨率和对齐方式决定。",
                            "HAL_DAC_SetValue(&hdac1, DAC_CHANNEL_1, DAC_ALIGN_12B_R, 2048);"
                        ),
                        createFunction(
                            "HAL_DAC_Stop",
                            "停止指定 DAC 通道。",
                            "HAL_StatusTypeDef HAL_DAC_Stop(DAC_HandleTypeDef *hdac, uint32_t Channel);",
                            [
                                { name: "hdac", description: "DAC 句柄。" },
                                { name: "Channel", description: "目标 DAC 通道。" }
                            ],
                            commonStatusReturn,
                            "停止后引脚电气状态取决于具体芯片 DAC 实现与 GPIO 配置。",
                            "HAL_DAC_Stop(&hdac1, DAC_CHANNEL_1);"
                        )
                    ]
                }
            ]
        },
        {
            id: "timers",
            name: "Timers",
            modules: [
                {
                    id: "tim",
                    name: "TIM",
                    description: "定时器：基本计时、PWM、输入捕获与编码器模式。",
                    functions: [
                        createFunction(
                            "HAL_TIM_Base_Start",
                            "启动定时器基本计数。",
                            "HAL_StatusTypeDef HAL_TIM_Base_Start(TIM_HandleTypeDef *htim);",
                            [{ name: "htim", description: "定时器句柄。" }],
                            commonStatusReturn,
                            "仅启动计数，不会自动使能更新中断。",
                            "HAL_TIM_Base_Start(&htim6);"
                        ),
                        createFunction(
                            "HAL_TIM_Base_Start_IT",
                            "启动定时器基本计数并使能更新中断。",
                            "HAL_StatusTypeDef HAL_TIM_Base_Start_IT(TIM_HandleTypeDef *htim);",
                            [{ name: "htim", description: "定时器句柄。" }],
                            commonStatusReturn,
                            "周期回调为 HAL_TIM_PeriodElapsedCallback()。中断频率由计数时钟、PSC 和 ARR 共同决定。",
                            "HAL_TIM_Base_Start_IT(&htim6);"
                        ),
                        createFunction(
                            "HAL_TIM_PWM_Start",
                            "启动指定定时器通道的 PWM 输出。",
                            "HAL_StatusTypeDef HAL_TIM_PWM_Start(TIM_HandleTypeDef *htim, uint32_t Channel);",
                            [
                                { name: "htim", description: "定时器句柄。" },
                                { name: "Channel", description: "TIM_CHANNEL_1 等通道。" }
                            ],
                            commonStatusReturn,
                            "PWM 频率由 PSC 和 ARR 决定，占空比通常由 CCR 决定。高级定时器还涉及主输出和死区配置。",
                            "HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1);"
                        ),
                        createFunction(
                            "HAL_TIM_PWM_Stop",
                            "停止指定定时器通道的 PWM 输出。",
                            "HAL_StatusTypeDef HAL_TIM_PWM_Stop(TIM_HandleTypeDef *htim, uint32_t Channel);",
                            [
                                { name: "htim", description: "定时器句柄。" },
                                { name: "Channel", description: "待停止的 PWM 通道。" }
                            ],
                            commonStatusReturn,
                            "电机驱动场景还应结合驱动使能、刹车和故障输入设计安全关断。",
                            "HAL_TIM_PWM_Stop(&htim1, TIM_CHANNEL_1);"
                        ),
                        createFunction(
                            "HAL_TIM_IC_Start_IT",
                            "以中断方式启动指定通道的输入捕获。",
                            "HAL_StatusTypeDef HAL_TIM_IC_Start_IT(TIM_HandleTypeDef *htim, uint32_t Channel);",
                            [
                                { name: "htim", description: "定时器句柄。" },
                                { name: "Channel", description: "输入捕获通道。" }
                            ],
                            commonStatusReturn,
                            "捕获事件回调为 HAL_TIM_IC_CaptureCallback()。溢出处理会影响长周期测量。",
                            "HAL_TIM_IC_Start_IT(&htim2, TIM_CHANNEL_1);"
                        ),
                        createFunction(
                            "HAL_TIM_Encoder_Start",
                            "启动定时器编码器接口。",
                            "HAL_StatusTypeDef HAL_TIM_Encoder_Start(TIM_HandleTypeDef *htim, uint32_t Channel);",
                            [
                                { name: "htim", description: "定时器句柄。" },
                                { name: "Channel", description: "TIM_CHANNEL_ALL 或指定通道。" }
                            ],
                            commonStatusReturn,
                            "需要先配置编码器模式、输入极性与滤波。读取计数值时应考虑溢出和方向。",
                            "HAL_TIM_Encoder_Start(&htim3, TIM_CHANNEL_ALL);"
                        )
                    ]
                }
            ]
        },
        {
            id: "connectivity",
            name: "Connectivity",
            modules: [
                {
                    id: "uart",
                    name: "UART",
                    description: "串口通信：阻塞、中断与 DMA 收发。",
                    functions: [
                        createFunction(
                            "HAL_UART_Transmit",
                            "阻塞发送指定字节数的数据。",
                            "HAL_StatusTypeDef HAL_UART_Transmit(UART_HandleTypeDef *huart, const uint8_t *pData, uint16_t Size, uint32_t Timeout);",
                            [
                                { name: "huart", description: "UART 句柄。" },
                                { name: "pData", description: "发送缓冲区。" },
                                { name: "Size", description: "发送字节数。" },
                                { name: "Timeout", description: "最大阻塞等待时间。" }
                            ],
                            "HAL_OK、HAL_ERROR、HAL_BUSY 或 HAL_TIMEOUT。",
                            "Size 的单位是字节。不要在高频中断或实时控制环中使用长时间阻塞发送。",
                            "const uint8_t text[] = \"OK\\r\\n\";\nHAL_UART_Transmit(&huart1, text, sizeof(text) - 1, 100);"
                        ),
                        createFunction(
                            "HAL_UART_Receive",
                            "阻塞接收指定字节数的数据。",
                            "HAL_StatusTypeDef HAL_UART_Receive(UART_HandleTypeDef *huart, uint8_t *pData, uint16_t Size, uint32_t Timeout);",
                            [
                                { name: "huart", description: "UART 句柄。" },
                                { name: "pData", description: "接收缓冲区。" },
                                { name: "Size", description: "期望接收字节数。" },
                                { name: "Timeout", description: "最大阻塞等待时间。" }
                            ],
                            "HAL_OK、HAL_ERROR、HAL_BUSY 或 HAL_TIMEOUT。",
                            timeoutNote,
                            "uint8_t rx_byte;\nHAL_UART_Receive(&huart1, &rx_byte, 1, 100);"
                        ),
                        createFunction(
                            "HAL_UART_Transmit_IT",
                            "以中断方式启动串口发送。",
                            "HAL_StatusTypeDef HAL_UART_Transmit_IT(UART_HandleTypeDef *huart, const uint8_t *pData, uint16_t Size);",
                            [
                                { name: "huart", description: "UART 句柄。" },
                                { name: "pData", description: "发送缓冲区。" },
                                { name: "Size", description: "发送字节数。" }
                            ],
                            commonStatusReturn,
                            "函数返回后缓冲区仍会被中断使用，直到 HAL_UART_TxCpltCallback() 执行。缓冲区不能是很快失效的局部变量。",
                            "static uint8_t tx_buffer[] = {0x01, 0x02};\nHAL_UART_Transmit_IT(&huart1, tx_buffer, sizeof(tx_buffer));"
                        ),
                        createFunction(
                            "HAL_UART_Receive_IT",
                            "以中断方式启动定长串口接收。",
                            "HAL_StatusTypeDef HAL_UART_Receive_IT(UART_HandleTypeDef *huart, uint8_t *pData, uint16_t Size);",
                            [
                                { name: "huart", description: "UART 句柄。" },
                                { name: "pData", description: "接收缓冲区。" },
                                { name: "Size", description: "期望接收字节数。" }
                            ],
                            commonStatusReturn,
                            "完成回调为 HAL_UART_RxCpltCallback()。处理连续数据时，应及时重新启动接收或使用空闲线方案。",
                            "static uint8_t rx_buffer[8];\nHAL_UART_Receive_IT(&huart1, rx_buffer, sizeof(rx_buffer));"
                        ),
                        createFunction(
                            "HAL_UART_Transmit_DMA",
                            "以 DMA 方式启动串口发送。",
                            "HAL_StatusTypeDef HAL_UART_Transmit_DMA(UART_HandleTypeDef *huart, const uint8_t *pData, uint16_t Size);",
                            [
                                { name: "huart", description: "UART 句柄。" },
                                { name: "pData", description: "发送缓冲区。" },
                                { name: "Size", description: "发送字节数。" }
                            ],
                            commonStatusReturn,
                            "DMA 完成前不得修改或释放发送缓冲区。必须处理 HAL_BUSY，不能假定每次调用都会成功启动。",
                            "if (HAL_UART_Transmit_DMA(&huart1, tx_buffer, tx_length) == HAL_OK) {\n    tx_busy = 1;\n}"
                        ),
                        createFunction(
                            "HAL_UART_Receive_DMA",
                            "以 DMA 方式启动定长串口接收。",
                            "HAL_StatusTypeDef HAL_UART_Receive_DMA(UART_HandleTypeDef *huart, uint8_t *pData, uint16_t Size);",
                            [
                                { name: "huart", description: "UART 句柄。" },
                                { name: "pData", description: "接收缓冲区。" },
                                { name: "Size", description: "期望接收字节数。" }
                            ],
                            commonStatusReturn,
                            "变长帧常结合空闲线检测使用。不同 HAL 版本可能提供 ReceiveToIdle 系列接口。",
                            "HAL_UART_Receive_DMA(&huart1, rx_buffer, sizeof(rx_buffer));"
                        )
                    ]
                },
                {
                    id: "i2c",
                    name: "I2C",
                    description: "I²C 主机通信：设备收发、寄存器读写和设备探测。",
                    functions: [
                        createFunction(
                            "HAL_I2C_Master_Transmit",
                            "主机模式阻塞发送数据。",
                            "HAL_StatusTypeDef HAL_I2C_Master_Transmit(I2C_HandleTypeDef *hi2c, uint16_t DevAddress, const uint8_t *pData, uint16_t Size, uint32_t Timeout);",
                            [
                                { name: "hi2c", description: "I2C 句柄。" },
                                { name: "DevAddress", description: "设备地址，传入格式应遵循当前 HAL 的地址约定。" },
                                { name: "pData", description: "发送缓冲区。" },
                                { name: "Size", description: "发送字节数。" },
                                { name: "Timeout", description: "最大等待时间。" }
                            ],
                            "HAL_OK、HAL_ERROR、HAL_BUSY 或 HAL_TIMEOUT。",
                            "STM32 HAL 常见写法是把 7 位地址左移 1 位传入。请以当前系列头文件说明和现有工程写法为准。",
                            "HAL_I2C_Master_Transmit(&hi2c1, 0x68 << 1, data, 2, 100);"
                        ),
                        createFunction(
                            "HAL_I2C_Master_Receive",
                            "主机模式阻塞接收数据。",
                            "HAL_StatusTypeDef HAL_I2C_Master_Receive(I2C_HandleTypeDef *hi2c, uint16_t DevAddress, uint8_t *pData, uint16_t Size, uint32_t Timeout);",
                            [
                                { name: "hi2c", description: "I2C 句柄。" },
                                { name: "DevAddress", description: "设备地址。" },
                                { name: "pData", description: "接收缓冲区。" },
                                { name: "Size", description: "接收字节数。" },
                                { name: "Timeout", description: "最大等待时间。" }
                            ],
                            "HAL_OK、HAL_ERROR、HAL_BUSY 或 HAL_TIMEOUT。",
                            timeoutNote,
                            "HAL_I2C_Master_Receive(&hi2c1, 0x68 << 1, data, 6, 100);"
                        ),
                        createFunction(
                            "HAL_I2C_Mem_Write",
                            "向 I²C 设备内部寄存器或存储地址写入数据。",
                            "HAL_StatusTypeDef HAL_I2C_Mem_Write(I2C_HandleTypeDef *hi2c, uint16_t DevAddress, uint16_t MemAddress, uint16_t MemAddSize, const uint8_t *pData, uint16_t Size, uint32_t Timeout);",
                            [
                                { name: "hi2c", description: "I2C 句柄。" },
                                { name: "DevAddress", description: "设备地址。" },
                                { name: "MemAddress", description: "设备内部地址。" },
                                { name: "MemAddSize", description: "8 位或 16 位内部地址格式。" },
                                { name: "pData", description: "发送缓冲区。" },
                                { name: "Size", description: "发送字节数。" },
                                { name: "Timeout", description: "最大等待时间。" }
                            ],
                            "HAL_OK、HAL_ERROR、HAL_BUSY 或 HAL_TIMEOUT。",
                            "外部 EEPROM 还可能需要遵守页写入边界和内部写周期。",
                            "HAL_I2C_Mem_Write(&hi2c1, dev_addr, 0x20, I2C_MEMADD_SIZE_8BIT, data, 2, 100);"
                        ),
                        createFunction(
                            "HAL_I2C_Mem_Read",
                            "从 I²C 设备内部寄存器或存储地址读取数据。",
                            "HAL_StatusTypeDef HAL_I2C_Mem_Read(I2C_HandleTypeDef *hi2c, uint16_t DevAddress, uint16_t MemAddress, uint16_t MemAddSize, uint8_t *pData, uint16_t Size, uint32_t Timeout);",
                            [
                                { name: "hi2c", description: "I2C 句柄。" },
                                { name: "DevAddress", description: "设备地址。" },
                                { name: "MemAddress", description: "设备内部地址。" },
                                { name: "MemAddSize", description: "8 位或 16 位内部地址格式。" },
                                { name: "pData", description: "接收缓冲区。" },
                                { name: "Size", description: "读取字节数。" },
                                { name: "Timeout", description: "最大等待时间。" }
                            ],
                            "HAL_OK、HAL_ERROR、HAL_BUSY 或 HAL_TIMEOUT。",
                            "是否适合该接口取决于从设备的寄存器访问时序。",
                            "HAL_I2C_Mem_Read(&hi2c1, dev_addr, 0x75, I2C_MEMADD_SIZE_8BIT, &who_am_i, 1, 100);"
                        ),
                        createFunction(
                            "HAL_I2C_IsDeviceReady",
                            "尝试寻址设备，检查其是否应答。",
                            "HAL_StatusTypeDef HAL_I2C_IsDeviceReady(I2C_HandleTypeDef *hi2c, uint16_t DevAddress, uint32_t Trials, uint32_t Timeout);",
                            [
                                { name: "hi2c", description: "I2C 句柄。" },
                                { name: "DevAddress", description: "目标设备地址。" },
                                { name: "Trials", description: "尝试次数。" },
                                { name: "Timeout", description: "单次等待上限。" }
                            ],
                            "HAL_OK 表示设备应答，其余状态表示未成功。",
                            "适合上电探测和 EEPROM 写周期轮询，不代表后续数据通信一定正确。",
                            "if (HAL_I2C_IsDeviceReady(&hi2c1, dev_addr, 3, 20) == HAL_OK) {\n    device_online = 1;\n}"
                        )
                    ]
                },
                {
                    id: "spi",
                    name: "SPI",
                    description: "SPI 全双工通信：发送、接收和同步收发。",
                    functions: [
                        createFunction(
                            "HAL_SPI_Transmit",
                            "阻塞发送指定数量的 SPI 数据。",
                            "HAL_StatusTypeDef HAL_SPI_Transmit(SPI_HandleTypeDef *hspi, const uint8_t *pData, uint16_t Size, uint32_t Timeout);",
                            [
                                { name: "hspi", description: "SPI 句柄。" },
                                { name: "pData", description: "发送缓冲区。" },
                                { name: "Size", description: "发送数据项数量。" },
                                { name: "Timeout", description: "最大等待时间。" }
                            ],
                            "HAL_OK、HAL_ERROR、HAL_BUSY 或 HAL_TIMEOUT。",
                            "Size 的实际含义与 SPI 数据宽度配置有关。片选通常由 GPIO 手动控制。",
                            "HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_RESET);\nHAL_SPI_Transmit(&hspi1, data, length, 100);\nHAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_SET);"
                        ),
                        createFunction(
                            "HAL_SPI_Receive",
                            "阻塞接收指定数量的 SPI 数据。",
                            "HAL_StatusTypeDef HAL_SPI_Receive(SPI_HandleTypeDef *hspi, uint8_t *pData, uint16_t Size, uint32_t Timeout);",
                            [
                                { name: "hspi", description: "SPI 句柄。" },
                                { name: "pData", description: "接收缓冲区。" },
                                { name: "Size", description: "接收数据项数量。" },
                                { name: "Timeout", description: "最大等待时间。" }
                            ],
                            "HAL_OK、HAL_ERROR、HAL_BUSY 或 HAL_TIMEOUT。",
                            "主机接收数据时仍需产生时钟。HAL 会根据配置处理所需的发送过程。",
                            "HAL_SPI_Receive(&hspi1, rx_data, 4, 100);"
                        ),
                        createFunction(
                            "HAL_SPI_TransmitReceive",
                            "阻塞完成 SPI 全双工同步收发。",
                            "HAL_StatusTypeDef HAL_SPI_TransmitReceive(SPI_HandleTypeDef *hspi, const uint8_t *pTxData, uint8_t *pRxData, uint16_t Size, uint32_t Timeout);",
                            [
                                { name: "hspi", description: "SPI 句柄。" },
                                { name: "pTxData", description: "发送缓冲区。" },
                                { name: "pRxData", description: "接收缓冲区。" },
                                { name: "Size", description: "同步交换的数据项数量。" },
                                { name: "Timeout", description: "最大等待时间。" }
                            ],
                            "HAL_OK、HAL_ERROR、HAL_BUSY 或 HAL_TIMEOUT。",
                            "适合寄存器读写和全双工外设。确保发送、接收缓冲区长度均满足 Size。",
                            "HAL_SPI_TransmitReceive(&hspi1, tx_data, rx_data, 2, 100);"
                        ),
                        createFunction(
                            "HAL_SPI_TransmitReceive_DMA",
                            "以 DMA 方式启动 SPI 全双工同步收发。",
                            "HAL_StatusTypeDef HAL_SPI_TransmitReceive_DMA(SPI_HandleTypeDef *hspi, const uint8_t *pTxData, uint8_t *pRxData, uint16_t Size);",
                            [
                                { name: "hspi", description: "SPI 句柄。" },
                                { name: "pTxData", description: "发送缓冲区。" },
                                { name: "pRxData", description: "接收缓冲区。" },
                                { name: "Size", description: "交换的数据项数量。" }
                            ],
                            commonStatusReturn,
                            "完成前缓冲区必须持续有效。完成回调后再释放片选更可靠。",
                            "HAL_SPI_TransmitReceive_DMA(&hspi1, tx_data, rx_data, length);"
                        )
                    ]
                },
                {
                    id: "can",
                    name: "CAN",
                    description: "经典 bxCAN：启动、发送、接收与中断通知，主要用于 F1/F4。",
                    functions: [
                        createFunction(
                            "HAL_CAN_Start",
                            "启动经典 CAN 外设。",
                            "HAL_StatusTypeDef HAL_CAN_Start(CAN_HandleTypeDef *hcan);",
                            [{ name: "hcan", description: "CAN 句柄。" }],
                            commonStatusReturn,
                            "启动前应完成位时序和过滤器配置。G4 通常使用 FDCAN 驱动接口。",
                            "HAL_CAN_Start(&hcan1);",
                            ["F1", "F4"]
                        ),
                        createFunction(
                            "HAL_CAN_AddTxMessage",
                            "把一帧经典 CAN 报文加入发送邮箱。",
                            "HAL_StatusTypeDef HAL_CAN_AddTxMessage(CAN_HandleTypeDef *hcan, const CAN_TxHeaderTypeDef *pHeader, const uint8_t aData[], uint32_t *pTxMailbox);",
                            [
                                { name: "hcan", description: "CAN 句柄。" },
                                { name: "pHeader", description: "标识符、帧类型和数据长度等。" },
                                { name: "aData", description: "最多 8 字节数据。" },
                                { name: "pTxMailbox", description: "返回所用发送邮箱。" }
                            ],
                            commonStatusReturn,
                            "应检查空闲邮箱和总线错误状态。经典 CAN 单帧数据长度上限为 8 字节。",
                            "HAL_CAN_AddTxMessage(&hcan1, &tx_header, tx_data, &tx_mailbox);",
                            ["F1", "F4"]
                        ),
                        createFunction(
                            "HAL_CAN_GetRxMessage",
                            "从指定接收 FIFO 取出一帧经典 CAN 报文。",
                            "HAL_StatusTypeDef HAL_CAN_GetRxMessage(CAN_HandleTypeDef *hcan, uint32_t RxFifo, CAN_RxHeaderTypeDef *pHeader, uint8_t aData[]);",
                            [
                                { name: "hcan", description: "CAN 句柄。" },
                                { name: "RxFifo", description: "CAN_RX_FIFO0 或 CAN_RX_FIFO1。" },
                                { name: "pHeader", description: "接收帧头输出。" },
                                { name: "aData", description: "接收数据缓冲区。" }
                            ],
                            commonStatusReturn,
                            "通常在接收 FIFO 挂起回调中读取，避免 FIFO 溢出。",
                            "HAL_CAN_GetRxMessage(&hcan1, CAN_RX_FIFO0, &rx_header, rx_data);",
                            ["F1", "F4"]
                        ),
                        createFunction(
                            "HAL_CAN_ActivateNotification",
                            "使能经典 CAN 的指定中断通知。",
                            "HAL_StatusTypeDef HAL_CAN_ActivateNotification(CAN_HandleTypeDef *hcan, uint32_t ActiveITs);",
                            [
                                { name: "hcan", description: "CAN 句柄。" },
                                { name: "ActiveITs", description: "CAN_IT_* 通知位组合。" }
                            ],
                            commonStatusReturn,
                            "还必须正确配置 NVIC 中断。回调名称取决于启用的通知类型。",
                            "HAL_CAN_ActivateNotification(&hcan1, CAN_IT_RX_FIFO0_MSG_PENDING);",
                            ["F1", "F4"]
                        )
                    ]
                },
                {
                    id: "fdcan",
                    name: "FDCAN",
                    description: "FDCAN：支持经典 CAN 与 CAN FD，G4 常见。",
                    functions: [
                        createFunction(
                            "HAL_FDCAN_Start",
                            "启动 FDCAN 外设。",
                            "HAL_StatusTypeDef HAL_FDCAN_Start(FDCAN_HandleTypeDef *hfdcan);",
                            [{ name: "hfdcan", description: "FDCAN 句柄。" }],
                            commonStatusReturn,
                            "启动前应完成消息 RAM、过滤器和位时序配置。",
                            "HAL_FDCAN_Start(&hfdcan1);",
                            ["G4"]
                        ),
                        createFunction(
                            "HAL_FDCAN_AddMessageToTxFifoQ",
                            "把一帧报文加入 FDCAN 发送 FIFO 或队列。",
                            "HAL_StatusTypeDef HAL_FDCAN_AddMessageToTxFifoQ(FDCAN_HandleTypeDef *hfdcan, const FDCAN_TxHeaderTypeDef *pTxHeader, const uint8_t *pTxData);",
                            [
                                { name: "hfdcan", description: "FDCAN 句柄。" },
                                { name: "pTxHeader", description: "标识符、帧格式、数据长度等。" },
                                { name: "pTxData", description: "发送数据缓冲区。" }
                            ],
                            commonStatusReturn,
                            "CAN FD 的长度编码不是直接字节数，必须正确设置 DataLength。",
                            "HAL_FDCAN_AddMessageToTxFifoQ(&hfdcan1, &tx_header, tx_data);",
                            ["G4"]
                        ),
                        createFunction(
                            "HAL_FDCAN_GetRxMessage",
                            "从指定 FDCAN 接收 FIFO 读取一帧报文。",
                            "HAL_StatusTypeDef HAL_FDCAN_GetRxMessage(FDCAN_HandleTypeDef *hfdcan, uint32_t RxLocation, FDCAN_RxHeaderTypeDef *pRxHeader, uint8_t *pRxData);",
                            [
                                { name: "hfdcan", description: "FDCAN 句柄。" },
                                { name: "RxLocation", description: "接收 FIFO 或缓冲区位置。" },
                                { name: "pRxHeader", description: "接收帧头输出。" },
                                { name: "pRxData", description: "接收数据缓冲区。" }
                            ],
                            commonStatusReturn,
                            "接收缓冲区必须能容纳配置允许的最大数据长度。",
                            "HAL_FDCAN_GetRxMessage(&hfdcan1, FDCAN_RX_FIFO0, &rx_header, rx_data);",
                            ["G4"]
                        ),
                        createFunction(
                            "HAL_FDCAN_ActivateNotification",
                            "使能 FDCAN 的指定中断通知。",
                            "HAL_StatusTypeDef HAL_FDCAN_ActivateNotification(FDCAN_HandleTypeDef *hfdcan, uint32_t ActiveITs, uint32_t BufferIndexes);",
                            [
                                { name: "hfdcan", description: "FDCAN 句柄。" },
                                { name: "ActiveITs", description: "FDCAN_IT_* 通知位组合。" },
                                { name: "BufferIndexes", description: "专用接收缓冲区索引位图；不用时通常传 0。" }
                            ],
                            commonStatusReturn,
                            "通知、中断线映射和 NVIC 都必须正确配置。",
                            "HAL_FDCAN_ActivateNotification(&hfdcan1, FDCAN_IT_RX_FIFO0_NEW_MESSAGE, 0);",
                            ["G4"]
                        )
                    ]
                }
            ]
        },
        {
            id: "watchdog-time",
            name: "Watchdog & Time",
            modules: [
                {
                    id: "rtc",
                    name: "RTC",
                    description: "实时时钟：日期与时间的设置和读取。",
                    functions: [
                        createFunction(
                            "HAL_RTC_SetTime",
                            "设置 RTC 时间。",
                            "HAL_StatusTypeDef HAL_RTC_SetTime(RTC_HandleTypeDef *hrtc, RTC_TimeTypeDef *sTime, uint32_t Format);",
                            [
                                { name: "hrtc", description: "RTC 句柄。" },
                                { name: "sTime", description: "小时、分钟、秒等时间数据。" },
                                { name: "Format", description: "RTC_FORMAT_BIN 或 RTC_FORMAT_BCD。" }
                            ],
                            commonStatusReturn,
                            "输入数据格式必须与 Format 一致。",
                            "HAL_RTC_SetTime(&hrtc, &time, RTC_FORMAT_BIN);"
                        ),
                        createFunction(
                            "HAL_RTC_GetTime",
                            "读取 RTC 当前时间。",
                            "HAL_StatusTypeDef HAL_RTC_GetTime(RTC_HandleTypeDef *hrtc, RTC_TimeTypeDef *sTime, uint32_t Format);",
                            [
                                { name: "hrtc", description: "RTC 句柄。" },
                                { name: "sTime", description: "时间输出结构体。" },
                                { name: "Format", description: "BIN 或 BCD 格式。" }
                            ],
                            commonStatusReturn,
                            "在带影子寄存器的实现中，通常应随后调用 HAL_RTC_GetDate()，以解锁下一次一致读取。",
                            "HAL_RTC_GetTime(&hrtc, &time, RTC_FORMAT_BIN);\nHAL_RTC_GetDate(&hrtc, &date, RTC_FORMAT_BIN);"
                        ),
                        createFunction(
                            "HAL_RTC_SetDate",
                            "设置 RTC 日期。",
                            "HAL_StatusTypeDef HAL_RTC_SetDate(RTC_HandleTypeDef *hrtc, RTC_DateTypeDef *sDate, uint32_t Format);",
                            [
                                { name: "hrtc", description: "RTC 句柄。" },
                                { name: "sDate", description: "年、月、日、星期等日期数据。" },
                                { name: "Format", description: "BIN 或 BCD 格式。" }
                            ],
                            commonStatusReturn,
                            "STM32 HAL 常用 RTC 年份字段通常保存两位年份，世纪信息需由应用层管理。",
                            "HAL_RTC_SetDate(&hrtc, &date, RTC_FORMAT_BIN);"
                        ),
                        createFunction(
                            "HAL_RTC_GetDate",
                            "读取 RTC 当前日期。",
                            "HAL_StatusTypeDef HAL_RTC_GetDate(RTC_HandleTypeDef *hrtc, RTC_DateTypeDef *sDate, uint32_t Format);",
                            [
                                { name: "hrtc", description: "RTC 句柄。" },
                                { name: "sDate", description: "日期输出结构体。" },
                                { name: "Format", description: "BIN 或 BCD 格式。" }
                            ],
                            commonStatusReturn,
                            "读取时间和日期时，建议按 HAL 文档要求成对调用以获得一致快照。",
                            "HAL_RTC_GetDate(&hrtc, &date, RTC_FORMAT_BIN);"
                        )
                    ]
                },
                {
                    id: "iwdg",
                    name: "IWDG",
                    description: "独立看门狗：在规定窗口内刷新计数器。",
                    functions: [
                        createFunction(
                            "HAL_IWDG_Refresh",
                            "刷新独立看门狗计数器。",
                            "HAL_StatusTypeDef HAL_IWDG_Refresh(IWDG_HandleTypeDef *hiwdg);",
                            [{ name: "hiwdg", description: "IWDG 句柄。" }],
                            commonStatusReturn,
                            "应在系统关键任务均确认正常后刷新，不能无条件放在高优先级定时中断中。",
                            "if (system_health_ok) {\n    HAL_IWDG_Refresh(&hiwdg);\n}"
                        )
                    ]
                }
            ]
        }
    ]
};

function mergeGeneratedCatalog() {
    const catalog = window.HAL_GENERATED_CATALOG || {};
    seedData.categories.forEach(category => {
        category.modules.forEach(module => {
            const generatedFunctions = catalog[module.id] || [];
            const existingByName = new Map(module.functions.map(func => [func.name, func]));
            generatedFunctions.forEach(func => {
                const existing = existingByName.get(func.name);
                if (existing) {
                    existing.families = [...new Set([...existing.families, ...func.families])];
                    existing.familyPrototypes = func.familyPrototypes;
                } else {
                    module.functions.push(func);
                }
            });
        });
    });
}

mergeGeneratedCatalog();

const state = {
    data: null,
    selectedModuleId: "gpio",
    query: "",
    family: "ALL",
    searchIndex: [],
    searchIndexDirty: true,
    searchResultLimit: 200,
    editing: false,
    managing: false,
    selectedFunctionIds: new Set(),
    draggedFunctionId: null,
    editingFunctionId: null,
    editingModuleId: null,
    collapsedCategories: new Set()
};

const elements = {
    categoryNav: document.querySelector("#categoryNav"),
    searchInput: document.querySelector("#searchInput"),
    moduleTitle: document.querySelector("#moduleTitle"),
    moduleDescription: document.querySelector("#moduleDescription"),
    categoryLabel: document.querySelector("#categoryLabel"),
    resultCount: document.querySelector("#resultCount"),
    functionList: document.querySelector("#functionList"),
    activeFilters: document.querySelector("#activeFilters"),
    editModeBtn: document.querySelector("#editModeBtn"),
    addFunctionBtn: document.querySelector("#addFunctionBtn"),
    manageModeBtn: document.querySelector("#manageModeBtn"),
    manageToolbar: document.querySelector("#manageToolbar"),
    selectAllBtn: document.querySelector("#selectAllBtn"),
    selectedCount: document.querySelector("#selectedCount"),
    deleteSelectedBtn: document.querySelector("#deleteSelectedBtn"),
    moduleSettingsBtn: document.querySelector("#moduleSettingsBtn"),
    addModuleBtn: document.querySelector("#addModuleBtn"),
    dataMenuBtn: document.querySelector("#dataMenuBtn"),
    dataMenu: document.querySelector("#dataMenu"),
    exportBtn: document.querySelector("#exportBtn"),
    importBtn: document.querySelector("#importBtn"),
    resetBtn: document.querySelector("#resetBtn"),
    fileInput: document.querySelector("#fileInput"),
    toast: document.querySelector("#toast"),
    functionDialog: document.querySelector("#functionDialog"),
    functionForm: document.querySelector("#functionForm"),
    functionDialogTitle: document.querySelector("#functionDialogTitle"),
    fieldName: document.querySelector("#fieldName"),
    fieldPrototype: document.querySelector("#fieldPrototype"),
    fieldBrief: document.querySelector("#fieldBrief"),
    fieldParams: document.querySelector("#fieldParams"),
    fieldReturn: document.querySelector("#fieldReturn"),
    fieldNotes: document.querySelector("#fieldNotes"),
    fieldExample: document.querySelector("#fieldExample"),
    familyF1: document.querySelector("#familyF1"),
    familyF4: document.querySelector("#familyF4"),
    familyG4: document.querySelector("#familyG4"),
    moduleDialog: document.querySelector("#moduleDialog"),
    moduleForm: document.querySelector("#moduleForm"),
    moduleDialogTitle: document.querySelector("#moduleDialogTitle"),
    moduleCategory: document.querySelector("#moduleCategory"),
    moduleName: document.querySelector("#moduleName"),
    moduleDescriptionField: document.querySelector("#moduleDescriptionField"),
    deleteModuleBtn: document.querySelector("#deleteModuleBtn"),
    confirmDialog: document.querySelector("#confirmDialog"),
    confirmTitle: document.querySelector("#confirmTitle"),
    confirmText: document.querySelector("#confirmText")
};

function deepClone(value) {
    return JSON.parse(JSON.stringify(value));
}

function upgradeStoredData(stored) {
    if (!stored) {
        return deepClone(seedData);
    }
    if ((stored.schemaVersion || 1) >= seedData.schemaVersion) {
        return stored;
    }

    const latest = deepClone(seedData);
    latest.categories.forEach(latestCategory => {
        let storedCategory = stored.categories.find(category => category.id === latestCategory.id);
        if (!storedCategory) {
            stored.categories.push(latestCategory);
            return;
        }
        latestCategory.modules.forEach(latestModule => {
            let storedModule = storedCategory.modules.find(module => module.id === latestModule.id);
            if (!storedModule) {
                storedCategory.modules.push(latestModule);
                return;
            }
            const storedNames = new Set(storedModule.functions.map(func => func.name));
            const latestByName = new Map(latestModule.functions.map(func => [func.name, func]));
            storedModule.functions.forEach(func => {
                const latestFunction = latestByName.get(func.name);
                if (latestFunction && String(func.id).startsWith("catalog-")) {
                    Object.assign(func, latestFunction);
                }
            });
            latestModule.functions.forEach(func => {
                if (!storedNames.has(func.name)) {
                    storedModule.functions.push(func);
                }
            });
        });
    });
    stored.schemaVersion = seedData.schemaVersion;
    return stored;
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function getAllModules() {
    return state.data.categories.flatMap(category => category.modules.map(module => ({ category, module })));
}

function getSelectedModuleEntry() {
    return getAllModules().find(entry => entry.module.id === state.selectedModuleId) || getAllModules()[0];
}

function getModuleEntry(moduleId) {
    return getAllModules().find(entry => entry.module.id === moduleId);
}

function openDatabase() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);
        request.onupgradeneeded = () => {
            if (!request.result.objectStoreNames.contains(STORE_NAME)) {
                request.result.createObjectStore(STORE_NAME);
            }
        };
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

async function loadData() {
    try {
        const database = await openDatabase();
        const stored = await new Promise((resolve, reject) => {
            const transaction = database.transaction(STORE_NAME, "readonly");
            const request = transaction.objectStore(STORE_NAME).get(DATA_KEY);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
        database.close();
        return upgradeStoredData(stored);
    } catch (error) {
        const fallback = localStorage.getItem(DB_NAME);
        return upgradeStoredData(fallback ? JSON.parse(fallback) : null);
    }
}

async function saveData() {
    state.data.updatedAt = new Date().toISOString();
    state.searchIndexDirty = true;
    try {
        const database = await openDatabase();
        await new Promise((resolve, reject) => {
            const transaction = database.transaction(STORE_NAME, "readwrite");
            transaction.objectStore(STORE_NAME).put(state.data, DATA_KEY);
            transaction.oncomplete = resolve;
            transaction.onerror = () => reject(transaction.error);
        });
        database.close();
    } catch (error) {
        localStorage.setItem(DB_NAME, JSON.stringify(state.data));
    }
}

function showToast(message) {
    window.clearTimeout(showToast.timer);
    elements.toast.textContent = message;
    elements.toast.classList.add("is-visible");
    showToast.timer = window.setTimeout(() => elements.toast.classList.remove("is-visible"), 2400);
}

function renderNavigation() {
    elements.categoryNav.replaceChildren();
    state.data.categories.forEach(category => {
        const group = document.createElement("section");
        group.className = "category-group";
        if (state.collapsedCategories.has(category.id)) {
            group.classList.add("is-collapsed");
        }

        const header = document.createElement("button");
        header.type = "button";
        header.className = "category-header";
        header.innerHTML = `<span>${escapeHtml(category.name)}</span><span>⌄</span>`;
        header.addEventListener("click", () => {
            if (state.collapsedCategories.has(category.id)) {
                state.collapsedCategories.delete(category.id);
            } else {
                state.collapsedCategories.add(category.id);
            }
            renderNavigation();
        });

        const moduleList = document.createElement("div");
        moduleList.className = "module-list";
        category.modules.forEach(module => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "module-nav-button";
            button.classList.toggle("is-active", module.id === state.selectedModuleId && !state.query);
            button.innerHTML = `<span>${escapeHtml(module.name)}</span><span class="module-count">${module.functions.length}</span>`;
            button.addEventListener("click", () => {
                state.selectedModuleId = module.id;
                state.query = "";
                state.managing = false;
                state.selectedFunctionIds.clear();
                elements.searchInput.value = "";
                render();
                if (window.innerWidth < 760) {
                    document.querySelector(".content").scrollIntoView({ behavior: "smooth" });
                }
            });
            moduleList.append(button);
        });

        group.append(header, moduleList);
        elements.categoryNav.append(group);
    });
}

function normalizeSearchValue(value) {
    const raw = String(value ?? "");
    const separated = raw
        .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
        .replace(/[_\-./\\]+/g, " ");
    return `${raw.toLowerCase()} ${separated.toLowerCase()}`;
}

function getSearchText(item) {
    const func = item.func;
    return normalizeSearchValue([
        item.module.name,
        item.category.name,
        func.name,
        func.brief,
        func.prototype,
        func.returns,
        func.notes,
        func.example,
        ...func.params.flatMap(param => [param.name, param.description])
    ].join(" "));
}

function getSearchTokens(query) {
    const stopWords = new Set(["相关", "相关的", "函数", "接口", "内容", "function", "functions", "related"]);
    const tokens = normalizeSearchValue(query).match(/[a-z0-9]+|[\u4e00-\u9fff]+/g) || [];
    return [...new Set(tokens.filter(token => !stopWords.has(token)))];
}

function matchesSearchToken(searchText, token) {
    if (/^[a-z0-9]+$/.test(token) && token.length <= 3) {
        return new RegExp(`\\b${token}\\b`).test(searchText);
    }
    return searchText.includes(token);
}

function rebuildSearchIndex() {
    state.searchIndex = [];
    getAllModules().forEach(({ category, module }) => {
        module.functions.forEach(func => {
            const item = { category, module, func };
            state.searchIndex.push({
                ...item,
                searchText: getSearchText(item),
                nameText: normalizeSearchValue(func.name)
            });
        });
    });
    state.searchIndexDirty = false;
}

function getSearchScore(item, tokens, compactQuery) {
    const compactName = item.func.name.toLowerCase().replace(/[^a-z0-9\u4e00-\u9fff]+/g, "");
    let score = 0;
    if (compactQuery && compactName.includes(compactQuery)) {
        score -= 100;
    }
    if (tokens.every(token => item.nameText.includes(token))) {
        score -= 50;
    }
    if (tokens.some(token => item.module.name.toLowerCase().includes(token))) {
        score -= 20;
    }
    return score;
}

function getVisibleFunctions() {
    const query = state.query.trim();
    if (query) {
        if (state.searchIndexDirty) {
            rebuildSearchIndex();
        }
        const tokens = getSearchTokens(query);
        const compactQuery = query.toLowerCase().replace(/[^a-z0-9\u4e00-\u9fff]+/g, "");
        return state.searchIndex
            .filter(item => {
                const familyMatches = state.family === "ALL" || item.func.families.includes(state.family);
                const queryMatches = tokens.length > 0 && tokens.every(token => matchesSearchToken(item.searchText, token));
                return familyMatches && queryMatches;
            })
            .map((item, index) => ({
                item,
                index,
                score: getSearchScore(item, tokens, compactQuery)
            }))
            .sort((left, right) => left.score - right.score || left.index - right.index)
            .map(result => result.item);
    }
    const selected = getSelectedModuleEntry();
    return selected.module.functions
        .map(func => ({ ...selected, func }))
        .filter(item => state.family === "ALL" || item.func.families.includes(state.family));
}

function makeDocPreview(func) {
    const params = func.params.length
        ? func.params.map(param => ` * <span class="doc-tag">@param</span> <span class="doc-value">${escapeHtml(param.name)}</span> ${escapeHtml(param.description)}`).join("\n")
        : " * <span class=\"doc-tag\">@param</span> 无";
    return `<span class="doc-value">/**</span>\n * <span class="doc-tag">@brief</span> ${escapeHtml(func.brief)}\n${params}\n * <span class="doc-tag">@return</span> ${escapeHtml(func.returns)}\n * <span class="doc-tag">@notes</span> ${escapeHtml(func.notes)}\n * <span class="doc-tag">@example</span> 见下方示例\n <span class="doc-value">*/</span>\n<span class="prototype">${escapeHtml(func.prototype)}</span>`;
}

function updateManageToolbar() {
    if (!state.data) {
        return;
    }
    const entry = getSelectedModuleEntry();
    const allIds = entry.module.functions.map(func => func.id);
    const selectedCount = allIds.filter(id => state.selectedFunctionIds.has(id)).length;
    const allSelected = allIds.length > 0 && selectedCount === allIds.length;
    elements.selectedCount.textContent = `已选择 ${selectedCount} 项`;
    elements.selectAllBtn.textContent = allSelected ? "取消全选" : "全选";
    elements.selectAllBtn.setAttribute("aria-pressed", String(allSelected));
    elements.deleteSelectedBtn.disabled = selectedCount === 0;
}

function clearDropIndicators() {
    elements.functionList.querySelectorAll(".function-card").forEach(card => {
        card.classList.remove("is-drop-before", "is-drop-after", "is-dragging");
    });
}

async function reorderFunction(sourceId, targetId, placeAfter) {
    if (!sourceId || sourceId === targetId) {
        return;
    }
    const functions = getSelectedModuleEntry().module.functions;
    const sourceIndex = functions.findIndex(func => func.id === sourceId);
    if (sourceIndex < 0) {
        return;
    }
    const [moved] = functions.splice(sourceIndex, 1);
    let targetIndex = functions.findIndex(func => func.id === targetId);
    if (targetIndex < 0) {
        functions.splice(sourceIndex, 0, moved);
        return;
    }
    if (placeAfter) {
        targetIndex += 1;
    }
    functions.splice(targetIndex, 0, moved);
    await saveData();
    renderContent();
    showToast("函数顺序已保存");
}

function createFunctionDetail(module, func) {
    const paramsHtml = func.params.length
        ? `<ul class="param-list">${func.params.map(param => `<li><span class="param-name">${escapeHtml(param.name)}</span>${escapeHtml(param.description)}</li>`).join("")}</ul>`
        : "<p>无参数。</p>";
    const detail = document.createElement("div");
    detail.className = "function-detail";
    detail.innerHTML = `
        <pre class="code-preview">${makeDocPreview(func)}</pre>
        <div class="detail-grid">
            <section class="detail-cell">
                <h4>@PARAMETER</h4>
                ${paramsHtml}
            </section>
            <section class="detail-cell">
                <h4>@RETURN</h4>
                <p>${escapeHtml(func.returns)}</p>
            </section>
            <section class="detail-cell is-wide">
                <h4>@NOTES</h4>
                <p>${escapeHtml(func.notes)}</p>
            </section>
            <section class="detail-cell is-wide">
                <h4>@EXAMPLE</h4>
                <pre class="example-code">${escapeHtml(func.example || "暂无示例。")}</pre>
            </section>
        </div>
        <div class="card-editor-actions edit-only">
            <button class="mini-button" type="button" data-action="edit">编辑函数</button>
            <button class="mini-button is-danger" type="button" data-action="delete">删除函数</button>
        </div>`;

    detail.querySelector('[data-action="edit"]').addEventListener("click", event => {
        event.preventDefault();
        openFunctionEditor(module.id, func.id);
    });
    detail.querySelector('[data-action="delete"]').addEventListener("click", async event => {
        event.preventDefault();
        if (await confirmAction("删除函数", `确定删除 ${func.name} 吗？`)) {
            const entry = getModuleEntry(module.id);
            entry.module.functions = entry.module.functions.filter(current => current.id !== func.id);
            await saveData();
            render();
            showToast("函数已删除");
        }
    });
    return detail;
}

function createFunctionCard(item) {
    const { module, func } = item;
    const card = document.createElement("details");
    card.className = "function-card";
    card.dataset.functionId = func.id;
    card.dataset.moduleId = module.id;

    const moduleHint = state.query ? `<span class="family-tag">${escapeHtml(module.name)}</span>` : "";
    const kindHint = func.kind === "macro" ? '<span class="family-tag macro-tag">宏</span>' : "";

    card.innerHTML = `
        <summary>
            <label class="selection-box manage-only" title="选择 ${escapeHtml(func.name)}">
                <input type="checkbox" ${state.selectedFunctionIds.has(func.id) ? "checked" : ""} aria-label="选择 ${escapeHtml(func.name)}">
            </label>
            <span class="function-title">
                <span class="function-name">${escapeHtml(func.name)}</span>
                <span class="function-brief">${escapeHtml(func.brief)}</span>
            </span>
            <span class="family-tags">${moduleHint}${kindHint}${func.families.map(family => `<span class="family-tag">${family}</span>`).join("")}</span>
            <span class="summary-arrow" aria-hidden="true">›</span>
            <span class="drag-handle manage-only" draggable="true" role="button" tabindex="0" title="拖动调整顺序" aria-label="拖动 ${escapeHtml(func.name)} 调整顺序">⠿</span>
        </summary>`;

    const selectionBox = card.querySelector(".selection-box");
    const checkbox = selectionBox.querySelector("input");
    const dragHandle = card.querySelector(".drag-handle");
    selectionBox.addEventListener("click", event => event.stopPropagation());
    checkbox.addEventListener("change", () => {
        if (checkbox.checked) {
            state.selectedFunctionIds.add(func.id);
        } else {
            state.selectedFunctionIds.delete(func.id);
        }
        updateManageToolbar();
    });
    dragHandle.addEventListener("click", event => {
        event.preventDefault();
        event.stopPropagation();
    });
    dragHandle.addEventListener("dragstart", event => {
        if (!state.managing) {
            event.preventDefault();
            return;
        }
        state.draggedFunctionId = func.id;
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", func.id);
        event.dataTransfer.setDragImage(card, 28, 28);
        card.classList.add("is-dragging");
    });
    dragHandle.addEventListener("dragend", () => {
        state.draggedFunctionId = null;
        clearDropIndicators();
    });
    card.addEventListener("dragover", event => {
        if (!state.managing || state.draggedFunctionId === func.id) {
            return;
        }
        event.preventDefault();
        clearDropIndicators();
        const bounds = card.getBoundingClientRect();
        const placeAfter = event.clientY > bounds.top + bounds.height / 2;
        card.classList.add(placeAfter ? "is-drop-after" : "is-drop-before");
    });
    card.addEventListener("drop", event => {
        if (!state.managing) {
            return;
        }
        event.preventDefault();
        const bounds = card.getBoundingClientRect();
        const placeAfter = event.clientY > bounds.top + bounds.height / 2;
        const sourceId = event.dataTransfer.getData("text/plain") || state.draggedFunctionId;
        clearDropIndicators();
        reorderFunction(sourceId, func.id, placeAfter);
    });
    card.addEventListener("toggle", () => {
        if (card.open && !card.querySelector(".function-detail")) {
            card.append(createFunctionDetail(module, func));
        }
    });
    return card;
}

function renderContent() {
    const selected = getSelectedModuleEntry();
    const allVisible = getVisibleFunctions();
    const visible = state.query ? allVisible.slice(0, state.searchResultLimit) : allVisible;

    if (state.query) {
        elements.categoryLabel.textContent = "GLOBAL SEARCH";
        elements.moduleTitle.textContent = "全库搜索";
        elements.moduleDescription.textContent = `正在全部模块中搜索“${state.query}”。`;
        elements.manageModeBtn.disabled = true;
        elements.addFunctionBtn.disabled = true;
    } else {
        elements.categoryLabel.textContent = selected.category.name.toUpperCase();
        elements.moduleTitle.textContent = selected.module.name;
        elements.moduleDescription.textContent = selected.module.description;
        elements.manageModeBtn.disabled = false;
        elements.addFunctionBtn.disabled = false;
    }

    const macroCount = allVisible.filter(item => item.func.kind === "macro").length;
    const functionCount = allVisible.length - macroCount;
    elements.resultCount.textContent = `${allVisible.length} 项（函数 ${functionCount} / 宏 ${macroCount}）`;
    elements.activeFilters.hidden = state.family === "ALL" && !state.query;
    elements.activeFilters.textContent = [
        state.query ? `关键词：${state.query}` : "",
        state.family !== "ALL" ? `系列：STM32${state.family}` : ""
    ].filter(Boolean).join("　·　");

    elements.functionList.replaceChildren();
    if (!visible.length) {
        const empty = document.createElement("div");
        empty.className = "empty-state";
        empty.innerHTML = "<strong>没有匹配的函数</strong><span>换一个关键词、系列，或在编辑模式中添加函数。</span>";
        elements.functionList.append(empty);
        updateManageToolbar();
        return;
    }
    visible.forEach(item => elements.functionList.append(createFunctionCard(item)));
    if (visible.length < allVisible.length) {
        const loadMore = document.createElement("button");
        loadMore.className = "load-more";
        loadMore.type = "button";
        loadMore.textContent = `加载更多（已显示 ${visible.length} / ${allVisible.length}）`;
        loadMore.addEventListener("click", () => {
            state.searchResultLimit += 200;
            renderContent();
        });
        elements.functionList.append(loadMore);
    }
    updateManageToolbar();
}

function render() {
    document.body.classList.toggle("is-editing", state.editing);
    document.body.classList.toggle("is-managing", state.managing);
    const mobileLabel = window.innerWidth < 760;
    elements.editModeBtn.textContent = state.editing
        ? (mobileLabel ? "完成" : "退出编辑")
        : (mobileLabel ? "编辑" : "进入编辑");
    elements.editModeBtn.setAttribute("aria-pressed", String(state.editing));
    elements.manageModeBtn.textContent = state.managing ? "完成管理" : "管理";
    elements.manageModeBtn.setAttribute("aria-pressed", String(state.managing));
    elements.searchInput.disabled = state.managing;
    document.querySelectorAll(".chip").forEach(chip => {
        chip.disabled = state.managing;
    });
    renderNavigation();
    renderContent();
}

function openFunctionEditor(moduleId, functionId = null) {
    const entry = getModuleEntry(moduleId);
    const func = functionId ? entry.module.functions.find(item => item.id === functionId) : null;
    state.selectedModuleId = moduleId;
    state.editingFunctionId = functionId;
    elements.functionDialogTitle.textContent = func ? "编辑函数" : "添加函数";
    elements.fieldName.value = func?.name || "";
    elements.fieldPrototype.value = func?.prototype || "";
    elements.fieldBrief.value = func?.brief || "";
    elements.fieldParams.value = func?.params.map(param => `${param.name} | ${param.description}`).join("\n") || "";
    elements.fieldReturn.value = func?.returns || "";
    elements.fieldNotes.value = func?.notes || "";
    elements.fieldExample.value = func?.example || "";
    elements.familyF1.checked = func?.families.includes("F1") ?? true;
    elements.familyF4.checked = func?.families.includes("F4") ?? true;
    elements.familyG4.checked = func?.families.includes("G4") ?? true;
    elements.functionDialog.showModal();
}

function parseParameters(value) {
    return value.split("\n")
        .map(line => line.trim())
        .filter(Boolean)
        .map(line => {
            const separator = line.indexOf("|");
            if (separator < 0) {
                return { name: line, description: "" };
            }
            return {
                name: line.slice(0, separator).trim(),
                description: line.slice(separator + 1).trim()
            };
        });
}

async function handleFunctionSubmit(event) {
    if (event.submitter?.value === "cancel") {
        return;
    }
    event.preventDefault();
    const families = [elements.familyF1, elements.familyF4, elements.familyG4]
        .filter(input => input.checked)
        .map(input => input.value);
    if (!families.length) {
        showToast("至少选择一个适用系列");
        return;
    }

    const entry = getSelectedModuleEntry();
    const values = {
        name: elements.fieldName.value.trim(),
        prototype: elements.fieldPrototype.value.trim(),
        brief: elements.fieldBrief.value.trim(),
        params: parseParameters(elements.fieldParams.value),
        returns: elements.fieldReturn.value.trim() || "无。",
        notes: elements.fieldNotes.value.trim() || "暂无补充说明。",
        example: elements.fieldExample.value.trim(),
        families
    };

    if (state.editingFunctionId) {
        const index = entry.module.functions.findIndex(func => func.id === state.editingFunctionId);
        entry.module.functions[index] = { ...entry.module.functions[index], ...values };
    } else {
        entry.module.functions.push({
            id: `${values.name.toLowerCase().replace(/[^a-z0-9]+/g, "-")}-${crypto.randomUUID()}`,
            ...values
        });
    }

    await saveData();
    elements.functionDialog.close();
    render();
    showToast(state.editingFunctionId ? "函数修改已保存" : "函数已添加");
}

function populateCategorySelect(selectedCategoryId) {
    elements.moduleCategory.replaceChildren();
    state.data.categories.forEach(category => {
        const option = document.createElement("option");
        option.value = category.id;
        option.textContent = category.name;
        option.selected = category.id === selectedCategoryId;
        elements.moduleCategory.append(option);
    });
}

function openModuleEditor(moduleId = null) {
    const entry = moduleId ? getModuleEntry(moduleId) : getSelectedModuleEntry();
    state.editingModuleId = moduleId;
    elements.moduleDialogTitle.textContent = moduleId ? "编辑模块" : "添加模块";
    populateCategorySelect(entry.category.id);
    elements.moduleName.value = moduleId ? entry.module.name : "";
    elements.moduleDescriptionField.value = moduleId ? entry.module.description : "";
    elements.deleteModuleBtn.hidden = !moduleId;
    elements.moduleDialog.showModal();
}

async function handleModuleSubmit(event) {
    if (event.submitter?.value === "cancel") {
        return;
    }
    event.preventDefault();
    const targetCategory = state.data.categories.find(category => category.id === elements.moduleCategory.value);
    if (state.editingModuleId) {
        const source = getModuleEntry(state.editingModuleId);
        source.module.name = elements.moduleName.value.trim();
        source.module.description = elements.moduleDescriptionField.value.trim();
        if (source.category.id !== targetCategory.id) {
            source.category.modules = source.category.modules.filter(module => module.id !== source.module.id);
            targetCategory.modules.push(source.module);
        }
    } else {
        const name = elements.moduleName.value.trim();
        const module = {
            id: `${name.toLowerCase().replace(/[^a-z0-9]+/g, "-") || "module"}-${crypto.randomUUID()}`,
            name,
            description: elements.moduleDescriptionField.value.trim(),
            functions: []
        };
        targetCategory.modules.push(module);
        state.selectedModuleId = module.id;
    }
    await saveData();
    elements.moduleDialog.close();
    render();
    showToast(state.editingModuleId ? "模块修改已保存" : "模块已添加");
}

async function deleteCurrentModule() {
    const entry = getModuleEntry(state.editingModuleId);
    const suffix = entry.module.functions.length ? `其中包含 ${entry.module.functions.length} 个函数，删除后无法恢复。` : "删除后无法恢复。";
    if (!await confirmAction("删除模块", `确定删除 ${entry.module.name} 吗？${suffix}`)) {
        return;
    }
    entry.category.modules = entry.category.modules.filter(module => module.id !== entry.module.id);
    state.selectedModuleId = getAllModules()[0]?.module.id || "";
    await saveData();
    elements.moduleDialog.close();
    render();
    showToast("模块已删除");
}

function confirmAction(title, text) {
    elements.confirmTitle.textContent = title;
    elements.confirmText.textContent = text;
    elements.confirmDialog.showModal();
    return new Promise(resolve => {
        elements.confirmDialog.addEventListener("close", () => {
            resolve(elements.confirmDialog.returnValue === "confirm");
        }, { once: true });
    });
}

function exportData() {
    const blob = new Blob([JSON.stringify(state.data, null, 4)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `stm32-hal-manual-${new Date().toISOString().slice(0, 10)}.json`;
    link.click();
    URL.revokeObjectURL(url);
    elements.dataMenu.hidden = true;
    showToast("JSON 备份已导出");
}

function validateImportedData(data) {
    if (!data || !Array.isArray(data.categories)) {
        return false;
    }
    return data.categories.every(category =>
        typeof category.name === "string" &&
        Array.isArray(category.modules) &&
        category.modules.every(module =>
            typeof module.name === "string" &&
            Array.isArray(module.functions) &&
            module.functions.every(func =>
                typeof func.name === "string" &&
                typeof func.prototype === "string" &&
                Array.isArray(func.params) &&
                Array.isArray(func.families)
            )
        )
    );
}

async function importData(file) {
    try {
        const data = JSON.parse(await file.text());
        if (!validateImportedData(data)) {
            throw new Error("数据结构不正确");
        }
        state.data = data;
        state.selectedModuleId = getAllModules()[0]?.module.id || "";
        await saveData();
        render();
        showToast("数据导入成功");
    } catch (error) {
        showToast(`导入失败：${error.message}`);
    } finally {
        elements.fileInput.value = "";
    }
}

async function resetData() {
    if (!await confirmAction("恢复初始数据", "所有个人修改都会被初始数据库覆盖。建议先导出 JSON 备份。")) {
        return;
    }
    state.data = deepClone(seedData);
    state.selectedModuleId = "gpio";
    state.query = "";
    state.family = "ALL";
    elements.searchInput.value = "";
    document.querySelectorAll(".chip").forEach(chip => chip.classList.toggle("is-active", chip.dataset.family === "ALL"));
    await saveData();
    render();
    showToast("已恢复初始数据库");
}

function toggleManagement() {
    state.managing = !state.managing;
    state.selectedFunctionIds.clear();
    if (state.managing) {
        state.query = "";
        state.family = "ALL";
        elements.searchInput.value = "";
        document.querySelectorAll(".chip").forEach(chip => {
            chip.classList.toggle("is-active", chip.dataset.family === "ALL");
        });
    }
    render();
    showToast(state.managing ? "函数管理已开启" : "函数顺序与选择已保存");
}

function toggleSelectAll() {
    const ids = getSelectedModuleEntry().module.functions.map(func => func.id);
    const allSelected = ids.length > 0 && ids.every(id => state.selectedFunctionIds.has(id));
    if (allSelected) {
        ids.forEach(id => state.selectedFunctionIds.delete(id));
    } else {
        ids.forEach(id => state.selectedFunctionIds.add(id));
    }
    renderContent();
}

async function deleteSelectedFunctions() {
    const entry = getSelectedModuleEntry();
    const selectedCount = entry.module.functions.filter(func => state.selectedFunctionIds.has(func.id)).length;
    if (!selectedCount) {
        return;
    }
    if (!await confirmAction("批量删除函数", `确定删除已选择的 ${selectedCount} 个函数吗？删除后可通过“恢复初始数据”找回内置函数。`)) {
        return;
    }
    entry.module.functions = entry.module.functions.filter(func => !state.selectedFunctionIds.has(func.id));
    state.selectedFunctionIds.clear();
    await saveData();
    render();
    showToast(`已删除 ${selectedCount} 个函数`);
}

function bindEvents() {
    let searchTimer = 0;
    elements.searchInput.addEventListener("input", event => {
        const query = event.target.value.trim();
        window.clearTimeout(searchTimer);
        searchTimer = window.setTimeout(() => {
            state.query = query;
            state.searchResultLimit = 200;
            render();
        }, 120);
    });

    document.addEventListener("keydown", event => {
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
            event.preventDefault();
            elements.searchInput.focus();
        }
        if (event.key === "Escape" && !elements.dataMenu.hidden) {
            elements.dataMenu.hidden = true;
        }
    });

    document.querySelectorAll(".chip").forEach(chip => {
        chip.addEventListener("click", () => {
            state.family = chip.dataset.family;
            state.searchResultLimit = 200;
            document.querySelectorAll(".chip").forEach(current => current.classList.toggle("is-active", current === chip));
            renderContent();
        });
    });

    elements.editModeBtn.addEventListener("click", () => {
        state.editing = !state.editing;
        if (!state.editing) {
            state.managing = false;
            state.selectedFunctionIds.clear();
        }
        render();
        showToast(state.editing ? "编辑模式已开启" : "编辑模式已关闭");
    });
    elements.addFunctionBtn.addEventListener("click", () => openFunctionEditor(state.selectedModuleId));
    elements.manageModeBtn.addEventListener("click", toggleManagement);
    elements.selectAllBtn.addEventListener("click", toggleSelectAll);
    elements.deleteSelectedBtn.addEventListener("click", deleteSelectedFunctions);
    elements.moduleSettingsBtn.addEventListener("click", () => openModuleEditor(state.selectedModuleId));
    elements.addModuleBtn.addEventListener("click", () => openModuleEditor());
    elements.functionForm.addEventListener("submit", handleFunctionSubmit);
    elements.moduleForm.addEventListener("submit", handleModuleSubmit);
    elements.deleteModuleBtn.addEventListener("click", deleteCurrentModule);

    elements.dataMenuBtn.addEventListener("click", event => {
        event.stopPropagation();
        elements.dataMenu.hidden = !elements.dataMenu.hidden;
    });
    document.addEventListener("click", event => {
        if (!elements.dataMenu.contains(event.target) && event.target !== elements.dataMenuBtn) {
            elements.dataMenu.hidden = true;
        }
    });
    elements.exportBtn.addEventListener("click", exportData);
    elements.importBtn.addEventListener("click", () => {
        elements.dataMenu.hidden = true;
        elements.fileInput.click();
    });
    elements.fileInput.addEventListener("change", () => {
        if (elements.fileInput.files[0]) {
            importData(elements.fileInput.files[0]);
        }
    });
    elements.resetBtn.addEventListener("click", () => {
        elements.dataMenu.hidden = true;
        resetData();
    });
    window.addEventListener("resize", () => render());
}

async function initialize() {
    state.data = await loadData();
    if (!getModuleEntry(state.selectedModuleId)) {
        state.selectedModuleId = getAllModules()[0]?.module.id || "";
    }
    await saveData();
    bindEvents();
    render();
}

initialize();
