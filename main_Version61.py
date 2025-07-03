import discord
from discord.ext import commands, tasks
from discord import app_commands, ui
import json
import os
from datetime import datetime
from keep_alive import keep_alive

TOKEN = os.getenv('DISCORD_TOKEN')
FICHAS_CANAL_ID = 1386798237163323493
FICHAS_CANAL_HADES2_ID = 1388546663190364241
CANAL_ARQUIVO_FICHAS_ID = 1386832198405193868

NUMERO_FICHA_PADRAO = {"hades": 66, "hades2": 7}
IDIOMAS = {
    "pt": {"nome": "Português", "bandeira": "🇧🇷"},
    "en": {"nome": "English", "bandeira": "🇺🇸"},
    "es": {"nome": "Español", "bandeira": "🇪🇸"}
}

TEXTOS = {
    "pt": {
        "perguntas": [
            ("🎮 Nick no Roblox:", "roblox"),
            ("⚔️ DPS Atual:", "dps"),
            ("💎 Farm diário de gemas:", "farm"),
            ("🔹 Rank:", "rank"),
            ("🔹 Level:", "level"),
            ("🔹 Tempo de jogo:", "tempo")
        ],
        "confirmar_envio": "Deseja enviar essa ficha?",
        "refazer_pergunta": "Você quer refazer a ficha?",
        "sim": "Sim",
        "nao": "Não",
        "enviada": "✅ Ficha enviada com sucesso!",
        "refazendo": "Vamos recomeçar o preenchimento da ficha!",
        "cancelada": "Ok! Ficha não enviada. Caso queira, use /ficha novamente.",
        "preenchida": "✅ Preenchimento da ficha concluído! Aguarde confirmação para enviar..."
    },
    "en": {
        "perguntas": [
            ("🎮 Roblox username:", "roblox"),
            ("⚔️ Current DPS:", "dps"),
            ("💎 Daily gems farm:", "farm"),
            ("🔹 Rank:", "rank"),
            ("🔹 Level:", "level"),
            ("🔹 Playtime:", "tempo")
        ],
        "confirmar_envio": "Do you want to submit this form?",
        "refazer_pergunta": "Do you want to redo the form?",
        "sim": "Yes",
        "nao": "No",
        "enviada": "✅ Form submitted successfully!",
        "refazendo": "Let's start filling out the form again!",
        "cancelada": "Okay! Form not sent. If you want, use /ficha again.",
        "preenchida": "✅ Form completed! Please confirm to submit..."
    },
    "es": {
        "perguntas": [
            ("🎮 Usuario de Roblox:", "roblox"),
            ("⚔️ DPS actual:", "dps"),
            ("💎 Farmeo diario de gemas:", "farm"),
            ("🔹 Rango:", "rank"),
            ("🔹 Nivel:", "level"),
            ("🔹 Tiempo de juego:", "tempo")
        ],
        "confirmar_envio": "¿Desea enviar este formulario?",
        "refazer_pergunta": "¿Desea rehacer el formulario?",
        "sim": "Sí",
        "nao": "No",
        "enviada": "✅ ¡Ficha enviada con éxito!",
        "refazendo": "¡Vamos a empezar de nuevo a completar la ficha!",
        "cancelada": "¡Ok! Ficha no enviada. Si desea, use /ficha de nuevo.",
        "preenchida": "✅ ¡Ficha completada! Por favor, confirme para enviar..."
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

def remover_ficha_por_uid(uid, guilda, idioma):
    arquivo = arquivo_fichas(guilda, idioma)
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            todas = json.load(f)
    except Exception:
        todas = {}
    if uid in todas:
        del todas[uid]
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(todas, f, indent=4, ensure_ascii=False)

def carregar_numero_ficha(guilda):
    try:
        with open(f"numero_ficha_{guilda}.json", "r", encoding="utf-8") as f:
            return json.load(f).get("numero", NUMERO_FICHA_PADRAO[guilda])
    except:
        return NUMERO_FICHA_PADRAO[guilda]

def salvar_numero_ficha(guilda, n):
    with open(f"numero_ficha_{guilda}.json", "w", encoding="utf-8") as f:
        json.dump({"numero": n}, f)

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
        canal = await self.bot.fetch_channel(self.canal_id)
        await iniciar_formulario(self.bot, interaction, idioma, canal, self.nome_guilda, self.target_user)

async def fazer_perguntas(interaction, canal, idioma, target_user):
    respostas = {}
    perguntas = TEXTOS[idioma]["perguntas"]
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
    discord_id = ficha.get("discord", None)
    member = None
    canal = bot.get_channel(canal_id)
    if discord_id and str(discord_id).isdigit() and canal and canal.guild:
        member = canal.guild.get_member(int(discord_id))
    if member:
        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
        display_name = member.display_name
    else:
        avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
        display_name = user.display_name

    nome_guilda_fmt = "Hades" if nome_guilda == "hades" else "Hades 2"
    bandeira = IDIOMAS.get(ficha.get("idioma"), {}).get("bandeira", "")
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

# ========== NOVO FLUXO DE FICHA COM CONFIRMAÇÃO E MULTI-IDIOMA ==========
class ConfirmarFichaView(ui.View):
    def __init__(self, ficha_data, canal_destino, user, guilda, idioma, canal, bot_refazer):
        super().__init__(timeout=60)
        self.ficha_data = ficha_data
        self.canal_destino = canal_destino
        self.user = user
        self.guilda = guilda
        self.idioma = idioma
        self.canal = canal
        self.bot_refazer = bot_refazer

        # Botões multi-idioma:
        self.confirmar_button = ui.Button(label=TEXTOS[self.idioma]["sim"], style=discord.ButtonStyle.success, emoji="✅")
        self.cancelar_button = ui.Button(label=TEXTOS[self.idioma]["nao"], style=discord.ButtonStyle.danger, emoji="❌")
        self.confirmar_button.callback = self.confirmar
        self.cancelar_button.callback = self.recusar
        self.add_item(self.confirmar_button)
        self.add_item(self.cancelar_button)

    async def confirmar(self, interaction: discord.Interaction):
        user_id = self.user.id
        ficha_existente = carregar_ficha(user_id, self.guilda, self.idioma)
        if ficha_existente:
            numero_ficha = ficha_existente["numero"]
        else:
            numero_ficha = carregar_numero_ficha(self.guilda) + 1
            salvar_numero_ficha(self.guilda, numero_ficha)
        self.ficha_data["numero"] = numero_ficha
        salvar_ficha(user_id, self.ficha_data, self.guilda, self.idioma)
        await enviar_ficha_no_canal(interaction.client, self.user, self.idioma, self.ficha_data, self.guilda, self.canal_destino)
        await self.canal.send(f"{self.user.mention} {TEXTOS[self.idioma]['enviada']}")
        await interaction.response.edit_message(content=TEXTOS[self.idioma]['enviada'], embed=None, view=None)

    async def recusar(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=TEXTOS[self.idioma]['refazer_pergunta'],
            embed=None,
            view=RefazerFichaView(self.bot_refazer, self.canal, self.user, self.guilda, self.idioma)
        )

class RefazerFichaView(ui.View):
    def __init__(self, bot_refazer, canal, user, guilda, idioma):
        super().__init__(timeout=45)
        self.bot_refazer = bot_refazer
        self.canal = canal
        self.user = user
        self.guilda = guilda
        self.idioma = idioma

        # Botões multi-idioma:
        self.sim_button = ui.Button(label=TEXTOS[self.idioma]["sim"], style=discord.ButtonStyle.primary, emoji="🔄")
        self.nao_button = ui.Button(label=TEXTOS[self.idioma]["nao"], style=discord.ButtonStyle.secondary, emoji="⏹️")
        self.sim_button.callback = self.refazer
        self.nao_button.callback = self.parar
        self.add_item(self.sim_button)
        self.add_item(self.nao_button)

    async def refazer(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content=TEXTOS[self.idioma]['refazendo'], view=None)
        await self.bot_refazer(self.canal, self.user, self.guilda, self.idioma)

    async def parar(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content=TEXTOS[self.idioma]['cancelada'], view=None)

async def finalizar_ficha(interaction, user, ficha_data, guilda, idioma, canal_destino, canal, bot_refazer):
    bandeira = IDIOMAS.get(idioma, {}).get("bandeira", "")
    embed = discord.Embed(
        title=f"Confira sua ficha antes de enviar! {bandeira}",
        color=discord.Color.blurple()
    )
    embed.add_field(name="🎮 Roblox", value=ficha_data['roblox'], inline=False)
    embed.add_field(name="⚔️ DPS", value=ficha_data['dps'], inline=True)
    embed.add_field(name="💎 Farm", value=ficha_data['farm'], inline=True)
    embed.add_field(name="🔹 Rank", value=ficha_data['rank'], inline=True)
    embed.add_field(name="🔹 Level", value=ficha_data['level'], inline=True)
    embed.add_field(name="🔹 Tempo", value=ficha_data['tempo'], inline=True)
    embed.set_footer(text=f"Data: {ficha_data['data']} | Guilda: {guilda} | Idioma: {idioma}")
    view = ConfirmarFichaView(
        ficha_data, canal_destino, user, guilda, idioma, canal, bot_refazer
    )
    await interaction.followup.send(
        content=TEXTOS[idioma]['confirmar_envio'],
        embed=embed,
        view=view,
        ephemeral=True
    )

async def iniciar_formulario(bot, interaction, idioma, canal, nome_guilda, target_user):
    async def refazer(canal, user, guilda, idioma):
        await iniciar_formulario(bot, interaction, idioma, canal, guilda, user)
    respostas = await fazer_perguntas(interaction, canal, idioma, target_user)
    if respostas is None:
        return
    data_atual = datetime.now().strftime("%d/%m/%Y")
    user_id = target_user.id
    ficha_existente = carregar_ficha(user_id, nome_guilda, idioma)
    ficha = {
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
    canal_destino = FICHAS_CANAL_ID if nome_guilda == "hades" else FICHAS_CANAL_HADES2_ID
    await interaction.followup.send(TEXTOS[idioma]['preenchida'], ephemeral=True)
    await finalizar_ficha(interaction, target_user, ficha, nome_guilda, idioma, canal_destino, canal, refazer)