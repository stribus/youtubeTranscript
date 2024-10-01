# analizador de videos do youtube:
#  - recebe um link de um video do youtube e retorna um resumo do que o video fala

import pytubefix
import ffmpeg
import os
import sys
import openai
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


def validate_url(url):
    if "https://www.youtube.com/watch?v=" in url:
        return True
    if "https://youtu.be/" in url:
        return True
    if "https://www.youtube.com/playlist?list=" in url:
        return True
    return False

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
def transcribe_audio_OpenAI(filename):
    audio_file = open(filename, "rb")
    response = openai.audio.transcriptions.create(
        model="whisper-1"
        ,file=audio_file        
    )
    audio_file.close()
    return response

def summary_OpenAI(text):
    response = openai.chat.Completion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você receber a transcrição do audio de um video. Por favor, resuma o que foi dito."},
            {"role": "user", "content": f"""transcrição do audio: 
                        '''
                        {text}
                        '''
                        """},
        ],
    )
    return response.choices[0].message

def transcribe_audio_Groq(filename):
    api_keyq = os.getenv('GROQ_API_KEY')
    if api_keyq is None:
        raise ValueError("A variável de ambiente GROQ_API_KEY não está definida.")
    with open(filename, "rb") as file:
        client = Groq(api_key=api_keyq)
        transcription = client.audio.transcriptions.create(
            file=(filename, file.read()),
            model="whisper-large-v3",
            language="pt",
            response_format="verbose_json",
        )  
    return transcription

def summary_Groq(text):
    api_keyq = os.getenv('GROQ_API_KEY')
    if api_keyq is None:
        raise ValueError("A variável de ambiente GROQ_API_KEY não está definida.")    
    client = Groq(api_key=api_keyq)
    summary = client.chat.completions.create(    
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": "Você receber a transcrição do áudio de um vídeo. Por favor, resuma o que foi dito."
                    },
                    {
                        "role": "user",
                        "content": f"""transcrição do audio: 
                        '''
                        {text}
                        '''
                        """
                    }
                ],
                max_tokens=8000,
                stream=False,
                temperature=1,
                top_p=1
    )
    return summary.choices[0].message.content

def save_file(text, filename="output"):
    if "." in filename:
        filename = filename.split(".")[0]
    filename = filename + ".txt"
    with open(filename, "w") as file:
        file.write(text)
        

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Falta o link do video")
        print("Uso: python analizador.py <link do video> [openai|groq]")
        sys.exit(1)

    url = sys.argv[1]
#     # url = "https://www.youtube.com/watch?v=Cw8A_yXR1M0"

    AI = "groq"
    if len(sys.argv) >= 3:
        AI = sys.argv[2]

    if AI != "openai" and AI != "groq":
        print("Opção invalida")
        sys.exit(1)

    #verifica se o link é valido
    if validate_url(url):
        arquivo = download_audio(url)
    # senão verifica se é um arquivo
    elif os.path.isfile(url):
        arquivo = url
    else:
        print("Link invalido")
        sys.exit(1)  
    
    #TODO: verificar se o arquivo é um audio
    #TODO: verificar o tamanho do arquivo e se ele exceder o limite, dividir em partes menores
    
    
    if AI == "openai":
        # Obter a chave da API do OpenAI
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key is None:
            raise ValueError("A variável de ambiente OPEN_API_KEY não está definida.")
        os.environ["OPENAI_API_KEY"] = openai_api_key
        transcricao = transcribe_audio_OpenAI(arquivo)
    else:
        transcricao = transcribe_audio_Groq(arquivo)

    #verifica se transcricao tem text
    if hasattr(transcricao, 'text'):
        save_file(transcricao.text, arquivo)
    else:
        save_file(transcricao, arquivo)
        print("Erro na transcrição")
        sys.exit(1)
        
    print(transcricao.text)

    if sys.argv[3] == "-r":
        if AI == "openai":
            resumo = summary_OpenAI(transcricao.text)
        else:
            resumo = summary_Groq(transcricao.text)
    
    

    print(resumo)


    save_file(resumo, f"""resumo_{arquivo}""")   