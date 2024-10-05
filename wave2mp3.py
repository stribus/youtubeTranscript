# converte e compacta arquivo de audio wave para mp3


import ffmpeg
import os
import sys
from dotenv import load_dotenv

if __name__ == "__main__":
    filename = sys.argv[1]
    if not os.path.exists(filename):
        print("Arquivo não encontrado")
        exit()
        
    newfilename = filename.split('.')[0]+'.mp3'
    ffmpeg.input(filename).output(newfilename).run()
    print(f"Arquivo {newfilename} criado com sucesso")