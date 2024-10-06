import pytubefix
import ffmpeg
import os
import sys

def validateUrl(url):
    if "https://www.youtube.com/watch?v=" in url:
        return True
    if "https://youtu.be/" in url:
        return True
    if "https://www.youtube.com/playlist?list=" in url:
        return True
    return False

def downloadAudio(videoUrl, tipo='mp3'):
    yt = pytubefix.YouTube(videoUrl)
    if tipo == 'mp3' or tipo == 'wav':
        stream = yt.streams.filter(only_audio=True).first()
    else:
        stream = yt.streams.first()
    
    # Retira os caracteres especiais e espaços do nome do vídeo
    filename = ''.join(e for e in yt.title if e.isalnum())
    ffmpeg.input(stream.url).output(f"{filename}.{tipo}").run()
    return f"{filename}.{tipo}"

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Falta o link do vídeo")
        print("Uso: python downloadyoutube.py <link do vídeo> [mp3|wav|mp4]")
        sys.exit(1)
        
    url = sys.argv[1]
    if not validateUrl(url):
        print("Link inválido")
        sys.exit(1)
        
    tipo = 'mp3'
    if len(sys.argv) > 2:
        tipo = sys.argv[2]
        
    downloadAudio(url, tipo)