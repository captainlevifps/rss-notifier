# RSS -> Discord Notifier (مجاني 100%، شغال 24/7)

نظام واحد بيراقب 4 مصادر أخبار ويبعتهم لـ 4 قنوات مختلفة على Discord،
من غير bot token، من غير VPS، من غير أي فلوس — عن طريق **GitHub Actions + Discord Webhooks**.

## الفكرة باختصار

- كل 15 دقيقة، GitHub بيشغل `check_feeds.py` تلقائي (cron)، سواء لابتوبك مقفول أو لأ.
- السكريبت بيقارن كل feed بالأخبار اللي اتبعتت قبل كده (`seen.json`).
- أي خبر جديد بيتبعت مباشرة لقناة الـ Discord عن طريق **Webhook** (مش بوت حقيقي، أسهل وأثبت).

## الخطوات (مرة واحدة بس)

### 1) اعمل Webhook لكل قناة على Discord
لكل قناة (F1 / Marvel Rivals / Tech-AI / Jobs):
`Channel Settings -> Integrations -> Webhooks -> New Webhook -> Copy Webhook URL`

هيبقى معاك 4 لينكات (webhook URLs).

### 2) اعمل Repo على GitHub وارفع الملفات دي
لازم يكون فيه: `check_feeds.py`, `config.yaml`, `requirements.txt`, `.github/workflows/check-feeds.yml`

### 3) حط اللينكات كـ Secrets (مش في الكود!)
`Repo -> Settings -> Secrets and variables -> Actions -> New repository secret`

ضيف:
- `F1_WEBHOOK`
- `MARVEL_RIVALS_WEBHOOK`
- `TECH_AI_WEBHOOK`
- `JOBS_EGYPT_WEBHOOK`
- `JOBS_EGYPT_ALERT_URL` (اقرا خطوة 4)

### 4) مصدر أخبار الـ Jobs/Internships (Egypt)
LinkedIn معندهاش RSS رسمي، والـ scraping بتاعها بيخالف الشروط بتاعتهم وغير مضمون أصلاً.
البديل المجاني والمضمون: **Google Alerts** بيدّيك RSS فعلي مجاني:

1. روح [google.com/alerts](https://www.google.com/alerts)
2. دور على: `site:linkedin.com/jobs internship OR "entry level" Egypt`
3. من "Show options" اختار **Deliver to: RSS feed**
4. Google هيديك لينك RSS — ده اللي تحطه في `JOBS_EGYPT_ALERT_URL`

كده الفلتر بتاع `keywords` في `config.yaml` هيساعد يقلل الضوضاء.

### 5) الـ Mention قبل الرسالة
في `config.yaml`، غيّر قيمة `mention` لأي feed تحت اسمه:
- تاج رول: `<@&ROLE_ID>` (دوس على السيرفر Settings -> Roles، وفعّل Developer Mode من Discord عشان تقدر تعمل Copy Role ID)
- تاج شخص: `<@USER_ID>`
- الكل: `@everyone` (لازم الـ webhook تبعتها كـ mention مفعّل في السيرفر)

### 6) جرّبه يدوي أول مرة
`Actions tab -> Check RSS Feeds -> Run workflow`
أول تشغيل مش هيبعت رسايل (بيسجل الموجود بس كـ "متشاف")، من ثاني تشغيل هتبدأ توصلك الأخبار الجديدة فعلاً.

## شكل الرسالة (Discord Embed)
كل خبر بيتبعت كـ **Embed** فيه:
- اسم المصدر (`label`) فوق كـ author
- العنوان قابل للضغط ولينك مباشر
- سطرين وصف مختصر من الـ feed نفسه (لو موجود)
- شريط لون جانبي (`color`) مميز لكل مصدر
- صورة الخبر لو الموقع بعتها في الـ RSS
- الـ mention (لو مفعّل) بيتبعت كنص عادي فوق الـ embed عشان يعمل notification فعلي

عايز تغيّر شكل مصدر معين؟ عدّل `label` أو `color` بتاعه في `config.yaml` بس.

## تعديل/إضافة feed جديد
افتح `config.yaml` وضيف بلوك زي الموجودين، بس محتاج webhook جديد لكل قناة.

## حدود الخطة المجانية
- Public repo = دقايق تشغيل GitHub Actions مجانية بلا حد تقريبًا.
- Private repo = 2000 دقيقة/شهر مجانًا (كل تشغيلة بتاخد ~15-20 ثانية، وبكرون كل 5 دقايق = ~288 تشغيلة يوميًا، لسه مرتاح جدًا جوه الحد المجاني).
- Discord webhook rate limit: السكريبت بيستنى 1.5 ثانية بين كل رسالة عشان مايتحظرش.

## عايز أسرع من كده (real-time فعلي)؟
- GitHub Actions مش بيضمن التوقيت بالظبط مع `cron` — ممكن يتأخر شوية وقت الزحمة (خصوصًا أول كل ساعة). أقل حاجة عملية هي 5 دقايق زي ما هو مظبوط دلوقتي.
- كمان المصدر نفسه (الموقع/الـ subreddit) بياخد وقت لغاية ما الـ RSS بتاعه يتحدث، يعني مفيش "instant" 100% حتى لو أنت شيكت كل ثانية.
- لو محتاج فعلاً real-time (ثواني)، الحل بيبقى سيرفر شغال 24/7 (زي Oracle Cloud Free Tier) بيعمل `while True: check -> sleep(30s)` بدل الـ cron — ده لسه مجاني بس محتاج إعداد استضافة إضافي. قولّي لو عايز الكونفيج ده بدل GitHub Actions.
