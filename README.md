# Video Silence Cutter

Uma ferramenta de linha de comando que corta automaticamente os silêncios de um vídeo usando Whisper e FFmpeg.

## Pré-requisitos

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/download.html) instalado no PATH.

## Instalação

```bash
python -m venv .venv
# Ative o ambiente (Windows: .venv\Scripts\activate | Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

## Como usar

É **recomendado** executar o script estando na **pasta do projeto**. O vídeo final é sempre gerado no local apontado pelo parâmetro `--output`. 

### Exemplo básico (na pasta do projeto)
O script lê e salva os vídeos na pasta atual.

```bash
python main.py --input video.mp4 --output editado.mp4
```

### Exemplo avançado (caminhos absolutos)
Se você estiver em outra pasta (ou quiser buscar/salvar os vídeos em outro lugar), passe os **caminhos completos**:

```bash
python C:/caminho/do/projeto/main.py --input D:/MeusVideos/bruto.mp4 --output D:/MeusVideos/editado.mp4
```

*Nota: O arquivo editado sempre será criado no exato caminho informado em `--output`.*

### Argumentos:
- `--input`: Vídeo original (padrão: `gravacao-1.mp4`).
- `--output`: Destino do vídeo editado (padrão: `editado.mp4`).
- `--model`: Modelo Whisper (`small`, `medium`, `large-v2` - padrão: `small`).
