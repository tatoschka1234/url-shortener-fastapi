import logging.config
import pyshorteners

from typing import Any, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.db.db import Base
from sqlalchemy import exc


from src.core.logger import LOGGING
logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

type_tiny = pyshorteners.Shortener()


class Repository:
    def get(self, *args, **kwargs):
        raise NotImplementedError

    def get_multi(self, *args, **kwargs):
        raise NotImplementedError

    def create(self, *args, **kwargs):
        raise NotImplementedError

    def update(self, *args, **kwargs):
        raise NotImplementedError

    def delete(self, *args, **kwargs):
        raise NotImplementedError


ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
FullSchemaType = TypeVar("FullSchemaType", bound=BaseModel)
HealthModelType = TypeVar("HealthModelType", bound=Base)
ErrorModelType = TypeVar("ErrorModelType", bound=Base)


class RepositoryDB(Repository, Generic[ModelType, CreateSchemaType,
                   HealthModelType, ErrorModelType]):

    def __init__(self, model: Type[ModelType], health: Type[HealthModelType],
                 error: Type[ErrorModelType]):
        self._model = model
        self._health = health
        self._error = error

    async def get_db_status(self, db: AsyncSession) -> HealthModelType:
        self._health.db_status = "Unhealthy"
        try:
            results = await db.execute(statement="SELECT 1")
            if results:
                self._health.db_status = "Healthy"
        except Exception as e:
            self._health.db_status = f"Unhealthy: {e}"
        return self._health

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        statement = select(self._model).where(self._model.id == id)
        results = await db.execute(statement=statement)
        return results.scalar_one_or_none()

    @staticmethod
    def check_url(url):
        if not url.startswith("http"):
            url = "http://" + url
        if url[-1] != "/":
            url += "/"
        return url

    async def create_multi(self, db: AsyncSession,
                           objs_in: List[CreateSchemaType]) -> List[ModelType]:
        new_objs = []
        for obj in objs_in:
            obj_in_data = jsonable_encoder(obj)
            long_url = self.check_url(obj_in_data["original_url"])
            short_url = type_tiny.tinyurl.short(long_url)
            db_obj = self._model(**obj_in_data)
            db_obj.short_url = short_url
            db_obj.original_url = long_url
            new_objs.append(db_obj)
        try:
            db.add_all(new_objs)
            await db.commit()
            for obj in new_objs:
                await db.refresh(obj)
            return new_objs
        except exc.IntegrityError:
            await db.rollback()
            logger.exception("Item already exists")
            self._error.detail = "Item already exists"
            return self._error

    async def get_multi(
        self, db: AsyncSession, *, skip=0, limit=100
    ) -> List[ModelType]:
        statement = select(self._model).offset(skip).limit(limit)
        results = await db.execute(statement=statement)
        return results.scalars().all()

    async def create(self, db: AsyncSession, *,
                     obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        long_url = self.check_url(obj_in_data["original_url"])
        try:
            short_url = type_tiny.tinyurl.short(long_url)
        except pyshorteners.exceptions.BadURLException as e:
            logger.exception(e)
            self._error.detail = str(e)
            return self._error
        db_obj = self._model(**obj_in_data)
        db_obj.short_url = short_url
        db_obj.original_url = long_url
        try:
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except exc.IntegrityError as e:
            await db.rollback()
            logger.warning(f"Item with url "
                           f"{db_obj.original_url} already exists")
            self._error.detail = str(e)
            return self._error

    async def update_deleted_field(
        self,
        db: AsyncSession,
        *,
            url_id: int
    ) -> ModelType:
        record = await self.get(db, url_id)
        record.deleted = True
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record


class RepositoryUsage(Repository, Generic[ModelType, CreateSchemaType,
                      FullSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self._model = model

    async def create(self, db: AsyncSession, *,
                     obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self._model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def count(self, db: AsyncSession, *, max_result=10, offset=0,
                    full_info=False,
                    obj_id: int) -> Union[int, List[ModelType]]:
        statement = select(self._model.url_id, self._model.used_at,
                           self._model.client_host,
                           self._model.client_port
                           ).where(self._model.url_id == obj_id).offset(
            offset).limit(max_result)
        results = await db.execute(statement=statement)
        if full_info:
            return results.all()
        return len(results.scalars().all())
