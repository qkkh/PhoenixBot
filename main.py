import asyncio, os, re, discord, requests
from discord.ext import commands
from flask import Flask
from threading import Thread

# --- نظام الاستضافة للبقاء حياً 24 ساعة ---
app = Flask('')
@app.route('/')
def home(): return "Phoenix Panel is Active"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- إعدادات فينيكس الخاصة ---
OWNER_ID = 1341796578742243338 
PREFIX = "!" 
PHOENIX_COLOR = 0x00aaff 

# --- واجهات التفاعل (Modals) ---

class YTPostModal(discord.ui.Modal, title='نشر فيديو يوتيوب 🎬'):
    link = discord.ui.TextInput(label="رابط الفيديو", required=True)
    def __init__(self, bot): super().__init__(); self.bot = bot
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            r = requests.get(self.link.value).text
            ch_name = re.search(r'"author":"(.*?)"', r).group(1)
            clean_name = re.sub(r'[^\w\s]', '', ch_name) 
        except: clean_name = "قناتنا"
        
        channel = interaction.guild.get_channel(924316521050820609)
        if channel:
            msg = f"انتباه يا أبطال الفينيق المبدع {clean_name} نزل مقطع جديد ورهيب شاهدوا المقطع الآن"
            await channel.send(content=f"@everyone\n{msg}\n{self.link.value}")
            await interaction.followup.send("✅ تم النشر بنجاح يا زعيم", ephemeral=True)

# --- لوحة التحكم المتكاملة ---

class PhoenixDashboard(discord.ui.View):
    def __init__(self, bot): super().__init__(timeout=None); self.bot = bot
    
    @discord.ui.button(label="نشر يوتيوب", style=discord.ButtonStyle.primary, emoji="🎥")
    async def yt_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID: return 
        await interaction.response.send_modal(YTPostModal(self.bot))

    @discord.ui.button(label="إحصائيات السيرفر", style=discord.ButtonStyle.secondary, emoji="📊")
    async def stats_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID: return
        members = interaction.guild.member_count
        emb = discord.Embed(title="📊 حالة سيرفر Phoenix", color=PHOENIX_COLOR)
        emb.add_field(name="الأعضاء", value=f"{members} بطل") 
        emb.set_footer(text="نظام مراقبة الفينيق")
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @discord.ui.button(label="قفل الروم", style=discord.ButtonStyle.danger, emoji="🔒")
    async def lock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID: return
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
        await interaction.response.send_message("🔒 تم قفل الروم فوراً", ephemeral=True)

# --- البوت الأساسي ---

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=PREFIX, intents=discord.Intents.all())
    
    async def on_ready(self):
        await self.tree.sync()
        print(f"Phoenix Rising is Online")

bot = MyBot()

@bot.command(name="79") 
async def panel(ctx):
    if ctx.author.id == OWNER_ID:
        emb = discord.Embed(
            title="🎮 مركز عمليات PHOENIX RISING", 
            description="مرحباً بك يا زعيم الفينيق هذه هي لوحة التحكم الخاصة بك والمشفرة لتستجيب لك أنت فقط", 
            color=PHOENIX_COLOR
        )
        await ctx.send(embed=emb, view=PhoenixDashboard(bot))
    else:
        await ctx.send("عذراً هذا الأمر مشفر لصاحب البوت فقط")

if __name__ == '__main__':
    keep_alive()
    bot.run(os.getenv('DISCORD_TOKEN'))
