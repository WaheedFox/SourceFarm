# تدقيق الواقع الحالي — SourceFarm / Hozan / Titan / CUPS

**تاريخ اللقطة:** 7 نوفمبر 2026. **النطاق:** المرحلة صفر فقط؛ قراءة المستودعات العامة وفحص المصدر والاختبارات والبيانات الوصفية، من دون تعديل أي مستودع أو نشر أو Commit/Push.  
**مقياس الأدلة:** `VERIFIED` حقيقة مثبتة مباشرة؛ `OBSERVED` شيء شوهد مع سياق ناقص؛ `INFERRED` استنتاج غير مكتمل؛ `RECOMMENDED` اقتراح غير معتمد؛ `NOT VERIFIED` تعذّر التحقق منه.

## الخلاصة التنفيذية

المستودع العام `SourceFarm` لا يحتوي حالياً منصة SourceFarm الموصوفة. المحتوى حزمة Python اسمها وتطبيقها `hozan`: تشغيل بوت Titan واحد، معالج `/start`، خدمة هوية أولية ومستودع ذاكرة داخل العملية. لم أجد واجهة Frontend أو Mini App أو Store أو محرر تدفقات أو Templates أو Action Registry أو تخزيناً دائماً أو منظومة استضافة لبوتات المستخدمين.

`Titan` هو المكوّن الأكثر اكتمالاً: إطار Telegram مستقل، مع polling وdispatch وrouters وmiddleware وأدوات تشغيل ومراقبة واختبارات واسعة. لكنه ليس محرك إنشاء No-Code، ولا يكفي وجوده لإثبات تغطية Actions/Triggers داخل SourceFarm.

`CUPS` مستقل لإدارة الحسابات والمشاريع والاشتراكات وEntitlements وquotas؛ لديه خدمة SQLite وواجهة FastAPI وبوت إداري مبني على Titan. لا يوجد اعتماد أو تكامل فعلي بين SourceFarm/Hozan وCUPS، ولا اعتماد CUPS من Titan في الشيفرة الحالية. بعض وثائق CUPS تصف امتداداً مستقبلياً باسم `titan-extension-cups`، لكنه غير موجود في المستودعين المفحوصين.

## لقطة المستودعات العامة

| المستودع | الفرع / Commit | تاريخ Commit (UTC) | ملفات Git المتتبعة | ملفات Python / أسطر Python تقريبية | ملاحظة |
|---|---|---|---:|---:|---|
| [SourceFarm](https://github.com/WaheedFox/SourceFarm/tree/2187dfd29f8b1ce9fc45ba53acc61b091898cb44) | `master` / `2187dfd` | 2026-08-23 | 44 | 37 / 402 | المحتوى حزمة `hozan`، لا واجهة SourceFarm |
| [Titan](https://github.com/WaheedFox/Titan/tree/b00b43ecee5c3b7d6cc06467b07c4418d467521b) | `master` / `b00b43e` | 2026-11-05 | 212 | 115 / 20,466 | إطار Python؛ لا Tags في Snapshot |
| [CUPS](https://github.com/WaheedFox/CUPS/tree/565650cd55c0d92bdae2f99fe44b48f51a63c527) | `master` / `565650c` | 2026-08-25 | 67 | 41 / 3,663 | منصة Alpha مستقلة؛ Tag `phase-2-referral-baseline` |

الأعداد تقريبية ومحسوبة من ملفات Python المتتبعة، وتشمل المصدر والاختبارات والأمثلة.

## SourceFarm / Hozan: ما يوجد فعلياً

### الوحدات ونقاط الدخول

- `src/hozan/core/app/application.py`: يركّب `TelegramApplication` و`Lifecycle` و`MemoryAccountRepository` و`HozanIdentityService`، ثم يضم Router البداية.
- `src/hozan/platform/telegram/application.py`: ينشئ `Titan(token)`، يضم Routers، ويشغّل Titan. لا يوفّر Webhook أو إدارة بوتات متعددة.
- `src/hozan/features/identity/`: نماذج `Account` و`HozanIdentity`، Protocol للـ repository، تنفيذ ذاكرة، وخدمة لتوليد Hozan ID.
- `src/hozan/features/registration/start.py`: معالج واحد هو `/start`، ينشئ الحساب والهوية المجانية ويرد برسالة ترحيب.
- `src/hozan/features/registry.py`: Registry للـ features لكنه غير مستخدم في composition الحالي.
- `src/hozan/runtime/{events,scheduler,state,tasks}` و`contexts/*` و`policies` و`middlewares`: ملفات `__init__.py` فارغة؛ لا تمثل Runtime أو Context مكتملين.
- `migrations/` و`locales/` لا يحتويان إلا `.gitkeep`.

**VERIFIED:** اسم الحزمة في `pyproject.toml` هو `hozan`، إصدارها `0.1.0`، وREADME المتتبع الوحيد `README.md` يصف Hozan وصفاً مختصراً.

### حالة الوظائف المطلوبة

| المجال | ما يثبت وجوده | الحالة الحالية |
|---|---|---|
| حساب Hozan وهوية `#NNNNNNNN` | خدمة هوية، تنفيذ ذاكرة، واختبارات أساسية | يعمل داخل العملية فقط؛ البيانات تضيع عند إعادة التشغيل |
| أوامر Hozan/SourceFarm | Router لمعالج `/start` فقط | بقية الأوامر المطلوبة غير موصولة |
| `/assets` و`/settings` | مذكوران في نص رد `/start` | لا يوجد لهما معالج |
| `/search`, `/roles`, `/help`, `/donate`, `/inspect`, `/logs`, `/env`, `/scale` | لم يظهر تسجيل/معالج في `src/hozan` | غير منفذة في التطبيق الحالي |
| Templates / versions / Store / purchases | لا وحدات أو واجهة أو قاعدة بيانات | غير منفذة |
| No-Code Builder / Triggers / Actions / Logic / Workflows | لا Action Registry أو محرر أو محرك تدفقات | غير منفذة |
| Hozan managed services / catalog / activation | لا كتالوج أو تفعيل مجموعة/قناة أو دورة حياة خدمة | غير منفذة |
| تشغيل بوتات المستخدمين | متغير تشغيل واحد `HOZAN_TOKEN` | لا سجل بوتات مستخدمين أو عزل تشغيل |
| قاعدة بيانات / migrations | لا توجد؛ repository في الذاكرة | غير منفذة |
| Frontend / Mini App | لا ملفات Frontend/JS/TS/HTML في الملفات المتتبعة | غير موجودة في Snapshot |
| deployment / monitoring / backups | لا إعدادات تشغيل أو نشر متتبعة | لم أجد تنفيذاً أو دليلاً قابلاً للتحقق |

### الأوامر وقائمة BotFather

أتعامل مع إفادة المستخدم بأن أوامر BotFather مسجلة مسبقاً كمدخل موثوق؛ لم أستخدم بيانات بوت حقيقية لفحصها عبر Telegram. في مصدر Hozan الحالي، `/start` وحده معالج. لا يستدعي التطبيق `setMyCommands` أو `deleteMyCommands` عند التشغيل.

يوفر Titan دوالاً اختيارية `set_my_commands`, `delete_my_commands`, `get_my_commands` في `src/titan/adapter.py`، لكن وجودها لا يعني أن Hozan يستعملها. بالمقابل، يحجز Titan `/link` تلقائياً لـ Message Links، ويحجز `/mydata` و`/forgetme` لميزة الخصوصية. لذلك `/link` المسجل لدى المستخدم بوصفه «مشاركة رابط المنتج» سيُوجّه حالياً إلى سلوك Titan الداخلي؛ وتسجيل معالج Hozan مستقل بهذا الاسم يرفضه Titan بسبب التعارض. كما توجّه رسالة `/start` المستخدم إلى `/assets` و`/settings` من دون handlers.

## Titan Framework

**التقنيات:** Python `>=3.10`، التوزيعة `titan-framework==1.0.0b1`، اعتماد تشغيل `aiohttp>=3.9`، وlong polling عبر `getUpdates`. تشمل البنية Telegram transport وUpdate translator وContext وRouter وmiddleware/error handling وpolling lifecycle ونماذج مبسطة وprivacy/data registry وhealth/inspection وlint وplayground/profiler وMessage Links.

**حدود Telegram:** `Telegram.request(method, data)` يرسل JSON إلى Bot API ويقبل اسم طريقة عامّاً، لكنه مسار خام بلا schema validation. وجدت 26 convenience/adaptor wrappers لطرق Bot API محددة؛ معاملاتها subset وليست كامل API. Titan يملك أيضاً helper داخلياً للرسائل الغنية، لكنه ليس method رسمياً مستقلاً في Bot API. كما أن JSON-only transport لا يرفع `InputFile` المحلي بصيغة `multipart/form-data`. مطوّر Python يستطيع استعمال API خاماً؛ مستخدم SourceFarm لا يملك حالياً Builder/Action Registry يستخدمه. راجع `TELEGRAM_API_COVERAGE.md`.

**Updates:** يحتفظ Titan بالـ raw Update، لكن يترجم حقولاً قليلة. Polling يستخدم `update_id`; routing يعالج `message`, `channel_post`, `callback_query`، وaliases `new_member` و`left_member` المشتقة من الرسائل. الأنواع الأخرى تُسجل debug ثم تُسقط في dispatch. لا توجد طبقة Webhook في الشجرة.

## CUPS

**الوظيفة الفعلية:** خدمة Python تفصل `Account`, `Project`, `Subscription`, `Entitlement`, `Quota`, `Reservation`, `Consumption`، وبيانات referral/commission. محرك `EntitlementEngine` يحول حالة الاشتراك إلى entitlements، والتخزين SQLite. FastAPI يوفر `/entitlements/check` ومسارات quota/reserve/consume تحت `/v1/runtime/resources/...` و`/health`. بوت CUPS يوفر `/start`, `/addbot`, `/cancel`, `/plan`؛ اختيار `/addbot` الحالي محصور بـ `titan-framework`.

**غير موجود:** مزود دفع أو معالجة Telegram Stars أو اشتراك تجاري حقيقي؛ توجد `simulate_paid_payment`, `simulate_refund` و`set_subscription_for_test` للمحاكاة/الاختبار. لا توجد منتجات SourceFarm/Hozan في Catalog ولا دليل على نشر CUPS.

## الأمن والموثوقية: ما فُحص وما لم يُثبت

1. **CUPS Runtime API — OBSERVED، شدة عالية إذا كان مكشوفاً خارجياً:** نماذج HTTP تستقبل `account_id` و`project_id` من جسم الطلب؛ فحص الملكية يقارن `project.owner_id` مع `req.account_id` المرسل نفسه. لم أجد مصادقة أو API-key dependency أو هوية مشتقة من قناة موثوقة في تطبيق FastAPI. اختبارات TestClient تستدعي endpoint صالحاً بلا ترويسة مصادقة وتستعيد 200. هذا يثبت سلوك التطبيق في الاختبار فقط؛ لا توجد إعدادات نشر/حدود شبكة تثبت الوصول الخارجي. مسارات quota/reserve/consume لا تظهر مصادقة تطبيقية كذلك.
2. **CUPS contract غير مكتمل:** وثائق CUPS تعرض مثال `CUPSGuard(api_key=...)`، لكن `apps/titan_framework/cups_client.py` لا يقبل API key ولا يرسله، وRuntime API لا يعرف هذا الحقل. لا تعامل UUID المشروع وحده كاعتماد مصادقة.
3. **البيانات الدائمة:** SourceFarm/Hozan يستخدم ذاكرة فقط. CUPS ينشئ `cups.db` في مسار نسبي ويهيئ schema عند إنشاء `SQLiteStore`; لا توجد migrations أو إدارة نسخ احتياطي ضمن كود التشغيل.
4. **إدخال HTML:** بوت CUPS يضم اسم المشروع الذي يقدمه المستخدم مباشرة في رسالة `parse_mode="HTML"` في `apps/cups-bot/handlers/addbot.py`. قد يفسد ذلك تنسيق الرسالة أو ينتج كيانات غير صحيحة؛ يلزم escaping/تحقق لاحقاً. لم أختبر مدخلات خاصة.
5. **التواريخ:** اختبارات CUPS نجحت مع 299 تحذيراً، معظمها من `datetime.utcnow()` المتقادم في Python 3.13، إضافة إلى تحذير Starlette حول `HTTP_422_UNPROCESSABLE_ENTITY`.
6. لم يعثر فحص نصي للملفات المتتبعة على نمط Telegram token شائع أو ترويسة private-key. هذا لا يغطي أسرار بيئة النشر. لم تُطبع أو تُنسخ قيم سرية.

## النتائج المهمة

### F-SF-01 — منتج SourceFarm غير موجود كتطبيق في Snapshot

- **الحالة/الشدة:** VERIFIED / عالية.
- **الموقع:** `SourceFarm/src/hozan/`, `pyproject.toml:5-40`, `README.md:1-7`.
- **الدليل:** جميع ملفات التطبيق المتتبعة Python؛ لا ملفات UI أو Mini App أو Store أو Builder أو action/trigger engine أو تكاملات.
- **السلوك الفعلي:** تطبيق Hozan واحد يبدأ بمعالج `/start` وهوية ذاكرية.
- **الأثر:** لا توجد قاعدة تنفيذية تحقق وعد SourceFarm أو واجهة الصورة المرجعية.
- **التوصية الأولية:** اعتمد حدود المستودع/المنتج وموضع Hozan قبل تصميم انتقال تدريجي؛ لا يعني ذلك اعتماد monorepo مستقبلي الآن.
- **التحقق:** جرد 44 ملفاً وفحص `src/`, `tests/`, `pyproject.toml`.

### F-SF-02 — الهوية تفقد بياناتها عند إعادة تشغيل العملية

- **الحالة/الشدة:** VERIFIED / متوسطة.
- **الموقع:** `src/hozan/features/identity/memory.py:6-37`, `service.py:13-49`, `core/app/application.py:12-19`.
- **الدليل:** الحسابات والهويات قاموسان بالذاكرة؛ التطبيق ينشئ repository جديداً عند composition.
- **السلوك الفعلي:** البيانات تبقى طوال عمر العملية فقط. الاختبارات تثبت الإنشاء وإعادة الطلب تسلسلياً، لا الاستمرارية أو التزامن.
- **الأثر:** إعادة تشغيل تفقد الحسابات والهويات، فلا تصلح قاعدة لبناء الأصول والصلاحيات والإصدارات.
- **التوصية الأولية:** تخزين دائم وقيود uniqueness ومعالجة تزامن قبل بناء المنتج فوق الهوية.
- **التحقق:** فحص التنفيذ والاختبارات، بلا محاكاة نشر.

### F-SF-03 — تعارض `/link` مع Titan

- **الحالة/الشدة:** VERIFIED / متوسطة.
- **الموقع:** `Titan/src/titan/bot.py:315-337,381-401,477-503`; `SourceFarm/src/hozan/features/registration/start.py:11-27`.
- **الدليل:** Titan يحجز `/link` لميزة Message Links ويرفض تسجيل handler آخر؛ دلالته المقصودة في قائمة المستخدم هي مشاركة رابط المنتج. `/assets` و`/settings` المذكوران في الترحيب بلا معالج.
- **السلوك الفعلي:** `/link` يذهب إلى Titan، وبقية الأوامر غير موصولة.
- **الأثر:** اختلاف بين وصف BotFather وسلوك الأمر واحتمال تعارض عند تنفيذ handler المطلوب.
- **التوصية الأولية:** حسم عقد الأمر دون تغيير قائمة BotFather التي أفاد المستخدم أنها مسجلة.
- **التحقق:** تتبع التسجيل المحجوز وpreflight include والبحث في Routers.

### F-SF-04 — مسارات الحزم والتغليف غير متوافقة

- **الحالة/الشدة:** OBSERVED / عالية لقابلية التثبيت.
- **الموقع:** `SourceFarm/pyproject.toml:5-40`, `Titan/pyproject.toml:5-43`, `Titan/README.en.md:20`.
- **الدليل:** SourceFarm يطلب Titan من PyPI ويشير إلى README غير موجود؛ PyPI API أعاد 404؛ Titan README يوصي بـ Git install.
- **السلوك الفعلي:** الاختبارات نجحت بعد إضافة مصدر Titan المحلي إلى `PYTHONPATH`.
- **الأثر:** التثبيت وفق manifest لم يُثبت، كما أن بناء الحزمة لم يُتحقق منه.
- **التوصية الأولية:** اعتمد مصدر تثبيت/إصدار موثق قبل التنفيذ؛ لا تغيّر dependencies خلال هذا التدقيق.
- **التحقق:** فحص metadata والمصدر العام؛ لم يُشغّل `python -m build`.

### F-TI-01 — transport عام دون تغطية Actions typed شاملة

- **الحالة/الشدة:** VERIFIED / عالية لمتطلب المحرك، لا تعني خللاً في Titan كإطار.
- **الموقع:** `Titan/src/titan/telegram.py:29-89`, `adapter.py:19-298`, `update.py:20-110`, `bot.py:656-739`.
- **الدليل:** generic JSON request وعدد محدود من wrappers؛ dispatch يسقط الأنواع غير المدعومة.
- **السلوك الفعلي:** مطوّر Python يستطيع استدعاء API خاماً؛ مستخدم SourceFarm لا يستطيع إنشاء Action أو Trigger من ذلك، إذ لا يوجد Builder/registry.
- **الأثر:** وجود Titan لا يثبت تغطية Bot API داخل SourceFarm.
- **التوصية الأولية:** قِس التغطية عبر Registry وschemas واختبارات؛ احتفظ بـ Titan كبنية تشغيل ما لم يظهر قيد تقني آخر.
- **التحقق:** فحص Telegram transport والنماذج والrouting والاختبارات؛ راجع مصفوفة API.

### F-CUPS-01 — هوية Runtime API غير موثقة على مستوى التطبيق

- **الحالة/الشدة:** OBSERVED / عالية إذا كان API مكشوفاً لشبكة غير موثوقة؛ التعرض الفعلي NOT VERIFIED.
- **الموقع:** `CUPS/src/cups/api/runtime.py:37-45,103-146,171-226`; `tests/api/test_runtime.py:55-65,148-155`.
- **الدليل:** الجسم يحمل `account_id`; اختبارات TestClient تعمل بلا مصادقة HTTP؛ المقارنة تساوي owner id مع القيمة المرسلة.
- **السلوك الفعلي:** التطبيق لا يثبت أن caller مالك الحساب. إعداد reverse proxy أو حدود الشبكة غير موجود في المستودع.
- **الأثر:** مقارنة بمعرّف يختاره العميل لا تكفي لحماية endpoint عند كشفه، خصوصاً مسارات reservations/consumptions.
- **التوصية الأولية:** قبل التكامل، عرّف credential لكل مشروع أو هوية خدمة واربطها من جهة موثوقة، وأضف authorization/rate limits وسجلاً تدقيقياً. لا تنشر API مكشوفاً قبل ذلك.
- **التحقق:** مراجعة request models/routes واختبارات TestClient؛ لم يُفحص URL منشور.

### F-CUPS-02 — امتداد Titan/CUPS الموصوف غير موجود كتجميع فعلي

- **الحالة/الشدة:** VERIFIED / متوسطة.
- **الموقع:** `CUPS/pyproject.toml:28-44`, `CUPS/apps/titan_framework/cups_client.py:6-33`, `Titan/pyproject.toml:31-43`.
- **الدليل:** CUPS core لا يعتمد Titan؛ extra بوت CUPS يعتمد Titan من Git. العميل موجود داخل CUPS ولا يستورده Titan؛ لا يوجد `titan-extension-cups` في شجرة Titan.
- **السلوك الفعلي:** الاتجاه المثبت هو CUPS Bot → Titan، لا Titan Core → CUPS؛ العميل نموذج أولي داخل CUPS.
- **الأثر:** وصف وثائق CUPS لا يثبت أن Titan أو SourceFarm يستهلك Entitlements حالياً.
- **التوصية الأولية:** أبقِ CUPS مستقلاً حتى اعتماد عقد وهوية ومصادقة وتدفق بيانات.
- **التحقق:** جرد imports/dependencies والبحث عن `cups` في مصدر Titan.

### F-CUPS-03 — المدفوعات محاكاة وليست Billing فعلياً

- **الحالة/الشدة:** VERIFIED / متوسطة.
- **الموقع:** `CUPS/src/cups/service.py:261-277,326-383`, `CUPS/src/cups/domain/referral.py`.
- **الدليل:** تغيير الاشتراك موسوم test-only؛ عمليات الدفع/refund محاكاة؛ لا provider أو Telegram Stars handler في التطبيقات.
- **السلوك الفعلي:** يمكن حساب Entitlements واختبار الدفع التمثيلي، لكن لا توجد معالجة أموال حقيقية.
- **الأثر:** لا ينبغي اعتبار CUPS جاهزاً للتحصيل أو اشتراكات تجارية.
- **التوصية الأولية:** لا تفعّل خططاً مدفوعة قبل بناء ومراجعة دورة دفع حقيقية.
- **التحقق:** تتبع service والhandlers والdependencies؛ لا يوجد payment provider call.

## تقييم المكونات

| المكوّن | التصنيف الأولي | السبب |
|---|---|---|
| Hozan identity foundation | `MODERNIZE` | فصل خدمة/Repository مفيد، لكن التنفيذ ذاكرة ونطاقه ضيق |
| Titan framework | `KEEP` ثم `INVESTIGATE` عند ربط المحرك | إطار مستقل واختبارات قوية؛ التغطية typed ليست Bot API كاملة |
| CUPS core | `KEEP` مستقلاً، `INVESTIGATE` المصادقة والتكامل | نطاق Entitlements مستقل، مع فجوة مصادقة محتملة ومرحلة Alpha |
| Hozan/Titan boundary | `KEEP` كحد مبدئي | التطبيق يفصل Telegram adapter؛ لا حاجة ظاهرة لدبلجة polling |
| SourceFarm UI/Store/Builder | `INVESTIGATE` ثم تصميم بعد الموافقة | لا يوجد تنفيذ حالي يمكن ترقيعه أو مقارنة صفحات به |

## الصورة المرجعية

الصورة المرفقة لوحة هوية وشعارات، لا لقطة لشاشة Mini App. الظاهر: خلفية شبه سوداء، أبيض وأخضر بكسلي، حروف pixel/monospaced، حدود رمادية رفيعة وزوايا مستديرة، مع إشارات صغيرة سماوية/بنفسجية/صفراء. لا يمكن تقييم التنقل أو صفحات الواجهة الحالية بصرياً لأن الواجهة غير موجودة في Snapshot. استخدم اللوحة مرجعاً للهوية لاحقاً، لا كواجهة مكتملة.

## ترتيب أولي للمراحل اللاحقة — غير معتمد

1. تثبيت حدود المستودعات وهوية الحزم وموضع كود Hozan، ثم حسم قابلية تثبيت الاعتماديات.
2. إنشاء أساس بيانات/هوية مستمر وعقد صلاحيات/مصادقة قبل ربط APIs أو Bot Tokens.
3. اعتماد عقد محرك Telegram: Registry وtyped schemas وتحديثات/Actions/permissions واختبارات.
4. تصميم وفصل تجربتي SourceFarm وHozan، ثم Mini App وTemplates وStore وفق الصورة بعد الموافقة.
5. دراسة CUPS كتقديم مستقل للاشتراكات؛ لا دمج قبل إغلاق مصادقة API وتحديد ملكية البيانات.
6. الاستضافة والمراقبة والنسخ الاحتياطي والعزل قبل تشغيل بوتات مستخدمين.

هذا مقترح أولي وليس Architecture نهائية.

## قرارات تحتاج موافقة قبل المرحلة الأولى

- هل يبقى مستودع Hozan منفصلاً أم ضمن SourceFarm؟ لا يوجد مستودع Hozan عام مستقل أمكن فحصه.
- ما اسم الحزمة/المنتج المعتمد للمستودع الذي يحمل `src/hozan`؟
- هل يُدرس CUPS مستقبلاً كطبقة اشتراك مستقلة؟ لا يوجد تكامل حالياً.
- كيف تُحل دلالة `/link` مع أمر Titan المحجوز دون تغيير قائمة BotFather؟
- ما مصدر تثبيت Titan المعتمد؟
- هل تُقبل إضافة تخزين دائم ومصادقة API في المراحل التالية؟

## سجل التحقق والقيود

- فُحصت رؤوس Git العامة والفروع والـ commits والملفات المتتبعة للمستودعات الثلاثة؛ clones المحلية نظيفة. هذا لا يكشف تغييرات محلية غير مرفوعة؛ لم يكن هناك Replit Project متصل لفحصه.
- فُحص المصدر والاختبارات والmanifests وCI والوثائق ذات الصلة؛ لم يُعدّل أي ملف في SourceFarm أو Titan أو CUPS، ولم يجر Commit أو Push.
- بيئة الاختبار: Python `3.13.11`، pytest `9.2.0`، pytest-asyncio `1.4.1.post1`، aiohttp `3.14.5`، FastAPI `0.162.0`، httpx `0.28.1`.
- SourceFarm: `5 passed`; أضيف `Titan/src` محلياً إلى `PYTHONPATH`، لذا لا يثبت ذلك تثبيت PyPI.
- Titan: `992 passed`; لا اتصال ببوت Telegram أو حساب إنتاجي.
- CUPS: `73 passed, 299 warnings`; أبرزها DeprecationWarning لـ `datetime.utcnow()` وتحذير Starlette للثابت `HTTP_422_UNPROCESSABLE_ENTITY`.
- أحدث تشغيل Actions ظاهر لـ Titan على `b00b43e` ناجح، ولـ CUPS على `565650c` ناجح. لم يوجد تشغيل SourceFarm في API (`total_count=0`). لا يثبت هذا إعداد نشر/إنتاج.
- فُحص مرجع Bot API الرسمي بإصدار `10.3` (آخر تحديث ظاهر 24 أغسطس 2026) بتاريخ 7 نوفمبر 2026. لم تُستخدم أسرار أو بيانات Telegram حقيقية.
- غير متحقق: مصادقة/حدود شبكة CUPS عند النشر، إعداد تشغيل خارج Git، الحالة المحلية غير المرفوعة، تأكيد BotFather عبر Telegram، أو مستودع Hozan مستقل.

## المصادر

- [SourceFarm pyproject.toml](https://github.com/WaheedFox/SourceFarm/blob/2187dfd29f8b1ce9fc45ba53acc61b091898cb44/pyproject.toml)
- [Hozan application](https://github.com/WaheedFox/SourceFarm/blob/2187dfd29f8b1ce9fc45ba53acc61b091898cb44/src/hozan/core/app/application.py)
- [Hozan identity repository](https://github.com/WaheedFox/SourceFarm/blob/2187dfd29f8b1ce9fc45ba53acc61b091898cb44/src/hozan/features/identity/memory.py)
- [Titan Telegram transport](https://github.com/WaheedFox/Titan/blob/b00b43ecee5c3b7d6cc06467b07c4418d467521b/src/titan/telegram.py)
- [Titan dispatch](https://github.com/WaheedFox/Titan/blob/b00b43ecee5c3b7d6cc06467b07c4418d467521b/src/titan/bot.py)
- [CUPS Runtime API](https://github.com/WaheedFox/CUPS/blob/565650cd55c0d92bdae2f99fe44b48f51a63c527/src/cups/api/runtime.py)
- [CUPS service](https://github.com/WaheedFox/CUPS/blob/565650cd55c0d92bdae2f99fe44b48f51a63c527/src/cups/service.py)
- [Telegram Bot API](https://core.telegram.org/bots/api)
