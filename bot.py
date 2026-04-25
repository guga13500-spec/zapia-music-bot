"""
ZapiaMusic - Bot de música para TeamTalk5
Servidor: blindmasters.org:19558
Canal: Grupo dos amigos

Comandos (via mensagem de texto no canal):
  h           - mostra os comandos disponíveis
  t <música>  - toca uma música (busca no YouTube)
  p           - pausa/continua a música
  s           - para a música
  v <0-100>   - ajusta o volume
"""

# ── Monkey-patch: força URL fixa do SDK (v5.22a) ──────────────────────────────
# A lib teamtalk.py tenta scraping buscando versão 5.15 (inexistente).
# Sobrescrevemos download() para usar a URL correta antes de qualquer import.
import os
import sys
import platform


def _patched_download() -> None:
    import requests

    machine = platform.machine()
    if machine in ("AMD64", "x86_64"):
        suffix = "ubuntu22_x86_64"
    elif "arm" in machine:
        suffix = "raspbian_armhf"
    else:
        sys.exit(f"Arquitetura não suportada: {machine}")

    sdk_url = f"https://bearware.dk/teamtalksdk/v5.22a/tt5sdk_v5.22a_{suffix}.7z"
    print(f"[patch] Baixando SDK de {sdk_url}")

    import teamtalk.tools.ttsdk_downloader as _ttdl
    cd = os.path.dirname(os.path.dirname(os.path.abspath(_ttdl.__file__)))
    dest = os.path.join(cd, "ttsdk.7z")

    r = requests.get(sdk_url, stream=True, timeout=120)
    r.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in r.iter_content(chunk_size=65536):
            f.write(chunk)
    print("[patch] Download concluído.")


# Aplica o patch ANTES de qualquer import do teamtalk
try:
    import teamtalk.tools.ttsdk_downloader as _ttdl
    _ttdl.download = _patched_download
    print("[patch] SDK downloader corrigido para v5.22a.")
except ImportError:
    pass

# ── Importações principais ────────────────────────────────────────────────────
import asyncio
import logging
import teamtalk

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ── Configurações do servidor ──────────────────────────────────────────────────
SERVER = {
    "host": "blindmasters.org",
    "port": 19558,
    "username": "ADM.geral2007",
    "password": "2007",
    "nickname": "ZapiaMusic",
    "channel": "/Grupo dos amigos",
    "channel_password": "",
}

AJUDA = (
    "=== ZapiaMusic - Comandos ===\n"
    "h            - mostra esta ajuda\n"
    "t <música>   - toca uma música (ex: t Evidências Chitãozinho)\n"
    "p            - pausa ou continua a música\n"
    "s            - para a música\n"
    "v <0-100>    - ajusta o volume (ex: v 80)"
)

# ── Estado global do bot ───────────────────────────────────────────────────────
pausado = False
streamer_atual = None

# ── Bot ────────────────────────────────────────────────────────────────────────
bot = teamtalk.TeamTalkBot(client_name="ZapiaMusic")


@bot.event
async def on_ready():
    logging.info("Bot conectado e pronto!")
    for tt in bot.teamtalks:
        canal = tt.get_channel(SERVER["channel"])
        if canal:
            tt.join_channel(canal)
            logging.info(f"Entrou no canal: {canal.name}")


@bot.event
async def on_message(message):
    global pausado, streamer_atual

    texto = message.content.strip()
    if not texto:
        return

    canal = message.channel
    tt = message.server

    def get_streamer():
        return teamtalk.Streamer.get_streamer_for_channel(canal)

    # ── h: ajuda ──────────────────────────────────────────────────────────────
    if texto.lower() == "h":
        canal.send_message(AJUDA)
        return

    # ── t <música>: tocar ─────────────────────────────────────────────────────
    if texto.lower().startswith("t "):
        query = texto[2:].strip()
        if not query:
            canal.send_message("Use: t <nome da musica>  (ex: t Evidências Chitãozinho)")
            return
        streamer_atual = get_streamer()
        if not streamer_atual.ffmpeg_available:
            canal.send_message("Erro: ffmpeg não instalado.")
            return
        if not streamer_atual.yt_dlp_available:
            canal.send_message("Erro: yt-dlp não instalado.")
            return
        canal.send_message(f"Procurando: {query}...")
        pausado = False
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, streamer_atual.search_and_stream, query)
        return

    # ── p: pausar/continuar ───────────────────────────────────────────────────
    if texto.lower() == "p":
        s = get_streamer()
        if pausado:
            canal.send_message("Continuando...")
            pausado = False
            canal.send_message("(Nota: use 't <música>' para tocar de novo)")
        else:
            canal.send_message("Pausando...")
            s.stop()
            pausado = True
        return

    # ── s: parar ──────────────────────────────────────────────────────────────
    if texto.lower() == "s":
        s = get_streamer()
        s.stop()
        pausado = False
        canal.send_message("Música parada.")
        return

    # ── v <número>: volume ────────────────────────────────────────────────────
    if texto.lower().startswith("v "):
        try:
            vol = int(texto[2:].strip())
            vol = max(0, min(100, vol))
            s = get_streamer()
            s.volume = vol
            canal.send_message(f"Volume: {vol}%")
        except ValueError:
            canal.send_message("Use: v <0-100>  (ex: v 80)")
        return


# ── Inicialização ──────────────────────────────────────────────────────────────
async def main():
    await bot.add_server(SERVER)
    await bot._start()


if __name__ == "__main__":
    bot.run()
