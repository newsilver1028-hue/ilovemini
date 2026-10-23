import 'dart:convert';
import 'package:flutter/material.dart';

final vehicleBrandCatalog = (jsonDecode(
            r'''[{"name": "현대", "group": "국산", "models": [{"name": "아반떼", "generations": []}, {"name": "쏘나타", "generations": []}, {"name": "그랜저", "generations": []}, {"name": "엑센트", "generations": []}, {"name": "베르나", "generations": []}, {"name": "클릭", "generations": []}, {"name": "i10", "generations": []}, {"name": "i20", "generations": []}, {"name": "i30", "generations": []}, {"name": "i40", "generations": []}, {"name": "아이오닉", "generations": []}, {"name": "아슬란", "generations": []}, {"name": "에쿠스", "generations": []}, {"name": "제네시스(현대)", "generations": []}, {"name": "제네시스 쿠페", "generations": []}, {"name": "벨로스터", "generations": []}, {"name": "투스카니", "generations": []}, {"name": "티뷰론", "generations": []}, {"name": "스쿠프", "generations": []}, {"name": "포니", "generations": []}, {"name": "엑셀", "generations": []}, {"name": "엘란트라", "generations": []}, {"name": "스텔라", "generations": []}, {"name": "마르샤", "generations": []}, {"name": "다이너스티", "generations": []}, {"name": "아토스", "generations": []}, {"name": "베뉴", "generations": []}, {"name": "코나", "generations": []}, {"name": "투싼", "generations": []}, {"name": "싼타페", "generations": []}, {"name": "팰리세이드", "generations": []}, {"name": "넥쏘", "generations": []}, {"name": "베라크루즈", "generations": []}, {"name": "테라칸", "generations": []}, {"name": "갤로퍼", "generations": []}, {"name": "아이오닉 5", "generations": []}, {"name": "아이오닉 6", "generations": []}, {"name": "아이오닉 9", "generations": []}, {"name": "스타리아", "generations": []}, {"name": "스타렉스", "generations": []}, {"name": "그레이스", "generations": []}, {"name": "트라제 XG", "generations": []}, {"name": "라비타", "generations": []}, {"name": "포터", "generations": []}, {"name": "리베로", "generations": []}, {"name": "카운티", "generations": []}, {"name": "마이티", "generations": []}, {"name": "메가트럭", "generations": []}, {"name": "파비스", "generations": []}, {"name": "엑시언트", "generations": []}, {"name": "쏠라티", "generations": []}]}, {"name": "제네시스", "group": "국산", "models": [{"name": "G70", "generations": []}, {"name": "G80", "generations": []}, {"name": "G90", "generations": []}, {"name": "EQ900", "generations": []}, {"name": "GV60", "generations": []}, {"name": "GV70", "generations": []}, {"name": "GV80", "generations": []}]}, {"name": "기아", "group": "국산", "models": [{"name": "모닝", "generations": []}, {"name": "레이", "generations": []}, {"name": "프라이드", "generations": []}, {"name": "리오", "generations": []}, {"name": "K3", "generations": []}, {"name": "K4", "generations": []}, {"name": "K5", "generations": []}, {"name": "K7", "generations": []}, {"name": "K8", "generations": []}, {"name": "K9", "generations": []}, {"name": "포르테", "generations": []}, {"name": "쎄라토", "generations": []}, {"name": "스펙트라", "generations": []}, {"name": "세피아", "generations": []}, {"name": "크레도스", "generations": []}, {"name": "옵티마", "generations": []}, {"name": "로체", "generations": []}, {"name": "스팅어", "generations": []}, {"name": "엔터프라이즈", "generations": []}, {"name": "오피러스", "generations": []}, {"name": "포텐샤", "generations": []}, {"name": "슈마", "generations": []}, {"name": "엘란", "generations": []}, {"name": "비스토", "generations": []}, {"name": "캐피탈", "generations": []}, {"name": "콩코드", "generations": []}, {"name": "스토닉", "generations": []}, {"name": "셀토스", "generations": []}, {"name": "니로", "generations": []}, {"name": "스포티지", "generations": []}, {"name": "쏘렌토", "generations": []}, {"name": "모하비", "generations": []}, {"name": "쏘울", "generations": []}, {"name": "텔루라이드", "generations": []}, {"name": "타스만", "generations": []}, {"name": "록스타", "generations": []}, {"name": "레토나", "generations": []}, {"name": "EV3", "generations": []}, {"name": "EV4", "generations": []}, {"name": "EV5", "generations": []}, {"name": "EV6", "generations": []}, {"name": "EV9", "generations": []}, {"name": "카니발", "generations": []}, {"name": "카렌스", "generations": []}, {"name": "카스타", "generations": []}, {"name": "PV5", "generations": []}, {"name": "봉고", "generations": []}, {"name": "프레지오", "generations": []}, {"name": "베스타", "generations": []}, {"name": "타우너", "generations": []}, {"name": "그랜버드", "generations": []}]}, {"name": "쉐보레", "group": "국산", "models": [{"name": "스파크", "generations": []}, {"name": "아베오", "generations": []}, {"name": "크루즈", "generations": []}, {"name": "말리부", "generations": []}, {"name": "임팔라", "generations": []}, {"name": "카마로", "generations": []}, {"name": "콜벳", "generations": []}, {"name": "볼트 EV", "generations": []}, {"name": "볼트 EUV", "generations": []}, {"name": "볼트(Volt)", "generations": []}, {"name": "트랙스", "generations": []}, {"name": "트레일블레이저", "generations": []}, {"name": "이쿼녹스", "generations": []}, {"name": "트래버스", "generations": []}, {"name": "타호", "generations": []}, {"name": "서버번", "generations": []}, {"name": "블레이저", "generations": []}, {"name": "콜로라도", "generations": []}, {"name": "실버라도", "generations": []}]}, {"name": "GM대우·대우", "group": "국산", "models": [{"name": "마티즈", "generations": []}, {"name": "티코", "generations": []}, {"name": "젠트라", "generations": []}, {"name": "칼로스", "generations": []}, {"name": "라세티", "generations": []}, {"name": "누비라", "generations": []}, {"name": "라노스", "generations": []}, {"name": "르망", "generations": []}, {"name": "씨에로", "generations": []}, {"name": "넥시아", "generations": []}, {"name": "에스페로", "generations": []}, {"name": "레간자", "generations": []}, {"name": "매그너스", "generations": []}, {"name": "토스카", "generations": []}, {"name": "프린스", "generations": []}, {"name": "브로엄", "generations": []}, {"name": "슈퍼살롱", "generations": []}, {"name": "로얄", "generations": []}, {"name": "스테이츠맨", "generations": []}, {"name": "베리타스", "generations": []}, {"name": "G2X", "generations": []}, {"name": "윈스톰", "generations": []}, {"name": "레조", "generations": []}, {"name": "다마스", "generations": []}, {"name": "라보", "generations": []}]}, {"name": "르노코리아·르노삼성", "group": "국산", "models": [{"name": "SM3", "generations": []}, {"name": "SM5", "generations": []}, {"name": "SM6", "generations": []}, {"name": "SM7", "generations": []}, {"name": "QM3", "generations": []}, {"name": "QM5", "generations": []}, {"name": "QM6", "generations": []}, {"name": "XM3", "generations": []}, {"name": "아르카나", "generations": []}, {"name": "그랑 콜레오스", "generations": []}]}, {"name": "KG모빌리티·쌍용", "group": "국산", "models": [{"name": "티볼리", "generations": []}, {"name": "코란도", "generations": []}, {"name": "렉스턴", "generations": []}, {"name": "토레스", "generations": []}, {"name": "액티언", "generations": []}, {"name": "무쏘", "generations": []}, {"name": "카이런", "generations": []}, {"name": "체어맨", "generations": []}, {"name": "로디우스", "generations": []}, {"name": "코란도 투리스모", "generations": []}, {"name": "이스타나", "generations": []}, {"name": "무쏘 스포츠", "generations": []}, {"name": "액티언 스포츠", "generations": []}, {"name": "코란도 스포츠", "generations": []}, {"name": "렉스턴 스포츠", "generations": []}, {"name": "렉스턴 스포츠 칸", "generations": []}, {"name": "무쏘 EV", "generations": []}]}, {"name": "MINI", "group": "수입", "models": [{"name": "쿠퍼 3도어", "generations": ["R50", "R53", "R56", "F56", "F66"]}, {"name": "쿠퍼 5도어", "generations": ["F55", "F65"]}, {"name": "쿠퍼 일렉트릭", "generations": ["F56 SE", "J01"]}, {"name": "컨버터블", "generations": ["R52", "R57", "F57", "F67"]}, {"name": "클럽맨", "generations": ["R55", "F54"]}, {"name": "컨트리맨", "generations": ["R60", "F60", "U25"]}, {"name": "에이스맨", "generations": ["J05"]}, {"name": "페이스맨", "generations": ["R61"]}, {"name": "쿠페", "generations": ["R58"]}, {"name": "로드스터", "generations": ["R59"]}, {"name": "클래식 MINI", "generations": ["클래식"]}]}, {"name": "BMW", "group": "수입", "models": [{"name": "1시리즈", "generations": []}, {"name": "2시리즈", "generations": []}, {"name": "3시리즈", "generations": []}, {"name": "4시리즈", "generations": []}, {"name": "5시리즈", "generations": []}, {"name": "6시리즈", "generations": []}, {"name": "7시리즈", "generations": []}, {"name": "8시리즈", "generations": []}, {"name": "X1", "generations": []}, {"name": "X2", "generations": []}, {"name": "X3", "generations": []}, {"name": "X4", "generations": []}, {"name": "X5", "generations": []}, {"name": "X6", "generations": []}, {"name": "X7", "generations": []}, {"name": "XM", "generations": []}, {"name": "i3", "generations": []}, {"name": "i4", "generations": []}, {"name": "i5", "generations": []}, {"name": "i7", "generations": []}, {"name": "i8", "generations": []}, {"name": "iX", "generations": []}, {"name": "iX1", "generations": []}, {"name": "iX2", "generations": []}, {"name": "iX3", "generations": []}, {"name": "Z3", "generations": []}, {"name": "Z4", "generations": []}, {"name": "Z8", "generations": []}]}, {"name": "메르세데스-벤츠", "group": "수입", "models": [{"name": "A-Class", "generations": []}, {"name": "B-Class", "generations": []}, {"name": "C-Class", "generations": []}, {"name": "E-Class", "generations": []}, {"name": "S-Class", "generations": []}, {"name": "CLA", "generations": []}, {"name": "CLS", "generations": []}, {"name": "CLK", "generations": []}, {"name": "CL", "generations": []}, {"name": "GLA", "generations": []}, {"name": "GLB", "generations": []}, {"name": "GLC", "generations": []}, {"name": "GLE", "generations": []}, {"name": "GLS", "generations": []}, {"name": "G-Class", "generations": []}, {"name": "GLK", "generations": []}, {"name": "ML", "generations": []}, {"name": "GL", "generations": []}, {"name": "EQA", "generations": []}, {"name": "EQB", "generations": []}, {"name": "EQC", "generations": []}, {"name": "EQE", "generations": []}, {"name": "EQE SUV", "generations": []}, {"name": "EQS", "generations": []}, {"name": "EQS SUV", "generations": []}, {"name": "SL", "generations": []}, {"name": "SLK", "generations": []}, {"name": "SLC", "generations": []}, {"name": "AMG GT", "generations": []}, {"name": "SLS AMG", "generations": []}, {"name": "SLR 맥라렌", "generations": []}, {"name": "V-Class", "generations": []}, {"name": "비토", "generations": []}, {"name": "스프린터", "generations": []}]}, {"name": "아우디", "group": "수입", "models": [{"name": "A1", "generations": []}, {"name": "A2", "generations": []}, {"name": "A3", "generations": []}, {"name": "A4", "generations": []}, {"name": "A5", "generations": []}, {"name": "A6", "generations": []}, {"name": "A7", "generations": []}, {"name": "A8", "generations": []}, {"name": "80", "generations": []}, {"name": "100", "generations": []}, {"name": "Q2", "generations": []}, {"name": "Q3", "generations": []}, {"name": "Q4", "generations": []}, {"name": "Q5", "generations": []}, {"name": "Q6", "generations": []}, {"name": "Q7", "generations": []}, {"name": "Q8", "generations": []}, {"name": "e-tron", "generations": []}, {"name": "e-tron GT", "generations": []}, {"name": "TT", "generations": []}, {"name": "R8", "generations": []}]}, {"name": "폭스바겐", "group": "수입", "models": [{"name": "골프", "generations": []}, {"name": "폴로", "generations": []}, {"name": "제타", "generations": []}, {"name": "파사트", "generations": []}, {"name": "아테온", "generations": []}, {"name": "CC", "generations": []}, {"name": "비틀", "generations": []}, {"name": "페이톤", "generations": []}, {"name": "시로코", "generations": []}, {"name": "업", "generations": []}, {"name": "티구안", "generations": []}, {"name": "투아렉", "generations": []}, {"name": "T-Roc", "generations": []}, {"name": "T-Cross", "generations": []}, {"name": "아틀라스", "generations": []}, {"name": "ID.3", "generations": []}, {"name": "ID.4", "generations": []}, {"name": "ID.5", "generations": []}, {"name": "ID.7", "generations": []}, {"name": "ID. Buzz", "generations": []}, {"name": "투란", "generations": []}, {"name": "샤란", "generations": []}, {"name": "트랜스포터", "generations": []}, {"name": "멀티밴", "generations": []}]}, {"name": "포르쉐", "group": "수입", "models": [{"name": "911", "generations": []}, {"name": "박스터", "generations": []}, {"name": "카이맨", "generations": []}, {"name": "718 박스터", "generations": []}, {"name": "718 카이맨", "generations": []}, {"name": "944", "generations": []}, {"name": "928", "generations": []}, {"name": "968", "generations": []}, {"name": "파나메라", "generations": []}, {"name": "타이칸", "generations": []}, {"name": "마칸", "generations": []}, {"name": "카이엔", "generations": []}]}, {"name": "스마트", "group": "수입", "models": [{"name": "포투", "generations": []}, {"name": "포포", "generations": []}, {"name": "로드스터", "generations": []}, {"name": "#1", "generations": []}, {"name": "#3", "generations": []}, {"name": "#5", "generations": []}]}, {"name": "오펠", "group": "수입", "models": [{"name": "코르사", "generations": []}, {"name": "아스트라", "generations": []}, {"name": "인시그니아", "generations": []}, {"name": "벡트라", "generations": []}, {"name": "오메가", "generations": []}, {"name": "아담", "generations": []}, {"name": "티그라", "generations": []}, {"name": "모카", "generations": []}, {"name": "그랜드랜드", "generations": []}, {"name": "크로스랜드", "generations": []}, {"name": "자피라", "generations": []}, {"name": "메리바", "generations": []}]}, {"name": "토요타", "group": "수입", "models": [{"name": "야리스", "generations": []}, {"name": "코롤라", "generations": []}, {"name": "캠리", "generations": []}, {"name": "아발론", "generations": []}, {"name": "크라운", "generations": []}, {"name": "프리우스", "generations": []}, {"name": "미라이", "generations": []}, {"name": "86", "generations": []}, {"name": "GR86", "generations": []}, {"name": "수프라", "generations": []}, {"name": "RAV4", "generations": []}, {"name": "하이랜더", "generations": []}, {"name": "랜드크루저", "generations": []}, {"name": "C-HR", "generations": []}, {"name": "벤자", "generations": []}, {"name": "4러너", "generations": []}, {"name": "세쿼이아", "generations": []}, {"name": "bZ4X", "generations": []}, {"name": "시에나", "generations": []}, {"name": "알파드", "generations": []}, {"name": "벨파이어", "generations": []}, {"name": "하이에이스", "generations": []}, {"name": "타코마", "generations": []}, {"name": "툰드라", "generations": []}, {"name": "하이럭스", "generations": []}]}, {"name": "렉서스", "group": "수입", "models": [{"name": "CT", "generations": []}, {"name": "IS", "generations": []}, {"name": "ES", "generations": []}, {"name": "GS", "generations": []}, {"name": "LS", "generations": []}, {"name": "RC", "generations": []}, {"name": "LC", "generations": []}, {"name": "SC", "generations": []}, {"name": "LFA", "generations": []}, {"name": "LBX", "generations": []}, {"name": "UX", "generations": []}, {"name": "NX", "generations": []}, {"name": "RX", "generations": []}, {"name": "RZ", "generations": []}, {"name": "GX", "generations": []}, {"name": "LX", "generations": []}, {"name": "TX", "generations": []}, {"name": "LM", "generations": []}]}, {"name": "혼다", "group": "수입", "models": [{"name": "시빅", "generations": []}, {"name": "어코드", "generations": []}, {"name": "인사이트", "generations": []}, {"name": "레전드", "generations": []}, {"name": "피트", "generations": []}, {"name": "CR-Z", "generations": []}, {"name": "S2000", "generations": []}, {"name": "NSX", "generations": []}, {"name": "프렐류드", "generations": []}, {"name": "HR-V", "generations": []}, {"name": "CR-V", "generations": []}, {"name": "파일럿", "generations": []}, {"name": "패스포트", "generations": []}, {"name": "오딧세이", "generations": []}, {"name": "리지라인", "generations": []}]}, {"name": "닛산", "group": "수입", "models": [{"name": "알티마", "generations": []}, {"name": "맥시마", "generations": []}, {"name": "센트라", "generations": []}, {"name": "티아나", "generations": []}, {"name": "큐브", "generations": []}, {"name": "리프", "generations": []}, {"name": "스카이라인", "generations": []}, {"name": "GT-R", "generations": []}, {"name": "350Z", "generations": []}, {"name": "370Z", "generations": []}, {"name": "Z", "generations": []}, {"name": "쥬크", "generations": []}, {"name": "캐시카이", "generations": []}, {"name": "엑스트레일", "generations": []}, {"name": "로그", "generations": []}, {"name": "무라노", "generations": []}, {"name": "패스파인더", "generations": []}, {"name": "패트롤", "generations": []}, {"name": "아르마다", "generations": []}, {"name": "아리야", "generations": []}, {"name": "프런티어", "generations": []}, {"name": "나바라", "generations": []}, {"name": "타이탄", "generations": []}]}, {"name": "인피니티", "group": "수입", "models": [{"name": "G", "generations": []}, {"name": "M", "generations": []}, {"name": "Q30", "generations": []}, {"name": "Q50", "generations": []}, {"name": "Q60", "generations": []}, {"name": "Q70", "generations": []}, {"name": "EX", "generations": []}, {"name": "FX", "generations": []}, {"name": "JX", "generations": []}, {"name": "QX30", "generations": []}, {"name": "QX50", "generations": []}, {"name": "QX55", "generations": []}, {"name": "QX60", "generations": []}, {"name": "QX70", "generations": []}, {"name": "QX80", "generations": []}]}, {"name": "마쓰다", "group": "수입", "models": [{"name": "마쓰다2", "generations": []}, {"name": "마쓰다3", "generations": []}, {"name": "마쓰다6", "generations": []}, {"name": "MX-5", "generations": []}, {"name": "RX-7", "generations": []}, {"name": "RX-8", "generations": []}, {"name": "CX-3", "generations": []}, {"name": "CX-30", "generations": []}, {"name": "CX-5", "generations": []}, {"name": "CX-50", "generations": []}, {"name": "CX-60", "generations": []}, {"name": "CX-70", "generations": []}, {"name": "CX-80", "generations": []}, {"name": "CX-90", "generations": []}, {"name": "MX-30", "generations": []}]}, {"name": "스바루", "group": "수입", "models": [{"name": "임프레자", "generations": []}, {"name": "레거시", "generations": []}, {"name": "WRX", "generations": []}, {"name": "BRZ", "generations": []}, {"name": "포레스터", "generations": []}, {"name": "아웃백", "generations": []}, {"name": "크로스트렉", "generations": []}, {"name": "트라이베카", "generations": []}, {"name": "어센트", "generations": []}, {"name": "솔테라", "generations": []}]}, {"name": "미쓰비시", "group": "수입", "models": [{"name": "랜서", "generations": []}, {"name": "갤랑", "generations": []}, {"name": "이클립스", "generations": []}, {"name": "3000GT", "generations": []}, {"name": "미라지", "generations": []}, {"name": "i-MiEV", "generations": []}, {"name": "아웃랜더", "generations": []}, {"name": "이클립스 크로스", "generations": []}, {"name": "파제로", "generations": []}, {"name": "ASX", "generations": []}, {"name": "트라이톤", "generations": []}, {"name": "델리카", "generations": []}]}, {"name": "스즈키", "group": "수입", "models": [{"name": "스위프트", "generations": []}, {"name": "알토", "generations": []}, {"name": "왜건 R", "generations": []}, {"name": "발레노", "generations": []}, {"name": "키자시", "generations": []}, {"name": "짐니", "generations": []}, {"name": "비타라", "generations": []}, {"name": "SX4", "generations": []}, {"name": "S-Cross", "generations": []}]}, {"name": "테슬라", "group": "수입", "models": [{"name": "모델 S", "generations": []}, {"name": "모델 3", "generations": []}, {"name": "모델 X", "generations": []}, {"name": "모델 Y", "generations": []}, {"name": "사이버트럭", "generations": []}, {"name": "로드스터", "generations": []}]}, {"name": "포드", "group": "수입", "models": [{"name": "머스탱", "generations": []}, {"name": "포커스", "generations": []}, {"name": "퓨전", "generations": []}, {"name": "토러스", "generations": []}, {"name": "피에스타", "generations": []}, {"name": "몬데오", "generations": []}, {"name": "GT", "generations": []}, {"name": "익스플로러", "generations": []}, {"name": "익스페디션", "generations": []}, {"name": "이스케이프", "generations": []}, {"name": "쿠가", "generations": []}, {"name": "에지", "generations": []}, {"name": "브롱코", "generations": []}, {"name": "브롱코 스포츠", "generations": []}, {"name": "머스탱 마하-E", "generations": []}, {"name": "레인저", "generations": []}, {"name": "F-150", "generations": []}, {"name": "F-시리즈 슈퍼듀티", "generations": []}, {"name": "매버릭", "generations": []}, {"name": "트랜짓", "generations": []}]}, {"name": "링컨", "group": "수입", "models": [{"name": "컨티넨탈", "generations": []}, {"name": "타운카", "generations": []}, {"name": "MKZ", "generations": []}, {"name": "MKS", "generations": []}, {"name": "코세어", "generations": []}, {"name": "노틸러스", "generations": []}, {"name": "에비에이터", "generations": []}, {"name": "내비게이터", "generations": []}, {"name": "MKC", "generations": []}, {"name": "MKX", "generations": []}, {"name": "MKT", "generations": []}]}, {"name": "캐딜락", "group": "수입", "models": [{"name": "ATS", "generations": []}, {"name": "CTS", "generations": []}, {"name": "CT4", "generations": []}, {"name": "CT5", "generations": []}, {"name": "CT6", "generations": []}, {"name": "DTS", "generations": []}, {"name": "STS", "generations": []}, {"name": "XTS", "generations": []}, {"name": "에스컬레이드", "generations": []}, {"name": "XT4", "generations": []}, {"name": "XT5", "generations": []}, {"name": "XT6", "generations": []}, {"name": "SRX", "generations": []}, {"name": "리릭", "generations": []}, {"name": "옵틱", "generations": []}, {"name": "비스틱", "generations": []}, {"name": "셀레스틱", "generations": []}, {"name": "에스컬레이드 IQ", "generations": []}]}, {"name": "GMC", "group": "수입", "models": [{"name": "시에라", "generations": []}, {"name": "캐니언", "generations": []}, {"name": "유콘", "generations": []}, {"name": "아카디아", "generations": []}, {"name": "터레인", "generations": []}, {"name": "허머 EV", "generations": []}]}, {"name": "지프", "group": "수입", "models": [{"name": "랭글러", "generations": []}, {"name": "글래디에이터", "generations": []}, {"name": "체로키", "generations": []}, {"name": "그랜드 체로키", "generations": []}, {"name": "컴패스", "generations": []}, {"name": "레니게이드", "generations": []}, {"name": "패트리어트", "generations": []}, {"name": "커맨더", "generations": []}, {"name": "왜고니어", "generations": []}, {"name": "그랜드 왜고니어", "generations": []}, {"name": "어벤저", "generations": []}]}, {"name": "크라이슬러", "group": "수입", "models": [{"name": "300", "generations": []}, {"name": "200", "generations": []}, {"name": "세브링", "generations": []}, {"name": "PT 크루저", "generations": []}, {"name": "크로스파이어", "generations": []}, {"name": "퍼시피카", "generations": []}, {"name": "보이저", "generations": []}, {"name": "타운 앤 컨트리", "generations": []}]}, {"name": "닷지", "group": "수입", "models": [{"name": "챌린저", "generations": []}, {"name": "차저", "generations": []}, {"name": "다트", "generations": []}, {"name": "바이퍼", "generations": []}, {"name": "네온", "generations": []}, {"name": "듀랑고", "generations": []}, {"name": "저니", "generations": []}, {"name": "니트로", "generations": []}, {"name": "호넷", "generations": []}, {"name": "그랜드 캐러밴", "generations": []}, {"name": "램(닷지)", "generations": []}]}, {"name": "램", "group": "수입", "models": [{"name": "1500", "generations": []}, {"name": "2500", "generations": []}, {"name": "3500", "generations": []}, {"name": "프로마스터", "generations": []}]}, {"name": "랜드로버", "group": "수입", "models": [{"name": "레인지로버", "generations": []}, {"name": "레인지로버 스포츠", "generations": []}, {"name": "레인지로버 벨라", "generations": []}, {"name": "레인지로버 이보크", "generations": []}, {"name": "디스커버리", "generations": []}, {"name": "디스커버리 스포츠", "generations": []}, {"name": "디펜더", "generations": []}, {"name": "프리랜더", "generations": []}]}, {"name": "재규어", "group": "수입", "models": [{"name": "XE", "generations": []}, {"name": "XF", "generations": []}, {"name": "XJ", "generations": []}, {"name": "X-Type", "generations": []}, {"name": "S-Type", "generations": []}, {"name": "XK", "generations": []}, {"name": "F-Type", "generations": []}, {"name": "F-Pace", "generations": []}, {"name": "E-Pace", "generations": []}, {"name": "I-Pace", "generations": []}]}, {"name": "벤틀리", "group": "수입", "models": [{"name": "컨티넨탈 GT", "generations": []}, {"name": "플라잉스퍼", "generations": []}, {"name": "뮬산", "generations": []}, {"name": "아르나지", "generations": []}, {"name": "브룩랜즈", "generations": []}, {"name": "아주르", "generations": []}, {"name": "벤테이가", "generations": []}]}, {"name": "롤스로이스", "group": "수입", "models": [{"name": "팬텀", "generations": []}, {"name": "고스트", "generations": []}, {"name": "레이스", "generations": []}, {"name": "던", "generations": []}, {"name": "실버 스퍼", "generations": []}, {"name": "실버 섀도", "generations": []}, {"name": "실버 세라프", "generations": []}, {"name": "스펙터", "generations": []}, {"name": "컬리넌", "generations": []}]}, {"name": "애스턴마틴", "group": "수입", "models": [{"name": "DB7", "generations": []}, {"name": "DB9", "generations": []}, {"name": "DB11", "generations": []}, {"name": "DB12", "generations": []}, {"name": "DBS", "generations": []}, {"name": "밴티지", "generations": []}, {"name": "뱅퀴시", "generations": []}, {"name": "라피드", "generations": []}, {"name": "발키리", "generations": []}, {"name": "DBX", "generations": []}]}, {"name": "맥라렌", "group": "수입", "models": [{"name": "F1", "generations": []}, {"name": "MP4-12C", "generations": []}, {"name": "540C", "generations": []}, {"name": "570S", "generations": []}, {"name": "570GT", "generations": []}, {"name": "600LT", "generations": []}, {"name": "650S", "generations": []}, {"name": "675LT", "generations": []}, {"name": "720S", "generations": []}, {"name": "750S", "generations": []}, {"name": "765LT", "generations": []}, {"name": "아투라", "generations": []}, {"name": "GT", "generations": []}, {"name": "GTS", "generations": []}, {"name": "P1", "generations": []}, {"name": "세나", "generations": []}, {"name": "스피드테일", "generations": []}, {"name": "엘바", "generations": []}]}, {"name": "로터스", "group": "수입", "models": [{"name": "엘리스", "generations": []}, {"name": "엑시지", "generations": []}, {"name": "에보라", "generations": []}, {"name": "에미라", "generations": []}, {"name": "에스프리", "generations": []}, {"name": "에바이야", "generations": []}, {"name": "엘레트라", "generations": []}, {"name": "에메야", "generations": []}]}, {"name": "르노", "group": "수입", "models": [{"name": "트윙고", "generations": []}, {"name": "클리오", "generations": []}, {"name": "메간", "generations": []}, {"name": "라구나", "generations": []}, {"name": "탈리스만", "generations": []}, {"name": "조에", "generations": []}, {"name": "캡처", "generations": []}, {"name": "카자르", "generations": []}, {"name": "콜레오스", "generations": []}, {"name": "오스트랄", "generations": []}, {"name": "에스파스", "generations": []}, {"name": "캉구", "generations": []}, {"name": "마스터", "generations": []}, {"name": "트라픽", "generations": []}, {"name": "트위지", "generations": []}]}, {"name": "푸조", "group": "수입", "models": [{"name": "106", "generations": []}, {"name": "107", "generations": []}, {"name": "108", "generations": []}, {"name": "206", "generations": []}, {"name": "207", "generations": []}, {"name": "208", "generations": []}, {"name": "306", "generations": []}, {"name": "307", "generations": []}, {"name": "308", "generations": []}, {"name": "406", "generations": []}, {"name": "407", "generations": []}, {"name": "408", "generations": []}, {"name": "508", "generations": []}, {"name": "607", "generations": []}, {"name": "RCZ", "generations": []}, {"name": "2008", "generations": []}, {"name": "3008", "generations": []}, {"name": "5008", "generations": []}, {"name": "리프터", "generations": []}, {"name": "트래블러", "generations": []}, {"name": "파트너", "generations": []}, {"name": "엑스퍼트", "generations": []}]}, {"name": "시트로엥", "group": "수입", "models": [{"name": "C1", "generations": []}, {"name": "C2", "generations": []}, {"name": "C3", "generations": []}, {"name": "C4", "generations": []}, {"name": "C5", "generations": []}, {"name": "C6", "generations": []}, {"name": "사라", "generations": []}, {"name": "잔티아", "generations": []}, {"name": "C3 에어크로스", "generations": []}, {"name": "C5 에어크로스", "generations": []}, {"name": "C4 피카소", "generations": []}, {"name": "그랜드 C4 피카소", "generations": []}, {"name": "베를링고", "generations": []}, {"name": "스페이스투어러", "generations": []}]}, {"name": "DS", "group": "수입", "models": [{"name": "DS 3", "generations": []}, {"name": "DS 4", "generations": []}, {"name": "DS 5", "generations": []}, {"name": "DS 7", "generations": []}, {"name": "DS 9", "generations": []}]}, {"name": "알핀", "group": "수입", "models": [{"name": "A110", "generations": []}, {"name": "A310", "generations": []}, {"name": "A610", "generations": []}, {"name": "A290", "generations": []}]}, {"name": "피아트", "group": "수입", "models": [{"name": "500", "generations": []}, {"name": "500L", "generations": []}, {"name": "500X", "generations": []}, {"name": "판다", "generations": []}, {"name": "푼토", "generations": []}, {"name": "티포", "generations": []}, {"name": "124 스파이더", "generations": []}, {"name": "쿠페", "generations": []}, {"name": "도블로", "generations": []}, {"name": "두카토", "generations": []}]}, {"name": "알파로메오", "group": "수입", "models": [{"name": "줄리아", "generations": []}, {"name": "줄리에타", "generations": []}, {"name": "미토", "generations": []}, {"name": "147", "generations": []}, {"name": "156", "generations": []}, {"name": "159", "generations": []}, {"name": "브레라", "generations": []}, {"name": "스파이더", "generations": []}, {"name": "4C", "generations": []}, {"name": "8C", "generations": []}, {"name": "스텔비오", "generations": []}, {"name": "토날레", "generations": []}, {"name": "주니어", "generations": []}]}, {"name": "마세라티", "group": "수입", "models": [{"name": "기블리", "generations": []}, {"name": "콰트로포르테", "generations": []}, {"name": "그란투리스모", "generations": []}, {"name": "그란카브리오", "generations": []}, {"name": "MC20", "generations": []}, {"name": "쿠페", "generations": []}, {"name": "스파이더", "generations": []}, {"name": "르반떼", "generations": []}, {"name": "그레칼레", "generations": []}]}, {"name": "페라리", "group": "수입", "models": [{"name": "348", "generations": []}, {"name": "355", "generations": []}, {"name": "360", "generations": []}, {"name": "F430", "generations": []}, {"name": "458", "generations": []}, {"name": "488", "generations": []}, {"name": "F8", "generations": []}, {"name": "296", "generations": []}, {"name": "SF90", "generations": []}, {"name": "550", "generations": []}, {"name": "575M", "generations": []}, {"name": "599", "generations": []}, {"name": "F12", "generations": []}, {"name": "812", "generations": []}, {"name": "캘리포니아", "generations": []}, {"name": "포르토피노", "generations": []}, {"name": "로마", "generations": []}, {"name": "FF", "generations": []}, {"name": "GTC4루쏘", "generations": []}, {"name": "라페라리", "generations": []}, {"name": "엔초", "generations": []}, {"name": "F40", "generations": []}, {"name": "F50", "generations": []}, {"name": "12칠린드리", "generations": []}, {"name": "푸로산게", "generations": []}]}, {"name": "람보르기니", "group": "수입", "models": [{"name": "가야르도", "generations": []}, {"name": "우라칸", "generations": []}, {"name": "무르시엘라고", "generations": []}, {"name": "아벤타도르", "generations": []}, {"name": "레부엘토", "generations": []}, {"name": "테메라리오", "generations": []}, {"name": "디아블로", "generations": []}, {"name": "쿤타치", "generations": []}, {"name": "미우라", "generations": []}, {"name": "우루스", "generations": []}, {"name": "LM002", "generations": []}]}, {"name": "볼보", "group": "수입", "models": [{"name": "S40", "generations": []}, {"name": "S60", "generations": []}, {"name": "S70", "generations": []}, {"name": "S80", "generations": []}, {"name": "S90", "generations": []}, {"name": "C30", "generations": []}, {"name": "C70", "generations": []}, {"name": "V40", "generations": []}, {"name": "V50", "generations": []}, {"name": "V60", "generations": []}, {"name": "V70", "generations": []}, {"name": "V90", "generations": []}, {"name": "850", "generations": []}, {"name": "940", "generations": []}, {"name": "960", "generations": []}, {"name": "XC40", "generations": []}, {"name": "XC60", "generations": []}, {"name": "XC70", "generations": []}, {"name": "XC90", "generations": []}, {"name": "C40", "generations": []}, {"name": "EC40", "generations": []}, {"name": "EX30", "generations": []}, {"name": "EX40", "generations": []}, {"name": "EX90", "generations": []}]}, {"name": "폴스타", "group": "수입", "models": [{"name": "폴스타 1", "generations": []}, {"name": "폴스타 2", "generations": []}, {"name": "폴스타 3", "generations": []}, {"name": "폴스타 4", "generations": []}]}, {"name": "사브", "group": "수입", "models": [{"name": "900", "generations": []}, {"name": "9000", "generations": []}, {"name": "9-3", "generations": []}, {"name": "9-5", "generations": []}, {"name": "9-4X", "generations": []}, {"name": "9-7X", "generations": []}]}, {"name": "BYD", "group": "수입", "models": [{"name": "돌핀", "generations": []}, {"name": "씰", "generations": []}, {"name": "한", "generations": []}, {"name": "아토 3", "generations": []}, {"name": "씨라이언 7", "generations": []}, {"name": "탕", "generations": []}]}, {"name": "지커", "group": "수입", "models": [{"name": "001", "generations": []}, {"name": "007", "generations": []}, {"name": "X", "generations": []}, {"name": "7X", "generations": []}, {"name": "009", "generations": []}]}]''')
        as List)
    .cast<Map<String, dynamic>>();

class VehicleCatalogPicker extends StatelessWidget {
  const VehicleCatalogPicker({
    super.key,
    required this.modelController,
    this.generationController,
  });

  final TextEditingController modelController;
  final TextEditingController? generationController;

  @override
  Widget build(BuildContext context) => FormField<String>(
        validator: (_) =>
            modelController.text.trim().isEmpty ? '차종을 선택해 주세요.' : null,
        builder: (field) => Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            OutlinedButton.icon(
              icon: const Icon(Icons.directions_car_outlined),
              label: Text(modelController.text.trim().isEmpty
                  ? '차종 선택 *'
                  : modelController.text),
              onPressed: () async {
                final selected = await showModalBottomSheet<bool>(
                  context: context,
                  isScrollControlled: true,
                  showDragHandle: true,
                  builder: (sheetContext) => _VehicleCatalogSelectionSheet(
                    modelController: modelController,
                    generationController: generationController,
                  ),
                );
                if (selected == true) {
                  field.didChange(modelController.text);
                  field.validate();
                }
              },
            ),
            if (field.errorText != null)
              Padding(
                padding: const EdgeInsets.only(left: 12, top: 4),
                child: Text(field.errorText!,
                    style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                        fontSize: 12)),
              ),
          ],
        ),
      );
}

class _VehicleCatalogSelectionSheet extends StatefulWidget {
  const _VehicleCatalogSelectionSheet(
      {required this.modelController, this.generationController});
  final TextEditingController modelController;
  final TextEditingController? generationController;

  @override
  State<_VehicleCatalogSelectionSheet> createState() =>
      _VehicleCatalogSelectionSheetState();
}

class _VehicleCatalogSelectionSheetState
    extends State<_VehicleCatalogSelectionSheet> {
  String group = '수입';
  String? brand;
  String? model;
  bool custom = false;
  final customModel = TextEditingController();
  final formKey = GlobalKey<FormState>();

  List<Map<String, dynamic>> get brands =>
      vehicleBrandCatalog.where((b) => b['group'] == group).toList();
  List<Map<String, dynamic>> get models => brand == null
      ? []
      : (brands.firstWhere((b) => b['name'] == brand)['models'] as List)
          .cast<Map<String, dynamic>>();
  List<String> get generations => model == null || custom
      ? []
      : (models.firstWhere((entry) => entry['name'] == model)['generations']
              as List)
          .cast<String>();

  @override
  void dispose() {
    customModel.dispose();
    super.dispose();
  }

  Widget dropdown(String label, String? selected, List<String> options,
          ValueChanged<String?> changed) =>
      DropdownButtonFormField<String>(
        key: ValueKey('$label/$group/$brand/$model/$selected'),
        initialValue: selected,
        isExpanded: true,
        decoration: InputDecoration(labelText: label),
        items: options
            .map((v) => DropdownMenuItem(
                value: v, child: Text(v, overflow: TextOverflow.ellipsis)))
            .toList(),
        onChanged: options.isEmpty ? null : changed,
        validator: (v) => v == null ? '$label 선택해 주세요.' : null,
      );

  void finish() {
    if (!(formKey.currentState?.validate() ?? false)) return;
    widget.modelController.text =
        custom ? customModel.text.trim() : '$brand $model';
    widget.generationController?.text =
        generations.isEmpty ? '' : generations.first;
    Navigator.pop(context, true);
  }

  @override
  Widget build(BuildContext context) => SafeArea(
        child: Padding(
          padding: EdgeInsets.fromLTRB(
              20, 8, 20, MediaQuery.viewInsetsOf(context).bottom + 20),
          child: Form(
            key: formKey,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text('차종 선택',
                      style: Theme.of(context)
                          .textTheme
                          .titleLarge
                          ?.copyWith(fontWeight: FontWeight.w800)),
                  const SizedBox(height: 16),
                  dropdown(
                      '국산 / 수입',
                      group,
                      const ['국산', '수입'],
                      (v) => setState(() {
                            group = v!;
                            brand = null;
                            model = null;
                            custom = false;
                          })),
                  const SizedBox(height: 12),
                  dropdown(
                      '브랜드',
                      brand,
                      brands.map((b) => b['name'] as String).toList(),
                      (v) => setState(() {
                            brand = v;
                            model = null;
                            custom = false;
                          })),
                  const SizedBox(height: 12),
                  dropdown(
                      '차종',
                      model,
                      [
                        ...models.map((m) => m['name'] as String),
                        if (brand != null) '기타 차종 직접 입력'
                      ],
                      (v) => setState(() {
                            model = v;
                            custom = v == '기타 차종 직접 입력';
                          })),
                  if (custom) ...[
                    const SizedBox(height: 12),
                    TextFormField(
                        controller: customModel,
                        decoration:
                            const InputDecoration(labelText: '차종 직접 입력'),
                        validator: (v) => v == null || v.trim().isEmpty
                            ? '차종을 입력해 주세요.'
                            : null),
                  ],
                  if (brand == 'MINI' && model != null && !custom) ...[
                    const SizedBox(height: 12),
                    _MiniModelPreview(
                        model: model!,
                        generation:
                            generations.isEmpty ? '' : generations.first),
                    if (generations.isNotEmpty)
                      Padding(
                          padding: const EdgeInsets.only(top: 6),
                          child: Text('세대 ${generations.join(' · ')}',
                              textAlign: TextAlign.center,
                              style: Theme.of(context).textTheme.bodySmall)),
                  ],
                  if (brand == 'BMW' && model != null && !custom) ...[
                    const SizedBox(height: 12),
                    _BmwModelPreview(model: model!),
                    const Padding(
                      padding: EdgeInsets.only(top: 6),
                      child: Text('BMW 참고 이미지',
                          textAlign: TextAlign.center,
                          style: TextStyle(fontSize: 12)),
                    ),
                  ],
                  const SizedBox(height: 18),
                  FilledButton(
                      onPressed: finish, child: const Text('차종 선택 완료')),
                ],
              ),
            ),
          ),
        ),
      );
}

class _MiniModelPreview extends StatelessWidget {
  const _MiniModelPreview({required this.model, required this.generation});
  final String model;
  final String generation;
  static const _photos = <String, String>{
    'R50': 'assets/images/mini-vehicles/mini_cooper_3door_r50.webp',
    'R53': 'assets/images/mini-vehicles/mini_cooper_3door_r53.webp',
    'R56': 'assets/images/mini-vehicles/mini_cooper_3door_r56.webp',
    'F56': 'assets/images/mini-vehicles/mini_cooper_3door_f56.webp',
    'F66': 'assets/images/mini-vehicles/mini_cooper_3door_f66.webp',
    'F55': 'assets/images/mini-vehicles/mini_cooper_5door_f55.webp',
    'F65': 'assets/images/mini-vehicles/mini_cooper_5door_f65.webp',
    'F56 SE': 'assets/images/mini-vehicles/mini_cooper_electric_f56se.webp',
    'J01': 'assets/images/mini-vehicles/mini_cooper_electric_j01.webp',
    'R52': 'assets/images/mini-vehicles/mini_convertible_r52.webp',
    'R57': 'assets/images/mini-vehicles/mini_convertible_r57.webp',
    'F57': 'assets/images/mini-vehicles/mini_convertible_f57.webp',
    'F67': 'assets/images/mini-vehicles/mini_convertible_f67.webp',
    'R55': 'assets/images/mini-vehicles/mini_clubman_r55.webp',
    'F54': 'assets/images/mini-vehicles/mini_clubman_f54.webp',
    'R60': 'assets/images/mini-vehicles/mini_countryman_r60.webp',
    'F60': 'assets/images/mini-vehicles/mini_countryman_f60.webp',
    'U25': 'assets/images/mini-vehicles/mini_countryman_u25.webp',
    'J05': 'assets/images/mini-vehicles/mini_aceman_j05.webp',
    'R61': 'assets/images/mini-vehicles/mini_paceman_r61.webp',
    'R58': 'assets/images/mini-vehicles/mini_coupe_r58.webp',
    'R59': 'assets/images/mini-vehicles/mini_roadster_r59.webp',
    '클래식': 'assets/images/mini-vehicles/mini_classic.webp',
  };

  @override
  Widget build(BuildContext context) {
    final code = _photos.keys
        .where((key) => generation.toUpperCase().contains(key.toUpperCase()))
        .firstOrNull;
    final asset = _photos[code] ??
        (model.contains('컨버터블')
            ? _photos['F67']
            : model.contains('클럽맨')
                ? _photos['F54']
                : model.contains('컨트리맨')
                    ? _photos['U25']
                    : model.contains('전기')
                        ? _photos['J01']
                        : model.contains('5도어')
                            ? _photos['F65']
                            : model.contains('쿠퍼')
                                ? _photos['F66']
                                : null);
    if (asset == null) return const SizedBox.shrink();
    return Container(
      height: 150,
      width: double.infinity,
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(12)),
      child: Image.asset(asset,
          fit: BoxFit.contain,
          errorBuilder: (_, __, ___) =>
              const Icon(Icons.directions_car, size: 48)),
    );
  }
}

class _BmwModelPreview extends StatelessWidget {
  const _BmwModelPreview({required this.model});
  final String model;

  static const _sedan =
      'assets/images/bmw-vehicles/bmw-sedan-5-series-2024.jpg';
  static const _suv = 'assets/images/bmw-vehicles/bmw-suv-x5-2024.jpg';
  static const _electric =
      'assets/images/bmw-vehicles/bmw-electric-suv-ix3.jpg';

  @override
  Widget build(BuildContext context) {
    final normalized = model.toLowerCase();
    final isElectricSuv = normalized.startsWith('ix');
    final isSuv = normalized.startsWith('x') || normalized == 'xm';
    return Container(
      height: 150,
      width: double.infinity,
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(12),
      ),
      clipBehavior: Clip.antiAlias,
      child: Image.asset(isElectricSuv ? _electric : isSuv ? _suv : _sedan,
          fit: BoxFit.cover,
          errorBuilder: (_, __, ___) => const Center(
              child: Icon(Icons.directions_car_filled, size: 48))),
    );
  }
}
