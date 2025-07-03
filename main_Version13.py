import discord
from discord.ext import commands, tasks
from discord import app_commands, ui
import json
import os
from datetime import datetime
import pytz
from keep_alive import keep_alive

# Configurações
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

FICHAS_CANAL_ID = 1390134033387618474        # Canal de testes
FICHAS_CANAL_HADES2_ID = 1390146714417102938  # << TROQUE para o canal do Hades 2 (substitua pelo correto!)

def carregar_numero_ficha():
    try:
        with open("numero_ficha.json", "r", encoding="utf-8") as f:
            return json.load(f).get("numero", 66)
    except:
        return 66

def salvar_numero_ficha(n):
    with open("numero_ficha.json", "w", encoding="utf-8") as f:
        json.dump({"numero": n}, f)

def carregar_ficha(user_id, idioma):
    arquivo = f"fichas_{idioma}.json"
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f).get(str(user_id))
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

class MenuIdioma(ui.View):
    def __init__(self, bot, interaction, canal_id, nome_guilda):
        super().__init__(timeout=60)
        self.bot = bot
        self.interaction = interaction
        self.canal_id = canal_id
        self.nome_guilda = nome_guilda
        self.select = ui.Select(
            placeholder="Escolha o idioma / Choose language",
            options=[
                discord.SelectOption(label="Português", value="pt", emoji="🇧🇷"),
                discord.SelectOption(label="English", value="en", emoji="🇺🇸")
            ]
        )
        self.select.callback = self.selecionar_idioma
        self.add_item(self.select)

    async def selecionar_idioma(self, interaction: discord.Interaction):
        if interaction.user != self.interaction.user:
            await interaction.response.send_message("❌ Apenas quem iniciou pode interagir.", ephemeral=True)
            return
        idioma = self.select.values[0]
        await interaction.response.edit_message(content="✅ Idioma selecionado!", view=None)
        await iniciar_formulario(self.bot, interaction, idioma, self.canal_id, self.nome_guilda)

@bot.tree.command(name="ficha", description="Preencher ficha de jogador (Hades)")
async def slash_ficha(interaction: discord.Interaction):
    view = MenuIdioma(bot, interaction, FICHAS_CANAL_ID, "Hades")
    msg = (
        "📄 Clique abaixo para escolher o idioma.\n"
        "⚠️ **Você só pode ter UMA ficha registrada. Preencher de novo irá editar sua ficha!**\n"
        f"Número inicial da ficha: **{carregar_numero_ficha()}**\n"
        "Se precisar reiniciar a contagem, use `/edit_numero_ficha` (ADM)."
    )
    await interaction.response.send_message(msg, view=view, ephemeral=True)

@bot.tree.command(name="ficha_hades2", description="Preencher ficha de jogador (Hades 2)")
async def slash_ficha_hades2(interaction: discord.Interaction):
    view = MenuIdioma(bot, interaction, FICHAS_CANAL_HADES2_ID, "Hades 2")
    msg = (
        "📄 Clique abaixo para escolher o idioma.\n"
        "⚠️ **Você só pode ter UMA ficha registrada. Preencher de novo irá editar sua ficha!**\n"
        f"Número inicial da ficha: **{carregar_numero_ficha()}**\n"
        "Se precisar reiniciar a contagem, use `/edit_numero_ficha` (ADM)."
    )
    await interaction.response.send_message(msg, view=view, ephemeral=True)

async def iniciar_formulario(bot, interaction, idioma, canal_id, nome_guilda):
    perguntas_pt = [
        ("🎮 Nick no Roblox:", "roblox"),
        ("⚔️ DPS Atual:", "dps"),
        ("💎 Farm diário de gemas:", "farm"),
        ("🔹 Rank:", "rank"),
        ("🔹 Level:", "level"),
        ("🔹 Tempo de jogo:", "tempo")
    ]
    perguntas_en = [
        ("🎮 Roblox Username:", "roblox"),
        ("⚔️ Current DPS:", "dps"),
        ("💎 Daily Gem Farm:", "farm"),
        ("🔹 Rank:", "rank"),
        ("🔹 Level:", "level"),
        ("🔹 Playtime:", "tempo")
    ]
    perguntas = perguntas_pt if idioma == "pt" else perguntas_en
    respostas = {}
    canal = await bot.fetch_channel(canal_id)
    def check(m):
        return m.author == interaction.user and m.channel == canal
    await canal.send(
        f"{interaction.user.mention} "
        + (
            "📋 Vamos preencher sua ficha! Responda às perguntas abaixo:\n"
            "⚠️ **Você só pode ter UMA ficha. Preencher novamente edita sua ficha!**"
            if idioma == "pt" else
            "📋 Let's fill out your form! Answer below:\n"
            "⚠️ **You can only have ONE profile. Filling again will edit your profile!**"
        )
    )
    for pergunta, chave in perguntas:
        await canal.send(pergunta)
        msg = await bot.wait_for("message", check=check, timeout=180)
        respostas[chave] = msg.content.strip()
    data_atual = datetime.now().strftime("%d/%m/%Y")
    user_id = interaction.user.id
    ficha_existente = carregar_ficha(user_id, idioma)
    all_nums = []
    for lang in ["pt", "en"]:
        try:
            with open(f"fichas_{lang}.json", "r", encoding="utf-8") as f:
                all_nums += [x["numero"] for x in json.load(f).values() if "numero" in x]
        except:
            pass
    numero_ficha = ficha_existente["numero"] if ficha_existente and "numero" in ficha_existente else max([carregar_numero_ficha()] + all_nums, default=carregar_numero_ficha())
    if not ficha_existente:
        numero_ficha = numero_ficha + 1 if numero_ficha in all_nums else numero_ficha
        salvar_numero_ficha(numero_ficha)
    ficha = {
        "numero": numero_ficha,
        "idioma": idioma,
        "roblox": respostas.get("roblox"),
        "dps": respostas.get("dps"),
        "farm": respostas.get("farm"),
        "rank": respostas.get("rank"),
        "level": respostas.get("level"),
        "tempo": respostas.get("tempo"),
        "data": data_atual
    }
    avatar_url = interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
    embed = discord.Embed(
        title=f"🌌 Ficha de Jogador #{numero_ficha} – Arise Crossover 🌌",
        color=discord.Color.purple()
    )
    embed.add_field(name="🎮 Roblox", value=ficha['roblox'], inline=False)
    embed.add_field(name="🏰 Guilda", value=nome_guilda, inline=True)
    embed.add_field(name="💬 Discord", value=interaction.user.mention, inline=True)
    embed.add_field(name="⚔️ DPS", value=ficha['dps'], inline=False)
    embed.add_field(name="💎 Farm", value=ficha['farm'], inline=False)
    embed.add_field(
        name="📊 Outras Informações",
        value=f"🔹 Rank: {ficha['rank']}\n🔹 Level: {ficha['level']}\n🔹 Tempo: {ficha['tempo']}",
        inline=False
    )
    embed.set_footer(text=f"📆 Data da ficha: {ficha['data']}")
    embed.set_thumbnail(url=avatar_url)
    mensagem_id = None
    if ficha_existente and "mensagem_id" in ficha_existente:
        try:
            ficha_msg = await canal.fetch_message(ficha_existente["mensagem_id"])
            await ficha_msg.edit(embed=embed)
            await canal.send(f"{interaction.user.mention} sua ficha foi **atualizada** com sucesso!")
            mensagem_id = ficha_existente["mensagem_id"]
        except Exception as e:
            ficha_msg = await canal.send(embed=embed)
            mensagem_id = ficha_msg.id
            await canal.send(f"{interaction.user.mention} sua ficha foi enviada novamente porque a anterior não foi encontrada!")
    else:
        ficha_msg = await canal.send(embed=embed)
        mensagem_id = ficha_msg.id
        await canal.send(f"{interaction.user.mention} sua ficha foi **criada** com sucesso!")
    ficha["mensagem_id"] = mensagem_id
    salvar_ficha(user_id, ficha, idioma)
    marcar_preencheu(user_id)

@bot.tree.command(name="edit_numero_ficha", description="Editar número inicial das fichas (ADM)")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(numero="Novo número inicial (deve ser inteiro positivo)")
async def edit_numero_ficha(interaction: discord.Interaction, numero: int):
    if numero < 1:
        await interaction.response.send_message("❌ O número inicial deve ser positivo!", ephemeral=True)
        return
    salvar_numero_ficha(numero)
    await interaction.response.send_message(f"✅ Número inicial das fichas atualizado para **{numero}**.", ephemeral=True)

# --- Funções para manipular servidores ---
def carregar_servidores():
    if not os.path.exists(ARQUIVO):
        return []
    with open(ARQUIVO, 'r') as f:
        return json.load(f)

def salvar_servidores(lista):
    with open(ARQUIVO, 'w') as f:
        json.dump(lista, f, indent=4)

# --- Funções para persistir último envio de avisos ---
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

# --- Função de carregar aviso customizado ---
def carregar_aviso(tipo):
    if not os.path.exists(AVISOS_CONFIG):
        return {}
    with open(AVISOS_CONFIG, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config.get(tipo, {})

# --- Função genérica para enviar aviso embed customizado ou texto ---
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

# --- Evento on_ready ---
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

# --- Comandos de servidor (prefix) ---
@bot.command(name="adicionar_servidor")
async def adicionar_servidor(ctx, nome: str, link: str, membro: discord.Member = None):
    servidores = carregar_servidores()
    autor_id = membro.id if membro else None
    for servidor in servidores:
        if servidor['nome'].lower() == nome.lower():
            servidor['link'] = link
            servidor['autor_id'] = autor_id
            salvar_servidores(servidores)
            await ctx.send(f"🔁 Servidor **{nome}** atualizado!")
            return
    servidores.append({'nome': nome, 'link': link, 'autor_id': autor_id})
    salvar_servidores(servidores)
    await ctx.send(f"✅ Servidor **{nome}** adicionado com sucesso!")

@bot.command(name="remover_servidor")
async def remover_servidor(ctx, nome: str):
    servidores = carregar_servidores()
    nome_lower = nome.lower()
    novos = [s for s in servidores if s['nome'].lower() != nome_lower]
    if len(novos) == len(servidores):
        await ctx.send(f"❌ Nenhum servidor chamado **{nome}** encontrado.")
        return
    salvar_servidores(novos)
    await ctx.send(f"🗑️ Servidor **{nome}** removido com sucesso!")

@bot.command(name="atualizar_servidor")
async def atualizar_servidor(ctx, nome: str, membro: discord.Member):
    servidores = carregar_servidores()
    for servidor in servidores:
        if servidor['nome'].lower() == nome.lower():
            servidor['autor_id'] = membro.id
            salvar_servidores(servidores)
            await ctx.send(f"✅ Foto do servidor **{nome}** atualizada para **{membro.display_name}**.")
            return
    await ctx.send(f"❌ Servidor **{nome}** não encontrado.")

@bot.command(name="servidores")
async def servidores_cmd(ctx):
    servidores = carregar_servidores()
    if not servidores:
        await ctx.send("❌ Nenhum servidor foi adicionado ainda.")
        return
    for servidor in servidores:
        embed = discord.Embed(
            title=servidor["nome"],
            description="Clique no botão abaixo para entrar no servidor do Roblox.",
            color=discord.Color.green()
        )
        autor_id = servidor.get("autor_id")
        if autor_id:
            membro = ctx.guild.get_member(autor_id)
            if membro:
                embed.set_author(name=membro.display_name, icon_url=membro.avatar.url if membro.avatar else None)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="🎮 Jogar agora", url=servidor["link"]))
        await ctx.send(embed=embed, view=view)

@bot.command(name="servidor")
async def servidor(ctx, *, nome: str):
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
                membro = ctx.guild.get_member(autor_id)
                if membro:
                    embed.set_author(name=membro.display_name, icon_url=membro.avatar.url if membro.avatar else None)
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="🎮 Jogar agora", url=servidor["link"]))
            await ctx.send(embed=embed, view=view)
            return
    await ctx.send(f"❌ Servidor **{nome}** não foi encontrado.")

@bot.command(name="ajuda")
async def ajuda(ctx):
    try:
        autor = await bot.fetch_user(967559600574447619)
        embed = discord.Embed(
            title="🌐 Comandos do Bot da HADES",
            description="Aqui estão todos os comandos disponíveis:",
            color=discord.Color.blue()
        )
        embed.set_author(
            name=autor.display_name if hasattr(autor, "display_name") else autor.name,
            icon_url=autor.avatar.url if autor.avatar else None
        )
        embed.add_field(
            name="➤ /adicionar_servidor <nome> <link> [@pessoa]",
            value="Adiciona ou atualiza um servidor com nome, link e foto opcional.",
            inline=False
        )
        embed.add_field(
            name="🗑️ /remover_servidor <nome>",
            value="Remove um servidor salvo pelo nome.",
            inline=False
        )
        embed.add_field(
            name="🔄 /atualizar_servidor <nome> @pessoa",
            value="Atualiza a imagem do servidor com o avatar da pessoa mencionada.",
            inline=False
        )
        embed.add_field(
            name="📋 /servidores",
            value="Lista todos os servidores com botão de entrada.",
            inline=False
        )
        embed.add_field(
            name="🔍 /servidor <nome>",
            value="Mostra somente o servidor especificado.",
            inline=False
        )
        embed.add_field(
            name="📢 /enviar_aviso_diario",
            value="Envia manualmente o aviso diário para @analise.",
            inline=False
        )
        embed.add_field(
            name="📢 /enviar_aviso_2dias",
            value="Envia manualmente o aviso a cada 2 dias para @HADES.",
            inline=False
        )
        embed.set_footer(text="Bot para gerenciar e divulgar servidores Roblox.")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send("⚠️ Ocorreu um erro ao gerar a mensagem de ajuda.")
        print(f"[ERRO AJUDA] {e}")

# --- Avisos automáticos ---
@tasks.loop(minutes=1)
async def enviar_aviso_diario():
    agora = get_hora_brasilia()
    if agora.hour == 15 and agora.minute == 0:
        ultimo = get_data_ultimo_envio("ultimo_aviso_diario")
        if not ultimo or (agora.date() > ultimo.date()):
            print(f"📢 Enviando aviso diário às {agora.strftime('%H:%M')} (Horário de Brasília)")
            await enviar_aviso("diario", CANAL_AVISOS_ID, CARGO_ANALISE_ID, "# 📝 Verifiquem a Entrada/diaria e abra seu ticket!")
            set_data_ultimo_envio("ultimo_aviso_diario")

@tasks.loop(minutes=1)
async def aviso_cada_2_dias():
    agora = get_hora_brasilia()
    if agora.hour == 15 and agora.minute == 0:
        ultimo = get_data_ultimo_envio("ultimo_aviso_2dias")
        if not ultimo or (agora - ultimo).total_seconds() >= 172800:
            print(f"📢 Enviando aviso de 2 dias às {agora.strftime('%H:%M')} (Horário de Brasília)")
            await enviar_aviso("2dias", CANAL_2DIAS_ID, CARGO_2DIAS_ID, "# 📝 Mande sua meta diária e ajude a guilda a evoluir!")
            set_data_ultimo_envio("ultimo_aviso_2dias")

@tasks.loop(minutes=5)
async def keep_alive_task():
    print(f"🔄 Keep-Alive: {get_hora_brasilia().strftime('%H:%M:%S')} - Bot ativo")

# --- Comandos manuais para avisos ---
@bot.command(name="enviar_aviso_diario")
@commands.has_permissions(administrator=True)
async def cmd_enviar_aviso_diario(ctx):
    await enviar_aviso("diario", CANAL_AVISOS_ID, CARGO_ANALISE_ID, "# 📝 Verifiquem a Entrada/diaria e abra seu ticket!")
    set_data_ultimo_envio("ultimo_aviso_diario")
    await ctx.send("✅ Aviso diário enviado manualmente.")

@bot.command(name="enviar_aviso_2dias")
@commands.has_permissions(administrator=True)
async def cmd_enviar_aviso_2dias(ctx):
    await enviar_aviso("2dias", CANAL_2DIAS_ID, CARGO_2DIAS_ID, "# 📝 Mande sua meta diária e ajude a guilda a evoluir!")
    set_data_ultimo_envio("ultimo_aviso_2dias")
    await ctx.send("✅ Aviso de 2 dias enviado manualmente.")

# --- Slash commands para avisos ---
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

# --- Demais comandos e edição de avisos ---
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

# ---- INICIALIZAÇÃO ----
keep_alive()
bot.run(TOKEN)