# analizador de videos do youtube:
#  - recebe um link de um video do youtube e retorna um resumo do que o video fala

import pytubefix
import ffmpeg
import os
import sys
import openai
from dotenv import load_dotenv

load_dotenv()
#pega a chave da api do openai do arquivo .env
os.environ["OPENAI_API_KEY"] = os.getenv("OPEN_API_KEY")



#baixa o audio do youtube
def download_audio(video_url):
    yt = pytubefix.YouTube(video_url)
    # stream  = yt.streams.filter(only_audio=True).first()
    stream  = yt.streams.first()
    #retira os caracters especiais e espaços do nome do video
    filename = ''.join(e for e in yt.title if e.isalnum())
    ffmpeg.input(stream.url).output(filename+'.wav').run()
    return filename+'.wav'

#transcreve o audio
def transcribe_audio(filename):
    audio_file = open(filename, "rb")
    response = openai.audio.transcriptions.create(
        model="whisper-1"
        ,file=audio_file        
    )
    audio_file.close()
    return response

url = sys.argv[1]
# url = "https://www.youtube.com/watch?v=Cw8A_yXR1M0"

arquivo = download_audio(url)
transcricao = transcribe_audio(arquivo)

print(transcricao)
print(transcricao.text)

