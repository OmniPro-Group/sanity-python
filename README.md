# sanity-python
Sanity Python Client

## Example
```python
from sanity.client import Client
import logging
from scripts.colour_json import print_json_in_colour

logger = logging.getLogger(__name__)

project_id = "<project id>"
dataset = "<dataset>"
token = "<api token>"

client = Client(
    logger,
    project_id=project_id,
    dataset=dataset,
    token=token,
    use_cdn=True
)

# GET Query Method
result = client.query(
    groq="count(*[_type == 'post'])",
    explain=False,
    variables={
        "language": "es",
        "t": 4
    },
    method="GET"
)
print_json_in_colour(result)

# POST Query Method
result = client.query(
    groq="count(*[_type == 'post'])",
    variables={
        "language": "es",
        "t": 4
    },
    method="POST"
)
print_json_in_colour(result)

# Assets
png = "https://some.web.address.com/some_name.png"
result = client.assets(file_path=png)
print_json_in_colour(result)

png2 = "some_file_path/name"
result = client.assets(file_path=png2, mime_type="image/png")
print_json_in_colour(result)

# Mutate
transactions = [
    {
        "createOrReplace": {
            "_id": "speaker.asdf",
            "_type": "speaker",
            "title": "Some Name",
            "slug": {
                "_type": "slug",
                "current": "some-name"
            },
            'image': {
              '_type': 'image',
              'asset': {
                '_ref': 'image-6ffb37d2eeabc7d07b3ca485c7b497e77bdcccd4-1232x1280-png',
                '_type': 'reference'
              }
            }
        }
    }
]
result = client.mutate(
    transactions=transactions,
    return_ids=False,
    return_documents=False,
    visibility="sync",
    dry_run=False,
)
print_json_in_colour(result)
```

## Pre Commit Howto
```shell
pip install -r requirements.txt
pre-commit --version
# create .pre-commit-config.yaml file
pre-commit install
pre-commit run --all-files
```
