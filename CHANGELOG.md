# Changelog

## 0.1.0 - Kh盻殃 t蘯｡o

- T蘯｡o repo Python cho Nakazasen AI Router.
- Thﾃｪm API router t盻訴 thi盻ブ.
- Thﾃｪm provider gi蘯｣ l蘯ｭp cho success, quota fail, auth fail, timeout.
- Thﾃｪm test fallback, cooldown quota, disable auth, local_only, vﾃ khﾃｴng log API key.

## 0.3.0 - Provider Registry vﾃ env config

- Thﾃｪm Provider Registry cho OpenRouter, Groq, DeepSeek, NVIDIA NIM, ChatAnyWhere, Mistral vﾃ local OpenAI-compatible.
- Thﾃｪm `create_router_from_env()` ﾄ黛ｻ・t蘯｡o router t盻ｫ bi蘯ｿn mﾃｴi trﾆｰ盻拵g.
- Cloud provider khﾃｴng cﾃｳ API key s蘯ｽ b盻・b盻・qua.
- Local OpenAI-compatible cﾃｳ th盻・ch蘯｡y khﾃｴng c蘯ｧn key n蘯ｿu dﾃｹng localhost/127.0.0.1.
- Test m蘯ｷc ﾄ黛ｻ杵h v蘯ｫn mock-first, khﾃｴng g盻絞 internet vﾃ khﾃｴng c蘯ｧn API key th蘯ｭt.

## 0.4.0 - Optional network transport vﾃ live smoke test

- Thﾃｪm `UrllibHTTPClient` dﾃｹng Python standard library ﾄ黛ｻ・g盻絞 provider th蘯ｭt khi caller opt-in.
- `create_router_from_env(enable_network=True)` m盻嬖 dﾃｹng transport th蘯ｭt; m蘯ｷc ﾄ黛ｻ杵h v蘯ｫn khﾃｴng g盻絞 internet.
- Thﾃｪm live smoke test tﾃｹy ch盻肱, skip m蘯ｷc ﾄ黛ｻ杵h n蘯ｿu khﾃｴng cﾃｳ `RUN_LIVE_AI_TESTS=1`.
- Khﾃｴng yﾃｪu c蘯ｧu API key th蘯ｭt cho test m蘯ｷc ﾄ黛ｻ杵h.
