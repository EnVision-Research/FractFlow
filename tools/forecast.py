"""
Weather forecast tool provider.

Provides tools for retrieving weather forecasts, alerts, and assessing running conditions.
"""

from typing import Any, Dict
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""

@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

@mcp.tool()
async def assess_running_condition(weather: Dict[str, Any]) -> str:
    """评估天气条件是否适合跑步。
    
    Args:
        weather: 天气信息字典，包含各种天气参数
    """
    # 初始化评分（满分10分）
    score = 10
    reasons = []
    
    # 检查天气状况
    condition = weather.get("condition", "")
    if "雨" in condition:
        score -= 5
        reasons.append("下雨天气不适合户外跑步")
    elif "雪" in condition:
        score -= 6
        reasons.append("雪天路滑，不建议户外跑步")
    elif "雾" in condition:
        score -= 4
        reasons.append("雾天能见度低，注意安全")
    elif "晴" in condition:
        score += 1
        reasons.append("晴天非常适合跑步")
    
    # 检查温度
    temp_low = weather.get("temperature_low", 15)
    temp_high = weather.get("temperature_high", 25)
    temp_avg = (temp_low + temp_high) / 2
    
    if temp_avg < 5:
        score -= 3
        reasons.append("温度过低，需要穿着保暖")
    elif temp_avg < 10:
        score -= 1
        reasons.append("温度稍低，需要适当保暖")
    elif 15 <= temp_avg <= 25:
        score += 1
        reasons.append("温度适宜")
    elif temp_avg > 30:
        score -= 4
        reasons.append("温度过高，可能中暑")
    elif temp_avg > 35:
        score -= 6
        reasons.append("温度过高，不建议户外运动")
    
    # 检查空气质量
    air_quality = weather.get("air_quality", "")
    if "优" in air_quality or "excellent" in air_quality.lower():
        score += 1
        reasons.append("空气质量优秀")
    elif "良好" in air_quality or "good" in air_quality.lower():
        # 良好不加减分
        pass
    elif "中等" in air_quality or "moderate" in air_quality.lower():
        score -= 1
        reasons.append("空气质量一般")
    elif "差" in air_quality or "poor" in air_quality.lower():
        score -= 3
        reasons.append("空气质量差，不建议户外运动")
    
    # 根据风力评分
    wind_speed = weather.get("wind_speed", "")
    if "微风" in wind_speed or "light" in wind_speed.lower():
        score += 1
        reasons.append("微风适宜跑步")
    elif "3" in wind_speed or "4" in wind_speed:
        # 3-4级风不加减分
        pass
    elif "5" in wind_speed or "6" in wind_speed:
        score -= 2
        reasons.append("风力较大，跑步可能受影响")
    elif any(str(i) in wind_speed for i in range(7, 13)):
        score -= 4
        reasons.append("大风天气，不建议户外跑步")
    
    # 综合评估
    recommendation = ""
    if score >= 8:
        recommendation = "天气非常适合跑步，推荐户外运动。"
    elif score >= 6:
        recommendation = "天气状况良好，适合跑步。"
    elif score >= 4:
        recommendation = "天气一般，如果决定跑步，需要注意防护。"
    else:
        recommendation = "天气不适合户外跑步，建议选择室内运动。"
    
    # 使用适当的换行符
    reasons_text = "- " + "\n- ".join(reasons) if reasons else "- 无特殊因素"
    
    return f"""
跑步适宜度评分: {score}/10
评估意见: {recommendation}
具体因素:
{reasons_text}
"""

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 