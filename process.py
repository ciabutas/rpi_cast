import yt_dlp as youtube_dl
import os
import threading
import logging
import json
from pathlib import Path
logger = logging.getLogger("RaspberryCast")
volume = 0


def launchvideo(url, config, sub=False):
    setState("2")

    if config["new_log"]:
        os.system("sudo fbi -T 1 -a --noverbose images/processing.jpg")

    logger.info('Extracting source video URL...')
    out = return_full_url(url, sub=sub, slow_mode=config["slow_mode"])

    logger.debug("Full video URL fetched.")

    thread = threading.Thread(target=playWithVLC, args=(out, sub,),
            kwargs=dict(width=config["width"], height=config["height"],
                        new_log=config["new_log"]))
    thread.start()


def queuevideo(url, config, onlyqueue=False):
    logger.info('Extracting source video URL, before adding to queue...')

    out = return_full_url(url, sub=False, slow_mode=config["slow_mode"])

    logger.info("Full video URL fetched.")

    if getState() == "0" and not onlyqueue:
        logger.info('No video currently playing, playing video instead of \
adding to queue.')
        thread = threading.Thread(target=playWithVLC, args=(out, False,),
            kwargs=dict(width=config["width"], height=config["height"],
                        new_log=config["new_log"]))
        thread.start()
    else:
        if out is not None:
            with open('video.queue', 'a') as f:
                f.write(out+'\n')


def return_full_url(url, sub=False, slow_mode=False):
    logger.debug(f"Parsing source url for {url} with subs: {sub}")

    # Validate URL
    if not url:
        logger.error("Empty URL provided")
        return None

    # Handle direct media files
    media_extensions = (".avi", ".mkv", ".mp4", ".mp3", ".webm")
    if url.lower().endswith(media_extensions) or sub or ".googlevideo.com/" in url:
        logger.debug('Direct video URL, no need to use yt-dlp')
        return url

    ydl_opts = {
        'logger': logger,
        'noplaylist': True,
        'ignoreerrors': True,
        'quiet': True,
        'no_warnings': True,
        'format': 'best[height<=360]' if slow_mode else 'best[height<=1080]',
        'socket_timeout': 10,
        'retries': 3
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                # First try to extract info
                result = ydl.extract_info(url, download=False)
                if not result:
                    logger.error("No video information found")
                    return None

                # Handle both single videos and playlists
                video = result.get('entries', [result])[0]
                if not video:
                    logger.error("No video found in result")
                    return None

                # Get the URL and verify it
                video_url = video.get('url')
                if not video_url:
                    formats = video.get('formats', [])
                    if formats:
                        video_url = formats[-1].get('url')
                    
                if not video_url:
                    logger.error("No playable URL found")
                    return None

                logger.info(f"Successfully extracted video URL for {url}")
                return video_url

            except youtube_dl.utils.DownloadError as e:
                logger.error(f"YouTube-DL download error: {str(e)}")
                return None
            except youtube_dl.utils.ExtractorError as e:
                logger.error(f"YouTube-DL extractor error: {str(e)}")
                return None

    except Exception as e:
        logger.error(f"Unexpected error extracting video URL: {str(e)}")
        return None


def playlist(url, cast_now, config):
    logger.info("Processing playlist.")

    if cast_now:
        logger.info("Playing first video of playlist")
        launchvideo(url, config)  # Launch first video
    else:
        queuevideo(url, config)

    thread = threading.Thread(target=playlistToQueue, args=(url, config))
    thread.start()


def playlistToQueue(url, config):
    logger.info("Adding every videos from playlist to queue.")
    ydl_opts = {
        'logger': logger,
        'extract_flat': 'in_playlist',
        'ignoreerrors': True,
        'quiet': True,
        'no_warnings': True
    }
    
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(url, download=False)
        for i in result['entries']:
            logger.info("queuing video")
            if i != result['entries'][0]:
                queuevideo(i['url'], config)


def playWithVLC(url, sub, width="", height="", new_log=False):
    logger.info("Starting VLC now.")
    
    setState("1")
    if sub:
        os.system(
            f"cvlc --fullscreen '{url}' --sub-file subtitle.srt"
        )
    elif url is not None:
        os.system(
            f"cvlc --fullscreen '{url}'"
        )

    if getState() != "2":  # In case we are again in the launchvideo function
        setState("0")
        with open('video.queue', 'r') as f:
            # Check if there are videos in queue
            first_line = f.readline().replace('\n', '')
            if first_line != "":
                logger.info("Starting next video in playlist.")
                with open('video.queue', 'r') as fin:
                    data = fin.read().splitlines(True)
                with open('video.queue', 'w') as fout:
                    fout.writelines(data[1:])
                thread = threading.Thread(
                    target=playWithVLC, args=(first_line, False,),
                        kwargs=dict(width=width, height=height,
                                    new_log=new_log),
                )
                thread.start()
            else:
                logger.info("Playlist empty, skipping.")
                if new_log:
                    os.system("sudo fbi -T 1 -a --noverbose images/ready.jpg")


def setState(state):
    # Write to file so it can be accessed from everywhere
    try:
        with open('state.tmp', 'w') as f:
            f.write(str(state))
    except IOError as e:
        logger.error(f"Failed to write state: {e}")


def getState():
    with open('state.tmp', 'r') as f:
        return f.read().replace('\n', '')


def setVolume(vol):
    global volume
    if vol == "more":
        volume += 300
    if vol == "less":
        volume -= 300


def cleanup_files():
    """Clean up temporary files"""
    patterns = ['*.srt', '*.tmp', '*.part']
    for pattern in patterns:
        for file in Path('.').glob(pattern):
            try:
                file.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete {file}: {e}")
