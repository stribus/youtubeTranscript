import os
import concurrent.futures
import sys
import time
import random
from pydub import AudioSegment
from groq import Groq
import ffmpeg


def get_chunk_duration_ms(mp3_file):
    """Retorna a duração de cada chunk em milissegundos, baseando-se no tamanho do arquivo de áudio.
        Limita o Tamanho de cada chunk a mais ou menos 20 mega bytes.
        sendo assim irá calcular a duração do chunk baseado no tamanho do arquivo.
    Args:
        mp3_file (string): nome do arquivo de áudio
    """
    
    file_size = os.path.getsize(mp3_file)
    max_file_size = 20 * 1024 * 1024  # 20 MB
    audio = AudioSegment.from_mp3(mp3_file)
    if file_size <= max_file_size:
        return audio.duration_seconds * 1000
    proportion = file_size / max_file_size
    max_audio_duration = audio.duration_seconds / proportion
    chunk_duration = max_audio_duration * 1000
    chunk_duration = int(chunk_duration)
    # testa salvando um arquivo com a duração do chunk
    chunk_size = max_file_size + 1
    while chunk_size > max_file_size:
        chunktest = audio[:chunk_duration]
        chunktest.export("chunktest.mp3", format="mp3")
        #pega o tamanho do arquivo criado
        chunk_size = os.path.getsize("chunktest.mp3")      
        os.remove("chunktest.mp3")        
        if chunk_size > max_file_size:
            chunk_duration = chunk_duration - 1000
        elif chunk_size <= 0:
            print("Erro ao calcular o tamanho do chunk")
            sys.exit(1)
        else:
            print(f"Chunk duration: {chunk_duration} ms")
            print(f"Chunk size: {chunk_size/1024/1024} MB")
            break
        
    return int(chunk_duration)


def convert2mp3(file_path):
    """Converte um arquivo de áudio para mp3
    Args:
        file_path (string): caminho do arquivo de áudio
    """
    # audio = AudioSegment.from_file(file_path)
    # audio.export(file_path, format="mp3")
    print(f"Convertendo arquivo {file_path} para mp3")
    newfilename = file_path.split('.')[0]+'.mp3'
    ffmpeg.input(file_path).output(newfilename).run()
    print(f"Arquivo {file_path} convertido para mp3")

def transcribe_chunk(chunk, chunk_number, api_key):
    max_retries = 5
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            # Exportar o chunk para um arquivo temporário
            temp_filename = f"temp_{chunk_number}.mp3"
            chunk.export(temp_filename, format="mp3")
            
            # Transcrever usando Groq API
            client = Groq(api_key=api_key)
            with open(temp_filename, "rb") as file:
                transcription = client.audio.transcriptions.create(
                    file=(temp_filename, file.read()),
                    model="whisper-large-v3",
                    language="pt",
                    response_format="verbose_json",
                )
            
            # Extrair o texto da transcrição
            text = transcription.text if hasattr(transcription, 'text') else ''
            
            return chunk_number, text
        
        except Exception as e:
            if attempt < max_retries - 1:
                delay = (base_delay * 2 ** attempt) + (random.randint(0, 1000) / 1000)
                print(f"Chunk {chunk_number}: Erro na requisição. Tentando novamente em {delay:.2f} segundos...")
                time.sleep(delay)
            else:
                print(f"Chunk {chunk_number}: Erro na requisição após {max_retries} tentativas; {e}")
                return chunk_number, ""
        
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

def transcribe_large_audio(file_path, output_file, max_workers=4):
    api_key = os.getenv('GROQ_API_KEY')
    if api_key is None:
        raise ValueError("A variável de ambiente GROQ_API_KEY não está definida.")
    
    #verifica se o arquivo é mp3 se não converte
    if file_path.split('.')[-1] != 'mp3':
        convert2mp3(file_path)
        file_path = file_path.split('.')[0]+'.mp3'
    else:
        print(f"Arquivo {file_path} é mp3")
    
    
    chunk_duration_ms = get_chunk_duration_ms(file_path)
    
    # Carregar o arquivo de áudio
    audio = AudioSegment.from_mp3(file_path) 
    
    # Dividir o áudio em chunks
    chunks = [audio[i:i+chunk_duration_ms] for i in range(0, len(audio), chunk_duration_ms)]
    
    # processar os chunks sequencialmente e com 0.5 segundos entre cada um
    # para evitar erros de limite de requisições
    results = []
    for i, chunk in enumerate(chunks):
        chunk_number, text = transcribe_chunk(chunk, i, api_key)
        results.append((chunk_number, text))
        time.sleep(0.5)    
    
    # Escrever os resultados no arquivo de saída
    with open(output_file, 'w', encoding='utf-8') as f:
        for _, text in results:
            f.write(f"{text}\n")
    
    print("Transcrição completa!")


if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print("Falta o arquivo de áudio")
        print("Uso: python transcripterAI.py <arquivo de áudio>")
        sys.exit(1)
        
    # Uso da função
    input_file = sys.argv[1]
    output_file = input_file.split("\\")[-1].split(".")[0] + "AI.txt"
    print(f"Transcrevendo o arquivo de áudio {input_file} para {output_file}")
    transcribe_large_audio(input_file, output_file, max_workers=4)