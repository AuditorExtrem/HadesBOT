import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from keep_alive import keep_alive
from core import *
from dotenv import load_dotenv

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# =================== COMANDOS DE FICHA ===================
import time
from discord.ext import commands

# 🧠 Cache de usuários
usuario_cache = {}

async def buscar_usuario(bot, discord_id):
    agora = time.time()

    if discord_id in usuario_cache:
        user, timestamp = usuario_cache[discord_id]
        if agora - timestamp < 60:
            return user

    user = await bot.fetch_user(int(discord_id))
    usuario_cache[discord_id] = (user, agora)
    return user

# 👇 Daqui pra baixo vem comandos
@bot.tree.command(name="ficha", description="Preencher ficha de jogador para HCFD ou Hades 2")
@app_commands.describe(
    usuario="(Opcional) Usuário que irá preencher a ficha",
    guilda="Guilda que está convidando o jogador"
)
@app_commands.choices(
    guilda=[
        app_commands.Choice(name="HCFD", value="hades"),
        app_commands.Choice(name="Hades 2", value="hades2")
    ]
)
async def ficha(
    interaction: discord.Interaction,
    guilda: app_commands.Choice[str],
    usuario: discord.Member = None
):
    canal_id = interaction.channel.id
    canal_nome = interaction.channel.name
    canal_mencao = interaction.channel.mention
    nome_guilda = guilda.value
    numero = proximo_numero_ficha(nome_guilda)

    # ✅ Se o autor estiver preenchendo a própria ficha
    if usuario is None or usuario == interaction.user:
        view = MenuIdioma(bot, canal_id, nome_guilda, interaction.user, canal_nome, canal_mencao)
        await interaction.response.send_message(
            f"📄 Clique abaixo para escolher o idioma.\n"
            "⚠️ Você só pode ter UMA ficha registrada. Preencher de novo irá editar sua ficha!\n"
            f"📌 Próximo número de ficha: **#{numero}**",
            view=view,
            ephemeral=True
        )
        return  # ✅ Importante: impede que o restante do código (DM) rode!

    # ✅ Se estiver convidando outra pessoa
    view = MenuIdioma(bot, canal_id, nome_guilda, usuario, canal_nome, canal_mencao)

    if nome_guilda == "HCFD":
        mensagem_dm = (
            f"🌟 Olá {usuario.mention}!\n\n"
            "Você foi convidado para entrar na **guilda HCFD –**! Parabéns!\n\n"
            "➡️ Volte ao ticket e responda com **seu nick do Roblox** para preencher a ficha."
        )
    else:
        mensagem_dm = (
            f"📘 Olá {usuario.mention}!\n\n"
            "Você foi convidado a entrar na **Hades 2**, nossa guilda secundária e futura top global!\n\n"
            "➡️ Volte ao ticket e envie **seu nick do Roblox** para completar a ficha."
        )

    try:
        await usuario.send(mensagem_dm, view=view)
        await interaction.response.send_message(
            f"✉️ Convite enviado por DM para {usuario.mention}!",
            ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            f"❌ Não consegui enviar DM para {usuario.mention}. Peça para liberar as DMs!",
            ephemeral=True
        )
import json
import asyncio
import discord
from discord import app_commands

# ───── Helpers ──────────────────────────────────────────────
def flag_by_lang(lang: str) -> str:
    """Devolve o emoji da bandeira pelo código de idioma."""
    return {
        "pt": "🇧🇷",
        "en": "🇺🇸",
        "es": "🇪🇸",
    }.get(lang.lower(), "")

def get_value(d: dict, *aliases, default="N/A"):
    """Pega o primeiro campo existente (case-insensitive) dentre os aliases."""
    lower = {k.lower(): v for k, v in d.items()}
    for key in aliases:
        if key.lower() in lower:
            return lower[key.lower()]
    return default

@bot.tree.command(name="enviar_ficha", description="Envia uma ficha específica pelo número e guilda.")
@app_commands.describe(
    numero="Número da ficha",
    guilda="Selecione a guilda da ficha",
    idioma="Idioma (padrão: pt)"
)
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
@app_commands.default_permissions(administrator=True)
async def enviar_ficha(
    interaction: discord.Interaction,
    numero: int,
    guilda: app_commands.Choice[str],
    idioma: app_commands.Choice[str] = None
):
    idioma_valor = idioma.value if idioma else "pt"
    arquivo = arquivo_fichas(guilda.value, idioma_valor)

    try:
        with open(arquivo, encoding="utf-8") as f:
            dados = json.load(f)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro ao ler o arquivo de fichas: {e}")
        return

    ficha_encontrada = None
    for ficha in dados.values():
        numero_ficha = get_value(ficha, "numero", "id", default=None)
        if numero_ficha is not None and int(numero_ficha) == numero:
            ficha_encontrada = ficha
            break

    if not ficha_encontrada:
        await interaction.response.send_message(f"❌ Ficha #{numero} não encontrada na guilda **{guilda.name}**.")
        return

    flag = flag_by_lang(idioma_valor)
    boas_vinda = random.choice(BOAS_VINDAS)
    roblox = ficha_encontrada.get("roblox", "-")
    data = ficha_encontrada.get("data", "-")
    discord_id = str(ficha_encontrada.get("discord", "-")).strip()

    embed = discord.Embed(
        title=f"🏰 Hades - Ficha #{numero} | Arise Crossover {flag}",
        description=f"**{boas_vinda}**",
        color=discord.Color.purple()
    )
    embed.add_field(name="🎮 Nick no Roblox", value=roblox, inline=False)
    embed.add_field(name="💬 Discord", value=f"<@{discord_id}>" if discord_id.isdigit() else "ID inválido", inline=False)
    embed.add_field(name="📅 Ficha registrada em:", value=data, inline=False)
    embed.set_footer(text="Arise Crossover | Sistema de Fichas Hades")

    # Avatar
    if discord_id.isdigit():
        try:
            user = await buscar_usuario(interaction.client, discord_id)
            embed.set_thumbnail(url=user.display_avatar.url)
        except discord.NotFound:
            pass

    await interaction.response.send_message(embed=embed)
@bot.tree.command(name="todas_fichas", description="Mostra todas as fichas salvas de todas as guildas e idiomas.")
@app_commands.default_permissions(administrator=True)
async def todas_fichas(interaction: discord.Interaction):
    import os

    arquivos = [
        "fichas_hades_pt.json",
        "fichas_hades_en.json",
        "ficha_hades_es.json",
        "fichas_hades2_pt.json",
        "fichas_hades2_en.json",
        "fichas_hades2_es.json",
    ]

    todas_fichas = []

    for arquivo in arquivos:
        if not os.path.exists(arquivo):
            continue
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                fichas = json.load(f)
                todas_fichas.extend(fichas.values())
        except Exception as e:
            print(f"Erro ao carregar {arquivo}: {e}")

    if not todas_fichas:
        await interaction.response.send_message("❌ Nenhuma ficha encontrada.", ephemeral=False)
        return

    fichas_ordenadas = sorted(todas_fichas, key=lambda f: f.get("numero", 0))

    embed = discord.Embed(
        title="📋 Todas as Fichas Salvas",
        description=f"Total: {len(fichas_ordenadas)} fichas",
        color=discord.Color.dark_green()
    )

    for ficha in fichas_ordenadas:
        numero = ficha.get("numero", "-")
        roblox = ficha.get("roblox", "-")
        discord_id = ficha.get("discord", "-")
        data = ficha.get("data", "-")
        linha = f"👤 <@{discord_id}> | 🎮 `{roblox}` | 📅 `{data}`"
        embed.add_field(name=f"Ficha #{numero}", value=linha, inline=False)

        # Evita o limite de 25 fields por embed
        if len(embed.fields) == 25:
            await interaction.channel.send(embed=embed)
            embed = discord.Embed(
                title="📋 Continuação das Fichas",
                color=discord.Color.dark_green()
            )

    if embed.fields:
        await interaction.channel.send(embed=embed)

    await interaction.response.send_message("✅ Fichas enviadas com sucesso.", ephemeral=False)

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

@bot.tree.command(name="definir_numero_ficha", description="Define manualmente o número da última ficha registrada.")
@app_commands.describe(
    guilda="Selecione a guilda para ajustar o número",
    numero="Número da última ficha registrada"
)
@app_commands.choices(
    guilda=[
        app_commands.Choice(name="HCFD", value="hades"),
        app_commands.Choice(name="Hades 2", value="hades2")
    ]
)
@app_commands.default_permissions(administrator=True)
async def definir_numero_ficha(interaction: discord.Interaction, guilda: app_commands.Choice[str], numero: int):
    try:
        salvar_numero_ficha(guilda.value, numero)  # Função já existe no core.py
        await interaction.response.send_message(
            f"✅ O número da última ficha da guilda **{guilda.name}** foi definido como `{numero}`.\n"
            f"A próxima ficha será **#{numero + 1}**.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro ao salvar o número: {e}", ephemeral=True)

@bot.tree.command(name="minha_ficha", description="Veja rapidamente sua ficha cadastrada em uma guilda/idioma")
@app_commands.choices(
    guilda=[
        app_commands.Choice(name="HCFD", value="hades"),
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

import discord
from discord import ui, Interaction
import json

class ViewSelecaoFicha(ui.View):
    def __init__(self, fichas, guilda, idioma):
        super().__init__(timeout=60)
        self.guilda = guilda
        self.idioma = idioma

        options = [
            discord.SelectOption(
                label=ficha['roblox'],
                description=f"Ficha #{ficha['numero']} - {ficha.get('rank', '')}",
                value=uid
            )
            for uid, ficha in fichas.items()
        ]

        self.select = ui.Select(
            placeholder="Selecione uma ficha para editar",
            options=options,
            min_values=1,
            max_values=1
        )
        self.select.callback = self.selecionar_ficha
        self.add_item(self.select)

    async def selecionar_ficha(self, interaction: Interaction):
        self.uid_escolhido = self.select.values[0]
        self.ficha_escolhida = carregar_ficha_por_uid(self.uid_escolhido, self.guilda, self.idioma)

        await interaction.response.edit_message(
            content=f"📄 Ficha de **{self.ficha_escolhida['roblox']}** selecionada com sucesso! Escolha o campo a editar:",
            view=ViewEditarCampoFicha(
                self.uid_escolhido,
                self.ficha_escolhida,
                self.guilda,
                self.idioma
            )
        )
class ViewEditarCampoFicha(ui.View):
    def __init__(self, uid, ficha, guilda, idioma):
        super().__init__(timeout=60)
        self.uid = uid
        self.ficha = ficha
        self.guilda = guilda
        self.idioma = idioma

        options = [
            discord.SelectOption(label=label, value=campo)
            for campo, label in CAMPOS_EDITAVEIS
        ]

        self.select = ui.Select(
            placeholder="Escolha o campo para editar",
            options=options
        )
        self.select.callback = self.selecionar_campo
        self.add_item(self.select)

    async def selecionar_campo(self, interaction: Interaction):
        self.campo = self.select.values[0]
        await interaction.response.send_message(
            f"✏️ Digite o novo valor para o campo **{self.campo}**:",
            ephemeral=True
        )

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        try:
            msg = await interaction.client.wait_for("message", timeout=120, check=check)
            valor = msg.content.strip()

            if self.campo == "numero":
                try:
                    valor = int(valor)
                except:
                    await interaction.followup.send("❌ Valor inválido. Use apenas números inteiros.", ephemeral=True)
                    return
                self.ficha["numero"] = valor
            elif self.campo == "discord":
                if valor.startswith("<@") and valor.endswith(">"):
                    valor = valor.replace("<@", "").replace(">", "").replace("!", "")
                self.ficha["discord"] = valor
            else:
                self.ficha[self.campo] = valor

            salvar_ficha_por_uid(self.uid, self.ficha, self.guilda, self.idioma)

            await interaction.followup.send(
                f"✅ Ficha de **{self.ficha['roblox']}** atualizada com sucesso! Campo **{self.campo}** alterado.",
                ephemeral=True
            )

        except Exception:
            await interaction.followup.send("⏱️ Tempo esgotado. Tente novamente.", ephemeral=True)
async def selecionar_campo(self, interaction: Interaction):
    self.campo = self.select.values[0]
    await interaction.response.send_message(f"✏️ Digite o novo valor para o campo **{self.campo}**:", ephemeral=True)

    def check(msg):
        return msg.author == interaction.user and msg.channel == interaction.channel

    try:
        msg = await interaction.client.wait_for("message", timeout=120, check=check)
        valor = msg.content.strip()
        if self.campo == "numero":
            try:
                valor = int(valor)
            except:
                await interaction.followup.send("❌ Valor inválido. Use apenas números inteiros.", ephemeral=True)
                return
            self.ficha["numero"] = valor
        elif self.campo == "discord":
            if valor.startswith("<@") and valor.endswith(">"):
                valor = valor.replace("<@", "").replace(">", "").replace("!", "")
            self.ficha["discord"] = valor
        else:
            self.ficha[self.campo] = valor

        salvar_ficha_por_uid(self.uid, self.ficha, self.guilda, self.idioma)
        await interaction.followup.send(f"✅ Ficha de **{self.ficha['roblox']}** atualizada com sucesso! Campo **{self.campo}** alterado.", ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"⏱️ Tempo esgotado. Tente novamente.", ephemeral=True)

from discord import app_commands
from discord.ext import commands
import discord
import json
from core import ViewSelecaoFicha, arquivo_fichas

@bot.tree.command(name="editar_ficha", description="Editar uma ficha via menu interativo")
@app_commands.describe(
    guilda="Selecione a guilda",
    idioma="Selecione o idioma"
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
    ]
)
@app_commands.default_permissions(administrator=True)
async def editar_ficha(interaction: discord.Interaction, guilda: app_commands.Choice[str], idioma: app_commands.Choice[str]):
    arquivo = arquivo_fichas(guilda.value, idioma.value)
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            todas = json.load(f)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro ao carregar as fichas: {e}", ephemeral=True)
        return

    if not todas:
        await interaction.response.send_message("⚠️ Nenhuma ficha registrada encontrada.", ephemeral=True)
        return

    view = ViewSelecaoFicha(todas, guilda.value, idioma.value)
    await interaction.response.send_message(
        "📋 Selecione qual ficha deseja editar:",
        view=view,
        ephemeral=True
    )
    view.message = await interaction.original_response()

from discord import app_commands
from discord.ext import commands
import discord

class ServidorCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="servidorhd", description="Gerencia servidores do Roblox")

    @app_commands.command(name="adicionar", description="Adiciona um novo servidor à lista")
    @app_commands.describe(
        nome="Nome do servidor (ex: VIP 1)",
        link="Link do servidor do Roblox",
        pessoa="Pessoa para exibir como autor (opcional)"
    )
    @app_commands.default_permissions(administrator=True)
    async def adicionar(self, interaction: discord.Interaction, nome: str, link: str, pessoa: discord.Member = None):
        servidores = carregar_servidores()
        nome_lower = nome.strip().lower()

        if any(s["nome"].strip().lower() == nome_lower for s in servidores):
            await interaction.response.send_message(f"❌ Já existe um servidor com o nome **{nome}**.", ephemeral=True)
            return

        novo = {
            "nome": nome.strip(),
            "link": link.strip()
        }
        if pessoa:
            novo["autor_id"] = pessoa.id

        servidores.append(novo)
        salvar_servidores(servidores)
        await interaction.response.send_message(f"✅ Servidor **{nome}** adicionado com sucesso!", ephemeral=True)

    @app_commands.command(name="remover", description="Remove um servidor salvo pelo nome")
    @app_commands.describe(nome="Nome do servidor")
    @app_commands.default_permissions(administrator=True)
    async def remover(self, interaction: discord.Interaction, nome: str):
        servidores = carregar_servidores()
        nome_lower = nome.lower()
        novos = [s for s in servidores if s["nome"].lower() != nome_lower]

        if len(novos) == len(servidores):
            await interaction.response.send_message(f"❌ Nenhum servidor chamado **{nome}** encontrado.", ephemeral=True)
            return

        salvar_servidores(novos)
        await interaction.response.send_message(f"🗑️ Servidor **{nome}** removido com sucesso!", ephemeral=True)

    @app_commands.command(name="atualizar", description="Atualiza a imagem do servidor com o avatar da pessoa mencionada")
    @app_commands.describe(nome="Nome do servidor", membro="Membro para atualizar foto")
    @app_commands.default_permissions(administrator=True)
    async def atualizar(self, interaction: discord.Interaction, nome: str, membro: discord.Member):
        servidores = carregar_servidores()
        for servidor in servidores:
            if servidor["nome"].lower() == nome.lower():
                servidor["autor_id"] = membro.id
                salvar_servidores(servidores)
                await interaction.response.send_message(f"✅ Foto do servidor **{nome}** atualizada para **{membro.display_name}**.", ephemeral=True)
                return
        await interaction.response.send_message(f"❌ Servidor **{nome}** não encontrado.", ephemeral=True)

    @app_commands.command(name="listar", description="Lista todos os servidores com botão de entrada")
    @app_commands.default_permissions(administrator=True)
    async def listar(self, interaction: discord.Interaction):
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

    @app_commands.command(name="mostrar", description="Mostra somente o servidor especificado")
    @app_commands.describe(nome="Nome do servidor")
    @app_commands.default_permissions(administrator=True)
    async def mostrar(self, interaction: discord.Interaction, nome: str):
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
@bot.tree.command(name="pingstaff", description="Envie uma mensagem anônima para o canal atual")
@app_commands.describe(mensagem="Mensagem que será enviada no canal, sem mostrar quem enviou")
@app_commands.default_permissions(administrator=True) 
async def pingstaff(interaction: discord.Interaction, mensagem: str):
    await interaction.channel.send(mensagem)
    await interaction.response.send_message("✅ Mensagem enviada anonimamente no canal!", ephemeral=True)

@bot.tree.command(name="ajuda", description="Mostra a lista de comandos disponíveis")
async def ajuda(interaction: discord.Interaction):
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
# =================== EVENTO ON_READY E TASKS ===================
@bot.event
async def on_ready():
    print(f'✅ {bot.user} está online!')

    bot.tree.add_command(ServidorCommands())

    try:
        synced = await bot.tree.sync()
        print(f"🔄 Sincronizados {len(synced)} comandos slash")
    except Exception as e:
        print(f"❌ Erro ao sincronizar slash commands: {e}")

    keep_alive_task.start()

@tasks.loop(minutes=5)
async def keep_alive_task():
    pass

import os


load_dotenv()  # Para ambiente local

print("🔍 Checando variáveis de ambiente...")

# 🔥 NOVO: mostra todas as variáveis de ambiente
for key, value in os.environ.items():
    print(f"{key} = {value}")


# 🔥 NOVO: printa o valor da variável específica
print(f"TOKEN encontrado: {TOKEN}")

if not TOKEN:
    print("❌ Token não encontrado! Verifique variável de ambiente DISCORD_BOT_TOKEN.")
    exit()

if __name__ == "__main__":
    from keep_alive import keep_alive  # importe aqui se estiver usando o sistema de uptime
    keep_alive()
    bot.run(TOKEN)
