"""Local family school dashboard. Binds to 127.0.0.1 when run as a server."""

from __future__ import annotations

import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.db import (
    add_child,
    child_label,
    connect,
    delete_row,
    get_row,
    init_db,
    latest_grade_ids,
    list_children,
    list_rows,
    load_sample,
    recent_communications,
    rename_child,
    save_assignment,
    save_communication,
    save_event,
    save_grade,
    upcoming_items,
)

ROOT = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(ROOT / "templates"))
KIND_LABELS = {
    "field_trip": "Field trip",
    "milestone": "Milestone",
    "other": "Other date",
    "assignment": "Assignment",
}
STATUS_LABELS = {"not_started": "Not started", "done": "Done"}


def create_app(database_path: str | None = None) -> FastAPI:
    path = database_path or os.environ.get("DATABASE_PATH", "data/school.db")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        conn = connect(path)
        init_db(conn)
        conn.close()
        yield

    app = FastAPI(title="Family school dashboard", lifespan=lifespan)
    app.state.db_path = path
    app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")

    def db_conn():
        conn = connect(app.state.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def filter_state(conn: sqlite3.Connection, child: str) -> dict:
        children = list_children(conn)
        known = {row["id"] for row in children}
        if not child or child == "all":
            mode, child_id, notice = "all", None, None
        elif child.isdigit() and int(child) in known:
            mode, child_id, notice = "one", int(child), None
        else:
            mode, child_id, notice = "missing", None, "That child was not found."
        return {
            "children": children,
            "mode": mode,
            "child_id": child_id,
            "filter_value": child or "all",
            "notice": notice,
        }

    def page(request: Request, name: str, state: dict, status_code: int = 200, **extra):
        context = {
            "request": request,
            "kind_labels": KIND_LABELS,
            "status_labels": STATUS_LABELS,
            "child_label": child_label,
            **state,
            **extra,
        }
        return TEMPLATES.TemplateResponse(request, name, context, status_code=status_code)

    def go(path: str, child: str) -> RedirectResponse:
        suffix = "" if child in ("", "all") else f"?child={child}"
        return RedirectResponse(f"{path}{suffix}", status_code=303)

    @app.get("/")
    def home(request: Request, child: str = Query("all"), conn: sqlite3.Connection = Depends(db_conn)):
        state = filter_state(conn, child)
        return page(
            request,
            "home.html",
            state,
            upcoming=upcoming_items(conn, state["mode"], state["child_id"]),
            communications=recent_communications(conn, state["mode"], state["child_id"]),
        )

    @app.get("/children")
    def children_page(request: Request, child: str = Query("all"), conn: sqlite3.Connection = Depends(db_conn)):
        return page(request, "children.html", filter_state(conn, child), error=None)

    @app.post("/children")
    def create_child(
        request: Request,
        name: str = Form(""),
        child: str = Query("all"),
        conn: sqlite3.Connection = Depends(db_conn),
    ):
        error = add_child(conn, name)
        state = filter_state(conn, child)
        if error:
            return page(request, "children.html", state, status_code=400, error=error)
        return page(request, "children.html", state, error=None)

    @app.post("/children/{child_id}")
    def update_child(
        request: Request,
        child_id: int,
        name: str = Form(""),
        child: str = Query("all"),
        conn: sqlite3.Connection = Depends(db_conn),
    ):
        error = rename_child(conn, child_id, name)
        state = filter_state(conn, child)
        status = 400 if error else 200
        return page(request, "children.html", state, status_code=status, error=error)

    @app.post("/sample-data")
    def sample_data(request: Request, child: str = Query("all"), conn: sqlite3.Connection = Depends(db_conn)):
        error = load_sample(conn)
        state = filter_state(conn, child)
        status = 400 if error else 200
        return page(request, "children.html", state, status_code=status, error=error)

    async def _save(request, conn, child, saver, kind, row_id):
        form = dict(await request.form())
        error = saver(conn, form, row_id)
        if error:
            state = filter_state(conn, child)
            if row_id is not None:
                form["id"] = row_id
            return page(
                request,
                f"{kind}.html",
                state,
                status_code=400,
                rows=[],
                form=form,
                error=error,
                editing=row_id is not None,
            )
        return go(f"/{kind}", child)

    def register_collection(kind: str, shared: bool, saver, date_field: str):
        table = kind

        def collection(request: Request, child: str = Query("all"), conn: sqlite3.Connection = Depends(db_conn)):
            state = filter_state(conn, child)
            rows = list_rows(conn, table, date_field, state["mode"], state["child_id"], shared=shared)
            extra = {}
            if kind == "grades":
                extra["current_ids"] = latest_grade_ids(rows)
            return page(request, f"{kind}.html", state, rows=rows, form=None, error=None, editing=False, **extra)

        def new_form(request: Request, child: str = Query("all"), conn: sqlite3.Connection = Depends(db_conn)):
            state = filter_state(conn, child)
            return page(request, f"{kind}.html", state, rows=[], form={}, error=None, editing=False)

        async def create_row(request: Request, child: str = Query("all"), conn: sqlite3.Connection = Depends(db_conn)):
            return await _save(request, conn, child, saver, kind, None)

        def edit_form(request: Request, row_id: int, child: str = Query("all"), conn: sqlite3.Connection = Depends(db_conn)):
            row = get_row(conn, table, row_id)
            if row is None:
                raise HTTPException(status_code=404)
            state = filter_state(conn, child)
            return page(request, f"{kind}.html", state, rows=[], form=dict(row), error=None, editing=True)

        async def update_row(
            request: Request,
            row_id: int,
            child: str = Query("all"),
            conn: sqlite3.Connection = Depends(db_conn),
        ):
            return await _save(request, conn, child, saver, kind, row_id)

        def confirm(request: Request, row_id: int, child: str = Query("all"), conn: sqlite3.Connection = Depends(db_conn)):
            row = get_row(conn, table, row_id)
            if row is None:
                raise HTTPException(status_code=404)
            state = filter_state(conn, child)
            title = row["title"] if "title" in row.keys() else row["subject"]
            return page(
                request,
                "confirm_delete.html",
                state,
                item_title=title,
                action=f"/{kind}/{row_id}/delete",
                cancel=f"/{kind}",
            )

        def remove(row_id: int, child: str = Query("all"), conn: sqlite3.Connection = Depends(db_conn)):
            delete_row(conn, table, row_id)
            return go(f"/{kind}", child)

        routes = [
            ("get", f"/{kind}", collection, f"list_{kind}"),
            ("get", f"/{kind}/new", new_form, f"new_{kind}"),
            ("post", f"/{kind}", create_row, f"create_{kind}"),
            ("get", f"/{kind}/{{row_id}}/edit", edit_form, f"edit_{kind}"),
            ("post", f"/{kind}/{{row_id}}", update_row, f"update_{kind}"),
            ("get", f"/{kind}/{{row_id}}/delete", confirm, f"confirm_{kind}"),
            ("post", f"/{kind}/{{row_id}}/delete", remove, f"delete_{kind}"),
        ]
        for method, route, endpoint, operation_id in routes:
            endpoint.__name__ = operation_id
            getattr(app, method)(route, operation_id=operation_id)(endpoint)

    register_collection("communications", True, save_communication, "occurred_on")
    register_collection("events", True, save_event, "event_on")
    register_collection("assignments", False, save_assignment, "due_on")
    register_collection("grades", False, save_grade, "recorded_on")

    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "8000")),
        reload=False,
    )


if __name__ == "__main__":
    main()
