from src.models.urlmodel import UrlModel, UrlUsageModel
from src.schemas.shorturl import ShortUrlCreate, UrlUsageCreate, UrlUsageFull, DBHealthModel, HTTPError
from .base import RepositoryDB, RepositoryUsage


class RepositoryURLs(RepositoryDB[UrlModel, ShortUrlCreate, DBHealthModel,
                     HTTPError]):
    pass


class RepositoryURLUsage(RepositoryUsage[UrlUsageModel, UrlUsageCreate,
                         UrlUsageFull]):
    pass


url_crud = RepositoryURLs(UrlModel, DBHealthModel, HTTPError)
usage_crud = RepositoryURLUsage(UrlUsageModel)
