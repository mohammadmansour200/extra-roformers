import os
import shutil
import subprocess


class FFMPEGUtils:
    """
    FFmpeg utils used in separation.

    When created, FFMPEG binary path will be checked,
    raising exception if not found. Such path could be inferred using
    `FFMPEG_PATH` environment variable.
    """

    def __init__(self) -> None:
        """
        Default constructor, ensure FFMPEG binaries are available.

        Raises:
            ValueError:
                If ffmpeg or ffprobe is not found.
        """
        for binary in ("ffmpeg", "ffprobe"):
            if shutil.which(binary) is None:
                raise Exception("ffmpeg_utils:{} binary not found".format(binary))

    def replace_video_audio(self, input_video_path: str, input_audio_path: str, final_output_path: str):
        try:
            subprocess.run([
                "ffmpeg",
                "-y",
                "-loglevel", "quiet",
                "-an",
                "-i", input_video_path,
                "-i", input_audio_path,
                "-map", "0:v",
                "-map", "1:a",
                "-c:v", "copy",
                "-c:a", "copy",
                final_output_path, ], check=True)
        except Exception as e:
            raise Exception(
                "ffmpeg_utils:An error occurred with ffmpeg (see ffmpeg output below)\n\n{}".format(
                    e
                )
            )

    def is_video(self, path: str) -> bool:
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                 '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True, check=True
            )
            return 'video' in result.stdout
        except Exception as e:
            return False

    def convert_to_audio_format(self, output_dir: str, output_name: str, audio_format: str):
        processed_demucs_file_path = os.path.join(output_dir, f"{output_name}.wav")
        final_output_file_path = os.path.join(output_dir,
                                              f"{output_name}.{'mp3' if audio_format is None else audio_format}")
        try:
            subprocess.run([
                "ffmpeg",
                "-y",
                "-loglevel", "quiet",
                "-i", processed_demucs_file_path,
                final_output_file_path
            ]
                , check=True)
        except Exception as e:
            raise Exception(
                "ffmpeg_utils:An error occurred with ffmpeg (see ffmpeg output below)\n\n{}".format(
                    e
                )
            )
