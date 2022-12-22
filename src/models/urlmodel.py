from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from src.db.db import Base
from src.core.config import SHORT_URL_MAX_LEN


class UrlModel(Base):
    __tablename__ = "url"
    id = Column(Integer, primary_key=True)
    original_url = Column(String(2048), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    short_url = Column(String(SHORT_URL_MAX_LEN), unique=True, nullable=False)
    deleted = Column(Boolean, default=False)
    url_usages = relationship("UrlUsageModel")

    def __repr__(self):
        return (f"URL(original url: '{self.original_url}', "
                f"short='{self.short_url}', use: {self.url_usages}")


class UrlUsageModel(Base):
    __tablename__ = "usage"
    id = Column(Integer, primary_key=True)
    url_id = Column(Integer, ForeignKey('url.id'))

    used_at = Column(DateTime, default=datetime.utcnow)
    client_port = Column(Integer)
    client_host = Column(String(2048))
