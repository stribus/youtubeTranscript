import os
import concurrent.futures
import sys
import time
import random
from pydub import AudioSegment
from groq import Groq
import ffmpeg


def getChunkDurationMs(mp3File):
    """Retorna a duração de cada chunk em milissegundos, baseando-se no tamanho do arquivo de áudio.
        Limita o Tamanho de cada chunk a mais ou menos 20 mega bytes.
        sendo assim irá calcular a duração do chunk baseado no tamanho do arquivo.
    Args:
        mp3File (string): nome do arquivo de áudio
    """
    
    fileSize = os.path.getsize(mp3File)
    maxFileSize = 20 * 1024 * 1024  # 20 MB
    audio = AudioSegment.from_mp3(mp3File)
    if fileSize <= maxFileSize:
        return audio.duration_seconds * 1000
    proportion = fileSize / maxFileSize
    maxAudioDuration = audio.duration_seconds / proportion
    chunkDuration = maxAudioDuration * 1000
    chunkDuration = int(chunkDuration)
    # testa salvando um arquivo com a duração do chunk
    chunkSize = maxFileSize + 1
    while chunkSize > maxFileSize:
        chunkTest = audio[:chunkDuration]
        chunkTest.export("chunkTest.mp3", format="mp3")
        # pega o tamanho do arquivo criado
        chunkSize = os.path.getsize("chunkTest.mp3")      
        os.remove("chunkTest.mp3")
        if chunkSize > maxFileSize:
            chunkDuration = chunkDuration - 1000
        elif chunkSize <= 0:
            print("Erro ao calcular o tamanho do chunk")
            sys.exit(1)
        else:
            print(f"Chunk duration: {chunkDuration} ms")
            print(f"Chunk size: {chunkSize/1024/1024} MB")
            break
        
    return int(chunkDuration)


def convertToMp3(filePath):
    """Converte um arquivo de áudio para mp3
    Args:
        filePath (string): caminho do arquivo de áudio
    """
    print(f"Convertendo arquivo {filePath} para mp3")
    newFilename = filePath.split('.')[0] + '.mp3'
    ffmpeg.input(filePath).output(newFilename).run()
    print(f"Arquivo {filePath} convertido para mp3")

def transcribeChunk(chunk, chunkNumber, apiKey):
    maxRetries = 5
    baseDelay = 1
    
    for attempt in range(maxRetries):
        try:
            # Exportar o chunk para um arquivo temporário
            tempFilename = f"temp_{chunkNumber}.mp3"
            chunk.export(tempFilename, format="mp3")
            
            # Transcrever usando Groq API
            client = Groq(api_key=apiKey)
            with open(tempFilename, "rb") as file:
                transcription = client.audio.transcriptions.create(
                    file=(tempFilename, file.read()),
                    model="whisper-large-v3",
                    language="pt",
                    response_format="verbose_json",
                )
            
            # Extrair o texto da transcrição
            text = transcription.text if hasattr(transcription, 'text') else ''
            
            return chunkNumber, text
        
        except Exception as e:
            if attempt < maxRetries - 1:
                delay = (baseDelay * 2 ** attempt) + (random.randint(0, 1000) / 1000)
                print(f"Chunk {chunkNumber}: Erro na requisição. Tentando novamente em {delay:.2f} segundos...")
                time.sleep(delay)
            else:
                print(f"Chunk {chunkNumber}: Erro na requisição após {maxRetries} tentativas; {e}")
                return chunkNumber, ""
        
        finally:
            if os.path.exists(tempFilename):
                os.remove(tempFilename)

def transcribeLargeAudio(filePath, outputFile, maxWorkers=4):
    apiKey = os.getenv('GROQ_API_KEY')
    if apiKey is None:
        raise ValueError("A variável de ambiente GROQ_API_KEY não está definida.")
    
    # verifica se o arquivo é mp3 se não converte
    if filePath.split('.')[-1] != 'mp3':
        convertToMp3(filePath)
        filePath = filePath.split('.')[0] + '.mp3'
    else:
        print(f"Arquivo {filePath} é mp3")
    
    chunkDurationMs = getChunkDurationMs(filePath)
    
    # Carregar o arquivo de áudio
    audio = AudioSegment.from_mp3(filePath) 
    
    # Dividir o áudio em chunks
    chunks = [audio[i:i+chunkDurationMs] for i in range(0, len(audio), chunkDurationMs)]
    
    # processar os chunks sequencialmente e com 0.5 segundos entre cada um
    # para evitar erros de limite de requisições
    results = []
    for i, chunk in enumerate(chunks):
        chunkNumber, text = transcribeChunk(chunk, i, apiKey)
        results.append((chunkNumber, text))
        time.sleep(0.5)    
    
    # Escrever os resultados no arquivo de saída
    with open(outputFile, 'w', encoding='utf-8') as f:
        for _, text in results:
            f.write(f"{text}\n")
    
    print("Transcrição completa!")


if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print("Falta o arquivo de áudio")
        print("Uso: python transcripterAI.py <arquivo de áudio>")
        sys.exit(1)
        
    # Uso da função
    inputFile = sys.argv[1]
    outputFile = inputFile.split("\\")[-1].split(".")[0] + "AI.txt"
    print(f"Transcrevendo o arquivo de áudio {inputFile} para {outputFile}")
    transcribeLargeAudio(inputFile, outputFile, maxWorkers=4)