# 2026年 ValleyRAT / ManageEngine(UEMSAgent) 配布事例まとめ

- 集計元: `daily-news/news/2026_*/*.md` の「malware campaign」欄（日本語マルスパム）
- 集計期間: 2026-01-01 〜 2026-09-25（該当する最終事例は 20260917）
- 件数: 合計 54 件（ValleyRAT 45 件 / ManageEngine(UEMSAgent) 9 件）
- 表記: IOCは元記事の無害化表記（`[.]`、`hxxps`）のまま。「2次:」はメール本文のリンクではなく、実行後にダウンロードされる先
- 日付はtech-memoのファイル名の日付。元投稿の日付とは1日程度ずれる場合がある

| 日付 | 件名 | 種別 | ファイル名 | 配布用URL | C2サーバ | ソースURL |
| --- | --- | --- | --- | --- | --- | --- |
| 20260127 | （記載なし：組織の代表を装う） | ValleyRAT | .zip > .exe（ファイル名記載なし） |  |  | https://x.com/bomccss/status/2015743408179204472 |
| 20260130 | （記載なし：組織の代表を装う） | ValleyRAT |  |  |  | https://x.com/bomccss/status/2016740156213166171 |
| 20260204 | （記載なし） | ValleyRAT | .rar > .exe（ファイル名記載なし） |  |  | https://x.com/bomccss/status/2018531627488719270 |
| 20260213 | （記載なし：Chatwork招待メールを偽装） | ValleyRAT | .zip > .exe（ファイル名記載なし） |  | 38.246.251[.]131:6666 | https://x.com/bomccss/status/2021881807659315415 |
| 20260318 | （記載なし） | ValleyRAT | .iso > .exe（サイドローディング） | hxxps://gofile[.]io/d/nUieLG | 103.210.238[.]29:22011 | https://x.com/bomccss/status/2033839818422292907 |
| 20260319 | <役員名> | ValleyRAT | データレポート.rar > .exe + サイドローディング | hxxps[:]//wwwasdfsafsafas-1393918816.cos.ap-hongkong.myqcloud[.]com/データレポート.rar | 43[.]134[.]7[.]102 | https://x.com/bomccss/status/2034167843319910633 |
| 20260401 | 【重要通知】賞与に関する新着情報があります | ValleyRAT | .zip > .exe + libcef.dll（サイドローディング） |  | 198.44.170[.]58 ／ xjvbn[.]com, ljowqjd[.]cn（役割の記載なし） | https://x.com/bomccss/status/2038876980389818419 |
| 20260425 | 給与および職位名称改定に関する確認の徹底について（重要） | ValleyRAT | 給与および職位改定ならびに給与明細ダウンロードのご案内.gz > 20260422184418.exe + PDFCORE8.dll | hxxps[:]//yindd[.]top/給与および職位改定ならびに給与明細ダウンロードのご案内.gz（添付docからリンク）／2次: hxxps[://]ufeovssir[.]cc:443/20260422184418[.]exe, /PDFCORE8[.]dll | yscf988[.]club (223[.]26[.]62[.]116:7880, 7881) | https://x.com/bomccss/status/2047602469186977840 |
| 20260611 | [組織名] | ValleyRAT | 20260610105308_A07CE5BA525EBBCCF73.zip > .cmd > MicrosoftEdgeUpdate.exe + PDFCore8.dll | hxxps[:]//hrxjp[.]vip/er0L ／2次: hxxps[://]laonashijie-1433552157[.]cos[.]ap-hongkong[.]myqcloud[.]com/ | 43.128.26[.]132:778, 779 | https://x.com/bomccss/status/2064565203610800580 |
| 20260613 | 電子請求書明細書 | ValleyRAT | 20260611121147_A054ED7FCEE0EA7D5A8.zip > .com > MicrosoftEdgeUpdate.exe + pdfcore8.dll | hrxjp[.]vip/er0L ／2次: hxxps[:]//faipa[.]vip/ | 43.128.26[.]132:778, 779 | https://x.com/tdatwja/status/2065249834249163138 |
| 20260709 | 税務コンプライアンス違反及び罰金に関する通知 | ValleyRAT | Tax-Number725863.zip > .img > Tax-Number725863.exe + jli.dll | hxxps[:]//isudcnzy[.]eu[.]cc/d/4a28a94fbf3d | 103.59.103[.]30, 103.12.149[.]93, yk.ggdy[.]com | https://x.com/bomccss/status/2074744392624304304 |
| 20260722 | 税務コンプライアンス違反及び罰金に関する通知 | ValleyRAT | Tax-Number635863.zip > Tax-Number635863.img > Tax-Number635863.exe + jli.dll | hxxps[:]//isudcnzy.eu[.]cc/d/1b78c105d6b8 | 103.59.103[.]30:8888, 6666 ／ yk.ggdy[.]com:8003, 80 | https://x.com/bomccss/status/2079482891785138342 |
| 20260722 | 【重要】契約書添付について | ValleyRAT | 20260721074431.zip > No.20260721074047.IMG > VAT_N0.20260721074047.EXE + pdfcOrE8.dlL | hxxps[:]//morning-cell-6811.nukisora1808.workers[.]dev/ | 134.122.185[.]201:6685, 6698 ／ datusha[.]com[.]cn | https://x.com/bomccss/status/2079483283260535008 |
| 20260722 | 名簿を調整しました。 | ManageEngine(UEMSAgent) | 請求書.zip > setup1.vbs > Lo.zip / UEMSAgent.msi | hxxps[:]//vfvxvbb[.]com/ ／2次: hxxps[:]//jb.mywwjj[.]xyz/sys/A/1/c2b8[.]zip | 202.61.160[.]189:8383 | https://x.com/bomccss/status/2079559037830807925 |
| 20260728 | 只是一封通知邮件<組織名>的来信 | ValleyRAT | J-A20260727022544.zip > .img > Vat.No.20260727022528.EXE + PdFcOrE8.DlL | hxxps[:]//withered-lake-8596.krzakanna172.workers[.]dev/ | haochisadnka[.]cc (134.122.185[.]201:6685, 6698) | https://x.com/bomccss/status/2081672960348475777 |
| 20260731 | 税務コンプライアンス違反及び罰金に関する通知 | ValleyRAT | 20260730141517.zip > VATN0.20260730141511.IMG > .EXE + PdFcOrE8.DlL | hxxps[:]//kaiwyrey.eu[.]cc/d/bdc9637e70c2 | auk218[.]club (118.107.0[.]196:7800, 7811) | https://x.com/tdatwja/status/2082759599690788980 |
| 20260804 | [組織名] - 通知邮件 | ValleyRAT | JP-20260803123248.FDC1EEC62FDB.zip > Vat.N0.20260803123012.IMG > .EXE + PdfcOrE8.dLL | hxxps[:]//dark-silence-5cba.erinbraumbachlianebl.workers[.]dev/ | ljdnxz[.]cc (121.127.253[.]206:8856, 8868) | https://x.com/bomccss/status/2084261863546822943 |
| 20260804 | 【ご請求書】7月分のご確認をお願いいたします | ValleyRAT | mscopilot.exe + PDFCore8.dll（配布ファイル名記載なし） | hxxps[:]//kaiwyrey.eu[.]cc/d/fe93220bfecf/file?code=1082658a8855be82a6859324aef5153d | auk218[.]club (118.107.0[.]196:7800, 7811) | https://x.com/bomccss/status/2084258630598328801 |
| 20260804 | 税務申告不適合及び罰則に関する通知 / 照会番号 NTA/COMP/PEN/2026-083 | ValleyRAT | MSCOPILOT.EXE + pdfCORe8.dLL（配布ファイル名記載なし） | hxxps[:]//kxjbvskdmxbdfgd.pages[.]dev/ | haochisadnka[.]cc (134.122.185[.]201:6685, 6698) | https://x.com/bomccss/status/2084257779481788466 |
| 20260805 | e-Tax 税務署 確定申告書 | ValleyRAT | .zip > tax returns.img > tax returns.exe + taxreturns.dll（AppDomainManager Injection） |  | 204[.]194[.]50[.]231:449 ／ http[://]204[.]194[.]50[.]231/9856.png | https://x.com/tdatwja/status/2084589989367889931 |
| 20260805 | 【請求書】8月分ご請求書の送付について | ValleyRAT | -_2026080451201.zip > Vat.N0.20260804110703.IMG > .EXE + PdfcOrE8.dLL | hijndil-ownguen[.]pages[.]dev | ljdnxz[.]cc | https://x.com/tdatwja/status/2084588468886552914 |
| 20260805 | (楽楽明細)電子インボイス発行完了のお知らせ | ValleyRAT | RKM-20260709-1514.zip > Tax_Notice_34015.img > Tax_Notice_34015.exe + nvml.dll |  | 192.252.180[.]45:6666 | https://x.com/bomccss/status/2084508786782585333 |
| 20260807 | 発注書および在庫確認のお願い（他パターンあり） | ManageEngine(UEMSAgent) | 発注書.pdf > 6ea3d8d0.img > Click to open the file.vbs > UEMSAgent.msi | hxxps[:]//w1mail[.]com（PDF内リンク）／2次: hxxps[:]//agent.jpword[.]cc/setup.pdf | jpword[.]cc:8383 (103.193.172[.]103) ／ 122.10.117[.]3:8383 | https://x.com/bomccss/status/2085371684413227342 |
| 20260811 | 電子インボイス発行完了のお知らせ | ValleyRAT | RKM-20260810-1514.7z > Tax_Notice_90849.img > Tax_Notice_90849.exe + nvml.dll |  | 192.252.180[.]45:6666 ／ 64.81.30[.]192:6666 | https://x.com/bomccss/status/2086685233056043119 |
| 20260819 | 送金内容ご確認のお願い | ManageEngine(UEMSAgent) | PDF.zip > PDF.hta > UEMSAgent.msi | 2次: hxxps[:]//wordtax[.]ink/down/setup.appx (181.214.250[.]206) | jpword[.]cc:8383 (103.193.172[.]103) ／ 122.10.117[.]3:8383 | https://x.com/bomccss/status/2089549526571065346 |
| 20260819 | 電子インボイス発行完了のお知らせ | ValleyRAT | RKM-20260817-3684.zip > Check-Details_f8c8.img > Check-Details.exe + winhttp.dll |  | 207.56.119[.]83:6666 | https://x.com/bomccss/status/2089557077018738924 |
| 20260820 | 電子インボイス発行完了のお知らせ:RKM-20260817-3684 | ValleyRAT | RKM-20260817-3684.7z > Open_to_view_6fe9.img |  | 207.56.119[.]83:6666 | https://x.com/tdatwja/status/2089996616359174472 |
| 20260820 | 【重要】契約書添付について | ManageEngine(UEMSAgent) | HXN20160817021HAN.zip > EX20160817021011121.vbs > UEMSAgent.msi | hsacnajklnsdcm8u[.]pages[.]dev ／2次: hxxps[://]rukeyou[.]com/sys/X2/X2-payload_dfyihao.zip | 134[.]122[.]136[.]84:8383 | https://x.com/tdatwja/status/2089992039144542615 |
| 20260820 | <企業名> - 通知邮件 | ValleyRAT | du-A2026081702100.zip > Number.20260818090851.IMG | toyotechnicaljp[.]pages[.]dev | fshsjlk[.]cc (121.127.253[.]206:8856, 8868) ／ apm[.]hexin[.]cn (58.220.49[.]156:80) | https://x.com/tdatwja/status/2089988933946130695 |
| 20260820 | 【請求書】8月分ご請求書の送付について | ValleyRAT | C57852BA0-2784921-202608\~.zip > TI-No.20260816233301.IMG | hijndil-ownguen[.]pages[.]dev | fshsjlk[.]cc (121.127.253[.]206:8856, 8868) ／ apm[.]hexin[.]cn (58.220.49[.]156:80) | https://x.com/tdatwja/status/2089986367224963283 |
| 20260821 | 請求書発行のお知らせ | ValleyRAT | 請求書 (2).rar > 請求書.img > Loader.exe |  | 204.194.50[.]231:443, 449 | https://x.com/bomccss/status/2090383855962468746 |
| 20260825 | 【請求書】8月分ご請求書の送付について | ValleyRAT | JD09_109_R01000331_202608.zip > CIT-Number.20260824112143.IMG > .EXE + nW_Elf.dLL | hxxps[:]//dnbwr-rtw4u.pages[.]dev | fshsjlk[.]cc (121.127.253[.]206:8856, 8868) | https://x.com/bomccss/status/2091823024131711072 |
| 20260825 | 情報更新など | ValleyRAT | 2026082015837462_pdf.zip > .img > 2026081829618475_setup.exe + vulkan-1.dll |  | 170.62.130[.]47:443, 449 | https://x.com/bomccss/status/2091822824076021954 |
| 20260825 | 【お見積り・お取引のご相談】新規調達に関するお問い合わせ | ValleyRAT | 20260824 2.zip > 20260824*.img（3種）> 20260824.EXE + MSOCF.dll |  | 202.61.140[.]222:448 | https://x.com/bomccss/status/2091722745038221561 |
| 20260826 | [企業名] - 通知邮件 | ValleyRAT | em_2026082302001.zip > I.T.R.Number-20260824231719.IMG > .EXE + arphADump.dll | hxxps://kabereonjp.pages[.]dev（同系統: hxxps[:]//dnbwr-rtw4u.pages[.]dev） | fshsjlk[.]cc (121.127.253[.]206:8856, 8868) | https://x.com/bomccss/status/2092189322523091071 |
| 20260826 | 電子インボイス発行完了のお知らせ | ValleyRAT | RKM-20260709-1514.7z > Open_to_view_*.img > Open_to_view.exe + winhttp.dll |  | cicfo[.]com (202.146.222[.]95:6666) ／ 202.146.222[.]95:443 | https://x.com/tdatwja/status/2092165335088783857 |
| 20260827 | （記載なし：検体1） | ValleyRAT |  |  | cicfo[.]com (202.146.222[.]95:6666, 443) | https://x.com/bomccss/status/2092518189704032722 |
| 20260827 | （記載なし：検体2） | ValleyRAT |  |  | fshsjlk[.]cc (121.127.253[.]206:8856, 8868) | https://x.com/bomccss/status/2092518189704032722 |
| 20260827 | （記載なし：検体3） | ValleyRAT |  |  | 202.61.140[.]222:448 | https://x.com/bomccss/status/2092518189704032722 |
| 20260827 | （記載なし：検体4。検体1と同じtria.ge参照） | ValleyRAT |  |  | cicfo[.]com (202.146.222[.]95:6666, 443) | https://x.com/bomccss/status/2092518189704032722 |
| 20260828 | 支払い状況のお知らせ：振込が完了しました | ManageEngine(UEMSAgent) | 123.PDF4.zip > 123.PDF4.hta > UEMS Agent | 2次: hxxps[:]//www.rumail[.]cc/down/setup.appx (181.214.250[.]174) | jpword[.]cc:8383 (103.193.172[.]103) ／ 122.10.117[.]3:8383 | https://x.com/bomccss/status/2092945776871874952 |
| 20260828 | 【請求書】8月分ご請求書の送付について | ValleyRAT | FEI99106_20260824_165000\~.zip > I.T.R.Number-20260824231559.IMG > .EXE + arphADump.dll | hxxp[:]//hijndil-ownguen-an8.pages[.]dev | fshsjlk[.]cc (121.127.253[.]206:8856, 8868) | https://x.com/bomccss/status/2092865125552394560 |
| 20260901 | 電子インボイス発行完了のお知らせ | ValleyRAT | RKM-20260831-1514.zip > Open_to_view_38ab.img > Open_to_view.exe + winhttp.dll |  | cicfo[.]com (202.146.222[.]95:6666) ／ 202.146.222[.]95:443 | https://x.com/bomccss/status/2094365484737311169 |
| 20260901 | 請求書発行完了のお知らせ | ValleyRAT | 20260828.52178.DAC85C35C1.zip > .img > .exe + service.dll |  | 170.62.130[.]47:443, 449 | https://x.com/bomccss/status/2094361471887237347 |
| 20260901 | 資金の振込が完了しましたので、ご確認ください（他パターンあり） | ManageEngine(UEMSAgent) | 123.pdf9.zip > 123.pdf9.hta |  | jpword[.]cc:8383 | https://x.com/tdatwja/status/2094356131061932417 |
| 20260902 | 税務関連資料ご確認のお願 | ValleyRAT | 税務調査.zip > 税務調査.img > 税務調査.exe + heif.dll |  | 204.194.50[.]231:443, 449 | https://x.com/bomccss/status/2094706091389268471 |
| 20260903 | 【全社通知】給与改定および人事異動について | ValleyRAT | 人事異動に伴う給与調整.zip > .img > 人事異動に伴う給与調整.exe + libcares-2.dll |  | 204.194.50[.]231:443, 449 | https://x.com/bomccss/status/2094968760641970444 |
| 20260904 | 【新規お取引およびお見積りご依頼の件】<企業名> ／ 【全社通知】給与改定および人事異動について | ValleyRAT | 購買リスト.zip（人事異動に伴う給与調整.zip）> 購買リスト.img > 購買リスト.exe + libcares-2.dll |  | 204[.]194[.]50[.]231:443, 449 | https://x.com/tdatwja/status/2095400419853996542 |
| 20260908 | 電子インボイス発行完了のお知らせ | ValleyRAT | RKM-20260904-1514.7z > Open_to_view_f4d1.img > Open_to_view.exe + winhttp.dll |  | 202.146.222[.]95:443 | https://x.com/bomccss/status/2096865276533080401 |
| 20260909 | 令和8年度 第3四半期 税務関連資料および確認清单（チェックリスト）のご送付 [受付番号：2609018653] | ValleyRAT | 税務報告書.zip > 税務報告書.img > 税務報告書.exe + FileReportEx.dll |  | 14.128.53[.]155:443, 449 | https://x.com/bomccss/status/2097149249226203236 |
| 20260910 | 【国税庁・重要通知】法人税務資料確認清单のご案内(要PC確認・令和8年9月14日期限) | ValleyRAT | 税務報告書.zip > 税務報告書.img > 税務報告書.exe + FileReportEx.dll |  | 14[.]128[.]53[.]155:443, 449 | https://x.com/tdatwja/status/2097620482115952828 |
| 20260916 | 振込処理が正常に完了しましたので、入金をご確認ください | ManageEngine(UEMSAgent) | PDF INV 20260913 v02.zip > E_INV_20260913_v02.vhd > E_INV_20260913_v02.hta | 2次: hxxps[:]//dnswwt[.]club/down/file.zip (181.214.250[.]174) | inword[.]club / 156.245.245[.]223:8383 | https://x.com/bomccss/status/2099746747514011969 |
| 20260916 | 【結婚式のご招待】 | ManageEngine(UEMSAgent) | 結婚式のご招待.zip > 結婚式のご招待.vhdx > 結婚式のご招待.hta | 2次: hxxps[:]//dnswwt[.]club/down/setup.aac (181.214.250[.]174) | jpword[.]cc:8383 (122.10.117[.]3) | https://x.com/bomccss/status/2099745072027947391 |
| 20260917 | （記載なし：複数事例のまとめ） | ManageEngine(UEMSAgent) | （記載なし。.hta SHA256 a42a573e…） | 2次（配布サーバ）: ssmail[.]ink, dnswwt[.]club | inword[.]club / 156.245.245[.]223:8833 | https://x.com/tdatwja/status/2100138202166415386 |

## 集計対象外にしたもの

- 20260213-2（件名: 人事異動ならびに給与改定のお知らせ、c2: gbedn[.]fit:9887）、20260319-1（件名: 電子請求書発行のお知らせ）: マルウェア名の記載がないため除外
- 20260709-1: VenomRATのため除外
- 20260801: DonutLoader（同梱されたtorブラウザがValleyRATと判定されたという記載のみ）のため除外
- 20260910-2: RMM悪用だがAskLinkのため除外
- 「日々のニュース要約」欄のベンダーレポート（例: 20260205 LINE偽装ValleyRAT、20260404 伊藤忠C&Iレポート、20260525 偽Teams、20260624 Kaspersky ManageEngine悪用、20260905 日本向けValleyRAT動向など）は個別の配布観測ではないため除外
