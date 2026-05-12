# تقرير مراجعة موديول الجدول المدرسي وربطه بباقي البرنامج

**Generated at:** 2026-05-12 09:18:29 EEST

**Project root:** `/home/pc/mk`


## 1) ملخص تنفيذي أولي

- هذا التقرير يفحص الموجود فعليًا داخل فولدر المشروع.
- يركز على جزء الجدول المدرسي، الربط مع المدارس، الكنترول، الموظفين، وقاعدة البيانات.
- أي نقص مذكور هنا مبني على فحص الملفات، Routes، APIs، والجداول الحالية.


## 2) حالة Git والملفات المعدلة


### git status

```text
fatal: not a git repository (or any parent up to mount point /)
Stopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set).
```

### آخر commits

```text
fatal: not a git repository (or any parent up to mount point /)
Stopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set).
```

## 3) حالة Docker والخدمات


### docker compose ps

```text
NAME                 IMAGE                COMMAND                  SERVICE    CREATED        STATUS             PORTS
mk_school_backend    mk-backend           "uvicorn app.main:ap…"   backend    25 hours ago   Up 16 hours        0.0.0.0:8100->8000/tcp, [::]:8100->8000/tcp
mk_school_frontend   node:22-alpine       "docker-entrypoint.s…"   frontend   34 hours ago   Up About an hour   0.0.0.0:3100->3000/tcp, [::]:3100->3000/tcp
mk_school_postgres   postgres:16-alpine   "docker-entrypoint.s…"   postgres   34 hours ago   Up 25 hours        0.0.0.0:55433->5432/tcp, [::]:55433->5432/tcp
mk_school_redis      redis:7-alpine       "docker-entrypoint.s…"   redis      34 hours ago   Up 25 hours        0.0.0.0:56379->6379/tcp, [::]:56379->6379/tcp
```

### backend logs آخر 120 سطر

```text
mk_school_backend  |            ^^^^^^^^^^^^^^^^^
mk_school_backend  |   File "/app/app/api/v1/school_timetable_operational.py", line 54, in summary
mk_school_backend  |     result = await db.execute(text("""
mk_school_backend  |              ^^^^^^^^^^^^^^^^^^^^^^^^^
mk_school_backend  |   File "/usr/local/lib/python3.12/site-packages/sqlalchemy/ext/asyncio/session.py", line 449, in execute
mk_school_backend  |     result = await greenlet_spawn(
mk_school_backend  |              ^^^^^^^^^^^^^^^^^^^^^
mk_school_backend  |   File "/usr/local/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 201, in greenlet_spawn
mk_school_backend  |     result = context.throw(*sys.exc_info())
mk_school_backend  |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
mk_school_backend  |   File "/usr/local/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 2351, in execute
mk_school_backend  |     return self._execute_internal(
mk_school_backend  |            ^^^^^^^^^^^^^^^^^^^^^^^
mk_school_backend  |   File "/usr/local/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 2258, in _execute_internal
mk_school_backend  |     result = conn.execute(
mk_school_backend  |              ^^^^^^^^^^^^^
mk_school_backend  |   File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1419, in execute
mk_school_backend  |     return meth(
mk_school_backend  |            ^^^^^
mk_school_backend  |   File "/usr/local/lib/python3.12/site-packages/sqlalchemy/sql/elements.py", line 527, in _execute_on_connection
mk_school_backend  |     return connection._execute_clauseelement(
mk_school_backend  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
mk_school_backend  |   File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1641, in _execute_clauseelement
mk_school_backend  |     ret = self._execute_context(
mk_school_backend  |           ^^^^^^^^^^^^^^^^^^^^^^
mk_school_backend  |   File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1846, in _execute_context
mk_school_backend  |     return self._exec_single_context(
mk_school_backend  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^
mk_school_backend  |   File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1986, in _exec_single_context
mk_school_backend  |     self._handle_dbapi_exception(
mk_school_backend  |   File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 2363, in _handle_dbapi_exception
mk_school_backend  |     raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
mk_school_backend  |   File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
mk_school_backend  |     self.dialect.do_execute(
mk_school_backend  |   File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
mk_school_backend  |     cursor.execute(statement, parameters)
mk_school_backend  |   File "/usr/local/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 585, in execute
mk_school_backend  |     self._adapt_connection.await_(
mk_school_backend  |   File "/usr/local/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 132, in await_only
mk_school_backend  |     return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
mk_school_backend  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
mk_school_backend  |   File "/usr/local/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 196, in greenlet_spawn
mk_school_backend  |     value = await result
mk_school_backend  |             ^^^^^^^^^^^^
mk_school_backend  |   File "/usr/local/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 563, in _prepare_and_execute
mk_school_backend  |     self._handle_exception(error)
mk_school_backend  |   File "/usr/local/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 513, in _handle_exception
mk_school_backend  |     self._adapt_connection._handle_exception(error)
mk_school_backend  |   File "/usr/local/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 797, in _handle_exception
mk_school_backend  |     raise translated_error from error
mk_school_backend  | sqlalchemy.exc.ProgrammingError: (sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError) <class 'asyncpg.exceptions.UndefinedColumnError'>: column "employee_id" does not exist
mk_school_backend  | [SQL: 
mk_school_backend  |         SELECT
mk_school_backend  |           (SELECT count(*) FROM school.teachers) AS teachers_count,
mk_school_backend  |           (SELECT count(*) FROM school.teachers WHERE employee_id IS NOT NULL) AS hr_linked_teachers_count,
mk_school_backend  |           (SELECT count(*) FROM school.school_classes) AS classes_count,
mk_school_backend  |           (SELECT count(*) FROM school.classrooms) AS classrooms_count,
mk_school_backend  |           (SELECT count(*) FROM school.lesson_periods) AS periods_count,
mk_school_backend  |           (SELECT count(*) FROM school.timetable_versions) AS versions_count,
mk_school_backend  |           (SELECT count(*) FROM school.timetable_slots) AS slots_count,
mk_school_backend  |           (SELECT count(*) FROM school.timetable_import_batches) AS imports_count,
mk_school_backend  |           (SELECT count(*) FROM school.vw_school_timetable_conflicts) AS hard_conflicts_count
mk_school_backend  |     ]
mk_school_backend  | (Background on this error at: https://sqlalche.me/e/20/f405)
mk_school_backend  | INFO:     172.18.0.1:38908 - "GET /api/v1/school-timetable/teacher-load HTTP/1.1" 200 OK
mk_school_backend  | INFO:     172.18.0.1:38886 - "GET /api/v1/school-timetable/grid HTTP/1.1" 200 OK
mk_school_backend  | WARNING:  WatchFiles detected changes in 'app/api/v1/school_timetable_operational.py'. Reloading...
mk_school_backend  | INFO:     Shutting down
mk_school_backend  | INFO:     Waiting for application shutdown.
mk_school_backend  | INFO:     Application shutdown complete.
mk_school_backend  | INFO:     Finished server process [18]
mk_school_backend  | INFO:     Started server process [23]
mk_school_backend  | INFO:     Waiting for application startup.
mk_school_backend  | INFO:     Application startup complete.
mk_school_backend  | WARNING:  WatchFiles detected changes in 'app/api/v1/school_timetable_operational.py'. Reloading...
mk_school_backend  | INFO:     Shutting down
mk_school_backend  | INFO:     Waiting for application shutdown.
mk_school_backend  | INFO:     Application shutdown complete.
mk_school_backend  | INFO:     Finished server process [23]
mk_school_backend  | INFO:     Started server process [24]
mk_school_backend  | INFO:     Waiting for application startup.
mk_school_backend  | INFO:     Application startup complete.
mk_school_backend  | WARNING:  WatchFiles detected changes in 'app/api/v1/school_timetable_operational.py'. Reloading...
mk_school_backend  | INFO:     Shutting down
mk_school_backend  | INFO:     Waiting for application shutdown.
mk_school_backend  | INFO:     Application shutdown complete.
mk_school_backend  | INFO:     Finished server process [24]
mk_school_backend  | INFO:     Started server process [25]
mk_school_backend  | INFO:     Waiting for application startup.
mk_school_backend  | INFO:     Application startup complete.
mk_school_backend  | WARNING:  WatchFiles detected changes in 'app/api/v1/school_timetable_operational.py'. Reloading...
mk_school_backend  | INFO:     Shutting down
mk_school_backend  | INFO:     Waiting for application shutdown.
mk_school_backend  | INFO:     Application shutdown complete.
mk_school_backend  | INFO:     Finished server process [25]
mk_school_backend  | INFO:     Started server process [26]
mk_school_backend  | INFO:     Waiting for application startup.
mk_school_backend  | INFO:     Application startup complete.
mk_school_backend  | WARNING:  WatchFiles detected changes in 'app/api/v1/school_timetable_operational.py'. Reloading...
mk_school_backend  | INFO:     Shutting down
mk_school_backend  | INFO:     Waiting for application shutdown.
mk_school_backend  | INFO:     Application shutdown complete.
mk_school_backend  | INFO:     Finished server process [26]
mk_school_backend  | INFO:     Started server process [27]
mk_school_backend  | INFO:     Waiting for application startup.
mk_school_backend  | INFO:     Application startup complete.
mk_school_backend  | WARNING:  WatchFiles detected changes in 'app/api/v1/platform.py'. Reloading...
mk_school_backend  | INFO:     Shutting down
mk_school_backend  | INFO:     Waiting for application shutdown.
mk_school_backend  | INFO:     Application shutdown complete.
mk_school_backend  | INFO:     Finished server process [27]
mk_school_backend  | INFO:     Started server process [28]
mk_school_backend  | INFO:     Waiting for application startup.
mk_school_backend  | INFO:     Application startup complete.
mk_school_backend  | INFO:     172.18.0.5:32938 - "GET /api/v1/platform/overview HTTP/1.1" 200 OK
mk_school_backend  | INFO:     172.18.0.1:43052 - "GET /health HTTP/1.1" 200 OK
mk_school_backend  | INFO:     172.18.0.1:55906 - "GET /api/v1/school-timetable/summary HTTP/1.1" 200 OK
mk_school_backend  | INFO:     172.18.0.1:42874 - "GET /api/v1/school-timetable/quality HTTP/1.1" 200 OK
mk_school_backend  | INFO:     172.18.0.1:42878 - "GET /api/v1/school-timetable/readiness HTTP/1.1" 200 OK
mk_school_backend  | INFO:     172.18.0.5:34868 - "GET /api/v1/school-timetable/readiness HTTP/1.1" 200 OK
```

### frontend logs آخر 120 سطر

```text
mk_school_frontend  |   pid: 181,
mk_school_frontend  |   stdout: <Buffer >,
mk_school_frontend  |   stderr: <Buffer >,
mk_school_frontend  |   digest: '1875598138'
mk_school_frontend  | }
mk_school_frontend  |  POST / 500 in 293ms
mk_school_frontend  |  ⨯ [Error: Command failed: test -f /srv/app/.env && echo EXISTS | base64 -w 0] {
mk_school_frontend  |   status: 1,
mk_school_frontend  |   signal: null,
mk_school_frontend  |   output: [Array],
mk_school_frontend  |   pid: 182,
mk_school_frontend  |   stdout: <Buffer >,
mk_school_frontend  |   stderr: <Buffer >,
mk_school_frontend  |   digest: '674302394'
mk_school_frontend  | }
mk_school_frontend  |  POST / 500 in 280ms
mk_school_frontend  |  ⨯ [Error: Command failed: test -f /root/.env && echo EXISTS | base64 -w 0] {
mk_school_frontend  |   status: 1,
mk_school_frontend  |   signal: null,
mk_school_frontend  |   output: [Array],
mk_school_frontend  |   pid: 183,
mk_school_frontend  |   stdout: <Buffer >,
mk_school_frontend  |   stderr: <Buffer >,
mk_school_frontend  |   digest: '360281370'
mk_school_frontend  | }
mk_school_frontend  |  POST / 500 in 295ms
mk_school_frontend  |  GET /login?a= 404 in 31ms
mk_school_frontend  |  POST / 303 in 74ms
mk_school_frontend  |  GET /login?a=bHM6IC92YXIvd3d3Ly5lbnYqOiBObyBzdWNoIGZpbGUgb3IgZGlyZWN0b3J5Cg%3D%3D 404 in 17ms
mk_school_frontend  |  POST / 303 in 51ms
mk_school_frontend  |  GET /login?a=L2FwcC8uZW52LmxvY2FsCg%3D%3D 404 in 27ms
mk_school_frontend  |  POST / 303 in 60ms
mk_school_frontend  |  GET /login?a= 404 in 32ms
mk_school_frontend  |  POST / 303 in 66ms
mk_school_frontend  |  GET /login?a=bHM6IC9vcHQvLmVudio6IE5vIHN1Y2ggZmlsZSBvciBkaXJlY3RvcnkK 404 in 21ms
mk_school_frontend  |  POST / 303 in 64ms
mk_school_frontend  |  GET /login?a= 404 in 29ms
mk_school_frontend  |  POST / 303 in 72ms
mk_school_frontend  |  GET /login?a=bHM6IC9zcnYvLmVudio6IE5vIHN1Y2ggZmlsZSBvciBkaXJlY3RvcnkK 404 in 28ms
mk_school_frontend  |  POST / 303 in 68ms
mk_school_frontend  |  GET /login?a= 404 in 18ms
mk_school_frontend  |  POST / 303 in 63ms
mk_school_frontend  |  GET /login?a=bHM6IC9ob21lLy5lbnYqOiBObyBzdWNoIGZpbGUgb3IgZGlyZWN0b3J5Cg%3D%3D 404 in 18ms
mk_school_frontend  |  POST / 303 in 50ms
mk_school_frontend  |  GET /login?a=VGtWWVZGOVFWVUpNU1VOZlFWQkpYMEpCVTBWZlZWSk1QV2gwZEhBNkx5OXNiMk5oYkdodmMzUTZPREV3TUFwQlVFbGZTVTVVUlZKT1FVeGZRa0ZUUlY5VlVrdzlhSFIwY0RvdkwyeHZZMkZzYUc5emREbzRNVEF3Q2c9PQ%3D%3D 404 in 31ms
mk_school_frontend  |  POST / 303 in 75ms
mk_school_frontend  |  GET /login?a=VGtWWVZGOVFWVUpNU1VOZlFWQkpYMEpCVTBWZlZWSk1QV2gwZEhBNkx5OXNiMk5oYkdodmMzUTZPREV3TUFwQlVFbGZTVTVVUlZKT1FVeGZRa0ZUUlY5VlVrdzlhSFIwY0RvdkwyeHZZMkZzYUc5emREbzRNVEF3Q2c9PQ%3D%3D 404 in 27ms
mk_school_frontend  |  POST / 303 in 59ms
mk_school_frontend  |  GET /login?a= 404 in 29ms
mk_school_frontend  |  POST / 303 in 70ms
mk_school_frontend  |  GET /login?a= 404 in 25ms
mk_school_frontend  |  POST / 303 in 67ms
mk_school_frontend  |  GET /login?a= 404 in 22ms
mk_school_frontend  |  POST / 303 in 59ms
mk_school_frontend  |  GET /login?a= 404 in 28ms
mk_school_frontend  |  POST / 303 in 71ms
mk_school_frontend  |  GET /login?a= 404 in 25ms
mk_school_frontend  |  POST / 303 in 55ms
mk_school_frontend  |  GET /login?a= 404 in 25ms
mk_school_frontend  |  POST / 303 in 71ms
mk_school_frontend  |  GET /login?a= 404 in 30ms
mk_school_frontend  |  POST / 303 in 65ms
mk_school_frontend  |  GET /login?a= 404 in 24ms
mk_school_frontend  |  POST / 303 in 66ms
mk_school_frontend  |  POST / 200 in 60172ms
mk_school_frontend  |  POST / 200 in 60073ms
mk_school_frontend  |  POST / 200 in 60127ms
mk_school_frontend  |  POST / 200 in 60141ms
mk_school_frontend  |  POST / 200 in 60096ms
mk_school_frontend  |  ○ Compiling /timetable ...
mk_school_frontend  |  ✓ Compiled /timetable in 1748ms (462 modules)
mk_school_frontend  |  ⨯ [TypeError: Cannot read properties of undefined (reading 'clientModules')] {
mk_school_frontend  |   page: '/timetable'
mk_school_frontend  | }
mk_school_frontend  |  ○ Compiling /_error ...
mk_school_frontend  |  ✓ Compiled /_error in 681ms (1067 modules)
mk_school_frontend  |  ⨯ [Error: ENOENT: no such file or directory, open '/app/.next/server/pages/_document.js'] {
mk_school_frontend  |   errno: -2,
mk_school_frontend  |   code: 'ENOENT',
mk_school_frontend  |   syscall: 'open',
mk_school_frontend  |   path: '/app/.next/server/pages/_document.js'
mk_school_frontend  | }
mk_school_frontend  |  HEAD /timetable 500 in 9559ms
mk_school_frontend  | Attention: Next.js now collects completely anonymous telemetry regarding usage.
mk_school_frontend  | This information is used to shape Next.js' roadmap and prioritize features.
mk_school_frontend  | You can learn more, including how to opt-out if you'd not like to participate in this anonymous program, by visiting the following URL:
mk_school_frontend  | https://nextjs.org/telemetry
mk_school_frontend  | 
mk_school_frontend  | [?25h
mk_school_frontend  | 
mk_school_frontend  | up to date, audited 34 packages in 5s
mk_school_frontend  | 
mk_school_frontend  | 8 packages are looking for funding
mk_school_frontend  |   run `npm fund` for details
mk_school_frontend  | 
mk_school_frontend  | 2 vulnerabilities (1 moderate, 1 critical)
mk_school_frontend  | 
mk_school_frontend  | To address all issues, run:
mk_school_frontend  |   npm audit fix --force
mk_school_frontend  | 
mk_school_frontend  | Run `npm audit` for details.
mk_school_frontend  | 
mk_school_frontend  | > mk-school-frontend@0.1.0 dev
mk_school_frontend  | > next dev -H 0.0.0.0 -H 0.0.0.0
mk_school_frontend  | 
mk_school_frontend  |    ▲ Next.js 15.3.3
mk_school_frontend  |    - Local:        http://localhost:3000
mk_school_frontend  |    - Network:      http://0.0.0.0:3000
mk_school_frontend  |    - Environments: .env.local
mk_school_frontend  | 
mk_school_frontend  |  ✓ Starting...
mk_school_frontend  |  ✓ Ready in 3.1s
mk_school_frontend  |  ○ Compiling /timetable ...
mk_school_frontend  |  ✓ Compiled /timetable in 8.8s (736 modules)
mk_school_frontend  |  HEAD /timetable 200 in 9721ms
mk_school_frontend  |  ○ Compiling /api/timetable/[...path] ...
mk_school_frontend  |  ✓ Compiled /api/timetable/[...path] in 869ms (729 modules)
mk_school_frontend  |  GET /api/timetable/readiness 200 in 2138ms
mk_school_frontend  |  ✓ Compiled /_not-found in 433ms (668 modules)
mk_school_frontend  |  GET /wp-json/gravitysmtp/v1/tests/mock-data?page=gravitysmtp-settings 404 in 647ms
```

## 4) فحص الصحة والروابط الرئيسية


### Backend health

```text
{"status":"ok","app":"MK School ERP","locale":"ar-EG","timezone":"Africa/Cairo"}```

### Frontend timetable HEAD

```text
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
HTTP/1.1 200 OK
Vary: RSC, Next-Router-State-Tree, Next-Router-Prefetch, Next-Router-Segment-Prefetch, Accept-Encoding
Cache-Control: no-store, must-revalidate
X-Powered-By: Next.js
Content-Type: text/html; charset=utf-8
Date: Tue, 12 May 2026 06:18:35 GMT
Connection: keep-alive
Keep-Alive: timeout=5

```

### Frontend home HEAD

```text
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
HTTP/1.1 200 OK
Vary: RSC, Next-Router-State-Tree, Next-Router-Prefetch, Next-Router-Segment-Prefetch, Accept-Encoding
link: </_next/static/css/app/layout.css?v=1778566715591>; rel=preload; as="style"
Cache-Control: no-store, must-revalidate
X-Powered-By: Next.js
Content-Type: text/html; charset=utf-8
Date: Tue, 12 May 2026 06:18:35 GMT
Connection: keep-alive
Keep-Alive: timeout=5

```

### Education control HEAD

```text
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
HTTP/1.1 200 OK
Vary: RSC, Next-Router-State-Tree, Next-Router-Prefetch, Next-Router-Segment-Prefetch, Accept-Encoding
link: </_next/static/css/app/layout.css?v=1778566716083>; rel=preload; as="style"
Cache-Control: no-store, must-revalidate
X-Powered-By: Next.js
Content-Type: text/html; charset=utf-8
Date: Tue, 12 May 2026 06:18:36 GMT
Connection: keep-alive
Keep-Alive: timeout=5

```

## 5) ملفات الجدول المدرسي في الباك إند



```
backend/app/api/v1/__pycache__/school_timetable_operational.cpython-312.pyc
backend/app/api/v1/school_timetable_operational.py
backend/migrations/001_school_erp_education_control.sql
backend/migrations/004_school_timetable_operational.sql
### backend timetable files
```text

### school_timetable_operational.py أول 260 سطر

```text
from __future__ import annotations

import csv
import io
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter(prefix="/api/v1/school-timetable", tags=["school-timetable"])


class TimetableCsvImport(BaseModel):
    batch_name: str = "استيراد TimeTable"
    csv_text: str


def rows(result) -> list[dict[str, Any]]:
    return [dict(row._mapping) for row in result]


async def audit_event(
    db: AsyncSession,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    exists = await db.execute(text("SELECT to_regclass('audit.events')"))
    if exists.scalar_one() is None:
        return

    await db.execute(
        text("""
            INSERT INTO audit.events(actor, action, entity_type, entity_id, payload)
            VALUES ('school-timetable-api', :action, :entity_type, :entity_id, CAST(:payload AS jsonb))
        """),
        {
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "payload": json.dumps(payload or {}, ensure_ascii=False),
        },
    )


@router.get("/summary")
async def summary(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await db.execute(text("""
        SELECT
          (SELECT count(*) FROM school.teachers) AS teachers_count,
          (SELECT count(*) FROM school.teachers WHERE employee_id IS NOT NULL) AS hr_linked_teachers_count,
          (SELECT count(*) FROM school.school_classes) AS classes_count,
          (SELECT count(*) FROM school.subjects) AS subjects_count,
          (SELECT COALESCE(sum(weekly_lessons), 0) FROM school.curriculum_plans WHERE is_active = true) AS planned_weekly_lessons_count,
          (SELECT count(*) FROM school.timetable_constraints WHERE is_active = true AND constraint_type = 'hard') AS hard_constraints_count,
          (SELECT count(*) FROM school.timetable_constraints WHERE is_active = true AND constraint_type = 'soft') AS soft_constraints_count,
          (SELECT count(*) FROM school.classrooms) AS classrooms_count,
          (SELECT count(*) FROM school.lesson_periods) AS periods_count,
          (SELECT count(*) FROM school.timetable_versions) AS versions_count,
          (SELECT count(*) FROM school.timetable_slots) AS slots_count,
          (SELECT count(*) FROM school.timetable_generation_runs) AS generation_runs_count,
          (SELECT count(*) FROM school.timetable_import_batches) AS imports_count,
          (SELECT count(*) FROM school.vw_school_timetable_conflicts) AS hard_conflicts_count
    """))
    return dict(result.one()._mapping)


@router.get("/readiness")
async def readiness(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    data = await summary(db)
    checks = [
        {
            "code": "academic_time",
            "name_ar": "الأيام والحصص",
            "ready": data["periods_count"] > 0,
            "message_ar": "تم إعداد حصص اليوم الدراسي" if data["periods_count"] > 0 else "شغل تجهيز الأيام والحصص أولًا",
        },
        {
            "code": "school_resources",
            "name_ar": "موارد المدرسة",
            "ready": data["classes_count"] > 0 and data["subjects_count"] > 0 and data["classrooms_count"] > 0,
            "message_ar": "الفصول والمواد والقاعات جاهزة" if data["classes_count"] > 0 and data["subjects_count"] > 0 and data["classrooms_count"] > 0 else "أضف فصولًا ومواد وقاعات قبل الاعتماد",
        },
        {
            "code": "curriculum_matrix",
            "name_ar": "الخطة الأسبوعية",
            "ready": data["planned_weekly_lessons_count"] > 0,
            "message_ar": "تم إدخال Curriculum Matrix" if data["planned_weekly_lessons_count"] > 0 else "أدخل الخطة الأسبوعية قبل التوليد",
        },
        {
            "code": "hr_teacher_link",
            "name_ar": "ربط HR بالمدرسين",
            "ready": data["hr_linked_teachers_count"] > 0 or data["teachers_count"] == 0,
            "message_ar": "يوجد مدرسون مرتبطون ببرنامج الموظفين" if data["hr_linked_teachers_count"] > 0 else "زامن المدرسين من برنامج الموظفين",
        },
        {
            "code": "hard_conflicts",
            "name_ar": "التعارضات الصارمة",
            "ready": data["hard_conflicts_count"] == 0,
            "message_ar": "لا توجد تعارضات صارمة" if data["hard_conflicts_count"] == 0 else "لا تنشر جدولًا به تعارضات",
        },
        {
            "code": "published_data",
            "name_ar": "دروس الجدول",
            "ready": data["slots_count"] > 0,
            "message_ar": "يوجد جدول قابل للمراجعة" if data["slots_count"] > 0 else "استورد أو أضف دروس الجدول",
        },
    ]

    return {
        "ready": all(item["ready"] for item in checks),
        "checks": checks,
        "summary": data,
    }


@router.post("/bootstrap")
async def bootstrap(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    await db.execute(text("""
        INSERT INTO school.week_days(day_code, name_ar, sort_order)
        VALUES
        ('saturday', 'السبت', 1),
        ('sunday', 'الأحد', 2),
        ('monday', 'الإثنين', 3),
        ('tuesday', 'الثلاثاء', 4),
        ('wednesday', 'الأربعاء', 5),
        ('thursday', 'الخميس', 6)
        ON CONFLICT (day_code)
        DO UPDATE SET name_ar = EXCLUDED.name_ar, sort_order = EXCLUDED.sort_order
    """))

    await db.execute(text("""
        INSERT INTO school.lesson_periods(period_no, name_ar, starts_at, ends_at)
        VALUES
        (1, 'الحصة 1', TIME '08:00', TIME '08:45'),
        (2, 'الحصة 2', TIME '08:50', TIME '09:35'),
        (3, 'الحصة 3', TIME '09:40', TIME '10:25'),
        (4, 'الحصة 4', TIME '10:45', TIME '11:30'),
        (5, 'الحصة 5', TIME '11:35', TIME '12:20'),
        (6, 'الحصة 6', TIME '12:25', TIME '13:10'),
        (7, 'الحصة 7', TIME '13:15', TIME '14:00')
        ON CONFLICT (period_no)
        DO UPDATE SET
          name_ar = EXCLUDED.name_ar,
          starts_at = EXCLUDED.starts_at,
          ends_at = EXCLUDED.ends_at
    """))

    exists = await db.execute(text("""
        SELECT id
        FROM school.timetable_versions
        WHERE is_current = true
        ORDER BY created_at DESC
        LIMIT 1
    """))

    if exists.first() is None:
        await db.execute(text("""
            INSERT INTO school.timetable_versions(name_ar, status, is_current)
            VALUES ('جدول المدرسة الأساسي', 'draft', true)
        """))

    await audit_event(db, "bootstrap", "school_timetable", payload={"source": "document_requirements"})
    await db.commit()
    return await summary(db)


@router.get("/week-days")
async def week_days(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(text("SELECT * FROM school.week_days ORDER BY sort_order"))
    return rows(result)


@router.get("/periods")
async def periods(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(text("SELECT * FROM school.lesson_periods ORDER BY period_no"))
    return rows(result)


@router.get("/grid")
async def grid(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(text("""
        SELECT *
        FROM school.vw_school_timetable_grid
        ORDER BY day_order, period_no, class_code
        LIMIT 2000
    """))
    return rows(result)


@router.get("/teacher-load")
async def teacher_load(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(text("""
        SELECT *
        FROM school.vw_school_teacher_load
        ORDER BY weekly_lessons_count DESC, teacher_name_ar
    """))
    return rows(result)


@router.get("/quality")
async def quality(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(text("""
        SELECT *
        FROM school.vw_school_timetable_quality
        ORDER BY quality_score DESC, timetable_name_ar
    """))
    return rows(result)


@router.get("/conflicts")
async def conflicts(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(text("""
        SELECT
          c.conflict_type,
          c.severity,
          tv.name_ar AS timetable_name_ar,
          wd.name_ar AS day_name_ar,
          lp.name_ar AS period_name_ar,
          c.entity_id,
          c.conflict_count
        FROM school.vw_school_timetable_conflicts c
        JOIN school.timetable_versions tv ON tv.id = c.timetable_version_id
        JOIN school.week_days wd ON wd.id = c.week_day_id
        JOIN school.lesson_periods lp ON lp.id = c.period_id
        ORDER BY wd.sort_order, lp.period_no, c.conflict_type
    """))
    return rows(result)


@router.post("/validation/run")
async def validation_run(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    readiness_result = await readiness(db)
    conflicts_result = await conflicts(db)
    quality_result = await quality(db)
    await audit_event(
        db,
        "validation_run",
        "school_timetable",
        payload={
            "ready": readiness_result["ready"],
            "hard_conflicts": len(conflicts_result),
            "quality_items": len(quality_result),
        },
    )
    await db.commit()
    return {
        "readiness": readiness_result,
        "conflicts": conflicts_result,
        "quality": quality_result,
    }


@router.get("/reports/teachers")
```

## 6) ملفات الجدول المدرسي في الفرونت إند



```
frontend/src/app/api/timetable/[...path]/route.ts
frontend/src/app/timetable/page.tsx
### frontend timetable files
```text

### timetable page أول 220 سطر

```text
// @ts-nocheck
"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { SchoolShell } from "@/components/layout/school-shell";

async function getApi(path) {
  const res = await fetch(`/api/timetable/${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function postApi(path, body) {
  const res = await fetch(`/api/timetable/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

const sample = `day,period,class,subject,teacher,room
الأحد,1,1A,لغة عربية,أحمد محمد,فصل 1
الأحد,2,1A,رياضيات,منى علي,فصل 1
الإثنين,1,1A,علوم,سعيد حسن,معمل علوم`;

export default function TimetablePage() {
  const [summary, setSummary] = useState(null);
  const [readiness, setReadiness] = useState(null);
  const [grid, setGrid] = useState([]);
  const [loads, setLoads] = useState([]);
  const [versions, setVersions] = useState([]);
  const [conflicts, setConflicts] = useState([]);
  const [quality, setQuality] = useState([]);
  const [runs, setRuns] = useState([]);
  const [plans, setPlans] = useState([]);
  const [constraints, setConstraints] = useState([]);
  const [csv, setCsv] = useState(sample);
  const [file, setFile] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const currentVersion = useMemo(
    () => versions.find((item) => item.is_current) ?? versions[0],
    [versions]
  );

  async function load() {
    setError("");
    setLoading(true);
    try {
      const [
        nextSummary,
        nextReadiness,
        nextGrid,
        nextLoads,
        nextVersions,
        nextConflicts,
        nextQuality,
        nextRuns,
        nextPlans,
        nextConstraints
      ] =
        await Promise.all([
          getApi("summary"),
          getApi("readiness"),
          getApi("grid"),
          getApi("teacher-load"),
          getApi("versions"),
          getApi("conflicts"),
          getApi("quality"),
          getApi("runs"),
          getApi("curriculum-plans"),
          getApi("constraints")
        ]);
      setSummary(nextSummary);
      setReadiness(nextReadiness);
      setGrid(nextGrid);
      setLoads(nextLoads);
      setVersions(nextVersions);
      setConflicts(nextConflicts);
      setQuality(nextQuality);
      setRuns(nextRuns);
      setPlans(nextPlans);
      setConstraints(nextConstraints);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function runAction(path, successMessage, body) {
    setMessage("");
    setError("");
    try {
      const result = await postApi(path, body);
      setMessage(typeof successMessage === "function" ? successMessage(result) : successMessage);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function importCsv() {
    await runAction(
      "import/time-table-csv",
      (result) => `تم الاستيراد: إجمالي ${result.total_rows} / مقبول ${result.accepted_rows} / مرفوض ${result.rejected_rows}`,
      { batch_name: file || "استيراد جدول", csv_text: csv }
    );
  }

  async function runValidation() {
    await runAction(
      "validation/run",
      (result) => `تم الفحص: الجاهزية ${result.readiness.ready ? "مكتملة" : "غير مكتملة"} / التعارضات ${result.conflicts.length}`,
    );
  }

  async function runGeneration() {
    await runAction(
      "runs",
      (result) => `تم التوليد: ${result.scheduled_lessons}/${result.total_cards} حصة / جودة ${result.quality_score}`,
      { name_ar: "توليد آلي من Curriculum Matrix", clear_existing: true, make_current: true }
    );
  }

  async function exportCsv() {
    setMessage("");
    setError("");
    try {
      const result = await postApi("exports/csv");
      const blob = new Blob([result.csv_text], { type: result.content_type || "text/csv;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = result.file_name || "school-timetable.csv";
      link.click();
      URL.revokeObjectURL(url);
      setMessage(`تم تجهيز ملف التصدير: ${result.file_name}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function chooseFile(event) {
    const selected = event.target.files?.[0];
    if (!selected) return;
    setFile(selected.name);
    setCsv(await selected.text());
    setMessage(`تم اختيار الملف: ${selected.name}`);
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <SchoolShell>
      <section className="hero surface">
        <div>
          <div className="eyebrow">School Timetable</div>
          <h1>منصة الجداول المدرسية</h1>
          <p>
            تنفيذ وثيقة الجداول داخل المنصة الموحدة: ربط المدرسين من HR، موارد المدرسة،
            منع التعارضات، الاستيراد، المراجعة، الاعتماد، والنشر.
          </p>
        </div>
        <div className="hero-actions">
          <span className="badge">{readiness?.ready ? "جاهز للمراجعة" : "قيد التجهيز"}</span>
          <Link href="/hr" className="btn btn-secondary">برنامج الموظفين</Link>
          <Link href="/school" className="btn btn-secondary">برنامج المدارس</Link>
          <Link href="/education-control" className="btn btn-secondary">برنامج الكنترول</Link>
        </div>
      </section>

      {error ? <pre className="error">{error}</pre> : null}
      {message ? <div className="success mt">{message}</div> : null}
      {loading ? <div className="surface section-pad mt">جاري تحميل بيانات الجدول...</div> : null}

      <section className="grid stats mt">
        <Metric label="مدرسون" value={summary?.teachers_count} />
        <Metric label="مرتبطون بـ HR" value={summary?.hr_linked_teachers_count} />
        <Metric label="فصول" value={summary?.classes_count} />
        <Metric label="مواد" value={summary?.subjects_count} />
        <Metric label="خطة أسبوعية" value={summary?.planned_weekly_lessons_count} />
        <Metric label="قاعات" value={summary?.classrooms_count} />
        <Metric label="دروس الجدول" value={summary?.slots_count} />
        <Metric label="تشغيلات التوليد" value={summary?.generation_runs_count} />
        <Metric label="تعارضات صارمة" value={summary?.hard_conflicts_count} danger={summary?.hard_conflicts_count > 0} />
      </section>

      <section className="split mt">
        <div className="surface section-pad">
          <h2>جاهزية التنفيذ</h2>
          <div className="check-list">
            {(readiness?.checks ?? []).map((check) => (
              <div key={check.code} className="check-row">
                <span className={check.ready ? "state-dot ready" : "state-dot blocked"} />
                <div>
                  <strong>{check.name_ar}</strong>
                  <p>{check.message_ar}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="surface section-pad">
          <h2>تشغيل الوثيقة</h2>
          <div className="action-stack">
            <button className="btn" onClick={() => runAction("bootstrap", "تم تجهيز الأيام والحصص")}>
              تجهيز الأيام والحصص
            </button>
            <button className="btn btn-secondary" onClick={() => runAction("sync/hr-teachers", (r) => `تمت مزامنة ${r.synced_count} مدرس من HR`)}>
              مزامنة المدرسين من HR
```

### timetable proxy route

```text

export const dynamic = "force-dynamic";
const BACKEND = process.env.API_INTERNAL_BASE_URL || "http://backend:8000";

async function forward(req: Request, path: string[]) {
  const url = `${BACKEND}/api/v1/school-timetable/${path.join("/")}`;
  const init: RequestInit = { method: req.method, headers: {"Content-Type": req.headers.get("content-type") || "application/json"} };
  if (req.method !== "GET" && req.method !== "HEAD") init.body = await req.text();
  const res = await fetch(url, init);
  return new Response(await res.text(), { status: res.status, headers: {"Content-Type": res.headers.get("content-type") || "application/json"} });
}

export async function GET(req: Request, ctx: { params: Promise<{ path: string[] }> }) {
  const params = await ctx.params;
  return forward(req, params.path);
}
export async function POST(req: Request, ctx: { params: Promise<{ path: string[] }> }) {
  const params = await ctx.params;
  return forward(req, params.path);
}
export async function DELETE(req: Request, ctx: { params: Promise<{ path: string[] }> }) {
  const params = await ctx.params;
  return forward(req, params.path);
}
```

## 7) Routes الموجودة في Next.js



```
### frontend app routes
frontend/src/app/access-mirror/page.tsx
frontend/src/app/education-control/institutes/page.tsx
frontend/src/app/education-control/page.tsx
frontend/src/app/education-control/results/page.tsx
frontend/src/app/education-control/scores/page.tsx
frontend/src/app/education-control/settings/page.tsx
frontend/src/app/education-control/students/page.tsx
frontend/src/app/education-control/subjects/page.tsx
frontend/src/app/hr/page.tsx
frontend/src/app/operations/page.tsx
frontend/src/app/page.tsx
frontend/src/app/platform/page.tsx
frontend/src/app/school/page.tsx
frontend/src/app/timetable/page.tsx
```text

## 8) OpenAPI الخاص بالباك إند


### كل school-timetable endpoints من OpenAPI

```text
curl: (23) Failure writing output to destination
Traceback (most recent call last):
  File "<stdin>", line 2, in <module>
  File "/usr/lib/python3.12/json/__init__.py", line 293, in load
    return loads(fp.read(),
           ^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/json/__init__.py", line 346, in loads
    return _default_decoder.decode(s)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/json/decoder.py", line 337, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/json/decoder.py", line 355, in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

## 9) اختبار APIs الخاصة بالجدول المدرسي


### summary

```text
{"teachers_count":3,"hr_linked_teachers_count":0,"classes_count":1,"subjects_count":0,"planned_weekly_lessons_count":0,"hard_constraints_count":0,"soft_constraints_count":0,"classrooms_count":2,"periods_count":7,"versions_count":1,"slots_count":3,"generation_runs_count":0,"imports_count":3,"hard_conflicts_count":0}```

### grid

```text
[{"id":"713f1204-df03-434d-b686-5a250341f94c","timetable_version_id":"b272c32b-f7a3-46a7-ba82-d79892fdc7f4","timetable_name_ar":"جدول مستورد من TimeTable","class_code":"1A","class_name_ar":"1A","week_day_id":2,"day_name_ar":"الأحد","day_order":2,"period_no":1,"period_name_ar":"الحصة 1","starts_at":"08:00:00","ends_at":"08:45:00","subject_name_ar":"لغة عربية","teacher_name_ar":"أحمد محمد","room_name_ar":"فصل 1","slot_type":"lesson","notes":null},{"id":"603e5801-125f-4b4a-a10e-ac6e0f49cf3d","timetable_version_id":"b272c32b-f7a3-46a7-ba82-d79892fdc7f4","timetable_name_ar":"جدول مستورد من TimeTable","class_code":"1A","class_name_ar":"1A","week_day_id":2,"day_name_ar":"الأحد","day_order":2,"period_no":2,"period_name_ar":"الحصة 2","starts_at":"08:50:00","ends_at":"09:35:00","subject_name_ar":"رياضيات","teacher_name_ar":"منى علي","room_name_ar":"فصل 1","slot_type":"lesson","notes":null},{"id":"8dcf543a-6276-4b83-b78c-8f03420fc449","timetable_version_id":"b272c32b-f7a3-46a7-ba82-d79892fdc7f4","timetable_name_ar":"جدول مستورد من TimeTable","class_code":"1A","class_name_ar":"1A","week_day_id":3,"day_name_ar":"الإثنين","day_order":3,"period_no":1,"period_name_ar":"الحصة 1","starts_at":"08:00:00","ends_at":"08:45:00","subject_name_ar":"علوم","teacher_name_ar":"سعيد حسن","room_name_ar":"معمل علوم","slot_type":"lesson","notes":null}]```

### teacher-load

```text
[{"timetable_version_id":"b272c32b-f7a3-46a7-ba82-d79892fdc7f4","timetable_name_ar":"جدول مستورد من TimeTable","teacher_id":"4187fa3f-5de1-4109-9d2b-312210e8093f","teacher_name_ar":"أحمد محمد","weekly_lessons_count":1},{"timetable_version_id":"b272c32b-f7a3-46a7-ba82-d79892fdc7f4","timetable_name_ar":"جدول مستورد من TimeTable","teacher_id":"f4bcd97d-3944-4f4b-b1c0-d7f4a19c2c45","teacher_name_ar":"سعيد حسن","weekly_lessons_count":1},{"timetable_version_id":"b272c32b-f7a3-46a7-ba82-d79892fdc7f4","timetable_name_ar":"جدول مستورد من TimeTable","teacher_id":"e64a3d53-a940-4022-aaa1-7a390471423e","teacher_name_ar":"منى علي","weekly_lessons_count":1}]```

### teachers

```text
[{"id":"4187fa3f-5de1-4109-9d2b-312210e8093f","teacher_code":"أحمد محمد","teacher_name_ar":"أحمد محمد","phone":null,"specialization":null,"is_active":true,"created_at":"2026-05-11T07:43:32.359842Z"},{"id":"f4bcd97d-3944-4f4b-b1c0-d7f4a19c2c45","teacher_code":"سعيد حسن","teacher_name_ar":"سعيد حسن","phone":null,"specialization":null,"is_active":true,"created_at":"2026-05-11T07:43:32.359842Z"},{"id":"e64a3d53-a940-4022-aaa1-7a390471423e","teacher_code":"منى علي","teacher_name_ar":"منى علي","phone":null,"specialization":null,"is_active":true,"created_at":"2026-05-11T07:43:32.359842Z"}]```

### classes

```text
[{"id":"ca4e539c-60dc-40a6-b11a-fe06b57a81ae","class_code":"1A","class_name_ar":"1A","stage_name_ar":null,"grade_name_ar":null,"capacity":0,"is_active":true,"created_at":"2026-05-11T07:43:32.359842Z"}]```

### classrooms

```text
[{"id":"ddc875e8-852b-40e8-866b-a16d637ecfdf","room_code":"فصل 1","room_name_ar":"فصل 1","name_ar":"فصل 1","capacity":0,"floor_name":null,"is_active":true,"created_at":"2026-05-11T07:43:32.359842Z"},{"id":"ee64ebd3-bef9-43ae-806a-831836dd292e","room_code":"معمل علوم","room_name_ar":"معمل علوم","name_ar":"معمل علوم","capacity":0,"floor_name":null,"is_active":true,"created_at":"2026-05-11T07:43:32.359842Z"}]```

### periods

```text
[{"id":"3c8f9a9f-c7e6-4dbb-9ab4-2dba852f265d","period_no":1,"name_ar":"الحصة 1","starts_at":"08:00:00","ends_at":"08:45:00","is_break":false,"is_active":true,"created_at":"2026-05-11T07:30:53.974713Z"},{"id":"08f17441-ced8-4497-8a11-5037873d2b4c","period_no":2,"name_ar":"الحصة 2","starts_at":"08:50:00","ends_at":"09:35:00","is_break":false,"is_active":true,"created_at":"2026-05-11T07:30:53.974713Z"},{"id":"4df9e2d9-735a-4a99-baa8-0b6ff6d01a10","period_no":3,"name_ar":"الحصة 3","starts_at":"09:40:00","ends_at":"10:25:00","is_break":false,"is_active":true,"created_at":"2026-05-11T07:30:53.974713Z"},{"id":"b48418a3-d54e-41f3-8ead-1d1ea9d584d6","period_no":4,"name_ar":"الحصة 4","starts_at":"10:45:00","ends_at":"11:30:00","is_break":false,"is_active":true,"created_at":"2026-05-11T07:30:53.974713Z"},{"id":"1f997c03-bba6-418d-8cd8-c3b7f60f5cb1","period_no":5,"name_ar":"الحصة 5","starts_at":"11:35:00","ends_at":"12:20:00","is_break":false,"is_active":true,"created_at":"2026-05-11T07:30:53.974713Z"},{"id":"3336e57b-cc3d-425f-98c6-05c4b27cbb2e","period_no":6,"name_ar":"الحصة 6","starts_at":"12:25:00","ends_at":"13:10:00","is_break":false,"is_active":true,"created_at":"2026-05-11T07:30:53.974713Z"},{"id":"b1247831-ae82-43eb-911c-98c973ec876f","period_no":7,"name_ar":"الحصة 7","starts_at":"13:15:00","ends_at":"14:00:00","is_break":false,"is_active":true,"created_at":"2026-05-11T07:30:53.974713Z"}]```

### versions

```text
[{"id":"b272c32b-f7a3-46a7-ba82-d79892fdc7f4","name_ar":"جدول مستورد من TimeTable","status":"draft","effective_from":null,"effective_to":null,"is_current":true,"created_at":"2026-05-11T07:28:12.247209Z"}]```

## 10) فحص جداول قاعدة البيانات school


### school schema tables

```text
 table_schema |          table_name           
--------------+-------------------------------
 school       | academic_years
 school       | classrooms
 school       | curriculum_plans
 school       | grades
 school       | guardians
 school       | institutes
 school       | lesson_periods
 school       | rooms
 school       | school_classes
 school       | student_guardians
 school       | students
 school       | subjects
 school       | teachers
 school       | timetable_constraints
 school       | timetable_export_jobs
 school       | timetable_generation_runs
 school       | timetable_import_batches
 school       | timetable_import_errors
 school       | timetable_slots
 school       | timetable_versions
 school       | vw_school_teacher_load
 school       | vw_school_timetable_conflicts
 school       | vw_school_timetable_grid
 school       | vw_school_timetable_quality
 school       | week_days
(25 rows)

```

### school table row counts

```text
        table_name        | rows 
--------------------------+------
 teachers                 |    3
 school_classes           |    1
 classrooms               |    2
 week_days                |    6
 lesson_periods           |    7
 timetable_versions       |    1
 timetable_slots          |    3
 timetable_import_batches |    3
 timetable_import_errors  |    3
(9 rows)

```

### school timetable constraints/indexes

```text
 schemaname |         tablename         |                            indexname                            |                                                                                         indexdef                                                                                          
------------+---------------------------+-----------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 school     | academic_years            | academic_years_name_key                                         | CREATE UNIQUE INDEX academic_years_name_key ON school.academic_years USING btree (name)
 school     | academic_years            | academic_years_pkey                                             | CREATE UNIQUE INDEX academic_years_pkey ON school.academic_years USING btree (id)
 school     | classrooms                | classrooms_pkey                                                 | CREATE UNIQUE INDEX classrooms_pkey ON school.classrooms USING btree (id)
 school     | classrooms                | uq_school_classrooms_room_code                                  | CREATE UNIQUE INDEX uq_school_classrooms_room_code ON school.classrooms USING btree (room_code)
 school     | curriculum_plans          | curriculum_plans_pkey                                           | CREATE UNIQUE INDEX curriculum_plans_pkey ON school.curriculum_plans USING btree (id)
 school     | curriculum_plans          | curriculum_plans_school_class_id_subject_id_key                 | CREATE UNIQUE INDEX curriculum_plans_school_class_id_subject_id_key ON school.curriculum_plans USING btree (school_class_id, subject_id)
 school     | grades                    | grades_pkey                                                     | CREATE UNIQUE INDEX grades_pkey ON school.grades USING btree (id)
 school     | grades                    | grades_stage_code_grade_code_key                                | CREATE UNIQUE INDEX grades_stage_code_grade_code_key ON school.grades USING btree (stage_code, grade_code)
 school     | guardians                 | guardians_pkey                                                  | CREATE UNIQUE INDEX guardians_pkey ON school.guardians USING btree (id)
 school     | institutes                | institutes_code_key                                             | CREATE UNIQUE INDEX institutes_code_key ON school.institutes USING btree (code)
 school     | institutes                | institutes_pkey                                                 | CREATE UNIQUE INDEX institutes_pkey ON school.institutes USING btree (id)
 school     | lesson_periods            | lesson_periods_period_no_key                                    | CREATE UNIQUE INDEX lesson_periods_period_no_key ON school.lesson_periods USING btree (period_no)
 school     | lesson_periods            | lesson_periods_pkey                                             | CREATE UNIQUE INDEX lesson_periods_pkey ON school.lesson_periods USING btree (id)
 school     | rooms                     | rooms_pkey                                                      | CREATE UNIQUE INDEX rooms_pkey ON school.rooms USING btree (id)
 school     | school_classes            | school_classes_class_code_key                                   | CREATE UNIQUE INDEX school_classes_class_code_key ON school.school_classes USING btree (class_code)
 school     | school_classes            | school_classes_pkey                                             | CREATE UNIQUE INDEX school_classes_pkey ON school.school_classes USING btree (id)
 school     | school_classes            | uq_school_classes_class_code                                    | CREATE UNIQUE INDEX uq_school_classes_class_code ON school.school_classes USING btree (class_code)
 school     | student_guardians         | student_guardians_pkey                                          | CREATE UNIQUE INDEX student_guardians_pkey ON school.student_guardians USING btree (student_id, guardian_id)
 school     | students                  | students_pkey                                                   | CREATE UNIQUE INDEX students_pkey ON school.students USING btree (id)
 school     | subjects                  | subjects_pkey                                                   | CREATE UNIQUE INDEX subjects_pkey ON school.subjects USING btree (id)
 school     | subjects                  | subjects_subject_code_key                                       | CREATE UNIQUE INDEX subjects_subject_code_key ON school.subjects USING btree (subject_code)
 school     | teachers                  | teachers_pkey                                                   | CREATE UNIQUE INDEX teachers_pkey ON school.teachers USING btree (id)
 school     | teachers                  | teachers_teacher_code_key                                       | CREATE UNIQUE INDEX teachers_teacher_code_key ON school.teachers USING btree (teacher_code)
 school     | teachers                  | uq_school_teachers_employee_id                                  | CREATE UNIQUE INDEX uq_school_teachers_employee_id ON school.teachers USING btree (employee_id) WHERE (employee_id IS NOT NULL)
 school     | teachers                  | uq_school_teachers_teacher_code                                 | CREATE UNIQUE INDEX uq_school_teachers_teacher_code ON school.teachers USING btree (teacher_code)
 school     | timetable_constraints     | timetable_constraints_pkey                                      | CREATE UNIQUE INDEX timetable_constraints_pkey ON school.timetable_constraints USING btree (id)
 school     | timetable_export_jobs     | timetable_export_jobs_pkey                                      | CREATE UNIQUE INDEX timetable_export_jobs_pkey ON school.timetable_export_jobs USING btree (id)
 school     | timetable_generation_runs | timetable_generation_runs_pkey                                  | CREATE UNIQUE INDEX timetable_generation_runs_pkey ON school.timetable_generation_runs USING btree (id)
 school     | timetable_import_batches  | timetable_import_batches_pkey                                   | CREATE UNIQUE INDEX timetable_import_batches_pkey ON school.timetable_import_batches USING btree (id)
 school     | timetable_import_errors   | timetable_import_errors_pkey                                    | CREATE UNIQUE INDEX timetable_import_errors_pkey ON school.timetable_import_errors USING btree (id)
 school     | timetable_slots           | timetable_slots_pkey                                            | CREATE UNIQUE INDEX timetable_slots_pkey ON school.timetable_slots USING btree (id)
 school     | timetable_slots           | timetable_slots_timetable_version_id_school_class_id_week_d_key | CREATE UNIQUE INDEX timetable_slots_timetable_version_id_school_class_id_week_d_key ON school.timetable_slots USING btree (timetable_version_id, school_class_id, week_day_id, period_id)
 school     | timetable_slots           | uq_school_timetable_room_conflict                               | CREATE UNIQUE INDEX uq_school_timetable_room_conflict ON school.timetable_slots USING btree (timetable_version_id, classroom_id, week_day_id, period_id) WHERE (classroom_id IS NOT NULL)
 school     | timetable_slots           | uq_school_timetable_teacher_conflict                            | CREATE UNIQUE INDEX uq_school_timetable_teacher_conflict ON school.timetable_slots USING btree (timetable_version_id, teacher_id, week_day_id, period_id) WHERE (teacher_id IS NOT NULL)
 school     | timetable_versions        | timetable_versions_pkey                                         | CREATE UNIQUE INDEX timetable_versions_pkey ON school.timetable_versions USING btree (id)
 school     | week_days                 | week_days_day_code_key                                          | CREATE UNIQUE INDEX week_days_day_code_key ON school.week_days USING btree (day_code)
 school     | week_days                 | week_days_pkey                                                  | CREATE UNIQUE INDEX week_days_pkey ON school.week_days USING btree (id)
 school     | week_days                 | week_days_sort_order_key                                        | CREATE UNIQUE INDEX week_days_sort_order_key ON school.week_days USING btree (sort_order)
(38 rows)

```

### school columns

```text
          table_name           |     column_name      |        data_type         | is_nullable 
-------------------------------+----------------------+--------------------------+-------------
 academic_years                | id                   | uuid                     | NO
 academic_years                | name                 | text                     | NO
 academic_years                | starts_on            | date                     | YES
 academic_years                | ends_on              | date                     | YES
 academic_years                | is_current           | boolean                  | NO
 academic_years                | created_at           | timestamp with time zone | NO
 classrooms                    | id                   | uuid                     | NO
 classrooms                    | institute_id         | uuid                     | YES
 classrooms                    | grade_id             | uuid                     | YES
 classrooms                    | code                 | text                     | YES
 classrooms                    | name_ar              | text                     | YES
 classrooms                    | capacity             | integer                  | NO
 classrooms                    | is_active            | boolean                  | NO
 classrooms                    | created_at           | timestamp with time zone | NO
 classrooms                    | room_code            | text                     | YES
 classrooms                    | room_name_ar         | text                     | YES
 classrooms                    | floor_name           | text                     | YES
 curriculum_plans              | id                   | uuid                     | NO
 curriculum_plans              | school_class_id      | uuid                     | NO
 curriculum_plans              | subject_id           | uuid                     | NO
 curriculum_plans              | teacher_id           | uuid                     | YES
 curriculum_plans              | classroom_id         | uuid                     | YES
 curriculum_plans              | weekly_lessons       | integer                  | NO
 curriculum_plans              | priority             | integer                  | NO
 curriculum_plans              | is_active            | boolean                  | NO
 curriculum_plans              | created_at           | timestamp with time zone | NO
 grades                        | id                   | uuid                     | NO
 grades                        | stage_code           | text                     | NO
 grades                        | grade_code           | text                     | NO
 grades                        | name_ar              | text                     | NO
 grades                        | sort_order           | integer                  | NO
 grades                        | is_active            | boolean                  | NO
 guardians                     | id                   | uuid                     | NO
 guardians                     | national_id          | text                     | YES
 guardians                     | full_name_ar         | text                     | NO
 guardians                     | phone                | text                     | YES
 guardians                     | relation_type        | text                     | YES
 guardians                     | created_at           | timestamp with time zone | NO
 institutes                    | id                   | uuid                     | NO
 institutes                    | code                 | text                     | YES
 institutes                    | name_ar              | text                     | NO
 institutes                    | institute_type       | text                     | YES
 institutes                    | education_stage      | text                     | YES
 institutes                    | zone_name            | text                     | YES
 institutes                    | administration_name  | text                     | YES
 institutes                    | is_active            | boolean                  | NO
 institutes                    | created_at           | timestamp with time zone | NO
 lesson_periods                | id                   | uuid                     | NO
 lesson_periods                | period_no            | integer                  | NO
 lesson_periods                | name_ar              | text                     | NO
 lesson_periods                | starts_at            | time without time zone   | NO
 lesson_periods                | ends_at              | time without time zone   | NO
 lesson_periods                | is_break             | boolean                  | NO
 lesson_periods                | is_active            | boolean                  | NO
 lesson_periods                | created_at           | timestamp with time zone | NO
 rooms                         | id                   | uuid                     | NO
 rooms                         | institute_id         | uuid                     | YES
 rooms                         | code                 | text                     | YES
 rooms                         | name_ar              | text                     | NO
 rooms                         | room_type            | text                     | NO
 rooms                         | capacity             | integer                  | NO
 rooms                         | is_active            | boolean                  | NO
 rooms                         | created_at           | timestamp with time zone | NO
 school_classes                | id                   | uuid                     | NO
 school_classes                | class_code           | text                     | NO
 school_classes                | class_name_ar        | text                     | NO
 school_classes                | stage_name_ar        | text                     | YES
 school_classes                | grade_name_ar        | text                     | YES
 school_classes                | capacity             | integer                  | NO
 school_classes                | is_active            | boolean                  | NO
 school_classes                | created_at           | timestamp with time zone | NO
 student_guardians             | student_id           | uuid                     | NO
 student_guardians             | guardian_id          | uuid                     | NO
 student_guardians             | relation_type        | text                     | YES
 student_guardians             | is_primary           | boolean                  | NO
 students                      | id                   | uuid                     | NO
 students                      | legacy_access_id     | text                     | YES
 students                      | national_id          | text                     | YES
 students                      | student_name_ar      | text                     | NO
 students                      | gender               | text                     | YES
 students                      | nationality          | text                     | YES
 students                      | religion             | text                     | YES
 students                      | health_status        | text                     | YES
 students                      | institute_id         | uuid                     | YES
 students                      | grade_id             | uuid                     | YES
 students                      | class_name           | text                     | YES
 students                      | enrollment_status    | text                     | NO
 students                      | created_at           | timestamp with time zone | NO
 subjects                      | id                   | uuid                     | NO
 subjects                      | subject_code         | text                     | YES
 subjects                      | subject_name_ar      | text                     | NO
 subjects                      | color_code           | text                     | YES
 subjects                      | is_active            | boolean                  | NO
 subjects                      | created_at           | timestamp with time zone | NO
 teachers                      | id                   | uuid                     | NO
 teachers                      | teacher_code         | text                     | YES
 teachers                      | teacher_name_ar      | text                     | NO
 teachers                      | phone                | text                     | YES
 teachers                      | specialization       | text                     | YES
 teachers                      | is_active            | boolean                  | NO
 teachers                      | created_at           | timestamp with time zone | NO
 teachers                      | employee_id          | uuid                     | YES
 timetable_constraints         | id                   | uuid                     | NO
 timetable_constraints         | constraint_type      | text                     | NO
 timetable_constraints         | target_scope         | text                     | NO
 timetable_constraints         | target_id            | uuid                     | YES
 timetable_constraints         | rule_code            | text                     | NO
 timetable_constraints         | rule_payload         | jsonb                    | NO
 timetable_constraints         | weight               | integer                  | NO
 timetable_constraints         | is_active            | boolean                  | NO
 timetable_constraints         | created_at           | timestamp with time zone | NO
 timetable_export_jobs         | id                   | uuid                     | NO
 timetable_export_jobs         | timetable_version_id | uuid                     | YES
 timetable_export_jobs         | export_type          | text                     | NO
 timetable_export_jobs         | report_scope         | text                     | NO
 timetable_export_jobs         | status               | text                     | NO
 timetable_export_jobs         | payload              | jsonb                    | NO
 timetable_export_jobs         | created_at           | timestamp with time zone | NO
 timetable_generation_runs     | id                   | uuid                     | NO
 timetable_generation_runs     | timetable_version_id | uuid                     | YES
 timetable_generation_runs     | status               | text                     | NO
 timetable_generation_runs     | total_cards          | integer                  | NO
 timetable_generation_runs     | scheduled_lessons    | integer                  | NO
 timetable_generation_runs     | conflict_count       | integer                  | NO
 timetable_generation_runs     | quality_score        | numeric                  | NO
 timetable_generation_runs     | summary_json         | jsonb                    | NO
 timetable_generation_runs     | started_at           | timestamp with time zone | NO
 timetable_generation_runs     | finished_at          | timestamp with time zone | YES
 timetable_import_batches      | id                   | uuid                     | NO
 timetable_import_batches      | batch_name           | text                     | NO
 timetable_import_batches      | source_program       | text                     | NO
 timetable_import_batches      | source_format        | text                     | NO
 timetable_import_batches      | total_rows           | integer                  | NO
 timetable_import_batches      | accepted_rows        | integer                  | NO
 timetable_import_batches      | rejected_rows        | integer                  | NO
 timetable_import_batches      | status               | text                     | NO
 timetable_import_batches      | created_at           | timestamp with time zone | NO
 timetable_import_errors       | id                   | uuid                     | NO
 timetable_import_errors       | batch_id             | uuid                     | YES
 timetable_import_errors       | row_number           | integer                  | NO
 timetable_import_errors       | row_data             | jsonb                    | NO
 timetable_import_errors       | error_message        | text                     | NO
 timetable_import_errors       | created_at           | timestamp with time zone | NO
 timetable_slots               | id                   | uuid                     | NO
 timetable_slots               | timetable_version_id | uuid                     | NO
 timetable_slots               | school_class_id      | uuid                     | NO
 timetable_slots               | week_day_id          | smallint                 | NO
 timetable_slots               | period_id            | uuid                     | NO
 timetable_slots               | subject_name_ar      | text                     | NO
 timetable_slots               | teacher_id           | uuid                     | YES
 timetable_slots               | classroom_id         | uuid                     | YES
 timetable_slots               | slot_type            | text                     | NO
 timetable_slots               | notes                | text                     | YES
 timetable_slots               | created_at           | timestamp with time zone | NO
 timetable_versions            | id                   | uuid                     | NO
 timetable_versions            | name_ar              | text                     | NO
 timetable_versions            | status               | text                     | NO
 timetable_versions            | effective_from       | date                     | YES
 timetable_versions            | effective_to         | date                     | YES
 timetable_versions            | is_current           | boolean                  | NO
 timetable_versions            | created_at           | timestamp with time zone | NO
 vw_school_teacher_load        | timetable_version_id | uuid                     | YES
 vw_school_teacher_load        | timetable_name_ar    | text                     | YES
 vw_school_teacher_load        | teacher_id           | uuid                     | YES
 vw_school_teacher_load        | teacher_name_ar      | text                     | YES
 vw_school_teacher_load        | weekly_lessons_count | bigint                   | YES
 vw_school_timetable_conflicts | conflict_type        | text                     | YES
 vw_school_timetable_conflicts | severity             | text                     | YES
 vw_school_timetable_conflicts | timetable_version_id | uuid                     | YES
 vw_school_timetable_conflicts | entity_id            | text                     | YES
 vw_school_timetable_conflicts | week_day_id          | smallint                 | YES
 vw_school_timetable_conflicts | period_id            | uuid                     | YES
 vw_school_timetable_conflicts | conflict_count       | bigint                   | YES
 vw_school_timetable_grid      | id                   | uuid                     | YES
 vw_school_timetable_grid      | timetable_version_id | uuid                     | YES
 vw_school_timetable_grid      | timetable_name_ar    | text                     | YES
 vw_school_timetable_grid      | class_code           | text                     | YES
 vw_school_timetable_grid      | class_name_ar        | text                     | YES
 vw_school_timetable_grid      | week_day_id          | smallint                 | YES
 vw_school_timetable_grid      | day_name_ar          | text                     | YES
 vw_school_timetable_grid      | day_order            | integer                  | YES
 vw_school_timetable_grid      | period_no            | integer                  | YES
 vw_school_timetable_grid      | period_name_ar       | text                     | YES
 vw_school_timetable_grid      | starts_at            | time without time zone   | YES
 vw_school_timetable_grid      | ends_at              | time without time zone   | YES
 vw_school_timetable_grid      | subject_name_ar      | text                     | YES
 vw_school_timetable_grid      | teacher_name_ar      | text                     | YES
 vw_school_timetable_grid      | room_name_ar         | text                     | YES
 vw_school_timetable_grid      | slot_type            | text                     | YES
 vw_school_timetable_grid      | notes                | text                     | YES
 vw_school_timetable_quality   | timetable_version_id | uuid                     | YES
 vw_school_timetable_quality   | timetable_name_ar    | text                     | YES
 vw_school_timetable_quality   | scheduled_lessons    | bigint                   | YES
 vw_school_timetable_quality   | required_lessons     | integer                  | YES
 vw_school_timetable_quality   | hard_conflicts       | bigint                   | YES
 vw_school_timetable_quality   | quality_score        | numeric                  | YES
 vw_school_timetable_quality   | reasons_json         | jsonb                    | YES
 week_days                     | id                   | smallint                 | NO
 week_days                     | day_code             | text                     | NO
 week_days                     | name_ar              | text                     | NO
 week_days                     | sort_order           | integer                  | NO
(201 rows)

```

## 11) فحص الربط بين الجدول وباقي البرنامج

### نتيجة فحص مبدئية

| منطقة الربط | الحالة الحالية المحتملة | المطلوب للوصول لربط إنتاجي |
|---|---|---|
| الجدول ↔ المدارس | يوجد classes/classrooms لكن غالبًا بدون institute_id إجباري | ربط كل فصل وقاعة ومعمل بمدرسة/معهد محدد |
| الجدول ↔ الموظفين | يوجد teachers داخل school لكن منفصل عن HR | ربط teacher_id بجدول الموظفين/العاملين بدل إنشاء مدرس مستقل فقط |
| الجدول ↔ الكنترول | يوجد education-control مستقل | ربط الصفوف والفصول والمواد بنتائج الكنترول والطلاب |
| الجدول ↔ المواد | subject_name_ar نص حر داخل slots | إنشاء جدول subjects رسمي وربطه بالحصص وبالكنترول |
| الجدول ↔ القاعات | classrooms موجودة | مطلوب نوع القاعة: فصل/معمل/ملعب/نشاط + السعة + صلاحية المادة |
| الجدول ↔ الاستيراد | CSV import موجود | مطلوب Import Wizard: Browse + Preview + Mapping + Validation قبل الحفظ |
| منع التعارض | موجود جزئيًا في API slots | مطلوب تعارض مدرس/فصل/قاعة/مجموعة/نصاب/أيام إجازات |
| التقسيم والمجموعات | غير مكتمل | مطلوب groups/sections/split lessons/lab groups |
| الواجهة | متذبذبة بسبب لصق ملفات طويلة | مطلوب UI ثابت مقسم Components وليس صفحة ضخمة واحدة |


## 12) النواقص النهائية في موديول الجدول المدرسي


### ناقص أساسي
- إدارة مدرسة/معهد متعددة وربط كل جدول بمدرسة محددة.
- جدول مواد رسمي بدل كتابة اسم المادة كنص داخل الحصة.
- ربط المدرسين ببرنامج الموظفين HR.
- ربط الفصول بطلاب الكنترول والمرحلة والصف.
- إنشاء نسخة جدول لكل مدرسة ولكل عام دراسي وفصل دراسي.
- شاشة بناء جدول يدوي كاملة.
- شاشة استيراد احترافية من TimeTable مع Browse + Preview + Mapping.
- دعم XLSX وليس CSV فقط.
- منع تعارض شامل: مدرس، فصل، قاعة، مجموعة، مادة، نصاب، أيام غياب.
- دعم الحصص المزدوجة والحصة نصفية/1.5.
- دعم تقسيم الفصل لمجموعات: حاسب، علوم، لغات، أنشطة.
- دعم القاعات المتخصصة ومعامل المواد.
- دعم قيود المدرسين: أيام ممنوعة، حصص مفضلة، حد أقصى يومي/أسبوعي.
- دعم طباعة جدول الفصل وجدول المدرس وجدول القاعة.
- Dashboard إحصائي: كثافة الحصص، التعارضات، نصاب المدرسين، الفجوات.
- Audit log لكل تعديل في الجدول.
- صلاحيات: مدير مدرسة، مسؤول جدول، مراجع، مشاهدة فقط.
- Import errors UI بدل الاعتماد على JSON فقط.

### ناقص معماري
- فصل موديول timetable إلى ملفات: API + Service + Repository + Schemas بدل ملف واحد ضخم.
- إضافة migrations رسمية مرتبة بدل تعديلات مباشرة في DB.
- إضافة tests لمنع التعارضات.
- إضافة seed data رسمية للأيام والحصص.
- إضافة route protection وصلاحيات.
- إضافة validation صارم للمدخلات.
- إضافة frontend components مستقلة بدل page.tsx كبير.


## 13) خطة استكمال مقترحة


### Phase A - تثبيت الأساس
1. تثبيت DB migrations لموديول timetable.
2. ربط teachers ببرنامج الموظفين.
3. ربط classes بالمدارس/المعاهد.
4. إنشاء subjects.
5. فصل كود API إلى services.

### Phase B - تشغيل UI حقيقي
1. صفحة Teachers.
2. صفحة Classes.
3. صفحة Rooms.
4. صفحة Periods.
5. صفحة Manual Timetable Builder.
6. صفحة Import Wizard.

### Phase C - ذكاء الجدولة
1. Rules Engine.
2. Conflict Detector.
3. Auto-scheduler.
4. Reports/Print.


## 14) مراقبة تحديثات المشروع

تم إنشاء سكربت مراقبة في: `scripts/watch_mk_updates.sh`

