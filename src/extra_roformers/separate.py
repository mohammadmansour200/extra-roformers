import logging
import os
import shutil
from pathlib import Path

import validators
from audio_separator.separator import Separator

from extra_roformers.downloader import Downloader
from extra_roformers.ffmpeg_utils import FFMPEGUtils

logging.getLogger("audio_separator").setLevel(logging.WARNING)

video_audio_track_ext_map = {
    ".mp4": "aac",
    ".m4v": "aac",
    ".webm": "opus",
    ".flv": "aac",
    ".mkv": "opus",
    ".mov": "aac",
    ".avi": "mp3",
    ".ts": "aac",
    ".ogg": "vorbis",
}

i18n = {
    "en": {
        "preparing": "Preparing files...",
        "error_no_files": "Please provide files for processing.",
        "saving_video": "Saving video in {path}",
        "saving_audio": "Saving audio in {path}",
    },
    "ar": {
        "preparing": "جاري تحضير الملفات من أجل معالجتها...",
        "error_no_files": "لا يوجد ملفات للمعالجة.",
        "saving_video": "جاري حفظ الفيديو في {path}",
        "saving_audio": "جاري حفظ الصوت في {path}",
    },
}


def get_output_format(input_filename):
    ext = Path(input_filename).suffix.lower()

    if ext in video_audio_track_ext_map:
        target_format = video_audio_track_ext_map[ext]
    elif ext in [".wav", ".flac"]:
        target_format = ext.replace(".", "")
    else:
        target_format = "mp3"

    return target_format


def extra_separator(
    media_paths: list[str],
    download_media_type: str,
    download_quality: str,
    output_dir: str,
    model: str = "vocals_mel_band_roformer.ckpt",
    lang: str = "ar",
):
    """
    Separates vocals from a list of media files (audio/video), using audio-separator, and replaces
    the audio track in video files with the extracted vocals if file was a video.

    This function supports both local files and remote URLs (e.g., YouTube links). It handles:
    - Downloading remote media using yt-dlp
    - Performing source separation using Demucs (vocal isolation)
    - For video: replacing the original audio with vocals using ffmpeg
    - Cleaning up intermediate files and keeping only the final output
    - Segmented processing in case of low-end devices

    Parameters:
        media_paths (list[str]): List of file paths or URLs pointing to audio/video files.
        download_media_type (str): Either "audio" or "video". Determines post-processing behavior.
        download_quality (str): Quality level for yt-dlp downloading ("high", "low", "medium").
        output_dir (str): Path to directory where final results will be saved.
        model (str): model to be used
        lang (str): Language for logs

    Notes:
        - Requires `ffmpeg`, and internet access for remote URLs.
        - For audio files, only the isolated vocal track is kept in mp3 format.
        - For video files, a new `.mp4` is generated with vocals replacing original audio.
        - Temporary files are stored in a `tmp/` subfolder inside the output directory and deleted after completion.

    Example:
        extra_separator(
            files=["https://www.youtube.com/watch?v=123", "local_song.mp3"],
            download_media_type="audio",
            download_quality="medium",
            output_dir="output"
        )
    """
    t = i18n[lang]

    abs_output_dir = os.path.abspath(output_dir)
    temp_output_dir = os.path.join(abs_output_dir, "tmp")
    model_output_dir = os.path.join(abs_output_dir, model)

    # Create directories if they don't exist
    os.makedirs(temp_output_dir, exist_ok=True)
    os.makedirs(model_output_dir, exist_ok=True)

    ffmpeg_utils = FFMPEGUtils()

    files_to_process = []

    # --- Preparing files for processing ---
    print(t["preparing"])

    if not media_paths:
        raise Exception(t["error_no_files"])

    downloader = Downloader(
        output_dir=temp_output_dir, media_type=download_media_type, quality=download_quality
    )
    for url in media_paths:
        is_url = validators.url(url)
        if is_url:
            downloaded_file_path = downloader.download(url=url)

            files_to_process.append(downloaded_file_path)
        else:
            files_to_process.append(os.path.abspath(url))

    # --- Demucs model inference ---
    separator = Separator(
        output_dir=model_output_dir,
        output_single_stem="Vocals",
    )
    separator.load_model(model)

    for file_path in files_to_process:
        file_path_obj = Path(file_path)

        original_file_ext = file_path_obj.suffix.lower()
        base_filename = file_path_obj.stem

        # --- Separate Audio ---
        output_names = {
            "Vocals": f"{base_filename}_vocals",
        }
        separated_files = separator.separate(file_path, output_names)

        vocal_file_name = separated_files[0]
        vocal_output_path = os.path.join(model_output_dir, vocal_file_name)

        # --- Post-Processing ---
        target_format = get_output_format(file_path)
        processed_file_path = os.path.join(
            temp_output_dir, f"{output_names['Vocals']}.{target_format}"
        )

        ffmpeg_utils.convert(vocal_output_path, processed_file_path)

        is_video = ffmpeg_utils.is_video(file_path)
        if is_video:
            print(t["saving_video"].format(path=abs_output_dir))

            final_video_output_path = os.path.join(
                abs_output_dir, f"{base_filename}_vocals{original_file_ext}"
            )

            ffmpeg_utils.replace_video_audio(
                input_video_path=file_path,
                input_audio_path=processed_file_path,
                final_output_path=final_video_output_path,
            )
        else:
            print(t["saving_audio"].format(path=abs_output_dir))

            final_audio_output_path = os.path.join(abs_output_dir, vocal_file_name)
            shutil.move(processed_file_path, final_audio_output_path)

    # --- Cleanup ---
    if os.path.exists(temp_output_dir):
        shutil.rmtree(temp_output_dir)
    if os.path.exists(model_output_dir):
        shutil.rmtree(model_output_dir)
