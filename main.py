import asyncio, os, discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# --- نظام الاستضافة ---
app = Flask('')
@app.route('/')
def home(): return "Phoenix Stats System Active"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- إعداداتك الخاصة ---
OWNER_ID = 1341796578742243338 
PHOENIX_COLOR = 0x00aaff 
CATEGORY_ID = 1497599277793284248 # الكاتيجوري المطلوب

# رومات الصور
GIRLS_ROOM = 1378251900348141589
BOYS_ROOM = 1378251863098392596
ANIME_ROOM = 1378251920237395998
WELCOME_ROOM_ID = 1347630031337160764

class ImageModal(discord.ui.Modal):
    def __init__(self, room_id, title_name):
        super().__init__(title=f"نشر في قسم {title_name}")
        self.room_id = room_id
        self.avatar_url = discord.ui.TextInput(label="رابط الأفتار", placeholder="ضع الرابط هنا...", required=True)
        self.banner_url = discord.ui.TextInput(label="رابط البانر", placeholder="ضع الرابط هنا (اختياري)...", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(self.room_id)
        if channel:
            embed = discord.Embed(title=f"New Post", color=PHOENIX_COLOR)
            embed.set_image(url=self.avatar_url.value)
            if self.banner_url.value:
                embed.set_thumbnail(url=self.banner_url.value)
            await channel.send(embed=embed)
            await interaction.response.send_message(f"✅ تم النشر في {channel.name}", ephemeral=True)

class PhoenixDashboard(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
    
    @discord.ui.button(label="PHOENIX status", style=discord.ButtonStyle.secondary)
    async def status_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID: return
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        category = guild.get_channel(CATEGORY_ID)
        
        if not category or not isinstance(category, discord.CategoryChannel):
            return await interaction.followup.send("❌ لم يتم العثور على الكاتيجوري", ephemeral=True)

        # 1. حذف القنوات القديمة داخل الكاتيجوري لتجنب التكرار
        for channel in category.voice_channels:
            await channel.delete()

        # 2. حساب الأرقام الفعلية
        total = guild.member_count
        online = len([m for m in guild.members if m.status != discord.Status.offline])
        bots = len([m for m in guild.members if m.bot])

        # 3. إنشاء القنوات الجديدة بالترتيب
        await guild.create_voice_channel(name=f"Members: {total}", category=category)
        await guild.create_voice_channel(name=f"Online: {online}", category=category)
        await guild.create_voice_channel(name=f"Bots: {bots}", category=category)

        await interaction.followup.send("✅ تم تحديث وإعادة بناء إحصائيات السيرفر بنجاح", ephemeral=True)

    @discord.ui.button(label="افتار بنات", style=discord.ButtonStyle.primary)
    async def girls_button(self, interaction, button):
        if interaction.user.id != OWNER_ID: return
        await interaction.response.send_modal(ImageModal(GIRLS_ROOM, "البنات"))

    @discord.ui.button(label="افتار شباب", style=discord.ButtonStyle.primary)
    async def boys_button(self, interaction, button):
        if interaction.user.id != OWNER_ID: return
        await interaction.response.send_modal(ImageModal(BOYS_ROOM, "الشباب"))

    @discord.ui.button(label="افتار انمي", style=discord.ButtonStyle.primary)
    async def anime_button(self, interaction, button):
        if interaction.user.id != OWNER_ID: return
        await interaction.response.send_modal(ImageModal(ANIME_ROOM, "الانمي"))

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
    
    async def on_ready(self):
        await self.tree.sync()
        print(f"Phoenix Stats Refresher is Online")

    async def on_member_join(self, member):
        welcome_channel = member.guild.get_channel(WELCOME_ROOM_ID)
        if welcome_channel:
            embed = discord.Embed(description=f"Welcome , {member.mention} Enjoy your stay in Phoenix Rising", color=PHOENIX_COLOR)
            embed.set_image(url="https://i.postimg.cc/85M8qK2y/welcome.png") # تأكد من رابط صورتك
            await welcome_channel.send(content=f"{member.mention}", embed=embed)

bot = MyBot()

@bot.command(name="79")
async def panel(ctx):
    if ctx.author.id == OWNER_ID:
        emb = discord.Embed(title="PHOENIX RISING", description="اضغط على PHOENIX status لتحديث قنوات الإحصائيات فوراً.", color=PHOENIX_COLOR)
        await ctx.send(embed=emb, view=PhoenixDashboard(bot))

if __name__ == '__main__':
    keep_alive()
    bot.run(os.getenv('DISCORD_TOKEN'))
