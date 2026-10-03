import os, sys, json, uuid
os.environ['TEST_DATABASE_URL']='sqlite:///:memory:'
sys.path.insert(0, r'E:\PWD301\src')
from pwd301 import create_app
from pwd301.extensions import db
from pwd301.models.identity import Role
from pwd301.models.course import Course, LearningUnit, CourseChangeRequest
from pwd301.models.notification_audit import AuditEvent, Notification
from pwd301.services.user_service import register_user, assign_role_to_user
from pwd301.services.course_service import create_course, update_course
from pwd301.services.session_auth_service import create_auth_session
from pwd301.models.types import utc_now
app=create_app('testing')
with app.app_context():
 db.create_all()
 for code in ('STUDENT','INSTRUCTOR','ADMIN'): db.session.add(Role(code=code,name=code))
 db.session.commit()
 instructor=assign_role_to_user(register_user('audit-instructor@example.com','Password@123','Audit Instructor').id,'INSTRUCTOR')
 admin=assign_role_to_user(register_user('audit-admin@example.com','Password@123','Audit Admin').id,'ADMIN')
 course=Course(course_code='AUDITPUB',course_code_normalized='AUDITPUB',title='Audit published',category='CNTT',owner_instructor_id=instructor.id,status='PUBLISHED',created_at=utc_now(),updated_at=utc_now())
 db.session.add(course); db.session.commit()
 client=app.test_client()
 _, raw_key=create_auth_session(instructor,session=db.session);db.session.commit()
 with client.session_transaction() as s:
  s['_user_id']=str(instructor.id);s['auth_session_key']=raw_key;s['auth_version']=instructor.auth_version;s['auth_source']='SESSION'
 result={}
 for label,identifier in [('uuid',str(course.public_id)),('numeric',str(course.id))]:
  response=client.post(f'/instructor/courses/{identifier}/learning-units',json={'title':label+' unit'})
  result[label]={'http_status':response.status_code,'unit_count':db.session.query(LearningUnit).filter(LearningUnit.course_id==course.id).count(),'request_count':db.session.query(CourseChangeRequest).filter(CourseChangeRequest.course_id==course.id).count()}
 notes_before=db.session.query(Notification).filter(Notification.user_id==instructor.id).count()
 try:
  update_course(admin,str(course.public_id),{'description':'Changed without admin reason'})
  audit=db.session.query(AuditEvent).filter(AuditEvent.action=='COURSE_UPDATED').order_by(AuditEvent.id.desc()).first()
  result['admin_edit_no_reason']={'accepted':True,'description_changed':course.description=='Changed without admin reason','audit_reason':audit.reason,'performed_as_admin':audit.performed_as_admin,'owner_notifications_delta':db.session.query(Notification).filter(Notification.user_id==instructor.id).count()-notes_before}
 except Exception as exc: result['admin_edit_no_reason']={'accepted':False,'error_type':type(exc).__name__}
 from pwd301.services.jwt_auth_service import create_token_pair
 other=assign_role_to_user(register_user('audit-other@example.com','Password@123','Audit Other').id,'INSTRUCTOR')
 course.status='SUBMITTED_FOR_REVIEW'; db.session.commit()
 tokens=create_token_pair(other)
 resp=client.post(f'/api/courses/{course.public_id}/submit',json={},headers={'Authorization':'Bearer '+tokens['access_token']})
 result['non_owner_idempotent_submit']={'http_status':resp.status_code,'response':resp.get_json()}
 print(json.dumps(result,ensure_ascii=False,indent=2))
 db.session.remove(); db.drop_all()





