import os
import tempfile
from typing import List, Optional
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import subprocess
import json
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip
from moviepy.video.fx import fadein, fadeout


load_dotenv()
mcp = FastMCP("video_processor")


def ensure_moviepy():
    """确保moviepy可用"""
    if VideoFileClip is None:
        raise ImportError("moviepy is required but not installed. Install with: pip install moviepy")


def validate_video_path(path: str) -> str:
    """验证和规范化视频文件路径"""
    expanded_path = os.path.expanduser(path)
    if not os.path.isabs(expanded_path):
        expanded_path = os.path.abspath(expanded_path)
    
    if not os.path.exists(expanded_path):
        raise FileNotFoundError(f"Video file not found: {expanded_path}")
    
    return expanded_path


def ensure_output_dir(output_path: str) -> str:
    """确保输出目录存在"""
    expanded_path = os.path.expanduser(output_path)
    if not os.path.isabs(expanded_path):
        expanded_path = os.path.abspath(expanded_path)
    
    output_dir = os.path.dirname(expanded_path)
    os.makedirs(output_dir, exist_ok=True)
    
    return expanded_path


@mcp.tool()
async def concatenate_videos(video_paths: List[str], output_path: str, transition_duration: float = 0.5) -> str:
    """
    拼接多个视频文件
    
    Args:
        video_paths: 视频文件路径列表
        output_path: 输出文件路径
        transition_duration: 过渡时长（秒），0表示无过渡
    
    Returns:
        成功信息和输出文件路径
    """
    try:
        ensure_moviepy()
        
        if not video_paths:
            return "Error: No video paths provided"
        
        if len(video_paths) < 2:
            return "Error: At least 2 videos are required for concatenation"
        
        # 验证所有输入文件
        validated_paths = []
        for path in video_paths:
            try:
                validated_path = validate_video_path(path)
                validated_paths.append(validated_path)
            except FileNotFoundError as e:
                return f"Error: {str(e)}"
        
        # 确保输出目录存在
        output_path = ensure_output_dir(output_path)
        
        # 加载视频文件
        clips = []
        for path in validated_paths:
            try:
                clip = VideoFileClip(path)
                clips.append(clip)
            except Exception as e:
                # 清理已加载的clips
                for c in clips:
                    c.close()
                return f"Error loading video {path}: {str(e)}"
        
        # 应用过渡效果
        if transition_duration > 0:
            processed_clips = []
            for i, clip in enumerate(clips):
                if i == 0:
                    # 第一个clip只需要fadeout
                    processed_clip = clip.fx(fadeout, transition_duration)
                elif i == len(clips) - 1:
                    # 最后一个clip只需要fadein
                    processed_clip = clip.fx(fadein, transition_duration)
                else:
                    # 中间的clips需要fadein和fadeout
                    processed_clip = clip.fx(fadein, transition_duration).fx(fadeout, transition_duration)
                processed_clips.append(processed_clip)
            
            final_clip = concatenate_videoclips(processed_clips, method="compose")
        else:
            final_clip = concatenate_videoclips(clips, method="compose")
        
        # 导出视频
        final_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            verbose=False,
            logger=None
        )
        
        # 清理资源
        final_clip.close()
        for clip in clips:
            clip.close()
        
        return f"Successfully concatenated {len(video_paths)} videos to: {output_path}"
        
    except Exception as e:
        return f"Error concatenating videos: {str(e)}"


@mcp.tool()
async def add_transitions(video_paths: List[str], transition_type: str = "fade", duration: float = 0.5) -> str:
    """
    为视频列表添加过渡效果，生成带过渡的临时文件
    
    Args:
        video_paths: 视频文件路径列表
        transition_type: 过渡类型 ("fade", "crossfade")
        duration: 过渡时长（秒）
    
    Returns:
        处理后的视频文件路径信息
    """
    try:
        ensure_moviepy()
        
        if not video_paths:
            return "Error: No video paths provided"
        
        # 验证所有输入文件
        validated_paths = []
        for path in video_paths:
            try:
                validated_path = validate_video_path(path)
                validated_paths.append(validated_path)
            except FileNotFoundError as e:
                return f"Error: {str(e)}"
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="video_transitions_")
        processed_paths = []
        
        # 处理每个视频
        for i, path in enumerate(validated_paths):
            try:
                clip = VideoFileClip(path)
                
                # 根据过渡类型处理
                if transition_type == "fade":
                    if i == 0:
                        # 第一个视频：只有fadeout
                        processed_clip = clip.fx(fadeout, duration)
                    elif i == len(validated_paths) - 1:
                        # 最后一个视频：只有fadein
                        processed_clip = clip.fx(fadein, duration)
                    else:
                        # 中间视频：fadein + fadeout
                        processed_clip = clip.fx(fadein, duration).fx(fadeout, duration)
                else:
                    # 其他过渡类型暂时使用fade
                    processed_clip = clip.fx(fadein, duration).fx(fadeout, duration)
                
                # 保存处理后的视频
                output_filename = f"transition_{i:03d}_{os.path.basename(path)}"
                output_path = os.path.join(temp_dir, output_filename)
                
                processed_clip.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    verbose=False,
                    logger=None
                )
                
                processed_paths.append(output_path)
                
                # 清理资源
                processed_clip.close()
                clip.close()
                
            except Exception as e:
                return f"Error processing video {path}: {str(e)}"
        
        result = f"Successfully added {transition_type} transitions to {len(video_paths)} videos.\n"
        result += f"Temporary files created in: {temp_dir}\n"
        result += "Processed files:\n"
        for path in processed_paths:
            result += f"- {path}\n"
        
        return result
        
    except Exception as e:
        return f"Error adding transitions: {str(e)}"


@mcp.tool()
async def convert_format(input_path: str, output_path: str, format: str = "mp4", quality: str = "high") -> str:
    """
    转换视频格式
    
    Args:
        input_path: 输入视频文件路径
        output_path: 输出视频文件路径
        format: 目标格式 ("mp4", "avi", "mov", "webm")
        quality: 质量设置 ("high", "medium", "low")
    
    Returns:
        转换结果信息
    """
    try:
        ensure_moviepy()
        
        # 验证输入文件
        input_path = validate_video_path(input_path)
        output_path = ensure_output_dir(output_path)
        
        # 加载视频
        clip = VideoFileClip(input_path)
        
        # 根据质量设置参数
        if quality == "high":
            bitrate = "5000k"
        elif quality == "medium":
            bitrate = "2000k"
        else:  # low
            bitrate = "1000k"
        
        # 转换格式
        if format.lower() == "mp4":
            clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                bitrate=bitrate,
                verbose=False,
                logger=None
            )
        elif format.lower() == "webm":
            clip.write_videofile(
                output_path,
                codec='libvpx',
                audio_codec='libvorbis',
                bitrate=bitrate,
                verbose=False,
                logger=None
            )
        else:
            # 对于其他格式，使用默认设置
            clip.write_videofile(
                output_path,
                bitrate=bitrate,
                verbose=False,
                logger=None
            )
        
        # 清理资源
        clip.close()
        
        return f"Successfully converted {input_path} to {format} format: {output_path}"
        
    except Exception as e:
        return f"Error converting video format: {str(e)}"


@mcp.tool()
async def optimize_quality(input_path: str, output_path: str, target_size_mb: Optional[int] = None) -> str:
    """
    优化视频质量和大小
    
    Args:
        input_path: 输入视频文件路径
        output_path: 输出视频文件路径
        target_size_mb: 目标文件大小（MB），None表示自动优化
    
    Returns:
        优化结果信息
    """
    try:
        ensure_moviepy()
        
        # 验证输入文件
        input_path = validate_video_path(input_path)
        output_path = ensure_output_dir(output_path)
        
        # 获取原始文件信息
        original_size = os.path.getsize(input_path) / (1024 * 1024)  # MB
        
        # 加载视频
        clip = VideoFileClip(input_path)
        duration = clip.duration
        
        # 计算目标比特率
        if target_size_mb:
            # 根据目标大小计算比特率
            target_bitrate = int((target_size_mb * 8 * 1024) / duration)  # kbps
            bitrate = f"{target_bitrate}k"
        else:
            # 自动优化：根据原始大小调整
            if original_size > 100:
                bitrate = "2000k"
            elif original_size > 50:
                bitrate = "3000k"
            else:
                bitrate = "5000k"
        
        # 优化并导出
        clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            bitrate=bitrate,
            verbose=False,
            logger=None
        )
        
        # 清理资源
        clip.close()
        
        # 获取输出文件大小
        output_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        compression_ratio = (original_size - output_size) / original_size * 100
        
        result = f"Successfully optimized video quality:\n"
        result += f"Original size: {original_size:.2f} MB\n"
        result += f"Optimized size: {output_size:.2f} MB\n"
        result += f"Compression: {compression_ratio:.1f}%\n"
        result += f"Output: {output_path}"
        
        return result
        
    except Exception as e:
        return f"Error optimizing video: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport='stdio')