# SoundGen — Generador de Intervalos Musicales

## Objetivo

Script CLI que recibe una nota musical y un intervalo, genera el sonido de ambos
tonos simultáneamente y exporta un archivo MP3.

## Stack tecnológico

| Componente       | Elección                                                   |
|------------------|-----------------------------------------------------------|
| Lenguaje         | Python 3                                                   |
| Síntesis de audio| `numpy` — síntesis aditiva con perfiles de instrumento       |
| Exportación MP3  | `ffmpeg` — conversión WAV → MP3                            |
| Entorno          | `venv` — entorno virtual aislado                           |

## Arquitectura

```
soundGen/
├── docs/
│   └── plan.md
├── output/             ← Archivos MP3 generados
├── venv/               ← Entorno virtual
├── requirements.txt
└── generate_interval.py
```

## Flujo del script

```
Entrada: nota (C4) + intervalo (tercera_mayor)
  │
  ├── 1. Parsear nota → frecuencia base (Hz)
  │      Fórmula: freq = 440 × 2^((midi - 69) / 12)
  │
  ├── 2. Calcular frecuencia del intervalo
  │      freq_intervalo = freq_base × 2^(semitonos / 12)
  │
├── 3. Generar ondas según instrumento (44100 Hz, síntesis aditiva)
│      - Tónica: suma de armónicos del perfil × envelope [N segundos]
│      - Silencio: 0.3s de pausa
│      - Intervalo: suma de armónicos del perfil × envelope [N segundos]
│      - Secuencia: [tónica] + [silencio] + [intervalo]
│      - Perfiles: sine (senoidal pura), organ (armónicos + sustain),
│                  piano (armónicos + decaimiento exponencial)
│
├── 4. Aplicar envolvente (fade o decaimiento según instrumento)
│
├── 5. Exportar como WAV en memoria
│
└── 6. Convertir a MP3 (ffmpeg)
         → output/{nota}_{intervalo}_{instrumento}.mp3
```

## Intervalos soportados (todos hasta la octava)

| # | Intervalo         | Semitonos | Relación frecuencia |
|---|-------------------|-----------|---------------------|
| 1 | Segunda menor     | 1         | ×2^(1/12)           |
| 2 | Segunda mayor     | 2         | ×2^(2/12)           |
| 3 | Tercera menor     | 3         | ×2^(3/12)           |
| 4 | Tercera mayor     | 4         | ×2^(4/12)           |
| 5 | Cuarta justa      | 5         | ×2^(5/12)           |
| 6 | Tritono           | 6         | ×2^(6/12)           |
| 7 | Quinta justa      | 7         | ×2^(7/12)           |
| 8 | Sexta menor       | 8         | ×2^(8/12)           |
| 9 | Sexta mayor       | 9         | ×2^(9/12)           |
| 10| Séptima menor     | 10        | ×2^(10/12)          |
| 11| Séptima mayor     | 11        | ×2^(11/12)          |
| 12| Octava            | 12        | ×2^(12/12) = ×2     |

## Notas soportadas

Formato: `NombreOctava` (ej: `C4`, `F#3`, `Bb5`)

- Alteraciones: `#` (sostenido) y `b` (bemol)
- Octavas: 0 a 8 (rango piano estándar)
- Escala cromática completa: C, C#/Db, D, D#/Eb, E, F, F#/Gb, G, G#/Ab, A, A#/Bb, B

## Uso

```bash
# Activar entorno
source venv/bin/activate

# Generar intervalo: tónica 2s → silencio → intervalo 2s
python generate_interval.py C4 quinta_justa
# → output/C4_quinta_justa.mp3

# Con duración personalizada por nota (segundos)
python generate_interval.py A3 octava --duration 3
```

## Instrumentos disponibles

| Instrumento | Técnica de síntesis                          | Envolvente        |
|-------------|----------------------------------------------|-------------------|
| `sine`      | Onda senoidal pura (sin armónicos)           | Fade in/out 50ms  |
| `organ`     | 4 armónicos (1×, 2×, 3×, 4×)                | Fade in/out 50ms  |
| `piano`     | 5 armónicos (1× a 5×)                        | Ataque 8ms + decaimiento exponencial |

## Dependencias

```txt
numpy
```

Además requiere `ffmpeg` instalado en el sistema para la conversión a MP3.
