# Nakazasen AI Router

Nakazasen AI Router l繝ｻ繝ｻ・｣・ｰ n騾ｶ・ｻ繝ｻ・ｽ m繝ｻ繝ｻ・ｽ・ｳng Python 繝ｻ繝ｻ・ｻ蟷｢・ｽ・ｻ郢晢ｽｻ繝ｻ繝ｻ・ｨ・ｴ騾ｶ・ｻ邵ｲ繝ｻph騾ｶ・ｻ髫ｪ・ｴ nhi騾ｶ・ｻ邵ｲ繝ｻnh繝ｻ繝ｻ・｣・ｰ cung c髯ゑｽｯ繝ｻ・･p AI trong t繝ｻ繝ｻ・ｽ・ｰ繝ｻ繝ｻ・ｽ・｡ng lai.

騾ｶ・ｻ郢晢ｽｻphi繝ｻ繝ｻ・ｽ・ｪn b髯ゑｽｯ繝ｻ・｣n hi騾ｶ・ｻ郢ｻ・ｻ t髯ゑｽｯ繝ｻ・｡i, d騾ｶ・ｻ繝ｻ・ｱ 繝ｻ繝ｻ・ｽ・｡n **ch繝ｻ繝ｻ・ｽ・ｰa g騾ｶ・ｻ驍ｨ繝ｻAI th髯ゑｽｯ繝ｻ・ｭt** v繝ｻ繝ｻ・｣・ｰ **kh繝ｻ繝ｻ・ｽ・ｴng ch騾ｶ・ｻ繝ｻ・ｩa API key th髯ゑｽｯ繝ｻ・ｭt**. M騾ｶ・ｻ繝ｻ・･c ti繝ｻ繝ｻ・ｽ・ｪu l繝ｻ繝ｻ・｣・ｰ chu髯ゑｽｯ繝ｻ・ｩn b騾ｶ・ｻ郢晢ｽｻc髯ゑｽｯ繝ｻ・･u tr繝ｻ繝ｻ・ｽ・ｺc s髯ゑｽｯ繝ｻ・｡ch 繝ｻ繝ｻ・ｻ蟷｢・ｽ・ｻ郢晢ｽｻsau n繝ｻ繝ｻ・｣・ｰy port Provider Router t騾ｶ・ｻ繝ｻ・ｫ `translation_app` sang.

## Tr髯ゑｽｯ繝ｻ・｡ng th繝ｻ繝ｻ・ｽ・｡i hi騾ｶ・ｻ郢ｻ・ｻ t髯ゑｽｯ繝ｻ・｡i

- API t騾ｶ・ｻ髫ｪ・ｴ thi騾ｶ・ｻ郢昴・ `AIRouter`, `AIRequest`, `AIResult`, `ProviderBase`, `ProviderCandidate`, `ProviderHealth`, `RouterPolicy`.
- Provider gi髯ゑｽｯ繝ｻ・｣ l髯ゑｽｯ繝ｻ・ｭp 繝ｻ繝ｻ・ｻ蟷｢・ｽ・ｻ郢晢ｽｻki騾ｶ・ｻ郢昴・th騾ｶ・ｻ繝ｻ・ｭ fallback, quota, auth, timeout.
- Kh繝ｻ繝ｻ・ｽ・ｴng g騾ｶ・ｻ驍ｨ繝ｻm髯ゑｽｯ繝ｻ・｡ng, kh繝ｻ繝ｻ・ｽ・ｴng g騾ｶ・ｻ驍ｨ繝ｻprovider th髯ゑｽｯ繝ｻ・ｭt.
- Kh繝ｻ繝ｻ・ｽ・ｴng l繝ｻ繝ｻ・ｽ・ｰu API key th髯ゑｽｯ繝ｻ・ｭt.

## C繝ｻ繝ｻ・｣・ｰi 繝ｻ繝ｻ・ｻ蟷｢・ｽ・ｺ繝ｻ・ｷt ph繝ｻ繝ｻ・ｽ・｡t tri騾ｶ・ｻ郢昴・
```bash
python -m pip install -e .[dev]
```

## Ch髯ゑｽｯ繝ｻ・｡y ki騾ｶ・ｻ郢昴・th騾ｶ・ｻ繝ｻ・ｭ

```bash
python -m pytest -q
python -m compileall src
```

## V繝ｻ繝ｻ・ｽ・ｭ d騾ｶ・ｻ繝ｻ・･ nhanh

```python
from nakazasen_ai_router import AIRouter, AIRequest, RouterPolicy
from nakazasen_ai_router.fake_providers import provider_success

router = AIRouter(
    providers=[provider_success("local-demo", is_cloud=False)],
    policy=RouterPolicy(local_only=True),
)

result = router.route(AIRequest(prompt="Xin ch繝ｻ繝ｻ・｣・ｰo"))
print(result.text)
```

## Cam k髯ゑｽｯ繝ｻ・ｿt b髯ゑｽｯ繝ｻ・｣o m髯ゑｽｯ繝ｻ・ｭt

- Kh繝ｻ繝ｻ・ｽ・ｴng commit API key th髯ゑｽｯ繝ｻ・ｭt.
- Log 繝ｻ繝ｻ豌医・・ｰ騾ｶ・ｻ繝ｻ・｣c l繝ｻ繝ｻ・｣・ｰm s髯ゑｽｯ繝ｻ・｡ch 繝ｻ繝ｻ・ｻ蟷｢・ｽ・ｻ郢晢ｽｻtr繝ｻ繝ｻ・ｽ・｡nh l騾ｶ・ｻ郢晢ｽｻchu騾ｶ・ｻ隰ｫ繝ｻnh髯ゑｽｯ繝ｻ・｡y c髯ゑｽｯ繝ｻ・｣m trong metadata.
- Provider th髯ゑｽｯ繝ｻ・ｭt s髯ゑｽｯ繝ｻ・ｽ 繝ｻ繝ｻ豌医・・ｰ騾ｶ・ｻ繝ｻ・｣c th繝ｻ繝ｻ・ｽ・ｪm sau, k繝ｻ繝ｻ・ｽ・ｨm test ri繝ｻ繝ｻ・ｽ・ｪng.

## D繝ｻ繝ｻ・ｽ・ｹng trong repo kh繝ｻ繝ｻ・ｽ・｡c

B髯ゑｽｯ繝ｻ・｡n c繝ｻ繝ｻ・ｽ・ｳ th騾ｶ・ｻ郢晢ｽｻt髯ゑｽｯ繝ｻ・｡o router nhanh t騾ｶ・ｻ繝ｻ・ｫ bi髯ゑｽｯ繝ｻ・ｿn m繝ｻ繝ｻ・ｽ・ｴi tr繝ｻ繝ｻ・ｽ・ｰ騾ｶ・ｻ隲｡・ｵg, kh繝ｻ繝ｻ・ｽ・ｴng c髯ゑｽｯ繝ｻ・ｧn l繝ｻ繝ｻ・ｽ・ｰu API key trong code.

V繝ｻ繝ｻ・ｽ・ｭ d騾ｶ・ｻ繝ｻ・･ PowerShell:

```powershell
$env:OPENROUTER_API_KEY = "<api-key>"
```

V繝ｻ繝ｻ・ｽ・ｭ d騾ｶ・ｻ繝ｻ・･ Python:

```python
from nakazasen_ai_router import AIRequest, create_router_from_env

router = create_router_from_env()
result = router.route(AIRequest(prompt="Xin ch繝ｻ繝ｻ・｣・ｰo"))
print(result.text)
```

C繝ｻ繝ｻ・ｽ・｡c bi髯ゑｽｯ繝ｻ・ｿn m繝ｻ繝ｻ・ｽ・ｴi tr繝ｻ繝ｻ・ｽ・ｰ騾ｶ・ｻ隲｡・ｵg 繝ｻ繝ｻ魄ｪng h騾ｶ・ｻ郢晢ｽｻtr騾ｶ・ｻ繝ｻ・｣:

| Provider | Bi髯ゑｽｯ繝ｻ・ｿn API key | Ghi ch繝ｻ繝ｻ・ｽ・ｺ |
|---|---|---|
| OpenRouter | `OPENROUTER_API_KEY` | Cloud OpenAI-compatible |
| Groq | `GROQ_API_KEY` | Cloud OpenAI-compatible |
| DeepSeek | `DEEPSEEK_API_KEY` | Cloud OpenAI-compatible |
| NVIDIA NIM | `NVIDIA_NIM_API_KEY` | Cloud OpenAI-compatible |
| ChatAnyWhere | `CHATANYWHERE_API_KEY` | Cloud OpenAI-compatible |
| Mistral | `MISTRAL_API_KEY` | Cloud OpenAI-compatible |
| Local server | `LOCAL_OPENAI_COMPATIBLE_BASE_URL` | Localhost c繝ｻ繝ｻ・ｽ・ｳ th騾ｶ・ｻ郢晢ｽｻkh繝ｻ繝ｻ・ｽ・ｴng c髯ゑｽｯ繝ｻ・ｧn key |

Trong test m髯ゑｽｯ繝ｻ・ｷc 繝ｻ繝ｻ・ｻ蟷｢・ｽ・ｻ隴夲ｽｵh, d騾ｶ・ｻ繝ｻ・ｱ 繝ｻ繝ｻ・ｽ・｡n v髯ゑｽｯ繝ｻ・ｫn kh繝ｻ繝ｻ・ｽ・ｴng g騾ｶ・ｻ驍ｨ繝ｻinternet. App b繝ｻ繝ｻ・ｽ・ｪn ngo繝ｻ繝ｻ・｣・ｰi n繝ｻ繝ｻ・ｽ・ｪn truy騾ｶ・ｻ繝ｻ・ｽ `http_client` th髯ゑｽｯ繝ｻ・ｭt khi mu騾ｶ・ｻ陷托ｽｵ g騾ｶ・ｻ驍ｨ繝ｻprovider th髯ゑｽｯ繝ｻ・ｭt.

## G騾ｶ・ｻ驍ｨ繝ｻprovider th髯ゑｽｯ繝ｻ・ｭt

M髯ゑｽｯ繝ｻ・ｷc 繝ｻ繝ｻ・ｻ蟷｢・ｽ・ｻ隴夲ｽｵh Nakazasen AI Router **kh繝ｻ繝ｻ・ｽ・ｴng g騾ｶ・ｻ驍ｨ繝ｻinternet**. `create_router_from_env()` ch騾ｶ・ｻ郢晢ｽｻd騾ｶ・ｻ繝ｻ・ｱng provider b髯ゑｽｯ繝ｻ・ｱng `_NoNetworkHTTPClient` n髯ゑｽｯ繝ｻ・ｿu b髯ゑｽｯ繝ｻ・｡n kh繝ｻ繝ｻ・ｽ・ｴng truy騾ｶ・ｻ繝ｻ・ｽ transport.

繝ｻ繝ｻ螯帙・・ｻ郢晢ｽｻg騾ｶ・ｻ驍ｨ繝ｻprovider th髯ゑｽｯ繝ｻ・ｭt, caller ph髯ゑｽｯ繝ｻ・｣i opt-in r繝ｻ繝ｻ・ｽ・ｵ r繝ｻ繝ｻ・｣・ｰng:

```python
from nakazasen_ai_router import AIRequest, create_router_from_env

router = create_router_from_env(enable_network=True)
result = router.route(AIRequest(prompt="Reply with OK."))
print(result.text)
```

Ho髯ゑｽｯ繝ｻ・ｷc truy騾ｶ・ｻ繝ｻ・ｽ transport ri繝ｻ繝ｻ・ｽ・ｪng:

```python
router = create_router_from_env(http_client_factory=my_http_client_factory)
```

Live smoke test c繝ｻ繝ｻ・ｽ・ｩng b騾ｶ・ｻ郢晢ｽｻt髯ゑｽｯ繝ｻ・ｯt m髯ゑｽｯ繝ｻ・ｷc 繝ｻ繝ｻ・ｻ蟷｢・ｽ・ｻ隴夲ｽｵh. Mu騾ｶ・ｻ陷托ｽｵ ch髯ゑｽｯ繝ｻ・｡y th騾ｶ・ｻ繝ｻ・ｧ c繝ｻ繝ｻ・ｽ・ｴng:

```powershell
$env:RUN_LIVE_AI_TESTS = "1"
$env:OPENROUTER_API_KEY = "<api-key>"
py -m pytest tests/test_live_smoke.py -q
```

N髯ゑｽｯ繝ｻ・ｿu kh繝ｻ繝ｻ・ｽ・ｴng c繝ｻ繝ｻ・ｽ・ｳ `RUN_LIVE_AI_TESTS=1`, test live s髯ゑｽｯ繝ｻ・ｽ skip. N髯ゑｽｯ繝ｻ・ｿu b髯ゑｽｯ繝ｻ・ｭt live nh繝ｻ繝ｻ・ｽ・ｰng thi髯ゑｽｯ繝ｻ・ｿu key, test s髯ゑｽｯ繝ｻ・ｽ skip thay v繝ｻ繝ｻ・ｽ・ｬ fail.

## Live smoke test v逶ｻ螫・key th陂ｯ・ｭt

Live smoke test ch逶ｻ繝ｻd・・ｽｹng khi b陂ｯ・｡n ch逶ｻ・ｧ ・・ｻ幢ｽｻ蜀｢g ki逶ｻ繝・tra provider th陂ｯ・ｭt. Kh・・ｽｴng commit API key v・・｣ｰ n・・ｽｪn ・・ｻ幢ｽｻ繝ｻfile key n陂ｯ・ｱm ngo・・｣ｰi repo.

V・・ｽｭ d逶ｻ・･:

```powershell
py scripts/live_smoke.py --provider openrouter --key-file "D:\path\to\API Key.txt"
```

Script h逶ｻ繝ｻtr逶ｻ・｣ c・・ｽ｡c provider: `openrouter`, `groq`, `deepseek`, `nvidia_nim`, `chatanywhere`, `mistral`.

File key c・・ｽｳ th逶ｻ繝ｻd・・ｽｹng d陂ｯ・｡ng bi陂ｯ・ｿn m・・ｽｴi tr・・ｽｰ逶ｻ諡ｵg:

```text
OPENROUTER_API_KEY=
```

Ho陂ｯ・ｷc nh・・ｽ｣n provider r逶ｻ螯ｬ key 逶ｻ繝ｻd・・ｽｲng sau. Script ch逶ｻ繝ｻ・・ｻ幢ｽｻ逧・trong b逶ｻ繝ｻnh逶ｻ繝ｻ ・・ｻ幢ｽｺ・ｷt bi陂ｯ・ｿn m・・ｽｴi tr・・ｽｰ逶ｻ諡ｵg t陂ｯ・｡m trong process, v・・｣ｰ ch逶ｻ繝ｻin provider/status/model/text preview an to・・｣ｰn. Kh・・ｽｴng in API key.

## Strategy `live_free_first`

Sau Gate 6, strategy `live_free_first` ﾆｰu tiﾃｪn cﾃ｡c provider ﾄ妥｣ live PASS trﾆｰ盻嫩 vﾃ ﾄ黛ｺｩy provider quota/l盻擁 xu盻創g sau:

1. `deepseek`
2. `nvidia_nim`
3. `chatanywhere`
4. `mistral`
5. `openrouter`
6. `groq`

Vﾃｭ d盻･:

```python
from nakazasen_ai_router import create_router_from_env

router = create_router_from_env(strategy="live_free_first", enable_network=True)
```

Strategy nﾃy ch盻・quy蘯ｿt ﾄ黛ｻ杵h th盻ｩ t盻ｱ provider. Nﾃｳ khﾃｴng t盻ｱ b蘯ｭt internet n蘯ｿu b蘯｡n khﾃｴng truy盻］ `enable_network=True` ho蘯ｷc `http_client_factory`.

Cﾃｳ th盻・ch蘯｡y smoke toﾃn b盻・provider theo th盻ｩ t盻ｱ nﾃy:

```powershell
py scripts/live_smoke.py --provider all --key-file "D:\path\to\API Key.txt" --stop-on-first-pass
```

Ghi chﾃｺ hi盻㌻ t蘯｡i: OpenRouter cﾃｳ th盻・b盻・quota/rate limit. Groq n蘯ｿu cﾃｲn l盻擁 nﾃｪn ﾄ黛ｻ皇 `error_type`, `status_code` vﾃ message ﾄ妥｣ sanitize t盻ｫ script, khﾃｴng debug b蘯ｱng cﾃ｡ch in key/header/raw response.
