import re
from typing import Any

import dlt
import lancedb
from bs4 import BeautifulSoup
from dlt.destinations.adapters import lancedb_adapter
from dlt.sources.helpers.rest_client.paginators import BasePaginator
from langchain_text_splitters import RecursiveCharacterTextSplitter
from requests import Request, Response

from src.config import settings
from src.rag.rest_api import rest_api_source


class WordPressPaginator(BasePaginator):
    def __init__(self, start_page: int = 1, per_page: int = settings.DAN_PER_PAGE):
        self.current_page = start_page
        self.per_page = per_page

    def update_request(self, request: Request) -> None:
        if request.params is None:
            request.params = {}
        request.params["page"] = self.current_page
        request.params["per_page"] = self.per_page

    def update_state(self, response: Response, data: list[Any] | None = None) -> None:
        if not data or len(data) < self.per_page or response.status_code == 400:
            self._has_next_page = False
        else:
            self.current_page += 1
            self._has_next_page = True


def remove_html_tags(text):
    """Remove HTML tags, JavaScript, and extra spaces from a string."""
    soup = BeautifulSoup(text, "html.parser")

    for script in soup(["script", "iframe"]):
        script.extract()

    cleaned_text = soup.get_text(separator=" ")
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

    return cleaned_text


def chunk_text(text, chunk_size=None, chunk_overlap=None):
    """Split text into chunks using RecursiveCharacterTextSplitter."""
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    return text_splitter.split_text(text)


def wordpress_rest_api_source():
    """Create a dlt source for DAN WordPress REST API endpoints."""
    base_url = settings.DAN_BASE_URL
    per_page = settings.DAN_PER_PAGE
    start_date = settings.DAN_START_DATE

    return rest_api_source(
        {
            "client": {
                "base_url": base_url,
                "paginator": WordPressPaginator(start_page=1),
            },
            "resource_defaults": {
                "primary_key": "id",
                "write_disposition": "merge",
                "endpoint": {
                    "params": {
                        "per_page": per_page,
                    },
                },
            },
            "resources": [
                {
                    "name": "dan_health_resources",
                    "endpoint": {
                        "path": "dan_health_resources",
                        "params": {
                            "modified_after": {
                                "type": "incremental",
                                "cursor_path": "modified",
                                "initial_value": start_date,
                            },
                        },
                    },
                },
                {
                    "name": "dan_alert_diver",
                    "endpoint": {
                        "path": "dan_alert_diver",
                        "params": {
                            "modified_after": {
                                "type": "incremental",
                                "cursor_path": "modified",
                                "initial_value": start_date,
                            },
                        },
                    },
                },
                {
                    "name": "dan_diving_incidents",
                    "endpoint": {
                        "path": "dan_diving_incidents",
                        "params": {
                            "modified_after": {
                                "type": "incremental",
                                "cursor_path": "modified",
                                "initial_value": start_date,
                            },
                        },
                    },
                },
                {
                    "name": "dan_diseases_conds",
                    "endpoint": {
                        "path": "dan_diseases_conds",
                        "params": {
                            "modified_after": {
                                "type": "incremental",
                                "cursor_path": "modified",
                                "initial_value": start_date,
                            },
                        },
                    },
                },
            ],
        }
    )


@dlt.transformer()
def dan_articles(article):
    """Transform DAN articles into text chunks for vectorization."""
    clean_content = remove_html_tags(article["content"]["rendered"])
    yield from chunk_text(clean_content)


def run_pipeline(*args, **kwargs):
    """Run the DAN articles ingestion pipeline into LanceDB."""
    pipeline = dlt.pipeline(
        pipeline_name="dan_articles",
        destination="lancedb",
        dataset_name="dan_articles",
    )

    data = wordpress_rest_api_source() | dan_articles

    pipeline.run(
        lancedb_adapter(data, embed="value"),
        table_name="texts",
        write_disposition="merge",
    )

    db = lancedb.connect(settings.LANCEDB_URI)
    dbtable = db.open_table(settings.LANCEDB_TABLE_NAME)
    dbtable.create_fts_index("value", replace=True)

    return settings.LANCEDB_TABLE_NAME
