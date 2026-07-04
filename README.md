# Nakazasen AI Router

Nakazasen AI Router lﾃ n盻］ mﾃｳng Python ﾄ黛ｻ・ﾄ訴盻「 ph盻訴 nhi盻「 nhﾃ cung c蘯･p AI trong tﾆｰﾆ｡ng lai.

盻・phiﾃｪn b蘯｣n hi盻㌻ t蘯｡i, d盻ｱ ﾃ｡n **chﾆｰa g盻絞 AI th蘯ｭt** vﾃ **khﾃｴng ch盻ｩa API key th蘯ｭt**. M盻･c tiﾃｪu lﾃ chu蘯ｩn b盻・c蘯･u trﾃｺc s蘯｡ch ﾄ黛ｻ・sau nﾃy port Provider Router t盻ｫ `translation_app` sang.

## Tr蘯｡ng thﾃ｡i hi盻㌻ t蘯｡i

- API t盻訴 thi盻ブ: `AIRouter`, `AIRequest`, `AIResult`, `ProviderBase`, `ProviderCandidate`, `ProviderHealth`, `RouterPolicy`.
- Provider gi蘯｣ l蘯ｭp ﾄ黛ｻ・ki盻ノ th盻ｭ fallback, quota, auth, timeout.
- Khﾃｴng g盻絞 m蘯｡ng, khﾃｴng g盻絞 provider th蘯ｭt.
- Khﾃｴng lﾆｰu API key th蘯ｭt.

## Cﾃi ﾄ黛ｺｷt phﾃ｡t tri盻ハ

```bash
python -m pip install -e .[dev]
```

## Ch蘯｡y ki盻ノ th盻ｭ

```bash
python -m pytest -q
python -m compileall src
```

## Vﾃｭ d盻･ nhanh

```python
from nakazasen_ai_router import AIRouter, AIRequest, RouterPolicy
from nakazasen_ai_router.fake_providers import provider_success

router = AIRouter(
    providers=[provider_success("local-demo", is_cloud=False)],
    policy=RouterPolicy(local_only=True),
)

result = router.route(AIRequest(prompt="Xin chﾃo"))
print(result.text)
```

## Cam k蘯ｿt b蘯｣o m蘯ｭt

- Khﾃｴng commit API key th蘯ｭt.
- Log ﾄ柁ｰ盻｣c lﾃm s蘯｡ch ﾄ黛ｻ・trﾃ｡nh l盻・chu盻擁 nh蘯｡y c蘯｣m trong metadata.
- Provider th蘯ｭt s蘯ｽ ﾄ柁ｰ盻｣c thﾃｪm sau, kﾃｨm test riﾃｪng.

## Dﾃｹng trong repo khﾃ｡c

B蘯｡n cﾃｳ th盻・t蘯｡o router nhanh t盻ｫ bi蘯ｿn mﾃｴi trﾆｰ盻拵g, khﾃｴng c蘯ｧn lﾆｰu API key trong code.

Vﾃｭ d盻･ PowerShell:

```powershell
$env:OPENROUTER_API_KEY = "sk-..."
```

Vﾃｭ d盻･ Python:

```python
from nakazasen_ai_router import AIRequest, create_router_from_env

router = create_router_from_env()
result = router.route(AIRequest(prompt="Xin chﾃo"))
print(result.text)
```

Cﾃ｡c bi蘯ｿn mﾃｴi trﾆｰ盻拵g ﾄ疎ng h盻・tr盻｣:

| Provider | Bi蘯ｿn API key | Ghi chﾃｺ |
|---|---|---|
| OpenRouter | `OPENROUTER_API_KEY` | Cloud OpenAI-compatible |
| Groq | `GROQ_API_KEY` | Cloud OpenAI-compatible |
| DeepSeek | `DEEPSEEK_API_KEY` | Cloud OpenAI-compatible |
| NVIDIA NIM | `NVIDIA_NIM_API_KEY` | Cloud OpenAI-compatible |
| ChatAnyWhere | `CHATANYWHERE_API_KEY` | Cloud OpenAI-compatible |
| Mistral | `MISTRAL_API_KEY` | Cloud OpenAI-compatible |
| Local server | `LOCAL_OPENAI_COMPATIBLE_BASE_URL` | Localhost cﾃｳ th盻・khﾃｴng c蘯ｧn key |

Trong test m蘯ｷc ﾄ黛ｻ杵h, d盻ｱ ﾃ｡n v蘯ｫn khﾃｴng g盻絞 internet. App bﾃｪn ngoﾃi nﾃｪn truy盻］ `http_client` th蘯ｭt khi mu盻創 g盻絞 provider th蘯ｭt.

## G盻絞 provider th蘯ｭt

M蘯ｷc ﾄ黛ｻ杵h Nakazasen AI Router **khﾃｴng g盻絞 internet**. `create_router_from_env()` ch盻・d盻ｱng provider b蘯ｱng `_NoNetworkHTTPClient` n蘯ｿu b蘯｡n khﾃｴng truy盻］ transport.

ﾄ雪ｻ・g盻絞 provider th蘯ｭt, caller ph蘯｣i opt-in rﾃｵ rﾃng:

```python
from nakazasen_ai_router import AIRequest, create_router_from_env

router = create_router_from_env(enable_network=True)
result = router.route(AIRequest(prompt="Reply with OK."))
print(result.text)
```

Ho蘯ｷc truy盻］ transport riﾃｪng:

```python
router = create_router_from_env(http_client_factory=my_http_client_factory)
```

Live smoke test cﾅｩng b盻・t蘯ｯt m蘯ｷc ﾄ黛ｻ杵h. Mu盻創 ch蘯｡y th盻ｧ cﾃｴng:

```powershell
$env:RUN_LIVE_AI_TESTS = "1"
$env:OPENROUTER_API_KEY = "sk-..."
py -m pytest tests/test_live_smoke.py -q
```

N蘯ｿu khﾃｴng cﾃｳ `RUN_LIVE_AI_TESTS=1`, test live s蘯ｽ skip. N蘯ｿu b蘯ｭt live nhﾆｰng thi蘯ｿu key, test s蘯ｽ skip thay vﾃｬ fail.
