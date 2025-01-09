from http.client import HTTPResponse
from typing import Tuple, cast


from httpx import AsyncClient, HTTPStatusError, Response
from SPARQLWrapper import QueryResult, SPARQLWrapper
from SPARQLWrapper.SPARQLExceptions import (
    EndPointInternalError,
    EndPointNotFound,
    QueryBadFormed,
    Unauthorized,
    URITooLong,
)


# Hack the SparqlWrapper to add async methods
class AsyncSparqlWrapper(SPARQLWrapper):
    async def _asyncQuery(self) -> Tuple[HTTPResponse, str]:
        async with AsyncClient() as client:
            request = self._createRequest()

            method = request.get_method()
            url = request.get_full_url()
            headers = dict(request.headers)
            # May not have correct type?
            data = request.data if method == "POST" else None

            response = await client.request(
                method, url, headers=headers, timeout=None, data=data
            )
            try:
                response.raise_for_status()
            except HTTPStatusError as e:
                if e.response.status_code == 400:
                    raise QueryBadFormed(e.response.read())
                elif e.response.status_code == 404:
                    raise EndPointNotFound(e.response.read())
                elif e.response.status_code == 401:
                    raise Unauthorized(e.response.read())
                elif e.response.status_code == 414:
                    raise URITooLong(e.response.read())
                elif e.response.status_code == 500:
                    raise EndPointInternalError(e.response.read())
                else:
                    raise e
            # worst part of HACK
            return cast(HTTPResponse, ResponseWrapper(response)), self.returnFormat

    async def asyncQuery(self) -> QueryResult:
        result = await self._asyncQuery()
        return QueryResult(result)

    async def asyncQueryAndConvert(self):
        res = await self.asyncQuery()
        return res.convert()


class ResponseWrapper:
    def __init__(self, response: Response):
        self.response = response

    def read(self) -> bytes:
        return self.response.read()

    def getcode(self) -> int:
        return self.response.status_code

    def geturl(self) -> str:
        return f"{self.response.url}"

    def info(self):
        return self.response.headers
