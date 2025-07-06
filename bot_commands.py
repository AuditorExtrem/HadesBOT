import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from keep_alive import keep_alive
from core import *

TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# =================== COMANDOS DE FICHA ===================
@bot.tree.command(name="ficha", description="Preencher ficha de jogador (Hades)")
@app_commands.describe(usuario="(Opcional) Usuário para responder a ficha")
async def ficha(interaction: discord.Interaction, usuario: discord.Member = None):
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
async def ficha_hades2(interaction: discord.Interaction, usuario: discord.Member = None):
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
class ConfirmarExclusaoView(discord.ui.View):
    def __init__(self, arquivo, user_id_antigo):
        super().__init__(timeout=60)
        self.arquivo = arquivo
        self.user_id_antigo = user_id_antigo

    @discord.ui.button(label="Sim", style=discord.ButtonStyle.danger, emoji="✅")
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            with open(self.arquivo, "r", encoding="utf-8") as f:
                todas = json.load(f)
            if self.user_id_antigo in todas:
                del todas[self.user_id_antigo]
                with open(self.arquivo, "w", encoding="utf-8") as f:
                    json.dump(todas, f, ensure_ascii=False, indent=2)
                await interaction.response.edit_message(content="🗑️ Ficha original excluída com sucesso.", view=None)
            else:
                await interaction.response.edit_message(content="⚠️ A ficha original já foi removida ou não existe.", view=None)
        except Exception as e:
            await interaction.response.edit_message(content=f"❌ Erro ao excluir ficha: {e}", view=None)

    @discord.ui.button(label="Não", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="A exclusão da ficha original foi cancelada.", view=None)

@bot.tree.command(name="fichas", description="Mostra todas as fichas salvas em ordem.")
@app_commands.describe(guilda="Selecione a guilda", idioma="Selecione o idioma")
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
async def fichas(interaction: discord.Interaction, guilda: app_commands.Choice[str], idioma: app_commands.Choice[str]):
    arquivo = arquivo_fichas(guilda.value, idioma.value)
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            fichas = json.load(f)
    except Exception:
        await interaction.response.send_message("❌ Não foi possível carregar o arquivo de fichas.", ephemeral=True)
        return

    if not fichas:
        await interaction.response.send_message("❌ Nenhuma ficha registrada.", ephemeral=True)
        return

    fichas_ordenadas = sorted(fichas.values(), key=lambda f: f.get("numero", 0))
    embed = discord.Embed(
        title=f"📋 Fichas Salvas – {guilda.name} ({idioma.name})",
        description=f"Total: {len(fichas_ordenadas)} fichas",
        color=discord.Color.blue()
    )

    for ficha in fichas_ordenadas:
        numero = ficha.get("numero", "-")
        roblox = ficha.get("roblox", "-")
        discord_id = ficha.get("discord", "-")
        data = ficha.get("data", "-")
        linha = f"👤 <@{discord_id}> | 🎮 `{roblox}` | 📅 `{data}`"
        embed.add_field(name=f"Ficha #{numero}", value=linha, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

import discord
import json
import os

@bot.tree.command(name="debug_fichas", description="(ADM) Ver fichas salvas da guilda/idioma selecionado")
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
async def debug_fichas(interaction: discord.Interaction, guilda: app_commands.Choice[str], idioma: app_commands.Choice[str]):
    arquivo = arquivo_fichas(guilda.value, idioma.value)
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            todas = json.load(f)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro ao carregar: {e}", ephemeral=True)
        return

    if not todas:
        await interaction.response.send_message("📂 Nenhuma ficha encontrada nesse arquivo.", ephemeral=True)
        return

    preview = ""
    for uid, ficha in todas.items():
        preview += f"• {ficha.get('roblox')} #{ficha.get('numero')} (ID: {uid})\n"
    await interaction.response.send_message(f"📝 Fichas encontradas:\n```{preview}```", ephemeral=True)

@bot.tree.command(name="duplicar_ficha", description="Duplica uma ficha existente para um novo número ou usuário (ADMIN)")
@app_commands.describe(
    numero_antigo="Número atual da ficha",
    user_id_antigo="ID do usuário da ficha a ser duplicada",
    numero_novo="Novo número da ficha duplicada",
    user_id_novo="(Opcional) Novo ID de usuário para a ficha duplicada",
    guilda="Selecione a guilda (hades ou hades2)",
    idioma="Selecione o idioma (pt, en, es)"
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
)
@app_commands.default_permissions(administrator=True)
async def duplicar_ficha(
    interaction: discord.Interaction,
    numero_antigo: int,
    user_id_antigo: str,
    numero_novo: int,
    user_id_novo: str = None,
    guilda: app_commands.Choice[str] = None,
    idioma: app_commands.Choice[str] = None,
):
    arquivo = arquivo_fichas(guilda.value, idioma.value)
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            todas = json.load(f)
    except Exception:
        await interaction.response.send_message("❌ Não foi possível abrir o arquivo de fichas.", ephemeral=True)
        return

    ficha = todas.get(user_id_antigo)
    if not ficha or ficha.get("numero") != numero_antigo:
        await interaction.response.send_message("❌ Ficha de origem não encontrada.", ephemeral=True)
        return

    novo_id = user_id_novo if user_id_novo else user_id_antigo
    if novo_id in todas:
        await interaction.response.send_message("❌ Já existe uma ficha com esse user_id no arquivo. Exclua ou use outro ID.", ephemeral=True)
        return

    nova_ficha = ficha.copy()
    nova_ficha["numero"] = numero_novo
    todas[novo_id] = nova_ficha

    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(todas, f, ensure_ascii=False, indent=2)

    mensagem = (
        f"✅ Ficha duplicada com sucesso!\n"
        f"Novo número: **{numero_novo}**\nUser ID: **{novo_id}**\n\n"
        f"❓ Deseja excluir a ficha original de número **{numero_antigo}**?"
    )
    view = ConfirmarExclusaoView(arquivo, user_id_antigo)
    await interaction.response.send_message(mensagem, view=view, ephemeral=True)

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
    except Exception:
        await interaction.response.send_message("❌ Erro ao carregar as fichas.", ephemeral=True)
        return

    if not todas:
        await interaction.response.send_message("⚠️ Nenhuma ficha registrada encontrada.", ephemeral=True)
        return

    await interaction.response.send_message(
        "📋 Selecione qual ficha deseja editar:",
        view=ViewSelecaoFicha(todas, guilda.value, idioma.value),
        ephemeral=True
    )
@bot.tree.command(name="remover_servidor", description="Remove um servidor salvo pelo nome")
@app_commands.describe(nome="Nome do servidor")
async def remover_servidor(interaction: discord.Interaction, nome: str):
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
async def atualizar_servidor(interaction: discord.Interaction, nome: str, membro: discord.Member):
    servidores = carregar_servidores()
    for servidor in servidores:
        if servidor['nome'].lower() == nome.lower():
            servidor['autor_id'] = membro.id
            salvar_servidores(servidores)
            await interaction.response.send_message(f"✅ Foto do servidor **{nome}** atualizada para **{membro.display_name}**.", ephemeral=True)
            return
    await interaction.response.send_message(f"❌ Servidor **{nome}** não encontrado.", ephemeral=True)

@bot.tree.command(name="servidores", description="Lista todos os servidores com botão de entrada")
async def servidores(interaction: discord.Interaction):
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
async def servidor(interaction: discord.Interaction, nome: str):
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
@bot.tree.command(name="enviar_aviso_diario", description="Envia aviso diário manualmente")
@app_commands.default_permissions(administrator=True)
async def enviar_aviso_diario_cmd(interaction: discord.Interaction):
    await enviar_aviso("diario", CANAL_AVISOS_ID, CARGO_ANALISE_ID, "# 📝 Verifiquem a Entrada/diaria e abra seu ticket!", bot)
    set_data_ultimo_envio("ultimo_aviso_diario")
    await interaction.response.send_message("✅ Aviso diário enviado manualmente.", ephemeral=True)

@bot.tree.command(name="enviar_aviso_2dias", description="Envia aviso de 2 dias manualmente")
@app_commands.default_permissions(administrator=True)
async def enviar_aviso_2dias_cmd(interaction: discord.Interaction):
    await enviar_aviso("2dias", CANAL_2DIAS_ID, CARGO_2DIAS_ID, "# 📝 Mande sua meta diária e ajude a guilda a evoluir!", bot)
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

@bot.tree.command(name="pingstaff", description="Envie uma mensagem anônima para o canal atual")
@app_commands.describe(mensagem="Mensagem que será enviada no canal, sem mostrar quem enviou")
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
            await enviar_aviso("diario", CANAL_AVISOS_ID, CARGO_ANALISE_ID, "# 📝 Verifiquem a Entrada/diaria e abra seu ticket!", bot)
            set_data_ultimo_envio("ultimo_aviso_diario")

@tasks.loop(minutes=1)
async def aviso_cada_2_dias():
    agora = get_hora_brasilia()
    if agora.hour == 15 and agora.minute == 0:
        ultimo = get_data_ultimo_envio("ultimo_aviso_2dias")
        if not ultimo or (agora - ultimo).total_seconds() >= 172800:
            await enviar_aviso("2dias", CANAL_2DIAS_ID, CARGO_2DIAS_ID, "# 📝 Mande sua meta diária e ajude a guilda a evoluir!", bot)
            set_data_ultimo_envio("ultimo_aviso_2dias")

@tasks.loop(minutes=5)
async def keep_alive_task():
    pass

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
