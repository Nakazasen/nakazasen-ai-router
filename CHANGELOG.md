# Changelog

## 0.1.0 - Kh騾ｶ・ｻ隹ｿ繝ｻt髯ゑｽｯ繝ｻ・｡o

- T髯ゑｽｯ繝ｻ・｡o repo Python cho Nakazasen AI Router.
- Th繝ｻ繝ｻ・ｽ・ｪm API router t騾ｶ・ｻ髫ｪ・ｴ thi騾ｶ・ｻ郢昴・
- Th繝ｻ繝ｻ・ｽ・ｪm provider gi髯ゑｽｯ繝ｻ・｣ l髯ゑｽｯ繝ｻ・ｭp cho success, quota fail, auth fail, timeout.
- Th繝ｻ繝ｻ・ｽ・ｪm test fallback, cooldown quota, disable auth, local_only, v繝ｻ繝ｻ・｣・ｰ kh繝ｻ繝ｻ・ｽ・ｴng log API key.

## 0.3.0 - Provider Registry v繝ｻ繝ｻ・｣・ｰ env config

- Th繝ｻ繝ｻ・ｽ・ｪm Provider Registry cho OpenRouter, Groq, DeepSeek, NVIDIA NIM, ChatAnyWhere, Mistral v繝ｻ繝ｻ・｣・ｰ local OpenAI-compatible.
- Th繝ｻ繝ｻ・ｽ・ｪm `create_router_from_env()` 繝ｻ繝ｻ・ｻ蟷｢・ｽ・ｻ郢晢ｽｻt髯ゑｽｯ繝ｻ・｡o router t騾ｶ・ｻ繝ｻ・ｫ bi髯ゑｽｯ繝ｻ・ｿn m繝ｻ繝ｻ・ｽ・ｴi tr繝ｻ繝ｻ・ｽ・ｰ騾ｶ・ｻ隲｡・ｵg.
- Cloud provider kh繝ｻ繝ｻ・ｽ・ｴng c繝ｻ繝ｻ・ｽ・ｳ API key s髯ゑｽｯ繝ｻ・ｽ b騾ｶ・ｻ郢晢ｽｻb騾ｶ・ｻ郢晢ｽｻqua.
- Local OpenAI-compatible c繝ｻ繝ｻ・ｽ・ｳ th騾ｶ・ｻ郢晢ｽｻch髯ゑｽｯ繝ｻ・｡y kh繝ｻ繝ｻ・ｽ・ｴng c髯ゑｽｯ繝ｻ・ｧn key n髯ゑｽｯ繝ｻ・ｿu d繝ｻ繝ｻ・ｽ・ｹng localhost/127.0.0.1.
- Test m髯ゑｽｯ繝ｻ・ｷc 繝ｻ繝ｻ・ｻ蟷｢・ｽ・ｻ隴夲ｽｵh v髯ゑｽｯ繝ｻ・ｫn mock-first, kh繝ｻ繝ｻ・ｽ・ｴng g騾ｶ・ｻ驍ｨ繝ｻinternet v繝ｻ繝ｻ・｣・ｰ kh繝ｻ繝ｻ・ｽ・ｴng c髯ゑｽｯ繝ｻ・ｧn API key th髯ゑｽｯ繝ｻ・ｭt.

## 0.4.0 - Optional network transport v繝ｻ繝ｻ・｣・ｰ live smoke test

- Th繝ｻ繝ｻ・ｽ・ｪm `UrllibHTTPClient` d繝ｻ繝ｻ・ｽ・ｹng Python standard library 繝ｻ繝ｻ・ｻ蟷｢・ｽ・ｻ郢晢ｽｻg騾ｶ・ｻ驍ｨ繝ｻprovider th髯ゑｽｯ繝ｻ・ｭt khi caller opt-in.
- `create_router_from_env(enable_network=True)` m騾ｶ・ｻ陞ｫ繝ｻd繝ｻ繝ｻ・ｽ・ｹng transport th髯ゑｽｯ繝ｻ・ｭt; m髯ゑｽｯ繝ｻ・ｷc 繝ｻ繝ｻ・ｻ蟷｢・ｽ・ｻ隴夲ｽｵh v髯ゑｽｯ繝ｻ・ｫn kh繝ｻ繝ｻ・ｽ・ｴng g騾ｶ・ｻ驍ｨ繝ｻinternet.
- Th繝ｻ繝ｻ・ｽ・ｪm live smoke test t繝ｻ繝ｻ・ｽ・ｹy ch騾ｶ・ｻ髢ｧ・ｱ, skip m髯ゑｽｯ繝ｻ・ｷc 繝ｻ繝ｻ・ｻ蟷｢・ｽ・ｻ隴夲ｽｵh n髯ゑｽｯ繝ｻ・ｿu kh繝ｻ繝ｻ・ｽ・ｴng c繝ｻ繝ｻ・ｽ・ｳ `RUN_LIVE_AI_TESTS=1`.
- Kh繝ｻ繝ｻ・ｽ・ｴng y繝ｻ繝ｻ・ｽ・ｪu c髯ゑｽｯ繝ｻ・ｧu API key th髯ゑｽｯ繝ｻ・ｭt cho test m髯ゑｽｯ繝ｻ・ｷc 繝ｻ繝ｻ・ｻ蟷｢・ｽ・ｻ隴夲ｽｵh.

## 0.1.0 - Internal release preparation

- Th・・ｽｪm script live smoke an to・・｣ｰn ・・ｻ幢ｽｻ繝ｻki逶ｻ繝・tra provider th陂ｯ・ｭt b陂ｯ・ｱng key n陂ｯ・ｱm ngo・・｣ｰi repo.
- X・・ｽ｡c minh lu逶ｻ貂｡g g逶ｻ邨・th陂ｯ・ｭt c・・ｽｳ ki逶ｻ繝・so・・ｽ｡t qua transport opt-in.
- Chu陂ｯ・ｩn b逶ｻ繝ｻtag n逶ｻ蜀・b逶ｻ繝ｻ`v0.1.0` sau khi unit test, packaging, secret scan v・・｣ｰ live smoke pass.

## Gate 7 - Live provider strategy stabilization

- Thﾃｪm strategy `live_free_first` v盻嬖 th盻ｩ t盻ｱ: DeepSeek, NVIDIA NIM, ChatAnyWhere, Mistral, OpenRouter, Groq.
- Thﾃｪm `create_live_free_first_router_from_env()` lﾃm wrapper ti盻㌻ d盻･ng.
- C蘯ｭp nh蘯ｭt live smoke script h盻・tr盻｣ `--provider all` vﾃ `--stop-on-first-pass`.
- Live smoke bﾃ｡o l盻擁 an toﾃn hﾆ｡n: `error_type`, `status_code`, model vﾃ message ﾄ妥｣ rﾃｺt g盻肱/sanitize.
- Gi盻ｯ m蘯ｷc ﾄ黛ｻ杵h khﾃｴng g盻絞 internet n蘯ｿu chﾆｰa opt-in `enable_network=True`.
