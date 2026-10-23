import 'dart:convert';

final prototypePartners = (jsonDecode(
            r'''[{"name":"아이모터스랩","region":"서울 성수동","region_group":"서울/경기 협력업체","category":"사고수리 전문","service_categories":["판금·도색","사고수리"],"address":"성수동2가 243-3","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=347","branch_label":"성수점"},{"name":"아이모터스랩","region":"경기 용인 죽전","region_group":"서울/경기 협력업체","category":"사고수리 전문","service_categories":["판금·도색","사고수리"],"address":"경기 용인시 수지구 용구대로 2699","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=347","branch_label":"죽전점"},{"name":"리본모터스 분당","region":"경기 분당","region_group":"서울/경기 협력업체","category":"사고수리 전문","service_categories":["판금·도색","사고수리"],"address":"","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=399"},{"name":"랩스타모터스","region":"경기 광주","region_group":"서울/경기 협력업체","category":"사고수리 전문","service_categories":["사고수리"],"address":"","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=286"},{"name":"성남 한국자동차유리","region":"경기 성남","region_group":"서울/경기 협력업체","category":"차량유리 전문","service_categories":["유리 교환·복원"],"address":"","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=412"},{"name":"글라스히어로즈","region":"서울/경기","region_group":"서울/경기 협력업체","category":"차량유리 전문","service_categories":["유리 교환·복원"],"address":"","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=509"},{"name":"용자팩토리","region":"서울/경기","region_group":"서울/경기 협력업체","category":"튜닝·전장","service_categories":["전장","튜닝"],"address":"","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=461"},{"name":"말자동차","region":"서울/경기","region_group":"서울/경기 협력업체","category":"튜닝·전장","service_categories":["전장·튜닝","악세사리"],"address":"","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=478"},{"name":"에스튠 수원","region":"경기 수원","region_group":"서울/경기 협력업체","category":"튜닝·전장","service_categories":["튜닝·전장"],"address":"경기도 수원시 영통구 센트럴파크로127번길 97-2","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=580"},{"name":"카카오파츠 서초","region":"서울 서초","region_group":"서울/경기 협력업체","category":"전장류 전문","service_categories":["전장","오디오·전장"],"address":"","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=240"},{"name":"인치업매니아 송파점","region":"서울 송파구","region_group":"서울/경기 협력업체","category":"휠·타이어 전문","service_categories":["휠","타이어"],"address":"","cafe_url":"","branch_label":"송파점"},{"name":"휘스토리 강북","region":"서울 강북","region_group":"서울/경기 협력업체","category":"휠·타이어","service_categories":["휠","타이어"],"address":"","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=380"},{"name":"군팩토리","region":"서울 양천구 목동","region_group":"서울/경기 협력업체","category":"오디오·전장 튜닝","service_categories":["오디오","전장","MINI 전문"],"address":"서울 양천구 목동중앙북로 120 1층 (목동 523-8)","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=660"},{"name":"포텐타이어","region":"인천","region_group":"서울/경기 협력업체","category":"휠·타이어 전문","service_categories":["휠","타이어","휠 복원","캘리퍼 도색"],"address":"","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=518"},{"name":"티스테이션 종암","region":"서울 종암","region_group":"서울/경기 협력업체","category":"타이어","service_categories":["타이어"],"address":"","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=236"},{"name":"힐링타이어","region":"경기 남양주","region_group":"서울/경기 협력업체","category":"휠·타이어 전문","service_categories":["휠 복원","휠","타이어"],"address":"","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=540"},{"name":"아라바서비스","region":"서울/경기","region_group":"서울/경기 협력업체","category":"정비·서비스","service_categories":["정비","수입차"],"address":"","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=349"},{"name":"수리아 용인","region":"경기 용인","region_group":"서울/경기 협력업체","category":"정비·서비스","service_categories":["정비"],"address":"","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=642"},{"name":"가람모터스 별내","region":"경기 별내","region_group":"서울/경기 협력업체","category":"정비·서비스","service_categories":["정비","수입차"],"address":"","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=625"},{"name":"크란츠모터스 구리","region":"경기 구리","region_group":"서울/경기 협력업체","category":"수입차 정비","service_categories":["MINI 정비","수입차 수리"],"address":"","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=425"},{"name":"모터스힐 구리","region":"경기 구리","region_group":"서울/경기 협력업체","category":"정비·서비스","service_categories":["정비"],"address":"","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=623"},{"name":"DH모터스 부천","region":"경기 부천","region_group":"서울/경기 협력업체","category":"정비·서비스","service_categories":["정비"],"address":"","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=557"},{"name":"한국디젤카연구소 논산","region":"충남 논산","region_group":"전라/경상/충청 협력업체","category":"디젤 정비 전문","service_categories":["디젤 정비","정비"],"address":"","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=543"},{"name":"에이블모터스 부산","region":"부산","region_group":"전라/경상/충청 협력업체","category":"사고수리·정비 전문","service_categories":["사고수리","판금·도색","정비"],"address":"","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=288"},{"name":"제틀리시 부산","region":"부산","region_group":"전라/경상/충청 협력업체","category":"사고수리·정비 전문","service_categories":["사고수리","판금·도색","정비"],"address":"","cafe_url":"https://m.cafe.naver.com/ArticleList.nhn?search.clubid=13071593&search.menuid=636"},{"name":"모터스킨","region":"서울 강서구","region_group":"신차패키지","category":"신차패키지","service_categories":["신차패키지","풀PPF","풀랩핑"],"address":"","cafe_url":""},{"name":"렌트리스 얼마면탈까","region":"온라인","region_group":"신차패키지","category":"신차패키지","service_categories":["신차패키지"],"address":"","cafe_url":""},{"name":"프린트랩","region":"온라인","region_group":"신차패키지","category":"신차패키지","service_categories":["신차패키지","수입차 부품"],"address":"","cafe_url":""},{"name":"대한민국대표 금호타이어","region":"지역 확인 필요","region_group":"신차패키지","category":"신차패키지","service_categories":["신차패키지","타이어"],"address":"","cafe_url":""}]''')
        as List)
    .map((row) => Map<String, dynamic>.from(row as Map))
    .where((row) => row['name'] != '대한민국대표 금호타이어')
    .toList();

List<Map<String, dynamic>> alignPartnerDirectory(
    List<Map<String, dynamic>> source) {
  final result = <Map<String, dynamic>>[];
  for (final item in source) {
    final name = '${item['name'] ?? ''}';
    // Partner API records are managed in the admin site. Keep every editable
    // value from the API authoritative; only derive labels that aren't stored
    // by the server. The static catalog below is just a fallback for demos.
    if (item['id'] != null) {
      final region = '${item['region'] ?? ''}';
      final services =
          (item['service_categories'] as List? ?? const []).join(' ');
      final hasAccident = RegExp(r'사고|판금').hasMatch(services);
      final hasMaintenance = RegExp(r'정비|수리|서비스|디젤').hasMatch(services);
      final category = hasAccident && hasMaintenance
          ? '사고수리·정비 전문'
          : hasAccident
              ? '사고수리 전문'
              : services.contains('유리')
                  ? '차량유리 전문'
                  : RegExp(r'전장|오디오|튜닝|부품').hasMatch(services)
                      ? '전장류 전문'
                      : RegExp(r'휠|타이어').hasMatch(services)
                          ? '휠·타이어 전문'
                          : '정비 전문';
      result.add({
        ...item,
        'category': item['category'] ?? category,
        'region_group': item['region_group'] ?? _partnerRegionGroup(region),
      });
      continue;
    }
    if (name.replaceAll(RegExp(r'\s+'), '') == '대한민국대표금호타이어') continue;
    if (name == '아이모터스랩' || name == '아이모터스랩 성수점' || name == '아이모터스랩 죽전점') {
      final sourceRegion = '${item['region'] ?? ''}';
      final sourceBranch = '${item['branch_label'] ?? ''}';
      final isJukjeon = sourceBranch.contains('죽전') ||
          sourceRegion.contains('죽전') ||
          name.contains('죽전');
      final branchPrototype = prototypePartners.firstWhere((row) =>
          row['name'] == '아이모터스랩' &&
          '${row['branch_label']}'.contains(isJukjeon ? '죽전' : '성수'));
      result.add({
        ...branchPrototype,
        ...item,
        'name': '아이모터스랩',
        'branch_label': sourceBranch.isEmpty
            ? branchPrototype['branch_label']
            : sourceBranch,
        'region': isJukjeon ? '경기 용인' : '서울 성수',
        'address': '',
      });
      continue;
    }
    final corrected = switch (name.replaceAll(RegExp(r'\s+'), '')) {
      '인천포텐(휠수리)' || '인천포텐휠수리' => '포텐타이어',
      '힐링휠복원남양주' => '힐링타이어',
      '수입차부품프린트랩' => '프린트랩',
      _ => name,
    };
    final matches = prototypePartners.where((row) => row['name'] == corrected);
    if (name.replaceAll(' ', '').contains('리본모터스')) {
      final prototype =
          prototypePartners.firstWhere((row) => row['name'] == '리본모터스 분당');
      result.add({
        ...prototype,
        ...item,
        'name': '리본모터스',
        'region_group': '서울/경기 협력업체',
        'category': '사고수리 전문',
        'service_categories': ['판금·도색', '사고수리'],
      });
    } else if (name.replaceAll(' ', '').contains('랩스타모터스') ||
        name.replaceAll(' ', '') == '랩스타') {
      final prototype =
          prototypePartners.firstWhere((row) => row['name'] == '랩스타모터스');
      result.add({
        ...prototype,
        ...item,
        'name': '랩스타모터스',
        'region': '경기도 광주',
        'address': '',
        'region_group': '서울/경기 협력업체',
        'category': '사고수리 전문',
        'service_categories': ['사고수리'],
      });
    } else {
      final aligned = matches.isEmpty ? item : {...matches.first, ...item};
      final compactName = name.replaceAll(RegExp(r'\s+'), '').toLowerCase();
      final displayOverrides = switch (compactName) {
        '성남한국자동차유리' => {'name': '한국자동차유리'},
        '한국자동차유리' => {'name': '한국자동차유리'},
        '카카오파츠서초' => {'name': '카카오파츠'},
        '카카오파츠' => {'name': '카카오파츠'},
        '휘스토리강북' || '휘스토리' => {
            'name': '휘스토리',
            'region': '서울 강북구',
            'address': '',
            'category': '전장류 전문',
            'service_categories': ['전장', '오디오·전장'],
          },
        '인치업매니아송파점' => {
            'name': '인치업매니아',
            'service_categories': ['휠', '타이어'],
            'branch_label': '송파점',
            'region': '서울 송파',
            'address': '',
          },
        '에스튠수원' || '에스튠' => {
            'name': '에스튠',
            'region': '경기도 수원',
            'address': '',
            'service_categories': ['튜닝·전장', '썬팅'],
          },
        '아라바서비스' => {'region': '경기 하남', 'address': ''},
        '포텐타이어' || '인천포텐(휠수리)' || '인천포텐휠수리' => {
            'name': '포텐타이어',
            'category': '휠·타이어 전문',
            'service_categories': ['휠', '타이어', '휠 복원', '캘리퍼 도색'],
          },
        '힐링휠복원남양주' || '힐링타이어' => {
            'name': '힐링타이어',
            'category': '휠·타이어 전문',
            'service_categories': ['휠 복원', '휠', '타이어'],
          },
        '한국디젤카연구소논산' || '한국디젤카연구소' => {
            'name': '한국디젤카연구소',
            'category': '디젤 정비 전문',
            'service_categories': ['디젤 정비'],
          },
        '에이블모터스부산' || '에이블모터스' => {
            'name': '에이블모터스',
            'category': '사고수리·정비 전문',
            'service_categories': ['사고수리', '정비'],
          },
        '모터스킨' => {
            'region': '서울 강서구',
            'address': '',
            'service_categories': ['신차패키지', '풀PPF', '풀랩핑'],
          },
        '렌트리스얼마면탈까' => {'region': '온라인'},
        '수입차부품프린트랩' || '프린트랩' => {
            'name': '프린트랩',
            'region': '온라인',
          },
        '군팩토리' => {'region': '서울 양천구', 'address': ''},
        '모터스힐구리' => {'name': '모터스힐'},
        '가람모터스별내' => {'name': '가람모터스'},
        'dh모터스부천' => {'name': 'DH모터스'},
        '크란츠모터스구리' => {'name': '크란츠모터스'},
        '수리아용인' || '수리아' || '수리야' => {
            'name': '수리아',
            'region': '경기 용인',
          },
        '제틀리시부산' => {'name': '제틀리시'},
        _ => <String, dynamic>{},
      };
      final displayPartner = {...aligned, ...displayOverrides};
      if (compactName == '제틀리시부산') {
        final services =
            (displayPartner['service_categories'] as List? ?? const [])
                .map((service) => service.toString())
                .toList();
        if (!services.contains('세차')) services.add('세차');
        displayPartner['service_categories'] = services;
      }
      result.add(displayPartner);
    }
  }
  final hasServerRecords = source.any((item) => item['id'] != null);
  final hasSeongsu = result.any((row) =>
      row['name'] == '아이모터스랩' && '${row['branch_label']}'.contains('성수'));
  final hasJukjeon = result.any((row) =>
      row['name'] == '아이모터스랩' && '${row['branch_label']}'.contains('죽전'));
  if (!hasServerRecords && hasSeongsu && !hasJukjeon) {
    final prototype = prototypePartners.firstWhere((row) =>
        row['name'] == '아이모터스랩' && '${row['branch_label']}'.contains('죽전'));
    result.add({...prototype, 'id': null, 'catalog_only': true});
  }
  return result;
}

String _partnerRegionGroup(String region) {
  if (RegExp(r'부산|경남|경북|충남|충북|전남|전북|대전|광주|울산|세종|논산').hasMatch(region)) {
    return '전라/경상/충청 협력업체';
  }
  return '서울/경기 협력업체';
}

List<Map<String, dynamic>> sortAccidentRepairPartners(
        List<Map<String, dynamic>> source) =>
    [...source];
