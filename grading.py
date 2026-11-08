"""GradeFlow grading logic. No network or UI dependencies."""
import csv
import io
import math
import re
import statistics
import unicodedata


def normalize(value):
    text = str(value).translate(str.maketrans('①②③④⑤❶❷❸❹❺', '1234512345'))
    return unicodedata.normalize('NFKC', text).strip()


def parse_key(text):
    """Read vertical triples or explicitly labelled horizontal tables, never infer weights."""
    rows = {}
    def add(number, answer, points):
        number = int(number)
        answer, points = int(answer), float(points)
        if number < 1 or answer not in range(1, 6) or not math.isfinite(points) or points <= 0:
            raise ValueError(f'{number}번 문항의 정답(1~5)과 양수 배점을 확인하세요.')
        if number in rows:
            raise ValueError(f'{number}번 문항이 중복되었습니다.')
        rows[number] = {'문제번호': number, '정답': answer, '배점': points}

    if not text.strip():
        raise ValueError('PDF에서 텍스트를 찾지 못했습니다. 스캔 이미지 대신 텍스트를 포함한 정답 PDF를 업로드해 주세요.')
    # Keep circled answers as explicit separators before NFKC removes them.
    remaining = []
    circled = re.compile(r'(\d(?:\s*\d){0,2})\s*([①②③④⑤❶❷❸❹❺])\s*(\d+(?:\.\d+)?)')
    for line in text.splitlines():
        matches = list(circled.finditer(line))
        if matches and not circled.sub('', line).strip():
            for match in matches:
                add(re.sub(r'\s', '', match[1]), normalize(match[2]), match[3])
        else:
            remaining.append(line)
    lines = normalize('\n'.join(remaining)).splitlines()
    horizontal = {}
    for line in lines:
        label = re.match(r'^\s*(문항\s*번호|문제\s*번호|문항|번호|정답|배점)\s*[:：|,\t ]+(.+)$', line)
        if label:
            kind = '정답' if label[1] == '정답' else '배점' if label[1] == '배점' else '번호'
            content = re.sub(r'[|,;\t]', ' ', label[2])
            content = re.sub(r'(?<=\d)[번점]', '', content).strip()
            if re.fullmatch(r'\d+(?:\.\d+)?(?:\s+\d+(?:\.\d+)?)*', content):
                if kind in horizontal:
                    raise ValueError('가로 정답표의 행이 중복되었거나 순서가 불명확합니다. 정답 PDF를 확인해 주세요.')
                horizontal[kind] = content.split()
                if len(horizontal) == 3:
                    lengths = {len(v) for v in horizontal.values()}
                    if len(lengths) != 1:
                        raise ValueError('가로 정답표의 문항·정답·배점 개수가 다릅니다.')
                    for n, a, p in zip(horizontal['번호'], horizontal['정답'], horizontal['배점']):
                        if not n.isdigit() or not a.isdigit():
                            raise ValueError('문항 번호와 정답은 정수여야 합니다.')
                        add(n, a, p)
                    horizontal = {}
                continue
        cleaned = re.sub(r'[|,;\t]', ' ', line)
        cleaned = re.sub(r'(?<=\d)[번점]', '', cleaned).strip()
        # One or more complete triples on the same PDF row.
        triple = r'(\d{1,3})\s+([1-5])\s+(\d+(?:\.\d+)?)'
        if re.fullmatch(r'(?:' + triple + r')(?:\s+' + triple + r')*', cleaned):
            for number, answer, points in re.findall(triple, cleaned):
                add(number, answer, points)
    if horizontal:
        raise ValueError('가로 정답표에 문항 번호·정답·배점 행이 모두 필요합니다. 배점은 자동으로 추정하지 않습니다.')
    questions = [rows[n] for n in sorted(rows)]
    if not questions:
        raise ValueError('정답표에서 문항·정답·배점을 읽지 못했습니다. 아래 추출 원문을 확인하고 문항 번호·정답·배점이 있는 PDF를 업로드해 주세요.')
    missing = sorted(set(range(1, max(rows) + 1)) - rows.keys())
    if missing:
        raise ValueError('정답표에서 누락된 문항: ' + ', '.join(map(str, missing[:20])) + '번. 추출 원문과 실제 정답표를 확인해 주세요.')
    if len(questions) > 300:
        raise ValueError('한 번에 300문항까지 분석할 수 있습니다.')
    return questions


def parse_students(text, count):
    text = text.lstrip('\ufeff')
    delimiter = '\t' if '\t' in text.splitlines()[0] else ','
    rows = [r for r in csv.reader(io.StringIO(text), delimiter=delimiter, strict=True) if any(c.strip() for c in r)]
    if len(rows) < 2:
        raise ValueError('학생명과 Q01, Q02… 헤더 및 학생 응답을 입력하세요.')
    header = [normalize(c) for c in rows[0]]
    numbered = [(i, int(c[1:])) for i, c in enumerate(header[1:], 1) if re.fullmatch(r'Q\d+', c, re.I)]
    if sorted(n for _, n in numbered) != list(range(1, count + 1)):
        raise ValueError(f'OMR 헤더에 Q01부터 Q{count:02}까지 중복 없이 필요합니다.')
    indices = [i for i, _ in sorted(numbered, key=lambda pair: pair[1])]
    students, names = [], set()
    for row in rows[1:]:
        name = row[0].strip()
        if not name or len(name) > 100 or name in names:
            raise ValueError('학생명이 비어 있거나 중복되었거나 너무 깁니다.')
        names.add(name)
        answers = []
        for index in indices:
            value = normalize(row[index] if index < len(row) else '')
            if value and value not in ('1', '2', '3', '4', '5'):
                raise ValueError(f'{name}의 응답은 1~5 또는 빈칸이어야 합니다.')
            answers.append(int(value) if value else None)
        students.append({'name': name, 'answers': answers})
    if len(students) > 2000:
        raise ValueError('한 번에 2,000명까지 분석할 수 있습니다.')
    return students


def analyze(questions, students):
    details = []
    for student in students:
        points = [q['배점'] if a == q['정답'] else 0 for q, a in zip(questions, student['answers'])]
        details.append({**student, 'points': points, 'total': sum(points),
                        'correct': sum(a == q['정답'] for q, a in zip(questions, student['answers']))})
    scores = [s['total'] for s in details]
    if not scores or not all(math.isfinite(s) for s in scores):
        raise ValueError('채점할 학생과 배점을 확인하세요.')
    items = [{**q, '오답수': sum(s['answers'][i] != q['정답'] for s in details)} for i, q in enumerate(questions)]
    for item in items:
        item['오답률(%)'] = item['오답수'] / len(details) * 100
    return {'questions': questions, 'details': details, 'items': items,
            'facts': {'학생수': len(details), '문항수': len(questions), '만점': sum(q['배점'] for q in questions),
                      '평균': statistics.mean(scores), '중앙값': statistics.median(scores),
                      '표준편차': statistics.pstdev(scores), '최고점': max(scores),
                      '최고점학생': [s['name'] for s in details if s['total'] == max(scores)],
                      '문항별통계': items}}
