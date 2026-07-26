"""
Rendering Service
Handles the core logic for showing and accepting pages in the APEX-like application.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from sqlalchemy.orm import Session
from fastapi import HTTPException, Request

from ...db import models
from ... import schemas
from ..session.service import SessionService
from ..region_types import (
    render_static_content_region,
    render_report_region,
    form_region
)
from ..item_types import (
    render_text_item,
    render_textarea_item,
    render_select_item,
    render_checkbox_item,
    render_radio_item,
    render_date_picker_item,
    render_display_only_item,
    render_hidden_item
)


class RenderingService:
    """Service for rendering pages and processing page submissions."""

    def __init__(self, db: Session):
        self.db = db
        self.session_service = SessionService(db)

    def show_page(
        self,
        application_alias: str,
        page_number: int,
        session_id: Optional[str] = None,
        request: Optional[Request] = None
    ) -> dict:
        """
        Render a page based on its metadata.

        Args:
            application_alias: The alias of the application
            page_number: The page number to render
            session_id: Optional session ID (if not provided, a new session will be created)
            request: Optional FastAPI request object (for getting client info, etc.)

        Returns:
            Dictionary containing the rendered HTML and session information
        """
        # Get the application by alias
        application = self.db.query(models.Application).filter(
            models.Application.alias == application_alias,
            models.Application.is_active == True
        ).first()

        if not application:
            raise HTTPException(
                status_code=404,
                detail=f"Application with alias '{application_alias}' not found"
            )

        # Get page by application ID and page number
        page = self.db.query(models.Page).filter(
            models.Page.application_id == application.id,
            models.Page.page_number == page_number,
            models.Page.is_active == True
        ).first()

        if not page:
            raise HTTPException(
                status_code=404,
                detail=f"Page {page_number} not found in application '{application_alias}'"
            )

        # Get or create session
        if not session_id:
            session_id = self.session_service.create_session(application.id)
        elif not self.session_service.validate_session(session_id):
            session_id = self.session_service.create_session(application.id)

        session = self.session_service.get_session(session_id)

        # Get all regions for this page, ordered by position
        regions = self.db.query(models.Region).filter(
            models.Region.page_id == page.id,
            models.Region.is_active == True
        ).order_by(models.Region.position).all()

        # Get all items for this page
        page_items = self.db.query(models.PageItem).filter(
            models.PageItem.page_id == page.id,
            models.PageItem.is_active == True
        ).all()

        # Get all processes for this page (for potential processing on show)
        page_processes = self.db.query(models.PageProcess).filter(
            models.PageProcess.page_id == page.id,
            models.PageProcess.is_active == True,
            models.PageProcess.execution_point == "ON_LOAD"  # Processes that run on page load
        ).order_by(models.PageProcess.execution_sequence).all()

        # Execute ON_LOAD processes
        self._execute_processes(page_processes, session_id, page.id)

        # Initialize session state for items on this page if not already set
        self._initialize_page_items(session_id, page.id, page_items)

        # Render each region
        rendered_regions = []
        for region in regions:
            region_html = self._render_region(region, session_id, page.id)
            rendered_regions.append({
                "region_id": region.id,
                "region_name": region.name,
                "region_type": region.region_type,
                "position": region.position,
                "html": region_html
            })

        # Get all item values for the page
        item_values = self.session_service.get_items_for_page(session_id, page.id)

        # Generate the complete HTML page
        html_content = self._generate_page_html(
            application=application,
            page=page,
            regions=rendered_regions,
            item_values=item_values,
            session_id=session_id
        )

        return {
            "application_id": application.id,
            "application_name": application.name,
            "application_alias": application.alias,
            "page_id": page.id,
            "page_name": page.name,
            "page_number": page.page_number,
            "session_id": session_id,
            "html": html_content,
            "regions": rendered_regions,
            "item_values": item_values
        }

    def accept_page(
        self,
        application_alias: str,
        page_number: int,
        session_id: str,
        form_data: dict
    ) -> dict:
        """
        Process a page submission (form post).

        Args:
            application_alias: The alias of the application
            page_number: The page number being submitted
            session_id: The session ID
            form_data: Dictionary of form field names and values

        Returns:
            Dictionary indicating success/failure and any redirect instructions
        """
        # Get application by alias
        application = self.db.query(models.Application).filter(
            models.Application.alias == application_alias,
            models.Application.is_active == True
        ).first()

        if not application:
            raise HTTPException(
                status_code=404,
                detail=f"Application with alias '{application_alias}' not found"
            )

        # Get page by application ID and page number
        page = self.db.query(models.Page).filter(
            models.Page.application_id == application.id,
            models.Page.page_number == page_number,
            models.Page.is_active == True
        ).first()

        if not page:
            raise HTTPException(
                status_code=404,
                detail=f"Page {page_number} not found in application '{application_alias}'"
            )

        # Validate session
        if not self.session_service.validate_session(session_id):
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired session"
            )

        # Get all items for this page
        page_items = self.db.query(models.PageItem).filter(
            models.PageItem.page_id == page.id,
            models.PageItem.is_active == True
        ).all()

        # Get all validations for this page
        page_validations = self.db.query(models.Validation).filter(
            models.Validation.page_id == page.id,
            models.Validation.is_active == True
        ).order_by(models.Validation.sequence).all()

        # Get all processes for this page (for processing on submit)
        page_processes = self.db.query(models.PageProcess).filter(
            models.PageProcess.page_id == page.id,
            models.PageProcess.is_active == True,
            models.PageProcess.execution_point.in_([
                "ON_SUBMIT_BEFORE_VALIDATION",
                "ON_SUBMIT_AFTER_VALIDATION",
                "ON_SUBMIT_BEFORE_PROCESSING"
            ])
        ).order_by(models.PageProcess.execution_sequence).all()

        # Step 1: Store submitted values in session
        for item in page_items:
            # Get the submitted value (handle checkboxes specially)
            if item.item_type == "checkbox":
                # For checkboxes, if it's in the form data, it's checked
                value = "Y" if item.name in form_data else "N"
            else:
                value = form_data.get(item.name, item.default_value or "")

            self.session_service.set_item(session_id, page.id, item.name, value)

        # Step 2: Execute BEFORE_VALIDATION processes
        before_validation_processes = [p for p in page_processes
                                     if p.execution_point == "ON_SUBMIT_BEFORE_VALIDATION"]
        self._execute_processes(before_validation_processes, session_id, page.id)

        # Step 3: Run validations
        validation_errors = self._run_validations(page_validations, session_id, page.id)

        if validation_errors:
            # If there are validation errors, don't proceed with processing
            return {
                "success": False,
                "validation_errors": validation_errors,
                "session_id": session_id,
                "message": "Validation failed"
            }

        # Step 4: Execute AFTER_VALIDATION processes
        after_validation_processes = [p for p in page_processes
                                    if p.execution_point == "ON_SUBMIT_AFTER_VALIDATION"]
        self._execute_processes(after_validation_processes, session_id, page.id)

        # Step 5: Execute the main processes (INSERT/UPDATE/DELETE, etc.)
        main_processes = [p for p in page_processes
                         if p.execution_point == "ON_SUBMIT_BEFORE_PROCESSING"]
        self._execute_processes(main_processes, session_id, page.id)

        # Step 6: Determine where to go next (branching)
        # For now, we'll just return success - branching logic would be implemented here

        return {
            "success": True,
            "session_id": session_id,
            "message": "Page processed successfully",
            "redirect_url": f"/{application.alias}/{page.page_number}"  # Simple redirect back to same page
        }

    def _initialize_page_items(self, session_id: str, page_id: int, page_items: list):
        """Initialize session state for page items with their default values if not already set."""
        for item in page_items:
            # Check if item already has a value in session
            existing_value = self.session_service.get_item(session_id, page_id, item.name)
            if existing_value is None and item.default_value is not None:
                # Set the default value
                self.session_service.set_item(session_id, page_id, item.name, item.default_value)

    def _render_region(self, region: models.Region, session_id: str, page_id: int) -> str:
        """Render a single region based on its type."""
        region_type = region.region_type.lower()

        if region_type == "static_content":
            return render_static_content_region(region, self.db)
        elif region_type == "report":
            return render_report_region(region, self.db, session_id, page_id)
        elif region_type == "form":
            return form_region(region, self.db, session_id, page_id)
        else:
            # For unsupported region types, return a placeholder
            return f"<div class='region region-{region.id}'><h3>{region.name}</h3><p>Region type '{region.region_type}' not yet implemented.</p></div>"

    def _execute_processes(
        self,
        processes: list,
        session_id: str,
        page_id: int
    ):
        """Execute a list of page processes."""
        for process in processes:
            self._execute_single_process(process, session_id, page_id)

    def _execute_single_process(
        self,
        process: models.PageProcess,
        session_id: str,
        page_id: int
    ):
        """Execute a single page process."""
        # For MVP, we'll implement basic SQL execution
        # In a full implementation, this would handle PL/SQL equivalent, etc.
        if process.process_type.lower() == "sql":
            self._execute_sql_process(process, session_id, page_id)
        elif process.process_type.lower() == "plsql":
            # Placeholder for PL/SQL execution
            pass
        elif process.process_type.lower() == "reset_pagination":
            # Reset pagination for report regions
            pass
        # Add more process types as needed

    def _execute_sql_process(
        self,
        process: models.PageProcess,
        session_id: str,
        page_id: int
    ):
        """Execute a SQL process."""
        if not process.process_code:
            return

        # Replace substitution strings in the SQL
        sql = self._substitute_strings(process.process_code, session_id, page_id)

        try:
            # Execute the SQL
            result = self.db.execute(sql)
            # For SELECT statements, we might want to store results in session state
            # For INSERT/UPDATE/DELETE, we commit the transaction
            if sql.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                self.db.commit()
        except Exception as e:
            # In a real implementation, you'd log this error
            # For now, we'll just raise it
            raise Exception(f"Error executing SQL process '{process.name}': {str(e)}")

    def _substitute_strings(self, text: str, session_id: str, page_id: int) -> str:
        """Substitute substitution strings in text with their session values."""
        # Common substitution strings in APEX:
        # &APP_USER., &APP_SESSION., &ITEM_NAME., etc.

        # Replace &APP_SESSION. with the actual session ID
        text = text.replace("&APP_SESSION.", session_id)

        # Get the session to get user info
        session = self.session_service.get_session(session_id)
        if session:
            # Replace &APP_USER. with the username if available
            if session.user_id:
                user = self.db.query(models.WorkspaceUser).filter(
                    models.WorkspaceUser.id == session.user_id
                ).first()
                if user:
                    text = text.replace("&APP_USER.", user.username)
            else:
                # If not authenticated, use a default
                text = text.replace("&APP_USER.", "GUEST")

        # Replace item references like &ITEM_NAME.
        # This is a simple implementation - a real one would use regex
        # to find all &WORD. patterns and replace them

        # For now, we'll do a simple replacement for known items
        # In a full implementation, you'd parse the string and replace all &ITEM. patterns
        items = self.session_service.get_items_for_page(session_id, page_id)
        for item_name, item_value in items.items():
            placeholder = f"&{item_name}."
            text = text.replace(placeholder, item_value or "")

        return text

    def _run_validations(
        self,
        validations: list,
        session_id: str,
        page_id: int
    ) -> list:
        """Run all validations for a page and return any errors."""
        errors = []

        for validation in validations:
            error = self._run_single_validation(validation, session_id, page_id)
            if error:
                errors.append(error)

        return errors

    def _run_single_validation(
        self,
        validation: models.Validation,
        session_id: str,
        page_id: int
    ) -> Optional[dict]:
        """Run a single validation and return error details if it fails."""
        # Get the item value
        item_value = self.session_service.get_item(session_id, page_id, validation.item_name)

        # If the item is not required and has no value, skip validation
        if not item_value and validation.validation_type != "NOT_NULL":
            return None

        # Replace substitution strings in the validation expression
        validation_expression = self._substitute_strings(
            validation.validation_expression, session_id, page_id
        )

        # For now, we'll implement a few basic validation types
        # A full implementation would have more sophisticated validation handling

        if validation.validation_type == "NOT_NULL":
            if not item_value or item_value.strip() == "":
                return {
                    "item_name": validation.item_name,
                    "message": validation.error_message or f"Field {validation.item_name} is required."
                }

        # Add more validation types as needed (VALUE_REQUIRED, COMPARISON, REGEX, etc.)

        return None  # Validation passed

    def _generate_page_html(
        self,
        application: models.Application,
        page: models.Page,
        regions: list,
        item_values: dict,
        session_id: str
    ) -> str:
        """Generate the complete HTML page."""
        # Get the page's CSS classes or theme information
        # For now, we'll use a simple template

        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            f"    <title>{application.name} - {page.name}</title>",
            "    <meta charset='utf-8'>",
            "    <meta name='viewport' content='width=device-width, initial-scale=1'>",
            "    <link rel='stylesheet' href='/static/css/apexos.css'>",
            "</head>",
            "<body>",
            f"    <div class='page' data-application-id='{application.id}' data-page-id='{page.id}'>",
            f"        <header class='page-header'>",
            f"            <h1>{application.name}</h1>",
            f"            <h2>{page.name}</h2>",
            "        </header>",
            f"        <div class='page-body'>"
        ]

        # Add each region
        for region in regions:
            html_parts.append(f"""
            <div class='region region-{region['region_id']}' data-region-type='{region['region_type']}'>
                <div class='region-header'>
                    <h3>{region['region_name']}</h3>
                </div>
                <div class='region-body'>
                    {region['html']}
                </div>
            </div>
            """)

        html_parts.extend([
            "        </div>",
            f"        <footer class='page-footer'>",
            f"            <p>Session: {session_id[:8]}...</p>",
            "        </footer>",
            "    </div>",
            "    <script src='/static/js/apexos.js'></script>",
            "</body>",
            "</html>"
        ])

        return "\n".join(html_parts)