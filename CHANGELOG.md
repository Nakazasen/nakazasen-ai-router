# Changelog

## 0.1.0 - Kh逶ｻ谿・t陂ｯ・｡o

- T陂ｯ・｡o repo Python cho Nakazasen AI Router.
- Th・・ｽｪm API router t逶ｻ險ｴ thi逶ｻ繝・
- Th・・ｽｪm provider gi陂ｯ・｣ l陂ｯ・ｭp cho success, quota fail, auth fail, timeout.
- Th・・ｽｪm test fallback, cooldown quota, disable auth, local_only, v・・｣ｰ kh・・ｽｴng log API key.

## 0.3.0 - Provider Registry v・・｣ｰ env config

- Th・・ｽｪm Provider Registry cho OpenRouter, Groq, DeepSeek, NVIDIA NIM, ChatAnyWhere, Mistral v・・｣ｰ local OpenAI-compatible.
- Th・・ｽｪm `create_router_from_env()` ・・ｻ幢ｽｻ繝ｻt陂ｯ・｡o router t逶ｻ・ｫ bi陂ｯ・ｿn m・・ｽｴi tr・・ｽｰ逶ｻ諡ｵg.
- Cloud provider kh・・ｽｴng c・・ｽｳ API key s陂ｯ・ｽ b逶ｻ繝ｻb逶ｻ繝ｻqua.
- Local OpenAI-compatible c・・ｽｳ th逶ｻ繝ｻch陂ｯ・｡y kh・・ｽｴng c陂ｯ・ｧn key n陂ｯ・ｿu d・・ｽｹng localhost/127.0.0.1.
- Test m陂ｯ・ｷc ・・ｻ幢ｽｻ譚ｵh v陂ｯ・ｫn mock-first, kh・・ｽｴng g逶ｻ邨・internet v・・｣ｰ kh・・ｽｴng c陂ｯ・ｧn API key th陂ｯ・ｭt.

## 0.4.0 - Optional network transport v・・｣ｰ live smoke test

- Th・・ｽｪm `UrllibHTTPClient` d・・ｽｹng Python standard library ・・ｻ幢ｽｻ繝ｻg逶ｻ邨・provider th陂ｯ・ｭt khi caller opt-in.
- `create_router_from_env(enable_network=True)` m逶ｻ螫・d・・ｽｹng transport th陂ｯ・ｭt; m陂ｯ・ｷc ・・ｻ幢ｽｻ譚ｵh v陂ｯ・ｫn kh・・ｽｴng g逶ｻ邨・internet.
- Th・・ｽｪm live smoke test t・・ｽｹy ch逶ｻ閧ｱ, skip m陂ｯ・ｷc ・・ｻ幢ｽｻ譚ｵh n陂ｯ・ｿu kh・・ｽｴng c・・ｽｳ `RUN_LIVE_AI_TESTS=1`.
- Kh・・ｽｴng y・・ｽｪu c陂ｯ・ｧu API key th陂ｯ・ｭt cho test m陂ｯ・ｷc ・・ｻ幢ｽｻ譚ｵh.

## 0.1.0 - Internal release preparation

- Thﾃｪm script live smoke an toﾃn ﾄ黛ｻ・ki盻ノ tra provider th蘯ｭt b蘯ｱng key n蘯ｱm ngoﾃi repo.
- Xﾃ｡c minh lu盻渡g g盻絞 th蘯ｭt cﾃｳ ki盻ノ soﾃ｡t qua transport opt-in.
- Chu蘯ｩn b盻・tag n盻冓 b盻・`v0.1.0` sau khi unit test, packaging, secret scan vﾃ live smoke pass.
