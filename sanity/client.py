"""Sanity.io HTTP API Python Client"""
import json
import requests
import mimetypes

from sanity import apiclient, exceptions
from sanity.webhook import parse_signature, timestamp_is_valid, contains_valid_signature, get_json_payload


class Client(apiclient.ApiClient):
    def __init__(
        self,
        logger,
        project_id,
        dataset,
        api_host=None,
        api_version="2023-05-03",
        use_cdn=True,
        token=None,
    ):
        """
        Client wrapper for Sanity.io HTTP API.

        :param logger: Logger
        :param project_id: Sanity Project ID
        :param dataset: Sanity project dataset to use
        :param api_host: The base URI to the API
        :param api_version: API Version to use (format YYYY-MM-DD)
        :param use_cdn: Use CDN endpoints for quicker responses
        :param token: API token
        """
        self.project_id = project_id
        self.dataset = dataset
        self.api_version = api_version
        self.token = token

        # API: https://<projectId>.api.sanity.io/v<YYYY-MM-DD>/<path>
        # API CDN: https://<projectId>.apicdn.sanity.io/v<YYYY-MM-DD>/<path>

        if use_cdn is True and api_host is None:
            api_host = f"https://{project_id}.apicdn.sanity.io/v{self.api_version}"
        elif use_cdn is False and api_host is None:
            api_host = f"https://{project_id}.api.sanity.io/v{self.api_version}"

        logger.debug(f"API Host: {api_host}")
        super().__init__(logger=logger, base_uri=api_host)

    def query(self, groq: str, variables: dict = None, explain: bool = False, method="GET"):
        """
        https://www.sanity.io/docs/http-query

        GET /data/query/<dataset>?query=<GROQ-query>
        POST /data/query/<dataset>
            {
              "query": "<the GROQ query>",
              "params": {
                "language": "es"
              }
            }

        :param groq: Sanity GROQ Query
        :param variables: Substitutions for the groq query
        :param explain: Return the query planner
        :param method: Use the GET or POST method

        :return:
        :rtype: json
        """
        url = f"/data/query/{self.dataset}"
        if method.upper() == "GET":
            params = {
                "query": groq,
                "explain": "true" if explain else "false"
            }
            if variables:
                for k, v in variables.items():
                    if type(v) == str:
                        params[f"${k}"] = f"\"{v}\""
                    else:
                        params[f"${k}"] = v
            return self.request(
                method="GET", url=url, data=None, params=params
            )
        elif method.upper() == "POST":
            payload = {
                "query": groq,
                "params": variables
            }
            return self.request(
                method="POST", url=url, data=payload, params=None
            )

    def mutate(
            self, transactions: list, return_ids: bool = False,
            return_documents: bool = False, visibility: str = "sync",
            dry_run: bool = False
    ):
        """
        https://www.sanity.io/docs/http-mutations

        POST /data/mutate/:dataset

        :param transactions: List of Sanity formatted transactions
        :param return_ids: Return IDs flag
        :param return_documents: Return Documents flag
        :param visibility: sync, async or deferred options. sync the request will not return until the requested
        changes are visible to subsequent queries - See Sanity docs for more details
        :param dry_run: Run mutation in test mode

        :return:
        :rtype: json
        """
        if not self.token:
            return ""

        url = f"/data/mutate/{self.dataset}"

        parameters = {
            "returnIds": "true" if return_ids else "false",
            "returnDocuments": "true" if return_documents else "false",
            "visibility": visibility,
            "dryRun": "true" if dry_run else "false"
        }

        payload = {
            "mutations": transactions
        }

        return self.request(
            method="POST", url=url, data=payload, params=parameters
        )

    def assets(self, file_path: str, mime_type: str = ""):
        """

        POST assets/images/:dataset

        :param file_path: Image file location or web address
        :param mime_type: Force the mime type

        :return:
        :rtype: json
        """
        url = f"/assets/images/{self.dataset}"

        data = None

        mt = mimetypes.guess_type(file_path)
        if mt:
            mime_type = mt[0]

        if "http" in file_path:
            r = requests.get(file_path, stream=False)
            if r.status_code == 200:
                data = r.content
            else:
                return None
        else:
            with open(file_path, 'rb') as f:
                data = f.read()

        try:
            return self.request(
                method="POST", url=url, data=data, content_type=mime_type
            )
        except exceptions.SanityIOError as e:
            raise e

    def history_document_revision(self, document_id, revision=None, dt=None):
        """

        GET /v2021-06-07/data/history/:dataset/documents/:documentId

        :param document_id:
        :param revision:
        :param dt: format 2019-05-28T17:18:39Z
        :return:
        :rtype: json
        """
        url = f"/data/history/{self.dataset}/documents/{document_id}"

        params = {
            "revision": revision,
            "time": dt,
        }
        try:
            return self.request(
                method="GET", url=url, data=None, params=params
            )
        except exceptions.SanityIOError as e:
            raise e

    def history_document_transactions(
            self, document_ids: list, exclude_content=True, from_time=None, to_time=None,
            from_transaction=None, to_transaction=None, authors=None, reverse=False, limit=100
    ):
        """

        GET /v2021-06-07/data/history/:dataset/transactions/:document_ids

        :param document_ids: comma separated list
        :param exclude_content:
        :param from_time: format 2019-05-28T17:18:39Z
        :param to_time: format 2019-05-28T17:18:39Z
        :param from_transaction:
        :param to_transaction:
        :param authors:
        :param reverse:
        :param limit:
        :return:
        :rtype: list
        """
        doc_ids = ",".join(document_ids)
        url = f"/data/history/{self.dataset}/transactions/{doc_ids}"

        params = {
            "excludeContent": exclude_content,
            "fromTime": from_time,
            "toTime": to_time,
            "fromTransaction": from_transaction,
            "toTransaction": to_transaction,
            "authors": authors,
            "reverse": reverse,
            "limit": limit,
        }
        try:
            data = self.request(
                method="GET", url=url, data=None, params=params,
                load_json=False, parse_ndjson=True
            )
            return data
        except exceptions.SanityIOError as e:
            raise e


def validate_webhook(event: dict, secret: str):
    headers = event.get("headers", {})

    timestamp, signatures = parse_signature(
        signature_header=headers.get("sanity-webhook-signature")
    )

    if not timestamp or not timestamp_is_valid(timestamp):
        return False

    return contains_valid_signature(
        payload=event["body"],
        timestamp=timestamp,
        signatures=signatures,
        secret=secret
    )


def parse_webhook(event: dict):
    try:
        return get_json_payload(event)
    except ValueError as err:
        raise err
