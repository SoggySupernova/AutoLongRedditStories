import sys
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": r"C:\\Program Files\\ImageMagick-7.1.2-Q16-HDRI\\magick.exe"}) # todo: find binary automatically


def subtitle_generator(txt):
    """
    Generates a TextClip with filled text and an outline (stroke).
    """
    return TextClip(
        txt,
        font="input/Montserrat-Bold.otf",
        fontsize=128,
        color="white",
        stroke_color="black",
        stroke_width=30,
        method="caption",
        size=(video.w * 0.9, None),
        align="center"
    )


def white_subtitle_generator(txt):
    """
    Generates a TextClip with filled text and an outline (stroke).
    """
    return TextClip(
        txt,
        font="input/Montserrat-Bold.otf",
        fontsize=128,
        color="white",
        method="caption",
        size=(video.w * 0.9, None),
        align="center"
    )




def main(input_video, input_srt, output_video):
    global video
    video = VideoFileClip(input_video)

    subtitles = SubtitlesClip(input_srt, subtitle_generator)
    subtitles = subtitles.set_position(
        ("center", video.h * 0.5)
    )


    whitesubtitles = SubtitlesClip(input_srt, white_subtitle_generator)
    whitesubtitles = whitesubtitles.set_position(
        ("center", video.h * 0.514) # it needs to be a little farther down for some reason
    )

    final = CompositeVideoClip([video, subtitles, whitesubtitles]) # I learned this trick from scratch hehe
    final.write_videofile(
        output_video,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True
    )


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("Usage: python add_subtitles.py input.mp4 subtitles.srt output.mp4")

    main(sys.argv[1], sys.argv[2], sys.argv[3])
