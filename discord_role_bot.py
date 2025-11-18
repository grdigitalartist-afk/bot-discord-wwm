import discord
from discord.ext import commands
import os

# Configuração do bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Dicionário de cargos disponíveis organizados por categoria
CARGOS_DISPONIVEIS = {
    'HEALER': {
        '🪭': 'Leque (HEALER)',
        '☂️': 'Guarda-chuva (HEALER)'
    },
    'DPS': {
        '⚔️': 'Sword (DPS)',
        '🗡️': 'Katana (DPS)',
        '🔱': 'Lança Leve (DPS)'
    },
    'TANKER': {
        '🛡️': 'Lança Pesada (TANKER)',
        '⚒️': 'Espadão (TANKER)'
    }
}

@bot.event
async def on_ready():
    print(f'{bot.user} está online!')
    print(f'ID: {bot.user.id}')
    
    # Sincroniza os comandos slash
    try:
        synced = await bot.tree.sync()
        print(f'{len(synced)} comandos sincronizados')
    except Exception as e:
        print(f'Erro ao sincronizar comandos: {e}')

@bot.tree.command(name='cargos', description='Mostra o painel de seleção de cargos')
async def cargos(interaction: discord.Interaction):
    # Cria o embed
    embed = discord.Embed(
        description='**Escolha qual conjunto de armas você utiliza em Where Winds Meet:**',
        color=discord.Color.gold()
    )
    
    # Adiciona o banner como imagem do embed
    embed.set_image(url='attachment://banner.png')
    
    # Adiciona informações dos cargos por categoria
    for categoria, cargos in CARGOS_DISPONIVEIS.items():
        cargos_texto = '\n'.join([f'{emoji} {nome}' for emoji, nome in cargos.items()])
        embed.add_field(
            name=f'**{categoria}**',
            value=cargos_texto,
            inline=True
        )
    
    embed.set_footer(text='💡 Clique novamente no mesmo botão para remover o cargo')
    
    # Cria a view com os botões
    view = RoleView()
    
    # Carrega o banner
    import aiohttp
    import io
    
    # URL do banner
    banner_url = 'https://cdn.discordapp.com/attachments/1440443176488927335/1440443320508616704/banner-bot.png?ex=691e2ce1&is=691cdb61&hm=3633b148a6a3e93d27cf4d84a5699b09294657864c778e515019a3a73c50328b&'
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(banner_url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    banner_file = discord.File(io.BytesIO(data), filename='banner.png')
                    await interaction.response.send_message(
                        embed=embed, 
                        view=view, 
                        file=banner_file
                    )
                else:
                    # Se falhar ao carregar o banner, envia sem ele
                    await interaction.response.send_message(embed=embed, view=view)
    except:
        # Se der erro, envia sem o banner
        await interaction.response.send_message(embed=embed, view=view)

class RoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Sem timeout para persistência
        
        # Cores para cada categoria
        cores = {
            'HEALER': discord.ButtonStyle.success,
            'DPS': discord.ButtonStyle.danger,
            'TANKER': discord.ButtonStyle.primary
        }
        
        # Cria botões organizados por categoria
        for categoria, cargos in CARGOS_DISPONIVEIS.items():
            for emoji, nome_cargo in cargos.items():
                button = discord.ui.Button(
                    label=nome_cargo,
                    emoji=emoji,
                    style=cores[categoria],
                    custom_id=f'role_{categoria}_{nome_cargo}'
                )
                button.callback = self.criar_callback(nome_cargo, categoria)
                self.add_item(button)
    
    def criar_callback(self, nome_cargo, categoria):
        async def callback(interaction: discord.Interaction):
            # Busca o cargo no servidor
            cargo = discord.utils.get(interaction.guild.roles, name=nome_cargo)
            
            if not cargo:
                await interaction.response.send_message(
                    f'❌ O cargo "{nome_cargo}" não existe no servidor. '
                    f'Use `/criar_cargos` primeiro!',
                    ephemeral=True
                )
                return
            
            # Verifica se o usuário já tem o cargo
            if cargo in interaction.user.roles:
                # Remove o cargo
                await interaction.user.remove_roles(cargo)
                await interaction.response.send_message(
                    f'➖ Cargo **{nome_cargo}** ({categoria}) removido!',
                    ephemeral=True
                )
            else:
                # Remove outros cargos da mesma categoria antes de adicionar
                cargos_categoria = CARGOS_DISPONIVEIS[categoria].values()
                cargos_para_remover = []
                
                for cargo_existente in interaction.user.roles:
                    if cargo_existente.name in cargos_categoria:
                        cargos_para_remover.append(cargo_existente)
                
                if cargos_para_remover:
                    await interaction.user.remove_roles(*cargos_para_remover)
                
                # Adiciona o novo cargo
                await interaction.user.add_roles(cargo)
                
                mensagem = f'✅ Cargo **{nome_cargo}** ({categoria}) adicionado!'
                if cargos_para_remover:
                    removidos = ', '.join([c.name for c in cargos_para_remover])
                    mensagem += f'\n⚠️ Removido: {removidos}'
                
                await interaction.response.send_message(mensagem, ephemeral=True)
        
        return callback

@bot.tree.command(name='criar_cargos', description='Cria automaticamente todos os cargos configurados')
@commands.has_permissions(administrator=True)
async def criar_cargos(interaction: discord.Interaction):
    cargos_criados = []
    cargos_existentes = []
    
    # Percorre todas as categorias e cargos
    for categoria, cargos in CARGOS_DISPONIVEIS.items():
        for nome_cargo in cargos.values():
            cargo_existe = discord.utils.get(interaction.guild.roles, name=nome_cargo)
            
            if not cargo_existe:
                await interaction.guild.create_role(name=nome_cargo)
                cargos_criados.append(f'{nome_cargo} ({categoria})')
            else:
                cargos_existentes.append(f'{nome_cargo} ({categoria})')
    
    embed = discord.Embed(
        title='⚙️ Criação de Cargos',
        color=discord.Color.green()
    )
    
    if cargos_criados:
        embed.add_field(
            name='✅ Cargos Criados',
            value='\n'.join(cargos_criados),
            inline=False
        )
    if cargos_existentes:
        embed.add_field(
            name='ℹ️ Já Existiam',
            value='\n'.join(cargos_existentes),
            inline=False
        )
    
    if not cargos_criados and not cargos_existentes:
        embed.description = 'Nenhum cargo foi processado.'
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Token do bot (use variável de ambiente)
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    print('ERRO: Token do Discord não encontrado!')
    print('Configure a variável de ambiente DISCORD_TOKEN')
else:
    bot.run(TOKEN)