# Nakazasen AI Router

Nakazasen AI Router l・・｣ｰ n逶ｻ・ｽ m・・ｽｳng Python ・・ｻ幢ｽｻ繝ｻ・・ｨｴ逶ｻ縲・ph逶ｻ險ｴ nhi逶ｻ縲・nh・・｣ｰ cung c陂ｯ・･p AI trong t・・ｽｰ・・ｽ｡ng lai.

逶ｻ繝ｻphi・・ｽｪn b陂ｯ・｣n hi逶ｻ繻ｻ t陂ｯ・｡i, d逶ｻ・ｱ ・・ｽ｡n **ch・・ｽｰa g逶ｻ邨・AI th陂ｯ・ｭt** v・・｣ｰ **kh・・ｽｴng ch逶ｻ・ｩa API key th陂ｯ・ｭt**. M逶ｻ・･c ti・・ｽｪu l・・｣ｰ chu陂ｯ・ｩn b逶ｻ繝ｻc陂ｯ・･u tr・・ｽｺc s陂ｯ・｡ch ・・ｻ幢ｽｻ繝ｻsau n・・｣ｰy port Provider Router t逶ｻ・ｫ `translation_app` sang.

## Tr陂ｯ・｡ng th・・ｽ｡i hi逶ｻ繻ｻ t陂ｯ・｡i

- API t逶ｻ險ｴ thi逶ｻ繝・ `AIRouter`, `AIRequest`, `AIResult`, `ProviderBase`, `ProviderCandidate`, `ProviderHealth`, `RouterPolicy`.
- Provider gi陂ｯ・｣ l陂ｯ・ｭp ・・ｻ幢ｽｻ繝ｻki逶ｻ繝・th逶ｻ・ｭ fallback, quota, auth, timeout.
- Kh・・ｽｴng g逶ｻ邨・m陂ｯ・｡ng, kh・・ｽｴng g逶ｻ邨・provider th陂ｯ・ｭt.
- Kh・・ｽｴng l・・ｽｰu API key th陂ｯ・ｭt.

## C・・｣ｰi ・・ｻ幢ｽｺ・ｷt ph・・ｽ｡t tri逶ｻ繝・
```bash
python -m pip install -e .[dev]
```

## Ch陂ｯ・｡y ki逶ｻ繝・th逶ｻ・ｭ

```bash
python -m pytest -q
python -m compileall src
```

## V・・ｽｭ d逶ｻ・･ nhanh

```python
from nakazasen_ai_router import AIRouter, AIRequest, RouterPolicy
from nakazasen_ai_router.fake_providers import provider_success

router = AIRouter(
    providers=[provider_success("local-demo", is_cloud=False)],
    policy=RouterPolicy(local_only=True),
)

result = router.route(AIRequest(prompt="Xin ch・・｣ｰo"))
print(result.text)
```

## Cam k陂ｯ・ｿt b陂ｯ・｣o m陂ｯ・ｭt

- Kh・・ｽｴng commit API key th陂ｯ・ｭt.
- Log ・・氈・ｰ逶ｻ・｣c l・・｣ｰm s陂ｯ・｡ch ・・ｻ幢ｽｻ繝ｻtr・・ｽ｡nh l逶ｻ繝ｻchu逶ｻ謫・nh陂ｯ・｡y c陂ｯ・｣m trong metadata.
- Provider th陂ｯ・ｭt s陂ｯ・ｽ ・・氈・ｰ逶ｻ・｣c th・・ｽｪm sau, k・・ｽｨm test ri・・ｽｪng.

## D・・ｽｹng trong repo kh・・ｽ｡c

B陂ｯ・｡n c・・ｽｳ th逶ｻ繝ｻt陂ｯ・｡o router nhanh t逶ｻ・ｫ bi陂ｯ・ｿn m・・ｽｴi tr・・ｽｰ逶ｻ諡ｵg, kh・・ｽｴng c陂ｯ・ｧn l・・ｽｰu API key trong code.

V・・ｽｭ d逶ｻ・･ PowerShell:

```powershell
$env:OPENROUTER_API_KEY = "<api-key>"
```

V・・ｽｭ d逶ｻ・･ Python:

```python
from nakazasen_ai_router import AIRequest, create_router_from_env

router = create_router_from_env()
result = router.route(AIRequest(prompt="Xin ch・・｣ｰo"))
print(result.text)
```

C・・ｽ｡c bi陂ｯ・ｿn m・・ｽｴi tr・・ｽｰ逶ｻ諡ｵg ・・鮪ng h逶ｻ繝ｻtr逶ｻ・｣:

| Provider | Bi陂ｯ・ｿn API key | Ghi ch・・ｽｺ |
|---|---|---|
| OpenRouter | `OPENROUTER_API_KEY` | Cloud OpenAI-compatible |
| Groq | `GROQ_API_KEY` | Cloud OpenAI-compatible |
| DeepSeek | `DEEPSEEK_API_KEY` | Cloud OpenAI-compatible |
| NVIDIA NIM | `NVIDIA_NIM_API_KEY` | Cloud OpenAI-compatible |
| ChatAnyWhere | `CHATANYWHERE_API_KEY` | Cloud OpenAI-compatible |
| Mistral | `MISTRAL_API_KEY` | Cloud OpenAI-compatible |
| Local server | `LOCAL_OPENAI_COMPATIBLE_BASE_URL` | Localhost c・・ｽｳ th逶ｻ繝ｻkh・・ｽｴng c陂ｯ・ｧn key |

Trong test m陂ｯ・ｷc ・・ｻ幢ｽｻ譚ｵh, d逶ｻ・ｱ ・・ｽ｡n v陂ｯ・ｫn kh・・ｽｴng g逶ｻ邨・internet. App b・・ｽｪn ngo・・｣ｰi n・・ｽｪn truy逶ｻ・ｽ `http_client` th陂ｯ・ｭt khi mu逶ｻ蜑ｵ g逶ｻ邨・provider th陂ｯ・ｭt.

## G逶ｻ邨・provider th陂ｯ・ｭt

M陂ｯ・ｷc ・・ｻ幢ｽｻ譚ｵh Nakazasen AI Router **kh・・ｽｴng g逶ｻ邨・internet**. `create_router_from_env()` ch逶ｻ繝ｻd逶ｻ・ｱng provider b陂ｯ・ｱng `_NoNetworkHTTPClient` n陂ｯ・ｿu b陂ｯ・｡n kh・・ｽｴng truy逶ｻ・ｽ transport.

・・妛・ｻ繝ｻg逶ｻ邨・provider th陂ｯ・ｭt, caller ph陂ｯ・｣i opt-in r・・ｽｵ r・・｣ｰng:

```python
from nakazasen_ai_router import AIRequest, create_router_from_env

router = create_router_from_env(enable_network=True)
result = router.route(AIRequest(prompt="Reply with OK."))
print(result.text)
```

Ho陂ｯ・ｷc truy逶ｻ・ｽ transport ri・・ｽｪng:

```python
router = create_router_from_env(http_client_factory=my_http_client_factory)
```

Live smoke test c・・ｽｩng b逶ｻ繝ｻt陂ｯ・ｯt m陂ｯ・ｷc ・・ｻ幢ｽｻ譚ｵh. Mu逶ｻ蜑ｵ ch陂ｯ・｡y th逶ｻ・ｧ c・・ｽｴng:

```powershell
$env:RUN_LIVE_AI_TESTS = "1"
$env:OPENROUTER_API_KEY = "<api-key>"
py -m pytest tests/test_live_smoke.py -q
```

N陂ｯ・ｿu kh・・ｽｴng c・・ｽｳ `RUN_LIVE_AI_TESTS=1`, test live s陂ｯ・ｽ skip. N陂ｯ・ｿu b陂ｯ・ｭt live nh・・ｽｰng thi陂ｯ・ｿu key, test s陂ｯ・ｽ skip thay v・・ｽｬ fail.

## Live smoke test v盻嬖 key th蘯ｭt

Live smoke test ch盻・dﾃｹng khi b蘯｡n ch盻ｧ ﾄ黛ｻ冢g ki盻ノ tra provider th蘯ｭt. Khﾃｴng commit API key vﾃ nﾃｪn ﾄ黛ｻ・file key n蘯ｱm ngoﾃi repo.

Vﾃｭ d盻･:

```powershell
py scripts/live_smoke.py --provider openrouter --key-file "D:\path\to\API Key.txt"
```

Script h盻・tr盻｣ cﾃ｡c provider: `openrouter`, `groq`, `deepseek`, `nvidia_nim`, `chatanywhere`, `mistral`.

File key cﾃｳ th盻・dﾃｹng d蘯｡ng bi蘯ｿn mﾃｴi trﾆｰ盻拵g:

```text
OPENROUTER_API_KEY=
```

Ho蘯ｷc nhﾃ｣n provider r盻妬 key 盻・dﾃｲng sau. Script ch盻・ﾄ黛ｻ皇 trong b盻・nh盻・ ﾄ黛ｺｷt bi蘯ｿn mﾃｴi trﾆｰ盻拵g t蘯｡m trong process, vﾃ ch盻・in provider/status/model/text preview an toﾃn. Khﾃｴng in API key.
