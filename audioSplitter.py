import sys
import librosa
import numpy as np
from pydub import AudioSegment
import os

def splitAudio(inputFile, outputDir, minSegmentLength=5*60, maxSegmentLength=10*60):
    # Carregar o arquivo de áudio
    audio = AudioSegment.from_wav(inputFile)
    
    # Carregar o áudio usando librosa para análise
    y, sr = librosa.load(inputFile, sr=None)
    
    # Detectar pausas na fala
    intervals = librosa.effects.split(y, top_db=20)
    
    # Converter os intervalos para segundos
    intervalsSec = intervals / sr
    
    # Inicializar variáveis para controle de segmentos
    currentSegmentStart = 0
    currentSegmentDuration = 0
    segmentCount = 1
    
    for i, interval in enumerate(intervalsSec):
        intervalDuration = interval[1] - interval[0]
        
        # Se adicionar este intervalo exceder o tamanho máximo, corte aqui
        if currentSegmentDuration + intervalDuration > maxSegmentLength:
            # Cortar o segmento
            segment = audio[currentSegmentStart*1000:(currentSegmentStart + currentSegmentDuration)*1000]
            
            # Salvar o segmento
            outputFile = os.path.join(outputDir, f"segment_{segmentCount}.wav")
            segment.export(outputFile, format="wav")
            
            # Preparar para o próximo segmento
            currentSegmentStart = interval[0]
            currentSegmentDuration = intervalDuration
            segmentCount += 1
        else:
            currentSegmentDuration += intervalDuration
        
        # Se o segmento atual atingiu o tamanho mínimo e estamos em uma pausa, corte aqui
        if currentSegmentDuration >= minSegmentLength and i < len(intervalsSec) - 1:
            nextInterval = intervalsSec[i+1]
            pauseDuration = nextInterval[0] - interval[1]
            
            if pauseDuration > 0.5:  # Pausa de meio segundo ou mais
                # Cortar o segmento
                segment = audio[currentSegmentStart*1000:(currentSegmentStart + currentSegmentDuration)*1000]
                
                # Salvar o segmento
                outputFile = os.path.join(outputDir, f"segment_{segmentCount}.wav")
                segment.export(outputFile, format="wav")
                
                # Preparar para o próximo segmento
                currentSegmentStart = nextInterval[0]
                currentSegmentDuration = 0
                segmentCount += 1
    
    # Salvar o último segmento, se houver
    if currentSegmentDuration > 0:
        segment = audio[currentSegmentStart*1000:]
        outputFile = os.path.join(outputDir, f"segment_{segmentCount}.wav")
        segment.export(outputFile, format="wav")

if __name__ == "__main__":
    # python audioSplitter.py audio.wav
    if len(sys.argv) < 2:
        print("Falta o arquivo de áudio")
        print("Uso: python audioSplitter.py <arquivo de áudio>")
        sys.exit(1)
        
    inputFile = sys.argv[1]
    print(f"Dividindo o arquivo de áudio {inputFile}")    
    outputDir = inputFile.split("\\")[-1].split(".")[0]
    print(f"Salvando os segmentos em {outputDir}")
    os.makedirs(outputDir, exist_ok=True)
    splitAudio(inputFile, outputDir)