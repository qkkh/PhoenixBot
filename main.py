import asyncio, os, discord, datetime
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
ALLOWED_CHANNELS = [1378251863098392596, 1378251900348141589, 1378251920237395998]

# نظام التحميل المنظم (Embeds) - تم تحسينه لمنع فشل التفاعل
class CloudDownloadView(discord.ui.View):
    def __init__(self, av_url, bn_url):
        super().__init__(timeout=None) # يخلي الزر شغال للأبد
        self.av_url, self.bn_url = av_url, bn_url

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="<:download:1286653105878077450>")
    async def download(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            embed_av = discord.Embed(color=0x2b2d31)
            embed_av.set_author(name="Phoenix", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
            embed_av.set_image(url=self.av_url)
            
            embed_bn = discord.Embed(color=0x2b2d31)
            embed_bn.set_author(name="Phoenix", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
            embed_bn.set_image(url=self.bn_url)
            
            await interaction.response.send_message(embeds=[embed_av, embed_bn], ephemeral=True)
        except:
            # إذا فشل الإمبد يرسل روابط نصية كخيار احتياطي أخير
            await interaction.response.send_message(f"Avatar: {self.av_url}\nBanner: {self.bn_url}", ephemeral=True)

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
                file = discord.File(fp=background.image_bytes, filename="welcome.png")
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

    async def on_message(self, message):
        if message.author.bot: return
        if message.channel.id in ALLOWED_CHANNELS and len(message.attachments) == 2:
            if all(message.attachments[i].content_type.startswith('image') for i in range(2)):
                msg = await message.channel.send("⏳ جاري المعالجة...")
                try:
                    av_url = message.attachments[0].url
                    bn_url = message.attachments[1].url
                    canvas = Editor(Canvas(size=(3188, 2160), color="#000000")) 
                    canvas.paste(Editor(await load_image_async(bn_url)).resize((3188, 1100)), (0, 0))
                    canvas.paste(Editor(await load_image_async(av_url)).resize((900, 900)).circle_image(), (100, 550))
                    canvas.paste(Editor("template.png"), (0, 0))
                    
                    file = discord.File(fp=canvas.image_bytes, filename="profile.png")
                    await message.channel.send(file=file, view=CloudDownloadView(av_url, bn_url))
                    await message.delete()
                    await msg.delete()
                except:
                    await msg.edit(content="❌ حدث خطأ، تأكد من جودة الصور.")
        await self.process_commands(message)

bot = MyBot()

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
