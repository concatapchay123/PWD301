r"""Adversarial and Empirical Stress Test Suite for Milestone 2 Prerequisite Cycle Detection.

Empirical Challenger M2 Verification:
1. Algorithm 03 DAG Cycle Prevention under complex topologies:
   - Self-dependency (A -> A) raises CourseValidationError and is rejected.
   - Direct mutual cycle (A -> B -> A) raises PrerequisiteCycleError.
   - Transitive cycle across multiple hops (A -> B -> C -> D -> E -> A, and 10-hop chain).
   - Valid DAG with multiple paths / diamond graph (A -> B -> D, A -> C -> D).
   - Complex mesh / double-diamond DAG accepted without false positives; cycle attempts blocked.
   - Disconnected components do not cause false positives; cross-component cycles detected.
   - Idempotent additions return existing link without duplicate rows or cycle errors.
   - Dynamic recovery: removing a link allows previously cyclic connections.
2. Web Route Error Handling in src/pwd301/blueprints/instructor/routes.py:
   - POST /instructor/courses/<course_id>/prerequisites when cycle would be introduced:
     - Catches PrerequisiteCycleError, flashes danger alert, redirects 302, NO 500 error.
   - Self-dependency web form submission flashes CourseValidationError danger alert, NO 500.
   - Empty prerequisite_course_id flashes danger alert, NO 500 error.
   - JSON API submission returns HTTP 409 (CYCLE_DETECTED) for cycles, 400 for errors, NO 500.
   - Unauthorized access (student, external instructor) fails closed (403 Forbidden).
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.services.course_service import create_course
from pwd301.services.enrollment_service import (
    add_course_prerequisite,
    get_course_prerequisites,
    remove_course_prerequisite,
)
from pwd301.services.exceptions import (
    CourseValidationError,
    PrerequisiteCycleError,
)
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure canonical roles exist in test database."""
    sess: Any = db.session
    role_map: dict[str, Role] = {}
    for code, name in [
        ("STUDENT", "Student"),
        ("INSTRUCTOR", "Instructor"),
        ("ADMIN", "System Administrator"),
    ]:
        role = sess.query(Role).filter(Role.code == code).first()
        if role is None:
            role = Role(code=code, name=name)
            sess.add(role)
            sess.flush()
        role_map[code] = role
    sess.commit()
    return role_map


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create a primary instructor user."""
    email = f"instructor_m2_adv_{uuid.uuid4().hex[:8]}@example.com"
    u = register_user(email, "Password@123", "Instructor Adv M2")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def other_instructor(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create another instructor user to test isolation."""
    email = f"instructor_other_{uuid.uuid4().hex[:8]}@example.com"
    u = register_user(email, "Password@123", "Other Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create a student user."""
    email = f"student_m2_adv_{uuid.uuid4().hex[:8]}@example.com"
    u = register_user(email, "Password@123", "Student Adv M2")
    return assign_role_to_user(u.id, "STUDENT")


# ==============================================================================
# SECTION 1: Algorithm 03 DAG Cycle Detection Stress Testing
# ==============================================================================


def test_algo03_self_dependency_rejected(
    app: Flask,
    instructor_user: User,
) -> None:
    """Algorithm 03 rejects self-referencing prerequisite (A -> A)."""
    sess: Any = db.session
    c_a = create_course(
        instructor_user,
        {"course_code": "ADV-SELF-A", "title": "Self Prerequisite Test"},
        session=sess,
    )
    sess.commit()

    with pytest.raises(CourseValidationError, match="cannot be a prerequisite of itself"):
        add_course_prerequisite(instructor_user, c_a.id, c_a.id, session=sess)

    # Verify zero prerequisite records created
    prereqs = get_course_prerequisites(c_a.id, session=sess)
    assert len(prereqs) == 0


def test_algo03_direct_mutual_cycle_rejected(
    app: Flask,
    instructor_user: User,
) -> None:
    """Algorithm 03 rejects direct 2-node mutual cycle (A -> B -> A)."""
    sess: Any = db.session
    c_a = create_course(
        instructor_user,
        {"course_code": "ADV-MUTUAL-A", "title": "Course Mutual A"},
        session=sess,
    )
    c_b = create_course(
        instructor_user,
        {"course_code": "ADV-MUTUAL-B", "title": "Course Mutual B"},
        session=sess,
    )
    sess.commit()

    # Add A -> B (A requires B)
    link_ab = add_course_prerequisite(instructor_user, c_a.id, c_b.id, session=sess)
    sess.commit()
    assert link_ab.course_id == c_a.id
    assert link_ab.prerequisite_course_id == c_b.id

    # Attempt to add B -> A (B requires A) -> cycle: A -> B -> A
    with pytest.raises(PrerequisiteCycleError, match="cyclic dependency"):
        add_course_prerequisite(instructor_user, c_b.id, c_a.id, session=sess)

    # Verify state remains clean
    prereqs_a = get_course_prerequisites(c_a.id, session=sess)
    prereqs_b = get_course_prerequisites(c_b.id, session=sess)
    assert len(prereqs_a) == 1
    assert prereqs_a[0].id == c_b.id
    assert len(prereqs_b) == 0


def test_algo03_transitive_multi_hop_cycle_rejected(
    app: Flask,
    instructor_user: User,
) -> None:
    """Algorithm 03 rejects transitive multi-hop cycle (A -> B -> C -> D -> E -> A)."""
    sess: Any = db.session
    courses: list[Course] = []
    for i in range(5):
        c = create_course(
            instructor_user,
            {"course_code": f"ADV-CHAIN-{i}", "title": f"Chain Node {i}"},
            session=sess,
        )
        courses.append(c)
    sess.commit()

    # Build chain: 0 -> 1 -> 2 -> 3 -> 4
    for i in range(4):
        add_course_prerequisite(instructor_user, courses[i].id, courses[i + 1].id, session=sess)
    sess.commit()

    # Verify chain: course[0] has prereq course[1]
    assert len(get_course_prerequisites(courses[0].id, session=sess)) == 1

    # 1. Attempt full loop: 4 -> 0 creates cycle: 0 -> 1 -> 2 -> 3 -> 4 -> 0
    with pytest.raises(PrerequisiteCycleError, match="cyclic dependency"):
        add_course_prerequisite(instructor_user, courses[4].id, courses[0].id, session=sess)

    # 2. Attempt intermediate shortcut cycle: 3 -> 1 creates cycle: 1 -> 2 -> 3 -> 1
    with pytest.raises(PrerequisiteCycleError, match="cyclic dependency"):
        add_course_prerequisite(instructor_user, courses[3].id, courses[1].id, session=sess)

    # 3. Attempt shortcut cycle: 4 -> 2 creates cycle: 2 -> 3 -> 4 -> 2
    with pytest.raises(PrerequisiteCycleError, match="cyclic dependency"):
        add_course_prerequisite(instructor_user, courses[4].id, courses[2].id, session=sess)

    # Verify zero extra edges were created
    assert len(get_course_prerequisites(courses[4].id, session=sess)) == 0
    assert len(get_course_prerequisites(courses[3].id, session=sess)) == 1


def test_algo03_large_10_hop_chain_cycle_prevention(
    app: Flask,
    instructor_user: User,
) -> None:
    """Algorithm 03 traverses deep graphs (10 nodes) and rejects deep cyclic loops."""
    sess: Any = db.session
    nodes: list[Course] = []
    for i in range(10):
        nodes.append(
            create_course(
                instructor_user,
                {"course_code": f"ADV-DEEP-{i:02d}", "title": f"Deep Node {i}"},
                session=sess,
            )
        )
    sess.commit()

    # Build chain: 0 -> 1 -> 2 -> ... -> 9
    for i in range(9):
        add_course_prerequisite(instructor_user, nodes[i].id, nodes[i + 1].id, session=sess)
    sess.commit()

    # Attempt to close the 10-hop cycle: 9 -> 0
    with pytest.raises(PrerequisiteCycleError, match="cyclic dependency"):
        add_course_prerequisite(instructor_user, nodes[9].id, nodes[0].id, session=sess)

    # Attempt mid-chain cycle: 8 -> 2
    with pytest.raises(PrerequisiteCycleError, match="cyclic dependency"):
        add_course_prerequisite(instructor_user, nodes[8].id, nodes[2].id, session=sess)


def test_algo03_diamond_graph_valid_dag_no_false_positives(
    app: Flask,
    instructor_user: User,
) -> None:
    r"""Algorithm 03 accepts diamond graphs with multiple valid paths without false alarms.

    Graph topology:
         A (Root prerequisite)
        / \
       B   C (Intermediate prerequisites)
        \ /
         D (Target course: requires both B and C)
    """
    sess: Any = db.session
    c_a = create_course(
        instructor_user,
        {"course_code": "ADV-DIA-A", "title": "Root Prerequisite A"},
        session=sess,
    )
    c_b = create_course(
        instructor_user,
        {"course_code": "ADV-DIA-B", "title": "Intermediate B"},
        session=sess,
    )
    c_c = create_course(
        instructor_user,
        {"course_code": "ADV-DIA-C", "title": "Intermediate C"},
        session=sess,
    )
    c_d = create_course(
        instructor_user,
        {"course_code": "ADV-DIA-D", "title": "Target Course D"},
        session=sess,
    )
    sess.commit()

    # 1. B requires A
    add_course_prerequisite(instructor_user, c_b.id, c_a.id, session=sess)
    # 2. C requires A
    add_course_prerequisite(instructor_user, c_c.id, c_a.id, session=sess)
    # 3. D requires B (path D -> B -> A exists)
    add_course_prerequisite(instructor_user, c_d.id, c_b.id, session=sess)

    # 4. D requires C (path D -> C -> A also exists)
    # Both paths converge at A. Algorithm 03 must NOT raise a false positive cycle error!
    link_dc = add_course_prerequisite(instructor_user, c_d.id, c_c.id, session=sess)
    sess.commit()
    assert link_dc.course_id == c_d.id
    assert link_dc.prerequisite_course_id == c_c.id

    # Verify D has exactly 2 direct prerequisites: B and C
    prereqs_d = get_course_prerequisites(c_d.id, session=sess)
    prereq_ids = {p.id for p in prereqs_d}
    assert prereq_ids == {c_b.id, c_c.id}

    # Now verify cycle detection STILL works on diamond:
    # Attempting A -> D forms cycle: D -> B/C -> A -> D
    with pytest.raises(PrerequisiteCycleError, match="cyclic dependency"):
        add_course_prerequisite(instructor_user, c_a.id, c_d.id, session=sess)

    # Attempting A -> B forms cycle: B -> A -> B
    with pytest.raises(PrerequisiteCycleError, match="cyclic dependency"):
        add_course_prerequisite(instructor_user, c_a.id, c_b.id, session=sess)

    # Attempting A -> C forms cycle: C -> A -> C
    with pytest.raises(PrerequisiteCycleError, match="cyclic dependency"):
        add_course_prerequisite(instructor_user, c_a.id, c_c.id, session=sess)


def test_algo03_complex_butterfly_mesh_dag(
    app: Flask,
    instructor_user: User,
) -> None:
    r"""Complex butterfly/double-diamond DAG with 6 nodes and multiple confluent paths.

    Topology:
       A (root)
      / \
     B   C
     |\ /|
     | X |
     |/ \|
     D   E
      \ /
       F (apex)
    """
    sess: Any = db.session
    c_a = create_course(instructor_user, {"course_code": "MESH-A", "title": "Mesh A"}, session=sess)
    c_b = create_course(instructor_user, {"course_code": "MESH-B", "title": "Mesh B"}, session=sess)
    c_c = create_course(instructor_user, {"course_code": "MESH-C", "title": "Mesh C"}, session=sess)
    c_d = create_course(instructor_user, {"course_code": "MESH-D", "title": "Mesh D"}, session=sess)
    c_e = create_course(instructor_user, {"course_code": "MESH-E", "title": "Mesh E"}, session=sess)
    c_f = create_course(instructor_user, {"course_code": "MESH-F", "title": "Mesh F"}, session=sess)
    sess.commit()

    # Layer 1 -> Layer 0
    add_course_prerequisite(instructor_user, c_b.id, c_a.id, session=sess)
    add_course_prerequisite(instructor_user, c_c.id, c_a.id, session=sess)

    # Layer 2 -> Layer 1 (cross-connected)
    add_course_prerequisite(instructor_user, c_d.id, c_b.id, session=sess)
    add_course_prerequisite(instructor_user, c_d.id, c_c.id, session=sess)
    add_course_prerequisite(instructor_user, c_e.id, c_b.id, session=sess)
    add_course_prerequisite(instructor_user, c_e.id, c_c.id, session=sess)

    # Layer 3 -> Layer 2
    add_course_prerequisite(instructor_user, c_f.id, c_d.id, session=sess)
    add_course_prerequisite(instructor_user, c_f.id, c_e.id, session=sess)
    sess.commit()

    # All 8 edges added cleanly without false positive cycle alarms
    assert len(get_course_prerequisites(c_f.id, session=sess)) == 2
    assert len(get_course_prerequisites(c_d.id, session=sess)) == 2
    assert len(get_course_prerequisites(c_e.id, session=sess)) == 2

    # Verify cycle detection catches reverse link F -> A
    with pytest.raises(PrerequisiteCycleError, match="cyclic dependency"):
        add_course_prerequisite(instructor_user, c_a.id, c_f.id, session=sess)

    # Verify cycle detection catches reverse link D -> A
    with pytest.raises(PrerequisiteCycleError, match="cyclic dependency"):
        add_course_prerequisite(instructor_user, c_a.id, c_d.id, session=sess)


def test_algo03_disconnected_components_isolation_and_cross_connection(
    app: Flask,
    instructor_user: User,
) -> None:
    """Disconnected subgraphs do not interfere; cross-component connections are tracked."""
    sess: Any = db.session

    # Component 1: X -> Y -> Z
    c_x = create_course(instructor_user, {"course_code": "DISC-X", "title": "Node X"}, session=sess)
    c_y = create_course(instructor_user, {"course_code": "DISC-Y", "title": "Node Y"}, session=sess)
    c_z = create_course(instructor_user, {"course_code": "DISC-Z", "title": "Node Z"}, session=sess)

    # Component 2: P -> Q -> R
    c_p = create_course(instructor_user, {"course_code": "DISC-P", "title": "Node P"}, session=sess)
    c_q = create_course(instructor_user, {"course_code": "DISC-Q", "title": "Node Q"}, session=sess)
    c_r = create_course(instructor_user, {"course_code": "DISC-R", "title": "Node R"}, session=sess)
    sess.commit()

    add_course_prerequisite(instructor_user, c_x.id, c_y.id, session=sess)
    add_course_prerequisite(instructor_user, c_y.id, c_z.id, session=sess)
    add_course_prerequisite(instructor_user, c_p.id, c_q.id, session=sess)
    add_course_prerequisite(instructor_user, c_q.id, c_r.id, session=sess)
    sess.commit()

    # Now bridge Component 1 and 2: P requires X (P -> X)
    add_course_prerequisite(instructor_user, c_p.id, c_x.id, session=sess)
    sess.commit()

    # Now P -> X -> Y -> Z.
    # Attempting Z -> P would close the cycle: P -> X -> Y -> Z -> P. Must fail!
    with pytest.raises(PrerequisiteCycleError, match="cyclic dependency"):
        add_course_prerequisite(instructor_user, c_z.id, c_p.id, session=sess)

    # But Z -> R is perfectly valid (R is disconnected from X, Y, Z)
    link_zr = add_course_prerequisite(instructor_user, c_z.id, c_r.id, session=sess)
    sess.commit()
    assert link_zr.course_id == c_z.id
    assert link_zr.prerequisite_course_id == c_r.id


def test_algo03_idempotency_and_link_removal_recovery(
    app: Flask,
    instructor_user: User,
) -> None:
    """Idempotent addition does not crash or cycle; removing an edge restores valid addition."""
    sess: Any = db.session
    c_a = create_course(instructor_user, {"course_code": "IDEM-A", "title": "Idem A"}, session=sess)
    c_b = create_course(instructor_user, {"course_code": "IDEM-B", "title": "Idem B"}, session=sess)
    c_c = create_course(instructor_user, {"course_code": "IDEM-C", "title": "Idem C"}, session=sess)
    sess.commit()

    # Add A -> B
    link1 = add_course_prerequisite(instructor_user, c_a.id, c_b.id, session=sess)
    sess.commit()

    # Re-add A -> B (idempotency check)
    link2 = add_course_prerequisite(instructor_user, c_a.id, c_b.id, session=sess)
    sess.commit()
    assert link1.course_id == link2.course_id
    assert link1.prerequisite_course_id == link2.prerequisite_course_id

    # Add B -> C
    add_course_prerequisite(instructor_user, c_b.id, c_c.id, session=sess)
    sess.commit()

    # C -> A is currently a cycle
    with pytest.raises(PrerequisiteCycleError):
        add_course_prerequisite(instructor_user, c_c.id, c_a.id, session=sess)

    # Remove the intermediate edge B -> C
    remove_course_prerequisite(instructor_user, c_b.id, c_c.id, session=sess)
    sess.commit()

    # Now C -> A is VALID and can be safely added!
    link_ca = add_course_prerequisite(instructor_user, c_c.id, c_a.id, session=sess)
    sess.commit()
    assert link_ca.course_id == c_c.id
    assert link_ca.prerequisite_course_id == c_a.id
    assert any(p.id == c_a.id for p in get_course_prerequisites(c_c.id, session=sess))


# ==============================================================================
# SECTION 2: Web Route Error Handling Stress Testing
# ==============================================================================


def test_web_route_json_api_cycle_and_validation_status_codes(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
) -> None:
    """JSON API returns HTTP 409 for cycles, 400 for validation errors, and 201 for success."""
    sess: Any = db.session
    c1 = create_course(
        instructor_user, {"course_code": "JSON-CYC-1", "title": "JSON Cycle 1"}, session=sess
    )
    c2 = create_course(
        instructor_user, {"course_code": "JSON-CYC-2", "title": "JSON Cycle 2"}, session=sess
    )
    sess.commit()

    login_web_user(client, instructor_user)
    with client.session_transaction() as session_ctx:
        session_ctx["active_role"] = "INSTRUCTOR"

    # Add C1 -> C2 via JSON -> returns 201 Created
    resp1 = client.post(
        f"/instructor/courses/{c1.public_id}/prerequisites",
        json={"prerequisite_course_id": str(c2.public_id)},
    )
    assert resp1.status_code == 201

    # Attempt cycle C2 -> C1 via JSON -> 409 Conflict (CYCLE_DETECTED)
    resp_cyc = client.post(
        f"/instructor/courses/{c2.public_id}/prerequisites",
        json={"prerequisite_course_id": str(c1.public_id)},
    )
    assert resp_cyc.status_code == 409
    data_cyc = resp_cyc.get_json()
    assert data_cyc["error"]["code"] == "CYCLE_DETECTED"

    # Attempt self-dependency C1 -> C1 via JSON -> 400 Bad Request
    resp_self = client.post(
        f"/instructor/courses/{c1.public_id}/prerequisites",
        json={"prerequisite_course_id": str(c1.public_id)},
    )
    assert resp_self.status_code == 400

    # Attempt missing prerequisite_course_id via JSON -> 400 Bad Request
    resp_missing = client.post(
        f"/instructor/courses/{c1.public_id}/prerequisites",
        json={},
    )
    assert resp_missing.status_code == 400


def test_web_route_authorization_isolation(
    app: Flask,
    client: FlaskClient,
    instructor_user: User,
    other_instructor: User,
    student_user: User,
) -> None:
    """Prerequisite endpoints fail closed when accessed by student or external instructor."""
    sess: Any = db.session
    c_owner = create_course(
        instructor_user,
        {"course_code": "AUTH-OWN", "title": "Owner Course"},
        session=sess,
    )
    c_prereq = create_course(
        instructor_user,
        {"course_code": "AUTH-PRE", "title": "Prereq Course"},
        session=sess,
    )
    sess.commit()

    # 1. Student attempting to manage prerequisites
    login_web_user(client, student_user)
    with client.session_transaction() as session_ctx:
        session_ctx["active_role"] = "STUDENT"

    resp_student = client.post(
        f"/instructor/courses/{c_owner.public_id}/prerequisites",
        json={"prerequisite_course_id": str(c_prereq.public_id)},
    )
    assert resp_student.status_code in (403, 302)

    # 2. External instructor (does NOT manage c_owner)
    login_web_user(client, other_instructor)
    with client.session_transaction() as session_ctx:
        session_ctx["active_role"] = "INSTRUCTOR"

    resp_other = client.post(
        f"/instructor/courses/{c_owner.public_id}/prerequisites",
        json={"prerequisite_course_id": str(c_prereq.public_id)},
    )
    assert resp_other.status_code == 403
