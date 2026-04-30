import asyncio, os, discord, datetime, io, aiohttp
from discord.ext import commands, tasks
from discord import app_commands
from flask import Flask
from threading import Thread
from easy_pil import Editor, Canvas
from PIL import Image

# --- إعدادات القنوات الجديدة بناءً على طلبك ---
CHANNELS = {
    "شباب": 1378251863098392596, 
    "بنات": 1378251900348141589, 
    "انمي": 1378251920237395998  
}
OWNER_ID = 1341796578742243338

# --- نظام البقاء متصلاً ---
app = Flask('')
@app.route('/')
def home(): return "Phoenix Rising Active"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

async def download_image(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200: return await resp.read()
        except: return None
    return None

# --- أزرار التحميل داخل رومات الأرشيف ---
class DownloadView(discord.ui.View):
    def __init__(self, av_data, bn_data):
        super().__init__(timeout=None)
        self.av_data, self.bn_data = av_data, bn_data

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="<:download:1286653105878077450>")
    async def download(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        files, embeds = [], []
        if self.av_data:
            files.append(discord.File(io.BytesIO(self.av_data), filename="avatar.png"))
            embeds.append(discord.Embed(color=0x2b2d31).set_image(url="attachment://avatar.png"))
        if self.bn_data:
            files.append(discord.File(io.BytesIO(self.bn_data), filename="banner.png"))
            embeds.append(discord.Embed(color=0x2b2d31).set_image(url="attachment://banner.png"))
        await interaction.followup.send(embeds=embeds, files=files, ephemeral=True)

# --- نافذة إدخال الروابط (Modal) ---
class PostModal(discord.ui.Modal):
    def __init__(self, category_name):
        super().__init__(title=f"نشر في أرشيف {category_name}")
        self.category_name = category_name
        
    avatar_url = discord.ui.TextInput(label="رابط الأفتار", placeholder="صق رابط الأفتار المباشر هنا...", required=True)
    banner_url = discord.ui.TextInput(label="رابط البنر", placeholder="صق رابط البنر المباشر هنا...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        # تأكيد استلام الطلب فوراً لمنع "Interaction Failed"
        await interaction.response.defer(ephemeral=True)
        
        av_data = await download_image(self.avatar_url.value)
        bn_data = await download_image(self.banner_url.value)
        
        if not av_data or not bn_data:
            return await interaction.followup.send("❌ حدث خطأ في تحميل الصور تأكد من الروابط", ephemeral=True)

        target_ch_id = CHANNELS.get(self.category_name)
        channel = interaction.guild.get_channel(target_ch_id)
        
        if not channel:
            return await interaction.followup.send("❌ لم أتمكن من العثور على الروم المطلوب", ephemeral=True)

        # دمج الأفتار والبنر في صورة واحدة
        try:
            canvas = Editor(Canvas(size=(3188, 2160), color="#000000")) 
            canvas.paste(Editor(Image.open(io.BytesIO(bn_data))).resize((3188, 1100)), (0, 0))
            canvas.paste(Editor(Image.open(io.BytesIO(av_data))).resize((900, 900)).circle_image(), (100, 550))
            canvas.paste(Editor("template.png"), (0, 0))
            
            img_bin = io.BytesIO()
            canvas.image.save(img_bin, "PNG")
            img_bin.seek(0)

            embed = discord.Embed(description=f"**تمت الأرشفة بواسطة: {interaction.user.mention}**", color=0x2b2d31)
            embed.set_image(url="attachment://archive.png")
            
            await channel.send(
                embed=embed, 
                file=discord.File(fp=img_bin, filename="archive.png"),
                view=DownloadView(av_data, bn_data)
            )
            await interaction.followup.send(f"✅ تم النشر بنجاح في {self.category_name}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ حدث خطأ أثناء المعالجة: {e}", ephemeral=True)

# --- واجهة اللوحة الرئيسية ---
class PersistentDashboard(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="اضغط هنا لاختيار القسم والنشر...",
        min_values=1, max_values=1,
        options=[
            discord.SelectOption(label="أرشيف الشباب", value="شباب", emoji="👦", description="نشر في روم شباب"),
            discord.SelectOption(label="أرشيف البنات", value="بنات", emoji="👧", description="نشر في روم بنات"),
            discord.SelectOption(label="أرشيف الانمي", value="انمي", emoji="⛩️", description="نشر في روم انمي")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        # التحقق من الصلاحيات (المالك أو من لديه صلاحية إدارة الرسائل)
        if interaction.user.id == OWNER_ID or interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_modal(PostModal(select.values[0]))
        else:
            await interaction.response.send_message("❌ هذا النظام مخصص للإدارة فقط", ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
    
    async def setup_hook(self):
        # جعل الأزرار تعمل حتى بعد إعادة تشغيل البوت
        self.add_view(PersistentDashboard())
        await self.tree.sync()

bot = MyBot()

@bot.tree.command(name="setav", description="إنشاء لوحة تحكم الأرشيف الثابتة")
async def setav(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ الأمر للمالك فقط", ephemeral=True)
    
    embed = discord.Embed(
        title="Phoenix Rising | نظام الأرشفة", 
        description="مرحباً بك في لوحة التحكم بالأرشيف\nاختر القسم الذي تريد رفع الصور إليه من القائمة أدناه",
        color=0x2b2d31
    )
    
    # استخدام صورة السيرفر كصورة رئيسية للوحة
    if interaction.guild.icon:
        embed.set_image(url=interaction.guild.icon.url)
    
    await interaction.channel.send(embed=embed, view=PersistentDashboard())
    await interaction.response.send_message("✅ تم إنشاء لوحة التحكم بنجاح", ephemeral=True)

if __name__ == '__main__':
    keep_alive()
    bot.run(os.getenv('DISCORD_TOKEN'))
