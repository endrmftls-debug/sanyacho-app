# -*- coding: utf-8 -*-
"""도감: 독초, 버섯(모두 '먹지 마세요'), 기타."""

MUSHROOM_NOTE = "버섯은 사진만으로 먹을 수 있는지 판단할 수 없어 이 앱은 버섯을 항상 '먹지 마세요'로 표시해요."

ENTRIES = [
dict(id="veratrum", ko="박새·여로류", aka=["박새", "여로", "참여로", "흰여로"], sci="Veratrum spp.", fam="멜란티움과", v="deadly", months=[],
     sum="산마늘(명이)·원추리·비비추 어린잎과 헷갈리는 맹독 식물이에요.",
     look=["잎이 줄기를 감싸며 여러 장 촘촘히 어긋나게 층층이 달림", "나란한 잎맥을 따라 세로 주름이 깊음", "여로는 잎에 털, 줄기 밑동이 그물 같은 섬유에 싸임", "마늘 냄새가 전혀 없음"],
     where="높은 산 숲·풀밭, 습한 곳",
     tox=dict(part="전체(특히 뿌리)", sym="구토, 어지러움, 맥박이 느려짐, 혈압 저하, 심하면 의식을 잃을 수 있어요."),
     like=[["allium_victorialis", "산마늘은 한 포기에 잎이 2~3장이고 마늘 향이 진해요."], ["hemerocallis", "원추리는 잎이 매끈하고 부채처럼 두 줄로 포개져요."], ["hosta", "비비추는 잎마다 긴 잎자루가 있어요."]]),

dict(id="caltha", ko="동의나물", aka=["입금화"], sci="Caltha palustris", fam="미나리아재비과", v="toxic", months=[],
     sum="곰취와 헷갈리는 독초. 물가·습지에서 자라요.",
     look=["둥근 심장(콩팥) 모양 잎이 두껍고 반짝임", "톱니가 둔하고 잎끝이 둥긂", "향이 없음", "4~5월 노란 꽃(꽃잎 5~6장)"],
     where="산골짜기 물가·습지",
     tox=dict(part="전체(특히 뿌리)", sym="구토, 복통, 설사, 피부·입 점막 자극."),
     like=[["ligularia", "곰취는 향이 좋고, 잎이 부드럽고 광택이 없으며 톱니가 뾰족해요."]]),

dict(id="convallaria", ko="은방울꽃", aka=["오월화"], sci="Convallaria majalis var. keiskei", fam="비짜루과", v="deadly", months=[],
     sum="산마늘·둥굴레와 잎이 닮은 맹독 식물. 심장에 작용하는 독이 있어요.",
     look=["땅에서 넓은 잎 2장이 서로 감싸며 나옴", "잎이 두껍고 뻣뻣하며 냄새가 없음", "5월 작은 흰 방울꽃이 한쪽으로 줄지어 매달림", "가을 빨간 열매"],
     where="산기슭 숲 가장자리",
     tox=dict(part="전체(뿌리·꽃·열매)", sym="구토, 메스꺼움, 부정맥, 심하면 급성 심부전으로 사망할 수 있어요."),
     like=[["allium_victorialis", "산마늘은 잎을 비비면 진한 마늘 향이 나요."], ["polygonatum", "둥굴레는 휘어진 줄기 하나에 잎이 여러 장 어긋나요."]]),

dict(id="phytolacca", ko="자리공류 (미국자리공)", aka=["미국자리공", "자리공"], sci="Phytolacca spp.", fam="자리공과", v="toxic", months=[],
     sum="뿌리를 더덕·도라지·인삼으로 착각해 먹는 사고가 잦은 독초예요.",
     look=["키 1~2m, 굵고 자주색인 줄기", "크고 넓은 타원형 잎", "여름 흰 꽃이삭 → 검보라 포도알 같은 열매송이(즙이 진한 자주색)", "뿌리가 매끈하고 주름이 없으며 향이 없음"],
     where="빈터·길가·산기슭",
     tox=dict(part="뿌리, 열매, 씨", sym="구토, 복통, 설사, 심하면 경련."),
     like=[["codonopsis", "더덕 뿌리는 가로 주름이 많고 향이 진하며 자르면 흰 즙이 나와요."], ["platycodon", "도라지 뿌리는 자르면 흰 즙이 나와요."]]),

dict(id="cicuta", ko="독미나리", aka=[], sci="Cicuta virosa", fam="미나리과", v="deadly", months=[],
     sum="미나리와 닮은 맹독 식물. 조금만 먹어도 경련을 일으키고 생명이 위험해요.",
     look=["물가·습지, 키 1m 안팎으로 큼", "잎이 2~3번 갈라지고 가장자리 톱니가 깊음(식약처)", "굵은 뿌리줄기를 자르면 속이 칸칸이 나뉘어 있음"],
     where="습지·연못가·도랑",
     tox=dict(part="전체(특히 뿌리줄기)", sym="구토, 경련, 의식 소실, 사망까지 이를 수 있어요."),
     like=[["oenanthe", "미나리는 키가 작고 잎 가장자리 톱니가 얕아요."]]),

dict(id="conium", ko="나도독미나리", aka=["독당근", "독인삼"], sci="Conium maculatum", fam="미나리과", v="deadly", months=[],
     sum="전호·당근 잎과 닮은 맹독 식물이에요.",
     look=["줄기가 매끈하고 속이 비며 붉은·자주색 얼룩 반점", "잎이 레이스처럼 잘게 갈라짐", "비비면 쥐오줌 같은 불쾌한 냄새", "흰 꽃이 우산 모양으로"],
     where="빈터·길가·물가",
     tox=dict(part="전체", sym="마비, 호흡 곤란, 사망까지 이를 수 있어요."),
     like=[["anthriscus", "전호는 줄기에 잔털이 있고 붉은 얼룩이 없어요."]]),

dict(id="angelica_toxic", ko="개구릿대·지리강활", aka=["개구릿대", "지리강활"], sci="Angelica anomala · A. purpuraefolia", fam="미나리과", v="deadly", months=[],
     sum="참당귀와 헷갈리는 독초예요. 지리강활은 특히 독성이 강해요.",
     look=["참당귀처럼 잎이 크게 갈라짐", "개구릿대는 갈라진 작은잎이 서로 떨어져 있음(산림청)", "꽃이 흰색(참당귀는 자주색)"],
     where="산골짜기",
     tox=dict(part="전체(특히 뿌리)", sym="구토, 경련 등 심한 중독."),
     like=[["angelica_gigas", "참당귀는 갈라진 작은잎이 밑에서 서로 이어져 있고 자주색 꽃이 피며 향이 진해요."]]),

dict(id="aconitum", ko="투구꽃·초오류", aka=["투구꽃", "놋젓가락나물", "진범", "초오"], sci="Aconitum spp.", fam="미나리아재비과", v="deadly", months=[],
     sum="투구 모양 보라 꽃. 뿌리(초오)는 사약 재료로 쓰이던 맹독이에요.",
     look=["잎이 손바닥처럼 3~5갈래로 깊게 갈라지고 다시 갈라짐", "가을 투구 모양 보라색(종류에 따라 노랑·흰) 꽃", "덩이뿌리"],
     where="산 숲 가장자리",
     tox=dict(part="전체(특히 뿌리)", sym="입·혀 저림, 구토, 부정맥, 호흡 마비, 사망. 초오로 담근 술 중독 사고가 있었어요."),
     like=[]),

dict(id="arisaema", ko="천남성류", aka=["천남성", "둥근잎천남성", "큰천남성"], sci="Arisaema spp.", fam="천남성과", v="toxic", months=[],
     sum="코브라 머리 같은 꽃. 덩이줄기가 감자처럼 보이지만 사약 재료로 쓰인 독초예요.",
     look=["잎 1~2장이 작은잎 여러 장으로 손바닥처럼 갈라짐", "줄기에 얼룩무늬", "5월 녹색·자주 줄무늬 덮개 꽃", "가을 옥수수처럼 빽빽한 빨간 열매송이"],
     where="산 숲 그늘",
     tox=dict(part="전체(덩이줄기·열매)", sym="입과 목이 타는 듯 아프고 부어오르며, 숨쉬기 어려울 수 있어요."),
     warn=["빨간 열매도 먹으면 안 돼요."]),

dict(id="pinellia", ko="반하", aka=["끼무릇"], sci="Pinellia ternata", fam="천남성과", v="toxic", months=[],
     sum="작은 천남성 친척. 덩이줄기 날것은 독이에요.",
     look=["잎자루 끝에 작은잎 3장", "잎자루 중간에 살눈", "가늘고 긴 녹색 덮개 꽃"],
     where="밭·들",
     tox=dict(part="덩이줄기 날것", sym="입과 목이 심하게 아리고 부어요.")),

dict(id="paris", ko="삿갓나물", aka=[], sci="Paris verticillata", fam="멜란티움과", v="toxic", months=[],
     sum="우산나물과 헷갈리는 독초예요.",
     look=["줄기 끝에 갈라지지 않은 통짜 잎 6~8장이 돌려남", "잎 가장자리에 톱니가 없음", "가운데에서 꽃 1송이, 열매는 검은 보라"],
     where="산 숲 그늘",
     tox=dict(part="전체(특히 뿌리·열매)", sym="구토, 복통, 설사, 두통."),
     like=[["syneilesis", "우산나물은 잎이 깊게 갈라지고 다시 갈라지며 톱니가 있어요."]]),

dict(id="farfugium", ko="털머위", aka=["말곰취"], sci="Farfugium japonicum", fam="국화과", v="toxic", months=[],
     sum="머위와 비슷한 남부 바닷가·섬의 늘푸른 독초예요.",
     look=["잎이 두껍고 윤기가 반짝, 겨울에도 푸름", "어린잎·잎자루에 갈색 털", "잎자루가 붉은빛", "가을 노란 꽃"],
     where="남부 해안·섬",
     tox=dict(part="전체", sym="간을 해치는 알칼로이드 성분이 있어요."),
     like=[["petasites", "머위는 겨울에 잎이 없고, 봄에 나는 잎이 얇고 부드러워요."]]),

dict(id="corydalis", ko="현호색·괴불주머니류", aka=["산괴불주머니", "현호색", "자주괴불주머니"], sci="Corydalis spp.", fam="양귀비과", v="toxic", months=[],
     sum="쑥·전호 어린잎과 헷갈리는 봄 독초예요.",
     look=["잎이 잘게 갈라지고 연한 녹색", "잎 앞뒤가 매끈하고 쑥 향이 없음", "봄에 긴 통 모양 꽃(산괴불주머니 노랑, 현호색 보라)"],
     where="산기슭·숲 가장자리",
     tox=dict(part="전체", sym="구토, 복통, 어지러움 등."),
     like=[["artemisia", "쑥은 잎 뒷면이 흰 털로 희끗하고 쑥 향이 나요."]]),

dict(id="amana", ko="산자고", aka=["까치무릇"], sci="Amana edulis", fam="백합과", v="toxic", months=[],
     sum="달래와 헷갈리는 봄 독초. 튤립을 닮은 흰 꽃이 피어요.",
     look=["잎 2장이 길고 넓적한 띠 모양(달래보다 넓음)", "냄새가 없음", "4월 자주색 줄이 있는 흰 꽃잎 6장", "달걀 모양 비늘줄기"],
     where="양지바른 산기슭",
     tox=dict(part="전체(특히 비늘줄기)", sym="구토, 설사 등. 식약처가 주의 독초로 꼽아요."),
     like=[["allium_monanthum", "달래는 파·마늘 냄새가 확실히 나요."]]),

dict(id="thalictrum", ko="꿩의다리류", aka=["꿩의다리", "산꿩의다리"], sci="Thalictrum spp.", fam="미나리아재비과", v="toxic", months=[],
     sum="잎이 작게 여러 번 갈라지는 독초예요.",
     look=["작고 둥근 잎이 3장씩 2~3번 갈라짐", "여름 실 같은 흰·연보라 꽃(꽃잎 대신 수술이 눈에 띔)"],
     where="산 풀밭·숲 가장자리",
     tox=dict(part="전체", sym="구토, 위장 장애.")),

dict(id="scopolia", ko="미치광이풀", aka=[], sci="Scopolia japonica", fam="가지과", v="deadly", months=[],
     sum="먹으면 미친 듯이 날뛴다는 이름의 맹독 식물이에요.",
     look=["이른 봄 숲속 습한 곳에 연한 잎이 부드럽게 퍼짐", "4~5월 자주색 종 모양 꽃이 잎겨드랑이에 하나씩 매달림"],
     where="깊은 산 계곡 숲",
     tox=dict(part="전체(특히 뿌리)", sym="동공 확대, 환각, 흥분, 빠른 맥박, 입 마름, 심하면 혼수.")),

dict(id="datura", ko="독말풀류", aka=["독말풀", "흰독말풀"], sci="Datura spp.", fam="가지과", v="deadly", months=[],
     sum="큰 나팔 모양 꽃, 가시 많은 열매. 전체가 맹독이에요.",
     look=["큰 흰색·연보라 나팔 모양 꽃", "가시가 많은 둥근 열매"], where="빈터·길가·밭",
     tox=dict(part="전체(특히 씨)", sym="환각, 착란, 동공 확대, 고열, 혼수.")),

dict(id="pulsatilla", ko="할미꽃류", aka=["할미꽃", "동강할미꽃"], sci="Pulsatilla spp.", fam="미나리아재비과", v="toxic", months=[],
     sum="흰 털에 덮인 고개 숙인 자주색 꽃. 전체에 독이 있어요.",
     look=["식물 전체가 흰 털로 덮임", "4월 고개 숙인 검붉은 자주색 꽃", "꽃 진 뒤 흰 털 뭉치(할머니 머리)"], where="양지바른 무덤가·산기슭",
     tox=dict(part="전체", sym="즙이 피부·입 점막을 자극(물집), 먹으면 구토·설사.")),

dict(id="chelidonium", ko="애기똥풀", aka=[], sci="Chelidonium majus var. asiaticum", fam="양귀비과", v="toxic", months=[],
     sum="줄기를 자르면 노란 즙(아기 똥 색)이 나와요. 먹으면 안 돼요.",
     look=["줄기·잎을 자르면 노란 즙", "잎이 깃처럼 갈라지고 뒷면이 흰빛", "노란 꽃잎 4장"], where="길가·숲 가장자리",
     tox=dict(part="전체", sym="구토, 복통, 간 손상이 보고됐어요.")),

dict(id="ranunculus", ko="미나리아재비류", aka=["미나리아재비", "개구리자리", "젓가락나물"], sci="Ranunculus spp.", fam="미나리아재비과", v="toxic", months=[],
     sum="반짝이는 노란 꽃. 즙이 피부를 자극하고 먹으면 안 돼요.",
     look=["노란 꽃잎 5장이 기름을 바른 듯 반짝임", "잎이 손바닥처럼 갈라짐"], where="들·물가·논둑",
     tox=dict(part="전체", sym="입과 위장 자극, 피부 물집.")),

dict(id="clematis", ko="으아리류", aka=["으아리", "사위질빵", "할미밀망"], sci="Clematis spp.", fam="미나리아재비과", v="toxic", months=[],
     sum="흰·보라 꽃의 덩굴. 즙이 피부를 자극해요.",
     look=["덩굴, 잎자루가 덩굴손처럼 감김", "꽃잎처럼 보이는 꽃받침 4~6장", "열매에 깃털 같은 긴 꼬리"], where="산기슭·숲 가장자리",
     tox=dict(part="전체", sym="피부 물집, 먹으면 위장 장애.")),

dict(id="aristolochia", ko="쥐방울덩굴", aka=["말방울"], sci="Aristolochia contorta", fam="쥐방울덩굴과", v="toxic", months=[],
     sum="나팔 모양 꽃의 덩굴. 신장을 해치는 성분이 있어요.",
     look=["덩굴, 하트 모양 잎", "구부러진 나팔 모양 꽃", "쥐방울 같은 둥근 열매"], where="산기슭·들",
     tox=dict(part="전체", sym="아리스톨로크산이 신장을 손상시키고 암을 일으킬 수 있어요.")),

dict(id="euphorbia", ko="대극류", aka=["대극", "개감수", "땅빈대"], sci="Euphorbia spp.", fam="대극과", v="toxic", months=[],
     sum="줄기를 자르면 흰 유액이 나와요. 피부·눈을 자극하고 먹으면 독이에요.",
     look=["잎·줄기를 자르면 흰 즙", "녹황색 작은 술잔 모양 꽃"], where="산기슭·밭·길가",
     tox=dict(part="전체(유액)", sym="피부 염증, 눈에 들어가면 위험, 먹으면 심한 구토·설사."),
     like=[["portulaca", "쇠비름은 줄기를 꺾어도 흰 즙이 나오지 않아요."]]),

dict(id="symplocarpus", ko="앉은부채", aka=["삿부채"], sci="Symplocarpus renifolius", fam="천남성과", v="toxic", months=[],
     sum="이른 봄 습지에서 눈을 녹이며 나오는 자주색 덮개 꽃. 큰 잎이 나물처럼 보여도 먹으면 안 돼요.",
     look=["2~3월 땅에 붙어 자주색 껍데기 같은 꽃", "꽃 진 뒤 큰 하트 모양 잎이 무더기로"], where="산골짜기 습지",
     tox=dict(part="전체", sym="입·목의 심한 통증과 붓기, 구토.")),

dict(id="dictamnus", ko="백선", aka=["봉삼(잘못된 이름)"], sci="Dictamnus dasycarpus", fam="운향과", v="toxic", months=[],
     sum="독특한 냄새의 풀. 즙이 묻은 채 햇볕을 쬐면 화상 같은 물집이 생겨요.",
     look=["깃 모양 겹잎", "5~6월 연분홍 꽃에 진한 줄무늬", "강한 냄새"], where="산기슭 양지",
     tox=dict(part="전체", sym="피부 물집(빛에 반응), 뿌리 껍질 복용 시 간 손상 보고.")),

dict(id="solanum_nigrum", ko="까마중", aka=["깜뚜라지"], sci="Solanum nigrum", fam="가지과", v="toxic", months=[],
     sum="흰 꽃, 까만 작은 열매. 덜 익은 열매와 잎에 독(솔라닌)이 있어요.",
     look=["작은 흰 꽃(노란 수술)", "콩알만 한 열매가 초록에서 검게 익음"], where="밭·길가",
     tox=dict(part="덜 익은 열매, 잎", sym="구토, 설사, 복통, 어지러움."),
     warn=["잘 익은 열매를 먹던 풍습도 있지만 비슷한 종과 구별이 어려워 권하지 않아요."]),

dict(id="adonis", ko="복수초", aka=["얼음새꽃"], sci="Adonis amurensis", fam="미나리아재비과", v="deadly", months=[],
     sum="이른 봄 눈 속에서 피는 노란 꽃. 심장에 작용하는 독이 있어요.",
     look=["2~3월 지름 3~4cm 노란 꽃이 잎보다 먼저", "잎이 잘게 갈라진 깃 모양"], where="산 숲 속",
     tox=dict(part="전체", sym="구토, 부정맥, 심하면 심장이 멈출 수 있어요.")),

dict(id="lycoris", ko="상사화·석산류", aka=["상사화", "석산", "꽃무릇"], sci="Lycoris spp.", fam="수선화과", v="toxic", months=[],
     sum="잎과 꽃이 따로 나는 상사화·꽃무릇. 알뿌리에 독이 있어요.",
     look=["상사화는 봄에 길쭉한 띠 모양 잎", "잎이 진 뒤 꽃대만 올라와 분홍(상사화)·빨강(석산) 꽃", "냄새가 없음"], where="절 주변·산기슭",
     tox=dict(part="전체(특히 알뿌리)", sym="구토, 설사, 침 흘림, 심하면 경련."),
     like=[["allium_victorialis", "산마늘·달래·산부추는 비비면 마늘·파 냄새가 나요."]]),

# ---------------- 버섯: 모두 '먹지 마세요' ----------------
dict(id="amanita", ko="광대버섯류", aka=["독우산광대버섯", "개나리광대버섯", "마귀광대버섯", "달걀버섯"], sci="Amanita spp.", fam="광대버섯과", v="mushroom", danger="deadly", months=[],
     sum="국내 버섯 중독 사망의 주범(독우산광대버섯·개나리광대버섯)이 속한 무리예요. 식용 달걀버섯도 같은 무리라 구별이 극히 위험해요.",
     look=["대부분 갓 아래 주름이 흰색", "대에 턱받이(치마)", "밑동에 주머니(대주머니)"], where="여름~가을 숲 바닥",
     tox=dict(part="전체", sym="독우산·개나리광대버섯(아마톡신): 6~24시간 뒤 구토·설사, 잠깐 나아진 듯하다 간·신장이 손상돼 사망할 수 있어요. 마귀광대버섯: 신경 증상."),
     warn=["증상이 늦게 나타나 괜찮다고 착각하기 쉬워요. 먹었다면 증상이 없어도 바로 병원으로."]),

dict(id="trichoderma", ko="붉은사슴뿔버섯", aka=[], sci="Trichoderma cornu-damae", fam="점버섯과", v="mushroom", danger="deadly", months=[],
     sum="붉은 손가락·사슴뿔 모양. 만지기만 해도 피부염, 먹으면 치명적이에요. 어린 영지와 헷갈리는 사고가 있어요.",
     look=["주황~붉은색 손가락 또는 사슴뿔 모양", "썩은 참나무 그루터기 주변"], where="여름~가을 활엽수림",
     tox=dict(part="전체", sym="트리코테신 독소. 적은 양으로도 사망할 수 있어요."),
     warn=["맨손으로 만지지 마세요."]),

dict(id="omphalotus", ko="화경버섯", aka=["화경솔밭버섯"], sci="Omphalotus guepiniiformis", fam="화경버섯과", v="mushroom", danger="toxic", months=[],
     sum="느타리·표고와 닮은 독버섯. 어두운 곳에서 주름이 희미하게 빛나요.",
     look=["죽은 활엽수(너도밤나무·서어나무 등)에 겹쳐 남", "갓이 자갈색", "갓과 대가 만나는 부분 살에 검은 얼룩"], where="여름~가을 고목",
     tox=dict(part="전체", sym="먹고 30분~1시간 뒤 구토·설사·복통.")),

dict(id="hypholoma_fasciculare", ko="노란다발", aka=[], sci="Hypholoma fasciculare", fam="포도버섯과", v="mushroom", danger="toxic", months=[],
     sum="식용 개암버섯과 닮은 독버섯. 그루터기에 다발로 나요.",
     look=["갓이 등황색~녹황색", "주름이 황색~녹황색(개암버섯은 황갈~자갈색)", "쓴맛"], where="봄~가을 활엽수 그루터기",
     tox=dict(part="전체", sym="메스꺼움, 구토, 설사, 단백뇨, 경우에 따라 마비·시력 손상(농촌진흥청)."),
     like=[["hypholoma_lateritium", "개암버섯은 갓이 황갈~적갈색에 비늘 조각이 있어요. 그래도 구별은 전문가 영역이에요."]]),

dict(id="entoloma", ko="외대버섯류", aka=["삿갓외대버섯"], sci="Entoloma spp.", fam="외대버섯과", v="mushroom", danger="toxic", months=[],
     sum="분홍빛 주름의 외대버섯 무리. 중독 사고가 잦아요.",
     look=["주름이 자라면서 분홍빛을 띰"], where="여름~가을 숲",
     tox=dict(part="전체", sym="구토, 설사, 복통.")),

dict(id="gymnopilus", ko="갈황색미치광이버섯", aka=[], sci="Gymnopilus junonius", fam="턱받이포도버섯과", v="mushroom", danger="toxic", months=[],
     sum="주황빛 큰 버섯이 그루터기에 다발로. 먹으면 환각·흥분이 와요.",
     look=["주황~황갈색 큰 갓", "그루터기에 다발로"], where="여름~가을 고목",
     tox=dict(part="전체", sym="어지러움, 환각, 흥분.")),

dict(id="tricholoma_matsutake", ko="송이", aka=["송이버섯"], sci="Tricholoma matsutake", fam="송이과", v="mushroom", danger="info", months=[],
     sum="소나무 숲의 귀한 식용버섯이에요. 하지만 닮은 버섯이 있어 사진만으로 판단하면 안 돼요.",
     look=["갓이 갈색이고 굵은 흰 대", "특유의 진한 향"], where="가을 소나무 숲",
     warn=["송이 채취는 산주·산림조합 허가 대상이에요. 무단 채취는 불법이에요."]),

dict(id="sarcodon", ko="능이", aka=["향버섯"], sci="Sarcodon aspratus", fam="노루털버섯과", v="mushroom", danger="info", months=[],
     sum="갓 위에 거친 비늘, 갓 아래에 주름 대신 바늘이 있는 버섯이에요.",
     look=["깔때기 모양 갓에 거친 비늘", "갓 아래가 가시(바늘) 모양"], where="가을 참나무 숲",
     warn=["날로 먹으면 중독될 수 있어요."]),

dict(id="lentinula", ko="표고", aka=["표고버섯"], sci="Lentinula edodes", fam="낙엽버섯과", v="mushroom", danger="info", months=[],
     sum="참나무 고목에 나는 버섯. 독버섯 화경버섯과 헷갈릴 수 있어요.",
     look=["갓 위에 흰 비늘 조각", "참나무 고목"], where="봄·가을 고목",
     like=[["omphalotus", "화경버섯은 갓과 대 사이 살에 검은 얼룩이 있고 어두운 곳에서 빛나요."]],
     warn=["덜 익힌 표고를 먹으면 채찍 모양 발진(표고 피부염)이 생길 수 있어요."]),

dict(id="pleurotus", ko="느타리류", aka=["느타리", "산느타리"], sci="Pleurotus spp.", fam="느타리과", v="mushroom", danger="info", months=[],
     sum="활엽수 고목에 겹쳐 나는 회색~흰 버섯. 화경버섯·외대버섯류와 헷갈려요.",
     look=["조개껍데기 모양 갓이 겹쳐 남", "대가 짧고 한쪽으로 치우침"], where="고목",
     like=[["omphalotus", "화경버섯은 어두운 곳에서 빛나고 대 부분 살에 검은 얼룩이 있어요."]]),

dict(id="ramaria", ko="싸리버섯류", aka=["싸리버섯", "노랑싸리버섯"], sci="Ramaria spp.", fam="나팔버섯과", v="mushroom", danger="toxic", months=[],
     sum="산호처럼 갈라진 버섯. 먹는 종류와 독이 있는 종류(노랑싸리버섯 등)가 섞여 있어 구별이 어려워요.",
     look=["산호·빗자루처럼 여러 갈래"], where="가을 숲 바닥",
     tox=dict(part="독성 종류", sym="구토, 설사.")),

dict(id="ganoderma", ko="영지류", aka=["영지", "불로초"], sci="Ganoderma spp.", fam="불로초과", v="mushroom", danger="info", months=[],
     sum="딱딱하고 광택 나는 갓의 약용버섯. 어린 붉은사슴뿔버섯을 영지 새싹으로 착각한 사고가 있었어요.",
     look=["딱딱한 나무질, 니스 칠한 듯 반짝이는 갓"], where="여름~가을 활엽수 그루터기",
     like=[["trichoderma", "붉은사슴뿔버섯은 손가락 모양의 붉은 버섯으로 만지기만 해도 위험해요."]],
     warn=["먹는 버섯이 아니라 달여 쓰는 약재예요."]),

dict(id="cantharellus", ko="꾀꼬리버섯류", aka=["꾀꼬리버섯"], sci="Cantharellus spp.", fam="꾀꼬리버섯과", v="mushroom", danger="info", months=[],
     sum="살구색 깔때기 모양 버섯. 주름이 칼날 같지 않고 낮은 맥 모양이에요.",
     look=["노랑~살구색 깔때기", "갓 아래가 낮은 주름맥"], where="여름~가을 숲 바닥"),

dict(id="hericium", ko="노루궁뎅이", aka=[], sci="Hericium erinaceus", fam="산호침버섯과", v="mushroom", danger="info", months=[],
     sum="흰 털 뭉치(고슴도치) 모양 버섯. 활엽수에 나요.",
     look=["흰 바늘이 아래로 늘어진 털 뭉치 모양"], where="가을 활엽수"),

dict(id="auricularia", ko="목이류", aka=["목이", "털목이"], sci="Auricularia spp.", fam="목이과", v="mushroom", danger="info", months=[],
     sum="귀 모양의 젤리 같은 버섯. 죽은 나무에 나요.",
     look=["귀 모양, 말랑한 젤리 질감"], where="봄~가을 죽은 활엽수"),

dict(id="armillaria", ko="뽕나무버섯류", aka=["뽕나무버섯", "뽕나무버섯부치"], sci="Armillaria spp.", fam="뽕나무버섯과", v="mushroom", danger="info", months=[],
     sum="그루터기에 다발로 나는 갈색 버섯. 날로 먹으면 중독돼요.",
     look=["갈색 갓, 다발", "대에 턱받이"], where="가을 그루터기",
     warn=["독버섯(노란다발 등)과 섞여 나기도 해요."]),

dict(id="hypholoma_lateritium", ko="개암버섯", aka=["밤버섯"], sci="Hypholoma lateritium", fam="포도버섯과", v="mushroom", danger="info", months=[],
     sum="그루터기에 다발로 나는 버섯. 독버섯 노란다발과 매우 비슷해 위험해요.",
     look=["갓이 황갈~적갈색에 오돌토돌한 비늘 조각", "주름이 황갈~자갈색"], where="가을 활엽수 그루터기",
     like=[["hypholoma_fasciculare", "노란다발은 갓·주름이 노랗거나 녹황색이에요."]]),

# ---------------- 기타 ----------------
dict(id="other_plant", ko="도감에 없는 식물", aka=[], sci="", fam="", v="other", months=[],
     sum="이 앱의 도감에 없는 식물이거나 AI가 무엇인지 확실히 모르는 식물이에요. 먹지 마세요."),
dict(id="other_fungi", ko="도감에 없는 버섯", aka=[], sci="", fam="", v="mushroom", danger="info", months=[],
     sum="이 앱의 도감에 없는 버섯이에요. 먹지 마세요."),
]
