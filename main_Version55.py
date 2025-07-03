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
        member = interaction.guild.get_member(int(discord_id)) if discord_id and str(discord_id).isdigit() else None
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
    member = interaction.guild.get_member(int(discord_id)) if discord_id and str(discord_id).isdigit() else None
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
    member = interaction.guild.get_member(int(discord_id)) if discord_id and str(discord_id).isdigit() else None
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
    await interaction.response.send_message(embed=embed, ephemeral=True)

keep_alive()
bot.run(TOKEN)