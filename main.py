import asyncio, os, discord, datetime, io, aiohttp
from discord.ext import commands, tasks
from discord import app_commands
from flask import Flask
from threading import Thread
from easy_pil import Editor, Canvas
from PIL import Image

# نظام البقاء متصلاً
app = Flask('')
@app.route('/')
def home(): return "Phoenix Rising Active"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# الإعدادات
WELCOME_ROOM_ID = 1347630031337160764
CATEGORY_ID = 1497599277793284248 
OWNER_ID = 1341796578742243338

# قنوات الأرشيف (بناءً على طلبك السابق)
ARCHIVE_CHANNELS = {
    "شباب": 1378251863098392596,
    "بنات": 1378251900348141589,
    "انمي": 1378251920237395998
}

async def download_image(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200: return await resp.read()
        except: return None
    return None

# --- أزرار التحميل المستمرة (Persistent) حق البروفايلات المنشورة ---
class CloudDownloadView(discord.ui.View):
    def __init__(self, av_data=None, bn_data=None):
        # تم إضافة timeout=None و custom_id لضمان عمل الأزرار دائماً في Render
        super().__init__(timeout=None)
        self.av_data = av_data
        self.bn_data = bn_data

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="<:download:1286653105878077450>", custom_id="download_btn_fixed")
    async def download(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        try:
            files, embeds = [], []
            if self.av_data:
                files.append(discord.File(io.BytesIO(self.av_data), filename="avatar.png"))
                embeds.append(discord.Embed(color=0x2b2d31).set_image(url="attachment://avatar.png"))
            if self.bn_data:
                files.append(discord.File(io.BytesIO(self.bn_data), filename="banner.png"))
                embeds.append(discord.Embed(color=0x2b2d31).set_image(url="attachment://banner.png"))
            await interaction.followup.send(embeds=embeds, files=files, ephemeral=True)
        except: await interaction.followup.send("حدث خطأ في التحميل", ephemeral=True)

# --- نافذة منبثقة لطلب روابط الصور (Modal) ---
class PostModal(discord.ui.Modal):
    def __init__(self, category_name):
        super().__init__(title=f"نشر في قسم {category_name}")
        self.category_name = category_name
        
    avatar_url = discord.ui.TextInput(label="رابط الأفتار", placeholder="صق رابط الأفتار المباشر هنا...", required=True)
    banner_url = discord.ui.TextInput(label="رابط البنر", placeholder="صق رابط البنر المباشر هنا...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        # تأكيد استلام الطلب فوراً لمنع Interaction Failed
        await interaction.response.defer(ephemeral=True)
        
        av_data = await download_image(self.avatar_url.value)
        bn_data = await download_image(self.banner_url.value)
        
        if not av_data or not bn_data:
            return await interaction.followup.send("❌ الروابط غير صالحة تأكد من الروابط"، ephemeral=True)

        target_ch_id = ARCHIVE_CHANNELS.get(self.category_name)
        channel = interaction.guild.get_channel(target_ch_id)
        
        if not channel:
            return await interaction.followup.send("❌ لم أتمكن من العثور على القناة المطلوبة"، ephemeral=True)

        # دمج الأفتار والبنر في صورة واحدة
        try:
            canvas = Editor(Canvas(size=(3188, 2160), color="#000000")) 
            canvas.paste(Editor(Image.open(io.BytesIO(bn_data))).resize((3188, 1100)), (0, 0))
            canvas.paste(Editor(Image.open(io.BytesIO(av_data))).resize((900, 900)).circle_image(), (100, 550))
            
            # فحص وجود ملف التمبلت لضمان عدم الانهيار في Render
            if os.path.exists("template.png"):
                canvas.paste(Editor("template.png"), (0, 0))
            
            img_bin = io.BytesIO()
            canvas.image.save(img_bin, "PNG")
            img_bin.seek(0)

            embed = discord.Embed(description=f"**بواسطة: {interaction.user.mention}**", color=0x2b2d31)
            embed.set_image(url="attachment://archive.png")
            
            # نشر الصورة مع زر التحميل
            await channel.send(
                embed=embed, 
                file=discord.File(fp=img_bin, filename="archive.png"),
                view=CloudDownloadView(av_data, bn_data)
            )
            await interaction.followup.send(f"✅ تم النشر في {self.category_name}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ حدث خطأ أثناء المعالجة: {e}", ephemeral=True)

# --- واجهة لوحة التحكم الثابتة المستمرة (هذا هو طلبك) ---
class PersistentDashboard(discord.ui.View):
    def __init__(self):
        # timeout=None و custom_id لضمان الاستمرارية دائماً
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="اضغط هنا لاختيار القسم والنشر...",
        custom_id="select_dashboard_unique", # معرف فريد للقائمة لمنع الانهيار
        options=[
            discord.SelectOption(label="أرشيف الشباب", value="شباب", emoji="👦", description="نشر في روم شباب"),
            discord.SelectOption(label="أرشيف البنات", value="بنات", emoji="👧", description="نشر في روم بنات"),
            discord.SelectOption(label="أرشيف الانمي", value="انمي", emoji="⛩️", description="نشر في روم انمي")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        # التحقق من الصلاحيات (المالك أو من لديه صلاحية إدارة الرسائل)
        if interaction.user.id == OWNER_ID or interaction.user.guild_permissions.manage_messages:
            # فتح النافذة لطلب الروابط
            await interaction.response.send_modal(PostModal(select.values[0]))
        else:
            await interaction.response.send_message("❌للإدارة فقط"، ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
    
    async def setup_hook(self):
        # تسجيل الواجهات كواجهات مستمرة لضمان عملها بعد إعادة تشغيل البوت
        self.add_view(PersistentDashboard())
        self.add_view(CloudDownloadView())
        await self.tree.sync()
        if not self.auto_refresh_task.is_running(): self.auto_refresh_task.start()

    async def on_member_join(self, member):
        channel = self.get_channel(WELCOME_ROOM_ID)
        if channel:
            welcome_text = f"_'Have fun in **__PhoenixRising__**_\n     _'User: {member.mention}_<a:Via1:1378238620418183188>"
            try:
                background = Editor("welcome.png")
                av_bytes = await download_image(str(member.display_avatar.url))
                if av_bytes:
                    avatar = Editor(Image.open(io.BytesIO(av_bytes))).resize((170, 170)).circle_image()
                    background.paste(avatar, (52, 72)) 
                file = discord.File(fp=background.image_bytes, filename="welcome_card.png")
                await channel.send(content=welcome_text, file=file)
            except: await channel.send(content=welcome_text)

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
                await guild.create_voice_channel(name=f"Members {total}", category=category)
                await guild.create_voice_channel(name=f"Online {online}", category=category)

bot = MyBot()

# أمر /setav لإنشاء لوحة التحكم الثابتة
@bot.tree.command(name="setav", description="إنشاء لوحة تحكم الأرشيف الثابتة")
async def setav(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌الأمر للمالك فقط"، ephemeral=True)
    
    embed = discord.Embed(
        title="Phoenix Rising | نظام الأرشفة", 
        description="مرحباً بك في لوحة التحكم بالأرشيف\nاختر القسم الذي تريد رفع الصور إليه من القائمة أدناه",
        color=0x2b2d31
    )
    
    # استخدام صورة السيرفر كصورة رئيسية للوحة
    if interaction.guild.icon:
        embed.set_image(url=interaction.guild.icon.url)
    
    await interaction.channel.send(embed=embed, view=PersistentDashboard())
    await interaction.response.send_message("✅تم إنشاء لوحة التحكم بنجاح"، ephemeral=True)

@bot.tree.command(name="مسح")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, العدد: int):
    await interaction.channel.purge(limit=العدد)
    await interaction.response.send_message(f"تم مسح {العدد}"، ephemeral=True)

@bot.tree.command(name="قفل_القناة")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("قُفلت القناة")

@bot.tree.command(name="فتح_القناة")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("فُتحت القناة")

@bot.tree.command(name="الحالة")
async def status(interaction: discord.Interaction, النص: str):
    if interaction.user.id == OWNER_ID:
        await bot.change_presence(activity=discord.Game(name=النص))
        await interaction.response.send_message("تحدثت الحالة"، ephemeral=True)

if __name__ == '__main__':
    keep_alive()
    token = os.getenv('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("❌ Error: DISCORD_TOKEN is missing!")
