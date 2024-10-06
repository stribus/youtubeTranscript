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

def validateUrl(url):
    if "https://www.youtube.com/watch?v=" in url:
        return True
    if "https://youtu.be/" in url:
        return True
    if "https://www.youtube.com/playlist?list=" in url:
        return True
    return False

# baixa o audio do youtube
def downloadAudio(videoUrl):
    yt = pytubefix.YouTube(videoUrl)
    # stream  = yt.streams.filter(only_audio=True).first()
    stream = yt.streams.first()
    # retira os caracteres especiais e espaços do nome do video
    filename = ''.join(e for e in yt.title if e.isalnum())
    ffmpeg.input(stream.url).output(filename + '.wav').run()
    return filename + '.wav'

# transcreve o audio
def transcribeAudioOpenAI(filename):
    audioFile = open(filename, "rb")
    response = openai.audio.transcriptions.create(
        model="whisper-1",
        file=audioFile
    )
    audioFile.close()
    return response

def summaryOpenAI(text):
    response = openai.chat.Completion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você receber a transcrição do audio de um video. Por favor, resuma o que foi dito."},
            {"role": "user", "content": f"""transcrição do audio: 
                        <transcricao>
                        {text}
                        </transcricao>
                        """},
        ],
    )
    return response.choices[0].message

def transcribeAudioGroq(fileName):
    apiKeyGroq = os.getenv('GROQ_API_KEY')
    if apiKeyGroq is None:
        raise ValueError("A variável de ambiente GROQ_API_KEY não está definida.")
    with open(fileName, "rb") as file:
        client = Groq(api_key=apiKeyGroq)
        transcription = client.audio.transcriptions.create(
            file=(fileName, file.read()),
            model="whisper-large-v3",
            language="pt",
            response_format="verbose_json",
        )  
    return transcription

def summaryGroq(text):
    apiKeyGroq = os.getenv('GROQ_API_KEY')
    if apiKeyGroq is None:
        raise ValueError("A variável de ambiente GROQ_API_KEY não está definida.")    
    client = Groq(api_key=apiKeyGroq)
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
                        <transcricao>
                        {text}
                        </transcricao>
                        """
                    }
                ],
                max_tokens=8000,
                stream=False,
                temperature=1,
                top_p=1
    )
    return summary.choices[0].message.content

def saveFile(text, filename="output"):
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
    # url = "https://www.youtube.com/watch?v=Cw8A_yXR1M0"

    ai = "groq"
    if len(sys.argv) >= 3:
        ai = sys.argv[2]

    if ai != "openai" and ai != "groq":
        print("Opção invalida")
        sys.exit(1)

    # verifica se o link é valido
    if validateUrl(url):
        arquivo = downloadAudio(url)
    # senão verifica se é um arquivo
    elif os.path.isfile(url):
        arquivo = url
    else:
        print("Link invalido")
        sys.exit(1)  
    
    # TODO: verificar se o arquivo é um audio
    # TODO: verificar o tamanho do arquivo e se ele exceder o limite, dividir em partes menores
    
    if ai == "openai":
        # Obter a chave da API do OpenAI
        openaiApiKey = os.getenv("OPENAI_API_KEY")
        if openaiApiKey is None:
            raise ValueError("A variável de ambiente OPEN_API_KEY não está definida.")
        os.environ["OPENAI_API_KEY"] = openaiApiKey
        transcricao = transcribeAudioOpenAI(arquivo)
    else:
        transcricao = transcribeAudioGroq(arquivo)

    # verifica se transcricao tem text
    if hasattr(transcricao, 'text'):
        saveFile(transcricao.text, arquivo)
    else:
        saveFile(transcricao, arquivo)
        print("Erro na transcrição")
        sys.exit(1)
        
    print(transcricao.text)

    resumo = ""
    if len(sys.argv) > 3 and sys.argv[3] == "-r":
        if ai == "openai":
            resumo = summaryOpenAI(transcricao.text)
        else:
            resumo = summaryGroq(transcricao.text)
    
    print(resumo)
    saveFile(resumo, f"""resumo_{arquivo}""")