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
    add_rule,
    child_count,
    child_label,
    connect,
    delete_row,
    delete_rule,
    get_row,
    gmail_communication_ids,
    gmail_id_for,
    init_db,
    latest_grade_ids,
    list_children,
    list_rows,
    list_rules,
    load_sample,
    recent_communications,
    rename_child,
    save_assignment,
    save_communication,
    save_event,
    save_grade,
    upcoming_items,
)
from app.gmail import (
    GmailClient,
    authorize_url,
    connected_address,
    delete_token,
    exchange_code,
    fetch_address,
    new_oauth_state,
    write_token,
)
from app.mail import run_check

ROOT = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(ROOT / "templates"))
KIND_LABELS = {
    "field_trip": "Field trip",
    "milestone": "Milestone",
    "other": "Other date",
    "assignment": "Assignment",
}
STATUS_LABELS = {"not_started": "Not started", "done": "Done"}


def create_app(
    database_path: str | None = None,
    mailbox=None,
    token_path: str | None = None,
) -> FastAPI:
    path = database_path or os.environ.get("DATABASE_PATH", "data/school.db")
    token_file = token_path or "data/gmail_token.json"

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        conn = connect(path)
        init_db(conn)
        conn.close()
        yield

    app = FastAPI(title="Family school dashboard", lifespan=lifespan)
    app.state.db_path = path
    app.state.mailbox = mailbox
    app.state.token_path = token_file
    app.state.oauth_states = {}
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
            if kind == "communications":
                extra["gmail_open_ids"] = gmail_communication_ids(conn)
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

    def gmail_page(request: Request, conn: sqlite3.Connection, child: str, error: str | None = None, status_code: int = 200, **extra):
        address = connected_address(app.state.token_path)
        return page(
            request,
            "gmail.html",
            filter_state(conn, child),
            status_code=status_code,
            error=error,
            connected=address is not None,
            address=address or "",
            rules=list_rules(conn),
            rule_kind=extra.get("rule_kind", "sender"),
            rule_value=extra.get("rule_value", ""),
        )

    def mailbox_for():
        if app.state.mailbox is not None:
            return app.state.mailbox
        return GmailClient(app.state.token_path)

    def redirect_uri() -> str:
        port = os.environ.get("PORT", "8000")
        return f"http://127.0.0.1:{port}/gmail/callback"

    @app.get("/gmail")
    def gmail_home(request: Request, child: str = Query("all"), conn: sqlite3.Connection = Depends(db_conn)):
        return gmail_page(request, conn, child)

    @app.get("/gmail/connect")
    def gmail_connect(request: Request, child: str = Query("all"), conn: sqlite3.Connection = Depends(db_conn)):
        client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
        if not client_id or not client_secret:
            return gmail_page(
                request,
                conn,
                child,
                error="Google client id and secret are required.",
                status_code=400,
            )
        state, verifier = new_oauth_state()
        callback = redirect_uri()
        app.state.oauth_states[state] = {"verifier": verifier, "redirect_uri": callback}
        return RedirectResponse(
            authorize_url(client_id=client_id, redirect_uri=callback, state=state, verifier=verifier),
            status_code=302,
        )

    @app.get("/gmail/callback")
    def gmail_callback(
        request: Request,
        child: str = Query("all"),
        code: str = Query(""),
        state: str = Query(""),
        error: str = Query(""),
        conn: sqlite3.Connection = Depends(db_conn),
    ):
        pending = app.state.oauth_states.pop(state, None)
        if error or not code or pending is None:
            reason = error or "Gmail could not be connected."
            return gmail_page(request, conn, child, error=reason, status_code=400)
        try:
            refresh, access = exchange_code(
                client_id=os.environ.get("GOOGLE_CLIENT_ID", ""),
                client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", ""),
                code=code,
                verifier=pending["verifier"],
                redirect_uri=pending["redirect_uri"],
            )
            email = fetch_address(access)
            write_token(app.state.token_path, refresh, email)
        except Exception as exc:
            return gmail_page(request, conn, child, error=f"Gmail could not be connected: {exc}", status_code=400)
        return RedirectResponse("/gmail", status_code=303)

    @app.post("/gmail/disconnect")
    def gmail_disconnect(child: str = Query("all")):
        delete_token(app.state.token_path)
        suffix = "" if child in ("", "all") else f"?child={child}"
        return RedirectResponse(f"/gmail{suffix}", status_code=303)

    @app.post("/gmail/rules")
    def create_rule(
        request: Request,
        kind: str = Form("sender"),
        value: str = Form(""),
        child: str = Query("all"),
        conn: sqlite3.Connection = Depends(db_conn),
    ):
        error = add_rule(conn, kind, value)
        if error:
            return gmail_page(request, conn, child, error=error, status_code=400, rule_kind=kind, rule_value=value)
        return go("/gmail", child)

    @app.post("/gmail/rules/{rule_id}/delete")
    def remove_rule(rule_id: int, child: str = Query("all"), conn: sqlite3.Connection = Depends(db_conn)):
        delete_rule(conn, rule_id)
        return go("/gmail", child)

    @app.post("/gmail/check")
    def gmail_check(request: Request, child: str = Query("all"), conn: sqlite3.Connection = Depends(db_conn)):
        if child_count(conn) == 0:
            return gmail_page(request, conn, child, error="Add a child first.", status_code=400)
        address = connected_address(app.state.token_path)
        if not address:
            return gmail_page(request, conn, child, error="Gmail is not connected.", status_code=400)
        if not list_rules(conn):
            return gmail_page(request, conn, child, error="Name a sender, domain, or label.", status_code=400)
        try:
            run_check(conn, mailbox_for(), address=address)
        except Exception as exc:
            reason = str(exc).strip() or "Gmail could not be read."
            if not reason.lower().startswith("gmail"):
                reason = f"Gmail could not be read: {reason}"
            return gmail_page(request, conn, child, error=reason, status_code=400)
        return go("/gmail", child)

    @app.get("/communications/{row_id}/original")
    def open_original(
        request: Request,
        row_id: int,
        child: str = Query("all"),
        conn: sqlite3.Connection = Depends(db_conn),
    ):
        row = get_row(conn, "communications", row_id)
        if row is None:
            raise HTTPException(status_code=404)
        state = filter_state(conn, child)
        gmail_id = gmail_id_for(conn, row_id)
        found = None
        if gmail_id and connected_address(app.state.token_path):
            try:
                found = mailbox_for().get_message(gmail_id)
            except Exception:
                found = None
        if found:
            return RedirectResponse(f"https://mail.google.com/mail/u/0/#all/{gmail_id}", status_code=302)
        rows = list_rows(conn, "communications", "occurred_on", state["mode"], state["child_id"], shared=True)
        return page(
            request,
            "communications.html",
            state,
            rows=rows,
            form=None,
            error="The original could not be opened.",
            editing=False,
            gmail_open_ids=gmail_communication_ids(conn),
        )

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
