import discord
from discord import ui
import json
import os
from datetime import datetime
import pytz

# =================== CONSTANTES GLOBAIS ===================
FICHAS_CANAL_ID = 1386798237163323493
FICHAS_CANAL_HADES2_ID = 1388546663190364241
CANAL_ARQUIVO_FICHAS_ID = 1386832198405193868
ARQUIVO_SERVIDORES = 'servidores.json'
ARQUIVO_ENVIOS = 'envios.json'
AVISOS_CONFIG = 'avisos_config.json'
CANAL_AVISOS_ID = 1380022433288949851
CARGO_ANALISE_ID = 1379508463172063286
CANAL_2DIAS_ID = 1379585139629228062
CARGO_2DIAS_ID = 1379508463172063290
NUMERO_FICHA_PADRAO = {"hades": 77, "hades2": 8}
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
    ("numero", "Número da ficha")
]
GUILDAS = [("hades", "Hades"), ("hades2", "Hades2")]

# =============== FUNÇÕES AUXILIARES ===============

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
    
def carregar_ficha_por_nick(roblox, guilda, idioma):
    arquivo = arquivo_fichas(guilda, idioma)
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            todas = json.load(f)
    except Exception:
        return None, None
    for uid, ficha in todas.items():
        if ficha.get("roblox", "").lower() == roblox.lower():
            return uid, ficha
    return None, None

def carregar_ficha_por_uid(uid, guilda, idioma):
    arquivo = arquivo_fichas(guilda, idioma)
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            todas = json.load(f)
        return todas.get(uid)
    except Exception:
        return None

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

def carregar_servidores():
    if not os.path.exists(ARQUIVO_SERVIDORES):
        return []
    with open(ARQUIVO_SERVIDORES, 'r') as f:
        return json.load(f)

def salvar_servidores(lista):
    with open(ARQUIVO_SERVIDORES, 'w') as f:
        json.dump(lista, f, indent=4)

def carregar_envios():
    if not os.path.exists(ARQUIVO_ENVIOS):
        return {}
    with open(ARQUIVO_ENVIOS, 'r') as f:
        return json.load(f)

def salvar_envios(dados):
    with open(ARQUIVO_ENVIOS, 'w') as f:
        json.dump(dados, f, indent=4)

def get_data_ultimo_envio(chave):
    envios = carregar_envios()
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
    envios = carregar_envios()
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

# =============== CLASSES DE UI ===============

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
            numero_ficha = ficha_existente.get("numero")
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

import json
from discord.ui import View, Button, Modal, TextInput
from discord import Interaction

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

class ViewSelecaoFicha(View):
    def __init__(self, todas_fichas: dict, guilda: str, idioma: str):
        super().__init__(timeout=300)
        self.todas_fichas = list(todas_fichas.items())
        self.guilda = guilda
        self.idioma = idioma
        self.pagina_atual = 0
        self.max_por_pagina = 25
        self.message = None

        self.atualizar_botoes()

    def atualizar_botoes(self):
        self.clear_items()
        inicio = self.pagina_atual * self.max_por_pagina
        fim = inicio + self.max_por_pagina
        fichas_pagina = self.todas_fichas[inicio:fim]

        for chave, ficha in fichas_pagina:
            numero = ficha.get("numero", "??")
            nome = ficha.get("roblox", "Sem nome")
            btn = Button(label=f"#{numero} {nome}", style=1)
            btn.callback = self.botao_callback_factory(chave)
            self.add_item(btn)

        if self.pagina_atual > 0:
            btn_ant = Button(label="⬅️ Anterior", style=2)
            btn_ant.callback = self.anterior_callback
            self.add_item(btn_ant)

        if fim < len(self.todas_fichas):
            btn_prox = Button(label="Próximo ➡️", style=2)
            btn_prox.callback = self.proximo_callback
            self.add_item(btn_prox)

    def botao_callback_factory(self, ficha_key):
        async def callback(interaction: Interaction):
            modal = ModalEditarFicha(self.todas_fichas_dict(), self.guilda, self.idioma, ficha_key)
            await interaction.response.send_modal(modal)
        return callback

    def todas_fichas_dict(self):
        return dict(self.todas_fichas)

    async def anterior_callback(self, interaction: Interaction):
        if self.pagina_atual > 0:
            self.pagina_atual -= 1
            self.atualizar_botoes()
            await interaction.response.edit_message(view=self)

    async def proximo_callback(self, interaction: Interaction):
        if (self.pagina_atual + 1) * self.max_por_pagina < len(self.todas_fichas):
            self.pagina_atual += 1
            self.atualizar_botoes()
            await interaction.response.edit_message(view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(content="⏱️ Tempo esgotado para editar a ficha.", view=self)
            except:
                pass

class ModalEditarFicha(Modal):
    def __init__(self, todas_fichas: dict, guilda: str, idioma: str, ficha_key: str):
        super().__init__(title="Editar Ficha")
        self.todas_fichas = todas_fichas
        self.guilda = guilda
        self.idioma = idioma
        self.ficha_key = ficha_key

        ficha = todas_fichas[ficha_key]

        self.text_roblox = TextInput(label="Nome Roblox", default=ficha.get("roblox", ""), max_length=30)
        self.text_dps = TextInput(label="DPS", default=ficha.get("dps", ""), max_length=20, required=False)
        self.text_farm = TextInput(label="Farm", default=ficha.get("farm", ""), max_length=20, required=False)
        self.text_rank = TextInput(label="Rank", default=ficha.get("rank", ""), max_length=20, required=False)
        self.text_level = TextInput(label="Level", default=str(ficha.get("level", "")), max_length=10, required=False)
        self.text_tempo = TextInput(label="Tempo", default=ficha.get("tempo", ""), max_length=20, required=False)
        self.text_data = TextInput(label="Data", default=ficha.get("data", ""), max_length=20, required=False)
        self.text_discord = TextInput(label="Discord", default=ficha.get("discord", ""), max_length=30, required=False)

        self.add_item(self.text_roblox)
        self.add_item(self.text_dps)
        self.add_item(self.text_farm)
        self.add_item(self.text_rank)
        self.add_item(self.text_level)
        self.add_item(self.text_tempo)
        self.add_item(self.text_data)
        self.add_item(self.text_discord)

    async def on_submit(self, interaction: Interaction):
        ficha = self.todas_fichas[self.ficha_key]
        ficha["roblox"] = self.text_roblox.value
        ficha["dps"] = self.text_dps.value
        ficha["farm"] = self.text_farm.value
        ficha["rank"] = self.text_rank.value
        try:
            ficha["level"] = int(self.text_level.value)
        except:
            ficha["level"] = self.text_level.value
        ficha["tempo"] = self.text_tempo.value
        ficha["data"] = self.text_data.value
        ficha["discord"] = self.text_discord.value

        salvar_ficha_por_uid(self.ficha_key, ficha, self.guilda, self.idioma)
        await interaction.response.send_message("✅ Ficha atualizada com sucesso!", ephemeral=True)
# =============== FLUXO DE PREENCHIMENTO DE FICHA ===============

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
        mention = member.mention
    else:
        try:
            fetched_user = await bot.fetch_user(int(discord_id))
            avatar_url = fetched_user.avatar.url if fetched_user.avatar else fetched_user.default_avatar.url
            display_name = fetched_user.display_name
            mention = fetched_user.mention
        except:
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            display_name = user.display_name
            mention = f"<@{discord_id}>" if discord_id else user.mention
    nome_guilda_fmt = "Hades" if nome_guilda == "hades" else "Hades 2"
    bandeira = IDIOMAS.get(ficha.get("idioma"), {}).get("bandeira", "")
    discord_str = member.mention if member else (f"<@{discord_id}>" if discord_id else user.mention)
    embed = discord.Embed(
        title=f"🌌 Ficha de Jogador #{ficha['numero']} – Arise Crossover {bandeira} 🌌",
        color=discord.Color.purple()
    )
    embed.add_field(name=f"🎮 {TEXTOS[idioma]['label_roblox']}", value=ficha['roblox'], inline=False)
    embed.add_field(name=f"🏰 Guilda", value=nome_guilda_fmt, inline=True)
    embed.add_field(name="💬 Discord", value=discord_str, inline=True)
    embed.add_field(name=f"⚔️ {TEXTOS[idioma]['label_dps']}", value=ficha['dps'], inline=False)
    embed.add_field(name=f"💎 {TEXTOS[idioma]['label_farm']}", value=ficha['farm'], inline=False)
    embed.add_field(
        name="📊 Outras Informações",
        value=(f"🔹 {TEXTOS[idioma]['label_rank']}: {ficha['rank']}\n"
               f"🔹 {TEXTOS[idioma]['label_level']}: {ficha['level']}\n"
               f"🔹 {TEXTOS[idioma]['label_tempo']}: {ficha['tempo']}"),
        inline=False
    )
    embed.set_footer(text=f"{TEXTOS[idioma]['label_data']}: {ficha['data']}")
    embed.set_thumbnail(url=avatar_url)
    if canal:
        await canal.send(embed=embed)

async def finalizar_ficha(interaction, user, ficha_data, guilda, idioma, canal_destino, canal, bot_refazer):
    bandeira = IDIOMAS.get(idioma, {}).get("bandeira", "")
    embed = discord.Embed(
        title=f"{TEXTOS[idioma]['titulo_embed']} {bandeira}",
        color=discord.Color.blurple()
    )
    embed.add_field(name=f"🎮 {TEXTOS[idioma]['label_roblox']}", value=ficha_data['roblox'], inline=False)
    embed.add_field(name=f"⚔️ {TEXTOS[idioma]['label_dps']}", value=ficha_data['dps'], inline=True)
    embed.add_field(name=f"💎 {TEXTOS[idioma]['label_farm']}", value=ficha_data['farm'], inline=True)
    embed.add_field(name=f"🔹 {TEXTOS[idioma]['label_rank']}", value=ficha_data['rank'], inline=True)
    embed.add_field(name=f"🔹 {TEXTOS[idioma]['label_level']}", value=ficha_data['level'], inline=True)
    embed.add_field(name=f"🔹 {TEXTOS[idioma]['label_tempo']}", value=ficha_data['tempo'], inline=True)
    embed.set_footer(text=f"{TEXTOS[idioma]['label_data']}: {ficha_data['data']} | Guilda: {guilda} | Idioma: {idioma}")
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
