import os
import sys
import shutil
import glob
import asyncio
import logging

logger = logging.getLogger(__name__)

def get_ffmpeg_cmd() -> str:
    """Finds available ffmpeg binary on system or package binaries."""
    # 1. Check system PATH
    cmd = shutil.which("ffmpeg")
    if cmd:
        return cmd
    
    # 2. Check site-packages imageio_ffmpeg binaries
    site_packages = os.path.join(sys.prefix, "Lib", "site-packages", "imageio_ffmpeg", "binaries")
    if os.path.exists(site_packages):
        exes = glob.glob(os.path.join(site_packages, "ffmpeg*.exe"))
        if exes:
            return exes[0]

    # 3. Fallback to CapCut or local AppData paths if available
    appdata_local = os.getenv("LOCALAPPDATA", "")
    if appdata_local:
        capcut_exes = glob.glob(os.path.join(appdata_local, "CapCut", "Apps", "*", "ffmpeg.exe"))
        if capcut_exes:
            return capcut_exes[-1]

    return "ffmpeg"

async def extract_audio_ffmpeg(input_mp4: str, output_mp3: str) -> bool:
    """
    Extracts MP3 audio from input video file using FFmpeg.
    Command: ffmpeg -y -i <input_mp4> -vn -acodec libmp3lame -q:a 2 <output_mp3>
    """
    ffmpeg_exe = get_ffmpeg_cmd()
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", input_mp4,
        "-vn",
        "-acodec", "libmp3lame",
        "-q:a", "2",
        output_mp3
    ]
    logger.info(f"Running audio extraction command: {' '.join(cmd)}")
    
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        logger.warning(f"FFmpeg libmp3lame failed (code {proc.returncode}), trying default mp3 encoder...")
        cmd_fallback = [
            ffmpeg_exe,
            "-y",
            "-i", input_mp4,
            "-vn",
            "-q:a", "2",
            output_mp3
        ]
        proc_f = await asyncio.create_subprocess_exec(
            *cmd_fallback,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr_f = await proc_f.communicate()
        if proc_f.returncode != 0:
            logger.error(f"FFmpeg fallback audio extraction failed: {stderr_f.decode(errors='ignore')}")
            return False
            
    return os.path.exists(output_mp3) and os.path.getsize(output_mp3) > 0

async def convert_video_note_ffmpeg(input_mp4: str, output_note_mp4: str) -> bool:
    r"""
    Converts video into a Telegram Video Note (cropped 1:1, scaled to 640x640).
    Command: ffmpeg -y -i <input_mp4> -vf "crop=min(iw\,ih):min(iw\,ih),scale=640:640" -c:v libx264 -crf 23 -preset ultrafast -c:a aac <output_note_mp4>
    """
    ffmpeg_exe = get_ffmpeg_cmd()
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", input_mp4,
        "-vf", "crop=min(iw\\,ih):min(iw\\,ih),scale=640:640",
        "-c:v", "libx264",
        "-crf", "23",
        "-preset", "ultrafast",
        "-c:a", "aac",
        output_note_mp4
    ]
    logger.info(f"Running video note conversion command: {' '.join(cmd)}")

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        logger.error(f"FFmpeg video note conversion failed (code {proc.returncode}): {stderr.decode(errors='ignore')}")
        return False

    return os.path.exists(output_note_mp4) and os.path.getsize(output_note_mp4) > 0
