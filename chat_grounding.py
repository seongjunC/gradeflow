"""Resolve explicit student references and prepare computed assessment context."""
import re


def student_references(data, text):
    ids = [next(part for part in match if part) for match in re.findall(
        r'(?<!\d)(\d+)\s*번\s*학생|(?<!\d)(\d+)\s*학생|학생\s*(\d+)(?!\d)', text)]
    selected, missing, ambiguous = [], [], []
    for number in dict.fromkeys(ids):
        matches = [s for s in data['details'] if re.findall(r'\d+', s['name']) == [number]]
        if not matches:
            missing.append(number)
        elif len(matches) > 1:
            ambiguous.append(number)
        elif matches[0] not in selected:
            selected.append(matches[0])
    for student in data['details']:
        if not re.search(r'\d', student['name']) and student['name'] in text and student not in selected:
            selected.append(student)
    return selected, missing, ambiguous


def assessment_context(data, messages):
    selected = []
    for message in messages[-8:]:
        references, _, _ = student_references(data, message['content'])
        for student in references:
            if student not in selected:
                selected.append(student)
    lowest = min(s['total'] for s in data['details'])
    most_wrong = max(item['오답수'] for item in data['items'])
    return {
        '계산된사실': {**data['facts'], '최저점': lowest,
                      '최저점학생': [s['name'] for s in data['details'] if s['total'] == lowest],
                      '최다오답문항': [item for item in data['items'] if item['오답수'] == most_wrong and most_wrong > 0]},
        '학생점수': [{'학생명': s['name'], '점수': s['total'], '정답수': s['correct']} for s in data['details']],
        '질문에언급된학생상세': selected,
        '정답배점': data['questions'], '문제지원문': data['paper_text'],
        '자료범위': '이번 시험 점수·학생 답안·정답 배점·문제지 텍스트만 제공됨. 출석·수업 참여·과거 시험 기록은 없음.',
    }


def grounded_reply(data, messages):
    """Answer exact lookups locally; leave interpretation and generation to the model."""
    question = messages[-1]['content'].strip()
    selected, missing, ambiguous = student_references(data, question)
    if missing:
        return '현재 평가 자료에 ' + ', '.join(f'{n}번 학생' for n in missing) + '은 없습니다. 학생 번호를 확인해 주세요.'
    if ambiguous:
        return ', '.join(f'{n}번' for n in ambiguous) + '에 해당하는 학생이 여러 명입니다. 정확한 학생명을 알려주세요.'
    if selected and re.fullmatch(r'[\s\S]*?(?:몇\s*점(?:이야|인가요|이니|이지)?|점수(?:는|가)?(?:\s*(?:얼마야|몇이야|알려줘|알려주세요))?)[?？.!\s]*', question):
        return '\n\n'.join(f"**{s['name']}**의 점수는 **{s['total']:g}점 / {data['facts']['만점']:g}점**입니다." for s in selected)
    if selected and re.search(r'출석|참여|참석|결석', question) and re.search(r'어제|수업|지난|오늘', question):
        return '제공된 자료에는 ' + ', '.join(s['name'] for s in selected) + '의 출석·수업 참여 기록이 없어 확인할 수 없습니다.'
    return None
