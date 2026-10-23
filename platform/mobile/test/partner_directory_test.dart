import 'package:flutter_test/flutter_test.dart';
import 'package:ilovemini/partner_directory.dart';

void main() {
  test('partner directory uses the requested shorter names and locations', () {
    final aligned = alignPartnerDirectory(prototypePartners);
    Map<String, dynamic> find(String name) =>
        aligned.firstWhere((partner) => partner['name'] == name);

    final seongsu = aligned.firstWhere((partner) =>
        partner['name'] == '아이모터스랩' && partner['branch_label'] == '성수점');
    final jukjeon = aligned.firstWhere((partner) =>
        partner['name'] == '아이모터스랩' && partner['branch_label'] == '죽전점');
    expect(seongsu['region'], '서울 성수');
    expect(seongsu['address'], '');
    expect(jukjeon['region'], '경기 용인');
    expect(jukjeon['address'], '');
    expect(find('랩스타모터스')['region'], '경기도 광주');
    expect(find('인치업매니아')['branch_label'], '송파점');
    expect(find('인치업매니아')['region'], '서울 송파');
    expect(find('아라바서비스')['region'], '경기 하남');
    expect(find('휘스토리')['region'], '서울 강북구');
    expect(find('휘스토리')['category'], '전장류 전문');
    expect(find('에스튠')['region'], '경기도 수원');
    expect(find('에스튠')['service_categories'], ['튜닝·전장', '썬팅']);
    expect(find('군팩토리')['region'], '서울 양천구');
    expect(
        aligned.any((partner) => partner['name'] == '대한민국대표 금호타이어'), isFalse);

    expect(find('한국자동차유리')['name'], '한국자동차유리');
    expect(find('카카오파츠')['name'], '카카오파츠');
    expect(find('모터스힐')['name'], '모터스힐');
    expect(find('가람모터스')['name'], '가람모터스');
    expect(find('DH모터스')['name'], 'DH모터스');
    expect(find('크란츠모터스')['name'], '크란츠모터스');
    expect(find('수리아')['name'], '수리아');
    expect(find('한국디젤카연구소')['name'], '한국디젤카연구소');
    expect(find('한국디젤카연구소')['category'], '디젤 정비 전문');
    expect(find('한국디젤카연구소')['service_categories'], ['디젤 정비']);
    expect(find('에이블모터스')['name'], '에이블모터스');
    expect(find('에이블모터스')['category'], '사고수리·정비 전문');
    expect(find('에이블모터스')['service_categories'], ['사고수리', '정비']);
    expect(find('포텐타이어')['service_categories'], ['휠', '타이어', '휠 복원', '캘리퍼 도색']);
    expect(find('힐링타이어')['service_categories'], ['휠 복원', '휠', '타이어']);
    expect(find('모터스킨')['region'], '서울 강서구');
    expect(find('모터스킨')['address'], '');
    expect(find('모터스킨')['service_categories'], ['신차패키지', '풀PPF', '풀랩핑']);
    expect(find('렌트리스 얼마면탈까')['region'], '온라인');
    expect(find('프린트랩')['region'], '온라인');
    expect(find('제틀리시')['name'], '제틀리시');
    expect(find('제틀리시')['service_categories'], contains('세차'));
    expect(find('말자동차')['service_categories'], ['전장·튜닝', '악세사리']);
  });

  test('partner directory normalizes legacy names and API details', () {
    final aligned = alignPartnerDirectory([
      {
        'name': '인천 포텐(휠수리)',
        'region': '인천',
        'service_categories': ['타이어', '휠']
      },
      {
        'name': '힐링휠복원 남양주',
        'region': '경기 남양주',
        'service_categories': ['휠 복원']
      },
      {
        'name': '한국디젤카연구소 논산',
        'region': '충남 논산',
        'service_categories': ['사고수리', '판금·도색', '디젤 정비']
      },
      {
        'name': '에이블모터스 부산',
        'region': '부산',
        'service_categories': ['수입차 정비']
      },
      {
        'name': '모터스킨',
        'region': '서울 강서구 등촌동',
        'address': '화곡로66길 153',
        'service_categories': ['신차패키지']
      },
      {'name': '렌트리스 얼마면탈까', 'region': '지역 확인 필요'},
      {'name': '수입차부품 프린트랩', 'region': '지역 확인 필요'},
    ]);
    final byName = {for (final partner in aligned) partner['name']: partner};
    expect(
        byName['포텐타이어']!['service_categories'], ['휠', '타이어', '휠 복원', '캘리퍼 도색']);
    expect(byName['힐링타이어']!['service_categories'], ['휠 복원', '휠', '타이어']);
    expect(byName['한국디젤카연구소']!['category'], '디젤 정비 전문');
    expect(byName['한국디젤카연구소']!['service_categories'], ['디젤 정비']);
    expect(byName['에이블모터스']!['category'], '사고수리·정비 전문');
    expect(byName['에이블모터스']!['service_categories'], ['사고수리', '정비']);
    expect(byName['모터스킨']!['region'], '서울 강서구');
    expect(byName['모터스킨']!['address'], '');
    expect(byName['렌트리스 얼마면탈까']!['region'], '온라인');
    expect(byName['프린트랩']!['region'], '온라인');
    expect(byName['프린트랩']!['region_group'], '신차패키지');
  });

  test('server managed partner values remain authoritative in the app', () {
    final aligned = alignPartnerDirectory([
      {
        'id': 51,
        'name': '랩스타모터스 새 이름',
        'region': '부산 해운대구',
        'branch_label': '본점',
        'address': '관리자에서 수정한 주소',
        'service_categories': ['전기차 정비'],
      },
    ]);

    expect(aligned, hasLength(1));
    expect(aligned.single['name'], '랩스타모터스 새 이름');
    expect(aligned.single['region'], '부산 해운대구');
    expect(aligned.single['branch_label'], '본점');
    expect(aligned.single['address'], '관리자에서 수정한 주소');
    expect(aligned.single['service_categories'], ['전기차 정비']);
    expect(aligned.single['region_group'], '전라/경상/충청 협력업체');
  });

  test('accident repair partners use requested labels and order', () {
    final aligned = alignPartnerDirectory([
      {
        'name': '랩스타모터스',
        'region': '경기 광주',
        'region_group': '전라/경상/충청 협력업체',
        'category': '정비',
        'service_categories': ['정비'],
      },
      {
        'name': '리본모터스 분당',
        'region': '경기 분당',
        'region_group': '전라/경상/충청 협력업체',
      },
      {
        'name': '아이모터스랩',
        'region': '경기 용인 죽전',
        'branch_label': '죽전점',
      },
      {
        'name': '아이모터스랩',
        'region': '서울 성수동',
        'branch_label': '성수점',
      },
    ]);

    final accidentPartners = sortAccidentRepairPartners(aligned
        .where((partner) =>
            partner['category'] == '사고수리 전문' ||
            (partner['service_categories'] as List? ?? [])
                .any((category) => category.toString().contains('사고')))
        .toList());

    expect(
      accidentPartners
          .map((partner) =>
              '${partner['name']}${partner['branch_label'] == null ? '' : ' · ${partner['branch_label']}'}')
          .toList(),
      ['아이모터스랩 · 성수점', '아이모터스랩 · 죽전점', '리본모터스', '랩스타모터스'],
    );
    expect(
      accidentPartners
          .every((partner) => partner['region_group'] == '서울/경기 협력업체'),
      isTrue,
    );
  });
}
