import sys
import librosa
import numpy as np
from pydub import AudioSegment
import os

def split_audio(input_file, output_dir, min_segment_length=5*60, max_segment_length=10*60):
    # Carregar o arquivo de áudio
    audio = AudioSegment.from_wav(input_file)
    
    # Carregar o áudio usando librosa para análise
    y, sr = librosa.load(input_file, sr=None)
    
    # Detectar pausas na fala
    intervals = librosa.effects.split(y, top_db=20)
    
    # Converter os intervalos para segundos
    intervals_sec = intervals / sr
    
    # Inicializar variáveis para controle de segmentos
    current_segment_start = 0
    current_segment_duration = 0
    segment_count = 1
    
    for i, interval in enumerate(intervals_sec):
        interval_duration = interval[1] - interval[0]
        
        # Se adicionar este intervalo exceder o tamanho máximo, corte aqui
        if current_segment_duration + interval_duration > max_segment_length:
            # Cortar o segmento
            segment = audio[current_segment_start*1000:(current_segment_start + current_segment_duration)*1000]
            
            # Salvar o segmento
            output_file = os.path.join(output_dir, f"segment_{segment_count}.wav")
            segment.export(output_file, format="wav")
            
            # Preparar para o próximo segmento
            current_segment_start = interval[0]
            current_segment_duration = interval_duration
            segment_count += 1
        else:
            current_segment_duration += interval_duration
        
        # Se o segmento atual atingiu o tamanho mínimo e estamos em uma pausa, corte aqui
        if current_segment_duration >= min_segment_length and i < len(intervals_sec) - 1:
            next_interval = intervals_sec[i+1]
            pause_duration = next_interval[0] - interval[1]
            
            if pause_duration > 0.5:  # Pausa de meio segundo ou mais
                # Cortar o segmento
                segment = audio[current_segment_start*1000:(current_segment_start + current_segment_duration)*1000]
                
                # Salvar o segmento
                output_file = os.path.join(output_dir, f"segment_{segment_count}.wav")
                segment.export(output_file, format="wav")
                
                # Preparar para o próximo segmento
                current_segment_start = next_interval[0]
                current_segment_duration = 0
                segment_count += 1
    
    # Salvar o último segmento, se houver
    if current_segment_duration > 0:
        segment = audio[current_segment_start*1000:]
        output_file = os.path.join(output_dir, f"segment_{segment_count}.wav")
        segment.export(output_file, format="wav")

if __name__ == "__main__":
    # python audioSplitter.py audio.wav
    if len(sys.argv) < 2:
        print("Falta o arquivo de áudio")
        print("Uso: python audioSplitter.py <arquivo de áudio>")
        sys.exit(1)
        
    input_file = sys.argv[1]
    print(f"Dividindo o arquivo de áudio {input_file}")    
    output_dir = input_file.split("\\")[-1].split(".")[0]
    print(f"Salvando os segmentos em {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    split_audio(input_file, output_dir)