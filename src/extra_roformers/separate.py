import os
import shutil
from pathlib import Path

import validators
from audio_separator.separator import Separator

from extra_roformers.downloader import Downloader
from extra_roformers.ffmpeg_utils import FFMPEGUtils

import logging
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
    ".ogg": "vorbis"
}

i18n = {
    "en": {
        "preparing": "Preparing files...",
        "error_no_files": "Please provide files for processing.",
        "saving_video": "Saving video in {path}",
        "saving_audio": "Saving audio in {path}"
    },
    "ar": {
        "preparing": "جاري تحضير الملفات من أجل معالجتها...",
        "error_no_files": "لا يوجد ملفات للمعالجة.",
        "saving_video": "جاري حفظ الفيديو في {path}",
        "saving_audio": "جاري حفظ الصوت في {path}"
    }
}


def get_output_format(input_filename):
    ext = Path(input_filename).suffix.lower()

    if ext in video_audio_track_ext_map:
        target_format = video_audio_track_ext_map[ext]
    elif ext in ['.wav', '.flac']:
        target_format = ext.replace('.', '')
    else:
        target_format = "mp3"

    return target_format

def extra_separator(
        files: list[str],
        download_format: str,
        quality: str,
        output_dir: str,
        model: str = 'vocals_mel_band_roformer.ckpt',
        lang: str = "ar"
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
        files (list[str]): List of file paths or URLs pointing to audio/video files.
        download_format (str): Either "audio" or "video". Determines post-processing behavior.
        quality (str): Quality level for yt-dlp downloading ("high", "low", "medium").
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
            media_type="audio",
            quality="medium",
            output_dir="output"
        )
    """
    t = i18n[lang]

    abs_output_dir = os.path.abspath(output_dir)
    temp_output_dir = os.path.join(abs_output_dir, 'tmp')
    separator_output_dir = os.path.join(abs_output_dir, model)

    # Create directories if they don't exist
    os.makedirs(temp_output_dir, exist_ok=True)
    os.makedirs(separator_output_dir, exist_ok=True)

    ffmpeg_utils = FFMPEGUtils()

    files_to_be_processed = []

    # --- Preparing files for processing ---
    print(t["preparing"])

    if not files:
        raise Exception(t["error_no_files"])

    downloader = Downloader(
        output_dir=temp_output_dir,
        media_type=download_format,
        quality=quality
    )
    for index, url in enumerate(files):
        is_url = validators.url(url)
        if is_url:
            downloaded_file_path = downloader.download(url=url)

            files_to_be_processed.append(downloaded_file_path)
        else:
            files_to_be_processed.append(os.path.abspath(url))

    # --- Demucs model inference ---
    separator = Separator(
        output_dir=separator_output_dir,
        output_single_stem='Vocals',
    )
    separator.load_model(model)

    # --- Postprocess ---
    for file_path in files_to_be_processed:
        file_path_obj = Path(file_path)
        original_file_ext = file_path_obj.suffix.lower()
        vocal_output_name = file_path_obj.stem

        # --- Separate Audio ---
        target_format = get_output_format(file_path)
        separated_files = separator.separate(file_path, output_format=target_format.upper(),
                                             output_filename=f"{vocal_output_name}_vocals")

        vocal_file_name = separated_files[0]
        vocal_output_path = os.path.join(separator_output_dir, vocal_file_name)

        # --- Post-Processing ---
        is_video = ffmpeg_utils.is_video(file_path)

        if is_video:
            print(t["saving_video"].format(path=abs_output_dir))

            final_video_output_path = os.path.join(abs_output_dir, f"{vocal_output_name}_vocals{original_file_ext}")

            ffmpeg_utils.replace_video_audio(
                input_video_path=file_path,
                input_audio_path=vocal_output_path,
                final_output_path=final_video_output_path
            )
        else:
            print(t["saving_audio"].format(path=abs_output_dir))

            final_audio_output_path = os.path.join(abs_output_dir, vocal_file_name)
            shutil.move(vocal_output_path, final_audio_output_path)

    # --- Cleanup ---
    if os.path.exists(temp_output_dir):
        shutil.rmtree(temp_output_dir)
    if os.path.exists(separator_output_dir):
        shutil.rmtree(separator_output_dir)
