from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Application(Base):
    __tablename__ = "apex_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    alias = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pages = relationship("Page", back_populates="application", cascade="all, delete-orphan")

class Page(Base):
    __tablename__ = "apex_pages"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("apex_applications.id"), nullable=False)
    name = Column(String(255), nullable=False)
    alias = Column(String(100), index=True)
    page_number = Column(Integer, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    application = relationship("Application", back_populates="pages")
    regions = relationship("Region", back_populates="page", cascade="all, delete-orphan")
    items = relationship("PageItem", back_populates="page", cascade="all, delete-orphan")
    processes = relationship("PageProcess", back_populates="page", cascade="all, delete-orphan")

class Region(Base):
    __tablename__ = "apex_regions"
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("apex_pages.id"), nullable=False)
    name = Column(String(255), nullable=False)
    region_type = Column(String(50), nullable=False)  # static_content, report, form, chart, etc.
    template_options = Column(JSON)  # Store region-specific options as JSON
    position = Column(Integer, default=0)  # For ordering regions on page
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    page = relationship("Page", back_populates="regions")

class PageItem(Base):
    __tablename__ = "apex_page_items"
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("apex_pages.id"), nullable=False)
    name = Column(String(255), nullable=False)  # Item name (e.g., P1_FIELD_NAME)
    alias = Column(String(100))  # Human-readable alias
    item_type = Column(String(50), nullable=False)  # text, textarea, select, date, etc.
    label = Column(String(255))
    placeholder = Column(String(255))
    default_value = Column(String(255))
    is_required = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    page = relationship("Page", back_populates="items")

class PageProcess(Base):
    __tablename__ = "apex_page_processes"
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("apex_pages.id"), nullable=False)
    name = Column(String(255), nullable=False)
    process_type = Column(String(50), nullable=False)  # sql, plsql, reset_pagination, etc.
    process_code = Column(Text)  # The actual SQL/PLSQL code or Python code
    execution_sequence = Column(Integer, default=10)  # Order of execution
    execution_point = Column(String(20), default="ON_SUBMIT_BEFORE_COMPUTATION")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    page = relationship("Page", back_populates="processes")

class Session(Base):
    __tablename__ = "apex_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    application_id = Column(Integer, ForeignKey("apex_applications.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("apex_workspace_users.id"), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    application = relationship("Application")
    user = relationship("WorkspaceUser")
    items = relationship("SessionStateItem", back_populates="session", cascade="all, delete-orphan")


class SessionStateItem(Base):
    __tablename__ = "apex_session_state"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("apex_sessions.id"), nullable=False)
    page_id = Column(Integer, nullable=False, index=True)
    item_name = Column(String(255), nullable=False)  # e.g., P1_FIELD_NAME
    item_value = Column(Text)  # Stored as string, application handles type conversion
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    session = relationship("Session", back_populates="items")

    # Ensure unique session/page/item combination
    __table_args__ = (
        Index('ux_session_page_item', 'session_id', 'page_id', 'item_name', unique=True),
    )


class Validation(Base):
    __tablename__ = "apex_validations"

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("apex_pages.id"), nullable=False)
    item_name = Column(String(255), nullable=False)  # The item this validation applies to (e.g., P1_FIELD_NAME)
    validation_type = Column(String(50), nullable=False)  # NOT_NULL, VALIDATION, SQL_COMPARISON, etc.
    validation_expression = Column(Text)  # The validation logic (SQL, PL/SQL, or literal)
    error_message = Column(String(4000))  # Error message to display when validation fails
    when_button_pressed = Column(String(255))  # Optional: button that triggers this validation
    condition_type = Column(String(255))  # Condition type (e.g., 'VAL_NOT_NULL')
    condition_expression = Column(Text)  # Condition expression
    is_active = Column(Boolean, default=True)
    sequence = Column(Integer, default=1)  # Order of execution
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    page = relationship("Page")


class Lov(Base):
    __tablename__ = "apex_lovs"

    id = Column(Integer, primary_key=True, index=True)
    lov_name = Column(String(255), unique=True, nullable=False)  # Unique name for the LOV
    lov_definition = Column(Text)  # SQL query or static values definition
    is_static = Column(Boolean, default=False)  # True for static LOVs, False for SQL-based
    display_extra = Column(Boolean, default=True)  # Show extra options
    translation_applicable = Column(Boolean, default=False)
    is_translatable = Column(Boolean, default=False)
    static_values = Column(Text)  # For static LOVs: "STATIC2:Value1;Display1,Value2;Display2"
    is_enterable = Column(Boolean, default=False)  # Whether users can enter custom values
    show_null_value = Column(Boolean, default=False)  # Show null option
    null_text = Column(String(255))  # Text for null option
    null_value = Column(String(255))  # Value for null option
    apex_item_height = Column(Integer)  # Height for textarea/LOV
    apex_item_width = Column(Integer)   # Width for textarea/LOV
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WorkspaceUser(Base):
    __tablename__ = "apex_workspace_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # Hashed password
    first_name = Column(String(255))
    last_name = Column(String(255))
    email = Column(String(255), unique=True)
    administrator_role = Column(String(50))  # e.g., 'ADMIN', 'DEVELOPER', 'END_USER'
    account_expiry_date = Column(DateTime)
    account_locked = Column(Boolean, default=False)
    failed_access_attempts = Column(Integer, default=0)
    change_password_on_first_use = Column(Boolean, default=False)
    first_name_phonetic = Column(String(255))
    last_name_phonetic = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
