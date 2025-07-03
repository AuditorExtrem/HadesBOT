import discord
from discord.ext import commands, tasks
from discord import app_commands, ui
import json
import os
from datetime import datetime
import pytz
from keep_alive import keep_alive

TOKEN = os.getenv('DISCORD_TOKEN')
ARQUIVO = 'servidores.json'
ARQUIVO_ENVIOS = 'envios.json'
AVISOS_CONFIG = 'avisos_config.json'
CANAL_AVISOS_ID = 1380022433288949851
CARGO_ANALISE_ID = 1379508463172063286
CANAL_2DIAS_ID = 1379585139629228062
CARGO_2DIAS_ID = 1379508463172063290

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

FICHAS_CANAL_ID = 1386798237163323493
FICHAS_CANAL_HADES2_ID = 1388546663190364241

NUMERO_FICHA_PADRAO = {
    "hades": 66,
    "hades2": 7
}
def arquivo_numero_ficha(guilda):
    return f"numero_ficha_{guilda}.json"

def carregar_numero_ficha(guilda):
    try:
        with open(arquivo_numero_ficha(guilda), "r", encoding="utf-8") as f:
            return json.load(f).get("numero", NUMERO_FICHA_PADRAO[guilda])
    except:
        return NUMERO_FICHA_PADRAO[guilda]

def salvar_numero_ficha(guilda, n):
    with open(arquivo_numero_ficha(guilda), "w", encoding="utf-8") as f:
        json.dump({"numero": n}, f)

def carregar_ficha(user_id, idioma, guilda):
    arquivo = f"fichas_{idioma}.json"
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            ficha = json.load(f).get(str(user_id))
            if ficha and ficha.get("guilda") == guilda:
                return ficha
            return None
    except:
        return None

def salvar_ficha(user_id, data, idioma):
    arquivo = f"fichas_{idioma}.json"
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            todas = json.load(f)
    except:
        todas = {}
    todas[str(user_id)] = data
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(todas, f, indent=4, ensure_ascii=False)

def marcar_preencheu(user_id):
    try:
        with open("marcados_ficha.json", "r", encoding="utf-8") as f:
            marcados = json.load(f)
    except:
        marcados = []
    if user_id not in marcados:
        marcados.append(user_id)
        with open("marcados_ficha.json", "w", encoding="utf-8") as f:
            json.dump(marcados, f)

def ja_preencheu(user_id):
    try:
        with open("marcados_ficha.json", "r", encoding="utf-8") as f:
            marcados = json.load(f)
        return user_id in marcados
    except:
        return False

IDIOMAS = {
    "pt": {
        "nome": "Português",
        "bandeira": "🇧🇷",
        "perguntas": [
            ("🎮 Nick no Roblox:", "roblox"),
            ("⚔️ DPS Atual:", "dps"),
            ("💎 Farm diário de gemas:", "farm"),
            ("🔹 Rank:", "rank"),
            ("🔹 Level:", "level"),
            ("🔹 Tempo de jogo:", "tempo")
        ]
    },
    "en": {
        "nome": "English",
        "bandeira": "🇺🇸",
        "perguntas": [
            ("🎮 Roblox Username:", "roblox"),
            ("⚔️ Current DPS:", "dps"),
            ("💎 Daily Gem Farm:", "farm"),
            ("🔹 Rank:", "rank"),
            ("🔹 Level:", "level"),
            ("🔹 Playtime:", "tempo")
        ]
    },
    "es": {
        "nome": "Español",
        "bandeira": "🇪🇸",
        "perguntas": [
            ("🎮 Usuario de Roblox:", "roblox"),
            ("⚔️ DPS actual:", "dps"),
            ("💎 Gemas diarias obtenidas:", "farm"),
            ("🔹 Rango:", "rank"),
            ("🔹 Nivel:", "level"),
            ("🔹 Tiempo de juego:", "tempo")
        ]
    }
}

class MenuIdioma(ui.View):
    def __init__(self, bot, interaction, canal_id, nome_guilda, target_user=None):
        super().__init__(timeout=60)
        self.bot = bot
        self.interaction = interaction
        self.canal_id = canal_id
        self.nome_guilda = nome_guilda
        self.target_user = target_user or interaction.user
        self.select = ui.Select(
            placeholder="Escolha o idioma / Choose language / Elige idioma",
            options=[
                discord.SelectOption(label=idata["nome"], value=lang, emoji=idata["bandeira"])
                for lang, idata in IDIOMAS.items()
            ]
        )
        self.select.callback = self.selecionar_idioma
        self.add_item(self.select)

    async def selecionar_idioma(self, interaction: discord.Interaction):
        if interaction.user != self.target_user:
            await interaction.response.send_message("❌ Apenas quem foi convidado pode interagir.", ephemeral=True)
            return
        idioma = self.select.values[0]
        await interaction.response.edit_message(content="✅ Idioma selecionado!", view=None)
        await iniciar_formulario(self.bot, interaction, idioma, self.canal_id, self.nome_guilda, self.target_user)

async def fazer_perguntas(interaction, canal, idioma, perguntas, target_user):
    respostas = {}
    for pergunta, chave in perguntas:
        await canal.send(f"{target_user.mention} {pergunta}")
        def check(m):
            return m.author == target_user and m.channel == canal
        try:
            msg = await interaction.client.wait_for("message", check=check, timeout=180)
            respostas[chave] = msg.content.strip()
        except Exception:
            await canal.send(f"{target_user.mention} Tempo esgotado para responder a pergunta.")
            return None
    return respostas

async def enviar_ficha_no_canal(bot, user, idioma, ficha, nome_guilda, canal_id):
    avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
    nome_guilda_fmt = "Hades" if nome_guilda == "hades" else "Hades 2"
    embed = discord.Embed(
        title=f"🌌 Ficha de Jogador #{ficha['numero']} – Arise Crossover 🌌",
        color=discord.Color.purple()
    )
    embed.add_field(name="🎮 Roblox", value=ficha['roblox'], inline=False)
    embed.add_field(name="🏰 Guilda", value=nome_guilda_fmt, inline=True)
    embed.add_field(name="💬 Discord", value=user.mention, inline=True)
    embed.add_field(name="⚔️ DPS", value=ficha['dps'], inline=False)
    embed.add_field(name="💎 Farm", value=ficha['farm'], inline=False)
    embed.add_field(
        name="📊 Outras Informações",
        value=f"🔹 Rank: {ficha['rank']}\n🔹 Level: {ficha['level']}\n🔹 Tempo: {ficha['tempo']}",
        inline=False
    )
    embed.set_footer(text=f"📆 Data da ficha: {ficha['data']}")
    embed.set_thumbnail(url=avatar_url)
    canal = bot.get_channel(canal_id)
    if canal:
        await canal.send(embed=embed)

async def iniciar_formulario(bot, interaction, idioma, canal_id, nome_guilda, target_user):
    perguntas = IDIOMAS[idioma]["perguntas"]
    canal = await bot.fetch_channel(interaction.channel.id)
    respostas = await fazer_perguntas(interaction, canal, idioma, perguntas, target_user)
    if respostas is None:
        return
    data_atual = datetime.now().strftime("%d/%m/%Y")
    user_id = target_user.id
    ficha_existente = carregar_ficha(user_id, idioma, nome_guilda)
    if ficha_existente:
        numero_ficha = ficha_existente["numero"]
    else:
        numero_ficha = carregar_numero_ficha(nome_guilda) + 1
        salvar_numero_ficha(nome_guilda, numero_ficha)
    ficha = {
        "numero": numero_ficha,
        "idioma": idioma,
        "roblox": respostas.get("roblox"),
        "dps": respostas.get("dps"),
        "farm": respostas.get("farm"),
        "rank": respostas.get("rank"),
        "level": respostas.get("level"),
        "tempo": respostas.get("tempo"),
        "data": data_atual,
        "guilda": nome_guilda
    }
    salvar_ficha(user_id, ficha, idioma)
    marcar_preencheu(user_id)
    canal_destino = FICHAS_CANAL_ID if nome_guilda == "hades" else FICHAS_CANAL_HADES2_ID
    await enviar_ficha_no_canal(bot, target_user, idioma, ficha, nome_guilda, canal_destino)
    await canal.send(f"{target_user.mention} sua ficha foi enviada no canal de fichas!")

@bot.tree.command(name="ficha", description="Preencher ficha de jogador (Hades)")
@app_commands.describe(usuario="(Opcional) Usuário para responder a ficha")
async def slash_ficha(interaction: discord.Interaction, usuario: discord.Member = None):
    if usuario is None or usuario == interaction.user:
        # O próprio usuário → ephemeral só para ele
        view = MenuIdioma(bot, interaction, FICHAS_CANAL_ID, "hades", target_user=interaction.user)
        await interaction.response.send_message(
            f"📄 Clique abaixo para escolher o idioma.\n"
            "Só quem for convidado poderá interagir.\n"
            "⚠️ Você só pode ter UMA ficha registrada. Preencher de novo irá editar sua ficha!\n"
            f"Número inicial da ficha: **{carregar_numero_ficha('hades')}**",
            view=view,
            ephemeral=True
        )
    else:
        # Envia convite via DM para o usuário marcado
        try:
            view = MenuIdioma(bot, interaction, FICHAS_CANAL_ID, "hades", target_user=usuario)
            await usuario.send(
                f"📄 Você foi convidado a preencher a ficha da guilda **Hades** por {interaction.user.mention}!\n"
                "Clique abaixo para escolher o idioma.\n"
                "⚠️ Você só pode ter UMA ficha registrada. Preencher de novo irá editar sua ficha!\n"
                f"Número inicial da ficha: **{carregar_numero_ficha('hades')}**",
                view=view
            )
            await interaction.response.send_message(f"✉️ Convite enviado por DM para {usuario.mention}!", ephemeral=True)
        except Exception:
            await interaction.response.send_message(f"❌ Não consegui enviar DM para {usuario.mention}. Peça para liberar DMs!", ephemeral=True)

@bot.tree.command(name="ficha_hades2", description="Preencher ficha de jogador (Hades 2)")
@app_commands.describe(usuario="(Opcional) Usuário para responder a ficha")
async def slash_ficha_hades2(interaction: discord.Interaction, usuario: discord.Member = None):
    if usuario is None or usuario == interaction.user:
        view = MenuIdioma(bot, interaction, FICHAS_CANAL_HADES2_ID, "hades2", target_user=interaction.user)
        await interaction.response.send_message(
            f"📄 Clique abaixo para escolher o idioma.\n"
            "Só quem for convidado poderá interagir.\n"
            "⚠️ Você só pode ter UMA ficha registrada. Preencher de novo irá editar sua ficha!\n"
            f"Número inicial da ficha: **{carregar_numero_ficha('hades2')}**",
            view=view,
            ephemeral=True
        )
    else:
        try:
            view = MenuIdioma(bot, interaction, FICHAS_CANAL_HADES2_ID, "hades2", target_user=usuario)
            await usuario.send(
                f"📄 Você foi convidado a preencher a ficha da guilda **Hades 2** por {interaction.user.mention}!\n"
                "Clique abaixo para escolher o idioma.\n"
                "⚠️ Você só pode ter UMA ficha registrada. Preencher de novo irá editar sua ficha!\n"
                f"Número inicial da ficha: **{carregar_numero_ficha('hades2')}**",
                view=view
            )
            await interaction.response.send_message(f"✉️ Convite enviado por DM para {usuario.mention}!", ephemeral=True)
        except Exception:
            await interaction.response.send_message(f"❌ Não consegui enviar DM para {usuario.mention}. Peça para liberar DMs!", ephemeral=True)

# ... (restante dos comandos slash e utilitários igual antes)

keep_alive()
bot.run(TOKEN)