# converte video para mp3
import ffmpeg
import os
import sys
from dotenv import load_dotenv


filename = sys.argv[1]
if not os.path.exists(filename):
    print("Arquivo não encontrado")
    exit()
    
newfilename = filename.split('.')[0]+'.mp3'
ffmpeg.input(filename).output(newfilename).run()