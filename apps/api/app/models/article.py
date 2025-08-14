from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.database.connection import Base

class Article(Base):
    __tablename__ = "articles"
    
    article_id = Column(String, primary_key=True)
    cluster_id = Column(String, ForeignKey("story_clusters.cluster_id"), nullable=False)
    url = Column(Text, nullable=False, unique=True)
    uniqueness_hash = Column(String, nullable=False, unique=True, index=True)
    
    # Article content
    source_name = Column(String, nullable=False)
    title = Column(Text, nullable=False)
    summary = Column(Text)
    publication_timestamp = Column(DateTime(timezone=True))
    
    # AI-generated metadata
    category = Column(String)
    subcategory = Column(String)
    tags = Column(Text)  # JSON string for now, can upgrade to JSONB later
    
    # Vector embedding (1536 dimensions for text-embedding-004)
    embedding = Column(Vector(1536))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    story_cluster = relationship("StoryCluster", back_populates="articles")
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_articles_cluster_id', 'cluster_id'),
        Index('ix_articles_category', 'category'),
        Index('ix_articles_publication_timestamp', 'publication_timestamp'),
    )
