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
        "preenchida": "✅ Preenchimento da ficha concluído! Aguarde confirmação para enviar...",
        "titulo_embed": "Confira sua ficha antes de enviar!",
        "label_roblox": "Roblox",
        "label_dps": "DPS",
        "label_farm": "Farm",
        "label_rank": "Rank",
        "label_level": "Level",
        "label_tempo": "Tempo",
        "label_data": "Data"
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
        "preenchida": "✅ Form completed! Please confirm to submit...",
        "titulo_embed": "Check your form before submitting!",
        "label_roblox": "Roblox",
        "label_dps": "DPS",
        "label_farm": "Farm",
        "label_rank": "Rank",
        "label_level": "Level",
        "label_tempo": "Playtime",
        "label_data": "Date"
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
        "preenchida": "✅ ¡Ficha completada! Por favor, confirme para enviar...",
        "titulo_embed": "¡Revisa tu ficha antes de enviar!",
        "label_roblox": "Roblox",
        "label_dps": "DPS",
        "label_farm": "Farm",
        "label_rank": "Rango",
        "label_level": "Nivel",
        "label_tempo": "Tiempo de juego",
        "label_data": "Fecha"
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
        # ========= PARTE 2 =========

import pytz

ARQUIVO = 'servidores.json'
ARQUIVO_ENVIOS = 'envios.json'
AVISOS_CONFIG = 'avisos_config.json'
CANAL_AVISOS_ID = 1380022433288949851
CARGO_ANALISE_ID = 1379508463172063286
CANAL_2DIAS_ID = 1379585139629228062
CARGO_2DIAS_ID = 1379508463172063290

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
        print("🔄 Comandos sincronizados:", [c.name for c in synced])
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
            "/minha_ficha\n"
            "/corrigir_numero_ficha"
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

# ----------- CORREÇÃO DE NÚMERO DE FICHA (APENAS UMA DEFINIÇÃO!) --------------
@bot.tree.command(
    name="corrigir_numero_ficha",
    description="Corrige o número de uma ficha duplicada."
)
@app_commands.describe(
    numero_atual="Número duplicado (ex: 68)",
    novo_numero="Novo número para aplicar (ex: 69)",
    guilda="Nome da guilda (ex: hades, hades2)"
)
async def corrigir_numero_ficha(
    interaction: discord.Interaction,
    numero_atual: int,
    novo_numero: int,
    guilda: str
):
    guilda = guilda.lower()
    fichas_encontradas = []
    for idioma in ["pt", "en", "es"]:
        arquivo = f"fichas_{guilda}_{idioma}.json"
        if not os.path.exists(arquivo):
            continue
        with open(arquivo, "r", encoding="utf-8") as f:
            dados = json.load(f)
            for uid, ficha in dados.items():
                if ficha.get("numero") == numero_atual:
                    fichas_encontradas.append({
                        "dados": ficha,
                        "arquivo": arquivo,
                        "idioma": idioma,
                        "uid": uid
                    })
    await interaction.response.defer(ephemeral=True)

    if not fichas_encontradas:
        await interaction.followup.send("❌ Nenhuma ficha com esse número foi encontrada.", ephemeral=True)
        return

    descricao = ""
    for i, ficha in enumerate(fichas_encontradas):
        d = ficha["dados"]
        descricao += f"`{i+1}` - Roblox: **{d.get('roblox', '-')[:20]}**, Discord: <@{d.get('discord', '-')}> (Idioma: {ficha['idioma']})\n"

    await interaction.followup.send(
        f"Foram encontradas **{len(fichas_encontradas)}** fichas com o número **{numero_atual}**:\n{descricao}\n\nResponda com o número da ficha que você deseja corrigir.",
        ephemeral=True
    )

    def check(m):
        return m.author.id == interaction.user.id and m.channel == interaction.channel and m.content.isdigit()

    try:
        msg = await bot.wait_for("message", check=check, timeout=30)
        escolha = int(msg.content.strip())
        if not (1 <= escolha <= len(fichas_encontradas)):
            await interaction.followup.send("❌ Escolha inválida.", ephemeral=True)
            return

        ficha_escolhida = fichas_encontradas[escolha - 1]
        ficha_escolhida["dados"]["numero"] = novo_numero

        # Atualiza o arquivo correspondente
        with open(ficha_escolhida["arquivo"], "r", encoding="utf-8") as f:
            dados_arquivo = json.load(f)
        dados_arquivo[ficha_escolhida["uid"]]["numero"] = novo_numero
        with open(ficha_escolhida["arquivo"], "w", encoding="utf-8") as f:
            json.dump(dados_arquivo, f, ensure_ascii=False, indent=4)

        await interaction.followup.send(f"✅ A ficha foi atualizada para o número **{novo_numero}** com sucesso!", ephemeral=True)

    except TimeoutError:
        await interaction.followup.send("⏰ Tempo esgotado. Nenhuma escolha foi feita.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Ocorreu um erro: {e}", ephemeral=True)

# ========= FIM DA PARTE 2 =========

# Inicie o bot (caso não esteja incluso no final da parte 1)
if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
