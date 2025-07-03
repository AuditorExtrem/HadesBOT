import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
from datetime import datetime
import pytz
from keep_alive import keep_alive

TOKEN = os.getenv('DISCORD_TOKEN')
ARQUIVO = 'servidores.json'
ARQUIVO_ENVIOS = 'envios.json'
AVISOS_CONFIG = 'avisos_config.json'
FICHAS_CANAL_ID = 1386798237163323493
FICHAS_CANAL_HADES2_ID = 1388546663190364241
CANAL_AVISOS_ID = 1380022433288949851
CARGO_ANALISE_ID = 1379508463172063286
CANAL_2DIAS_ID = 1379585139629228062
CARGO_2DIAS_ID = 1379508463172063290

NUMERO_FICHA_PADRAO = {"hades": 66, "hades2": 7}
IDIOMAS = {
    "pt": {
        "nome": "Português", "bandeira": "🇧🇷",
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
        "nome": "English", "bandeira": "🇺🇸",
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
        "nome": "Español", "bandeira": "🇪🇸",
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
CAMPOS_EDITAVEIS = [
    ("roblox", "Nome Roblox"),
    ("dps", "DPS"),
    ("farm", "Farm"),
    ("rank", "Rank"),
    ("level", "Level"),
    ("tempo", "Tempo"),
    ("data", "Data"),
    ("discord", "Discord"),
]
GUILDAS = [("hades", "Hades"), ("hades2", "Hades2")]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

def arquivo_fichas(guilda, idioma):
    return f"fichas_{guilda}_{idioma}.json"

def carregar_ficha(user_id, guilda, idioma):
    arquivo = arquivo_fichas(guilda, idioma)
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            ficha = json.load(f).get(str(user_id))
            return ficha
    except Exception:
        return None

def carregar_ficha_por_numero(numero, guilda, idioma):
    arquivo = arquivo_fichas(guilda, idioma)
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            todas = json.load(f)
    except Exception:
        return None, None
    for uid, ficha in todas.items():
        if ficha.get("numero") == numero:
            return uid, ficha
    return None, None

def salvar_ficha(user_id, data, guilda, idioma):
    arquivo = arquivo_fichas(guilda, idioma)
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            todas = json.load(f)
    except Exception:
        todas = {}
    todas[str(user_id)] = data
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(todas, f, indent=4, ensure_ascii=False)

def salvar_ficha_por_uid(uid, ficha, guilda, idioma):
    arquivo = arquivo_fichas(guilda, idioma)
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            todas = json.load(f)
    except Exception:
        todas = {}
    todas[str(uid)] = ficha
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(todas, f, indent=4, ensure_ascii=False)

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

def marcar_preencheu(user_id, guilda, idioma):
    arq = f"marcados_ficha_{guilda}_{idioma}.json"
    try:
        with open(arq, "r", encoding="utf-8") as f:
            marcados = json.load(f)
    except:
        marcados = []
    if user_id not in marcados:
        marcados.append(user_id)
        with open(arq, "w", encoding="utf-8") as f:
            json.dump(marcados, f)

def ja_preencheu(user_id, guilda, idioma):
    arq = f"marcados_ficha_{guilda}_{idioma}.json"
    try:
        with open(arq, "r", encoding="utf-8") as f:
            marcados = json.load(f)
        return user_id in marcados
    except:
        return False

# ---- FICHA ----
class MenuIdioma(ui.View):
    def __init__(self, bot, canal_id, nome_guilda, target_user, canal_nome, canal_mencao):
        super().__init__(timeout=120)
        self.bot = bot
        self.canal_id = canal_id
        self.nome_guilda = nome_guilda
        self.target_user = target_user
        self.canal_nome = canal_nome
        self.canal_mencao = canal_mencao
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
        if hasattr(self.bot, "last_slash_interaction_user") and interaction.user != self.bot.last_slash_interaction_user:
            try:
                await interaction.user.send(
                    f"Idioma selecionado!\n\nAgora volte para o canal {self.canal_mencao} ({self.canal_nome}) no servidor para responder às perguntas da ficha!"
                )
            except Exception:
                pass
        canal = await self.bot.fetch_channel(self.canal_id)
        await iniciar_formulario(self.bot, interaction, idioma, canal, self.nome_guilda, self.target_user)

def set_last_slash_interaction_user(bot, user):
    bot.last_slash_interaction_user = user

async def fazer_perguntas(interaction, canal, idioma, perguntas, target_user):
    respostas = {}
    for pergunta, chave in perguntas:
        await canal.send(f"{target_user.mention} {pergunta}")
        def check(m):
            return m.author == target_user and m.channel == canal
        try:
            msg = await interaction.client.wait_for("message", check=check, timeout=600)
            respostas[chave] = msg.content.strip()
        except Exception:
            await canal.send(f"{target_user.mention} Tempo esgotado para responder a pergunta.")
            return None
    return respostas

async def enviar_ficha_no_canal(bot, user, idioma, ficha, nome_guilda, canal_id):
    avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
    nome_guilda_fmt = "Hades" if nome_guilda == "hades" else "Hades 2"
    bandeira = IDIOMAS.get(ficha.get("idioma"), {}).get("bandeira", "")
    discord_id = ficha.get("discord", None)
    member = None
    canal = bot.get_channel(canal_id)
    if canal and discord_id and str(discord_id).isdigit():
        member = canal.guild.get_member(int(discord_id))
    discord_str = member.mention if member else (f"<@{discord_id}>" if discord_id else user.mention)
    embed = discord.Embed(
        title=f"🌌 Ficha de Jogador #{ficha['numero']} – Arise Crossover {bandeira} 🌌",
        color=discord.Color.purple()
    )
    embed.add_field(name="🎮 Roblox", value=ficha['roblox'], inline=False)
    embed.add_field(name="🏰 Guilda", value=nome_guilda_fmt, inline=True)
    embed.add_field(name="💬 Discord", value=discord_str, inline=True)
    embed.add_field(name="⚔️ DPS", value=ficha['dps'], inline=False)
    embed.add_field(name="💎 Farm", value=ficha['farm'], inline=False)
    embed.add_field(
        name="📊 Outras Informações",
        value=f"🔹 Rank: {ficha['rank']}\n🔹 Level: {ficha['level']}\n🔹 Tempo: {ficha['tempo']}",
        inline=False
    )
    embed.set_footer(text=f"📆 Data da ficha: {ficha['data']}")
    embed.set_thumbnail(url=avatar_url)
    if canal:
        await canal.send(embed=embed)

async def iniciar_formulario(bot, interaction, idioma, canal, nome_guilda, target_user):
    perguntas = IDIOMAS[idioma]["perguntas"]
    respostas = await fazer_perguntas(interaction, canal, idioma, perguntas, target_user)
    if respostas is None:
        return
    data_atual = datetime.now().strftime("%d/%m/%Y")
    user_id = target_user.id
    ficha_existente = carregar_ficha(user_id, nome_guilda, idioma)
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
        "guilda": nome_guilda,
        "discord": str(target_user.id)
    }
    salvar_ficha(user_id, ficha, nome_guilda, idioma)
    marcar_preencheu(user_id, nome_guilda, idioma)
    canal_destino = FICHAS_CANAL_ID if nome_guilda == "hades" else FICHAS_CANAL_HADES2_ID
    await enviar_ficha_no_canal(bot, target_user, idioma, ficha, nome_guilda, canal_destino)
    await canal.send(f"{target_user.mention} sua ficha foi enviada no canal de fichas!")

# ----------- COMANDO SLASH PARA EDITAR FICHA (EXPERIÊNCIA IGUAL /ver_ficha) --------------
@bot.tree.command(name="editar_ficha", description="Editar ficha de jogador (ADM)")
@app_commands.describe(
    numero="Número da ficha",
    guilda="Selecione a guilda (hades ou hades2)",
    idioma="Selecione o idioma (pt, en, es)",
    campo="Campo a editar",
    valor="Novo valor (se campo for Discord, marque o usuário)"
)
@app_commands.choices(
    guilda=[
        app_commands.Choice(name="Hades", value="hades"),
        app_commands.Choice(name="Hades 2", value="hades2"),
    ],
    idioma=[
        app_commands.Choice(name="Português", value="pt"),
        app_commands.Choice(name="Inglês", value="en"),
        app_commands.Choice(name="Espanhol", value="es"),
    ],
    campo=[
        app_commands.Choice(name=label, value=campo) for campo, label in CAMPOS_EDITAVEIS
    ]
)
@app_commands.default_permissions(administrator=True)
async def editar_ficha(
    interaction: discord.Interaction,
    numero: int,
    guilda: app_commands.Choice[str],
    idioma: app_commands.Choice[str],
    campo: app_commands.Choice[str],
    valor: str
):
    uid, ficha = carregar_ficha_por_numero(numero, guilda.value, idioma.value)
    if not ficha:
        await interaction.response.send_message("❌ Ficha não encontrada.", ephemeral=True)
        return
    novo_valor = valor
    if campo.value == "discord":
        # Extrai o ID do usuário mencionado (se vier em formato <@id>)
        user_id = None
        for word in valor.split():
            if word.startswith("<@") and word.endswith(">"):
                user_id = word.replace("<@", "").replace(">", "").replace("!", "")
        if user_id:
            novo_valor = user_id
    ficha[campo.value] = novo_valor
    salvar_ficha_por_uid(uid, ficha, guilda.value, idioma.value)
    display = f"<@{novo_valor}>" if campo.value == "discord" else novo_valor
    await interaction.response.send_message(
        f"✅ Ficha número {numero} da guilda {guilda.value} atualizada!\nCampo **{campo.value}** corrigido para: {display}",
        ephemeral=True
    )

# ---- O RESTANTE DO SEU CÓDIGO (Parte 2 etc) SEGUE IGUAL ----
# ... (não alterado aqui para focar só na Parte 1)

keep_alive()
bot.run(TOKEN)