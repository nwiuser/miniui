"""
Test script for Phase 2: Core Rendering Engine
This script tests the functionality implemented for Phase 2.
"""
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Override database URL to use SQLite for testing
os.environ["DATABASE_URL"] = "sqlite:///./test_phase2.db"

# Delete the test database file if it exists to start fresh
if os.path.exists("./test_phase2.db"):
    os.remove("./test_phase2.db")

from app.db import models
from app.db.session import SessionLocal, engine
from app.core.rendering.service import RenderingService
from app.core.session.service import SessionService


def test_phase2():
    """Test the Phase 2 implementation."""
    print("[TEST] Testing Phase 2: Core Rendering Engine")
    print("=" * 50)

    # Create tables
    models.Base.metadata.create_all(bind=engine)

    # Create a session
    db = SessionLocal()

    try:
        # First, let's create some test data
        print("[DATA] Creating test data...")

        # Create an application
        app = models.Application(
            name="Test Application",
            alias="TESTAPP",
            description="A test application for Phase 2"
        )
        db.add(app)
        db.commit()
        db.refresh(app)
        print(f"[SUCCESS] Created application: {app.name} (ID: {app.id})")

        # Create a page
        page = models.Page(
            application_id=app.id,
            name="Home Page",
            alias="HOME",
            page_number=1,
            description="The home page"
        )
        db.add(page)
        db.commit()
        db.refresh(page)
        print(f"[SUCCESS] Created page: {page.name} (ID: {page.id})")

        # Create a static content region
        region1 = models.Region(
            page_id=page.id,
            name="Welcome Message",
            region_type="static_content",
            template_options={"content": "<h1>Welcome to our APEX-like application!</h1><p>This is a static content region.</p>"},
            position=1
        )
        db.add(region1)

        # Create a report region (simple SQL query)
        region2 = models.Region(
            page_id=page.id,
            name="User Report",
            region_type="report",
            template_options={"source": "SELECT 'John' as first_name, 'Doe' as last_name UNION ALL SELECT 'Jane', 'Smith'"},
            position=2
        )
        db.add(region2)

        # Create a form region
        region3 = models.Region(
            page_id=page.id,
            name="User Information",
            region_type="form",
            position=3
        )
        db.add(region3)

        # Create some page items for the form
        item1 = models.PageItem(
            page_id=page.id,
            name="P1_NAME",
            alias="P_NAME",
            item_type="text",
            label="Name",
            placeholder="Enter your name"
        )
        db.add(item1)

        item2 = models.PageItem(
            page_id=page.id,
            name="P1_CHOICE",
            alias="P_CHOICE",
            item_type="select",
            label="Choice",
            placeholder="Select an option"
        )
        db.add(item2)

        # Create an LOV for the select item
        lov = models.Lov(
            lov_name="YES_NO",
            lov_definition="STATIC2:Yes;Y,No;N",
            is_static=True,
            static_values="STATIC2:Yes;Y,No;N"
        )
        db.add(lov)
        db.commit()
        db.refresh(lov)

        # Link the LOV to the select item
        item2.lov_id = lov.id
        db.commit()

        db.refresh(region1)
        db.refresh(region2)
        db.refresh(region3)
        db.refresh(item1)
        db.refresh(item2)
        print("[SUCCESS] Created regions, items, and LOV")

        # Now test the rendering service
        print("\n[RENDER] Testing rendering service...")
        rendering_service = RenderingService(db)

        # Render the page
        result = rendering_service.show_page(
            application_alias="TESTAPP",
            page_number=1
        )

        print(f"[PAGE] Rendered page: {result['page_name']}")
        print(f"[SESSION] Session ID: {result['session_id'][:8]}...")
        print(f"[REGIONS] Number of regions: {len(result['regions'])}")
        print(f"[SIZE] HTML length: {len(result['html'])} characters")

        # Check that the HTML contains expected content
        assert "Welcome to our APEX-like application!" in result['html']
        assert "P1_NAME" in result['html']
        assert "P1_CHOICE" in result['html']
        print("[SUCCESS] HTML content validation passed")

        # Get the session ID for further tests
        session_id = result['session_id']

        print("\n[INPUT] Testing accept page (form submission)...")
        # Test accepting the page (form submission)
        form_data = {
            "P1_NAME": "John Doe",
            "P1_CHOICE": "N",
            "p_session_id": session_id,
            "p_request": "SUBMIT"
        }

        accept_result = rendering_service.accept_page(
            application_alias="TESTAPP",
            page_number=1,
            session_id=session_id,
            form_data=form_data
        )

        print(f"[RESULT] Accept result: {accept_result['success']}")
        if accept_result['success']:
            print("[SUCCESS] Page acceptance successful")
        else:
            print(f"[FAILED] Page acceptance failed: {accept_result.get('message')}")

        # Check that the values were updated in the session
        session_service = SessionService(db)
        updated_name = session_service.get_item(session_id, page.id, "P1_NAME")
        updated_choice = session_service.get_item(session_id, page.id, "P1_CHOICE")
        print(f"[VALUES] Updated values - Name: {updated_name}, Choice: {updated_choice}")

        assert updated_name == "John Doe"
        assert updated_choice == "N"
        print("[SUCCESS] Session values updated correctly")

        print("\n[COMPLETE] All Phase 2 tests passed!")
        return True

    except Exception as e:
        print(f"[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = test_phase2()
    sys.exit(0 if success else 1)