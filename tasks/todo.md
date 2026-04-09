# Tasks - External Tool Support Implementation

## Completed

- [x] 创建天气工具 (weather.py) - 使用 Open-Meteo API，无需 API key
- [x] 更新 LLM base 支持 tools 参数 - 在抽象类中添加 tools 参数
- [x] 实现 Bailian function calling - 支持 Qwen 模型的工具调用格式
- [x] 添加 harness tool 执行循环 - 检测 tool calls 并执行，然后获取最终响应
- [x] 注册天气工具并测试 - 在 agent.py 中注册 weather tool

## Implementation Summary

### Files Created
- `src/small_agent/tools/builtin/weather.py` - Weather tool using Open-Meteo API

### Files Modified
- `src/small_agent/llm/base.py` - Added `tools` parameter to LLMProvider interface
- `src/small_agent/llm/bailian.py` - Implemented Qwen function calling support
- `src/small_agent/harness.py` - Added tool execution loop with proper message formatting
- `src/small_agent/agent.py` - Registered WeatherTool, wired up tool passing
- `src/small_agent/tools/builtin/__init__.py` - Exported WeatherTool

## Test Results

```
Test 1: 杭州现在天气怎么样？
Response: 杭州现在的天气情况如下：
- 温度：13.3°C
- 天气状况：晴朗
- 湿度：64%
- 风速：6.4 公里/小时

Test 2: 北京天气如何？
Response: 北京现在的天气情况如下：
- 温度：18.1°C
- 天气状况：雷暴
- 湿度：93%

Test 3: 上海现在天气怎么样？(CLI)
Response: 上海现在的天气情况如下：
- 温度：24.3°C
- 天气状况：阴天
```

## Key Technical Details

1. **Qwen Function Calling Format**: Assistant messages with tool_calls must have `content: null`
2. **Tool Message Structure**: Requires `tool_call_id` to match the preceding tool call
3. **Message Conversion**: Must preserve `tool_calls` and `tool_call_id` when converting to DashScope format
4. **Execution Loop**: Detect tool_calls → execute tools → add results → call LLM again for final response
