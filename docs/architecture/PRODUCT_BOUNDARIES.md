# حدود المنتجات الحالية — SourceFarm وHozan وCUPS

**الغرض:** مقارنة الواقع البرمجي بالرؤية التي قدمها المستخدم، دون اعتماد Architecture نهائية.  
**Snapshot:** SourceFarm `2187dfd` (2026-08-23)، Titan `b00b43e` (2026-11-05)، CUPS `565650c` (2026-08-25)، على `master` العام.

## خلاصة الحدود

- **SourceFarm كما هو مقصود:** بناء بوت يملكه المستخدم باستخدام Templates وStore وNo-Code Builder مع استضافة.
- **Hozan كما هو مقصود:** خدمات بوت مُدارة يملكها المنتج ويشغّلها، دون أن ينشئ المستخدم بوتاً أو يدير token.
- **CUPS كما هو موجود:** خدمة مستقلة للاشتراكات وEntitlements والمشاريع والموارد.
- **الواقع البرمجي:** لا يوجد اليوم تطبيق SourceFarm منفصل عن Hozan. مستودع `SourceFarm` يحزم `hozan`، ومحتواه identity/start scaffold فقط. لم أعثر على مستودع عام مستقل `WaheedFox/Hozan` بتاريخ الفحص؛ metadata تشير إليه وGitHub API يعيد 404. CUPS مستقل ولا يوجد به تكامل فعلي لـ SourceFarm/Hozan.

## المقارنة حسب المسؤولية

| المسؤولية | SourceFarm المطلوبة | Hozan المطلوبة | ما هو موجود فعلياً | حالة الحد |
|---|---|---|---|---|
| ملكية بوت Telegram | بوت المستخدم؛ ينشئه ويربطه | بوتات مملوكة/مدارة من المنصة | تطبيق واحد يبدأ بـ `HOZAN_TOKEN`؛ لا ربط بوت مستخدم ولا pool بوتات مدارة | غير منفصل عملياً |
| تجربة المستخدم | Builder وTemplates وStore وإدارة assets | كتالوج خدمة وتفعيل خدمة | `/start` يعرّف حساباً وهوية فقط | المنتجين غير مكتملين |
| Telegram runtime | تشغيل البوتات الناتجة من القوالب | تشغيل خدمات جاهزة | Titan long polling لبوت التطبيق الحالي | بوت واحد؛ لا orchestration |
| الأسرار | tokens الخاصة ببوت المستخدمين | tokens وأسرار بوتات الخدمة | `HOZAN_TOKEN` للتشغيل؛ لا نظام حفظ/عزل لبقية tokens | لا حدود بيانات منفذة |
| البيانات والهوية | حسابات وبوتات وقوالب وإصدارات وصلاحيات | حسابات وتفعيلات وخدمات وإعدادات | Telegram account وHozan ID في ذاكرة العملية؛ لا DB | غير دائمة وغير معزولة |
| Templates / Store / Payments | إصدار/نشر/اكتساب/بيع | ليست واجهة إنشاء بوت للمستخدم | لا كود لها في SourceFarm repository | غير منفذة |
| Managed services | لا تملك Bot Tokens المستخدمين | catalog وتفعيل وruntime ومراقبة | لا كتالوج خدمة أو تفعيل مجموعة/قناة أو logs/scaling | غير منفذة |
| التشغيل والاستضافة | تشغيل آمن ومتعدد لبوتات المستخدمين | تشغيل آمن لبوتات المنتج | لا deployment files أو workers متعددة المنتجات | غير متحقق في المصدر |
| الحسابات والاشتراكات | Store/حق الوصول للقوالب | اشتراك خدمة مُدارة | CUPS منفصل فيه accounts/projects/plans/catalog؛ لا SourceFarm/Hozan product | لا تكامل مثبت |

## الدليل التفصيلي

### SourceFarm

**VERIFIED:** لا توجد صفحة Frontend أو Mini App أو Store أو Templates أو workflow engine أو action/trigger registry في الملفات المتتبعة. لا سجل بوتات مستخدمين أو Token vault أو deployment worker. تمت مراجعة المصدر والـ manifests والاختبارات، لا الأسماء فقط.

**OBSERVED:** وصف `pyproject.toml` يقول no-code platform لكن package name هو `hozan` وREADME يصف Hozan؛ التطبيق الحالي يركّب Hozan app. هذا اختلاف بين الرؤية التي طلب المستخدم تدقيقها وبين Snapshot، وليس دليلاً على أن مكوّناً غير عام موجود في مكان آخر.

### Hozan

**VERIFIED:** خدمة هوية بسيطة ترتبط بـ Telegram user id وتولد Hozan ID مجاني بصيغة `#NNNNNNNN`. `/start` ينشئ الحساب والهوية، ومستودع الحسابات قاموس بالذاكرة. لا توجد خدمات مدارة للمجموعات أو القنوات، ولا Service Catalog أو lifecycle لكل خدمة، ولا تنفيذ لأوامر `/inspect`, `/logs`, `/env`, `/scale`.

**NOT VERIFIED:** تشغيل bot حقيقي أو بيئة نشر Hozan، ومحتوى مستودع غير عام أو غير موجود في القائمة العامة، وأي تغييرات محلية غير مرفوعة. المشروع الحالي يحتوي وثائق التدقيق ولا يحتوي شجرة SourceFarm/Hozan المحلية؛ لذلك لا تمثل اللقطة العامة كل ما قد يكون لدى المستخدم. لم أستخدم Telegram token أو خدمة إنتاجية.

### Titan

Titan حد مشترك فعلي لطبقة Telegram: SourceFarm/Hozan يعتمد عليه، وكذلك تطبيق بوت CUPS. يحتوي framework على polling وrouting ومجموعة wrappers. هذه مشاركة Runtime فقط، ولا تثبت وجود shared identity/database أو Builder engine. يملك Titan `/link` الداخلي؛ لذلك يؤثر في واجهة الأوامر، لكنه لا يجعل Hozan خدمة مُدارة.

### CUPS

CUPS يحدد منتجين في الكود (`titan-framework`, `cups-bot`) ويملك لهم Entitlement catalogs. لا يوجد Catalog لـ `sourcefarm` أو `hozan`، ولا import/API client في SourceFarm، ولا import لـ CUPS في Titan. تطبيق CUPS Bot يستخدم Titan، لكن نواة CUPS مستقلة عنه حسب manifest.

`TitanEntitlementClient` الموجود في `CUPS/apps/titan_framework/` يرسل `account_id`, `project_id`, `entitlement` إلى object اسمه `runtime`; لا يتضمن key رغم المثال الوثائقي `CUPSGuard(api_key=...)`، ولا يستعمله أي مستودع آخر. هذا نموذج عقد/vertical slice، وليس تكاملاً إنتاجياً.

في Runtime API لم تظهر مصادقة تطبيقية في المسارات المراجعة؛ اختبار TestClient يصل إلى entitlement بلا Authorization، واختبار 403 يقارن قيمة body مختلفة ولا يثبت هوية caller. هذا لا يثبت أن الخدمة مكشوفة خارجياً: الوصول وحدود الشبكة `NOT VERIFIED`. كما أن استيراد Runtime ينشئ خدمة SQLite افتراضية قبل fixture الاختبار التي تستبدلها بقاعدة in-memory؛ راجع تفاصيل الشيفرة والاختبارات في `REPOSITORY_AUDIT.md`.

## حدود الأمن والملكية التي لا ينبغي افتراضها

| الحد | ما يمكن إثباته | ما لم يثبت / الخطر |
|---|---|---|
| مستخدم SourceFarm وBot Token | لا توجد حالياً عملية إدخال/حفظ token للمستخدم | لا دليل على user token vault أو isolation |
| بوتات Hozan المدارة | التطبيق يقرأ `HOZAN_TOKEN` لبوت واحد | لا lifecycle أو per-service secret boundary في المصدر |
| CUPS project identity | UUID للمشروع وTelegram account id في domain | HTTP caller يرسل account id في body؛ لا مصادقة تطبيقية ظاهرة. التعرض الخارجي مجهول |
| الاشتراك/Entitlement | CUPS يحسب entitlement داخل الخدمة | لا مزود دفع فعلي؛ الدفع/refund محاكاة |
| بيانات الهوية | Hozan memory repository وCUPS SQLite منفصلان | لا DB أو سياسة retention/backup مشتركة |

## توصيات أولية للحدود — غير معتمدة

1. أبقِ **SourceFarm** و**Hozan** منتجين وتجربتين منفصلتين كما طلب المستخدم؛ لا توجد وظيفة حالية تبرر خلط واجهتيهما أو ملكية البوتات.
2. يمكن تقييم مشاركة Titan كطبقة Telegram/runtime فقط؛ لا تعتبرها إذناً لمشاركة tokens أو البيانات أو الصلاحيات.
3. لا تربط CUPS بأي منتج قبل اختيار consumer واضح وتعريف product id/catalog وidentity/authentication contract؛ الحالي لا يثبت قرار الدمج.
4. احسم أين يعيش تطبيق Hozan المستقل؛ المتاح في الفحص هو package `src/hozan` داخل SourceFarm فقط.
5. تعامل مع قائمة BotFather كمكتملة حسب إفادة المستخدم؛ لا تعِد التسجيل. عالج دلالة `/link` المحجوزة دون تغيير القائمة إلا بموافقة.
6. فُتحت صورة SourceFarm المرفقة نفسها، وهي لوحة هوية/مفهوم لا لقطة Mini App: شعار pixel أبيض/أخضر على خلفية سوداء، تنويعات للشعار، شريط تدفق مصغّر، وميزات مكتوبة بالعربية. استخدمها كمرجع هوية فقط، لا كدليل على وجود صفحات أو سلوك واجهة.

## أسئلة موافقة قبل الانتقال إلى المرحلة الأولى

- هل يعتمد اسم SourceFarm للمستودع والمنتج، واسم Hozan لمنتج/حزمة منفصلة؟
- هل يجب أن يبقى Hozan تطبيقاً مستقلاً تحت المستودع الحالي أم في مستودع منفصل؟
- هل يبقى CUPS خارج المنظومة الآن أم يُدرس لاحقاً كطبقة اشتراك مستقلة؟
- هل تبقى أسماء أوامر BotFather كما هي مع حل تعارض `/link` في التطبيق؟

لا تبدأ المرحلة الأولى حتى تتم مراجعة التقارير والحصول على موافقة صريحة.

## الأدلة

- [SourceFarm package manifest](https://github.com/WaheedFox/SourceFarm/blob/2187dfd29f8b1ce9fc45ba53acc61b091898cb44/pyproject.toml)
- [Hozan application composition](https://github.com/WaheedFox/SourceFarm/blob/2187dfd29f8b1ce9fc45ba53acc61b091898cb44/src/hozan/core/app/application.py)
- [Hozan start handler](https://github.com/WaheedFox/SourceFarm/blob/2187dfd29f8b1ce9fc45ba53acc61b091898cb44/src/hozan/features/registration/start.py)
- [CUPS catalog](https://github.com/WaheedFox/CUPS/tree/565650cd55c0d92bdae2f99fe44b48f51a63c527/src/cups/catalog)
- [CUPS Runtime API](https://github.com/WaheedFox/CUPS/blob/565650cd55c0d92bdae2f99fe44b48f51a63c527/src/cups/api/runtime.py)
- [Titan reserved `/link` implementation](https://github.com/WaheedFox/Titan/blob/b00b43ecee5c3b7d6cc06467b07c4418d467521b/src/titan/bot.py)

### مراجع الادعاءات ذات الأثر

| الادعاء | الملف في اللقطة العامة | الرمز | نطاق الأسطر |
|---|---|---|---|
| manifest يعرّف حزمة Hozan داخل SourceFarm | `SourceFarm/pyproject.toml` | `[project]`; dependencies | 5-40 |
| composition يبني تطبيق Hozan وذاكرة الهوية وRouter | `SourceFarm/src/hozan/core/app/application.py` | `Hozan.__init__` | 9-20 |
| الواجهة الحالية تسجل `/start` فقط | `SourceFarm/src/hozan/features/registration/start.py` | `build_router` | 8-29 |
| حسابات الهوية تخزن في قاموسين | `SourceFarm/src/hozan/features/identity/memory.py` | `MemoryAccountRepository` | 6-36 |
| Titan transport عام JSON | `Titan/src/titan/telegram.py` | `Telegram.request` | 50-89 |
| Titan يحجز `/link` ويعالج privacy commands داخلياً | `Titan/src/titan/bot.py` | `_register_link_command`; `_register_privacy_commands`; `Router.command` | 315-337; 381-401 |
| Bot API wrappers المتاحة محدودة ورفع الملفات ليس multipart | `Titan/src/titan/adapter.py`; `Titan/src/titan/telegram.py` | adapter methods; `Telegram.request` | 71-93; 19-298; 50-89 |
| Runtime API يستقبل owner/account id في body | `CUPS/src/cups/api/runtime.py`; `CUPS/src/cups/service.py` | request models; entitlement routes; `_owned_project` | 37-89; 103-146; 239-245 |
| اختبار Runtime لا يرسل Authorization ويختبر mismatch في body | `CUPS/tests/api/test_runtime.py` | test client; entitlement/mismatch cases | 28-31; 55-66; 148-155 |
| SQLite default path relative وعمليات الموارد تستخدم معاملات | `CUPS/src/cups/storage/sqlite.py` | `SQLiteStore.__init__`; resource methods | 181-188; 240-370 |
| مدفوعات CUPS تجريبية | `CUPS/src/cups/service.py` | `simulate_paid_payment`; `simulate_refund` | 261-277; 326-383 |
| التعرض الخارجي لـ CUPS وإعداد النشر | لا يوجد ملف إعداد/URL إنتاجي متاح في snapshot | لا ينطبق | لا ينطبق — `NOT VERIFIED` |

لا تمثل روابط GitHub أو نطاقات الأسطر أعلاه دليلاً على شجرة المستخدم المحلية غير المرفوعة.
