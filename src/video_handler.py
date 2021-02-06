from voice_handler import VoiceHandler
from PIL import Image, ImageDraw, ImageFont
import subprocess
import collections
from datetime import datetime as dt
import requests
import configparser
import textwrap


class VideoHandler:
    def __init__(self, rss_feed, vid_parts: dict):
        self.rss_feed = rss_feed
        self.vid_parts = vid_parts

    def __create_ffmpeg_inputs(self, videos: list, add_transition=True):
        # "-i 2015.mp4 -i t1.mp4 -i 5379.mp4 -i t1.mp4 -i 5655.mp4"
        input_list = []
        if not add_transition:
            for vid in videos:
                input_list.append("-i")
                input_list.append(vid)
        else:
            for vid in videos[:-1]:
                input_list.append("-i")
                input_list.append(vid)
                input_list.append("-i")
                input_list.append(self.vid_parts["transition"])
            input_list.append("-i")
            input_list.append(videos[-1])
        return input_list

    @staticmethod
    def __create_ffmpeg_filter_complex(vid_number: int, add_transition=True):

        vid_orders = vid_number

        if add_transition:
            vid_orders += vid_orders - 1

        tail = f"concat=n={vid_orders}:v=1:a=1[v][a]"
        scale_filter = []
        concat_filter = []
        for vid_id in range(vid_orders):
            scale_part = (
                f"[{vid_id}:v]scale=1920:1080:force_original_aspect_ratio=1[v{vid_id}]"
            )
            concat_part = f"[v{vid_id}][{vid_id}:a]"
            scale_filter.append(scale_part)
            concat_filter.append(concat_part)
        scale_filter_txt = ";".join(scale_filter)
        concat_filter_txt = "".join(concat_filter)
        complex_filter = [
            "-filter_complex",
            f"{scale_filter_txt};{concat_filter_txt}{tail}",
        ]
        return complex_filter

    # def __generate_video_metadata(self):
    #
    #     vid_title = f"{dt.strftime(dt.now(), '%d/%m/%Y')} Trending News in The Netherlands."
    #     desc = f"{dt.strftime(dt.now(), '%d/%m/%Y')} Trending News in The Netherlands."
    #     for news in self.rss_feed.values():
    #         title, url, excerpt = news["title"], news["url"], news["content"]["txt"]
    #         desc += "\n" + title + "\n" + "-" * 10 + "\n" + excerpt + "\n" + url + "\n" + "-" * 30 # todo test this bitch
    #     # save to file
    #     info_file = "vid_sources/vid_info.txt"
    #     with open(info_file, "+w") as file:
    #         file.writelines(f"Title: {vid_title}\n")
    #         file.writelines("*"*15 + "\n")
    #         file.writelines(desc)
    #     info = {"title": vid_title, "desc": desc, "info_file": info_file}
    #     return info

    @staticmethod
    def __download_news_image(news_id, img_url):
        print(img_url)
        res = requests.get(img_url)
        if res.ok:
            img_file = news_id + f".{img_url.split('.')[-1]}"
            file_path = "vid_sources/" + img_file
            with open(file_path, "+wb") as file:
                file.write(res.content)
            return file_path
        else:
            return False

    def __determine_appt_font_size(self, news_title, width):
        max_chr_length = width / len(news_title)
        im = Image.new("RGB", (100, 100), (0, 0, 0, 0))
        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype(self.vid_parts["font"], size=100)
        w, h = draw.textsize("a", font=font)
        appt_font_factor = round(max_chr_length / w, 1)
        appt_font_size = font.size * appt_font_factor

        if appt_font_size > 650:
            appt_font_size = 650

        return appt_font_size

    def __create_title_image(self, width, news_title, out):
        para = textwrap.wrap(news_title, width=80)
        max_w, max_h = width - 100, 60
        im = Image.new('RGB', (max_w, max_h),  "#153e7d")
        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype(self.vid_parts["font"], 18)
        current_h, pad = 5, 1
        for line in para:
            w, h = draw.textsize(line, font=font)
            draw.text((round((max_w - w) / 2), current_h), line, font=font, fill="white")
            current_h += h + pad
        im.save(out)
        return out

    def __add_title_to_image(self, news_title, news_img):
        print(news_img)
        im = Image.open(news_img)
        # draw = ImageDraw.Draw(im)
        # font_color = "white"
        max_w, max_h = im.size
        # font_size = self.__determine_appt_font_size(news_title=news_title, width=max_w)
        # title_font = ImageFont.truetype(self.config["font"], size=int(font_size))
        file_name = news_img
        # w, h = draw.textsize(news_title.capitalize(), font=title_font)
        # current_h = ((max_h / 2.5) - h) / 2
        # current_w = (max_w - w) / 2
        # button_size = (w + 10, h + 10)
        # button_img = Image.new("RGBA", button_size, "black")
        # button_draw = ImageDraw.Draw(button_img)
        # button_draw.text(
        #     (5, 1), news_title.capitalize(), font=title_font, fill=font_color
        # )
        # im.paste(
        #     button_img,
        #     (int(round(current_w)), (0, int(round(max_h - button_size[-1])))),
        # )
        # im.save(file_name)
        title_img = Image.open(self.__create_title_image(max_w, news_title, "vid_sources/title.jpg"))
        title_img_size = title_img.size
        im.paste(title_img, (0, int(round(max_h - title_img_size[-1])) - 5))
        im.save(file_name)
        return file_name

    def __add_background_music(self, news_video, out_video):
        subprocess.run(
            [
                "ffmpeg",
                "-i",
                news_video,
                "-stream_loop",
                "1",
                "-i",
                self.vid_parts["background_music"],
                "-filter_complex",
                "[1:a]volume=0.5,apad[A];[0:a][A]amerge[out]",
                "-c:v",
                "copy",
                "-map",
                "0:v",
                "-map",
                "[out]",
                "-y",
                "-shortest",
                out_video,
            ]
        )
        return True

    def __ffmpeg_worker(self, command_type, **kwargs):

        concat = 1
        create = 2
        output_file = kwargs["output"]
        add_transition = False
        if command_type == concat:
            if kwargs["video_type"] != "final":
                add_transition = True
            inputs = self.__create_ffmpeg_inputs(kwargs["videos"], add_transition)
            filter_complex = self.__create_ffmpeg_filter_complex(len(kwargs["videos"]), add_transition)
            command = [
                "ffmpeg",
                *inputs,
                *filter_complex,
                "-map",
                "[v]",
                "-map",
                "[a]",
                "-vsync",
                "2",
                "-y",
                output_file,
            ]
            subprocess.run(command)
            with open("vid_sources/ffmpegcommand.txt", "+a") as file:
                file.writelines("\n" + " ".join(command))
            return True

        elif command_type == create:
            # -vf pad="width=ceil(iw/2)*2:height=ceil(ih/2)*2"
            command = [
                    "ffmpeg",
                    "-y",
                    "-loop",
                    "1",
                    "-i",
                    f"{kwargs['image_file']}",
                    "-i",
                    f"{kwargs['voice_file']}",
                    "-aspect",
                    "1920:1080",
                    "-c:a",
                    "copy",
                    "-c:v",
                    "libx264",
                    "-vf",
                    "scale=1920:1080,pad=width=ceil(iw/2)*2:height=ceil(ih/2)*2",
                    "-shortest",
                    f"{output_file}",
                ]
            subprocess.run(command)

            return True

    def concat_news_videos(self, videos: list):
        file = "vid_sources/_news.mp4"  # Todo date of the day

        self.__ffmpeg_worker(
            command_type=1,
            video_type="news",
            videos=videos,
            output=file,
        )
        output_file = "vid_sources/news.mp4"
        self.__add_background_music(file, output_file)
        return output_file

    def concat_final_video(self, news_video):
        output_file = "vid_sources/finished.mp4"  # Todo date of the day
        videos = [
            self.vid_parts["intro"],
            news_video,
            self.vid_parts["outro"],
        ]
        self.__ffmpeg_worker(
            command_type=1,
            video_type="final",
            videos=videos,
            output=output_file,
        )
        return output_file

    def create_news_video(self):
        news_videos = []
        counter = 0
        voice_names = ["en-GB-Wavenet-A", "en-GB-Wavenet-B"] * 100
        for news_id, content in self.rss_feed.items():
            news_txt = content["content"]["txt"]
            news_img = self.__download_news_image(
                news_id, content["content"]["img_url"]
            )
            self.__add_title_to_image(content["title"], news_img)
            voice = VoiceHandler(
                news_id=news_id, news_txt=news_txt, wavenet_voice_name=voice_names[counter]
            )  # todo config dosyasından al
            output = "vid_sources/" + news_id + ".mp4"
            self.__ffmpeg_worker(
                command_type=2,
                image_file=news_img,
                voice_file=voice.voice,
                output=output,
            )
            news_videos.append(output)
            counter += 1

        news_vid = self.concat_news_videos(news_videos)
        # news_vid = 'vid_sources/_news.mp4'
        final_vid = self.concat_final_video(news_vid)
        return final_vid
