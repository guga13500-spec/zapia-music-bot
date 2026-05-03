"""
ZapiaMusic - Bot de música e assistente para TeamTalk5
Servidor: blindmasters.org:19558
Canal: Grupo dos amigos

Comandos:
  h            - ajuda
  t <música>   - toca música do YouTube
  p            - pausa/continua
  s            - para música
  v <0-100>    - volume
  falar <texto>- bot fala via ElevenLabs TTS
  piada        - conta uma piada
  zoar <nome>  - zoação leve de alguém
  clima <cidade>- previsão do tempo
  hora         - hora atual
  dado <N>     - rola um dado de N lados
  cara ou coroa- joga cara ou coroa
  contagem <N> - contagem regressiva falada
"""

import asyncio
import logging
import os
import random
import requests
import tempfile
import urllib.parse
from datetime import datetime

import teamtalk

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ── Configurações ──────────────────────────────────────────────────────────────
SERVER = {
    "host": "blindmasters.org",
    "port": 19558,
    "username": "ADM.geral2007",
    "password": "2007",
    "nickname": "ZapiaMusic",
    "channel": "/Grupo dos amigos",
    "channel_password": "",
}

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = "nPczCjzI2devNBz1zQrb"  # Brian - voz masculina profunda
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")

AJUDA = (
    "=== ZapiaMusic - Comandos ===\n"
    "h               - esta ajuda\n"
    "t <música>      - toca música (ex: t Evidências Chitãozinho)\n"
    "p               - pausa ou continua\n"
    "s               - para música\n"
    "v <0-100>       - volume (ex: v 80)\n"
    "falar <texto>   - bot fala em voz alta\n"
    "piada           - conta uma piada\n"
    "zoar <nome>     - zoação de alguém\n"
    "clima <cidade>  - previsão do tempo\n"
    "hora            - hora atual\n"
    "dado <N>        - rola dado de N lados\n"
    "cara ou coroa   - joga cara ou coroa\n"
    "contagem <N>    - contagem regressiva falada"
)

PIADAS = [
    "Por que o esqueleto não consegue namorar? Porque não tem coragem!",
    "O que o zero disse para o oito? Bonito cinto!",
    "Por que o livro de matemática é o mais triste? Porque tem muitos problemas.",
    "Sabe por que o computador foi ao médico? Porque tinha vírus!",
    "O que o elefante disse para o outro elefante? Nada! Elefante não fala!",
    "Por que o músico quebrou o violão? Porque queria um som mais pesado!",
    "Qual é o animal mais antigo? A zebra, porque ainda está em preto e branco.",
    "Por que a bruxa não usa calcinha? Para ter melhor aderência na vassoura!",
    "O que o surdo falou para o cego? Não ouço nada do que você não vê.",
    "Por que o homem jogou o relógio pela janela? Queria ver o tempo voar!",
    "Por que homem não sabe dar ponto final? Porque sempre termina em vírgula, aguardando resposta.",
    "Como se chama um bêbado honesto? Álcool sincero!",
]

ZOAÇÕES = [
    "é tão lento que quando nasceu a parteira perguntou: é menino ou menina? Ele disse: depende do dia!",
    "é tão estranho que o Google não sabe o que fazer com ele!",
    "é tão atrasado que chega ontem na reunião de hoje!",
    "é tão confuso que fica perdido dentro da própria casa!",
    "é tão sortudo no azar que se cair em pé ainda acerta o joelho!",
    "tem tanto papo que a rádio fica com ciúmes!",
    "é tão devagar que a tartaruga manda cartão de aniversário com antecedência pra ele!",
    "é tão teimoso que discute com o GPS!",
    "é tão preguiçoso que respira só quando precisa!",
]

# ── Estado global ──────────────────────────────────────────────────────────────
pausado = False
streamer_atual = None


# ── TTS via ElevenLabs ─────────────────────────────────────────────────────────
def tts_para_arquivo(texto: str):
    """Gera áudio TTS e retorna caminho do arquivo temporário."""
    if not ELEVENLABS_API_KEY:
        logging.warning("ELEVENLABS_API_KEY não configurada")
        return None
    try:
        resp = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}",
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "text": texto,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.4,
                    "similarity_boost": 0.8,
                    "style": 0.6,
                    "use_speaker_boost": True,
                },
            },
            timeout=30,
        )
        resp.raise_for_status()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tmp.write(resp.content)
        tmp.close()
        return tmp.name
    except Exception as e:
        logging.error(f"Erro TTS: {e}")
        return None


async def falar_no_canal(tt, canal, texto: str):
    """Gera TTS e transmite no canal TeamTalk."""
    canal.send_message(f"[TTS] {texto}")
    loop = asyncio.get_event_loop()
    arquivo = await loop.run_in_executor(None, tts_para_arquivo, texto)
    if arquivo and streamer_atual:
        await loop.run_in_executor(None, streamer_atual.stream_file, arquivo)
    elif arquivo:
        logging.info(f"Arquivo TTS gerado mas sem streamer: {arquivo}")


# ── Clima ──────────────────────────────────────────────────────────────────────
def get_clima(cidade: str) -> str:
    if not OPENWEATHER_API_KEY:
        return f"API de clima não configurada ainda. Em breve!"
    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={urllib.parse.quote(cidade)}"
            f"&appid={OPENWEATHER_API_KEY}&units=metric&lang=pt_br"
        )
        resp = requests.get(url, timeout=10)
        d = resp.json()
        if resp.status_code == 200:
            desc = d["weather"][0]["description"]
            temp = d["main"]["temp"]
            sensacao = d["main"]["feels_like"]
            humid = d["main"]["humidity"]
            return f"Clima em {cidade}: {desc}, {temp:.1f}°C (sensação {sensacao:.1f}°C), umidade {humid}%"
        else:
            return f"Cidade '{cidade}' não encontrada."
    except Exception as e:
        return f"Erro ao buscar clima: {e}"


# ── Bot ────────────────────────────────────────────────────────────────────────
bot = teamtalk.TeamTalkBot(client_name="ZapiaMusic")


@bot.event
async def on_ready():
    logging.info("Bot conectado e pronto!")
    for tt in bot.teamtalks:
        canal = tt.get_channel(SERVER["channel"])
        if canal:
            await tt.join_channel(canal)


def get_streamer():
    global streamer_atual
    if streamer_atual is None:
        streamer_atual = teamtalk.AudioStreamer()
    return streamer_atual


@bot.event
async def on_message(tt, msg):
    global pausado, streamer_atual

    if msg.type != teamtalk.TextMsgType.CHANNEL:
        return

    canal = tt.get_channel_by_id(msg.channel_id)
    if not canal or canal.name.lower() not in SERVER["channel"].lower():
        return

    texto = msg.content.strip()
    if not texto:
        return

    # ── h: ajuda ──────────────────────────────────────────────────────────────
    if texto.lower() == "h":
        canal.send_message(AJUDA)
        return

    # ── hora ──────────────────────────────────────────────────────────────────
    if texto.lower() == "hora":
        agora = datetime.now().strftime("%H:%M:%S")
        canal.send_message(f"São {agora} (horário local do servidor)")
        return

    # ── dado <N> ──────────────────────────────────────────────────────────────
    if texto.lower().startswith("dado"):
        partes = texto.split()
        lados = 6
        if len(partes) > 1:
            try:
                lados = int(partes[1])
            except ValueError:
                pass
        resultado = random.randint(1, lados)
        canal.send_message(f"Dado de {lados} lados: {resultado}!")
        return

    # ── cara ou coroa ─────────────────────────────────────────────────────────
    if texto.lower() in ("cara ou coroa", "cara", "coroa"):
        resultado = random.choice(["CARA", "COROA"])
        canal.send_message(f"Jogando a moeda... {resultado}!")
        return

    # ── piada ─────────────────────────────────────────────────────────────────
    if texto.lower() == "piada":
        piada = random.choice(PIADAS)
        canal.send_message(piada)
        if ELEVENLABS_API_KEY:
            await falar_no_canal(tt, canal, piada)
        return

    # ── zoar <nome> ───────────────────────────────────────────────────────────
    if texto.lower().startswith("zoar "):
        nome = texto[5:].strip()
        zoacao = random.choice(ZOAÇÕES)
        msg_zoacao = f"{nome} {zoacao}"
        canal.send_message(msg_zoacao)
        if ELEVENLABS_API_KEY:
            await falar_no_canal(tt, canal, msg_zoacao)
        return

    # ── clima <cidade> ────────────────────────────────────────────────────────
    if texto.lower().startswith("clima "):
        cidade = texto[6:].strip()
        resultado = get_clima(cidade)
        canal.send_message(resultado)
        return

    # ── falar <texto> ─────────────────────────────────────────────────────────
    if texto.lower().startswith("falar "):
        frase = texto[6:].strip()
        if frase:
            await falar_no_canal(tt, canal, frase)
        return

    # ── contagem <N> ──────────────────────────────────────────────────────────
    if texto.lower().startswith("contagem"):
        partes = texto.split()
        n = 10
        if len(partes) > 1:
            try:
                n = min(int(partes[1]), 30)
            except ValueError:
                pass
        canal.send_message(f"Contagem regressiva de {n}...")
        numeros = ", ".join(str(i) for i in range(n, 0, -1))
        frase_contagem = f"{numeros}... ZERO!"
        if ELEVENLABS_API_KEY:
            await falar_no_canal(tt, canal, frase_contagem)
        return

    # ── t <música>: tocar ─────────────────────────────────────────────────────
    if texto.lower().startswith("t "):
        query = texto[2:].strip()
        if not query:
            canal.send_message("Use: t <nome da música>")
            return
        s = get_streamer()
        canal.send_message(f"Procurando: {query}...")
        pausado = False
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, s.search_and_stream, query)
        return

    # ── p: pausar/continuar ───────────────────────────────────────────────────
    if texto.lower() == "p":
        s = get_streamer()
        if pausado:
            canal.send_message("Continuando...")
            pausado = False
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
