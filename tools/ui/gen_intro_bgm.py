# Uso: python3 tools/ui/gen_intro_bgm.py   (desde la raíz). Genera Audio/BGM/Intro.wav: pad ambiental suave de 32 s en bucle sin corte (placeholder).
# Para sustituirlo: borra Intro.wav y pon Audio/BGM/Intro.ogg (mismo nombre "Intro").
import numpy as np, wave
sr=22050; L=32; t=np.arange(sr*L)/sr
def lfo(f,ph=0): return 0.5+0.5*np.sin(2*np.pi*f*t+ph)
notes=[(110.0,.34),(165.0,.22),(220.0,.20),(262.5,.12),(330.0,.10)]
out=[np.zeros_like(t),np.zeros_like(t)]
for i,(f,a) in enumerate(notes):
    for ch,det in ((0,0.0),(1,0.25)):
        sig=np.sin(2*np.pi*(f+det)*t)+0.25*np.sin(2*np.pi*2*(f+det)*t)
        out[ch]+=a*sig*(0.35+0.65*lfo(1.0/16*(1+i%2),i*1.3+ch))
m=np.stack(out,1); m*=0.22/np.abs(m).max()
w=wave.open("Audio/BGM/Intro.wav","wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
w.writeframes((m*32767).astype('<i2').tobytes()); w.close(); print("OK")
