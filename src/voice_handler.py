from google.cloud import texttospeech
import subprocess
import collections


class VoiceHandler(texttospeech.TextToSpeechClient):

    def __init__(self, news_id, news_txt, wavenet_voice_name):
        super().__init__()

        self.client = self
        self.news_id = news_id
        self.news_txt = news_txt
        self.voice_name = wavenet_voice_name  # TODO en-GB-Wavenet-B
        self.voice_names = ["en-GB-Wavenet-A", "en-GB-Wavenet-B"]*100

        self.voice = self.__create_voice()

    @staticmethod
    def __create_ffmpeg_concat_input(voice_files: list):

        concat_input = ["concat:"]
        for file in voice_files[:-1]:
            concat_input.append(file)
            concat_input.append("|")
        concat_input.append(voice_files[-1])
        return "".join(concat_input)

    def concat_news_voices(self, voice_files: list):
        output = "vid_sources/" + self.news_id + ".mp3"
        concat_input = self.__create_ffmpeg_concat_input(voice_files)
        subprocess.run([
            "ffmpeg",
            "-y",
            "-i",
            concat_input,
            "-c:a",
            "copy",
            f"{output}"
        ])
        return output

    def __synthesize_voice(self, news_txt):

        input_text = texttospeech.SynthesisInput(text=news_txt)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            ssml_gender=texttospeech.SsmlVoiceGender.SSML_VOICE_GENDER_UNSPECIFIED,
            name=self.voice_name)

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.9
        )

        response = self.client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
        return response

    def __create_voice(self):

        if type(self.news_txt) is dict:
            mp3_files = []
            for part_id, part in self.news_txt.items():
                file_id = self.news_id + "_" + part_id
                mp3_file = "vid_sources/" + file_id + ".mp3"
                voice_chunk = self.__synthesize_voice(part)
                with open(mp3_file, "+wb") as out:
                    out.write(voice_chunk.audio_content)
                mp3_files.append(mp3_file)
            concatted_mp3_file = self.concat_news_voices(mp3_files)
            return concatted_mp3_file
        else:
            voice_chunk = self.__synthesize_voice(self.news_txt)
            mp3_file = "vid_sources/" + self.news_id + ".mp3"
            # print(self.news_id)
            with open(mp3_file, "+wb") as out:
                out.write(voice_chunk.audio_content)
            return mp3_file
