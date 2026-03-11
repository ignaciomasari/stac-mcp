"""STAC client wrapper for common catalog operations."""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

import requests
from pystac_client.exceptions import APIError

# Ensure Session.request enforces a default timeout when one is not provided.
# This is a conservative safeguard for environments where sessions may be
# constructed by third-party libraries (pystac_client) without an explicit
# timeout. We wrap at the class level so all Session instances pick this up.
try:
    _original_session_request = requests.Session.request

    def _session_request_with_default_timeout(
        self, method, url, *args, timeout=None, **kwargs
    ):
        default_timeout = int(os.getenv("STAC_MCP_REQUEST_TIMEOUT", "30"))
        if timeout is None:
            timeout = default_timeout
        return _original_session_request(
            self, method, url, *args, timeout=timeout, **kwargs
        )

    # Only set if not already wrapped (avoid double-wrapping in test environments)
    if requests.Session.request is not _session_request_with_default_timeout:
        requests.Session.request = _session_request_with_default_timeout
except (AttributeError, TypeError) as exc:  # pragma: no cover - defensive
    # logger may not be defined yet; use module-level logging as a fallback
    logging.getLogger(__name__).debug(
        "Could not install Session.request timeout wrapper: %s", exc
    )


# HTTP status code constants (avoid magic numbers - PLR2004)
HTTP_404 = 404

# Conformance URIs from STAC API specifications. Lists include multiple versions
# to support older APIs.
CONFORMANCE_AGGREGATION = [
    "https://api.stacspec.org/v1.0.0/ogc-api-features-p3/conf/aggregation",
]
CONFORMANCE_QUERY = [
    "https://api.stacspec.org/v1.0.0/item-search#query",
    "https://api.stacspec.org/v1.0.0-beta.2/item-search#query",
]
CONFORMANCE_QUERYABLES = [
    "https://api.stacspec.org/v1.0.0/item-search#queryables",
    "https://api.stacspec.org/v1.0.0-rc.1/item-search#queryables",
]
CONFORMANCE_SORT = [
    "https://api.stacspec.org/v1.0.0/item-search#sort",
]


# Initialized earlier for the timeout wrapper fallback
logger = logging.getLogger(__name__)


class ConformanceError(NotImplementedError):
    """Raised when a STAC API does not support a required capability."""


class SSLVerificationError(ConnectionError):
    """Raised when SSL certificate verification fails for a STAC request.

    This wraps an underlying ``ssl.SSLCertVerificationError`` (if available)
    to provide a clearer, library-specific failure mode and actionable
    guidance for callers. Handlers may choose to surface remediation steps
    (e.g., setting a custom CA bundle) without needing to parse low-level
    urllib exceptions.
    """


class STACTimeoutError(OSError):
    """Raised when a STAC API request times out.

    Provides actionable guidance for timeout scenarios, including suggestions
    to increase timeout or check network connectivity.
    """


class ConnectionFailedError(ConnectionError):
    """Raised when connection to STAC API fails.

    Wraps underlying connection errors (DNS, refused connection, etc.) with
    clearer context and remediation guidance.
    """


class STACClient:
    """STAC Client wrapper for common operations."""

    _DEFAULT_CATALOG_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"

    def __init__(
        self,
        catalog_url: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._search_cache: dict[
            str, tuple[float, list[Any] | list[dict[str, Any]]]
        ] = {}
        try:
            self.search_cache_ttl_seconds = int(
                os.getenv("STAC_MCP_SEARCH_CACHE_TTL_SECONDS", "300")
            )
        except (TypeError, ValueError):
            self.search_cache_ttl_seconds = 300

        # Resolve catalog URL: explicit arg > STAC_API_URL env var > package default
        if catalog_url is not None:
            self.catalog_url = catalog_url
        else:
            self.catalog_url = os.getenv("STAC_API_URL", self._DEFAULT_CATALOG_URL)

        self.headers = headers or {}
        self._client = None
        self._conformance = None
        self._last_retry_attempts = 0
        self._last_insecure_ssl = False

    def _search_cache_key(
        self,
        collections: list[str] | None,
        bbox: list[float] | None,
        datetime: str | None,
        query: dict[str, Any] | None,
        limit: int,
    ) -> str:
        """Create a deterministic cache key for search parameters."""
        # Include the identity of the underlying client object so that tests
        # which patch `STACClient.client` get distinct cache entries.
        try:
            client_id = id(self.client)
        except Exception:  # noqa: BLE001
            client_id = 0
        key_obj = {
            "collections": collections or [],
            "bbox": bbox,
            "datetime": datetime,
            "query": query,
            "limit": limit,
            "client_id": client_id,
        }
        # Use json.dumps with sort_keys for deterministic serialization.
        return json.dumps(key_obj, sort_keys=True, default=str)

    def _cached_search(
        self,
        collections: list[str] | None = None,
        bbox: list[float] | None = None,
        datetime: str | None = None,
        query: dict[str, Any] | None = None,
        sortby: list[str] | list[dict[str, str]] | None = None,
        limit: int = 10,
    ):  # -> list[dict[str, Any]]:
        """Run a search and cache the resulting item list per-client.

        Returns a list of pystac.Item objects (as returned by the underlying
        client's search.items()).
        """
        key = self._search_cache_key(collections, bbox, datetime, query, limit)
        now = time.time()
        cached = self._search_cache.get(key)
        if cached is not None:
            ts, val = cached
            # Read TTL from the environment dynamically so tests can adjust
            # the TTL even when a shared client was instantiated earlier.
            try:
                ttl = int(
                    os.getenv(
                        "STAC_MCP_SEARCH_CACHE_TTL_SECONDS",
                        str(self.search_cache_ttl_seconds),
                    )
                )
            except (TypeError, ValueError):
                ttl = getattr(self, "search_cache_ttl_seconds", 300)
            if now - ts <= ttl:
                return val
            # expired
            self._search_cache.pop(key, None)

        search = self.client.search(
            collections=collections,
            bbox=bbox,
            datetime=datetime,
            query=query,
            sortby=sortby,
            limit=limit,
        )
        items = []
        for idx, _item in enumerate(search.items()):
            items.append(_item if isinstance(_item, dict) else _item.to_dict())
            if idx + 1 >= limit:
                break

        self._search_cache[key] = (now, items)
        return items

    def _cached_collections(self, limit: int = 10) -> list[dict[str, Any]]:
        key = f"collections:limit={int(limit)}"
        now = time.time()
        cached = self._search_cache.get(key)
        if cached is not None:
            ts, val = cached
            try:
                ttl = int(
                    os.getenv(
                        "STAC_MCP_SEARCH_CACHE_TTL_SECONDS",
                        str(self.search_cache_ttl_seconds),
                    )
                )
            except (TypeError, ValueError):
                ttl = getattr(self, "search_cache_ttl_seconds", 300)
            if now - ts <= ttl:
                return val  # type: ignore[return-value]
            self._search_cache.pop(key, None)

        collections = []
        for collection in self.client.get_collections():
            collections.append(
                {
                    "id": collection.id,
                    "title": collection.title or collection.id,
                    "description": collection.description,
                    "extent": (
                        collection.extent.to_dict() if collection.extent else None
                    ),
                    "license": collection.license,
                    "providers": (
                        [p.to_dict() for p in collection.providers]
                        if collection.providers
                        else []
                    ),
                }
            )
            if limit > 0 and len(collections) >= limit:
                break

        self._search_cache[key] = (now, collections)
        return collections

    @property
    def client(self) -> Any:
        if self._client is None:
            from pystac_client import (  # noqa: PLC0415 local import (guarded)
                Client as _client,  # noqa: N813
            )
            from pystac_client.stac_api_io import (  # noqa: PLC0415 local import (guarded)
                StacApiIO,
            )

            stac_io = StacApiIO(headers=self.headers)
            self._client = _client.open(self.catalog_url, stac_io=stac_io)
            # Ensure the underlying requests session used by pystac_client
            # enforces a sensible default timeout to avoid indefinite hangs.
            # Some HTTP libraries or network environments may drop or stall
            # connections; wrapping the session.request call provides a
            # portable safeguard without changing call sites.
            try:
                session = getattr(stac_io, "session", None)
                if session is not None and hasattr(session, "request"):
                    original_request = session.request

                    def _request_with_default_timeout(
                        method, url, *args, timeout=None, **kwargs
                    ):
                        # Default timeout (seconds) can be overridden via env var
                        default_timeout = int(
                            os.getenv("STAC_MCP_REQUEST_TIMEOUT", "30")
                        )
                        if timeout is None:
                            timeout = default_timeout
                        return original_request(
                            method, url, *args, timeout=timeout, **kwargs
                        )

                    # Monkey-patch the session.request to apply default timeout
                    session.request = _request_with_default_timeout
            except (AttributeError, TypeError, RuntimeError) as exc:
                # Be conservative: if wrapping fails, fall back to original behavior
                logger.debug(
                    "Could not wrap pystac_client session.request with timeout: %s",
                    exc,
                )
        return self._client

    @property
    def conformance(self) -> list[str]:
        """Lazy-loads and caches STAC API conformance classes."""
        if self._conformance is None:
            self._conformance = self.client.to_dict().get("conformsTo", [])
        return self._conformance

    def _check_conformance(self, capability_uris: list[str]) -> None:
        """Raises ConformanceError if API lacks a given capability.

        Checks if any of the provided URIs are in the server's conformance list.
        """
        if not any(uri in self.conformance for uri in capability_uris):
            # For a cleaner error message, report the first (preferred) URI.
            capability_name = capability_uris[0]
            msg = (
                f"API at {self.catalog_url} does not support '{capability_name}' "
                "(or a compatible version)"
            )
            raise ConformanceError(msg)

    # ----------------------------- Collections ----------------------------- #
    def search_collections(self, limit: int = 10) -> list[dict[str, Any]]:
        # Use cached collections when possible
        try:
            return self._cached_collections(limit=limit)
        except APIError:  # pragma: no cover - network dependent
            logger.exception("Error fetching collections")
            raise

    def get_collection(self, collection_id: str) -> dict[str, Any]:
        try:
            collection = self.client.get_collection(collection_id)
        except APIError:  # pragma: no cover - network dependent
            logger.exception("Error fetching collection %s", collection_id)
            raise
        else:
            if collection is None:
                return None
            return {
                "id": collection.id,
                "title": collection.title or collection.id,
                "description": collection.description,
                "extent": collection.extent.to_dict() if collection.extent else None,
                "license": collection.license,
                "providers": (
                    [p.to_dict() for p in collection.providers]
                    if collection.providers
                    else []
                ),
                "summaries": (
                    collection.summaries.to_dict() if collection.summaries else {}
                ),
                "assets": (
                    {k: v.to_dict() for k, v in collection.assets.items()}
                    if collection.assets
                    else {}
                ),
            }

    # ------------------------------- Items -------------------------------- #
    def search_items(
        self,
        collections: list[str] | None = None,
        bbox: list[float] | None = None,
        datetime: str | None = None,
        query: dict[str, Any] | None = None,
        sortby: list[str] | list[dict[str, str]] | None = None,
        limit: int = 10,
    ) -> list[Any] | list[dict[str, Any]]:
        extra_args = {}
        if query:
            self._check_conformance(CONFORMANCE_QUERY)
            extra_args["query"] = query
        if sortby:
            self._check_conformance(CONFORMANCE_SORT)
            extra_args["sortby"] = sortby
        try:
            # Use cached search results (per-client) when available.
            items = self._cached_search(
                collections=collections,
                bbox=bbox,
                datetime=datetime,
                limit=limit,
                **extra_args,
            )
        except APIError:  # pragma: no cover - network dependent
            logger.exception("Error searching items")
            raise

        return items

    def get_item(self, collection_id: str, item_id: str) -> dict[str, Any]:
        try:
            collection = self.client.get_collection(collection_id)
            if collection is None:
                return None
            item = collection.get_item(item_id)
        except APIError:  # pragma: no cover - network dependent
            logger.exception(
                "Error fetching item %s from collection %s",
                item_id,
                collection_id,
            )
            raise
        else:
            if item is None:
                return None
            # Normalize defensively as above
            return {
                "id": getattr(item, "id", None),
                "collection": getattr(item, "collection_id", None),
                "geometry": getattr(item, "geometry", None),
                "bbox": getattr(item, "bbox", None),
                "datetime": (
                    item.datetime.isoformat()
                    if getattr(item, "datetime", None)
                    else None
                ),
                "properties": getattr(item, "properties", {}) or {},
                "assets": {
                    k: v.to_dict() for k, v in getattr(item, "assets", {}).items()
                },
            }

    # ----------------------- Collection Keywords ------------------------- #
    def list_collection_keywords(self) -> dict[str, list[str] | str]:
        """Return a lightweight mapping of {collection_id: keywords}.

        Falls back to the first sentence of the description (or the title)
        when a collection has no keywords defined.
        """
        key = "collection_keywords"
        now = time.time()
        cached = self._search_cache.get(key)
        if cached is not None:
            ts, val = cached
            try:
                ttl = int(
                    os.getenv(
                        "STAC_MCP_SEARCH_CACHE_TTL_SECONDS",
                        str(self.search_cache_ttl_seconds),
                    )
                )
            except (TypeError, ValueError):
                ttl = getattr(self, "search_cache_ttl_seconds", 300)
            if now - ts <= ttl:
                return val  # type: ignore[return-value]
            self._search_cache.pop(key, None)

        result: dict[str, list[str] | str] = {}
        for collection in self.client.get_collections():
            keywords = getattr(collection, "keywords", None)
            if keywords:
                result[collection.id] = keywords
            elif collection.description:
                result[collection.id] = collection.description.split(".", 1)[0]
            else:
                result[collection.id] = collection.title or collection.id

        self._search_cache[key] = (now, result)
        return result

    # ---------------------- Catalog Introspection ------------------------ #
    def get_root_document(self) -> dict[str, Any]:
        # Some underlying client implementations do not provide a
        # get_root_document() convenience. Use to_dict() as a stable
        # fallback and normalize the keys we care about.
        try:
            raw = self.client.to_dict() if hasattr(self.client, "to_dict") else {}
        except (AttributeError, APIError):
            # to_dict() may not be available or the underlying client raised an
            # APIError; swallow those specific errors and return an empty dict.
            raw = {}
        if not raw:  # Unexpected but keep consistent shape
            return {
                "id": None,
                "title": None,
                "description": None,
                "links": [],
                "conformsTo": [],
            }
        # Normalize subset we care about
        return {
            "id": raw.get("id"),
            "title": raw.get("title"),
            "description": raw.get("description"),
            "links": raw.get("links", []),
            "conformsTo": raw.get("conformsTo", raw.get("conforms_to", [])),
        }

    def get_conformance(
        self,
        check: str | list[str] | None = None,
    ) -> dict[str, Any]:
        conforms = self.conformance
        checks: dict[str, bool] | None = None
        if check:
            targets = [check] if isinstance(check, str) else list(check)
            checks = {c: c in conforms for c in targets}
        return {"conformsTo": conforms, "checks": checks}

    def get_queryables(self, collection_id: str | None = None) -> dict[str, Any]:
        # Some STAC servers expose a /queryables endpoint via a link on the root
        # document but may omit the exact conformance URI from the conformance
        # list. Try the strict conformance check first; if it fails, fall back
        # to inspecting the root document for an explicit queryables link and
        # allow the call to proceed when such a link is present.
        try:
            self._check_conformance(CONFORMANCE_QUERYABLES)
        except ConformanceError:
            # If the conformance check fails, see if the root advertises a
            # queryables link. If it does, proceed; otherwise re-raise the
            # ConformanceError.
            root = self.get_root_document()
            links = root.get("links", [])
            for link in links:
                rel = link.get("rel")
                href = link.get("href", "")
                # If we find a queryables link, break and allow the call to proceed.
                # We do not validate the href here; the subsequent request may still
                # fail.
                # opengis.net link is preferred, but some servers use custom rels with
                # /queryables in href.
                if rel == "http://www.opengis.net/def/rel/ogc/1.0/queryables" or (
                    isinstance(href, str) and "/queryables" in href
                ):
                    break
            else:
                # No queryables conformance and no link advertised -> fail.
                raise

        path = (
            f"/collections/{collection_id}/queryables"
            if collection_id
            else "/queryables"
        )
        base = self.catalog_url
        if base.endswith("/catalog.json"):
            base = base[: -len("/catalog.json")]
        base = base.rstrip("/")
        url = f"{base}{path}"
        request_headers = self.headers.copy()
        request_headers.setdefault("Accept", "application/json")
        try:
            res = requests.get(url, headers=request_headers, timeout=30)
            # If the collection-scoped endpoint returns 404 and we were trying a
            # collection-specific path, some servers instead expose the root
            # /queryables endpoint and accept a `collection` query parameter.
            # Try that fallback before giving up.
            if not res.ok:
                if res.status_code == HTTP_404 and collection_id is not None:
                    fallback_url = f"{base}/queryables?collection={collection_id}"
                    try:
                        res2 = requests.get(
                            fallback_url, headers=request_headers, timeout=30
                        )
                        if not res2.ok:
                            return {
                                "queryables": {},
                                "collection_id": collection_id,
                                "message": f"Queryables not available (HTTP \
                                    {res2.status_code})",
                            }
                        q = res2.json() if res2.content else {}
                    except requests.RequestException as e:
                        logger.exception("Failed to fetch queryables %s", fallback_url)
                        return {
                            "queryables": {},
                            "collection_id": collection_id,
                            "message": f"Queryables not available \
                                (request failed: {e})",
                        }
                else:
                    return {
                        "queryables": {},
                        "collection_id": collection_id,
                        "message": f"Queryables not available (HTTP {res.status_code})",
                    }
            else:
                q = res.json() if res.content else {}
        except requests.RequestException as e:
            logger.exception("Failed to fetch queryables %s", url)
            return {
                "queryables": {},
                "collection_id": collection_id,
                "message": f"Queryables not available (request failed: {e})",
            }
        props = q.get("properties") or q.get("queryables") or {}
        return {"queryables": props, "collection_id": collection_id}

    def get_aggregations(
        self,
        collections: list[str] | None = None,
        ids: list[str] | None = None,
        bbox: list[float] | None = None,
        intersects: dict[str, Any] | None = None,
        datetime: str | None = None,
        query: dict[str, Any] | None = None,
        filter_lang: str | None = None,  # noqa: ARG002
        filter_expr: dict[str, Any] | None = None,  # noqa: ARG002
        fields: list[str] | None = None,
        sortby: list[dict[str, Any]] | None = None,
        limit: int = 0,
    ) -> dict[str, Any]:
        self._check_conformance(CONFORMANCE_AGGREGATION)
        base = self.catalog_url
        if base.endswith("/catalog.json"):
            base = base[: -len("/catalog.json")]
        base = base.rstrip("/")
        url = f"{base}/search"

        request_headers = self.headers.copy()
        request_headers["Accept"] = "application/json"

        body: dict[str, Any] = {}
        if collections:
            body["collections"] = collections
        if ids:
            body["ids"] = ids
        if bbox:
            body["bbox"] = bbox
        if intersects:
            body["intersects"] = intersects
        if datetime:
            body["datetime"] = datetime
        if query:
            body["query"] = query
        if sortby:
            body["sortby"] = sortby
        if limit and limit > 0:
            body["limit"] = limit

        # Aggregation-specific part of the request
        if fields:
            body["aggregations"] = [{"name": f, "params": {}} for f in fields]

        try:
            resp = requests.post(url, json=body, headers=request_headers, timeout=60)
            if not resp.ok:
                return {
                    "supported": False,
                    "aggregations": {},
                    "message": f"Search endpoint unavailable (HTTP {resp.status_code})",
                    "parameters": body,
                }
            res_json = resp.json() if resp.content else {}
            aggs_result = res_json.get("aggregations") or {}
            return {
                "supported": "aggregations" in res_json,
                "aggregations": aggs_result,
                "meta": res_json.get("meta", {}),
                "links": res_json.get("links", []),
            }
        except requests.RequestException as e:
            logger.exception("Aggregation request failed %s", url)
            return {
                "supported": False,
                "aggregations": {},
                "message": f"Search endpoint unavailable (request failed: {e})",
                "parameters": body,
            }

