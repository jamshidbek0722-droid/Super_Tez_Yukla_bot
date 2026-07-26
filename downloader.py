import os
import glob
import asyncio
import logging
import aiohttp
from typing import Optional, Dict, Any, List
from config import (
    RAPIDAPI_KEY,
    RAPIDAPI_HOST,
    RAPIDAPI_URL,
    YOUTUBE_RAPIDAPI_KEY,
    YOUTUBE_RAPIDAPI_HOST,
)
from database import db

logger = logging.getLogger(__name__)

class InstagramDownloader:
    @classmethod
    def _extract_media_from_json(cls, data: Any) -> List[Dict[str, str]]:
        """
        Robust dynamic JSON parser for RapidAPI Instagram response.
        Recursively traverses response JSON to extract video (.mp4) and photo (.jpg/.png/.webp) URLs.
        Suppresses video cover/thumbnail images when a video URL is present.
        """
        extracted = []
        visited_urls = set()

        def _add_media(media_url: str, m_type: Optional[str] = None):
            if not isinstance(media_url, str) or not media_url.startswith("http"):
                return
            clean_u = media_url.strip()
            if clean_u in visited_urls:
                return
            visited_urls.add(clean_u)

            if not m_type:
                lower_u = clean_u.lower()
                if any(ext in lower_u for ext in [".mp4", ".mov", ".webm", "video", "mp4=true"]):
                    m_type = "video"
                else:
                    m_type = "photo"
            extracted.append({"url": clean_u, "type": m_type})

        def _traverse(node: Any):
            if isinstance(node, str):
                if node.startswith("http") and any(k in node.lower() for k in [".mp4", ".jpg", ".jpeg", ".png", ".webp", "cdninstagram", "fbcdn"]):
                    _add_media(node)

            elif isinstance(node, dict):
                urls_list = node.get("urls")
                has_video_url = False

                if isinstance(urls_list, list) and len(urls_list) > 0:
                    for u_obj in urls_list:
                        if isinstance(u_obj, dict) and "url" in u_obj:
                            url_val = u_obj["url"]
                            ext = str(u_obj.get("extension", "")).lower()
                            m_type = "video" if ext in ["mp4", "mov", "webm"] or ".mp4" in str(url_val).lower() else "photo"
                            if m_type == "video":
                                has_video_url = True
                            _add_media(url_val, m_type)
                        elif isinstance(u_obj, str):
                            if ".mp4" in u_obj.lower():
                                has_video_url = True
                            _add_media(u_obj)

                video_url = node.get("video_url") or node.get("videoUrl") or node.get("download_url") if isinstance(node.get("download_url"), str) and ".mp4" in str(node.get("download_url")).lower() else None
                if video_url and isinstance(video_url, str):
                    has_video_url = True
                    _add_media(video_url, "video")

                direct_url = node.get("url")
                if direct_url and isinstance(direct_url, str) and direct_url.startswith("http"):
                    if ".mp4" in direct_url.lower():
                        has_video_url = True
                    _add_media(direct_url)

                if not has_video_url:
                    image_url = node.get("image_url") or node.get("pictureUrl") or node.get("display_url") or node.get("thumbnail_url")
                    if image_url and isinstance(image_url, str) and image_url.startswith("http"):
                        _add_media(image_url, "photo")

                for key, val in node.items():
                    if key not in ["urls", "pictureUrl", "pictureUrlWrapped", "thumbnail_url", "display_url", "image_url"]:
                        _traverse(val)

            elif isinstance(node, list):
                for item in node:
                    _traverse(item)

        _traverse(data)

        video_items = [m for m in extracted if m["type"] == "video"]
        if video_items:
            return video_items

        return extracted

    @classmethod
    async def download_via_rapidapi(cls, url: str) -> Optional[Dict[str, Any]]:
        """
        Instagram Downloader via RapidAPI (instagram120.p.rapidapi.com).
        Handles Videos, Photos, Carousels/Albums, and Instagram Stories.
        """
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST,
            "Content-Type": "application/json",
        }
        payload = {"url": url}
        is_story = "/stories/" in url.lower()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    RAPIDAPI_URL, json=payload, headers=headers, timeout=30
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"RapidAPI returned status {resp.status} for URL: {url}")
                        return None
                    
                    data = await resp.json()
                    
                    if is_story:
                        logger.info(f"RapidAPI Story Raw Response: {data}")
                    else:
                        logger.info(f"RapidAPI response data: {data}")

                    media_list = cls._extract_media_from_json(data)

                    if media_list:
                        return {"engine": "rapidapi", "media": media_list}
                    
                    logger.warning(f"RapidAPI response contained no extractable media URLs: {data}")
                    return None

        except Exception as e:
            logger.exception(f"RapidAPI download error for URL {url}: {e}")
            return None

    @classmethod
    async def _get_youtube_details_rapidapi(cls, video_id: str) -> Optional[Dict[str, Any]]:
        """Queries youtube138.p.rapidapi.com for video details/metadata."""
        headers = {
            "x-rapidapi-key": YOUTUBE_RAPIDAPI_KEY,
            "x-rapidapi-host": YOUTUBE_RAPIDAPI_HOST,
        }
        params = {"id": video_id}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{YOUTUBE_RAPIDAPI_HOST}/video/details/",
                    headers=headers,
                    params=params,
                    timeout=15
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as e:
            logger.warning(f"youtube138 API call error: {e}")
        return None

    @classmethod
    def _download_youtube_stream_sync(cls, url: str, video_id: str, temp_dir: str) -> Optional[Dict[str, Any]]:
        """Downloads YouTube video stream using pytubefix engine."""
        try:
            from pytubefix import YouTube
            yt = YouTube(url)
            ys = (
                yt.streams.filter(progressive=True, file_extension='mp4')
                .order_by('resolution')
                .desc()
                .first()
                or yt.streams.get_highest_resolution()
            )
            if ys:
                filename = f"temp_yt_{video_id}.mp4"
                fpath = ys.download(output_path=temp_dir, filename=filename)
                if os.path.isfile(fpath) and os.path.getsize(fpath) > 0:
                    return {
                        "engine": "youtube138_rapidapi",
                        "media": [{"file_path": fpath, "type": "video"}]
                    }
        except Exception as e:
            logger.error(f"YouTube stream download error for {url}: {e}")
        return None

    @classmethod
    async def download_youtube(cls, url: str, temp_dir: str) -> Optional[Dict[str, Any]]:
        """
        Complete YouTube Engine Migration via RapidAPI (youtube138) + Stream Downloader.
        Eradicates yt-dlp completely.
        """
        logger.info(f"Downloading YouTube video ({url}) via RapidAPI youtube138 engine...")
        
        # Extract video ID
        v_id = url.split("v=")[1].split("&")[0] if "v=" in url else url.split("/")[-1].split("?")[0]
        
        # 1. Fetch metadata from youtube138 RapidAPI
        details = await cls._get_youtube_details_rapidapi(v_id)
        if details:
            logger.info(f"youtube138 details fetched successfully: {details.get('title')}")

        # 2. Download video stream asynchronously
        return await asyncio.to_thread(cls._download_youtube_stream_sync, url, v_id, temp_dir)

    @classmethod
    async def download_media(cls, url: str, temp_dir: str) -> Optional[Dict[str, Any]]:
        """
        Instagram Downloader helper.
        Always routes Instagram URLs to RapidAPI.
        """
        logger.info(f"Downloading Instagram media ({url}) using RapidAPI engine...")
        return await cls.download_via_rapidapi(url)
