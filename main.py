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
    # Corrigido: avatar e menção pelo campo Discord
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

async def iniciar_formulario(bot, interaction, idioma, canal, nome_guilda, target_user):
    perguntas = [
        ("🎮 Nick no Roblox:", "roblox"),
        ("⚔️ DPS Atual:", "dps"),
        ("💎 Farm diário de gemas:", "farm"),
        ("🔹 Rank:", "rank"),
        ("🔹 Level:", "level"),
        ("🔹 Tempo de jogo:", "tempo")
    ]
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
    canal_destino = FICHAS_CANAL_ID if nome_guilda == "hades" else FICHAS_CANAL_HADES2_ID
    await enviar_ficha_no_canal(bot, target_user, idioma, ficha, nome_guilda, canal_destino)
    await canal.send(f"{target_user.mention} sua ficha foi enviada no canal de fichas!")

# --- ARQUIVAR FICHA COM SELECT MENU ---
class ArquivarFichaMotivoView(ui.View):
    def __init__(self, interaction, numero, guilda, idioma, uid, ficha):
        super().__init__(timeout=60)
        self.numero = numero
        self.guilda = guilda
        self.idioma = idioma
        self.uid = uid
        self.ficha = ficha
        self.motivos = [
            ("saiu", f"❌ Jogador saiu da guilda"),
            ("expulso", f"❌ Jogador foi expulso"),
            ("trocou", f"🔄 Jogador trocou de guilda"),
        ]
        self.select = ui.Select(
            placeholder="Escolha o motivo do arquivamento",
            options=[
                discord.SelectOption(label=label, value=value, emoji=label[0])
                for value, label in self.motivos
            ],
            custom_id="motivo_arquivamento"
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: discord.Interaction):
        motivo = self.select.values[0]
        hoje = datetime.now().strftime("%d/%m/%Y")
        if motivo == "saiu":
            msg_motivo = f"❌ Jogador saiu da guilda {hoje}"
        elif motivo == "expulso":
            msg_motivo = f"❌ Jogador foi expulso {hoje}"
        else:
            msg_motivo = f"🔄 Jogador trocou de guilda {hoje}"
        canal = bot.get_channel(CANAL_ARQUIVO_FICHAS_ID)
        ficha = self.ficha
        bandeira = IDIOMAS.get(ficha.get("idioma"), {}).get("bandeira", "")
        discord_id = ficha.get("discord", None)
        member = None
        if discord_id and str(discord_id).isdigit() and interaction.guild:
            member = interaction.guild.get_member(int(discord_id))
        discord_str = member.mention if member else f"<@{discord_id}>" if discord_id else "-"
        embed = discord.Embed(
            title=f"🌌 Ficha Arquivada #{ficha['numero']} – Arise Crossover {bandeira} 🌌",
            color=discord.Color.dark_red()
        )
        embed.add_field(name="🎮 Roblox", value=ficha['roblox'], inline=False)
        embed.add_field(name="🏰 Guilda", value=self.guilda, inline=True)
        embed.add_field(name="💬 Discord", value=discord_str, inline=True)
        embed.add_field(name="⚔️ DPS", value=ficha['dps'], inline=False)
        embed.add_field(name="💎 Farm", value=ficha['farm'], inline=False)
        embed.add_field(
            name="📊 Outras Informações",
            value=f"🔹 Rank: {ficha['rank']}\n🔹 Level: {ficha['level']}\n🔹 Tempo: {ficha['tempo']}",
            inline=False
        )
        embed.set_footer(text=f"📆 Data da ficha: {ficha['data']}")
        if member:
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        if canal:
            await canal.send(content=msg_motivo, embed=embed)
        remover_ficha_por_uid(self.uid, self.guilda, self.idioma)
        await interaction.response.edit_message(content=f"Ficha arquivada e enviada para <#{CANAL_ARQUIVO_FICHAS_ID}> com motivo: {msg_motivo}", embed=None, view=None)

# ----------- SLASH COMMANDS DE FICHA -----------

@bot.tree.command(name="ficha", description="Preencher ficha de jogador (Hades)")
@app_commands.describe(usuario="(Opcional) Usuário para responder a ficha")
async def slash_ficha(interaction: discord.Interaction, usuario: discord.Member = None):
    canal_id = interaction.channel.id
    canal_nome = interaction.channel.name
    canal_mencao = interaction.channel.mention
    if usuario is None or usuario == interaction.user:
        view = MenuIdioma(bot, canal_id, "hades", interaction.user, canal_nome, canal_mencao)
        await interaction.response.send_message(
            f"📄 Clique abaixo para escolher o idioma.\n"
            "Só quem for convidado poderá interagir.\n"
            "⚠️ Você só pode ter UMA ficha registrada. Preencher de novo irá editar sua ficha!\n"
            f"Número inicial da ficha: **{carregar_numero_ficha('hades')}**",
            view=view,
            ephemeral=True
        )
    else:
        view = MenuIdioma(bot, canal_id, "hades", usuario, canal_nome, canal_mencao)
        try:
            await usuario.send(
                f"📄 Você foi convidado a preencher a ficha da guilda **Hades** por {interaction.user.mention}!\n"
                "Selecione o idioma abaixo para começar.",
                view=view
            )
            await interaction.response.send_message(f"✉️ Convite enviado por DM para {usuario.mention}!", ephemeral=True)
        except Exception:
            await interaction.response.send_message(f"❌ Não consegui enviar DM para {usuario.mention}. Peça para liberar DMs!", ephemeral=True)
@bot.tree.command(name="edit_numero_ficha", description="Editar o número inicial das fichas de uma guilda (ADM)")
@app_commands.describe(guilda="Guilda (hades ou hades2)", numero="Novo número inicial")
@app_commands.choices(
    guilda=[
        app_commands.Choice(name="Hades", value="hades"),
        app_commands.Choice(name="Hades 2", value="hades2"),
    ]
)
@app_commands.default_permissions(administrator=True)
async def edit_numero_ficha(
    interaction: discord.Interaction,
    guilda: app_commands.Choice[str],
    numero: int
):
    salvar_numero_ficha(guilda.value, numero)
    await interaction.response.send_message(
        f"✅ Número inicial das fichas da guilda **{guilda.name}** atualizado para {numero}.",
        ephemeral=True
)
@bot.tree.command(name="ficha_hades2", description="Preencher ficha de jogador (Hades 2)")
@app_commands.describe(usuario="(Opcional) Usuário para responder a ficha")
async def slash_ficha_hades2(interaction: discord.Interaction, usuario: discord.Member = None):
    canal_id = interaction.channel.id
    canal_nome = interaction.channel.name
    canal_mencao = interaction.channel.mention
    if usuario is None or usuario == interaction.user:
        view = MenuIdioma(bot, canal_id, "hades2", interaction.user, canal_nome, canal_mencao)
        await interaction.response.send_message(
            f"📄 Clique abaixo para escolher o idioma.\n"
            "Só quem for convidado poderá interagir.\n"
            "⚠️ Você só pode ter UMA ficha registrada. Preencher de novo irá editar sua ficha!\n"
            f"Número inicial da ficha: **{carregar_numero_ficha('hades2')}**",
            view=view,
            ephemeral=True
        )
    else:
        view = MenuIdioma(bot, canal_id, "hades2", usuario, canal_nome, canal_mencao)
        try:
            await usuario.send(
                f"📄 Você foi convidado a preencher a ficha da guilda **Hades 2** por {interaction.user.mention}!\n"
                "Selecione o idioma abaixo para começar.",
                view=view
            )
            await interaction.response.send_message(f"✉️ Convite enviado por DM para {usuario.mention}!", ephemeral=True)
        except Exception:
            await interaction.response.send_message(f"❌ Não consegui enviar DM para {usuario.mention}. Peça para liberar DMs!", ephemeral=True)

@bot.tree.command(name="ver_ficha", description="Ver ficha de jogador")
@app_commands.describe(numero="Número da ficha", guilda="Guilda", idioma="Idioma")
@app_commands.choices(
    guilda=[
        app_commands.Choice(name="Hades", value="hades"),
        app_commands.Choice(name="Hades 2", value="hades2"),
    ],
    idioma=[
        app_commands.Choice(name="Português", value="pt"),
        app_commands.Choice(name="Inglês", value="en"),
        app_commands.Choice(name="Espanhol", value="es"),
    ]
)
async def ver_ficha(
    interaction: discord.Interaction,
    numero: int,
    guilda: app_commands.Choice[str],
    idioma: app_commands.Choice[str]
):
    uid, ficha = carregar_ficha_por_numero(numero, guilda.value, idioma.value)
    if not ficha:
        await interaction.response.send_message("❌ Ficha não encontrada.", ephemeral=True)
        return
    discord_id = ficha.get("discord", None)
    member = None
    if discord_id and str(discord_id).isdigit() and interaction.guild:
        member = interaction.guild.get_member(int(discord_id))
    bandeira = IDIOMAS.get(ficha.get("idioma"), {}).get("bandeira", "")
    discord_str = member.mention if member else (f"<@{discord_id}>" if discord_id else "-")
    embed = discord.Embed(
        title=f"🌌 Ficha de Jogador #{ficha['numero']} – Arise Crossover {bandeira} 🌌",
        color=discord.Color.purple()
    )
    embed.add_field(name="🎮 Roblox", value=ficha['roblox'], inline=False)
    embed.add_field(name="🏰 Guilda", value=guilda.name, inline=True)
    embed.add_field(name="💬 Discord", value=discord_str, inline=True)
    embed.add_field(name="⚔️ DPS", value=ficha['dps'], inline=False)
    embed.add_field(name="💎 Farm", value=ficha['farm'], inline=False)
    embed.add_field(
        name="📊 Outras Informações",
        value=f"🔹 Rank: {ficha['rank']}\n🔹 Level: {ficha['level']}\n🔹 Tempo: {ficha['tempo']}",
        inline=False
    )
    embed.set_footer(text=f"📆 Data da ficha: {ficha['data']}")
    if member:
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="editar_ficha", description="Editar uma informação específica da ficha (ADM)")
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
        user_id = None
        # Corrigido: aceita menção ou ID puro!
        if valor.startswith("<@") and valor.endswith(">"):
            user_id = valor.replace("<@", "").replace(">", "").replace("!", "")
            novo_valor = user_id
        elif valor.isdigit():
            novo_valor = valor
        else:
            novo_valor = valor  # fallback
    ficha[campo.value] = novo_valor
    salvar_ficha_por_uid(uid, ficha, guilda.value, idioma.value)
    # Mostra menção azul se possível
    discord_str = f"<@{novo_valor}>" if campo.value == "discord" and novo_valor.isdigit() else novo_valor
    await interaction.response.send_message(
        f"✅ Ficha número {numero} da guilda {guilda.value} atualizada!\nCampo **{campo.value}** corrigido para: {discord_str}",
        ephemeral=True
    )

@bot.tree.command(name="arquivar_ficha", description="Arquiva a ficha de um jogador e envia ao canal de arquivo (ADM)")
@app_commands.choices(
    guilda=[
        app_commands.Choice(name="Hades", value="hades"),
        app_commands.Choice(name="Hades 2", value="hades2"),
    ],
    idioma=[
        app_commands.Choice(name="Português", value="pt"),
        app_commands.Choice(name="Inglês", value="en"),
        app_commands.Choice(name="Espanhol", value="es"),
    ]
)
@app_commands.describe(
    numero="Número da ficha",
    guilda="Selecione a guilda (hades ou hades2)",
    idioma="Selecione o idioma (pt, en, es)"
)
@app_commands.default_permissions(administrator=True)
async def arquivar_ficha(
    interaction: discord.Interaction,
    numero: int,
    guilda: app_commands.Choice[str],
    idioma: app_commands.Choice[str]
):
    uid, ficha = carregar_ficha_por_numero(numero, guilda.value, idioma.value)
    if not ficha:
        await interaction.response.send_message("❌ Ficha não encontrada.", ephemeral=True)
        return
    view = ArquivarFichaMotivoView(interaction, numero, guilda.name, idioma.name, uid, ficha)
    await interaction.response.send_message("Escolha o motivo do arquivamento:", view=view, ephemeral=True)

@bot.tree.command(name="minha_ficha", description="Veja rapidamente sua ficha cadastrada em uma guilda/idioma")
@app_commands.choices(
    guilda=[
        app_commands.Choice(name="Hades", value="hades"),
        app_commands.Choice(name="Hades 2", value="hades2"),
    ],
    idioma=[
        app_commands.Choice(name="Português", value="pt"),
        app_commands.Choice(name="Inglês", value="en"),
        app_commands.Choice(name="Espanhol", value="es"),
    ]
)
async def minha_ficha(
    interaction: discord.Interaction,
    guilda: app_commands.Choice[str],
    idioma: app_commands.Choice[str]
):
    ficha = carregar_ficha(interaction.user.id, guilda.value, idioma.value)
    if not ficha:
        await interaction.response.send_message("❌ Você não possui ficha cadastrada nessa guilda/idioma.", ephemeral=True)
        return
    discord_id = ficha.get("discord", interaction.user.id)
    member = None
    if discord_id and str(discord_id).isdigit() and interaction.guild:
        member = interaction.guild.get_member(int(discord_id))
    discord_str = member.mention if member else f"<@{discord_id}>" if discord_id else "-"
    bandeira = IDIOMAS.get(ficha.get("idioma"), {}).get("bandeira", "")
    embed = discord.Embed(
        title=f"🌌 Ficha de Jogador #{ficha['numero']} – Arise Crossover {bandeira} 🌌",
        color=discord.Color.purple()
    )
    embed.add_field(name="🎮 Roblox", value=ficha['roblox'], inline=False)
    embed.add_field(name="🏰 Guilda", value=guilda.name, inline=True)
    embed.add_field(name="💬 Discord", value=discord_str, inline=True)
    embed.add_field(name="⚔️ DPS", value=ficha['dps'], inline=False)
    embed.add_field(name="💎 Farm", value=ficha['farm'], inline=False)
    embed.add_field(
        name="📊 Outras Informações",
        value=f"🔹 Rank: {ficha['rank']}\n🔹 Level: {ficha['level']}\n🔹 Tempo: {ficha['tempo']}",
        inline=False
    )
    embed.set_footer(text=f"📆 Data da ficha: {ficha['data']}")
    if member:
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)
# ========= PARTE 2 =========

ARQUIVO = 'servidores.json'
ARQUIVO_ENVIOS = 'envios.json'
AVISOS_CONFIG = 'avisos_config.json'
CANAL_AVISOS_ID = 1380022433288949851
CARGO_ANALISE_ID = 1379508463172063286
CANAL_2DIAS_ID = 1379585139629228062
CARGO_2DIAS_ID = 1379508463172063290

import pytz

# ----------- SERVIDORES --------------
def carregar_servidores():
    if not os.path.exists(ARQUIVO):
        return []
    with open(ARQUIVO, 'r') as f:
        return json.load(f)
def salvar_servidores(lista):
    with open(ARQUIVO, 'w') as f:
        json.dump(lista, f, indent=4)

@bot.tree.command(name="adicionar_servidor", description="Adiciona ou atualiza um servidor com nome, link e foto opcional")
@app_commands.describe(nome="Nome do servidor", link="Link do servidor", membro="(Opcional) Membro para foto/autor")
async def adicionar_servidor_slash(interaction: discord.Interaction, nome: str, link: str, membro: discord.Member = None):
    servidores = carregar_servidores()
    autor_id = membro.id if membro else None
    for servidor in servidores:
        if servidor['nome'].lower() == nome.lower():
            servidor['link'] = link
            servidor['autor_id'] = autor_id
            salvar_servidores(servidores)
            await interaction.response.send_message(f"🔁 Servidor **{nome}** atualizado!", ephemeral=True)
            return
    servidores.append({'nome': nome, 'link': link, 'autor_id': autor_id})
    salvar_servidores(servidores)
    await interaction.response.send_message(f"✅ Servidor **{nome}** adicionado com sucesso!", ephemeral=True)

@bot.tree.command(name="remover_servidor", description="Remove um servidor salvo pelo nome")
@app_commands.describe(nome="Nome do servidor")
async def remover_servidor_slash(interaction: discord.Interaction, nome: str):
    servidores = carregar_servidores()
    nome_lower = nome.lower()
    novos = [s for s in servidores if s['nome'].lower() != nome_lower]
    if len(novos) == len(servidores):
        await interaction.response.send_message(f"❌ Nenhum servidor chamado **{nome}** encontrado.", ephemeral=True)
        return
    salvar_servidores(novos)
    await interaction.response.send_message(f"🗑️ Servidor **{nome}** removido com sucesso!", ephemeral=True)

@bot.tree.command(name="atualizar_servidor", description="Atualiza a imagem do servidor com o avatar da pessoa mencionada")
@app_commands.describe(nome="Nome do servidor", membro="Membro para atualizar foto")
async def atualizar_servidor_slash(interaction: discord.Interaction, nome: str, membro: discord.Member):
    servidores = carregar_servidores()
    for servidor in servidores:
        if servidor['nome'].lower() == nome.lower():
            servidor['autor_id'] = membro.id
            salvar_servidores(servidores)
            await interaction.response.send_message(f"✅ Foto do servidor **{nome}** atualizada para **{membro.display_name}**.", ephemeral=True)
            return
    await interaction.response.send_message(f"❌ Servidor **{nome}** não encontrado.", ephemeral=True)

@bot.tree.command(name="servidores", description="Lista todos os servidores com botão de entrada")
async def servidores_slash(interaction: discord.Interaction):
    servidores = carregar_servidores()
    if not servidores:
        await interaction.response.send_message("❌ Nenhum servidor foi adicionado ainda.", ephemeral=True)
        return
    for servidor in servidores:
        embed = discord.Embed(
            title=servidor["nome"],
            description="Clique no botão abaixo para entrar no servidor do Roblox.",
            color=discord.Color.green()
        )
        autor_id = servidor.get("autor_id")
        if autor_id:
            membro = interaction.guild.get_member(autor_id)
            if membro:
                embed.set_author(name=membro.display_name, icon_url=membro.avatar.url if membro.avatar else None)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="🎮 Jogar agora", url=servidor["link"]))
        await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("Lista de servidores enviada!", ephemeral=True)

@bot.tree.command(name="servidor", description="Mostra somente o servidor especificado")
@app_commands.describe(nome="Nome do servidor")
async def servidor_slash(interaction: discord.Interaction, nome: str):
    servidores = carregar_servidores()
    nome_lower = nome.lower()
    for servidor in servidores:
        if servidor["nome"].lower() == nome_lower:
            embed = discord.Embed(
                title=servidor["nome"],
                description="Clique no botão abaixo para entrar no servidor do Roblox.",
                color=discord.Color.green()
            )
            autor_id = servidor.get("autor_id")
            if autor_id:
                membro = interaction.guild.get_member(autor_id)
                if membro:
                    embed.set_author(name=membro.display_name, icon_url=membro.avatar.url if membro.avatar else None)
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="🎮 Jogar agora", url=servidor["link"]))
            await interaction.channel.send(embed=embed, view=view)
            await interaction.response.send_message(f"Servidor **{nome}** encontrado!", ephemeral=True)
            return
    await interaction.response.send_message(f"❌ Servidor **{nome}** não foi encontrado.", ephemeral=True)

# ----------- AVISOS --------------
def carregar_envios():
    if not os.path.exists(ARQUIVO_ENVIOS):
        return {}
    with open(ARQUIVO_ENVIOS, 'r') as f:
        return json.load(f)
def salvar_envios(dados):
    with open(ARQUIVO_ENVIOS, 'w') as f:
        json.dump(dados, f, indent=4)
envios = carregar_envios()
def get_data_ultimo_envio(chave):
    data_str = envios.get(chave)
    if data_str:
        try:
            dt = datetime.fromisoformat(data_str)
            if dt.tzinfo is None:
                brasilia_tz = pytz.timezone('America/Sao_Paulo')
                dt = brasilia_tz.localize(dt)
            return dt
        except Exception:
            return None
    return None
def set_data_ultimo_envio(chave):
    brasilia_tz = pytz.timezone('America/Sao_Paulo')
    agora_brasilia = datetime.now(brasilia_tz)
    envios[chave] = agora_brasilia.isoformat()
    salvar_envios(envios)
def get_hora_brasilia():
    brasilia_tz = pytz.timezone('America/Sao_Paulo')
    return datetime.now(brasilia_tz)
def carregar_aviso(tipo):
    if not os.path.exists(AVISOS_CONFIG):
        return {}
    with open(AVISOS_CONFIG, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config.get(tipo, {})
async def enviar_aviso(tipo, canal_id, cargo_id, texto_padrao):
    canal = bot.get_channel(canal_id)
    if not canal:
        print("[ERRO] Canal de avisos não encontrado.")
        return
    cargo = canal.guild.get_role(cargo_id)
    if not cargo:
        print("[ERRO] Cargo de aviso não encontrado.")
        return
    dados = carregar_aviso(tipo)
    if dados:
        embed = discord.Embed(
            title=dados.get("titulo", "⏳ Guild Donation Coming Up"),
            description=dados.get("descricao", "Prepare your donations in advance!"),
            color=0x192A56
        )
        if dados.get("imagem"):
            embed.set_image(url=dados["imagem"])
        await canal.send(content=cargo.mention, embed=embed)
    else:
        await canal.send(f"{texto_padrao}\n{cargo.mention}")

@bot.event
async def on_ready():
    print(f'✅ {bot.user} está online!')
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Sincronizados {len(synced)} comandos slash")
    except Exception as e:
        print(f"❌ Erro ao sincronizar slash commands: {e}")
    enviar_aviso_diario.start()
    aviso_cada_2_dias.start()
    keep_alive_task.start()

@tasks.loop(minutes=1)
async def enviar_aviso_diario():
    agora = get_hora_brasilia()
    if agora.hour == 15 and agora.minute == 0:
        ultimo = get_data_ultimo_envio("ultimo_aviso_diario")
        if not ultimo or (agora.date() > ultimo.date()):
            await enviar_aviso("diario", CANAL_AVISOS_ID, CARGO_ANALISE_ID, "# 📝 Verifiquem a Entrada/diaria e abra seu ticket!")
            set_data_ultimo_envio("ultimo_aviso_diario")

@tasks.loop(minutes=1)
async def aviso_cada_2_dias():
    agora = get_hora_brasilia()
    if agora.hour == 15 and agora.minute == 0:
        ultimo = get_data_ultimo_envio("ultimo_aviso_2dias")
        if not ultimo or (agora - ultimo).total_seconds() >= 172800:
            await enviar_aviso("2dias", CANAL_2DIAS_ID, CARGO_2DIAS_ID, "# 📝 Mande sua meta diária e ajude a guilda a evoluir!")
            set_data_ultimo_envio("ultimo_aviso_2dias")

@tasks.loop(minutes=5)
async def keep_alive_task():
    pass

@bot.tree.command(name="enviar_aviso_diario", description="Envia aviso diário manualmente")
@app_commands.default_permissions(administrator=True)
async def slash_enviar_aviso_diario(interaction: discord.Interaction):
    await enviar_aviso("diario", CANAL_AVISOS_ID, CARGO_ANALISE_ID, "# 📝 Verifiquem a Entrada/diaria e abra seu ticket!")
    set_data_ultimo_envio("ultimo_aviso_diario")
    await interaction.response.send_message("✅ Aviso diário enviado manualmente.", ephemeral=True)

@bot.tree.command(name="enviar_aviso_2dias", description="Envia aviso de 2 dias manualmente")
@app_commands.default_permissions(administrator=True)
async def slash_enviar_aviso_2dias(interaction: discord.Interaction):
    await enviar_aviso("2dias", CANAL_2DIAS_ID, CARGO_2DIAS_ID, "# 📝 Mande sua meta diária e ajude a guilda a evoluir!")
    set_data_ultimo_envio("ultimo_aviso_2dias")
    await interaction.response.send_message("✅ Aviso de 2 dias enviado manualmente.", ephemeral=True)

@bot.tree.command(name="editar_aviso_diario", description="Edite o aviso diário com título, descrição e imagem")
@app_commands.default_permissions(administrator=True)
async def editar_aviso_diario(interaction: discord.Interaction, titulo: str, descricao: str, imagem_url: str = None):
    if not os.path.exists(AVISOS_CONFIG):
        config = {}
    else:
        with open(AVISOS_CONFIG, 'r', encoding='utf-8') as f:
            config = json.load(f)
    config["diario"] = {
        "titulo": titulo,
        "descricao": descricao,
        "imagem": imagem_url
    }
    with open(AVISOS_CONFIG, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)
    await interaction.response.send_message("✅ Aviso diário atualizado com sucesso!", ephemeral=True)

@bot.tree.command(name="editar_aviso_2_dias", description="Edite o aviso de 2 dias com título, descrição e imagem")
@app_commands.default_permissions(administrator=True)
async def editar_aviso_2_dias(interaction: discord.Interaction, titulo: str, descricao: str, imagem_url: str = None):
    if not os.path.exists(AVISOS_CONFIG):
        config = {}
    else:
        with open(AVISOS_CONFIG, 'r', encoding='utf-8') as f:
            config = json.load(f)
    config["2dias"] = {
        "titulo": titulo,
        "descricao": descricao,
        "imagem": imagem_url
    }
    with open(AVISOS_CONFIG, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)
    await interaction.response.send_message("✅ Aviso de 2 dias atualizado com sucesso!", ephemeral=True)

# ----------- OUTROS SLASH --------------
@bot.tree.command(name="pingstaff", description="Envie uma mensagem anônima para o canal atual")
@app_commands.describe(mensagem="Mensagem que será enviada no canal, sem mostrar quem enviou")
async def pingstaff(interaction: discord.Interaction, mensagem: str):
    await interaction.channel.send(mensagem)
    await interaction.response.send_message("✅ Mensagem enviada anonimamente no canal!", ephemeral=True)

@bot.tree.command(name="ajuda", description="Mostra a lista de comandos disponíveis")
async def ajuda_slash(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌐 Comandos do Bot da HADES",
        description="Aqui estão todos os comandos disponíveis:",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="Fichas",
        value=(
            "/ficha [@usuário]\n"
            "/ficha_hades2 [@usuário]\n"
            "/ver_ficha\n"
            "/editar_ficha\n"
            "/arquivar_ficha\n"
            "/minha_ficha"
        ),
        inline=False
    )
    embed.add_field(
        name="Servidores",
        value=(
            "/adicionar_servidor <nome> <link> [@pessoa]\n"
            "/remover_servidor <nome>\n"
            "/atualizar_servidor <nome> @pessoa\n"
            "/servidores\n"
            "/servidor <nome>\n"
        ),
        inline=False
    )
    embed.add_field(
        name="Avisos",
        value=(
            "/enviar_aviso_diario\n"
            "/enviar_aviso_2dias\n"
            "/editar_aviso_diario\n"
            "/editar_aviso_2_dias\n"
        ),
        inline=False
    )
    embed.add_field(
        name="Outros",
        value="/pingstaff <mensagem>",
        inline=False
    )
    embed.set_footer(text="Bot para gerenciar e divulgar servidores Roblox.")
    await interaction.response.send_message(embed=embed, ephemeral=True)

keep_alive()
bot.run(TOKEN)
