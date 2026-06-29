import argparse
import io
import os
import struct
import subprocess
import tempfile

import numpy as np

# Frecuencia de muestreo estándar de CD: 44100 samples/segundo
SAMPLE_RATE = 44100
# Profundidad de bits: 16-bit PCM
BITS_PER_SAMPLE = 16
# Silencio entre tónica e intervalo (para separar auditivamente)
GAP_SECONDS = 0.3

# Perfiles de instrumento: cada uno define armónicos y envolvente
# Cada armónico es (ratio_frecuencia, amplitud_relativa)
INSTRUMENTS = {
    "sine": {
        "harmonics": [(1, 1.0)],
        "envelope": "fade",
    },
    "organ": {
        "harmonics": [(1, 1.0), (2, 0.6), (3, 0.3), (4, 0.15)],
        "envelope": "fade",
    },
    "piano": {
        "harmonics": [(1, 1.0), (2, 0.5), (3, 0.25), (4, 0.12), (5, 0.06)],
        "envelope": "piano",
        "sustain": 0.2,
    },
}

# Mapeo de nombres de nota a número MIDI dentro de una octava (C=0 ... B=11)
# Sostenidos (#) y bemoles (b) apuntan al mismo semitono (enharmonía)
NOTES = {
    "C": 0, "C#": 1, "Db": 1,
    "D": 2, "D#": 3, "Eb": 3,
    "E": 4,
    "F": 5, "F#": 6, "Gb": 6,
    "G": 7, "G#": 8, "Ab": 8,
    "A": 9, "A#": 10, "Bb": 10,
    "B": 11,
}

# Mapeo de nombres de intervalo a su distancia en semitonos
# Fórmula: intervalo en Hz = freq_base * 2^(semitonos / 12)
INTERVALS = {
    "segunda_menor": 1,
    "segunda_mayor": 2,
    "tercera_menor": 3,
    "tercera_mayor": 4,
    "cuarta_justa": 5,
    "tritono": 6,
    "quinta_justa": 7,
    "sexta_menor": 8,
    "sexta_mayor": 9,
    "septima_menor": 10,
    "septima_mayor": 11,
    "octava": 12,
}


def parse_note(note: str) -> int:
    """Convierte un nombre de nota (ej: 'C4', 'F#3', 'Bb5') a número MIDI."""
    note = note.strip()
    if len(note) == 2:
        # Formato: Letra + Octava (C4, A3, B5)
        name, octave = note[0].upper(), int(note[1])
    elif len(note) == 3:
        # Formato: Letra + Alteración + Octava (C#4, Bb3, F#5)
        name, octave = note[0].upper() + note[1], int(note[2])
    else:
        raise ValueError(f"Formato de nota inválido: {note}")

    if name not in NOTES:
        raise ValueError(f"Nota desconocida: {name}")

    # MIDI: C0 = 12, C4 = 60, A4 = 69
    return NOTES[name] + (octave + 1) * 12


def midi_to_freq(midi: int) -> float:
    """Convierte número MIDI a frecuencia en Hz (temperamento igual, A4=440Hz)."""
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def generate_wave(freq: float, duration: float, instrument: str) -> np.ndarray:
    """Genera una forma de onda según el perfil del instrumento.

    Síntesis aditiva: suma de senoidales armónicas con envolvente.
    - sine:   onda senoidal pura
    - organ:  armónicos con sustain constante
    - piano:  armónicos con ataque rápido y decaimiento exponencial
    """
    profile = INSTRUMENTS[instrument]
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, False)

    wave = np.zeros(n)
    for ratio, amp in profile["harmonics"]:
        wave += amp * np.sin(2 * np.pi * freq * ratio * t)

    max_val = np.max(np.abs(wave))
    if max_val > 0:
        wave /= max_val

    if profile["envelope"] == "piano":
        attack = int(SAMPLE_RATE * 0.008)
        sustain = profile["sustain"]
        env = np.ones(n)
        env[:attack] = np.linspace(0, 1, attack)
        env[attack:] = sustain + (1 - sustain) * np.exp(-4 * t[attack:] / duration)
    else:
        fade_len = int(SAMPLE_RATE * 0.05)
        env = np.ones(n)
        env[:fade_len] = np.linspace(0, 1, fade_len)
        env[-fade_len:] = np.linspace(1, 0, fade_len)

    return wave * env


def write_wav(buf: io.BytesIO, pcm: np.ndarray) -> None:
    """Escribe un header WAV PCM estándar en un buffer en memoria."""
    n_samples = len(pcm)
    data_size = n_samples * (BITS_PER_SAMPLE // 8)

    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + data_size))
    buf.write(b"WAVE")
    buf.write(b"fmt ")
    buf.write(struct.pack("<I", 16))          # tamaño del chunk fmt
    buf.write(struct.pack("<H", 1))            # formato PCM
    buf.write(struct.pack("<H", 1))            # 1 canal (mono)
    buf.write(struct.pack("<I", SAMPLE_RATE))
    buf.write(struct.pack("<I", SAMPLE_RATE * (BITS_PER_SAMPLE // 8)))
    buf.write(struct.pack("<H", BITS_PER_SAMPLE // 8))
    buf.write(struct.pack("<H", BITS_PER_SAMPLE))
    buf.write(b"data")
    buf.write(struct.pack("<I", data_size))
    buf.write(pcm.tobytes())
    buf.seek(0)


def generate_mp3(note_name: str, interval_name: str, duration: float = 2.0,
                 instrument: str = "piano") -> str:
    """Genera un archivo MP3 con la tónica seguida del intervalo (secuencial).

    La línea de tiempo es:
      [tónica] → [silencio] → [intervalo]
    El usuario escucha primero la nota de referencia y luego la del intervalo,
    para entrenar el reconocimiento auditivo de intervalos.
    """
    midi_base = parse_note(note_name)
    semitones = INTERVALS[interval_name]

    freq_base = midi_to_freq(midi_base)
    freq_intv = midi_to_freq(midi_base + semitones)

    wav_base = generate_wave(freq_base, duration, instrument)
    wav_intv = generate_wave(freq_intv, duration, instrument)
    silence = np.zeros(int(SAMPLE_RATE * GAP_SECONDS))

    audio = np.concatenate([wav_base, silence, wav_intv])
    pcm = np.int16(audio * 32767)

    # Escribir WAV en memoria
    buf = io.BytesIO()
    write_wav(buf, pcm)

    os.makedirs("output", exist_ok=True)
    mp3_path = os.path.abspath(f"output/{note_name}_{interval_name}_{instrument}.mp3")

    # Convertir WAV → MP3 vía ffmpeg usando archivo temporal
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(buf.read())
        tmp_path = tmp.name

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", tmp_path, "-codec:a", "libmp3lame",
             "-b:a", "192k", mp3_path],
            capture_output=True, check=True)
    except subprocess.CalledProcessError:
        raise RuntimeError("Error al convertir a MP3. ¿ffmpeg está instalado?")
    finally:
        os.unlink(tmp_path)

    return mp3_path


def list_intervals() -> None:
    """Imprime la tabla de intervalos disponibles con sus semitonos."""
    print("Intervalos disponibles:")
    for i, (name, semitones) in enumerate(INTERVALS.items(), 1):
        print(f"  {i:2d}. {name:20s} ({semitones} semitonos)")


def main() -> None:
    """Punto de entrada: parsea argumentos y delega la generación."""
    parser = argparse.ArgumentParser(description="Generador de intervalos musicales")
    parser.add_argument("nota", nargs="?", help="Nota base (ej: C4, F#3, Bb5)")
    parser.add_argument("intervalo", nargs="?", help="Intervalo a generar")
    parser.add_argument("--duration", "-d", type=float, default=2.0,
                        help="Duración de cada nota en segundos (default: 2.0)")
    parser.add_argument("--instrument", "-i", default="piano",
                        choices=list(INSTRUMENTS.keys()),
                        help="Timbre del instrumento (default: piano)")
    parser.add_argument("--list", "-l", action="store_true",
                        help="Listar intervalos disponibles")

    args = parser.parse_args()

    if args.list:
        list_intervals()
        return

    if not args.nota:
        parser.error("Se requiere una nota (ej: C4, F#3)")
    if not args.intervalo:
        parser.error("Se requiere un intervalo. Usa --list para ver los disponibles.")

    try:
        path = generate_mp3(args.nota, args.intervalo, args.duration, args.instrument)
        print(f"Generado: {path}")
    except (ValueError, KeyError) as e:
        print(f"Error: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
