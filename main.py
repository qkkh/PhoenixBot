import asyncio, os, discord, datetime, io, aiohttp
from discord.ext import commands, tasks
from discord import app_commands
from flask import Flask
from threading import Thread
from easy_pil import Editor, load_image_async, Canvas

# كود الاستمرارية
app = Flask('')
@app.route('/')
def home(): return "Phoenix Rising System Active"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

WELCOME_ROOM_ID = 1347630031337160764
CATEGORY_ID = 1497599277793284248 
OWNER_ID = 1341796578742243338

# وظيفة ذكية لتحميل الصور وتجاوز قيود الروابط المؤقتة
async def download_image(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.read()
    return None

class CloudDownloadView(discord.ui.View):
    def __init__(self, av_data, bn_data):
        super().__init__(timeout=None)
        self.av_data = av_data
        self.bn_data = bn_data

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="<:download:1286653105878077450>")
    async def download(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        # نرسل البيانات المخزنة كملفات مباشرة
        file1 = discord.File(io.BytesIO(self.av_data), filename="avatar.png")
        file2 = discord.File(io.BytesIO(self.bn_data), filename="banner.png")
        
        embed1 = discord.Embed(color=0x2b2d31).set_image(url="attachment://avatar.png")
        embed2 = discord.Embed(color=0x2b2d31).set_image(url="attachment://banner.png")
        
        await interaction.followup.send(embeds=[embed1, embed2], files=[file1, file2], ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
    
    async def setup_hook(self):
        await self.tree.sync()
        if not self.auto_refresh_task.is_running():
            self.auto_refresh_task.start()

    async def on_member_join(self, member):
        channel = self.get_channel(WELCOME_ROOM_ID)
        if channel:
            try:
                background = Editor("welcome.png")
                avatar_image = await load_image_async(member.display_avatar.url)
                avatar = Editor(avatar_image).resize((170, 170)).circle_image()
                background.paste(avatar, (52, 72)) 
                file = discord.File(fp=background.image_bytes, filename="welcome_card.png")
                await channel.send(content=f"_'Have fun in **__PhoenixRising__**_\n     _'User: {member.mention}_<a:Via1:1378238620418183188>", file=file)
            except: pass

    @tasks.loop(minutes=30)
    async def auto_refresh_task(self):
        for guild in self.guilds:
            category = guild.get_channel(CATEGORY_ID)
            if category:
                for ch in category.voice_channels: 
                    try: await ch.delete()
                    except: pass
                total = guild.member_count
                online = len([m for m in guild.members if m.status != discord.Status.offline])
                await guild.create_voice_channel(name=f"Members: {total}", category=category)
                await guild.create_voice_channel(name=f"Online: {online}", category=category)

bot = MyBot()

@bot.tree.command(name="نشر", description="نشر بروفايل")
async def post(interaction: discord.Interaction, الافتار: str, البنر: str):
    if interaction.user.id == OWNER_ID or interaction.user.guild_permissions.manage_messages:
        await interaction.response.defer(ephemeral=True)
        try:
            # نسحب بيانات الصور فوراً قبل ما تنتهي صلاحية الرابط
            av_data = await download_image(الافتار)
            bn_data = await download_image(البنر)
            
            if not av_data or not bn_data:
                return await interaction.followup.send("❌ تعذر سحب الصور من الروابط تأكد من صحتها")

            canvas = Editor(Canvas(size=(3188, 2160), color="#000000")) 
            canvas.paste(Editor(await load_image_async(io.BytesIO(bn_data))).resize((3188, 1100)), (0, 0))
            canvas.paste(Editor(await load_image_async(io.BytesIO(av_data))).resize((900, 900)).circle_image(), (100, 550))
            canvas.paste(Editor("template.png"), (0, 0))
            
            file = discord.File(fp=canvas.image_bytes, filename="profile.png")
            # نمرر البيانات المخزنة للـ View عشان تبقى شغالة للأبد
            await interaction.channel.send(file=file, view=CloudDownloadView(av_data, bn_data))
            await interaction.followup.send("Done", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)

# الأوامر الإدارية
@bot.tree.command(name="مسح")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, العدد: int):
    await interaction.channel.purge(limit=العدد)
    await interaction.response.send_message(f"🧹 تم مسح {العدد} رسالة", ephemeral=True)

@bot.tree.command(name="قفل_القناة")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 تم قفل القناة")

@bot.tree.command(name="فتح_القناة")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 تم فتح القناة")

@bot.tree.command(name="الحالة")
async def change_status(interaction: discord.Interaction, النص: str):
    if interaction.user.id == OWNER_ID:
        await bot.change_presence(activity=discord.Game(name=النص))
        await interaction.response.send_message(f"✅ تم تغيير الحالة", ephemeral=True)

if __name__ == '__main__':
    keep_alive()
    bot.run(os.getenv('DISCORD_TOKEN'))
