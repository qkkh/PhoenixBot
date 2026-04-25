import asyncio, os, discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# --- نظام الاستضافة للبقاء حياً 24 ساعة ---
app = Flask('')
@app.route('/')
def home(): return "Phoenix Elite is Active"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- إعداداتك الخاصة ---
OWNER_ID = 1341796578742243338 
PHOENIX_COLOR = 0x00aaff 

# رومات الصور
GIRLS_ROOM = 1378251900348141589
BOYS_ROOM = 1378251863098392596
ANIME_ROOM = 1378251920237395998
WELCOME_ROOM_ID = 1347630031337160764 # روم الترحيب الجديد

class ImageModal(discord.ui.Modal):
    def __init__(self, room_id, title_name):
        super().__init__(title=f"نشر في قسم {title_name}")
        self.room_id = room_id
        self.img_url = discord.ui.TextInput(label="رابط الصورة (Avatar/Banner)", placeholder="ضع الرابط هنا...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(self.room_id)
        if channel:
            embed = discord.Embed(color=PHOENIX_COLOR)
            embed.set_image(url=self.img_url.value)
            await channel.send(embed=embed)
            await interaction.response.send_message(f"✅ تم النشر في قسم {channel.name}", ephemeral=True)

class PhoenixDashboard(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
    
    @discord.ui.button(label="PHOENIX status", style=discord.ButtonStyle.secondary)
    async def status_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID: return
        guild = interaction.guild
        embed = discord.Embed(title="PHOENIX status", color=PHOENIX_COLOR)
        embed.add_field(name="الأعضاء", value=str(guild.member_count), inline=True)
        embed.add_field(name="المتصلين", value=str(len([m for m in guild.members if m.status != discord.Status.offline])), inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="افتار بنات", style=discord.ButtonStyle.primary)
    async def girls_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID: return
        await interaction.response.send_modal(ImageModal(GIRLS_ROOM, "البنات"))

    @discord.ui.button(label="افتار شباب", style=discord.ButtonStyle.primary)
    async def boys_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID: return
        await interaction.response.send_modal(ImageModal(BOYS_ROOM, "الشباب"))

    @discord.ui.button(label="افتار انمي", style=discord.ButtonStyle.primary)
    async def anime_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID: return
        await interaction.response.send_modal(ImageModal(ANIME_ROOM, "الانمي"))

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
    
    async def on_ready(self):
        await self.tree.sync()
        print(f"Phoenix Elite Panel is Online")

    # نظام الترحيب المطور
    async def on_member_join(self, member):
        welcome_channel = member.guild.get_channel(WELCOME_ROOM_ID)
        if welcome_channel:
            embed = discord.Embed(
                description=f"Welcome , {member.mention} Enjoy your stay in Phoenix Rising", 
                color=PHOENIX_COLOR
            )
            # تم استخدام رابط مباشر افتراضي، تأكد من استبداله برابط صورتك المرفوعة
            embed.set_image(url="https://i.postimg.cc/85M8qK2y/welcome.png") 
            await welcome_channel.send(content=f"{member.mention}", embed=embed)

bot = MyBot()

@bot.command(name="79")
async def panel(ctx):
    if ctx.author.id == OWNER_ID:
        # تصميم البانل الجديد
        emb = discord.Embed(
            title="PHOENIX RISING", 
            description="مرحباً بك يا زعيم الفينيق. هذه هي لوحة التحكم الخاصة بك، مصممة لتنفيذ أوامرك بضغطة زر واحدة.", 
            color=PHOENIX_COLOR
        )
        emb.set_thumbnail(url=bot.user.display_avatar.url)
        await ctx.send(embed=emb, view=PhoenixDashboard(bot))

if __name__ == '__main__':
    keep_alive()
    bot.run(os.getenv('DISCORD_TOKEN'))
