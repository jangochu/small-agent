# Lessons Learned

## Qwen Function Calling Format

**Lesson**: Qwen models have specific requirements for tool calling message format.

**Key findings:**
1. Assistant messages with `tool_calls` must have `content: null` (not empty string "")
2. Tool messages must include `tool_call_id` matching the preceding tool call's id
3. The `tool_calls` array must be preserved exactly as returned by the API
4. Second call to get final response can include `tools` parameter or omit it

**How to apply:**
- When converting messages to DashScope format, preserve `tool_calls` and `tool_call_id` fields
- Set `content: null` for assistant messages that contain tool calls
- Always execute a second LLM call after tool execution to get the final natural language response

## Open-Meteo Geocoding

**Lesson**: City name geocoding can return multiple results with ambiguous names.

**Key findings:**
- "杭州" can match multiple locations (e.g., 杭州 in Sichuan vs 杭州 in Zhejiang)
- Open-Meteo returns results ordered by relevance, but not always the expected city
- Using `feature_code` filtering (PPLC, PPLA) helps prefer major cities

**How to apply:**
- When geocoding, request multiple results and filter by feature_code
- Consider allowing users to specify province/country for disambiguation

