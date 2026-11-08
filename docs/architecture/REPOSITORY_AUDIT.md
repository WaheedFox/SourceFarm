# تدقيق الواقع الحالي — SourceFarm / Hozan / Titan / CUPS

**تاريخ استكمال الوثائق:** 8 نوفمبر 2026. **تاريخ اللقطة العامة:** 7 نوفمبر 2026. **النطاق:** استكمال توثيق المرحلة صفر فقط؛ قراءة المستودعات العامة وفحص المصدر والاختبارات والبيانات الوصفية، من دون تعديل تطبيق أو اعتماديات أو قاعدة بيانات أو نشر أو Commit/Push.  
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

1. **مصادقة CUPS — OBSERVED:** لم أجد مصادقة أو API-key dependency على Runtime routes. نماذج الطلب تستقبل `account_id`; اختبار صالح يصل إلى 200 من دون ترويسة مصادقة. فحص الملكية يقارن `owner_id` مع ذلك الحقل المرسل. هذا يثبت تصميم الكود/الاختبار، لا التعرض الخارجي.
2. **أثر أمني مشروط — INFERRED:** إذا كان Runtime API متاحاً لشبكة غير موثوقة بلا حماية خارجية، فقد تسمح الهوية المرسلة في الطلب بعمليات entitlement/resource غير مصادق عليها. هذا استنتاج مشروط؛ لم أختبر endpoint عاماً أو أحاول تجاوز المصادقة.
3. **التعرض الخارجي — NOT VERIFIED:** لا توجد في المستودع إعدادات نشر/حدود شبكة أو URL إنتاجي يمكن فحصه؛ قد يكون API خلف شبكة داخلية أو proxy موثوق.
4. **العميل الموصوف في الوثائق غير مكتمل:** CUPS docs تعرض `CUPSGuard(api_key=...)`، لكن `apps/titan_framework/cups_client.py` لا يقبل ولا يرسل API key، وRuntime API لا يعرّف هذا الحقل. راجع سجل Finding المفصل.
5. **SQLite واختبارات CUPS:** مسارات quota/reservation/consumption التي راجعتها تستخدم SQL placeholders ومعاملات SQLite. لكن `runtime.py` ينشئ خدمة افتراضية عند import، واختبار API يستوردها قبل استبدالها بـ `:memory:` في fixture؛ لذلك يمكن أن يفتح/ينشئ `cups.db` عند جمع الاختبارات. لم أشغّل الاختبارات في جولة الاستكمال كي لا أكتب في قاعدة بيانات.
6. **مدخل HTML في CUPS Bot:** اسم المشروع يمر مباشرة إلى نص `parse_mode="HTML"`. الخطر المثبت هو احتمال تنسيق غير صالح أو فشل رسالة Telegram؛ لم أختبر مدخلات خاصة ولم أصفه كـ XSS.
7. **المدفوعات محاكاة:** `simulate_paid_payment`, `simulate_refund` و`set_subscription_for_test` لا تمثل مزود دفع حقيقياً أو Telegram Stars.
8. **SQL parameterization:** الاستعلامات التي راجعتها في quota/reservation/consumption تستخدم معاملات `?` و`BEGIN IMMEDIATE`؛ هذا مؤشر إيجابي محدود، وليس تدقيقاً أمنياً شاملاً لكل الاستعلامات.
9. فحص نصي سابق للملفات المتتبعة لم يعثر على نمط Telegram token شائع أو ترويسة private-key؛ لا يغطي أسرار بيئة النشر. لم تُطبع أو تُنسخ قيم سرية. لم تُجرَ اختبارات هجومية أو اتصالات إنتاجية.

## ملخص النتائج المهمة

الملاحظات التالية فهرس مختصر للقراءة السريعة؛ السجل الموحد أدناه هو المرجع الرسمي للنتائج، وفيه كل الحقول المطلوبة لكل Finding.
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

## سجل Findings الموحّد

تعني الحالات: `VERIFIED` دليل مباشر في المصدر/الاختبار؛ `OBSERVED` سلوك أو نمط شوهد لكن سياقه ناقص؛ `INFERRED` أثر مشروط مستنتج ولم يُختبر؛ `NOT VERIFIED` لم يتوفر الدليل اللازم. الشدة تصف الأثر المحتمل في نطاق اللقطة، ولا تثبت التعرض أو الحدوث.

### Finding F-SF-01 — تطبيق SourceFarm غير موجود في اللقطة العامة

- **ID:** `F-SF-01`
- **Title:** SourceFarm runtime not present in the public snapshot
- **Status:** `VERIFIED`
- **Severity:** High — فجوة وظيفية مقابل نطاق المنتج المطلوب
- **Location:** مستودع SourceFarm العام، `master` عند `2187dfd29f8b1ce9fc45ba53acc61b091898cb44`
- **File:** `src/hozan/core/app/application.py`; `src/hozan/features/registration/start.py`; جرد ملفات Git
- **Symbol:** `Hozan.__init__`; `build_router`; tracked-file inventory
- **Line Range:** `application.py:9-20`; `start.py:8-29`; الجرد: لا ينطبق
- **Evidence:** composition يركّب `MemoryAccountRepository` وخدمة الهوية وRouter البداية؛ ملفات التطبيق المتتبعة وعددها 44 لا تتضمن واجهة أو Mini App أو Store أو Builder أو workflow/action registry.
- **Actual Behavior:** اللقطة العامة تشغّل تطبيق Hozan واحداً ومعالج `/start` فقط، ولا تنفذ بناء بوتات المستخدمين.
- **Expected Behavior:** وفق نطاق SourceFarm الذي طُلب تدقيقه، وجود تجربة بناء ونشر وإدارة لبوتات المستخدمين. هذا وصف للمتطلب لا قرار معماري.
- **Impact:** لا يمكن اعتبار هذا المستودع وحده تطبيق SourceFarm الموصوف أو الاستناد إليه كتنفيذ واجهة الصورة.
- **Recommendation:** إبقاء الفجوة موثقة وعدم بدء تنفيذ المرحلة الأولى قبل مراجعة المستخدم.
- **Verification Method:** جرد `git ls-files` في اللقطة العامة وقراءة composition وRouter والاختبارات.
- **Verification Result:** وجود scaffold Hozan مؤكد في اللقطة العامة؛ لا يستنتج ذلك غياب تغييرات محلية غير مرفوعة (راجع `F-SCOPE-01`).

### Finding F-SF-02 — تخزين الهوية في الذاكرة

- **ID:** `F-SF-02`
- **Title:** Hozan identity is process-local
- **Status:** `VERIFIED`
- **Severity:** Medium
- **Location:** مستودع SourceFarm العام عند commit المذكور أعلاه
- **File:** `src/hozan/features/identity/memory.py`; `src/hozan/features/identity/service.py`; `src/hozan/core/app/application.py`; `tests/test_identity.py`
- **Symbol:** `MemoryAccountRepository`; `HozanIdentityService`; `Hozan.__init__`
- **Line Range:** `memory.py:6-36`; `service.py:9-49`; `application.py:9-20`; `test_identity.py:8-26`
- **Evidence:** الحسابات والهويات تحفظ في قاموسين داخل repository؛ التطبيق ينشئ ذلك repository في composition. الاختبارات تغطي الإنشاء وإعادة الطلب، لا الاستمرارية بعد إعادة التشغيل.
- **Actual Behavior:** بيانات الهوية مرتبطة بعمر العملية الحالية.
- **Expected Behavior:** إذا كانت الهوية مطلوبة للاستمرار بين مرات التشغيل، فيلزم عقد تخزين دائم قبل الاعتماد عليها لهذا الغرض.
- **Impact:** إعادة تشغيل العملية تفقد الحسابات والهويات الموجودة في هذا التنفيذ.
- **Recommendation:** تسجيل الاستمرارية كمتطلب غير محقق، من دون اختيار قاعدة بيانات أو بنية نهائية هنا.
- **Verification Method:** مراجعة repository وcomposition واختبارات الهوية.
- **Verification Result:** التنفيذ الذاكري مؤكد؛ لم تُختبر بيئة نشر أو استمرارية خارج الاختبارات.

### Finding F-SF-03 — تعارض `/link` مع Titan وعدم وجود معالجات لبعض الأوامر

- **ID:** `F-SF-03`
- **Title:** Reserved Titan command conflicts with the advertised product command
- **Status:** `VERIFIED`
- **Severity:** Medium
- **Location:** SourceFarm وTitan العامان عند commits الموثقة في جدول اللقطات
- **File:** `Titan/src/titan/bot.py`; `SourceFarm/src/hozan/features/registration/start.py`
- **Symbol:** `_register_link_command`; `Router.command`; `_handle_update`; `build_router`
- **Line Range:** `bot.py:315-337,381-401,656-739`; `start.py:8-29`
- **Evidence:** Titan يسجل `/link` كأمر داخلي ويرفض تعارض التسجيل؛ رسالة `/start` تسرد `/assets` و`/settings` ولا تظهر لهما handlers في Router الحالي.
- **Actual Behavior:** `/link` يذهب إلى سلوك Titan الداخلي؛ الرسالة تعرض أوامر لا يربطها التطبيق الحالي بمعالجات.
- **Expected Behavior:** يتطابق سلوك الأوامر مع القائمة التي أفاد المستخدم بأنها مسجلة في BotFather، من دون إعادة ضبطها أو تغييرها في هذا التدقيق.
- **Impact:** اختلاف ملحوظ بين توقع المستخدم وما ينفذه التطبيق، مع تعارض عند محاولة تسجيل handler بالاسم المحجوز.
- **Recommendation:** إبقاء دلالة الأمر نقطة قرار للمراجعة؛ لا تغيير لقائمة BotFather دون موافقة.
- **Verification Method:** تتبع التسجيل المحجوز وdispatch ومراجعة Router `/start`.
- **Verification Result:** تعارض المصدر مؤكد؛ لم يُتصل ببوت حقيقي ولم تُفحص قائمة BotFather عبر Telegram.

### Finding F-SF-04 — بيانات التغليف والاعتمادية غير متوافقة

- **ID:** `F-SF-04`
- **Title:** Public package metadata does not establish a reproducible install
- **Status:** `OBSERVED`
- **Severity:** High — قابلية التثبيت
- **Location:** SourceFarm وTitan public snapshots
- **File:** `SourceFarm/pyproject.toml`; `Titan/pyproject.toml`; `Titan/README.en.md`; tracked README inventory
- **Symbol:** `[project]`; dependency declaration; README metadata
- **Line Range:** `SourceFarm/pyproject.toml:5-40`; `Titan/pyproject.toml:5-43`; `Titan/README.en.md:20`; README inventory: N/A
- **Evidence:** SourceFarm يعلن حزمة `hozan` ويشير إلى `README.en.md` غير الموجود ضمن الملفات المتتبعة؛ PyPI JSON endpoint لـ `titan-framework` أعاد 404 وقت الفحص؛ تعليمات Titan تشير إلى Git install.
- **Actual Behavior:** تشغيل اختبارات SourceFarm السابق احتاج إتاحة مصدر Titan المحلي عبر `PYTHONPATH`.
- **Expected Behavior:** يحدد manifest وREADME مصدر تثبيت موجوداً وقابلاً لإعادة الإنتاج.
- **Impact:** لم يثبت تثبيت SourceFarm من metadata وحدها؛ نجاح الاختبار مع مصدر محلي لا يثبت قابلية التثبيت من PyPI.
- **Recommendation:** توثيق مصدر التثبيت قبل أي اعتماد؛ لم تُغيّر dependencies في هذه الجولة.
- **Verification Method:** قراءة manifests والجرد، واستعلام قراءة فقط إلى PyPI؛ لم يُبنَ wheel.
- **Verification Result:** التناقضات ملحوظة؛ `python -m build` والتثبيت النظيف غير متحققين.

### Finding F-TI-01 — Titan يوفّر transport عاماً لا تغطية Actions typed شاملة

- **ID:** `F-TI-01`
- **Title:** Titan exposes a generic transport and a limited wrapper set
- **Status:** `VERIFIED`
- **Severity:** High مقابل متطلب محرك No-Code؛ لا يعني خللاً عاماً في Titan
- **Location:** مستودع Titan العام عند `b00b43ecee5c3b7d6cc06467b07c4418d467521b`
- **File:** `src/titan/telegram.py`; `src/titan/adapter.py`; `src/titan/update.py`; `src/titan/bot.py`; SourceFarm file inventory
- **Symbol:** `Telegram.request`; adapter wrappers; `BotApiTranslator`; `Update.raw`; `_handle_update`
- **Line Range:** `telegram.py:50-89`; `adapter.py:71-93,274-298`; `update.py:40-110,122-131`; `bot.py:656-739`
- **Evidence:** مسار JSON عام يقبل method name؛ 26 wrapper مميزاً لطرق رسمية، إضافة إلى helper غير رسمي `sendRichMessage`؛ dispatch يغطي أنواع Update محددة ويسقط غير المدعوم؛ لا يوجد SourceFarm Action Registry.
- **Actual Behavior:** مطور Python يمكنه استخدام raw request ضمن حدود النقل، لكن لا يوجد في SourceFarm نموذج Actions/Triggers يعرّض ذلك لمستخدم No-Code، كما أن النقل لا يقدم رفع `InputFile` عبر multipart.
- **Expected Behavior:** وجود عقود وأشكال typed وعمليات رفع/dispatch مطلوبة إذا أريد ادعاء تغطية قابلة للاستخدام في Builder.
- **Impact:** عدد wrappers في Titan لا يساوي تغطية Bot API ولا يثبت تكامل SourceFarm.
- **Recommendation:** اعتبار مصفوفة API مرجع مقارنة فقط؛ لا تعتمدها كاختبار عملي لكل method أو كقرار بنية.
- **Verification Method:** تتبع request/adapter/update/dispatch ومقارنة آلية بالمرجع الرسمي؛ مراجعة يدوية محدودة موضحة في `TELEGRAM_API_COVERAGE.md`.
- **Verification Result:** حدود المصدر مؤكدة؛ لم تُستدعَ طرق Bot API عملياً ولم يحدث اتصال بحساب أو token.

### Finding F-CUPS-01-OBS — لا تظهر مصادقة تطبيقية على Runtime routes

- **ID:** `F-CUPS-01-OBS`
- **Title:** Runtime identity is caller-supplied in the reviewed routes
- **Status:** `OBSERVED`
- **Severity:** High إذا اعتمدت routes على شبكة غير موثوقة؛ هذا الشرط لم يثبت
- **Location:** CUPS public snapshot `565650cd55c0d92bdae2f99fe44b48f51a63c527`
- **File:** `src/cups/api/runtime.py`; `src/cups/service.py`; `tests/api/test_runtime.py`
- **Symbol:** request models; `check_entitlement`; quota/reserve/consume routes; `_owned_project`; TestClient cases
- **Line Range:** `runtime.py:19-32,37-89,103-146,171-226`; `service.py:239-245`; `test_runtime.py:28-31,55-66,148-155`
- **Evidence:** `account_id` و`project_id` حقول body؛ مقارنة الملكية تستخدم `req.account_id`; لم تظهر dependency للمصادقة في routes التي راجعتها. اختبار entitlement يرسل الطلب بلا Authorization ويستعيد 200، واختبار الحساب الخاطئ يختبر اختلاف body account id فقط.
- **Actual Behavior:** الشيفرة المراجعة لا تثبت هوية caller من credential؛ اختبار mismatch لا يثبت مصادقة.
- **Expected Behavior:** اشتقاق هوية caller من اعتماد موثوق ثم إجراء فحص الملكية والتفويض.
- **Impact:** لا يجوز اعتبار `account_id` المرسل دليلاً على الهوية؛ أما أثر ذلك خارج التطبيق فيعتمد على التعرض والحماية الخارجية.
- **Recommendation:** توثيق عقد المصادقة والتفويض قبل أي تكامل لاحق؛ لا تغيير للكود في هذه الجولة.
- **Verification Method:** مراجعة routes ونماذج الطلب واختبارات TestClient والبحث النصي عن dependencies/auth headers.
- **Verification Result:** غياب المصادقة التطبيقية ظاهر في المسارات المراجعة؛ التعرض الخارجي منفصل و`NOT VERIFIED`.

### Finding F-CUPS-01-INF — أثر محتمل مشروط بإتاحة API

- **ID:** `F-CUPS-01-INF`
- **Title:** Unauthenticated runtime operations may be reachable if external controls are absent
- **Status:** `INFERRED`
- **Severity:** High، مشروط بإتاحة الخدمة وعدم وجود حماية خارجية
- **Location:** CUPS Runtime API؛ فرضية الأثر فقط
- **File:** `src/cups/api/runtime.py`; `src/cups/service.py`
- **Symbol:** caller-supplied account identity; ownership/resource operations
- **Line Range:** `runtime.py:103-146,171-226`; `service.py:153-245`
- **Evidence:** هوية الحساب واردة في body، ولا تظهر dependency مصادقة في routes المقروءة.
- **Actual Behavior:** الكود يقبل identity من الطلب ويستخدمها في عمليات entitlement/resource؛ لم يُختبر طلب خارجي.
- **Expected Behavior:** منع الوصول غير المصادق عليه عند أي حد خارجي، مع التفويض على هوية موثوقة.
- **Impact:** إذا انعدم أي تحكم خارجي وكانت الخدمة متاحة، فقد تكون عمليات runtime متاحة لcaller غير موثق. مقدار الأثر لا يثبت من المصدر وحده.
- **Recommendation:** التعامل معه كخطر مشروط يستدعي مراجعة إعداد النشر لاحقاً، وليس كإثبات اختراق أو تعرض.
- **Verification Method:** تحليل ساكن لتدفق الهوية فقط؛ لم تُنفذ اختبارات هجومية أو اتصال إنتاجي.
- **Verification Result:** الاستنتاج مشروط؛ لم يُتحقق من وجود خدمة عامة أو من إمكان الوصول إليها.

### Finding F-CUPS-01-NV — التعرض الخارجي لـ CUPS غير متحقق

- **ID:** `F-CUPS-01-NV`
- **Title:** External reachability and production controls are unknown
- **Status:** `NOT VERIFIED`
- **Severity:** غير محددة
- **Location:** بيئة نشر CUPS غير متاحة في المستودع
- **File:** لا توجد ملفات نشر/عنوان خدمة متاح للفحص ضمن اللقطة
- **Symbol:** لا ينطبق
- **Line Range:** لا ينطبق
- **Evidence:** لم يظهر دليل نشر أو عنوان إنتاج موثق في ملفات Git التي فُحصت.
- **Actual Behavior:** لا يمكن تحديد ما إذا كان Runtime API عاماً أو داخلياً أو محمياً بـ proxy/firewall.
- **Expected Behavior:** إثبات حدود الوصول من إعداد نشر مصرح به، لا من افتراضات الكود.
- **Impact:** لا يمكن تأكيد أو نفي خطر خارجي من هذه المراجعة.
- **Recommendation:** إبقاء التعرض `NOT VERIFIED`؛ لا فحص نشط ولا اتصال إنتاجي في هذا العمل.
- **Verification Method:** مراجعة ملفات المستودع فقط، بلا مسح شبكي أو اتصال بالخدمة.
- **Verification Result:** لا دليل كافياً؛ تبقى الحالة `NOT VERIFIED`.

### Finding F-CUPS-02 — عقد عميل CUPS الموصوف غير مكتمل

- **ID:** `F-CUPS-02`
- **Title:** The documented CUPS guard is not implemented by the reviewed client
- **Status:** `VERIFIED`
- **Severity:** Medium
- **Location:** CUPS public snapshot
- **File:** `apps/titan_framework/cups_client.py`; `pyproject.toml`; `docs/ARCHITECTURE.md`; `docs/IMPLEMENTATION-PLAN.md`; Titan manifest
- **Symbol:** `TitanEntitlementClient`; optional `bot` extra; `CUPSGuard` docs
- **Line Range:** `cups_client.py:6-33`; `pyproject.toml:28-40`; `ARCHITECTURE.md:7-18,63-70,107-140`; `IMPLEMENTATION-PLAN.md:157-184`
- **Evidence:** العميل يرسل JSON دون API key؛ CUPS core لا يعتمد Titan، بينما bot extra يشير إلى Titan؛ Titan لا يستورد CUPS في المصدر المفحوص.
- **Actual Behavior:** الموجود client/vertical slice داخل CUPS، وليس تكاملاً مستخدماً من Titan أو SourceFarm.
- **Expected Behavior:** أن تصف الوثائق الوضع الحالي كتجريبي أو مخطط، وألا يوصف API key كحماية قائمة في العميل.
- **Impact:** الاعتماد على الوصف الوثائقي قد يوحي بتكامل أو مصادقة غير موجودين.
- **Recommendation:** الاحتفاظ بالفصل بين الواقع والنية المخططة؛ لا اعتماد دمج في هذه الجولة.
- **Verification Method:** مراجعة manifests والعميل والوثائق والبحث عن imports.
- **Verification Result:** اتجاه Bot CUPS → Titan ظاهر؛ لا تكامل Titan/SourceFarm → CUPS مثبت.

### Finding F-CUPS-03 — الدفع محاكاة

- **ID:** `F-CUPS-03`
- **Title:** Payment and refund flows are simulations
- **Status:** `VERIFIED`
- **Severity:** Medium
- **Location:** CUPS public snapshot
- **File:** `src/cups/service.py`; `tests/contract/test_referral_vertical_slice.py`; payment-related handlers
- **Symbol:** `set_subscription_for_test`; `simulate_paid_payment`; `simulate_refund`
- **Line Range:** `service.py:261-277,326-383`; `test_referral_vertical_slice.py:104-111,144-189`
- **Evidence:** عمليات الاختبار تغيّر حالة الاشتراك/الدفع تمثيلياً؛ لا يظهر provider أو Telegram Stars callback في المسارات المفحوصة.
- **Actual Behavior:** يمكن محاكاة سيناريوهات entitlement/refund ضمن الاختبارات، لا تحصيل أموال فعلي.
- **Expected Behavior:** وصف المنتج على أنه simulation إلى أن يثبت تكامل دفع حقيقي.
- **Impact:** لا يثبت جاهزية billing تجاري.
- **Recommendation:** عدم تسويق أو تفعيل تحصيل مدفوع استناداً إلى هذه الوظائف.
- **Verification Method:** مراجعة service والاختبارات والhandlers والdependencies.
- **Verification Result:** لا يوجد استدعاء payment provider في الشيفرة التي فُحصت.

### Finding F-CUPS-04 — تهيئة قاعدة البيانات عند استيراد Runtime

- **ID:** `F-CUPS-04`
- **Title:** Importing the API module may open or create the default SQLite file
- **Status:** `VERIFIED`
- **Severity:** Medium — أثر جانبي على بيئة الاختبار/التشغيل
- **Location:** CUPS public snapshot
- **File:** `src/cups/api/runtime.py`; `src/cups/service.py`; `src/cups/storage/sqlite.py`; `apps/cups-bot/main.py`; `tests/api/test_runtime.py`
- **Symbol:** module-level `_service`; `CUPSService.__init__`; `SQLiteStore.__init__`; test fixture
- **Line Range:** `runtime.py:25-32`; `service.py:36-53`; `sqlite.py:181-188`; `main.py:40-43`; `test_runtime.py:12,18-25`
- **Evidence:** Runtime ينشئ خدمة افتراضية عند import؛ service ينشئ `SQLiteStore()` عند عدم تمرير store؛ store يفتح المسار الافتراضي النسبي `cups.db`. ملف الاختبار يستورد Runtime قبل fixture التي تستبدل الخدمة بـ SQLite in-memory.
- **Actual Behavior:** جمع/استيراد اختبار API قد يفتح أو ينشئ `cups.db` قبل تطبيق fixture؛ بوت CUPS وRuntime يستخدمان مساراً نسبياً افتراضياً، والتعليق يقصد مشاركة الملف.
- **Expected Behavior:** إعداد اختبار معزول قبل استيراد module، ومسار تشغيل صريح؛ التأكد من working directory إذا كان المقصود مشاركة الملف بين عمليتين.
- **Impact:** قد يتغير ملف محلي أثناء جمع الاختبارات؛ كما لا يثبت source وحده أن عمليتي API والبوت تشيران إلى الملف نفسه في النشر.
- **Recommendation:** توثيق ذلك كأثر يجب معالجته لاحقاً؛ لم أعدل الكود ولم أشغّل الاختبارات في هذه الجولة.
- **Verification Method:** تتبع الاستدعاءات الساكن بين module/service/store وfixture.
- **Verification Result:** مسار الإنشاء عند الاستيراد ظاهر في الشيفرة؛ لم أنفذ import أو اختباراً في هذه الجولة كي لا أكتب إلى قاعدة بيانات.

### Finding F-CUPS-05 — إدراج اسم المشروع في HTML

- **ID:** `F-CUPS-05`
- **Title:** User-provided project name is interpolated into an HTML Telegram message
- **Status:** `VERIFIED`
- **Severity:** Low — موثوقية/تنسيق الرسالة
- **Location:** CUPS Bot public snapshot
- **File:** `apps/cups-bot/handlers/addbot.py`
- **Symbol:** project-name state and reply construction
- **Line Range:** `addbot.py:18-32,63-69,86-97`
- **Evidence:** اسم المشروع يأتي من نص المستخدم ثم يدخل الرسالة التي تستخدم `parse_mode="HTML"` من دون escaping ظاهر في هذا المسار.
- **Actual Behavior:** قيمة الاسم قد تكوّن كيانات Telegram HTML غير صالحة أو تغيّر التنسيق المقصود.
- **Expected Behavior:** escaping آمن أو تنسيق entities منفصل عن نص المستخدم.
- **Impact:** فشل/تشوه رسالة البوت ممكن؛ لم يثبت تنفيذ كود في متصفح ولا أوصف النمط بأنه XSS.
- **Recommendation:** إبقاء ملاحظة التنسيق موثقة؛ لا اختبار مدخلات خاصة في هذه الجولة.
- **Verification Method:** مراجعة إدخال الحالة ونص الرد و`parse_mode`.
- **Verification Result:** interpolation المباشر ظاهر؛ لم تُجرَ تجربة هجومية أو إرسال رسالة.

### Finding F-CUPS-06 — مؤشرات إيجابية محدودة في SQL

- **ID:** `F-CUPS-06`
- **Title:** Reviewed resource SQL uses bound parameters and explicit transactions
- **Status:** `VERIFIED`
- **Severity:** Informational — control إيجابي، وليس ثغرة
- **Location:** CUPS public snapshot
- **File:** `src/cups/storage/sqlite.py`; resource API tests
- **Symbol:** quota/reservation/consumption queries; transaction boundaries
- **Line Range:** `sqlite.py:240-370`; `tests/api/test_runtime.py:32-155`
- **Evidence:** الاستعلامات المراجعة تستخدم placeholders؛ عمليات الحجز والاستهلاك تستخدم معاملات SQLite؛ اختبارات API تغطي حالات مورد/حدود/idempotency.
- **Actual Behavior:** الإدخال في هذه العمليات يمر عبر SQL parameters، وتوجد حماية transaction-level في المسارات المحددة.
- **Expected Behavior:** استمرار parameterization والاختبارات، مع مراجعة بقية الاستعلامات بشكل منفصل قبل ادعاء ضمان أمني شامل.
- **Impact:** يقلل هذا النمط مخاطر بناء SQL من النص في المسارات المفحوصة فقط.
- **Recommendation:** الحفاظ على النمط؛ لا تعتبره بديلاً عن المصادقة أو مراجعة بقية SQL.
- **Verification Method:** قراءة استعلامات SQLite واختبارات runtime؛ لم تُشغّل اختبارات في جولة الاستكمال.
- **Verification Result:** دليل الشيفرة إيجابي ومحدود؛ لا يصدر عنه حكم شامل على أمان CUPS.

### Finding F-TG-01 — تصحيح جرد Bot API وإعادة إنتاجه

- **ID:** `F-TG-01`
- **Title:** Bot API inventory counts are reproducible after fixing end-of-document parsing
- **Status:** `VERIFIED`
- **Severity:** Informational — تصحيح دقة وثائقية
- **Location:** Telegram Bot API الرسمي كما استُرجع في 7 نوفمبر 2026؛ مصفوفة المقارنة
- **File:** `docs/architecture/TELEGRAM_API_COVERAGE.md`
- **Symbol:** `Inventory.finish_heading`; method/type headings; `GameHighScore`
- **Line Range:** `TELEGRAM_API_COVERAGE.md:30-145` (المنهجية، السكربت، ومراجع الشيفرة)؛ `:790` (صف `GameHighScore`)
- **Evidence:** parser السابق لم ينهِ آخر heading عند نهاية HTML، فسقط `GameHighScore` بثلاثة حقول. النسخة المصححة تستدعي `close()` ثم تنهي heading أخيراً، وتحوي فحوص التكرار والعدد.
- **Actual Behavior:** الأعداد السابقة `399 types / 364 field tables / 1,885 fields` كانت أقل بثلاثة حقول؛ القيم المعتمدة الآن `185 methods / 400 types / 365 field tables / 1,888 fields / 28 Update fields`.
- **Expected Behavior:** إمكان إعادة إنتاج الجرد آلياً، مع توضيح الاستثناءات ووسم المراجعة اليدوية.
- **Impact:** استخدام العدد القديم كان سيغفل نوعاً واحداً وثلاثة حقول من المصفوفة.
- **Recommendation:** اعتماد الأرقام المصححة فقط مع مرجع الصفحة وتاريخ الجلب؛ لا تدّعِ تنفيذ الطرق عملياً.
- **Verification Method:** سكربت Python من المكتبة القياسية يقرأ صفحة Telegram الرسمية، يعدّ headings والجداول، ويتحقق من الفريدة وحقول Update؛ مراجعة يدوية للتصنيف وآخر صف.
- **Verification Result:** الأعداد قابلة لإعادة الإنتاج من الصفحة وقت الفحص؛ لا duplicate method/type names ولا duplicate field names per type. لا method من الـ185 جُرّبت على Telegram فعلي.

### Finding F-SCOPE-01 — حالة SourceFarm المحلية غير متاحة للفحص

- **ID:** `F-SCOPE-01`
- **Title:** Local and unpushed SourceFarm/Hozan state is unknown
- **Status:** `NOT VERIFIED`
- **Severity:** Informational — قيد نطاق
- **Location:** مصدر الشيفرة المحلية للمستخدم غير متصل/غير موجود ضمن الملفات المتاحة لهذا التدقيق
- **File:** غير متاح
- **Symbol:** لا ينطبق
- **Line Range:** لا ينطبق
- **Evidence:** اللقطة التي أمكن قراءتها هي المستودعات العامة فقط؛ ملفات هذا المشروع الحالي هي وثائق التدقيق والقالب العام، وليست شجرة SourceFarm المحلية.
- **Actual Behavior:** لا يمكن معرفة التعديلات غير المرفوعة أو الملفات المحلية المحذوفة/المضافة عند المستخدم.
- **Expected Behavior:** مقارنة اللقطة العامة مع مشروع/نسخة محلية فعلية إذا أريد إغلاق هذه الفجوة.
- **Impact:** قد تختلف حالة المستخدم المحلية عن الاستنتاجات الواردة للمستودع العام.
- **Recommendation:** عدم تعميم أي نتيجة من snapshot العام على ملفات محلية غير مرئية؛ لا يلزم ربط GitHub لهذا التقرير.
- **Verification Method:** تحديد نطاق الملفات المتاحة ومقارنته بلقطة Git العامة؛ لا استخدام لمعلومات اعتماد أو صلاحيات GitHub.
- **Verification Result:** الحالة المحلية/غير المرفوعة `NOT VERIFIED`، ولا يمثل المستودع العام كامل ما لدى المستخدم.

### Finding F-IMAGE-01 — تمت معاينة الصورة المرجعية نفسها

- **ID:** `F-IMAGE-01`
- **Title:** Attached SourceFarm reference image was directly inspected
- **Status:** `VERIFIED`
- **Severity:** Informational — توثيق مرئي
- **Location:** ملف الصورة المرفق بالمحادثة والمحافظ عليه مع الملفات المرفقة
- **File:** المرفق الأصلي `attached_assets/file_0000000096108210a5743aafa6644090_1794050409771.png`؛ المسار المتاح أثناء المراجعة `.local/conversation-workspace/files/attached_assets/file_0000000096108210a5743aafa6644090_1794050409771.png`
- **Symbol:** لا ينطبق — صورة نقطية
- **Line Range:** لا ينطبق
- **Evidence:** فتحت الصورة نفسها بدقة 1024×1024؛ تعرض شعار SourceFarm الأبيض/الأخضر بأسلوب pixel على خلفية سوداء، ثلاثة تنويعات للشعار، شريطاً مصغراً لتدفق (شعار → محادثة → برق → إرسال → بوت)، وأسفلها ميزات مكتوبة بالعربية.
- **Actual Behavior:** الصورة لوحة هوية/مفهوم، وليست لقطة واجهة Mini App يمكن تقييم التنقل أو حالات الاستخدام منها.
- **Expected Behavior:** توثيق ما يظهر فعلاً في الصورة مع الفصل بين الهوية البصرية ووجود واجهة تنفيذية.
- **Impact:** وصف الصورة لا يثبت وجود صفحات أو وظائف في التطبيق.
- **Recommendation:** استخدامها كمرجع بصري فقط بعد مراجعة المستخدم؛ لا استنتاج تصميم أو تنفيذ غير ظاهر.
- **Verification Method:** فتح ملف PNG ومعاينة الصورة مباشرة.
- **Verification Result:** الصورة متاحة وتمت معاينتها؛ ليست مجرد استنتاج من وصف نصي سابق.

### Finding F-DEL-01 — التقارير أربعة ملفات منفصلة وغير مدمجة

- **ID:** `F-DEL-01`
- **Title:** Four approved reports exist as separate Markdown files in this project
- **Status:** `VERIFIED`
- **Severity:** Informational — تسليم
- **Location:** جذر المشروع الحالي، تحت `docs/architecture/`
- **File:** `REPOSITORY_AUDIT.md`; `DEPENDENCY_MAP.md`; `TELEGRAM_API_COVERAGE.md`; `PRODUCT_BOUNDARIES.md`
- **Symbol:** repository file inventory
- **Line Range:** لا ينطبق — تحقق من شجرة الملفات
- **Evidence:** تظهر الملفات الأربعة كملفات منفصلة في Git status للمشروع. في SourceFarm public snapshot لم تكن هذه الملفات ضمن الملفات المتتبعة؛ كانت وثيقتا ADR فقط تحت `docs/ADRs/`.
- **Actual Behavior:** التسليم هنا أربعة ملفات Markdown منفصلة غير ملتزمة بعد؛ لم تُدمج في ملف واحد ولم تُضف إلى المستودع العام SourceFarm.
- **Expected Behavior:** وجود الوثائق الأربع المعتمدة فقط كملفات منفصلة، دون ملفات تسليم إضافية.
- **Impact:** يمكن مراجعة كل موضوع مستقلاً؛ لا يعني ذلك أنها نُشرت أو أضيفت إلى SourceFarm.
- **Recommendation:** مراجعة الملفات في هذا المشروع؛ لا Commit/Push قبل موافقة المستخدم.
- **Verification Method:** جرد `docs/architecture/` و`git status`؛ مقارنة قائمة الملفات المتتبعة في SourceFarm public HEAD.
- **Verification Result:** أربعة ملفات منفصلة موجودة هنا؛ غير متتبعة بعد في المشروع؛ لا Commit أو Push.

## تقييم المكونات

| المكوّن | التصنيف الأولي | السبب |
|---|---|---|
| Hozan identity foundation | `MODERNIZE` | فصل خدمة/Repository مفيد، لكن التنفيذ ذاكرة ونطاقه ضيق |
| Titan framework | `KEEP` ثم `INVESTIGATE` عند ربط المحرك | إطار مستقل واختبارات قوية؛ التغطية typed ليست Bot API كاملة |
| CUPS core | `KEEP` مستقلاً، `INVESTIGATE` المصادقة والتكامل | نطاق Entitlements مستقل، مع فجوة مصادقة محتملة ومرحلة Alpha |
| Hozan/Titan boundary | `KEEP` كحد مبدئي | التطبيق يفصل Telegram adapter؛ لا حاجة ظاهرة لدبلجة polling |
| SourceFarm UI/Store/Builder | `INVESTIGATE` ثم تصميم بعد الموافقة | لا يوجد تنفيذ حالي يمكن ترقيعه أو مقارنة صفحات به |

## الصورة المرجعية

تم فتح ملف PNG المرفق نفسه `attached_assets/file_0000000096108210a5743aafa6644090_1794050409771.png` ومعاينته مباشرة؛ كان متاحاً أثناء الاستكمال عبر `.local/conversation-workspace/files/attached_assets/file_0000000096108210a5743aafa6644090_1794050409771.png`. الصورة لوحة هوية ومفهوم وليست لقطة Mini App: شعار SourceFarm pixel أبيض/أخضر على خلفية سوداء، ثلاثة تنويعات للشعار، شريط تدفق مصغر (الشعار ← محادثة ← برق ← إرسال ← بوت)، وأسفلها ميزات مكتوبة بالعربية عن مكونات جاهزة، وربط التدفقات، وبوتات بلا برمجة، والنشر الفوري على Telegram. لا يمكن تقييم التنقل أو صفحات الواجهة الحالية من هذه الصورة.

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

- كانت النسخ العامة الثلاثة عند الـ commits المبينة أعلاه نظيفة في فحص Git السابق؛ جولة الاستكمال لم تعدل أي نسخة مصدر. هذا لا يكشف تغييرات محلية غير مرفوعة عند المستخدم.
- المشروع الحالي هو مساحة توثيق لهذه الجولة، وليس شجرة شيفرة SourceFarm/Hozan المحلية؛ لذلك لا يثبت وجوده حالة الملفات المحلية التي لم تُرفع.
- فُحص المصدر والاختبارات والmanifests وCI والوثائق ذات الصلة. في جولة الاستكمال لم يُعدّل أي كود تطبيق أو اعتماديات أو قاعدة بيانات، ولم تُجرَ اختبارات هجومية أو اتصالات إنتاجية، ولم يقع Commit أو Push.
- بيئة الاختبار: Python `3.13.11`، pytest `9.2.0`، pytest-asyncio `1.4.1.post1`، aiohttp `3.14.5`، FastAPI `0.162.0`، httpx `0.28.1`.
- نتائج التشغيل المذكورة أدناه من الجولة السابقة على commits نفسها، وليست اختبارات أُعيد تشغيلها في استكمال الوثائق.
- SourceFarm: `5 passed`; أضيف `Titan/src` محلياً إلى `PYTHONPATH`، لذا لا يثبت ذلك تثبيت PyPI.
- Titan: `992 passed`; لا اتصال ببوت Telegram أو حساب إنتاجي.
- CUPS: `73 passed, 299 warnings`; أبرزها DeprecationWarning لـ `datetime.utcnow()` وتحذير Starlette للثابت `HTTP_422_UNPROCESSABLE_ENTITY`. لم تُعَد الاختبارات هنا لأن استيراد Runtime قد يفتح/ينشئ `cups.db` قبل fixture الذاكرة.
- أحدث تشغيل Actions ظاهر لـ Titan على `b00b43e` ناجح، ولـ CUPS على `565650c` ناجح. لم يوجد تشغيل SourceFarm في API (`total_count=0`). لا يثبت هذا إعداد نشر/إنتاج.
- فُحص مرجع Bot API الرسمي بإصدار `10.3` (آخر تحديث ظاهر 24 أغسطس 2026) بتاريخ 7 نوفمبر 2026. جُددت طريقة العد في الوثيقة لإظهار فحوص اكتمال headings والتكرار؛ لم تُستخدم أسرار أو بيانات Telegram حقيقية، ولم تُختبر الطرق فعلياً.
- التقارير الأربعة الآن ملفات منفصلة في `docs/architecture/` في هذا المشروع. وهي ليست ملفات متتبعة في SourceFarm public HEAD؛ لم تُضف إلى ذلك المستودع.
- Git في هذا المشروع قبل إدخال الوثائق: branch `main`, HEAD `133c0f1e3c1581628263af291a8dfa48aab62eb2`; الحالة `?? .agents/agent_assets_metadata.toml` و`?? .conversation/` فقط.
- Git بعد الاستكمال: HEAD نفسه بلا commit جديد؛ الحالة `M .replit` إضافة إلى المسارين السابقين والوثائق الأربعة `?? docs/architecture/*.md`. لا توجد تغييرات staged ولا Commit/Push. لم ألمس `.replit`؛ ظهر اختلافه بعد الفحص الأولي بالتزامن مع إعداد المشروع، ويضيف `python-base-3.13` إلى `modules`. لا أملك من Git دليلاً يحدد من أنشأه، لذلك أبقيته كما هو.
- لم أغيّر manifests أو lockfiles أو ملفات التطبيق أو قاعدة بيانات. تغيير `.replit` أعلاه إعداد runtime/toolchain مرصود في Git status، وليس تغييراً في dependencies package؛ يجب عدم نسبته إلى تحرير الوثائق.
- فحص Git العام بعد إعداد التقارير أعاد نفس commits للنسخ الثلاثة وكانت جميعها `CLEAN`: SourceFarm `2187dfd29f8b1ce9fc45ba53acc61b091898cb44` (44 ملفاً، وصفر من تقارير `docs/architecture/` متتبعة)، Titan `b00b43ecee5c3b7d6cc06467b07c4418d467521b` (212 ملفاً)، وCUPS `565650cd55c0d92bdae2f99fe44b48f51a63c527` (67 ملفاً).
- `NOT VERIFIED`: مصادقة/حدود شبكة CUPS عند النشر، إعداد تشغيل خارج Git، الحالة المحلية غير المرفوعة لدى المستخدم، تأكيد BotFather عبر Telegram، أو مستودع Hozan مستقل.

## المصادر

- [SourceFarm pyproject.toml](https://github.com/WaheedFox/SourceFarm/blob/2187dfd29f8b1ce9fc45ba53acc61b091898cb44/pyproject.toml)
- [Hozan application](https://github.com/WaheedFox/SourceFarm/blob/2187dfd29f8b1ce9fc45ba53acc61b091898cb44/src/hozan/core/app/application.py)
- [Hozan identity repository](https://github.com/WaheedFox/SourceFarm/blob/2187dfd29f8b1ce9fc45ba53acc61b091898cb44/src/hozan/features/identity/memory.py)
- [Titan Telegram transport](https://github.com/WaheedFox/Titan/blob/b00b43ecee5c3b7d6cc06467b07c4418d467521b/src/titan/telegram.py)
- [Titan dispatch](https://github.com/WaheedFox/Titan/blob/b00b43ecee5c3b7d6cc06467b07c4418d467521b/src/titan/bot.py)
- [CUPS Runtime API](https://github.com/WaheedFox/CUPS/blob/565650cd55c0d92bdae2f99fe44b48f51a63c527/src/cups/api/runtime.py)
- [CUPS service](https://github.com/WaheedFox/CUPS/blob/565650cd55c0d92bdae2f99fe44b48f51a63c527/src/cups/service.py)
- [Telegram Bot API](https://core.telegram.org/bots/api)
