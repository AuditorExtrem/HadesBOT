import discord
from discord.ext import commands, tasks
from discord import app_commands
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
