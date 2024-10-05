import sys
import speech_recognition as sr
from pydub import AudioSegment
import os
import concurrent.futures
import time
import random

def transcribe_chunk(chunk, recognizer, chunk_number):
    max_retries = 5
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            # Exportar o chunk para um arquivo temporário
            temp_filename = f"temp_{chunk_number}.wav"
            chunk.export(temp_filename, format="wav")
            
            # Carregar o arquivo temporário com speech_recognition
            with sr.AudioFile(temp_filename) as source:
                audio_listened = recognizer.record(source)
            
            # Tentar reconhecer o texto
            text = recognizer.recognize_google(audio_listened, language="pt-BR")
            
            # Remover o arquivo temporário
            os.remove(temp_filename)
            
            return chunk_number, text
        
        except sr.UnknownValueError:
            print(f"Chunk {chunk_number}: Não foi possível entender o áudio")
            return chunk_number, ""
        
        except sr.RequestError as e:
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

def transcribe_large_audio(file_path, output_file, chunk_duration_ms=30000, max_workers=4):
    # Carregar o arquivo de áudio
    audio = AudioSegment.from_wav(file_path)
    
    # Inicializar o reconhecedor
    recognizer = sr.Recognizer()
    
    # Dividir o áudio em chunks
    chunks = [audio[i:i+chunk_duration_ms] for i in range(0, len(audio), chunk_duration_ms)]
    
    # Processar os chunks em paralelo
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_chunk = {executor.submit(transcribe_chunk, chunk, recognizer, i): i 
                                    for i, chunk in enumerate(chunks)}
        
        for future in concurrent.futures.as_completed(future_to_chunk):
            chunk_number, text = future.result()
            results.append((chunk_number, text))
    
    # Ordenar os resultados pelo número do chunk
    results.sort(key=lambda x: x[0])
    
    # Escrever os resultados no arquivo de saída
    with open(output_file, 'w', encoding='utf-8') as f:
        for _, text in results:
            f.write(f"{text}\n")
    
    print("Transcrição completa!")


if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print("Falta o arquivo de áudio")
        print("Uso: python transcripter.py <arquivo de áudio>")
        sys.exit(1)
        
    # Uso da função
    input_file = sys.argv[1]
    output_file = input_file.split("\\")[-1].split(".")[0] + ".txt"
    print(f"Transcrevendo o arquivo de áudio {input_file} para {output_file}")
    transcribe_large_audio(input_file, output_file, max_workers=4)