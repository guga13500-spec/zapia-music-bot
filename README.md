# ZapiaMusic Bot - TeamTalk5

Bot de música para o servidor blindmasters.org.

## Requisitos

- Python 3.8 ou superior
- ffmpeg instalado no sistema
- yt-dlp (instalado via pip)

## Instalação

```bash
bash instalar.sh
```

Ou manualmente:
```bash
pip install teamtalk.py yt-dlp
sudo apt-get install ffmpeg   # Linux
```

## Como usar

```bash
python3 bot.py
```

## Comandos no TeamTalk (digite no canal de texto)

| Comando | O que faz |
|---------|-----------|
| `h` | Mostra todos os comandos |
| `t nome da música` | Toca uma música do YouTube (ex: `t Evidências Chitãozinho`) |
| `p` | Pausa a música |
| `s` | Para a música |
| `v 80` | Ajusta o volume (0 a 100) |

## Observações

- O bot precisa estar no mesmo canal que você para tocar música
- Requer conexão com a internet para buscar músicas no YouTube
- ffmpeg é obrigatório para converter o áudio
