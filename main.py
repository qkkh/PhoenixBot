import asyncio, os, re, discord, requests
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread

# --- نظام الاستضافة للبقاء حياً 24 ساعة ---
app = Flask('')
@app.route('/')
def home(): return "Phoenix Panel is Active"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- إعداداتك الخاصة ---
OWNER_ID = 1341796578742243338 # حسابك أنت فقط [cite: 2026-03-24]
PHOENIX_COLOR = 0x00aaff # اللون الأزرق الملكي

# --- إعدادات قنوات الإحصائيات (ضع الـ ID هنا) ---
STATS_CHANNEL_ID = 123456789012345678 # استبدل هذا الرقم بـ ID القناة الصوتية [cite: 2026-03-24]

# --- واجهات التفاعل (نوافذ إدخال البيانات) ---

class YTPostModal(discord.ui.Modal, title='نشر فيديو يوتيوب 🎬'):
    link = discord.ui.TextInput(label="رابط الفيديو", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            r = requests.get(self.link.value).text
            ch_name = re.search(r'"author":"(.*?)"', r).group(1)
            clean_name = re.sub(r'[^\w\s]', '', ch_name) # بدون علامات ترقيم [cite: 2026-03-24]
        except: clean_name = "قناتنا"
        
        channel = interaction.guild.get_channel(924316521050820609) # روم اليوتيوب
        if channel:
            msg = f"انتباه يا أبطال الفينيق المبدع {clean_name} نزل مقطع جديد ورهيب شاهدوا المقطع الآن" [cite: 2026-03-24]
            await channel.send(content=f"@everyone\n{msg}\n{self.link.value}")
            await interaction.followup.send("✅ تم النشر بنجاح يا زعيم", ephemeral=True)

class AnnounceModal(discord.ui.Modal, title='إرسال إعلان عام 📢'):
    text = discord.ui.TextInput(label="محتوى الإعلان", style=discord.TextStyle.paragraph, required=True)
    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📢 تنبيه من Phoenix Rising", description=self.text.value, color=PHOENIX_COLOR)
        await interaction.channel.send(content="@everyone", embed=embed)
        await interaction.response.send_message("✅ تم إرسال الإعلان", ephemeral=True)

# --- لوحة التحكم (الأزرار فقط) ---

class PhoenixDashboard(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
    
    @discord.ui.button(label="نشر يوتيوب", style=discord.ButtonStyle.primary, emoji="🎥")
    async def yt_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID: return
        await interaction.response.send_modal(YTPostModal())

    @discord.ui.button(label="إرسال إعلان", style=discord.ButtonStyle.success, emoji="📢")
    async def ann_button(self, interaction: interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID: return
        await interaction.response.send_modal(AnnounceModal())

    @discord.ui.button(label="قفل الروم", style=discord.ButtonStyle.danger, emoji="🔒")
    async def lock_button(self, interaction: interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID: return
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
        await interaction.response.send_message("🔒 تم قفل الروم", ephemeral=True)

    @discord.ui.button(label="فتح الروم", style=discord.ButtonStyle.secondary, emoji="🔓")
    async def unlock_button(self, interaction: interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID: return
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
        await interaction.response.send_message("🔓 تم فتح الروم", ephemeral=True)

# --- البوت الأساسي ---

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
    
    async def on_ready(self):
        await self.tree.sync()
        self.update_stats.start() # تشغيل تحديث الأعضاء تلقائياً [cite: 2026-03-24]
        print(f"🔥 Phoenix Panel is Online")

    # مهمة تحديث اسم القناة الصوتية بعدد الأعضاء [cite: 2026-03-24]
    @tasks.loop(minutes=5)
    async def update_stats(self):
        channel = self.get_channel(STATS_CHANNEL_ID)
        if channel:
            await channel.edit(name=f"📊 الأعضاء: {channel.guild.member_count}")

bot = MyBot()

@bot.command(name="79")
async def panel(ctx):
    if ctx.author.id == OWNER_ID:
        emb = discord.Embed(
            title="🎮 مركز عمليات PHOENIX RISING", 
            description="مرحباً بك يا زعيم الفينيق هذه هي لوحة التحكم الخاصة بك والمشفرة لتستجيب لك أنت فقط", [cite: 2026-03-24]
            color=PHOENIX_COLOR
        )
        await ctx.send(embed=emb, view=PhoenixDashboard(bot))

if __name__ == '__main__':
    keep_alive()
    bot.run(os.getenv('DISCORD_TOKEN'))
