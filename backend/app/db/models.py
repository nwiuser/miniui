from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm relationship
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

class SessionState(Base):
    __tablename__ = "apex_session_state"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    page_id = Column(Integer, nullable=False, index=True)
    item_name = Column(String(255), nullable=False)  # e.g., P1_FIELD_NAME
    item_value = Column(Text)  # Stored as string, application handles type conversion
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Ensure unique session/item combination
    __table_args__ = (
        Index('ux_session_item', 'session_id', 'item_name', unique=True),
    )
