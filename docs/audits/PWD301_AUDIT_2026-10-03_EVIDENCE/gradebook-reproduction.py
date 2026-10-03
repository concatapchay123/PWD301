import os, runpy, json
os.environ['TEST_DATABASE_URL']='sqlite:///:memory:'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
cf=runpy.run_path(r'E:\PWD301\tests\conftest.py')
m=runpy.run_path(r'E:\PWD301\tests\unit\test_grading_service.py')
api=runpy.run_path(r'E:\PWD301\tests\api\test_grading_api.py')
from pwd301.extensions import db
from pwd301.models.attempt_regrade import AssessmentAttempt, AttemptQuestionGradeHistory
from pwd301.services.attempt_service import list_assessment_student_results, list_pending_grading_attempts, grade_essay_question, get_instructor_attempt_evaluation

def setup():
    gen=cf['app'].__wrapped__()
    app=next(gen)
    roles=m['setup_roles'].__wrapped__(app)
    admin=m['admin_user'].__wrapped__(app,roles)
    inst=m['instructor_user'].__wrapped__(app,roles)
    student=m['student_user'].__wrapped__(app,roles)
    course=m['published_course'].__wrapped__(app,inst,admin)
    enrolled=m['enrolled_student'].__wrapped__(app,student,course)
    return gen,app,admin,inst,student,course,enrolled

def close(gen):
    try: next(gen)
    except StopIteration: pass

gen,app,admin,inst,student,course,enrolled=setup()
try:
    m['test_mixed_attempt_with_essay_transitions_to_pending_grading'](app,inst,enrolled,course)
    att=db.session.query(AssessmentAttempt).one()
    res=list_assessment_student_results(inst,att.assessment,session=db.session)
    pending=list_pending_grading_attempts(inst,att.assessment,session=db.session)
    print(json.dumps({'probe':'pending_gradebook_omission','attempt_status':att.status,'gradebook_total':res['total'],'pending_total':len(pending)}))
    client=app.test_client()
    headers=api['_auth_headers'](inst)
    ov=client.get('/instructor/grading',headers=headers)
    print(json.dumps({'probe':'grading_overview','http':ov.status_code,'body':ov.json}))
    essay=next(q for q in att.attempt_questions if q.question_type_snapshot=='ESSAY')
    for score in ('bogus','NaN','Infinity'):
        response=client.post(f'/instructor/attempts/{att.public_id}/grades/{essay.public_id}',json={'awarded_points':score,'reason':'valid audit reason'},headers=headers)
        print(json.dumps({'probe':'invalid_manual_score','score':score,'http':response.status_code,'body':response.json}))
        db.session.rollback()
    hidden=client.get(f'/student/attempt/{att.public_id}/result',headers=api['_auth_headers'](student))
    print(json.dumps({'probe':'student_hidden_contract','http':hidden.status_code,'keys':sorted(hidden.json),'score_status':hidden.json.get('score_status'),'raw_score':hidden.json.get('raw_score'),'aliases_absent':all(k not in hidden.json for k in ('total_score','max_points','is_passed'))}))
    adminDetail=client.get(f'/instructor/attempts/{att.public_id}/results',headers=api['_auth_headers'](admin))
    print(json.dumps({'probe':'admin_detail_without_reason','http':adminDetail.status_code,'has_student_email':bool(adminDetail.json.get('student_email'))}))
finally: close(gen)
gen,app,admin,inst,student,course,enrolled=setup()
try:
    m['test_objective_auto_grading_single_choice'](app,inst,enrolled,course)
    att=db.session.query(AssessmentAttempt).one()
    aq=att.attempt_questions[0]
    released=app.test_client().get(f'/student/attempt/{att.public_id}/result',headers=api['_auth_headers'](student))
    print(json.dumps({'probe':'student_released_contract','http':released.status_code,'keys':sorted(released.json),'aliases':{k:released.json.get(k) for k in ('score_status','raw_score','total_score','max_score','max_points','passed','is_passed')}}))
    print(json.dumps({'probe':'manual_grade_objective_before','type':aq.question_type_snapshot,'score':float(att.result.raw_score)}))
    result=grade_essay_question(inst,att,aq,0,session=db.session)
    print(json.dumps({'probe':'manual_grade_objective_after','result':result,'history_reason':db.session.query(AttemptQuestionGradeHistory).order_by(AttemptQuestionGradeHistory.id.desc()).first().reason}))
finally: close(gen)

