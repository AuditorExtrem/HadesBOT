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
    if discord_id and str(discord_id).isdigit():
        discord_str = f"<@{discord_id}>"
    else:
        discord_str = str(discord_id) if discord_id else "-"
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
    canal = bot.get_channel(canal_id)
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

# ----------- COMANDO /ver_ficha (ADM) --------------
@bot.tree.command(name="ver_ficha", description="(ADM) Ver ficha de um membro pelo número, guilda e idioma")
@app_commands.choices(
    guilda=[
        app_commands.Choice(name="Hades", value="hades"),
        app_commands.Choice(name="Hades 2", value="hades2")
    ],
    idioma=[
        app_commands.Choice(name="Português", value="pt"),
        app_commands.Choice(name="Inglês", value="en"),
        app_commands.Choice(name="Espanhol", value="es")
    ]
)
@app_commands.describe(
    numero="Número da ficha que deseja buscar",
    guilda="Selecione a guilda",
    idioma="Selecione o idioma"
)
async def ver_ficha(
    interaction: discord.Interaction,
    numero: int,
    guilda: app_commands.Choice[str],
    idioma: app_commands.Choice[str]
):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Você não tem permissão para isso.", ephemeral=True)
    caminho = f"fichas_{guilda.value}_{idioma.value}.json"
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            fichas = json.load(f)
    except FileNotFoundError:
        return await interaction.response.send_message(f"❌ Arquivo `{caminho}` não encontrado.", ephemeral=True)
    for uid, ficha in fichas.items():
        if ficha.get("numero") == numero:
            membro = interaction.guild.get_member(int(uid)) if uid.isdigit() else None
            bandeira = IDIOMAS[idioma.value]["bandeira"] if idioma.value in IDIOMAS else ""
            nome_guilda_fmt = "Hades" if guilda.value == "hades" else "Hades 2"
            avatar_url = membro.avatar.url if membro and membro.avatar else None
            # Mostra menção se for ID, senão mostra texto
            discord_id = ficha.get('discord', '')
            if discord_id and str(discord_id).isdigit():
                discord_str = f"<@{discord_id}>"
            else:
                discord_str = str(discord_id) if discord_id else "-"
            embed = discord.Embed(
                title=f"🌌 Ficha de Jogador #{ficha['numero']} – Arise Crossover {bandeira} 🌌",
                color=discord.Color.purple()
            )
            embed.add_field(name="🎮 Roblox", value=ficha.get('roblox', '-'), inline=False)
            embed.add_field(name="🏰 Guilda", value=nome_guilda_fmt, inline=True)
            embed.add_field(name="💬 Discord", value=discord_str, inline=True)
            embed.add_field(name="⚔️ DPS", value=ficha.get('dps', '-'), inline=False)
            embed.add_field(name="💎 Farm", value=ficha.get('farm', '-'), inline=False)
            embed.add_field(
                name="📊 Outras Informações",
                value=f"🔹 Rank: {ficha.get('rank', '-')}\n🔹 Level: {ficha.get('level', '-')}\n🔹 Tempo: {ficha.get('tempo', '-')}",
                inline=False
            )
            embed.set_footer(text=f"📆 Data da ficha: {ficha.get('data', '-')}")
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
            return await interaction.response.send_message(embed=embed, ephemeral=True)
    await interaction.response.send_message(
        f"⚠️ Nenhuma ficha com número `{numero}` foi encontrada no arquivo `{caminho}`.",
        ephemeral=True
    )

# ----------- SELECT MENU EDITAR FICHA --------------
class EditarFichaView(ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.guilda = None
        self.idioma = None
        self.campo = None

        # Guilda Select
        self.guilda_select = ui.Select(
            placeholder="Selecione a guilda",
            options=[discord.SelectOption(label=label, value=value) for value, label in GUILDAS]
        )
        self.guilda_select.callback = self.guilda_callback
        self.add_item(self.guilda_select)

        # Idioma Select
        self.idioma_select = ui.Select(
            placeholder="Selecione o idioma",
            options=[
                discord.SelectOption(label=IDIOMAS[key]["nome"], value=key, emoji=IDIOMAS[key]["bandeira"])
                for key in IDIOMAS
            ]
        )
        self.idioma_select.callback = self.idioma_callback
        self.add_item(self.idioma_select)

        # Campo Select (agora com Discord!)
        self.campo_select = ui.Select(
            placeholder="Selecione o campo para editar",
            options=[
                discord.SelectOption(label=label, value=value)
                for value, label in CAMPOS_EDITAVEIS
            ]
        )
        self.campo_select.callback = self.campo_callback
        self.add_item(self.campo_select)

    async def guilda_callback(self, interaction: discord.Interaction):
        self.guilda = self.guilda_select.values[0]
        await interaction.response.send_message(f"Guilda selecionada: {self.guilda}", ephemeral=True)

    async def idioma_callback(self, interaction: discord.Interaction):
        self.idioma = self.idioma_select.values[0]
        await interaction.response.send_message(f"Idioma selecionado: {self.idioma}", ephemeral=True)

    async def campo_callback(self, interaction: discord.Interaction):
        self.campo = self.campo_select.values[0]
        if self.campo == "discord":
            await interaction.response.send_modal(EditarFichaDiscordModal(self))
        else:
            await interaction.response.send_modal(EditarFichaModal(self))

# Modal padrão para todos os campos exceto Discord
class EditarFichaModal(ui.Modal, title="Editar Ficha"):
    numero = ui.TextInput(label="Número da Ficha", placeholder="Ex: 10", required=True)
    valor = ui.TextInput(label="Novo Valor", placeholder="Digite o novo valor do campo", required=True)

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        if not all([self.view.guilda, self.view.idioma, self.view.campo]):
            await interaction.response.send_message("Por favor, selecione guilda, idioma e campo antes.", ephemeral=True)
            return

        guilda = self.view.guilda
        idioma = self.view.idioma
        campo = self.view.campo
        try:
            numero = int(self.numero.value.strip())
        except Exception:
            await interaction.response.send_message("Número inválido!", ephemeral=True)
            return
        valor = self.valor.value.strip()

        uid, ficha = carregar_ficha_por_numero(numero, guilda, idioma)
        if not ficha:
            await interaction.response.send_message("❌ Ficha não encontrada na guilda/idioma selecionados.", ephemeral=True)
            return
        ficha[campo] = valor
        salvar_ficha_por_uid(uid, ficha, guilda, idioma)
        await interaction.response.send_message(
            f"✅ Ficha número {numero} da guilda {guilda} atualizada!\nCampo **{campo}** corrigido para: **{valor}**",
            ephemeral=True
        )

# Modal personalizado só para o campo Discord
class EditarFichaDiscordModal(ui.Modal, title="Editar Ficha - Discord"):
    numero = ui.TextInput(label="Número da Ficha", placeholder="Ex: 10", required=True)
    membro = ui.TextInput(label="Mencione o usuário (@)", placeholder="Ex: @usuario", required=True)

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        if not all([self.view.guilda, self.view.idioma, self.view.campo]):
            await interaction.response.send_message("Por favor, selecione guilda, idioma e campo antes.", ephemeral=True)
            return

        guilda = self.view.guilda
        idioma = self.view.idioma
        campo = self.view.campo
        try:
            numero = int(self.numero.value.strip())
        except Exception:
            await interaction.response.send_message("Número inválido!", ephemeral=True)
            return
        mencao = self.membro.value.strip()

        # Tenta extrair o ID da menção ou username
        user_id = None
        if mencao.startswith("<@") and mencao.endswith(">"):
            mencao_id = mencao.replace("<@", "").replace("!", "").replace(">", "")
            if mencao_id.isdigit():
                user_id = mencao_id
        elif mencao.isdigit():
            user_id = mencao
        else:
            # Busca por nome
            guild = interaction.guild
            member = discord.utils.get(guild.members, name=mencao.replace("@", ""))
            if member:
                user_id = str(member.id)
        if not user_id:
            await interaction.response.send_message("Mencione corretamente o usuário (ex: @usuario)!", ephemeral=True)
            return

        uid, ficha = carregar_ficha_por_numero(numero, guilda, idioma)
        if not ficha:
            await interaction.response.send_message("❌ Ficha não encontrada na guilda/idioma selecionados.", ephemeral=True)
            return
        ficha[campo] = user_id
        salvar_ficha_por_uid(uid, ficha, guilda, idioma)
        await interaction.response.send_message(
            f"✅ Ficha número {numero} da guilda {guilda} atualizada!\nCampo **{campo}** corrigido para: <@{user_id}>",
            ephemeral=True
        )

@bot.tree.command(name="editar_ficha", description="Editar ficha de jogador por menus (ADM)")
@app_commands.default_permissions(administrator=True)
async def editar_ficha_slash(interaction: discord.Interaction):
    view = EditarFichaView()
    await interaction.response.send_message("Selecione as opções para editar uma ficha:", view=view, ephemeral=True)

# --- PARTE 1 FIM ---
# =======================
# PARTE 2 - COMANDOS DO BOT HADES
# =======================

# =======================
# COMANDOS EXTRAS E IMPORTANTE PARA O SERVIDOR
# =======================
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
            await interaction.response.send_message(f"ðŸ” Servidor **{nome}** atualizado!", ephemeral=True)
            return
    servidores.append({'nome': nome, 'link': link, 'autor_id': autor_id})
    salvar_servidores(servidores)
    await interaction.response.send_message(f"âœ… Servidor **{nome}** adicionado com sucesso!", ephemeral=True)

@bot.tree.command(name="remover_servidor", description="Remove um servidor salvo pelo nome")
@app_commands.describe(nome="Nome do servidor")
async def remover_servidor_slash(interaction: discord.Interaction, nome: str):
    servidores = carregar_servidores()
    nome_lower = nome.lower()
    novos = [s for s in servidores if s['nome'].lower() != nome_lower]
    if len(novos) == len(servidores):
        await interaction.response.send_message(f"âŒ Nenhum servidor chamado **{nome}** encontrado.", ephemeral=True)
        return
    salvar_servidores(novos)
    await interaction.response.send_message(f"ðŸ—‘ï¸ Servidor **{nome}** removido com sucesso!", ephemeral=True)

@bot.tree.command(name="atualizar_servidor", description="Atualiza a imagem do servidor com o avatar da pessoa mencionada")
@app_commands.describe(nome="Nome do servidor", membro="Membro para atualizar foto")
async def atualizar_servidor_slash(interaction: discord.Interaction, nome: str, membro: discord.Member):
    servidores = carregar_servidores()
    for servidor in servidores:
        if servidor['nome'].lower() == nome.lower():
            servidor['autor_id'] = membro.id
            salvar_servidores(servidores)
            await interaction.response.send_message(f"âœ… Foto do servidor **{nome}** atualizada para **{membro.display_name}**.", ephemeral=True)
            return
    await interaction.response.send_message(f"âŒ Servidor **{nome}** nÃ£o encontrado.", ephemeral=True)

@bot.tree.command(name="servidores", description="Lista todos os servidores com botÃ£o de entrada")
async def servidores_slash(interaction: discord.Interaction):
    servidores = carregar_servidores()
    if not servidores:
        await interaction.response.send_message("âŒ Nenhum servidor foi adicionado ainda.", ephemeral=True)
        return
    for servidor in servidores:
        embed = discord.Embed(
            title=servidor["nome"],
            description="Clique no botÃ£o abaixo para entrar no servidor do Roblox.",
            color=discord.Color.green()
        )
        autor_id = servidor.get("autor_id")
        if autor_id:
            membro = interaction.guild.get_member(autor_id)
            if membro:
                embed.set_author(name=membro.display_name, icon_url=membro.avatar.url if membro.avatar else None)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="ðŸŽ® Jogar agora", url=servidor["link"]))
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
                description="Clique no botÃ£o abaixo para entrar no servidor do Roblox.",
                color=discord.Color.green()
            )
            autor_id = servidor.get("autor_id")
            if autor_id:
                membro = interaction.guild.get_member(autor_id)
                if membro:
                    embed.set_author(name=membro.display_name, icon_url=membro.avatar.url if membro.avatar else None)
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="ðŸŽ® Jogar agora", url=servidor["link"]))
            await interaction.channel.send(embed=embed, view=view)
            await interaction.response.send_message(f"Servidor **{nome}** encontrado!", ephemeral=True)
            return
    await interaction.response.send_message(f"âŒ Servidor **{nome}** nÃ£o foi encontrado.", ephemeral=True)

# ----------- AVISOS --------------
# (mantÃ©m igual ao exemplo anterior, veja a parte 2 anterior para nÃ£o perder nada!)

# ----------- OUTROS SLASH --------------
@bot.tree.command(name="pingstaff", description="Envie uma mensagem anÃ´nima para o canal atual")
@app_commands.describe(mensagem="Mensagem que serÃ¡ enviada no canal, sem mostrar quem enviou")
async def pingstaff(interaction: discord.Interaction, mensagem: str):
    await interaction.channel.send(mensagem)
    await interaction.response.send_message("âœ… Mensagem enviada anonimamente no canal!", ephemeral=True)

@bot.tree.command(name="ajuda", description="Mostra a lista de comandos disponÃ­veis")
async def ajuda_slash(interaction: discord.Interaction):
    embed = discord.Embed(
        title="ðŸŒ Comandos do Bot da HADES",
        description="Aqui estÃ£o todos os comandos disponÃ­veis:",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="Fichas",
        value=(
            "/ficha [@usuÃ¡rio]\n"
            "/ficha_hades2 [@usuÃ¡rio]\n"
            "/edit_numero_ficha\n"
            "/editar_ficha (menus)\n"
            "/ver_ficha (ADM)"
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
