"""Sonidos del sable, sintetizados con numpy (mono, 16 bit, 44.1 kHz).

  SableLuzHum    zumbido en loop mientras se empuna (los ciclos cierran justo: loop sin 'click')
  SableLuzOn     encendido: chasquido + la hoja que 'crece' subiendo de tono hasta el zumbido
  SableLuzOff    apagado: el zumbido baja de tono y se corta
  SableLuzClash  choque/golpe: chisporroteo brillante con un golpe grave

El 'vuuum' del swing es el audio original del mod (sable_sonido.mp3 -> SableLuzHit.wav).
"""
import wave

import numpy as np

SR = 44100
F0 = 90.0            # fundamental del zumbido (Hz)


def _save(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def _hum_wave(phase, bright=1.0):
    """Timbre del zumbido a partir de la fase de la fundamental (radianes)."""
    x = (np.sin(phase) + 0.55 * np.sin(2 * phase + 0.3) + 0.32 * np.sin(3 * phase + 1.1)
         + 0.18 * bright * np.sin(4 * phase) + 0.09 * bright * np.sin(6 * phase + 0.7))
    return x / 2.0


def _lowpass(x, a):
    """Filtro de un polo (a cerca de 1 = mas grave)."""
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc = a * acc + (1 - a) * v
        y[i] = acc
    return y


def hum(seconds=2.0):
    """Loop: frecuencias con numero entero de ciclos en 'seconds'."""
    t = np.arange(int(SR * seconds)) / SR
    x = _hum_wave(2 * np.pi * F0 * t)
    x += 0.25 * np.sin(2 * np.pi * (F0 * 1.5) * t)                  # quinta suave, da 'cuerpo'
    x *= 1 + 0.12 * np.sin(2 * np.pi * 1.0 * t) + 0.05 * np.sin(2 * np.pi * 3.5 * t)  # vaiven
    # 'buzz' de fondo: ruido grave generado en frecuencia (fases al azar), periodico por construccion
    rng = np.random.default_rng(1)
    spec = np.zeros(len(t) // 2 + 1, complex)
    fr = np.fft.rfftfreq(len(t), 1 / SR)
    band = (fr > 40) & (fr < 2500)
    spec[band] = np.exp(2j * np.pi * rng.random(band.sum())) / (1 + fr[band] / 400)
    buzz = np.fft.irfft(spec, len(t))
    x += 0.05 * buzz / np.abs(buzz).max()
    return 0.45 * x / np.abs(x).max()


def ignite(seconds=0.75):
    t = np.arange(int(SR * seconds)) / SR
    f = F0 * (0.45 + 0.55 * (1 - np.exp(-t / 0.12)))               # sube hasta el zumbido
    phase = 2 * np.pi * np.cumsum(f) / SR
    x = _hum_wave(phase, bright=1.6) * np.clip(t / 0.05, 0, 1)
    rng = np.random.default_rng(2)
    snap = rng.normal(0, 1, len(t)) * np.exp(-t / 0.035)            # chasquido inicial
    hiss = _lowpass(rng.normal(0, 1, len(t)), 0.3) * np.exp(-t / 0.18) * 0.5
    x = x * 0.8 + snap * 0.7 + hiss
    x *= np.clip((seconds - t) / 0.08, 0, 1) * 0.3 + 0.7            # termina al nivel del zumbido
    return 0.8 * x / np.abs(x).max()


def retract(seconds=0.6):
    t = np.arange(int(SR * seconds)) / SR
    f = F0 * (1.0 - 0.6 * (t / seconds) ** 1.5)                     # baja de tono
    phase = 2 * np.pi * np.cumsum(f) / SR
    x = _hum_wave(phase, bright=1.3) * np.clip(1 - t / seconds, 0, 1) ** 1.3
    rng = np.random.default_rng(3)
    x += _lowpass(rng.normal(0, 1, len(t)), 0.4) * np.exp(-t / 0.1) * 0.25
    return 0.7 * x / np.abs(x).max()


def clash(seconds=0.45):
    t = np.arange(int(SR * seconds)) / SR
    rng = np.random.default_rng(4)
    crackle = rng.normal(0, 1, len(t))
    # chisporroteo: rafagas cortas al azar
    gate = (rng.random(len(t) // 220 + 1) < 0.55).repeat(220)[:len(t)]
    crackle *= gate * np.exp(-t / 0.16)
    bright = crackle - _lowpass(crackle, 0.85)                        # solo agudos
    thump = np.sin(2 * np.pi * 70 * t) * np.exp(-t / 0.06)           # golpe grave
    zap = _hum_wave(2 * np.pi * np.cumsum(F0 * 2.2 * (1 + 0.5 * np.exp(-t / 0.05))) / SR, 2.0) * np.exp(-t / 0.1)
    x = 0.9 * bright + 0.8 * thump + 0.5 * zap
    return 0.9 * x / np.abs(x).max()


def write_all(sound_dir):
    import os
    os.makedirs(sound_dir, exist_ok=True)
    for name, fn in (('SableLuzHum', hum), ('SableLuzOn', ignite), ('SableLuzOff', retract),
                     ('SableLuzClash', clash)):
        _save(os.path.join(sound_dir, name + '.wav'), fn())
