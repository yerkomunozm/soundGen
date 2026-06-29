# SoundGen

Generador de intervalos musicales. Dada una nota base y un intervalo,
sintetiza la tónica seguida del intervalo (secuencial) y las exporta
como archivo MP3 para entrenar el reconocimiento auditivo.

## Requisitos

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/) instalado en el sistema
  ```bash
  brew install ffmpeg        # macOS
  sudo apt install ffmpeg    # Ubuntu/Debian
  ```

## Instalación

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
# Ver intervalos disponibles
python generate_interval.py --list

# Generar un intervalo (default: piano): tónica → silencio → intervalo
python generate_interval.py C4 quinta_justa

# Con instrumento y duración personalizada
python generate_interval.py A3 octava --instrument organ --duration 3

# Onda senoidal pura
python generate_interval.py F#4 tercera_menor -i sine -d 2

# Generar los 12 intervalos desde C4
./generate_all.sh

# Desde otra nota, duración e instrumento
./generate_all.sh A3 1.5 organ
```

Los archivos MP3 se guardan en `output/` con el formato `{nota}_{intervalo}_{instrumento}.mp3`.

## Intervalos soportados

| Intervalo | Semitonos |
|-----------|-----------|
| Segunda menor | 1 |
| Segunda mayor | 2 |
| Tercera menor | 3 |
| Tercera mayor | 4 |
| Cuarta justa | 5 |
| Tritono | 6 |
| Quinta justa | 7 |
| Sexta menor | 8 |
| Sexta mayor | 9 |
| Séptima menor | 10 |
| Séptima mayor | 11 |
| Octava | 12 |

## Instrumentos

| Instrumento | Descripción                                      |
|-------------|--------------------------------------------------|
| `piano`     | 5 armónicos + ataque rápido + decaimiento natural |
| `organ`     | 4 armónicos con sustain constante                |
| `sine`      | Onda senoidal pura (tono puro de laboratorio)    |

Se seleccionan con `--instrument` / `-i` (default: `piano`).

## Notas soportadas

Formato: `NombreOctava` — ej: `C4`, `F#3`, `Bb5`

Alteraciones: `#` (sostenido) y `b` (bemol). Octavas de 0 a 8.

## Estructura del proyecto

```
soundGen/
├── docs/plan.md              # Documentación técnica
├── output/                   # MP3 generados
├── venv/                     # Entorno virtual
├── generate_interval.py      # Script principal
├── generate_all.sh           # Genera todos los intervalos
├── requirements.txt          # Dependencias Python
└── README.md
```
